<div align="center">

# 🚀 ONLUYEN AI PRO - DASHBOARD SOLVER

**Hệ thống tự động hóa giải và nộp bài tập Onluyen.vn thế hệ mới**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-3B82F6?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![AI Powered](https://img.shields.io/badge/AI-Gemini%20%7C%20Groq%20%7C%20Mistral-success?style=for-the-badge)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

*Công cụ hỗ trợ học tập - Tăng tốc độ làm bài - Tối ưu hóa điểm số*

</div>

---

## 🌟 Giới thiệu

**Onluyen AI Pro** là một phần mềm Desktop được phát triển bằng Python, mang đến giải pháp toàn diện cho việc học tập trực tuyến. Với giao diện Dashboard hiện đại, ứng dụng không chỉ giúp bạn quản lý danh sách bài tập mà còn tích hợp sức mạnh của các Mô hình Ngôn ngữ Lớn (LLMs) hàng đầu như **Google Gemini, Groq, Mistral** để tự động giải các dạng bài từ trắc nghiệm, đúng/sai đến điền số.

## ✨ Tính năng nổi bật

- 🎨 **Giao diện Dashboard Hiện đại**: Chế độ Dark Mode dịu mắt, dễ thao tác.
- ⏱️ **Đồng hồ Real-time**: Bộ đếm thời gian làm bài chạy mượt mà, không bị khựng.
- 🤖 **Đa dạng AI Provider**: Hỗ trợ Google Gemini (Khuyên dùng), Groq, Mistral, OpenRouter.
- 🔄 **Tự động sửa lỗi 404 & 503**: Tự động tìm Model mới và Retry khi server AI quá tải.
- 🖼️ **Xử lý ảnh (Multimodal)**: Tự động trích xuất hình ảnh đề bài gửi cho Gemini phân tích.
- 💾 **Lưu trữ Cục bộ**: Tự động lưu Tài khoản, API Key và lịch sử làm bài.

---

## 🛠️ Hướng dẫn Cài đặt

### Bước 1: Cài đặt Python (Bắt buộc)
Nếu máy bạn chưa có Python, hãy tải và cài đặt:
- **Windows:** Tải tại [python.org/downloads](https://www.python.org/downloads/). *(Lưu ý: Khi cài nhớ tích chọn **"Add python.exe to PATH"**)*.
- **macOS:** Tải tại [python.org/downloads/macos](https://www.python.org/downloads/macos/).
- **Linux (Ubuntu/Debian):** Mở Terminal và chạy lệnh:
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip python3-venv python3-tk
Bước 2: Tải mã nguồn dự án
Bạn có 2 cách để lấy code về máy:

Cách 1: Tải file ZIP (Dành cho người mới)

Bấm vào nút màu xanh <> Code ở góc phải trang GitHub này.

Chọn Download ZIP.

Giải nén file ZIP vừa tải, bạn sẽ được một thư mục chứa code.

Cách 2: Sử dụng Git Clone (Dành cho Dev)
Mở Command Prompt (Windows) hoặc Terminal (macOS/Linux) và chạy lệnh:

bash
git clone https://github.com/thanhngucomvn999/Onluyen-Solver-v2.git
cd Onluyen-Solver-v2
Bước 3: Cài đặt Thư viện & Khởi chạy
Mở Command Prompt/Terminal ngay tại thư mục chứa code và chạy lần lượt các lệnh sau:

1. Tạo môi trường ảo (Khuyên dùng):

Windows:

bash
python -m venv venv
venv\Scripts\activate
macOS / Linux:

bash
python3 -m venv venv
source venv/bin/activate
2. Cài đặt thư viện:

bash
pip install -r requirements.txt
3. Khởi chạy Ứng dụng:

bash
python main.py
(Nếu dùng macOS/Linux mà lệnh python không nhận, hãy thử python3 main.py).

📖 Hướng dẫn Sử dụng
Đăng nhập: Mở app, nhập Email/SĐT và Mật khẩu Onluyen.

Cấu hình AI:

Lấy API Key miễn phí tại Google AI Studio.

Vào tab Cấu hình AI, chọn gemini, dán Key và bấm Test Key -> Thêm Key.

Giải bài:

Vào tab Bài tập, chọn bài và bấm Làm bài.

Chọn chế độ AI Mạnh (dùng Key) hoặc Miễn phí (Jev).

Theo dõi tiến trình, hệ thống sẽ tự động giải và nộp bài.

(Mẹo: Vào tab Cài đặt để hẹn giờ nộp bài giống người thật).

🚑 Xử lý Lỗi Thường Gặp
Lỗi 404: Model Not Found (Gemini): Google ngừng cung cấp model cũ. Hệ thống đã tự động tìm model thay thế. Hãy vào Cấu hình AI bấm Test Key lại.

Lỗi 503: Server Quá Tải: Hệ thống đã tự động chờ và thử lại (Retry 5 lần). Nếu vẫn lỗi, hãy chờ 1-2 phút rồi chạy lại.

Lỗi 429: Hết hạn mức: Key Gemini miễn phí giới hạn 15 lượt/phút. Vào Cài đặt, chọn "Cố định thời gian mỗi câu" (VD: 5 giây) để giãn cách.

Nộp bài thất bại (Nộp nhanh quá): Onluyen yêu cầu làm bài tối thiểu 3 phút. Vào Cài đặt, chọn chế độ "Tự động nộp bài (đảm bảo đủ 3 phút)".

⚠️ Tuyên bố Miễn trừ Trách nhiệm
DỰ ÁN NÀY ĐƯỢC TẠO RA VỚI MỤC ĐÍCH HỌC TẬP VÀ NGHIÊN CỨU CÔNG NGHỆ AI.

Tác giả không chịu trách nhiệm cho bất kỳ hành vi vi phạm quy chế thi cử, gian lận học tập hoặc các hậu quả pháp lý nào phát sinh từ việc sử dụng công cụ này. Vui lòng sử dụng một cách có trách nhiệm.

<div align="center"> <b>Phát triển bởi <a href="https://github.com/thanhngucomvn999">thanhngucomvn999</a></b><br> <i>Nếu dự án này giúp ích cho bạn, đừng ngần ngại tặng mình 1 ⭐ (Star) nhé! ❤️</i> </div> ```
