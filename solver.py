import re
import json
import time
import requests
import urllib.parse
from typing import List, Dict, Any

class SolverError(Exception): pass

def clean_display_text(text: str) -> str:
    if not text: return ""
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text)).strip()

# Bóc tách JSON an toàn
def safe_parse_json(text: str) -> dict:
    try:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass
    return {}

class AISolver:
    def __init__(self, provider: str, api_key: str, model: str = "", rpd_limit: int = 1500):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model
        self.used_today = 0
        self.rpd_limit = rpd_limit
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Onluyen-Solver/4.0"})

    def _get_default_model(self) -> str:
        defaults = {
            "gemini": "gemini-1.5-flash", 
            "groq": "llama-3.1-8b-instant",
            "openrouter": "google/gemma-2-9b-it:free",
            "mistral": "open-mistral-nemo",
            "jev": "jev-classifier"
        }
        return defaults.get(self.provider, "")

    def fetch_models_and_limits(self) -> Dict[str, Any]:
        if self.provider == "jev":
            return {"models": ["jev-classifier"], "limits": {"rpm": 100, "rpd": 10000}}
        try:
            if self.provider == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
                resp = self._session.get(url, timeout=10)
                if resp.status_code != 200: return {"error": f"HTTP {resp.status_code}: Key không hợp lệ"}
                models = []
                for m in resp.json().get("models", []):
                    name = m.get("name", "").replace("models/", "")
                    if "flash" in name and "tts" not in name and "vision" not in name:
                        models.append(name)
                models.sort(key=lambda x: 100 if "3.8" in x else (90 if "2.5" in x else 0), reverse=True)
                return {"models": models[:15], "limits": {"rpm": 15, "rpd": 1500}}
            return {"models": [], "limits": {"rpm": 10, "rpd": 1000}}
        except Exception as e:
            return {"error": str(e)}

    def check_quota(self) -> tuple[bool, str]:
        try:
            if self.provider == "jev": return True, "Sẵn sàng"
            model = self.model or self._get_default_model()
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            payload = {"contents": [{"parts": [{"text": "1"}]}], "generationConfig": {"maxOutputTokens": 1}}
            resp = self._session.post(url, json=payload, timeout=10)
            if resp.status_code == 200: return True, "Sẵn sàng"
            elif resp.status_code == 404:
                models_info = self.fetch_models_and_limits()
                if models_info.get("models"):
                    self.model = models_info["models"][0]
                    return True, f"Đã tự động chuyển sang {self.model}"
                return False, "Model không tồn tại."
            return False, f"Lỗi HTTP {resp.status_code}"
        except Exception as e: return False, str(e)

    def _call_gemini(self, prompt: str, images_b64: List[str] = None) -> str:
        model = self.model or self._get_default_model()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        parts = [{"text": prompt}]
        if images_b64:
            for img in images_b64:
                parts.append({"inlineData": {"mimeType": img.split(";")[0].replace("data:", ""), "data": img.split(",")[1]}})
                
        payload = {"contents": [{"parts": parts}], "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048, "responseMimeType": "application/json"}}
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                resp = self._session.post(url, json=payload, timeout=60)
                if resp.status_code == 200: return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                elif resp.status_code in (503, 429):
                    time.sleep((attempt + 1) * 3)
                    continue
                elif resp.status_code == 404:
                    info = self.fetch_models_and_limits()
                    if info.get("models") and info["models"][0] != model:
                        self.model = info["models"][0]
                        return self._call_gemini(prompt, images_b64)
                    raise SolverError(f"Lỗi 404: Model {model} không khả dụng.")
                else: raise SolverError(f"Gemini Error {resp.status_code}: {resp.text}")
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1: raise SolverError(f"Lỗi mạng: {str(e)}")
                time.sleep((attempt + 1) * 3)
        raise SolverError("Server AI quá tải (503).")

    def _get_images(self, html_content: str) -> List[str]:
        matches = re.findall(r'<img[^>]+src=["\'](data:image/[^;]+;base64,[^"\']+)["\']', html_content)
        return [m for m in matches if len(m) < 4 * 1024 * 1024][:3]

    def solve(self, question: Any) -> Dict[str, Any]:
        if self.used_today >= self.rpd_limit: raise SolverError("Đã hết hạn mức RPD.")
        
        qtype, content = question.qtype, clean_display_text(question.content)
        images_b64 = self._get_images(question.content) if self.provider == "gemini" else []
            
        role = "Bạn là một giáo viên giỏi giải bài tập chính xác tuyệt đối. Hãy phân tích cẩn thận."
        
        if qtype == "choice":
            opts = "\n".join([f"{chr(65+i)}. {clean_display_text(o['text'])}" for i, o in enumerate(question.options)])
            prompt = f"{role}\nCâu hỏi: {content}\n\nCác lựa chọn:\n{opts}\n\nHãy giải thích ngắn gọn lý do, sau đó chỉ trả về JSON: {{\"answer\": \"<chữ_cái_đáp_án>\"}}"
            
        elif qtype == "true_false":
            stmts = "\n".join([f"{i+1}. {clean_display_text(o['text'])}" for i, o in enumerate(question.options)])
            prompt = f"{role}\nĐề bài: {content}\nCác nhận định:\n{stmts}\n\nTrả về JSON: {{\"answers\": [\"true\", \"false\", ...]}}"
            
        else:
            # NÂNG CẤP SHORT ANSWER: Ép AI suy luận và đổi dấu chấm thành dấu phẩy
            prompt = (
                f"{role}\n"
                f"Đề bài: {content}\n\n"
                f"YÊU CẦU BẮT BUỘC:\n"
                f"1. Hãy suy luận từng bước để tìm ra đáp số cuối cùng.\n"
                f"2. Nếu đáp số là số thập phân, BẮT BUỘC sử dụng dấu phẩy (,) thay vì dấu chấm (.). Ví dụ: 3.14 phải viết là 3,14.\n"
                f"3. Không bao gồm đơn vị đo lường (kg, m, cm...).\n"
                f"4. Chỉ trả về JSON duy nhất: {{\"answer\": \"<đáp_số>\"}}"
            )

        try:
            if self.provider == "gemini": raw = self._call_gemini(prompt, images_b64)
            elif self.provider == "jev":
                time.sleep(1.5)
                return self._solve_jev(question)
            else:
                url = {"groq": "https://api.groq.com/openai/v1/chat/completions"}.get(self.provider)
                if not url: raise SolverError("Provider chưa hỗ trợ.")
                resp = self._session.post(url, headers={"Authorization": f"Bearer {self.api_key}"}, json={"model": self.model or self._get_default_model(), "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}, timeout=45)
                raw = resp.json()["choices"][0]["message"]["content"]

            json_ans = safe_parse_json(raw)
            self.used_today += 1
            
        except Exception as e:
            raise SolverError(str(e))

        # XỬ LÝ KẾT QUẢ TRẢ VỀ
        if qtype == "choice":
            ans_letter = str(json_ans.get("answer", "A")).upper()
            # Fallback nếu AI trả lời lan man
            if len(ans_letter) > 1:
                match = re.search(r'[A-D]', raw.upper())
                ans_letter = match.group(0) if match else "A"
                
            idx = ord(ans_letter) - ord('A')
            opt_id = question.options[idx]["id"] if idx < len(question.options) else question.options[0]["id"]
            return {"stepId": question.id, "type": "choice", "optionId": opt_id}
            
        elif qtype == "true_false":
            arr = json_ans.get("answers", [])
            if not isinstance(arr, list): arr = []
            while len(arr) < len(question.options): arr.append("false")
            return {"stepId": question.id, "type": "true_false", "choices": [str(x).lower() for x in arr[:len(question.options)]]}
            
        else:
            ans_text = str(json_ans.get("answer", "0")).strip()
            # TỰ ĐỘNG ĐỔI DẤU CHẤM THÀNH DẤU PHẨY (Ví dụ: 3.14 -> 3,14)
            ans_text = re.sub(r'(\d)\.(\d)', r'\1,\2', ans_text)
            return {"stepId": question.id, "type": "text", "text": ans_text}

    def _solve_jev(self, question: Any) -> Dict[str, Any]:
        def _q(labels, text):
            url = f"https://classifier.dev/{','.join(labels)}/{urllib.parse.quote(text[:800], safe='')}"
            try:
                r = self._session.get(url, timeout=15)
                return r.text.strip() if r.status_code == 200 else labels[0]
            except: return labels[0]

        if question.qtype == "choice":
            opts = "\n".join([f"{chr(65+i)}. {clean_display_text(o['text'])}" for i, o in enumerate(question.options)])
            pred = _q(["A", "B", "C", "D"][:len(question.options)], f"Câu hỏi: {question.content}\n{opts}")
            for l in ["A", "B", "C", "D"]:
                if l in pred.upper():
                    idx = ord(l) - ord('A')
                    if idx < len(question.options): return {"stepId": question.id, "type": "choice", "optionId": question.options[idx]["id"]}
            return {"stepId": question.id, "type": "choice", "optionId": question.options[0]["id"]}
        elif question.qtype == "true_false":
            res = [_q(["Dung", "Sai"], f"Đề: {question.content}\nNhận định: {s['text']}") for s in question.options]
            return {"stepId": question.id, "type": "true_false", "choices": ["true" if "dung" in r.lower() else "false" for r in res]}
        return {"stepId": question.id, "type": "text", "text": "1"}
