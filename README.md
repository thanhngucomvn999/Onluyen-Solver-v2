# Onluyen Python Solver GUI

Ung dung desktop Python de dang nhap Onluyen, lay cau hoi va giai bang AI mien phi.

## Che do hoat dong
- Che do 1 - API thuan: Goi truc tiep API Onluyen, toc do cao, khong can trinh duyet.
- Che do 2 - Trinh duyet: Dieu khien Chromium qua Playwright, phu hop cau hoi phuc tap.

## AI mien phi ho tro
- Google Gemini (1500 request/ngay)
- Groq (30 RPM, 14400 RPD)
- OpenRouter (model :free)

## Cai dat
pip install -r requirements.txt
playwright install chromium

## Chay
python main.py

## Luu y
- Endpoint Onluyen co the thay doi. Neu gap loi, mo DevTools (F12) tren app.onluyen.vn de kiem tra.
- Selector CSS trong onluyen_browser.py chi la vi du, can cap nhat theo giao dien hien tai.
- Khong su dung de gian lan trong kiem tra chinh thuc.
