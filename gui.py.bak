import threading
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import time
import json
import os
import base64
from datetime import datetime
from onluyen_api import OnluyenAPI, SessionExpiredError
from solver import AISolver, clean_display_text

try:
    import customtkinter.windows.widgets.core_widget_classes.ctk_base_class as ctk_base
    original_draw = ctk_base.CTkBaseClass._draw
    def safe_draw(self, *args, **kwargs):
        try: return original_draw(self, *args, **kwargs)
        except tk.TclError: pass
    ctk_base.CTkBaseClass._draw = safe_draw
except Exception: pass

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

BG = "#0F172A"; SIDEBAR = "#1E293B"; CARD = "#1E293B"; HOVER = "#334155"; BORDER = "#334155"
ACCENT = "#3B82F6"; ACCENT_HOVER = "#2563EB"; TEXT_P = "#F8FAFC"; TEXT_S = "#94A3B8"
DANGER = "#EF4444"; SUCCESS = "#10B981"; WARNING = "#F59E0B"

CONFIG_FILE = ".ai_config.json"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Onluyen Solver - Pro Dashboard")
        self.geometry("1280x800")
        self.configure(fg_color=BG)
        
        self.api = OnluyenAPI()
        self.running = False
        self.ai_config = self._load_config()
        
        self.start_time = 0
        self.timer_running = False
        
        self.pacing_mode = ctk.StringVar(value="1")
        self.total_time_minutes = ctk.DoubleVar(value=10.0)
        self.delay_per_question = ctk.DoubleVar(value=5.0)
        self.submit_mode = ctk.StringVar(value="1")
        self.submit_wait_minutes = ctk.DoubleVar(value=3.0)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.pages = {}
        self._build_pages()
        self.show_page("login")
        self.after(100, self._auto_login)

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f: 
                    data = json.load(f)
                    if isinstance(data, dict): return []
                    return data
            except: pass
        return []

    def _save_config(self):
        today = datetime.now().strftime("%Y-%m-%d")
        for cfg in self.ai_config:
            if cfg.get("last_date") != today:
                cfg["used_today"] = 0
                cfg["last_date"] = today
        with open(CONFIG_FILE, "w") as f: json.dump(self.ai_config, f, indent=4)

    def _clear_frame(self, frame):
        for widget in frame.winfo_children():
            try: widget.destroy()
            except Exception: pass

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.grid(row=0, column=0, padx=25, pady=(40, 40), sticky="w")
        ctk.CTkLabel(logo, text="ONLUYEN", font=("Segoe UI", 24, "bold"), text_color=ACCENT).pack(side="left")
        ctk.CTkLabel(logo, text="PRO", font=("Segoe UI", 24), text_color=TEXT_P).pack(side="left", padx=(5,0))

        self.nav_btns = {}
        menus = [("assign", "📚  Bài tập"), ("history", "📊  Bài đã nộp"), ("ai", "🤖  Cấu hình AI"), ("solve", "🚀  Tiến trình"), ("settings", "⚙️  Cài đặt")]
        
        for i, (key, text) in enumerate(menus, start=1):
            btn = ctk.CTkButton(self.sidebar, text=text, font=("Segoe UI", 15), anchor="w", fg_color="transparent", hover_color=HOVER, corner_radius=8, height=45)
            btn.configure(command=lambda k=key: self.show_page(k))
            btn.grid(row=i, column=0, padx=15, pady=5, sticky="ew")
            self.nav_btns[key] = btn

        bottom = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        bottom.grid(row=7, column=0, padx=15, pady=20, sticky="ew")
        
        self.user_frame = ctk.CTkFrame(bottom, fg_color=CARD, corner_radius=8, border_width=1, border_color=BORDER)
        self.user_frame.pack(fill="x")
        
        self.user_btn = ctk.CTkButton(self.user_frame, text="👤 Tài khoản ▾", font=("Segoe UI", 13, "bold"), fg_color="transparent", hover_color=HOVER, height=40, anchor="w")
        self.user_btn.pack(fill="x", padx=2, pady=2)
        self.user_btn.bind("<Button-1>", self._show_user_menu)

        self.user_menu = tk.Menu(self, tearoff=0, bg=CARD, fg=TEXT_P, font=("Segoe UI", 12), activebackground=ACCENT, activeforeground=TEXT_P)
        self.user_menu.add_command(label="Đổi tài khoản", command=self._show_account_manager)
        self.user_menu.add_separator()
        self.user_menu.add_command(label="Đăng xuất", command=self._logout)

        ctk.CTkLabel(bottom, text="v4.0.0 - Stable", font=("Segoe UI", 10), text_color=TEXT_S).pack(pady=(10, 0))

    def _show_user_menu(self, event):
        x = self.user_btn.winfo_rootx()
        y = self.user_btn.winfo_rooty() - 80
        self.user_menu.post(x, y)

    def _build_pages(self):
        # --- LOGIN ---
        self.pages["login"] = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
        left = ctk.CTkFrame(self.pages["login"], fg_color=SIDEBAR, corner_radius=0)
        left.place(relx=0, rely=0, relwidth=0.5, relheight=1)
        ctk.CTkLabel(left, text="Chào mừng đến với\nOnluyen AI Pro", font=("Segoe UI", 38, "bold"), text_color=TEXT_P, justify="left").place(relx=0.5, rely=0.4, anchor="center")
        ctk.CTkLabel(left, text="Tự động hóa - Chính xác - Nhanh chóng", font=("Segoe UI", 16), text_color=TEXT_S).place(relx=0.5, rely=0.5, anchor="center")
        
        right = ctk.CTkFrame(self.pages["login"], fg_color="transparent")
        right.place(relx=0.5, rely=0, relwidth=0.5, relheight=1)
        self.login_form = ctk.CTkFrame(right, fg_color="transparent")
        self.login_form.place(relx=0.5, rely=0.5, anchor="center")
        
        ctk.CTkLabel(self.login_form, text="Đăng nhập", font=("Segoe UI", 28, "bold"), text_color=TEXT_P).pack(anchor="w", pady=(0, 20))
        self.entry_user = ctk.CTkEntry(self.login_form, width=350, height=50, placeholder_text="Email / SĐT", font=("Segoe UI", 14), corner_radius=8, fg_color=BG, border_color=BORDER)
        self.entry_user.pack(pady=10)
        self.entry_pass = ctk.CTkEntry(self.login_form, width=350, height=50, show="*", placeholder_text="Mật khẩu", font=("Segoe UI", 14), corner_radius=8, fg_color=BG, border_color=BORDER)
        self.entry_pass.pack(pady=10)
        
        self.btn_login = ctk.CTkButton(self.login_form, text="Đăng nhập ngay", font=("Segoe UI", 15, "bold"), height=50, corner_radius=8, fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self._do_login)
        self.btn_login.pack(fill="x", pady=20)
        self.lbl_login = ctk.CTkLabel(self.login_form, text="", font=("Segoe UI", 13))
        self.lbl_login.pack()
        
        self.btn_back_login = ctk.CTkButton(self.login_form, text="Quay lại", font=("Segoe UI", 13), fg_color="transparent", hover_color=HOVER, text_color=TEXT_S, command=self._cancel_add_account)

        # --- ASSIGN ---
        self.pages["assign"] = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
        h_assign = ctk.CTkFrame(self.pages["assign"], fg_color="transparent")
        h_assign.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(h_assign, text="Danh sách bài tập", font=("Segoe UI", 26, "bold"), text_color=TEXT_P).pack(side="left")
        ctk.CTkButton(h_assign, text="🔄 Làm mới", width=110, height=38, fg_color=CARD, hover_color=HOVER, text_color=TEXT_P, corner_radius=8, command=self._load_assignments).pack(side="right")
        self.assign_scroll = ctk.CTkScrollableFrame(self.pages["assign"], fg_color="transparent")
        self.assign_scroll.pack(fill="both", expand=True, padx=40, pady=(0, 30))

        # --- HISTORY ---
        self.pages["history"] = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
        h_history = ctk.CTkFrame(self.pages["history"], fg_color="transparent")
        h_history.pack(fill="x", padx=40, pady=(40, 20))
        ctk.CTkLabel(h_history, text="Bài tập đã nộp", font=("Segoe UI", 26, "bold"), text_color=TEXT_P).pack(side="left")
        ctk.CTkButton(h_history, text="🔄 Làm mới", width=110, height=38, fg_color=CARD, hover_color=HOVER, text_color=TEXT_P, corner_radius=8, command=self._load_history).pack(side="right")
        self.history_scroll = ctk.CTkScrollableFrame(self.pages["history"], fg_color="transparent")
        self.history_scroll.pack(fill="both", expand=True, padx=40, pady=(0, 30))

        # --- AI SETTINGS ---
        self.pages["ai"] = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
        ctk.CTkLabel(self.pages["ai"], text="Cấu hình AI Provider", font=("Segoe UI", 26, "bold"), text_color=TEXT_P).pack(anchor="w", padx=40, pady=(40, 20))
        
        add_frame = ctk.CTkFrame(self.pages["ai"], fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER)
        add_frame.pack(fill="x", padx=40, pady=(0, 10))
        
        inner = ctk.CTkFrame(add_frame, fg_color="transparent")
        inner.pack(pady=20, padx=20, fill="x")
        
        row1 = ctk.CTkFrame(inner, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        
        ctk.CTkLabel(row1, text="Provider:", font=("Segoe UI", 14), text_color=TEXT_P).pack(side="left")
        self.provider_var = ctk.StringVar(value="gemini")
        self.opt_provider = ctk.CTkOptionMenu(row1, values=["gemini", "jev", "groq", "openrouter", "mistral"], variable=self.provider_var, fg_color=BG, button_color=HOVER, width=120, command=self._on_provider_change)
        self.opt_provider.pack(side="left", padx=10)
        
        self.lbl_api = ctk.CTkLabel(row1, text="API Key:", font=("Segoe UI", 14), text_color=TEXT_P)
        self.lbl_api.pack(side="left", padx=(10,0))
        
        self.entry_api = ctk.CTkEntry(row1, width=250, height=35, placeholder_text="Nhập API Key...", fg_color=BG, border_color=BORDER)
        self.entry_api.pack(side="left", padx=10)
        
        ctk.CTkLabel(row1, text="Model:", font=("Segoe UI", 14), text_color=TEXT_P).pack(side="left", padx=(10,0))
        self.entry_model = ctk.CTkEntry(row1, width=180, height=35, placeholder_text="Tự động", fg_color=BG, border_color=BORDER)
        self.entry_model.pack(side="left", padx=10)
        
        ctk.CTkButton(row1, text="➕ Thêm Key", width=100, height=35, fg_color=ACCENT, hover_color=ACCENT_HOVER, command=self._add_key).pack(side="left", padx=5)
        ctk.CTkButton(row1, text="🔍 Test Key", width=100, height=35, fg_color=HOVER, border_width=1, border_color=BORDER, command=self._test_api_key).pack(side="left", padx=5)
        
        self.lbl_provider_note = ctk.CTkLabel(inner, text="", font=("Segoe UI", 12, "italic"), text_color=WARNING, justify="left")
        self.lbl_provider_note.pack(fill="x", pady=(5, 0))
        
        self._on_provider_change("gemini")
        
        self.lbl_ai_status = ctk.CTkLabel(self.pages["ai"], text="", font=("Segoe UI", 13), text_color=TEXT_S)
        self.lbl_ai_status.pack(anchor="w", padx=40, pady=(0, 10))

        list_frame = ctk.CTkFrame(self.pages["ai"], fg_color="transparent")
        list_frame.pack(fill="both", expand=True, padx=40)
        ctk.CTkLabel(list_frame, text="Danh sách Key đang hoạt động", font=("Segoe UI", 16, "bold"), text_color=TEXT_P).pack(anchor="w", pady=(10, 10))
        
        self.key_list_frame = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.key_list_frame.pack(fill="both", expand=True)
        self._refresh_key_list()

        # --- SOLVE ---
        self.pages["solve"] = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
        self.info_card = ctk.CTkFrame(self.pages["solve"], fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER)
        self.info_card.pack(fill="x", padx=40, pady=(30, 20))
        info_inner = ctk.CTkFrame(self.info_card, fg_color="transparent")
        info_inner.pack(fill="x", padx=20, pady=15)
        self.lbl_bai_hoc = ctk.CTkLabel(info_inner, text="Chưa chọn bài tập", font=("Segoe UI", 20, "bold"), text_color=TEXT_P, anchor="w")
        self.lbl_bai_hoc.pack(side="left")
        self.lbl_timer = ctk.CTkLabel(info_inner, text="⏱️ 00:00", font=("Consolas", 22, "bold"), text_color=ACCENT)
        self.lbl_timer.pack(side="right")

        progress_frame = ctk.CTkFrame(self.pages["solve"], fg_color="transparent")
        progress_frame.pack(fill="x", padx=40, pady=(0, 10))
        self.lbl_progress = ctk.CTkLabel(progress_frame, text="Đang chờ lệnh...", font=("Segoe UI", 13), text_color=TEXT_S)
        self.lbl_progress.pack(anchor="w")
        self.progress = ctk.CTkProgressBar(progress_frame, height=10, corner_radius=5, progress_color=ACCENT, fg_color=BORDER)
        self.progress.pack(fill="x", pady=5)
        self.progress.set(0)
        
        split_frame = ctk.CTkFrame(self.pages["solve"], fg_color="transparent")
        split_frame.pack(fill="both", expand=True, padx=40, pady=10)
        split_frame.grid_columnconfigure(0, weight=4)
        split_frame.grid_columnconfigure(1, weight=6)
        split_frame.grid_rowconfigure(0, weight=1)
        
        left_log_frame = ctk.CTkFrame(split_frame, fg_color="transparent")
        left_log_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        ctk.CTkLabel(left_log_frame, text="⚡ Tiến trình xử lý", font=("Segoe UI", 14, "bold"), text_color=TEXT_S).pack(anchor="w", pady=(0, 5))
        self.log_box = ctk.CTkTextbox(left_log_frame, font=("Consolas", 13), fg_color="#0B1120", text_color="#A3E635", corner_radius=10, border_width=1, border_color=BORDER)
        self.log_box.pack(fill="both", expand=True)
        
        right_log_frame = ctk.CTkFrame(split_frame, fg_color="transparent")
        right_log_frame.grid(row=0, column=1, sticky="nsew")
        ctk.CTkLabel(right_log_frame, text="🔍 Chi tiết câu hỏi & Đáp án AI", font=("Segoe UI", 14, "bold"), text_color=TEXT_S).pack(anchor="w", pady=(0, 5))
        self.log_detail_box = ctk.CTkTextbox(right_log_frame, font=("Consolas", 13), fg_color="#0B1120", text_color="#60A5FA", corner_radius=10, border_width=1, border_color=BORDER)
        self.log_detail_box.pack(fill="both", expand=True)
        
        self.btn_stop = ctk.CTkButton(self.pages["solve"], text="Dừng tiến trình", fg_color=DANGER, font=("Segoe UI", 14, "bold"), height=45, width=200, corner_radius=8, command=self._stop_solving, state="disabled")
        self.btn_stop.pack(pady=(0, 20))

        # --- SETTINGS ---
        self.pages["settings"] = ctk.CTkFrame(self.content, fg_color=BG, corner_radius=0)
        ctk.CTkLabel(self.pages["settings"], text="Cài đặt thời gian", font=("Segoe UI", 26, "bold"), text_color=TEXT_P).pack(anchor="w", padx=40, pady=(40, 20))
        
        set_card = ctk.CTkFrame(self.pages["settings"], fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER)
        set_card.pack(fill="x", padx=40, pady=10)
        s_inner = ctk.CTkFrame(set_card, fg_color="transparent")
        s_inner.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(s_inner, text="1. Phân bổ thời gian", font=("Segoe UI", 16, "bold"), text_color=TEXT_P).pack(anchor="w", pady=(0, 10))
        ctk.CTkRadioButton(s_inner, text="Giải tốc độ tối đa (làm ngay không chờ)", variable=self.pacing_mode, value="1", font=("Segoe UI", 14)).pack(anchor="w", pady=5)
        f_div = ctk.CTkFrame(s_inner, fg_color="transparent")
        f_div.pack(anchor="w", pady=5)
        ctk.CTkRadioButton(f_div, text="Chia đều tổng thời gian làm bài (phút):", variable=self.pacing_mode, value="2", font=("Segoe UI", 14)).pack(side="left")
        ctk.CTkEntry(f_div, textvariable=self.total_time_minutes, width=60).pack(side="left", padx=10)
        f_fix = ctk.CTkFrame(s_inner, fg_color="transparent")
        f_fix.pack(anchor="w", pady=5)
        ctk.CTkRadioButton(f_fix, text="Cố định thời gian mỗi câu (giây):", variable=self.pacing_mode, value="3", font=("Segoe UI", 14)).pack(side="left")
        ctk.CTkEntry(f_fix, textvariable=self.delay_per_question, width=60).pack(side="left", padx=10)

        ctk.CTkLabel(s_inner, text="2. Chế độ nộp bài", font=("Segoe UI", 16, "bold"), text_color=TEXT_P).pack(anchor="w", pady=(20, 10))
        f_auto = ctk.CTkFrame(s_inner, fg_color="transparent")
        f_auto.pack(anchor="w", pady=5)
        ctk.CTkRadioButton(f_auto, text="Tự động nộp bài sau khi làm xong (đảm bảo đủ 3 phút):", variable=self.submit_mode, value="1", font=("Segoe UI", 14)).pack(side="left")
        f_timed = ctk.CTkFrame(s_inner, fg_color="transparent")
        f_timed.pack(anchor="w", pady=5)
        ctk.CTkRadioButton(f_timed, text="Hẹn giờ nộp bài (đợi đủ số phút):", variable=self.submit_mode, value="2", font=("Segoe UI", 14)).pack(side="left")
        ctk.CTkEntry(f_timed, textvariable=self.submit_wait_minutes, width=60).pack(side="left", padx=10)
        ctk.CTkRadioButton(s_inner, text="KHÔNG nộp bài (Chỉ lưu đáp án lên server)", variable=self.submit_mode, value="3", font=("Segoe UI", 14)).pack(anchor="w", pady=5)

    # --- LOGIC ĐIỀU HƯỚNG ---
    def show_page(self, name):
        for p in self.pages.values(): p.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        for k, btn in self.nav_btns.items():
            btn.configure(fg_color=HOVER if k == name else "transparent")

    def _auto_login(self):
        if self.api.auto_login():
            self._login_success()

    def _do_login(self):
        u, p = self.entry_user.get().strip(), self.entry_pass.get().strip()
        if not u or not p:
            self.lbl_login.configure(text="Vui lòng nhập đủ Email/SĐT và Mật khẩu", text_color=DANGER)
            return
        self.btn_login.configure(state="disabled", text="Đang xử lý...")
        def task():
            try:
                self.api.login(u, p)
                self.after(0, self._login_success)
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: self.lbl_login.configure(text=err_msg, text_color=DANGER))
                self.after(0, lambda: self.btn_login.configure(state="normal", text="Đăng nhập ngay"))
        threading.Thread(target=task, daemon=True).start()

    def _login_success(self):
        self.btn_login.configure(state="normal", text="Đăng nhập ngay")
        name = self.api.display_name or self.api.email
        self.user_btn.configure(text=f"👤 {name} ▾")
        if hasattr(self, 'account_dialog') and self.account_dialog.winfo_exists():
            self.account_dialog.destroy()
        self.show_page("assign")
        self._load_assignments()

    def _logout(self):
        self.api.logout()
        self.user_btn.configure(text="👤 Tài khoản ▾")
        self.show_page("login")

    def _load_assignments(self):
        self._clear_frame(self.assign_scroll)
        ctk.CTkLabel(self.assign_scroll, text="Đang tải...", text_color=TEXT_S).pack(pady=30)
        def task():
            try:
                try: assigns = self.api.get_assignments(filter_status="todo")
                except TypeError:
                    assigns = self.api.get_assignments()
                    assigns = [a for a in assigns if getattr(a, 'status', 0) not in (2, 3) and not getattr(a, 'completed', False)]
                if self.pages["assign"].winfo_exists(): self.after(0, lambda: self._render_assignments(assigns))
            except SessionExpiredError:
                self.after(0, lambda: messagebox.showerror("Hết phiên", "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại."))
                self.after(0, self._logout)
            except Exception as e:
                err_msg = str(e)
                if self.pages["assign"].winfo_exists():
                    self.after(0, lambda: ctk.CTkLabel(self.assign_scroll, text=f"Lỗi: {err_msg}", text_color=DANGER).pack())
        threading.Thread(target=task, daemon=True).start()

    def _render_assignments(self, assigns):
        self._clear_frame(self.assign_scroll)
        if not assigns:
            ctk.CTkLabel(self.assign_scroll, text="Không có bài tập nào chưa làm.", text_color=TEXT_S).pack(pady=30)
            return
        for a in assigns:
            card = ctk.CTkFrame(self.assign_scroll, fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER)
            card.pack(fill="x", pady=8, padx=10)
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", padx=20, pady=15, fill="x", expand=True)
            ctk.CTkLabel(info, text=a.title, font=("Segoe UI", 16, "bold"), text_color=TEXT_P, anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"Môn: {a.subject}", font=("Segoe UI", 13), text_color=TEXT_S, anchor="w").pack(fill="x")
            ctk.CTkButton(card, text="Làm bài", width=100, height=38, fg_color=ACCENT, hover_color=ACCENT_HOVER, corner_radius=8, command=lambda title=a.title, id=a.assign_id: self._show_mode_dialog(title, id)).pack(side="right", padx=20)

    def _load_history(self):
        self._clear_frame(self.history_scroll)
        ctk.CTkLabel(self.history_scroll, text="Đang tải...", text_color=TEXT_S).pack(pady=30)
        def task():
            try:
                try: assigns = self.api.get_assignments(filter_status="done")
                except TypeError:
                    assigns = self.api.get_assignments()
                    assigns = [a for a in assigns if getattr(a, 'status', 0) in (2, 3) or getattr(a, 'completed', False)]
                if self.pages["history"].winfo_exists(): self.after(0, lambda: self._render_history(assigns))
            except SessionExpiredError:
                self.after(0, lambda: messagebox.showerror("Hết phiên", "Phiên đăng nhập đã hết hạn."))
                self.after(0, self._logout)
            except Exception as e:
                err_msg = str(e)
                if self.pages["history"].winfo_exists():
                    self.after(0, lambda: ctk.CTkLabel(self.history_scroll, text=f"Lỗi: {err_msg}", text_color=DANGER).pack())
        threading.Thread(target=task, daemon=True).start()

    def _render_history(self, assigns):
        self._clear_frame(self.history_scroll)
        if not assigns:
            ctk.CTkLabel(self.history_scroll, text="Chưa có bài tập nào đã nộp.", text_color=TEXT_S).pack(pady=30)
            return
        for a in assigns:
            card = ctk.CTkFrame(self.history_scroll, fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER)
            card.pack(fill="x", pady=8, padx=10)
            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(side="left", padx=20, pady=15, fill="x", expand=True)
            ctk.CTkLabel(info, text=a.title, font=("Segoe UI", 16, "bold"), text_color=TEXT_P, anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"Môn: {a.subject}", font=("Segoe UI", 13), text_color=TEXT_S, anchor="w").pack(fill="x")
            score = getattr(a, 'score', None) or getattr(a, 'totalScore', None)
            score_str = f"{score}/10" if score is not None else "Đã nộp"
            ctk.CTkLabel(card, text=score_str, font=("Segoe UI", 18, "bold"), text_color=SUCCESS).pack(side="right", padx=20)

    def _on_provider_change(self, choice):
        if choice == "jev":
            self.entry_api.configure(state="disabled", placeholder_text="Không cần API Key")
            self.lbl_api.configure(text="API Key (Miễn phí):")
        else:
            self.entry_api.configure(state="normal", placeholder_text="Nhập API Key...")
            self.lbl_api.configure(text="API Key:")
        notes = {
            "gemini": "🔗 generativelanguage.googleapis.com | Khuyên dùng model: gemini-1.5-flash",
            "groq": "🔗 api.groq.com | Lấy key tại console.groq.com",
            "openrouter": "🔗 openrouter.ai | Key bắt đầu bằng 'sk-or-...'",
            "mistral": "🔗 api.mistral.ai | Key lấy từ console.mistral.ai",
            "jev": "🔗 classifier.dev | Miễn phí, độ chính xác thấp, không cần API Key"
        }
        if hasattr(self, 'lbl_provider_note'): self.lbl_provider_note.configure(text=notes.get(choice, ""))

    def _log_ui(self, msg, color=TEXT_S):
        if hasattr(self, 'lbl_ai_status') and self.lbl_ai_status.winfo_exists():
            self.after(0, lambda: self.lbl_ai_status.configure(text=msg, text_color=color))

    def _test_api_key(self):
        p, k = self.provider_var.get(), self.entry_api.get().strip()
        if p != "jev" and not k: return messagebox.showwarning("Thiếu Key", "Vui lòng nhập API Key để test.")
        self._log_ui("Đang kiểm tra Key...", ACCENT)
        def task():
            solver = AISolver(p, k)
            info = solver.fetch_models_and_limits()
            if "error" in info: return self.after(0, lambda: self._log_ui(f"Lỗi: {info['error']}", DANGER))
            models = info.get("models", [])
            if not models and p != "jev": return self.after(0, lambda: self._log_ui("Key hợp lệ nhưng không lấy được model.", DANGER))
            best_model = models[0] if models else ""
            self.after(0, lambda: self.entry_model.delete(0, "end") or self.entry_model.insert(0, best_model))
            self.after(0, lambda: self._log_ui(f"✅ Key OK! Model khuyên dùng: {best_model}", SUCCESS))
        threading.Thread(target=task, daemon=True).start()

    def _add_key(self):
        p, k, m = self.provider_var.get(), self.entry_api.get().strip(), self.entry_model.get().strip()
        if p != "jev" and not k: return messagebox.showerror("Lỗi", "Vui lòng nhập API Key.")
        self._log_ui("Đang xác thực và thêm Key...", ACCENT)
        def task():
            solver = AISolver(p, k, m)
            info = solver.fetch_models_and_limits()
            if "error" in info: return self.after(0, lambda: self._log_ui(f"Lỗi: {info['error']}", DANGER))
            final_model = m if m else (info["models"][0] if info["models"] else solver._get_default_model())
            solver.model = final_model
            is_ready, quota_msg = solver.check_quota()
            def update_ui():
                today = datetime.now().strftime("%Y-%m-%d")
                self.ai_config.append({"provider": p, "api_key": k, "model": final_model, "valid": is_ready, "status_msg": quota_msg, "limits": info["limits"], "used_today": 0, "last_date": today})
                self._save_config()
                self._refresh_key_list()
                self.entry_api.delete(0, "end")
                self.entry_model.delete(0, "end")
                self._log_ui(f"Thêm thành công! Trạng thái: {quota_msg}", SUCCESS if is_ready else WARNING)
            self.after(0, update_ui)
        threading.Thread(target=task, daemon=True).start()

    def _refresh_key_list(self):
        self._clear_frame(self.key_list_frame)
        if not self.ai_config:
            ctk.CTkLabel(self.key_list_frame, text="Chưa có API Key nào. Hãy thêm ở trên.", text_color=TEXT_S).pack(pady=20)
            return
        for i, cfg in enumerate(self.ai_config):
            card = ctk.CTkFrame(self.key_list_frame, fg_color=CARD, corner_radius=8, border_width=1, border_color=BORDER)
            card.pack(fill="x", pady=5, padx=5)
            status_msg = cfg.get("status_msg", "Chưa kiểm tra")
            is_valid = cfg.get("valid", False)
            color = SUCCESS if is_valid else WARNING
            if "Lỗi" in status_msg or "Hết" in status_msg: color = DANGER
            model_str = cfg.get('model') or "Mặc định"
            limits = cfg.get("limits", {})
            used = cfg.get("used_today", 0)
            limit_str = f"({limits.get('rpm', '?')} RPM / {limits.get('rpd', '?')} RPD) - Đã dùng: {used}" if limits else ""
            info = f"[{cfg['provider'].upper()}] {model_str} {limit_str}"
            ctk.CTkLabel(card, text=info, font=("Segoe UI", 14, "bold"), text_color=TEXT_P).pack(side="left", padx=15, pady=10)
            ctk.CTkLabel(card, text=status_msg, font=("Segoe UI", 12, "bold"), text_color=color).pack(side="left", padx=10)
            ctk.CTkButton(card, text="Xóa", width=50, height=30, fg_color="transparent", border_width=1, border_color=DANGER, text_color=DANGER, hover_color="#450a0a", command=lambda idx=i: self._remove_key(idx)).pack(side="right", padx=5)
            ctk.CTkButton(card, text="Check", width=60, height=30, fg_color="transparent", border_width=1, border_color=ACCENT, text_color=ACCENT, hover_color="#1e3a8a", command=lambda idx=i: self._check_key_quota(idx)).pack(side="right", padx=5)

    def _check_key_quota(self, idx):
        if idx >= len(self.ai_config): return
        cfg = self.ai_config[idx]
        self._log_ui(f"Đang kiểm tra lại {cfg['provider'].upper()}...", ACCENT)
        def task():
            solver = AISolver(cfg["provider"], cfg["api_key"], cfg["model"], rpd_limit=cfg["limits"].get("rpd", 1500))
            solver.used_today = cfg.get("used_today", 0)
            is_ready, quota_msg = solver.check_quota()
            def update_ui():
                if idx < len(self.ai_config):
                    self.ai_config[idx]["valid"] = is_ready
                    self.ai_config[idx]["status_msg"] = quota_msg
                    self.ai_config[idx]["model"] = solver.model
                    self._save_config()
                    self._refresh_key_list()
                    self._log_ui(f"Cập nhật: {quota_msg}", SUCCESS if is_ready else DANGER)
            self.after(0, update_ui)
        threading.Thread(target=task, daemon=True).start()

    def _remove_key(self, idx):
        if idx < len(self.ai_config):
            self.ai_config.pop(idx)
            self._save_config()
            self._refresh_key_list()

    def _show_mode_dialog(self, title, assign_id):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Chọn chế độ giải")
        dialog.geometry("450x320")
        dialog.configure(fg_color=BG)
        dialog.attributes("-topmost", True)
        dialog.grab_set()
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        ctk.CTkLabel(dialog, text="CHỌN CHẾ ĐỘ GIẢI BÀI", font=("Segoe UI", 18, "bold"), text_color=TEXT_P).pack(pady=(20, 5))
        ctk.CTkLabel(dialog, text=title, font=("Segoe UI", 13), text_color=ACCENT).pack(pady=(0, 15))
        has_api_key = any(k.get("valid") for k in self.ai_config if k.get("provider") != "jev")
        btn1 = ctk.CTkButton(dialog, text="1. Sử dụng API Key (AI Mạnh)\nĐộ chính xác cao, có phân tích từng bước", font=("Segoe UI", 14), height=60, fg_color=ACCENT, hover_color=ACCENT_HOVER, command=lambda: self._start_solving(title, assign_id, True, dialog))
        btn1.pack(fill="x", padx=30, pady=8)
        if not has_api_key: btn1.configure(state="disabled", text="1. Sử dụng API Key (Chưa cài đặt)\nHãy vào Cấu hình AI để thêm Key")
        btn2 = ctk.CTkButton(dialog, text="2. Không dùng API Key (Miễn phí)\nDùng Jev Classifier, chính xác thấp hơn", font=("Segoe UI", 14), height=60, fg_color="#4B5563", hover_color="#374151", command=lambda: self._start_solving(title, assign_id, False, dialog))
        btn2.pack(fill="x", padx=30, pady=8)
        ctk.CTkButton(dialog, text="Hủy", font=("Segoe UI", 13), fg_color="transparent", hover_color=HOVER, text_color=TEXT_S, command=dialog.destroy).pack(pady=(10, 15))

    def _start_solving(self, title, assign_id, use_api: bool, dialog):
        dialog.destroy()
        if use_api:
            valid_keys = [k for k in self.ai_config if k.get("valid") and k.get("provider") != "jev"]
            if not valid_keys: return messagebox.showerror("Lỗi", "Không có API Key hợp lệ nào.")
            chosen_config = valid_keys[0]
        else:
            chosen_config = {"provider": "jev", "api_key": "", "model": "jev-classifier", "used_today": 0}
        self.show_page("solve")
        self._run_solver(title, assign_id, chosen_config)

    def _run_solver(self, title, assign_id, config):
        self.running = True
        self.btn_stop.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_detail_box.delete("1.0", "end")
        self.progress.set(0)
        self.lbl_bai_hoc.configure(text=f"{title}\nID: {assign_id}")
        self.lbl_progress.configure(text="Đang khởi tạo...")
        self.start_time = time.time()
        self.timer_running = True
        self._update_timer()
        
        pacing = self.pacing_mode.get()
        sub_mode = self.submit_mode.get()
        try: total_mins = float(self.total_time_minutes.get())
        except: total_mins = 10.0
        try: delay_sec = float(self.delay_per_question.get())
        except: delay_sec = 5.0
        try: wait_mins = float(self.submit_wait_minutes.get())
        except: wait_mins = 3.0
        
        def task():
            try:
                provider = config["provider"]
                self._log(f"> Đang tải đề bài (Provider: {provider})...")
                qs = self.api.get_questions(assign_id)
                total = len(qs)
                self._log(f"> Tìm thấy {total} câu hỏi.")
                self.after(0, lambda: self.lbl_progress.configure(text=f"Tiến độ: 0/{total} câu hỏi"))
                delay_per_q = 0.0
                if pacing == "2": delay_per_q = max(0.5, (total_mins * 60) / total)
                elif pacing == "3": delay_per_q = delay_sec
                
                solver = AISolver(provider, config["api_key"], config["model"], rpd_limit=config.get("limits", {}).get("rpd", 1500))
                solver.used_today = config.get("used_today", 0)
                payloads = []
                
                for i, q in enumerate(qs):
                    if not self.running: break
                    t0 = time.time()
                    self._log(f"[{i+1}/{total}] Đang giải ({q.qtype}): {clean_display_text(q.content)[:40]}...")
                    try:
                        payload = solver.solve(q)
                        payloads.append(payload)
                        config["used_today"] = solver.used_today
                        for idx, cfg in enumerate(self.ai_config):
                            if cfg["provider"] == provider and cfg["api_key"] == config["api_key"]:
                                self.ai_config[idx]["used_today"] = solver.used_today
                                break
                        q_time = time.time() - t0
                        ans_display = ""
                        sent_id = ""
                        if q.qtype == "choice":
                            chosen_id = payload.get("optionId")
                            sent_id = str(chosen_id)
                            for idx, opt in enumerate(q.options):
                                if opt["id"] == chosen_id: ans_display = chr(65 + idx); break
                        elif q.qtype == "true_false":
                            ans_display = ", ".join(["Đ" if c == "true" else "S" for c in payload.get("choices", [])])
                            sent_id = str(payload.get("choices", []))
                        elif q.qtype == "text":
                            ans_display = payload.get("text", "")
                            sent_id = ans_display
                        self._log(f"  -> Đáp án: {ans_display} ({q_time:.1f}s)")
                        detail_text = f"[Câu {q.index}/{total}] - {q.qtype.upper()}\nNội dung: {clean_display_text(q.content)}\n=> AI chọn: {ans_display}\n=> ID gửi S3: {sent_id}\n=> Thời gian: {q_time:.2f}s\n" + "-"*40 + "\n\n"
                        self._log_detail(detail_text)
                    except Exception as api_err:
                        err_msg = str(api_err)
                        self._log(f"  -> [LỖI API]: {err_msg}")
                        if "429" in err_msg or "quota" in err_msg.lower():
                            self._log("  -> Đã hết hạn mức. Dừng.")
                            self.running = False
                            break
                        if q.qtype == "choice" and q.options: payloads.append({"stepId": q.id, "type": "choice", "optionId": q.options[0]["id"]})
                        elif q.qtype == "true_false": payloads.append({"stepId": q.id, "type": "true_false", "choices": ["true"] * len(q.options)})
                        else: payloads.append({"stepId": q.id, "type": "text", "text": "0"})
                    self.after(0, lambda p=(i+1)/total, cur=i+1, tot=total: [self.progress.set(p), self.lbl_progress.configure(text=f"Tiến độ: {cur}/{tot} câu hỏi")])
                    spent = time.time() - t0
                    if delay_per_q > spent and self.running: time.sleep(delay_per_q - spent)
                
                if self.running:
                    self._log("\n> Đang upload đáp án lên S3...")
                    if self.api.upload_answers(assign_id, payloads):
                        self._log("> Upload thành công!")
                        if sub_mode == "3":
                            self._log("\n> [CHẾ ĐỘ] KHÔNG nộp bài. Đáp án đã lưu.")
                            self.after(0, lambda: self.lbl_progress.configure(text="Hoàn tất (Chưa nộp)"))
                            return
                        wait_seconds = int(wait_mins * 60) if sub_mode == "2" else 0
                        if sub_mode in ("1", "2") and wait_seconds < 180: wait_seconds = 180
                        if wait_seconds > 0:
                            self._log(f"> Chờ {wait_seconds/60:.1f} phút trước khi nộp...")
                            for r in range(wait_seconds, 0, -1):
                                if not self.running: break
                                self.after(0, lambda rem=r: self.lbl_progress.configure(text=f"Đang chờ nộp bài: {rem//60:02d}:{rem%60:02d}..."))
                                time.sleep(1)
                        if self.running:
                            self._log("> Đang nộp bài...")
                            self.after(0, lambda: self.lbl_progress.configure(text="Đang nộp bài..."))
                            res = self.api.submit(assign_id)
                            if res["success"]: 
                                self._log("🎉 NỘP BÀI THÀNH CÔNG!")
                                self.after(0, lambda: self.lbl_progress.configure(text="Đã hoàn tất!"))
                            else: self._log(f"Lỗi nộp: {res.get('message')}")
                    else: self._log("> Upload thất bại.")
            except Exception as e: self._log(f"\n[LỖI HỆ THỐNG]: {e}")
            finally:
                self.after(0, lambda: self.btn_stop.configure(state="disabled"))
                self.after(0, self._refresh_key_list)
                self._save_config()
        threading.Thread(target=task, daemon=True).start()

    def _update_timer(self):
        if not self.timer_running: return
        elapsed = int(time.time() - self.start_time)
        self.lbl_timer.configure(text=f"⏱️ {elapsed//60:02d}:{elapsed%60:02d}")
        self.after(1000, self._update_timer)

    def _stop_solving(self):
        self.running = False
        self.timer_running = False
        self._log("\n> Đã dừng theo yêu cầu.")
        self.lbl_progress.configure(text="Đã dừng.")

    def _log(self, msg):
        if self.log_box.winfo_exists():
            self.after(0, lambda: self.log_box.insert("end", msg + "\n"))
            self.after(0, lambda: self.log_box.see("end"))
        
    def _log_detail(self, msg):
        if self.log_detail_box.winfo_exists():
            self.after(0, lambda: self.log_detail_box.insert("end", msg))
            self.after(0, lambda: self.log_detail_box.see("end"))

    def _show_account_manager(self):
        self.account_dialog = ctk.CTkToplevel(self)
        self.account_dialog.title("Quản lý tài khoản")
        self.account_dialog.geometry("400x500")
        self.account_dialog.configure(fg_color=BG)
        self.account_dialog.attributes("-topmost", True)
        self.account_dialog.grab_set()
        self.account_dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - self.account_dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - self.account_dialog.winfo_height()) // 2
        self.account_dialog.geometry(f"+{x}+{y}")
        self.acc_list_frame = ctk.CTkScrollableFrame(self.account_dialog, fg_color="transparent")
        self.acc_list_frame.pack(fill="both", expand=True, padx=20, pady=20)
        self._render_saved_accounts()

    def _render_saved_accounts(self):
        self._clear_frame(self.acc_list_frame)
        accounts = self.api.get_saved_accounts()
        for acc in accounts:
            card = ctk.CTkFrame(self.acc_list_frame, fg_color=CARD, corner_radius=8, border_width=1, border_color=BORDER)
            card.pack(fill="x", pady=5, padx=5)
            name = acc.get("display_name") or acc.get("username")
            ctk.CTkLabel(card, text=name, font=("Segoe UI", 14, "bold"), text_color=TEXT_P).pack(side="left", padx=15, pady=10)
            ctk.CTkButton(card, text="Chọn", width=60, height=30, fg_color=ACCENT, command=lambda a=acc: self._switch_account(a)).pack(side="right", padx=10)
        ctk.CTkButton(self.acc_list_frame, text="+ Thêm tài khoản", font=("Segoe UI", 14, "bold"), height=40, fg_color=SUCCESS, hover_color="#059669", command=self._add_new_account_ui).pack(fill="x", pady=20, padx=5)

    def _switch_account(self, acc):
        username = acc.get("username")
        try: password = base64.b64decode(acc.get("password")).decode()
        except: password = ""
        self.account_dialog.destroy()
        self.show_page("login")
        self.entry_user.delete(0, "end")
        self.entry_user.insert(0, username)
        self.entry_pass.delete(0, "end")
        self.entry_pass.insert(0, password)
        self._do_login()

    def _add_new_account_ui(self):
        self.account_dialog.destroy()
        self.show_page("login")
        self.entry_user.delete(0, "end")
        self.entry_pass.delete(0, "end")
        self.lbl_login.configure(text="")
        self.btn_back_login.pack(fill="x", pady=(0, 10))
        self.btn_login.configure(text="Đăng nhập tài khoản mới")

    def _cancel_add_account(self):
        self.btn_back_login.pack_forget()
        self.btn_login.configure(text="Đăng nhập ngay")
        self.entry_user.delete(0, "end")
        self.entry_pass.delete(0, "end")
        self.show_page("assign")

if __name__ == "__main__":
    app = App()
    app.mainloop()
