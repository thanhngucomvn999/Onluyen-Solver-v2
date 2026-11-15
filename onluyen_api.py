import re
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
