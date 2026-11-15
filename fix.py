#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FIX v6.7 — Đồng bộ 100% logic API từ tool_onluyen.py.
- Thêm fallback API /detail/ nếu /doing/ lỗi.
- Bỏ lệnh skip câu hỏi rỗng (khắc phục lỗi 30/31 câu).
- Giữ nguyên giao diện GUI.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FILES = {}

# ============================================================
# 1. onluyen_api.py — COPY NGUYÊN LOGIC TỪ TOOL_ONLUYEN.PY
# ============================================================
FILES["onluyen_api.py"] = r'''import re
import json
import base64
import hashlib
import os
import time
import html
from typing import List, Optional, Dict, Any
import requests
from models import Assignment, Question

SESSION_FILE = ".onluyen_session.json"
ACCOUNTS_FILE = ".onluyen_accounts.json"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Mobile Safari/537.36"

class SessionExpiredError(Exception):
    pass

def _process_img_tag(match) -> str:
    src = match.group(1).strip()
    if src.startswith("data:image"):
        try:
            parts = src.split(",", 1)
            if len(parts) == 2:
                header, b64data = parts
                ext = "png"
                if "image/jpeg" in header: ext = "jpg"
                elif "image/webp" in header: ext = "webp"
                elif "image/gif" in header: ext = "gif"

                raw_bytes = base64.b64decode(b64data)
                h = hashlib.md5(raw_bytes).hexdigest()[:12]
                cache_dir = os.path.join(os.getcwd(), "images_cache")
                os.makedirs(cache_dir, exist_ok=True)
                img_path = os.path.join(cache_dir, f"{h}.{ext}")
                if not os.path.exists(img_path):
                    with open(img_path, "wb") as f:
                        f.write(raw_bytes)
                return f" ![Hình ảnh]({img_path}) "
        except Exception:
            return " [Hình ảnh lỗi] "
    return f" ![Hình ảnh]({src}) "

def clean_html(raw_html: str) -> str:
    if not raw_html: return ""
    raw_html = re.sub(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', _process_img_tag, raw_html)
    raw_html = re.sub(r'<br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
    raw_html = re.sub(r'</p>', '\n', raw_html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", raw_html)
    text = html.unescape(text)
    
    text = re.sub(r'\\+left|\\+right', '', text)
    text = re.sub(r'\\+{', '{', text)
    text = re.sub(r'\\+}', '}', text)
    text = re.sub(r'\\+frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', text)
    text = re.sub(r'\\+sqrt\{([^}]+)\}', r'√(\1)', text)
    
    return re.sub(r'\s+', ' ', text).strip()

class OnluyenAPI:
    LOGIN_URL = "https://oauth.onluyen.vn/api/account/login"
    BASE_API = "https://api-elb.onluyen.vn/api"

    def __init__(self):
        self.username = ""
        self.password = ""
        self.token = ""
        self.user_id = ""
        self.display_name = ""
        self.email = ""
        self.school_id = "648"
        self.school_year = "2026"
        self.code_app = "SCHOOL"
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json, text/plain, */*",
            "origin": "https://app.onluyen.vn",
            "referer": "https://app.onluyen.vn/",
            "user-agent": DEFAULT_USER_AGENT
        })

    def _apply_headers(self):
        self.session.headers.update({
            "authorization": f"Bearer {self.token}",
            "code-app": self.code_app,
            "school-id": self.school_id,
            "school-year": self.school_year,
            "user-id": self.user_id,
            "user-name": self.username,
            "content-type": "application/json",
            # Thêm headers viết liền theo tool_onluyen
            "schoolyear": self.school_year,
            "schoolid": self.school_id,
            "userid": self.user_id
        })

    def _save_session(self):
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "token": self.token, "user_id": self.user_id, 
                    "email": self.email, "display_name": self.display_name,
                    "school_id": self.school_id, "school_year": self.school_year
                }, f)
        except Exception: pass

    def auto_login(self) -> bool:
        if not os.path.exists(SESSION_FILE): return False
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.token = data.get("token", "")
                self.user_id = data.get("user_id", "")
                self.email = data.get("email", "")
                self.display_name = data.get("display_name", "")
                self.username = self.email
                self.school_id = data.get("school_id", self.school_id)
                self.school_year = data.get("school_year", self.school_year)
                
            payload_part = self.token.split(".")[1]
            payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
            jwt_data = json.loads(base64.urlsafe_b64decode(payload_part.encode()).decode("utf-8"))
            if jwt_data.get("exp", 0) > time.time() + 300:
                self._apply_headers()
                return True
        except Exception:
            pass
        return False

    def login(self, username: str, password: str):
        payload = {"userName": username, "password": password, "codeApp": self.code_app}
        resp = self.session.post(self.LOGIN_URL, json=payload, timeout=15)
        if resp.status_code != 200:
            raise Exception("Đăng nhập thất bại. Sai tài khoản hoặc mật khẩu.")
            
        data = resp.json()
        self.token = data.get("access_token", "")
        if not self.token: raise Exception("Không lấy được token.")
        
        self.username = username
        self.email = username
        self.password = password
        
        try:
            payload_part = self.token.split(".")[1]
            payload_part += "=" * ((4 - len(payload_part) % 4) % 4)
            jwt_data = json.loads(base64.urlsafe_b64decode(payload_part.encode()).decode("utf-8"))
            self.user_id = jwt_data.get("userId", "")
            self.display_name = jwt_data.get("DisplayName", "")
            self.school_id = str(jwt_data.get("CreateBySchool", self.school_id))
        except Exception: pass

        self._apply_headers()
        self._save_session()
        self._save_account(username, password)

    def _save_account(self, username, password):
        accounts = self.get_saved_accounts()
        for acc in accounts:
            if acc["username"] == username: return
        accounts.append({
            "username": username, 
            "password": base64.b64encode(password.encode()).decode(),
            "display_name": self.display_name or username
        })
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)

    def get_saved_accounts(self) -> List[Dict]:
        if os.path.exists(ACCOUNTS_FILE):
            try:
                with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception: pass
        return []

    def logout(self):
        self.token = ""
        if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)

    def get_assignments(self, filter_status="all") -> List[Assignment]:
        url = f"{self.BASE_API}/school-online/assignment/assign-student-suggest?pageIndex=1&pageSize=50"
        resp = self.session.get(url, timeout=15)
        if resp.status_code == 401: raise SessionExpiredError()
        if resp.status_code != 200: return []

        items = resp.json().get("data", [])
        results = []
        for it in items:
            st = it.get("status")
            if filter_status == "todo" and st not in (0, 1): continue
            if filter_status == "done" and st not in (2, 3): continue
            results.append(Assignment(
                assign_id=it.get("assignId"), title=it.get("name"),
                subject=it.get("className", "Môn học"), status=st,
                completed=st in (2,3), score=it.get("score")
            ))
        return results

    def get_questions(self, assign_id: str) -> List[Question]:
        self.session.post(f"{self.BASE_API}/school-online/assignment/start/{assign_id}", json={}, timeout=15)
        
        # 1. Thử lấy từ doing
        url_doing = f"{self.BASE_API}/school-online/assignment/doing/{assign_id}"
        res = self.session.get(url_doing, timeout=20)
        if res.status_code == 401: raise SessionExpiredError()
        
        data = None
        if res.status_code == 200:
            data = res.json().get("data")
            
        # 2. Fallback lấy từ detail
        if not data:
            url_detail = f"{self.BASE_API}/school-online/assignment/detail/{assign_id}"
            res_detail = self.session.get(url_detail, timeout=20)
            if res_detail.status_code == 200:
                data = res_detail.json().get("data")
                
        if not data:
            raise Exception("Không thể tải đề bài. Bài đã nộp hoặc lỗi API.")
            
        self.put_url = data.get("preSignedUrlAnswer", "")
        raw_qs = data.get("data", [])
        
        questions = []
        # Copy y nguyên vòng lặp của tool_onluyen.py (Không có lệnh continue)
        for idx, item in enumerate(raw_qs):
            std = item.get("dataStandard", {})
            vi = std.get("languagesData", {}).get("vi", {})
            
            step_id = std.get("stepId")  # Có thể là 0
            ta = std.get("typeAnswer", 0)
            content = clean_html(vi.get("content", ""))
            
            qtype = "true_false" if ta == 1 else ("text" if ta in (3, 5) else "choice")
            
            opts = []
            for o in vi.get("options", []):
                opts.append({"id": o.get("idOption"), "text": clean_html(o.get("content", ""))})
                
            questions.append(Question(
                id=step_id, index=idx+1,
                content=content, qtype=qtype, options=opts
            ))
            
        return questions

    def upload_answers(self, assign_id: str, payloads: List[Dict]) -> bool:
        if not getattr(self, 'put_url', ""): return False
        s3_payload = []
        now = int(time.time())
        for p in payloads:
            item = {"id": p["stepId"], "isSkip": False, "studentDoRight": None, "timeUpdate": now, "lang": "vi"}
            if p["type"] == "choice":
                item["optionId"] = [p.get("optionId")]
                item["optionText"] = []
            elif p["type"] == "true_false":
                item["optionId"] = []
                item["optionText"] = p.get("choices", [])
            else:
                item["optionId"] = []
                item["optionText"] = [p.get("text", "")]
            s3_payload.append(item)
            
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://app.onluyen.vn",
            "Referer": "https://app.onluyen.vn/"
        }
        resp = requests.put(self.put_url, data=json.dumps(s3_payload, ensure_ascii=False), headers=headers, timeout=20)
        return resp.status_code in (200, 204)

    def submit(self, assign_id: str) -> Dict:
        url = f"{self.BASE_API}/school-online/assignment/submit/{assign_id}"
        resp = self.session.put(url, json={}, timeout=15)
        if resp.status_code == 200:
            return {"success": True, "message": "Nộp bài thành công"}
        return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text}"}
'''

