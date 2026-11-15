import requests
import sys

def check_api(provider, api_key):
    provider = provider.lower().strip()
    api_key = api_key.strip()
    
    if provider == "xai" and not api_key.startswith("xai-"):
        print(f"[❌] LỖI ĐỊNH DẠNG: Key của xAI phải bắt đầu bằng 'xai-'. Key bạn nhập bắt đầu bằng '{api_key[:4]}...'")
        print("   -> Hãy tạo key mới tại https://console.x.ai/")
        return
    if provider == "groq" and not api_key.startswith("gsk_"):
        print(f"[❌] LỖI ĐỊNH DẠNG: Key của Groq phải bắt đầu bằng 'gsk_'. Key bạn nhập bắt đầu bằng '{api_key[:4]}...'")
        print("   -> Hãy tạo key mới tại https://console.groq.com/keys")
        return
    
    if provider == "jev":
        print("[✅] Jev Classifier không cần API Key. Luôn sẵn sàng.")
        return

    print(f"\n[⏳] Đang kiểm tra kết nối tới {provider.upper()}...")
    
    if provider == "gemini":
        models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        chat_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": "Hi"}]}]}
    elif provider == "groq":
        models_url = "https://api.groq.com/openai/v1/models"
        chat_url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hi"}]}
    elif provider == "xai":
        models_url = "https://api.x.ai/v1/models"
        chat_url = "https://api.x.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": "grok-4.3", "messages": [{"role": "user", "content": "Hi"}]}
    elif provider == "openai":
        models_url = "https://api.openai.com/v1/models"
        chat_url = "https://api.openai.com/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": "gpt-6-luna", "messages": [{"role": "user", "content": "Hi"}]}
    elif provider == "openrouter":
        models_url = "https://openrouter.ai/api/v1/models"
        chat_url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": "inclusionai/ling-3.0-flash:free", "messages": [{"role": "user", "content": "Hi"}]}
    elif provider == "mistral":
        models_url = "https://api.mistral.ai/v1/models"
        chat_url = "https://api.mistral.ai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": "ministral-3b-2512", "messages": [{"role": "user", "content": "Hi"}]}
    else:
        print(f"[❌] Nhà cung cấp '{provider}' không được hỗ trợ trong script này.")
        return

    try:
        print("[1/2] Đang lấy danh sách model...")
        resp = requests.get(models_url, headers=headers, timeout=30)
        
        if resp.status_code != 200:
            print(f"   [❌] LỖI KEY HOẶC QUYỀN TRUY CẬP: HTTP {resp.status_code}")
            print(f"   Chi tiết: {resp.text[:200]}")
            return
        
        data = resp.json()
        models = []
        if provider == "gemini":
            models = [m["name"].replace("models/", "") for m in data.get("models", [])]
        else:
            models = [m["id"] for m in data.get("data", [])]
            
        print(f"   [✅] Kết nối thành công! Tìm thấy {len(models)} model.")
        print(f"   [ℹ️] 5 model đầu tiên: {', '.join(models[:5])}")
        
    except requests.exceptions.Timeout:
        print("   [❌] LỖI MẠNG: Quá thời gian chờ (Timeout 30s).")
        print("   -> Hãy kiểm tra VPN/Proxy hoặc thử lại sau.")
        return
    except Exception as e:
        print(f"   [❌] LỖI KHÔNG XÁC ĐỊNH: {e}")
        return

    try:
        print("\n[2/2] Đang thử gửi tin nhắn (Ping)...")
        resp_chat = requests.post(chat_url, headers=headers, json=payload, timeout=30)
        
        if resp_chat.status_code == 200:
            print("   [✅] Chat thành công! Key hoàn toàn sử dụng được.")
        elif resp_chat.status_code == 429:
            print("   [⚠️] Key hợp lệ nhưng ĐÃ HẾT HẠN MỨC (Rate Limit 429).")
        elif resp_chat.status_code == 402:
            print("   [⚠️] Key hợp lệ nhưng TÀI KHOẢN HẾT TIỀN (Credit 402).")
        else:
            print(f"   [❌] Lỗi khi chat: HTTP {resp_chat.status_code}")
            print(f"   Chi tiết: {resp_chat.text[:200]}")
            
    except Exception as e:
        print(f"   [❌] Lỗi mạng khi chat: {e}")


if __name__ == "__main__":
    print("="*50)
    print(" CÔNG CỤ KIỂM TRA API KEY ONLUYEN")
    print("="*50)
    print("Hỗ trợ: gemini, groq, xai, openai, openrouter, mistral")
    
    p = input("\nNhập nhà cung cấp (VD: xai): ").strip()
    k = input("Nhập API Key: ").strip()
    
    if not p or not k:
        print("Vui lòng nhập đủ thông tin.")
    else:
        check_api(p, k)
        
    print("\n" + "="*50)
    input("Nhấn Enter để thoát...")
