<div align="center">

# 🚀 ONLUYEN AI PRO - SOLVER

**Hệ thống tự động hóa giải bài tập Onluyen.vn thế hệ mới**

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![CustomTkinter](https://img.shields.io/badge/UI-CustomTkinter-3B82F6?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![AI Powered](https://img.shields.io/badge/AI-Gemini%20%7C%20Groq%20%7C%20Mistral-success?style=for-the-badge)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

[ Tính năng ](#-tính-năng-nổi-bật) • [ Cài đặt ](#-hướng-dẫn-cài-đặt) • [ Sử dụng ](#-hướng-dẫn-sử-dụng) • [ Đóng góp ](#-đóng-góp)

</div>

---

## 🌟 Giới thiệu

**Onluyen AI Pro** là một công cụ hỗ trợ học tập mạnh mẽ, giao diện Dashboard hiện đại, giúp tự động hóa việc giải và nộp bài tập trên hệ thống Onluyen.vn. Với sức mạnh của các mô hình ngôn ngữ lớn (LLMs) hàng đầu, công cụ không chỉ đưa ra đáp án mà còn phân tích từng bước để đảm bảo độ chính xác cao nhất.

## ✨ Tính năng nổi bật

- 🎨 **Giao diện Dashboard Hiện đại**: Thiết kế Dark Mode tuyệt đẹp, trực quan, dễ thao tác với CustomTkinter.
- ⏱️ **Đồng hồ Real-time**: Theo dõi thời gian làm bài theo thời gian thực, không bị giật lag khi AI đang xử lý.
- 🤖 **Đa dạng AI Provider**: Hỗ trợ Google Gemini (Khuyên dùng), Groq, OpenRouter, Mistral. Tự động chuyển đổi model nếu bị lỗi 404.
- 🔄 **Chống lỗi 503 (Quá tải)**: Tự động thử lại (Retry) với cơ chế chờ thông minh khi server AI quá tải.
- 🖼️ **Xử lý ảnh (Multimodal)**: Tự động trích xuất ảnh trong đề bài (hình học, biểu đồ) và gửi cho AI phân tích (Áp dụng cho Gemini).
- 💾 **Tự động lưu trữ**: Tự động lưu tài khoản, cấu hình API và tiến trình làm bài. Không bao giờ lo mất dữ liệu.
- 📊 **Xem lại lịch sử**: Quản lý danh sách bài đã nộp và điểm số ngay trên app.
- 🛡️ **Bảo mật**: File cấu hình chứa thông tin cá nhân được tự động ẩn khỏi Git (`.gitignore`).

## 📸 Hình ảnh minh họa

**
> *Ví dụ:*
<img width="1364" height="731" alt="image" src="https://github.com/user-attachments/assets/8a0b07e0-c5e3-4846-9fe3-a114f4546ee6" />


## 🛠️ Hướng dẫn cài đặt

**Yêu cầu:** Máy tính đã cài đặt Python 3.9 trở lên.

1. **Clone repository này về máy:**
   ```bash
   git clone https://github.com/TEN_GITHUB_CUA_BAN/Onluyen-Solver.git
   cd Onluyen-Solver
