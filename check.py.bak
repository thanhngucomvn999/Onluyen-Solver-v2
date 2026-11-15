import requests

def check_api(provider, api_key):
    provider = provider.lower().strip()
    api_key = api_key.strip()

    if provider == "xai" and not api_key.startswith("xai-"):
        print(f"[X] Key xAI phải bắt đầu 'xai-'. Bạn nhập '{api_key[:4]}...'")
        return
    if provider == "groq" and not api_key.startswith("gsk_"):
        print(f"[X] Key Groq phải bắt đầu 'gsk_'. Bạn nhập '{api_key[:4]}...'")
        return
    if provider == "jev":
        print("[OK] Jev không cần API Key.")
        return

    print(f"\n[...] Đang kiểm tra {provider.upper()}...")

    cfg = {
        "gemini":     {"models_url": f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
                       "chat_url":   f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={api_key}",
                       "headers": {"Content-Type": "application/json"},
                       "payload": {"contents": [{"parts": [{"text": "Hi"}]}]},
                       "is_gemini": True},
        "groq":       {"models_url": "https://api.groq.com/openai/v1/models",
                       "chat_url":   "https://api.groq.com/openai/v1/chat/completions",
                       "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                       "payload": {"model": "qwen/qwen3.8-27b", "messages": [{"role": "user", "content": "Hi"}]}},
        "xai":        {"models_url": "https://api.x.ai/v1/models",
                       "chat_url":   "https://api.x.ai/v1/chat/completions",
                       "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                       "payload": {"model": "grok-4.7", "messages": [{"role": "user", "content": "Hi"}]}},
        "openai":     {"models_url": "https://api.openai.com/v1/models",
                       "chat_url":   "https://api.openai.com/v1/chat/completions",
                       "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                       "payload": {"model": "gpt-4.1-mini", "messages": [{"role": "user", "content": "Hi"}]}},
        "openrouter": {"models_url": "https://openrouter.ai/api/v1/models",
                       "chat_url":   "https://openrouter.ai/api/v1/chat/completions",
                       "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                       "payload": {"model": "openrouter/free", "messages": [{"role": "user", "content": "Hi"}]}},
        "mistral":    {"models_url": "https://api.mistral.ai/v1/models",
                       "chat_url":   "https://api.mistral.ai/v1/chat/completions",
                       "headers": {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                       "payload": {"model": "mistral-small-latest", "messages": [{"role": "user", "content": "Hi"}]}},
    }.get(provider)

    if not cfg:
        print(f"[X] Provider '{provider}' không hỗ trợ.")
        return

    try:
        print("[1/2] Lấy danh sách model...")
        r = requests.get(cfg["models_url"], headers=cfg["headers"], timeout=30)
        if r.status_code != 200:
            print(f"   [X] HTTP {r.status_code}: {r.text[:200]}")
            return
        if cfg.get("is_gemini"):
            models = [m["name"].replace("models/", "") for m in r.json().get("models", [])]
        else:
            models = [m["id"] for m in r.json().get("data", [])]
        print(f"   [OK] {len(models)} model. 5 đầu: {', '.join(models[:5])}")
    except requests.exceptions.Timeout:
        print("   [X] Timeout 30s."); return
    except Exception as e:
        print(f"   [X] {e}"); return

    try:
        print("\n[2/2] Ping chat...")
        r = requests.post(cfg["chat_url"], headers=cfg["headers"], json=cfg["payload"], timeout=30)
        if r.status_code == 200: print("   [OK] Chat thành công.")
        elif r.status_code == 429: print("   [!] Hết rate limit (429).")
        elif r.status_code == 402: print("   [!] Hết tiền (402).")
        else: print(f"   [X] HTTP {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"   [X] Lỗi mạng: {e}")


if __name__ == "__main__":
    print("=" * 50)
    print(" KIỂM TRA API KEY ONLUYEN (15/11/2026)")
    print("=" * 50)
    print("Hỗ trợ: gemini, groq, xai, openai, openrouter, mistral")
    p = input("\nProvider: ").strip()
    k = input("API Key: ").strip()
    if p and k: check_api(p, k)
    print("\n" + "=" * 50)
    input("Enter để thoát...")
