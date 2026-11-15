import re
import json
import time
import requests
from typing import List, Dict, Any

class SolverError(Exception): pass

def clean_display_text(text: str) -> str:
    if not text: return ""
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text)).strip()

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
        # Cập nhật danh sách model mới nhất
        defaults = {
            "gemini": "gemini-3.8-flash", 
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
                    if "flash" in name or "pro" in name: models.append(name)
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
                return False, "Model không tồn tại và không tìm thấy thay thế."
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
                    time.sleep((attempt + 1) * 2)
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
                time.sleep((attempt + 1) * 2)
        raise SolverError("Server AI quá tải (503). Vui lòng thử lại sau.")

    def _parse_json_response(self, raw_text: str, qtype: str) -> Any:
        raw_text = re.sub(r'```json\s*|\s*```', '', raw_text).strip()
        try:
            data = json.loads(raw_text)
            if qtype == "choice":
                ans = str(data.get("answer", "A")).upper()
                return ans if ans in "ABCD" else "A"
            elif qtype == "true_false": return [str(x).lower() for x in data.get("answers", [])]
            else: return str(data.get("answer", "0")).strip()
        except json.JSONDecodeError:
            if qtype == "choice":
                match = re.search(r'[A-D]', raw_text.upper())
                return match.group(0) if match else "A"
            elif qtype == "true_false": return [x for x in re.findall(r'true|false', raw_text.lower())]
            else: return raw_text.split("\n")[-1].strip()[:50]

    def _get_images(self, html_content: str) -> List[str]:
        matches = re.findall(r'<img[^>]+src=["\'](data:image/[^;]+;base64,[^"\']+)["\']', html_content)
        return [m for m in matches if len(m) < 4 * 1024 * 1024][:3]

    def solve(self, question: Any) -> Dict[str, Any]:
        if self.used_today >= self.rpd_limit: raise SolverError("Đã hết hạn mức RPD.")
        
        qtype, content = question.qtype, clean_display_text(question.content)
        images_b64 = self._get_images(question.content) if self.provider == "gemini" else []
            
        role = "Bạn là giáo viên giỏi. Hãy phân tích cẩn thận."
        if qtype == "choice":
            opts = "\n".join([f"{chr(65+i)}. {clean_display_text(o['text'])}" for i, o in enumerate(question.options)])
            prompt = f"{role}\nCâu hỏi: {content}\n\nCác lựa chọn:\n{opts}\n\nHãy giải thích ngắn, sau đó trả về JSON: {{\"answer\": \"A\"}}"
        elif qtype == "true_false":
            stmts = "\n".join([f"{i+1}. {clean_display_text(o['text'])}" for i, o in enumerate(question.options)])
            prompt = f"{role}\nĐề bài: {content}\nCác nhận định:\n{stmts}\n\nTrả về JSON: {{\"answers\": [\"true\", \"false\"]}}"
        else:
            prompt = f"{role}\nGiải bài sau và đưa ra đáp số: {content}\nTrả về JSON: {{\"answer\": \"đáp số\"}}"

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

            ai_answer = self._parse_json_response(raw, qtype)
            self.used_today += 1
        except Exception as e:
            raise SolverError(str(e))

        if qtype == "choice":
            idx = ord(ai_answer) - ord('A')
            opt_id = question.options[idx]["id"] if idx < len(question.options) else question.options[0]["id"]
            return {"stepId": question.id, "type": "choice", "optionId": opt_id}
        elif qtype == "true_false":
            while len(ai_answer) < len(question.options): ai_answer.append("true")
            return {"stepId": question.id, "type": "true_false", "choices": ai_answer[:len(question.options)]}
        else: return {"stepId": question.id, "type": "text", "text": ai_answer}

    def _solve_jev(self, question: Any) -> Dict[str, Any]:
        import urllib.parse
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
