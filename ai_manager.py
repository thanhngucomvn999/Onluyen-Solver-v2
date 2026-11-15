import time
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Optional
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

class AIManager:
    PROVIDERS = {
        "gemini": {"check_url": "https://generativelanguage.googleapis.com/v1beta/models", "auth_param": "key", "default_model": "gemini-1.5-flash", "rpm": 15, "rpd": 1500},
        "groq": {"check_url": "https://api.groq.com/openai/v1/models", "auth_header": "Authorization", "auth_prefix": "Bearer ", "default_model": "llama-3.1-8b-instant", "rpm": 30, "rpd": 14400},
        "openrouter": {"check_url": "https://openrouter.ai/api/v1/models", "auth_header": "Authorization", "auth_prefix": "Bearer ", "default_model": "google/gemma-2-9b-it:free", "rpm": 20, "rpd": 50},
        "mistral": {"check_url": "https://api.mistral.ai/v1/models", "auth_header": "Authorization", "auth_prefix": "Bearer ", "default_model": "open-mistral-nemo", "rpm": 60, "rpd": 1000},
        "jev": {"check_url": None, "default_model": "jev-classifier", "rpm": 100, "rpd": 10000}
    }

    def __init__(self):
        self.keys: List[AIKey] = []
        self.load_keys()

    def load_keys(self):
        self.keys = []
        if os.path.exists(KEYS_FILE):
            try:
                with open(KEYS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        k = AIKey(
                            provider=item.get("provider"),
                            key=item.get("key"),
                            model=item.get("model"),
                            valid=True,
                            daily_limit=self.PROVIDERS.get(item.get("provider"), {}).get("rpd", 1500)
                        )
                        self.keys.append(k)
            except Exception:
                pass
        self.keys.append(AIKey(provider="jev", key="free", model="jev-classifier", valid=True, daily_limit=10000))

    def save_keys(self):
        data = []
        for k in self.keys:
            if k.provider != "jev":
                data.append({"provider": k.provider, "key": k.key, "model": k.model})
        with open(KEYS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def add_key(self, provider: str, key: str, model: Optional[str] = None) -> bool:
        if provider not in self.PROVIDERS:
            raise ValueError(f"Nhà cung cấp '{provider}' không được hỗ trợ.")
            
        use_model = model if model else self.PROVIDERS[provider]["default_model"]
        ai_key = AIKey(provider=provider, key=key.strip(), model=use_model)
        
        if provider != "jev": 
            self._validate_key(ai_key)
        else: 
            ai_key.valid = True
            ai_key.daily_limit = self.PROVIDERS["jev"]["rpd"]
            
        self.keys.append(ai_key)
        self.save_keys()
        return ai_key.valid

    def remove_key(self, index: int):
        if 0 <= index < len(self.keys) and self.keys[index].provider != "jev":
            self.keys.pop(index)
            self.save_keys()

    def _validate_key(self, ai_key: AIKey) -> bool:
        cfg = self.PROVIDERS[ai_key.provider]
        try:
            headers, params = {}, {}
            if "auth_param" in cfg: params[cfg["auth_param"]] = ai_key.key
            if "auth_header" in cfg: headers[cfg["auth_header"]] = cfg.get("auth_prefix", "") + ai_key.key
            
            resp = requests.get(cfg["check_url"], headers=headers, params=params, timeout=25)
            if resp.status_code == 200:
                ai_key.valid = True
                ai_key.last_error = None
                ai_key.daily_limit = cfg["rpd"]
                return True
            else:
                ai_key.valid = False
                ai_key.last_error = f"HTTP {resp.status_code}"
                return False
        except Exception as e:
            ai_key.valid = False
            ai_key.last_error = str(e)
            return False

    def get_best_key(self, preferred_provider: Optional[str] = None) -> Optional[AIKey]:
        valid = [k for k in self.keys if k.valid and k.used_today < k.daily_limit]
        if not valid: return None
        if preferred_provider:
            preferred = [k for k in valid if k.provider == preferred_provider]
            if preferred: return preferred[0]
        
        priority = {"gemini": 0, "groq": 1, "mistral": 2, "openrouter": 3, "jev": 99}
        valid.sort(key=lambda k: (priority.get(k.provider, 50), k.used_today))
        return valid[0]

    def mark_used(self, ai_key: AIKey, success: bool = True, error: str = ""):
        ai_key.used_today += 1
        if not success: ai_key.last_error = error

    def get_status(self) -> List[Dict]:
        return [{"provider": k.provider, "model": k.model, "valid": k.valid, "used": k.used_today, "limit": k.daily_limit, "error": k.last_error} for k in self.keys]
