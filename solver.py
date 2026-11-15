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

def safe_parse_json(text: str) -> dict:
    try:
        m = re.search(r'\{[\s\S]*\}', text)
        if m: return json.loads(m.group(0))
    except Exception:
        pass
    return {}

class AISolver:
    _OPENAI_COMPAT_URLS = {
        "groq":       "https://api.groq.com/openai/v1/chat/completions",
        "openrouter": "https://openrouter.ai/api/v1/chat/completions",
        "mistral":    "https://api.mistral.ai/v1/chat/completions",
        "xai":        "https://api.x.ai/v1/chat/completions",
        "openai":     "https://api.openai.com/v1/chat/completions",
    }
    _MODELS_URLS = {
        "groq":       "https://api.groq.com/openai/v1/models",
        "openrouter": "https://openrouter.ai/api/v1/models",
        "mistral":    "https://api.mistral.ai/v1/models",
        "xai":        "https://api.x.ai/v1/models",
        "openai":     "https://api.openai.com/v1/models",
    }
    _LIMITS = {
        "gemini":     {"rpm": 15,  "rpd": 1500,  "free": True},
        "groq":       {"rpm": 30,  "rpd": 1000,  "free": True},
        "openrouter": {"rpm": 20,  "rpd": 50,    "free": True},
        "mistral":    {"rpm": 60,  "rpd": 1000,  "free": True},
        "jev":        {"rpm": 100, "rpd": 10000, "free": True},
        "xai":        {"rpm": 60,  "rpd": 1000,  "free": False},
        "openai":     {"rpm": 60,  "rpd": 10000, "free": False},
    }

    def __init__(self, provider: str, api_key: str, model: str = "", rpd_limit: int = 1500):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model
        self.used_today = 0
        self.rpd_limit = rpd_limit
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Onluyen-Solver/6.0"})

    def _get_default_model(self) -> str:
        # CẬP NHẬT 15/11/2026: Model mặc định theo thông tin mới nhất
        return {
            "gemini":     "gemini-3.8-flash",          # Free tier, production default
            "groq":       "qwen/qwen3.8-27b",          # Model mới, thay thế Llama cũ
            "openrouter": "openrouter/free",            # Router tự chọn model free
            "mistral":    "mistral-small-latest",       # Mistral Small 4
            "xai":        "grok-4.7",                   # Reasoning model, 500K context
            "openai":     "gpt-4.1-mini",              # Thay thế gpt-4o-mini sắp bị khai tử
            "jev":        "jev-classifier",
        }.get(self.provider, "")

    def fetch_models_and_limits(self) -> Dict[str, Any]:
        if self.provider == "jev":
            return {"models": ["jev-classifier"], "limits": self._LIMITS["jev"]}
        try:
            if self.provider == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
                r = self._session.get(url, timeout=10)
                if r.status_code != 200:
                    return {"error": f"HTTP {r.status_code}: Key không hợp lệ"}
                models = []
                for m in r.json().get("models", []):
                    name = m.get("name", "").replace("models/", "")
                    if "flash" in name and "tts" not in name and "vision" not in name:
                        models.append(name)
                def _score(x):
                    if "3.8" in x: return 150
                    if "3.6" in x: return 120
                    if "3.5" in x: return 100
                    if "2.5" in x: return 50
                    return 0
                models.sort(key=_score, reverse=True)
                return {"models": models[:15], "limits": self._LIMITS["gemini"]}

            url = self._MODELS_URLS.get(self.provider)
            if not url:
                return {"error": f"Provider {self.provider} không hỗ trợ."}
            r = self._session.get(url, headers={"Authorization": f"Bearer {self.api_key}"}, timeout=10)
            if r.status_code != 200:
                return {"error": f"HTTP {r.status_code}: Key không hợp lệ"}
            models = [m["id"] for m in r.json().get("data", [])]
            return {"models": models[:20],
                    "limits": self._LIMITS.get(self.provider, {"rpm": 10, "rpd": 1000, "free": False})}
        except Exception as e:
            return {"error": str(e)}

    def check_quota(self) -> tuple:
        try:
            if self.provider == "jev":
                return True, "Sẵn sàng"
            if self.provider == "gemini":
                model = self.model or self._get_default_model()
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                r = self._session.post(url, json={"contents": [{"parts": [{"text": "1"}]}],
                                                  "generationConfig": {"maxOutputTokens": 1}}, timeout=10)
                if r.status_code == 200: return True, "Sẵn sàng"
                if r.status_code == 404:
                    info = self.fetch_models_and_limits()
                    if info.get("models"):
                        self.model = info["models"][0]
                        return True, f"Đã tự động chuyển sang {self.model}"
                    return False, "Model không tồn tại."
                return False, f"Lỗi HTTP {r.status_code}"

            url = self._OPENAI_COMPAT_URLS.get(self.provider)
            if not url: return False, "Provider chưa hỗ trợ."
            model = self.model or self._get_default_model()
            r = self._session.post(url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "messages": [{"role": "user", "content": "1"}], "max_tokens": 1},
                timeout=15)
            if r.status_code == 200: return True, "Sẵn sàng"
            if r.status_code == 429: return True, "Sẵn sàng (đã chạm rate limit tạm thời)"
            if r.status_code == 404:
                info = self.fetch_models_and_limits()
                if info.get("models") and info["models"][0] != model:
                    self.model = info["models"][0]
                    return True, f"Đã tự động chuyển sang {self.model}"
                return False, "Model không tồn tại."
            return False, f"Lỗi HTTP {r.status_code}"
        except Exception as e:
            return False, str(e)

    def _call_gemini(self, prompt: str, images_b64: List[str] = None) -> str:
        model = self.model or self._get_default_model()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        parts = [{"text": prompt}]
        if images_b64:
            for img in images_b64:
                parts.append({"inlineData": {"mimeType": img.split(";")[0].replace("data:", ""),
                                              "data": img.split(",")[1]}})
        payload = {"contents": [{"parts": parts}],
                   "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048,
                                         "responseMimeType": "application/json"}}
        for attempt in range(5):
            try:
                r = self._session.post(url, json=payload, timeout=60)
                if r.status_code == 200:
                    return r.json()["candidates"][0]["content"]["parts"][0]["text"]
                if r.status_code in (503, 429):
                    time.sleep((attempt + 1) * 3); continue
                if r.status_code == 404:
                    info = self.fetch_models_and_limits()
                    if info.get("models") and info["models"][0] != model:
                        self.model = info["models"][0]
                        return self._call_gemini(prompt, images_b64)
                    raise SolverError(f"Model {model} không khả dụng.")
                raise SolverError(f"Gemini {r.status_code}: {r.text[:200]}")
            except requests.exceptions.RequestException as e:
                if attempt == 4: raise SolverError(f"Lỗi mạng: {e}")
                time.sleep((attempt + 1) * 3)
        raise SolverError("Gemini quá tải.")

    def _call_openai_compatible(self, prompt: str) -> str:
        url = self._OPENAI_COMPAT_URLS.get(self.provider)
        if not url: raise SolverError(f"Provider {self.provider} chưa hỗ trợ.")
        model = self.model or self._get_default_model()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            try:
                r = self._session.post(url, headers=headers,
                    json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1},
                    timeout=60)
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"]
                if r.status_code in (429, 503):
                    time.sleep((attempt + 1) * 3); continue
                if r.status_code == 404:
                    info = self.fetch_models_and_limits()
                    if info.get("models") and info["models"][0] != model:
                        model = info["models"][0]; self.model = model; continue
                    raise SolverError(f"Model {model} không khả dụng.")
                if r.status_code == 402:
                    raise SolverError(f"{self.provider}: Hết credit (402)")
                raise SolverError(f"{self.provider} {r.status_code}: {r.text[:200]}")
            except requests.exceptions.RequestException as e:
                if attempt == 3: raise SolverError(f"Lỗi mạng: {e}")
                time.sleep((attempt + 1) * 3)
        raise SolverError(f"{self.provider} quá tải.")

    def _get_images(self, html_content: str) -> List[str]:
        m = re.findall(r'<img[^>]+src=["\'](data:image/[^;]+;base64,[^"\']+)["\']', html_content)
        return [x for x in m if len(x) < 4 * 1024 * 1024][:3]

    def solve(self, question: Any) -> Dict[str, Any]:
        if self.used_today >= self.rpd_limit:
            raise SolverError("Đã hết hạn mức RPD.")
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
            prompt = (f"{role}\nĐề bài: {content}\n\n"
                      f"YÊU CẦU BẮT BUỘC:\n"
                      f"1. Hãy suy luận từng bước để tìm ra đáp số cuối cùng.\n"
                      f"2. Nếu đáp số là số thập phân, BẮT BUỘC sử dụng dấu phẩy (,) thay vì dấu chấm (.).\n"
                      f"3. Không bao gồm đơn vị đo lường (kg, m, cm...).\n"
                      f"4. Chỉ trả về JSON duy nhất: {{\"answer\": \"<đáp_số>\"}}")

        try:
            if self.provider == "gemini":
                raw = self._call_gemini(prompt, images_b64)
            elif self.provider == "jev":
                time.sleep(1.5); return self._solve_jev(question)
            else:
                raw = self._call_openai_compatible(prompt)
            json_ans = safe_parse_json(raw)
            self.used_today += 1
        except Exception as e:
            raise SolverError(str(e))

        if qtype == "choice":
            ans = str(json_ans.get("answer", "A")).upper()
            if len(ans) > 1:
                m = re.search(r'[A-D]', raw.upper())
                ans = m.group(0) if m else "A"
            idx = ord(ans) - ord('A')
            opt_id = question.options[idx]["id"] if idx < len(question.options) else question.options[0]["id"]
            return {"stepId": question.id, "type": "choice", "optionId": opt_id}
        if qtype == "true_false":
            arr = json_ans.get("answers", [])
            if not isinstance(arr, list): arr = []
            while len(arr) < len(question.options): arr.append("false")
            return {"stepId": question.id, "type": "true_false",
                    "choices": [str(x).lower() for x in arr[:len(question.options)]]}
        text = str(json_ans.get("answer", "0")).strip()
        text = re.sub(r'(\d)\.(\d)', r'\1,\2', text)
        return {"stepId": question.id, "type": "text", "text": text}

    def _solve_jev(self, question: Any) -> Dict[str, Any]:
        def _q(labels, text):
            url = f"https://classifier.dev/{','.join(labels)}/{urllib.parse.quote(text[:800], safe='')}"
            try:
                r = self._session.get(url, timeout=15)
                return r.text.strip() if r.status_code == 200 else labels[0]
            except Exception:
                return labels[0]
        if question.qtype == "choice":
            opts = "\n".join([f"{chr(65+i)}. {clean_display_text(o['text'])}" for i, o in enumerate(question.options)])
            pred = _q(["A", "B", "C", "D"][:len(question.options)], f"Câu hỏi: {question.content}\n{opts}")
            for l in ["A", "B", "C", "D"]:
                if l in pred.upper():
                    idx = ord(l) - ord('A')
                    if idx < len(question.options):
                        return {"stepId": question.id, "type": "choice", "optionId": question.options[idx]["id"]}
            return {"stepId": question.id, "type": "choice", "optionId": question.options[0]["id"]}
        if question.qtype == "true_false":
            res = [_q(["Dung", "Sai"], f"Đề: {question.content}\nNhận định: {s['text']}") for s in question.options]
            return {"stepId": question.id, "type": "true_false",
                    "choices": ["true" if "dung" in r.lower() else "false" for r in res]}
        return {"stepId": question.id, "type": "text", "text": "1"}
