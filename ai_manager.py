import time
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import requests

KEYS_FILE = "api_keys.json"

@dataclass
class AIKey:
    provider: str
    key: str
    model: str = ""
    valid: bool = False
    last_checked: float = 0.0
    daily_limit: int = 0
    used_today: int = 0
    last_error: Optional[str] = None
    last_date: str = ""
    is_free: bool = False

class AIManager:
    PROVIDERS = {
        "groq":       {"check_url": "https://api.groq.com/openai/v1/models", "auth_header": "Authorization",
                       "auth_prefix": "Bearer ", "default_model": "qwen/qwen3.8-27b",
                       "rpm": 30, "rpd": 1000, "is_free": True},
        "gemini":     {"check_url": "https://generativelanguage.googleapis.com/v1beta/models",
                       "auth_param": "key", "default_model": "gemini-3.8-flash",
                       "rpm": 15, "rpd": 1500, "is_free": True},
        "openrouter": {"check_url": "https://openrouter.ai/api/v1/models", "auth_header": "Authorization",
                       "auth_prefix": "Bearer ", "default_model": "openrouter/free",
                       "rpm": 20, "rpd": 50, "is_free": True},
        "mistral":    {"check_url": "https://api.mistral.ai/v1/models", "auth_header": "Authorization",
                       "auth_prefix": "Bearer ", "default_model": "mistral-small-latest",
                       "rpm": 60, "rpd": 1000, "is_free": True},
        "xai":        {"check_url": "https://api.x.ai/v1/models", "auth_header": "Authorization",
                       "auth_prefix": "Bearer ", "default_model": "grok-4.7",
                       "rpm": 60, "rpd": 1000, "is_free": False},
        "openai":     {"check_url": "https://api.openai.com/v1/models", "auth_header": "Authorization",
                       "auth_prefix": "Bearer ", "default_model": "gpt-4.1-mini",
                       "rpm": 60, "rpd": 10000, "is_free": False},
        "jev":        {"check_url": None, "default_model": "jev-classifier",
                       "rpm": 100, "rpd": 10000, "is_free": True},
    }

    def __init__(self):
        self.keys: List[AIKey] = []
        self.load_keys()

    def load_keys(self):
        self.keys = []
        today = datetime.now().strftime("%Y-%m-%d")
        if os.path.exists(KEYS_FILE):
            try:
                with open(KEYS_FILE, "r", encoding="utf-8") as f:
                    for item in json.load(f):
                        cfg = self.PROVIDERS.get(item.get("provider"), {})
                        k = AIKey(
                            provider=item.get("provider"),
                            key=item.get("key"),
                            model=item.get("model") or cfg.get("default_model", ""),
                            valid=True,
                            daily_limit=cfg.get("rpd", 1500),
                            used_today=item.get("used_today", 0),
                            last_date=item.get("last_date", ""),
                            is_free=cfg.get("is_free", False),
                        )
                        if k.last_date != today:
                            k.used_today = 0; k.last_date = today
                        self.keys.append(k)
            except Exception:
                pass
        self.keys.append(AIKey(provider="jev", key="free", model="jev-classifier",
                                valid=True, daily_limit=10000, is_free=True, last_date=today))

    def save_keys(self):
        data = [{"provider": k.provider, "key": k.key, "model": k.model,
                 "used_today": k.used_today, "last_date": k.last_date}
                for k in self.keys if k.provider != "jev"]
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def add_key(self, provider: str, key: str, model: Optional[str] = None) -> bool:
        if provider not in self.PROVIDERS:
            raise ValueError(f"Provider '{provider}' không hỗ trợ.")
        cfg = self.PROVIDERS[provider]
        ai_key = AIKey(provider=provider, key=key.strip(),
                        model=model if model else cfg["default_model"],
                        is_free=cfg.get("is_free", False),
                        last_date=datetime.now().strftime("%Y-%m-%d"))
        if provider != "jev":
            self._validate_key(ai_key)
        else:
            ai_key.valid = True; ai_key.daily_limit = cfg["rpd"]
        self.keys.append(ai_key); self.save_keys()
        return ai_key.valid

    def remove_key(self, index: int):
        if 0 <= index < len(self.keys) and self.keys[index].provider != "jev":
            self.keys.pop(index); self.save_keys()

    def _validate_key(self, ai_key: AIKey) -> bool:
        cfg = self.PROVIDERS[ai_key.provider]
        try:
            headers, params = {"User-Agent": "Onluyen-Solver/6.0"}, {}
            if "auth_param" in cfg: params[cfg["auth_param"]] = ai_key.key
            if "auth_header" in cfg: headers[cfg["auth_header"]] = cfg.get("auth_prefix", "") + ai_key.key
            r = requests.get(cfg["check_url"], headers=headers, params=params, timeout=10)
            if r.status_code == 200:
                ai_key.valid = True; ai_key.last_error = None
                ai_key.daily_limit = cfg["rpd"]; ai_key.last_checked = time.time()
                return True
            ai_key.valid = False; ai_key.last_error = f"HTTP {r.status_code}"
            return False
        except Exception as e:
            ai_key.valid = False; ai_key.last_error = str(e); return False

    def _reset_if_new_day(self):
        today = datetime.now().strftime("%Y-%m-%d")
        for k in self.keys:
            if k.last_date != today:
                k.used_today = 0; k.last_date = today

    def get_best_key(self, preferred_provider: Optional[str] = None) -> Optional[AIKey]:
        self._reset_if_new_day()
        valid = [k for k in self.keys if k.valid and k.used_today < k.daily_limit]
        if not valid: return None
        if preferred_provider:
            pref = [k for k in valid if k.provider == preferred_provider]
            if pref: return pref[0]
        # Ưu tiên FREE: groq > gemini > openrouter > mistral > jev > openai > xai
        prio = {"groq": 0, "gemini": 1, "openrouter": 2, "mistral": 3,
                "jev": 4, "openai": 10, "xai": 11}
        valid.sort(key=lambda k: (prio.get(k.provider, 50), k.used_today))
        return valid[0]

    def mark_used(self, ai_key: AIKey, success: bool = True, error: str = ""):
        ai_key.used_today += 1
        if not success: ai_key.last_error = error

    def get_status(self) -> List[Dict]:
        return [{"provider": k.provider, "model": k.model, "valid": k.valid,
                 "used": k.used_today, "limit": k.daily_limit,
                 "error": k.last_error, "is_free": k.is_free} for k in self.keys]
