#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PROJECT SETUP FOR GITHUB - V4.0
Tự động dọn dẹp dữ liệu cá nhân và tạo toàn bộ mã nguồn dự án sạch.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# 1. DỌN DẸP DỮ LIỆU CÁ NHÂN TRƯỚC KHI UP GITHUB
def clean_sensitive_data():
    print("[*] Đang dọn dẹp dữ liệu cá nhân (tránh lộ thông tin khi up GitHub)...")
    sensitive_files = [
        ".ai_config.json", 
        ".onluyen_session.json", 
        ".onluyen_accounts.json",
        "api_keys.json"
    ]
    for f in sensitive_files:
        path = BASE_DIR / f
        if path.exists():
            path.unlink()
            print(f"  [-] Đã xóa: {f}")

# 2. NỘI DUNG CÁC FILE
FILES = {}

FILES["requirements.txt"] = """requests>=2.28.0
customtkinter>=5.2.0
python-dotenv>=1.0.0
"""

FILES[".gitignore"] = """__pycache__/
*.pyc
*.pyo
*.pyd
.env
curls.txt
venv/
.venv/
.DS_Store
*.log

# Dữ liệu người dùng (Không được up lên)
.ai_config.json
.onluyen_session.json
.onluyen_accounts.json
api_keys.json
images_cache/
result_*.json
"""

FILES["models.py"] = """from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class Assignment:
    assign_id: str
    title: str
    subject: Optional[str] = None
    completed: bool = False
    status: int = 0
    start_time: int = 0
    score: Optional[float] = None

@dataclass
class Question:
    id: str
    index: int
    content: str
    qtype: str = "choice"
    options: Optional[List[Dict[str, Any]]] = None
    images: Optional[List[str]] = None
    answer: Optional[Any] = None
"""

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
    text = text.replace("\\left", "").replace("\\right", "")
    text = text.replace("\\{", "{").replace("\\}", "}")
    text = re.sub(r'\\frac\{([^}]+)\}\{([^}]+)\}', r'(\1)/(\2)', text)
    text = re.sub(r'\\sqrt\{([^}]+)\}', r'√(\1)', text)
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
            "content-type": "application/json"
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
        resp = self.session.get(f"{self.BASE_API}/school-online/assignment/doing/{assign_id}", timeout=20)
        if resp.status_code == 401: raise SessionExpiredError()
        
        data = resp.json().get("data", {})
        if not data: raise Exception("Không thể tải đề bài. Bài đã nộp hoặc lỗi API.")
        
        self.put_url = data.get("preSignedUrlAnswer", "")
        raw_qs = data.get("data", [])
        
        questions = []
        idx = 1
        for q in raw_qs:
            std = q.get("dataStandard")
            if not std: continue
            vi = std.get("languagesData", {}).get("vi", {})
            ta = std.get("typeAnswer", 0)
            qtype = "true_false" if ta == 1 else ("text" if ta in (3, 5) else "choice")
            
            opts = []
            for o in vi.get("options", []):
                opts.append({"id": o.get("idOption"), "text": clean_html(o.get("content", ""))})
                
            questions.append(Question(
                id=std.get("stepId"), index=idx,
                content=vi.get("content", ""), qtype=qtype, options=opts
            ))
            idx += 1
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
            
        resp = requests.put(self.put_url, json=s3_payload, headers={"Content-Type": "application/json"}, timeout=20)
        return resp.status_code in (200, 204)

    def submit(self, assign_id: str) -> Dict:
        url = f"{self.BASE_API}/school-online/assignment/submit/{assign_id}"
        resp = self.session.put(url, json={}, timeout=15)
        if resp.status_code == 200:
            return {"success": True, "message": "Nộp bài thành công"}
        return {"success": False, "message": f"HTTP {resp.status_code}: {resp.text}"}
'''

FILES["solver.py"] = r'''import re
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
'''

FILES["main.py"] = """from gui import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
"""

# 3. GHI FILE
def write_all_files():
    clean_sensitive_data()
    print("\n[*] Đang tạo cấu trúc dự án sạch cho GitHub...")
    for name, content in FILES.items():
        path = BASE_DIR / name
        path.write_text(content, encoding="utf-8")
        print(f"  [+] Đã tạo: {name}")
    
    print("\n" + "=" * 60)
    print(" HOÀN TẤT! Dự án đã sẵn sàng để đưa lên GitHub.")
    print(" Lưu ý: File gui.py được giữ nguyên (không ghi đè) để bảo toàn giao diện.")
    print(" Hãy chạy lệnh: python main.py để kiểm tra.")
    print("=" * 60)

if __name__ == "__main__":
    write_all_files()