# ============================================================
# 2. solver.py — CHỐNG LỖI VÀ ĐÁP ÁN RÁC
# ============================================================
FILES["solver.py"] = r'''import re
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
    except Exception: pass
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
        self._session.headers.update({"User-Agent": "Onluyen-Solver/6.7"})

    def _get_default_model(self) -> str:
        return {
            "gemini":     "gemini-3.8-flash",
            "groq":       "qwen/qwen3.8-27b",
            "openrouter": "openrouter/free",
            "mistral":    "mistral-small-latest",
            "xai":        "grok-4.7",
            "openai":     "gpt-4.1-mini",
            "jev":        "jev-classifier",
        }.get(self.provider, "")

    def fetch_models_and_limits(self) -> Dict[str, Any]:
        if self.provider == "jev":
            return {"models": ["jev-classifier"], "limits": self._LIMITS["jev"]}
        for attempt in range(3):
            try:
                if self.provider == "gemini":
                    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
                    r = self._session.get(url, timeout=25)
                    if r.status_code in (401, 403): return {"error": f"HTTP {r.status_code}: Key bị từ chối"}
                    if r.status_code != 200: return {"error": f"HTTP {r.status_code}: {r.text[:120]}"}
                    models = []
                    for m in r.json().get("models", []):
                        name = m.get("name", "").replace("models/", "")
                        if "flash" in name and "tts" not in name and "vision" not in name:
                            models.append(name)
                    models.sort(key=lambda x: 150 if "3.8" in x else (100 if "3.1" in x else 0), reverse=True)
                    return {"models": models[:15], "limits": self._LIMITS["gemini"]}

                url = self._MODELS_URLS.get(self.provider)
                if not url: return {"error": f"Provider {self.provider} không hỗ trợ."}
                r = self._session.get(url, headers={"Authorization": f"Bearer {self.api_key}"}, timeout=25)
                if r.status_code in (401, 403): return {"error": f"HTTP {r.status_code}: Key bị từ chối"}
                if r.status_code != 200: return {"error": f"HTTP {r.status_code}: {r.text[:120]}"}
                models = [m["id"] for m in r.json().get("data", [])]
                return {"models": models[:20], "limits": self._LIMITS.get(self.provider, {"rpm": 10, "rpd": 1000})}
            except requests.exceptions.RequestException as e:
                if attempt < 2: time.sleep(1.5 * (attempt + 1)); continue
                return {"error": f"Timeout/Network: {str(e)[:150]}"}
            except Exception as e:
                return {"error": str(e)}
        return {"error": "Không thể kết nối"}

    def check_quota(self) -> tuple:
        try:
            if self.provider == "jev": return True, "Sẵn sàng"
            if self.provider == "gemini":
                model = self.model or self._get_default_model()
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
                r = self._session.post(url, json={"contents": [{"parts": [{"text": "1"}]}], "generationConfig": {"maxOutputTokens": 1}}, timeout=25)
                if r.status_code == 200: return True, "Sẵn sàng"
                if r.status_code in (401, 403): return False, f"Key bị từ chối (HTTP {r.status_code})"
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
            r = self._session.post(url, headers={"Authorization": f"Bearer {self.api_key}"}, json={"model": model, "messages": [{"role": "user", "content": "1"}], "max_tokens": 1}, timeout=25)
            if r.status_code == 200: return True, "Sẵn sàng"
            if r.status_code == 429: return True, "Sẵn sàng (đã chạm rate limit tạm thời)"
            if r.status_code in (401, 403): return False, f"Key bị từ chối (HTTP {r.status_code})"
            if r.status_code == 404:
                info = self.fetch_models_and_limits()
                if info.get("models") and info["models"][0] != model:
                    self.model = info["models"][0]
                    return True, f"Đã tự động chuyển sang {self.model}"
                return False, "Model không tồn tại."
            return False, f"Lỗi HTTP {r.status_code}"
        except requests.exceptions.Timeout:
            return False, "Timeout mạng (25s)"
        except Exception as e:
            return False, str(e)[:120]

    def _call_gemini(self, prompt: str, images_b64: List[str] = None) -> str:
        model = self.model or self._get_default_model()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        parts = [{"text": prompt}]
        if images_b64:
            for img in images_b64:
                parts.append({"inlineData": {"mimeType": img.split(";")[0].replace("data:", ""), "data": img.split(",")[1]}})
        payload = {"contents": [{"parts": parts}], "generationConfig": {"temperature": 0.1, "maxOutputTokens": 2048, "responseMimeType": "application/json"}}
        for attempt in range(5):
            try:
                r = self._session.post(url, json=payload, timeout=60)
                if r.status_code == 200: return r.json()["candidates"][0]["content"]["parts"][0]["text"]
                if r.status_code in (503, 429): time.sleep((attempt + 1) * 3); continue
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
                r = self._session.post(url, headers=headers, json={"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0.1}, timeout=60)
                if r.status_code == 200: return r.json()["choices"][0]["message"]["content"]
                if r.status_code in (429, 503): time.sleep((attempt + 1) * 3); continue
                if r.status_code == 404:
                    info = self.fetch_models_and_limits()
                    if info.get("models") and info["models"][0] != model:
                        model = info["models"][0]; self.model = model; continue
                    raise SolverError(f"Model {model} không khả dụng.")
                raise SolverError(f"{self.provider} {r.status_code}: {r.text[:200]}")
            except requests.exceptions.RequestException as e:
                if attempt == 3: raise SolverError(f"Lỗi mạng: {e}")
                time.sleep((attempt + 1) * 3)
        raise SolverError(f"{self.provider} quá tải.")

    def _get_images(self, html_content: str) -> List[str]:
        m = re.findall(r'<img[^>]+src=["\'](data:image/[^;]+;base64,[^"\']+)["\']', html_content)
        return [x for x in m if len(x) < 4 * 1024 * 1024][:3]

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
            prompt = (f"{role}\nĐề bài: {content}\n\nYÊU CẦU BẮT BUỘC:\n1. Suy luận từng bước.\n2. Nếu đáp số là số thập phân, BẮT BUỘC sử dụng dấu phẩy (,).\n3. Không bao gồm đơn vị.\n4. Chỉ trả về JSON: {{\"answer\": \"<đáp_số>\"}}")

        try:
            if self.provider == "gemini": raw = self._call_gemini(prompt, images_b64)
            elif self.provider == "jev": time.sleep(1.5); return self._solve_jev(question)
            else: raw = self._call_openai_compatible(prompt)
            json_ans = safe_parse_json(raw)
            self.used_today += 1
        except Exception as e:
            raise SolverError(str(e))

        if qtype == "choice":
            ans = str(json_ans.get("answer", "")).upper().strip()
            if len(ans) != 1 or ans not in ("A", "B", "C", "D"):
                m = re.search(r'\b([A-D])\b', raw.upper())
                if not m: raise SolverError(f"AI không trả về đáp án: {raw[:80]}")
                ans = m.group(1)
            idx = ord(ans) - ord('A')
            if idx >= len(question.options): raise SolverError("Đáp án vượt quá số lựa chọn")
            return {"stepId": question.id, "type": "choice", "optionId": question.options[idx]["id"]}
        if qtype == "true_false":
            arr = json_ans.get("answers", [])
            if not isinstance(arr, list) or len(arr) < len(question.options): raise SolverError(f"AI thiếu đáp án Đ/S: {raw[:80]}")
            return {"stepId": question.id, "type": "true_false", "choices": [str(x).lower() for x in arr[:len(question.options)]]}
        text = str(json_ans.get("answer", "")).strip()
        if not text: raise SolverError(f"AI không trả về đáp số: {raw[:80]}")
        text = re.sub(r'(\d)\.(\d)', r'\1,\2', text)
        return {"stepId": question.id, "type": "text", "text": text}

    def _solve_jev(self, question: Any) -> Dict[str, Any]:
        def _q(labels, text):
            url = f"https://classifier.dev/{','.join(labels)}/{urllib.parse.quote(text[:800], safe='')}"
            try:
                r = self._session.get(url, timeout=20)
                return r.text.strip() if r.status_code == 200 else labels[0]
            except Exception: return labels[0]
        if question.qtype == "choice":
            opts = "\n".join([f"{chr(65+i)}. {clean_display_text(o['text'])}" for i, o in enumerate(question.options)])
            pred = _q(["A", "B", "C", "D"][:len(question.options)], f"Câu hỏi: {question.content}\n{opts}")
            for l in ["A", "B", "C", "D"]:
                if l in pred.upper():
                    idx = ord(l) - ord('A')
                    if idx < len(question.options): return {"stepId": question.id, "type": "choice", "optionId": question.options[idx]["id"]}
            return {"stepId": question.id, "type": "choice", "optionId": question.options[0]["id"]}
        if question.qtype == "true_false":
            res = [_q(["Dung", "Sai"], f"Đề: {question.content}\nNhận định: {s['text']}") for s in question.options]
            return {"stepId": question.id, "type": "true_false", "choices": ["true" if "dung" in r.lower() else "false" for r in res]}
        return {"stepId": question.id, "type": "text", "text": "1"}
'''

# ============================================================
# 3. gui.py — GIỮ NGUYÊN GIAO DIỆN GỐC
# ============================================================
# Chúng ta sẽ không ghi đè gui.py vì giao diện hiện tại của bạn đã ổn.
# Chỉ cập nhật các file logic bên dưới.

# ============================================================
# TIẾN TRÌNH GHI FILE
# ============================================================
def write_all_files():
    print("=" * 64)
    print(" FIX V6.7 — ĐỒNG BỘ 100% API TỪ TOOL_ONLUYEN (LẤY ĐỦ 31 CÂU)")
    print("=" * 64)
    
    for name, content in FILES.items():
        path = BASE_DIR / name
        if path.exists():
            backup = path.with_suffix(path.suffix + ".bak")
            backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  [BAK ] {backup.name}")
        path.write_text(content, encoding="utf-8")
        print(f"  [OK  ] {name}")
    
    print("\n" + "=" * 64)
    print(" HOÀN TẤT! Đã sửa lỗi bỏ sót câu hỏi bằng cách áp dụng đúng logic gốc.")
    print(" Chạy: python main.py")
    print("=" * 64)

if __name__ == "__main__":
    write_all_files()