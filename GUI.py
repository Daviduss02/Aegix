import customtkinter as ctk
import tkinter as tk
import threading
import os
import sys
from lang import LangManager
from ai_engine import AIEngine
from scanner import ScanEngine
import config

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class AegixApp(ctk.CTk):
    def __init__(self):
        # SSH X11 check
        if os.environ.get('DISPLAY') is None:
            print("[!] DISPLAY environment variable not set. X11 forwarding might be disabled.")
            # We don't exit here, super().__init__() will raise TclError which is handled in main.py

        super().__init__()

        self.cfg  = config.load()
        self.lang = LangManager(self.cfg.get("language", "EN"))
        self.ai_engine = AIEngine(
            provider=self.cfg["provider"],
            api_key=self.cfg["groq_api_key"],
            ollama_host=self.cfg["ollama_host"],
            ollama_port=self.cfg["ollama_port"],
            groq_model=self.cfg["groq_model"],
            ollama_model=self.cfg["ollama_model"]
        )
        self.scan_engine = ScanEngine(
            output_cb=lambda text: self.after(0, self.append_to_output, text),
            done_cb=lambda: self.after(0, self._on_scan_done),
            ai_query_cb=self.ai_engine.ask,
            confirm_cb=self._confirm_command
        )


        self._spinner_active   = False
        self._spinner_index    = 0
        self._spinner_after_id = None

        ctk.set_appearance_mode(self.cfg.get("theme", "Dark"))
        ctk.set_default_color_theme("blue")
        self.geometry(self.cfg.get("geometry", "1400x800"))
        self.minsize(800, 500)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.ai_chat_visible = True

        # ── TOP BAR ───────────────────────────────────────
        self.top_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_propagate(False)

        self.btn_file = ctk.CTkButton(self.top_bar, text="", width=60, fg_color="transparent")
        self.btn_file.pack(side="left", padx=5, pady=5)

        self.btn_settings = ctk.CTkButton(self.top_bar, text="", width=80,
                                          fg_color="transparent", command=self.open_settings)
        self.btn_settings.pack(side="left", padx=5, pady=5)

        self.btn_toggle_ai = ctk.CTkButton(self.top_bar, text="", width=120,
                                           command=self.toggle_ai_chat)
        self.btn_toggle_ai.pack(side="right", padx=10, pady=5)

        # ── PANED WINDOW ──────────────────────────────────
        self.paned = tk.PanedWindow(self, orient="horizontal", sashwidth=6,
                                    sashrelief="flat", background="#2b2b2b", bd=0)
        self.paned.grid(row=1, column=0, sticky="nsew")

        # ── LEFT PANEL ────────────────────────────────────
        self.left_frame = ctk.CTkFrame(self.paned, corner_radius=0)
        self.left_frame.grid_rowconfigure(0, weight=7)
        self.left_frame.grid_rowconfigure(1, weight=3)
        self.left_frame.grid_columnconfigure(0, weight=1)

        # WORKSPACE
        self.workspace = ctk.CTkFrame(self.left_frame, fg_color=("gray85", "gray20"))
        self.workspace.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.workspace.grid_rowconfigure(1, weight=1)
        self.workspace.grid_columnconfigure(0, weight=1)

        ip_bar = ctk.CTkFrame(self.workspace, fg_color="transparent")
        ip_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        ctk.CTkLabel(ip_bar, text="Target IP:").pack(side="left", padx=(0, 6))
        self.ip_entry = ctk.CTkEntry(ip_bar, width=160)
        self.ip_entry.insert(0, "10.0.0.0")
        self.ip_entry.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(ip_bar, text="Mask:").pack(side="left", padx=(0, 6))
        self.mask_entry = ctk.CTkEntry(ip_bar, width=80)
        self.mask_entry.insert(0, "8")
        self.mask_entry.pack(side="left")

        middle = ctk.CTkFrame(self.workspace, fg_color="transparent")
        middle.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 6))
        middle.grid_rowconfigure(0, weight=1)
        middle.grid_columnconfigure(0, weight=0)
        middle.grid_columnconfigure(1, weight=1)

        tools_panel = ctk.CTkFrame(middle, fg_color=("gray78", "gray18"), width=220)
        tools_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        tools_panel.grid_propagate(False)
        ctk.CTkLabel(tools_panel, text="Tools", font=("Arial", 13, "bold")).pack(
            pady=(12, 8), padx=12, anchor="w")
        ctk.CTkFrame(tools_panel, height=1, fg_color=("gray65", "gray35")).pack(
            fill="x", padx=8, pady=(0, 8))
        self.tool_vars = {}
        for tool_name in ["nmap", "enum4linux", "SQLmap"]:
            var = tk.BooleanVar(value=False)
            ctk.CTkCheckBox(tools_panel, text=tool_name, variable=var,
                            font=("Arial", 12)).pack(anchor="w", padx=14, pady=5)
            self.tool_vars[tool_name] = var

        details_panel = ctk.CTkFrame(middle, fg_color="transparent")
        details_panel.grid(row=0, column=1, sticky="nsew")
        details_panel.grid_rowconfigure(1, weight=1)
        details_panel.grid_columnconfigure(0, weight=1)
        details_header = ctk.CTkFrame(details_panel, fg_color="transparent")
        details_header.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        ctk.CTkLabel(details_header, text="Details", font=("Arial", 13, "bold"),
                     anchor="w").pack(side="left")
        self.details_char_label = ctk.CTkLabel(details_header, text="0 / 1000",
                                               font=("Arial", 11),
                                               text_color=("gray50", "gray60"))
        self.details_char_label.pack(side="right")
        self.details_textbox = ctk.CTkTextbox(details_panel, wrap="word")
        self.details_textbox.grid(row=1, column=0, sticky="nsew")
        self.details_textbox.bind("<KeyRelease>", self._on_details_key)

        run_bar = ctk.CTkFrame(self.workspace, fg_color="transparent")
        run_bar.grid(row=2, column=0, sticky="ew", padx=12, pady=(4, 10))
        self.btn_run = ctk.CTkButton(
            run_bar, text="RUN", width=110, height=34,
            font=("Arial", 13, "bold"),
            fg_color=("#c0392b", "#922b21"),
            hover_color=("#a93226", "#7b241c"),
            command=self.on_run_clicked
        )
        self.btn_run.pack(side="right")

        # OUTPUT CONSOLE
        self.output_frame = ctk.CTkFrame(self.left_frame, fg_color=("gray80", "gray15"))
        self.output_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.output_textbox = ctk.CTkTextbox(self.output_frame, wrap="word")
        self.output_textbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.output_textbox.configure(state="disabled")

        # ── RIGHT PANEL (AI Chat) ─────────────────────────
        self.ai_frame = ctk.CTkFrame(self.paned, corner_radius=0, fg_color=("gray90", "gray25"))
        self.ai_label = ctk.CTkLabel(self.ai_frame, text="", font=("Arial", 16, "bold"))
        self.ai_label.pack(pady=10)
        self.ai_textbox = ctk.CTkTextbox(self.ai_frame, wrap="word")
        self.ai_textbox.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.ai_textbox.configure(state="disabled")
        self.ai_entry = ctk.CTkEntry(self.ai_frame, placeholder_text="")
        self.ai_entry.pack(fill="x", padx=10, pady=10)
        self.ai_entry.bind("<Return>", self.send_message_to_ai)

        self.paned.add(self.left_frame, stretch="always", minsize=500)
        self.paned.add(self.ai_frame, stretch="never", minsize=200, width=340)

        self.apply_language()

    def on_close(self):
        self.scan_engine.stop()
        self.cfg["geometry"] = self.geometry()
        config.save(self.cfg)
        self.destroy()

    def _confirm_command(self, command):
        result = [False]
        event = threading.Event()

        def on_confirm(val):
            result[0] = val
            event.set()
            dialog.destroy()

        def create_dialog():
            nonlocal dialog
            dialog = ctk.CTkToplevel(self)
            dialog.title("Aegix Agent: Confirmation")
            dialog.geometry("550x250")
            dialog.attributes("-topmost", True)
            dialog.resizable(False, False)
            
            # Center the dialog
            self.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() // 2) - 275
            y = self.winfo_y() + (self.winfo_height() // 2) - 125
            dialog.geometry(f"+{x}+{y}")

            label = ctk.CTkLabel(dialog, text="The AI Agent wants to execute the following command:", 
                                 font=("Arial", 13, "bold"), wraplength=500)
            label.pack(pady=(20, 10), padx=20)
            
            cmd_frame = ctk.CTkFrame(dialog, fg_color=("gray85", "gray20"))
            cmd_frame.pack(fill="x", padx=30, pady=10)
            
            cmd_label = ctk.CTkLabel(cmd_frame, text=command, font=("Courier New", 12), 
                                     wraplength=480, text_color=("#1a5276", "#5dade2"))
            cmd_label.pack(pady=10, padx=10)
            
            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(pady=(10, 20))
            
            yes_btn = ctk.CTkButton(btn_frame, text="Yes (Execute)", width=120, height=32,
                                     fg_color="#27ae60", hover_color="#229954",
                                     command=lambda: on_confirm(True))
            yes_btn.pack(side="left", padx=15)
            
            no_btn = ctk.CTkButton(btn_frame, text="No (Skip)", width=120, height=32,
                                    fg_color="#c0392b", hover_color="#a93226",
                                    command=lambda: on_confirm(False))
            no_btn.pack(side="left", padx=15)
            
            dialog.protocol("WM_DELETE_WINDOW", lambda: on_confirm(False))

        dialog = None
        self.after(0, create_dialog)
        event.wait()
        return result[0]

    def _on_details_key(self, event=None):

        content = self.details_textbox.get("0.0", "end-1c")
        if len(content) > 1000:
            self.details_textbox.delete("1.0+1000c", "end")
            content = content[:1000]
        self.details_char_label.configure(
            text=f"{len(content)} / 1000",
            text_color=("gray50", "gray60") if len(content) < 900 else ("#c0392b", "#e74c3c")
        )

    def on_run_clicked(self):
        if self.scan_engine.is_running:
            self._stop_scan()
        else:
            self._start_scan()

    def _start_scan(self):
        self.btn_run.configure(text="STOP",
                               fg_color=("#566573", "#2c3e50"),
                               hover_color=("#717d7e", "#34495e"))
        self.output_textbox.configure(state="normal")
        self.output_textbox.delete("0.0", "end")
        self.output_textbox.configure(state="disabled")
        self.scan_engine.start(
            ip=self.ip_entry.get().strip(),
            mask=self.mask_entry.get().strip(),
            details=self.details_textbox.get("0.0", "end-1c").strip(),
            tool_vars={k: v.get() for k, v in self.tool_vars.items()}
        )

    def _stop_scan(self):
        self.scan_engine.stop()
        self.append_to_output("\n[!] Scan stopped by user.")

    def _on_scan_done(self):
        self.btn_run.configure(text="RUN",
                               fg_color=("#c0392b", "#922b21"),
                               hover_color=("#a93226", "#7b241c"))

    def apply_language(self):
        self.title(self.lang.t("title"))
        self.btn_file.configure(text=self.lang.t("file"))
        self.btn_settings.configure(text=self.lang.t("settings"))
        self.btn_toggle_ai.configure(
            text=self.lang.t("hide_ai") if self.ai_chat_visible else self.lang.t("show_ai")
        )
        self.ai_label.configure(text=self.lang.t("ai_label"))
        self.ai_entry.configure(placeholder_text=self.lang.t("ai_placeholder"))
        self.output_textbox.configure(state="normal")
        self.output_textbox.delete("0.0", "end")
        self.output_textbox.insert("0.0", self.lang.t("output_default"))
        self.output_textbox.configure(state="disabled")

    def toggle_language(self):
        new_lang = "SK" if self.lang.current == "EN" else "EN"
        self.lang.load(new_lang)
        self.cfg["language"] = new_lang
        config.save(self.cfg)
        self.apply_language()

    def open_settings(self):
        win = ctk.CTkToplevel(self)
        win.title(self.lang.t("settings_title"))
        win.geometry("720x500")
        win.minsize(600, 420)
        win.attributes("-topmost", True)
        win.grid_rowconfigure(0, weight=1)
        win.grid_columnconfigure(0, weight=0)
        win.grid_columnconfigure(1, weight=1)

        nav_frame = ctk.CTkFrame(win, width=210, corner_radius=0, fg_color=("gray80", "gray18"))
        nav_frame.grid(row=0, column=0, sticky="nsew")
        nav_frame.grid_propagate(False)
        ctk.CTkLabel(nav_frame, text=self.lang.t("settings_title"),
                     font=("Arial", 12, "bold")).pack(pady=(14, 8), padx=14, anchor="w")

        content_frame = ctk.CTkFrame(win, corner_radius=0, fg_color=("gray92", "gray15"))
        content_frame.grid(row=0, column=1, sticky="nsew")

        pages, nav_buttons = {}, {}

        def show_page(key):
            for p in pages.values(): p.pack_forget()
            if key in pages: pages[key].pack(fill="both", expand=True, padx=25, pady=20)
            for k, b in nav_buttons.items():
                b.configure(fg_color=("gray68", "gray32") if k == key else "transparent")

        def add_nav(key, label):
            btn = ctk.CTkButton(nav_frame, text=label, anchor="w", height=30,
                                fg_color="transparent", hover_color=("gray72", "gray35"),
                                corner_radius=4, command=lambda k=key: show_page(k))
            btn.pack(fill="x", padx=6, pady=1)
            nav_buttons[key] = btn

        # Appearance
        p = ctk.CTkFrame(content_frame, fg_color="transparent")
        pages["appearance"] = p
        ctk.CTkLabel(p, text=self.lang.t("appearance_label"),
                     font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 4))
        ctk.CTkFrame(p, height=1, fg_color=("gray70", "gray40")).pack(fill="x", pady=(0, 16))
        r = ctk.CTkFrame(p, fg_color="transparent"); r.pack(fill="x", pady=6)
        ctk.CTkLabel(r, text=self.lang.t("dark_mode"), anchor="w", width=220).pack(side="left")
        sw = ctk.CTkSwitch(r, text="", command=self.toggle_theme, width=50); sw.pack(side="left")
        if ctk.get_appearance_mode() == "Dark": sw.select()

        # Language
        p = ctk.CTkFrame(content_frame, fg_color="transparent")
        pages["language"] = p
        ctk.CTkLabel(p, text=self.lang.t("language_label"),
                     font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 4))
        ctk.CTkFrame(p, height=1, fg_color=("gray70", "gray40")).pack(fill="x", pady=(0, 16))
        r = ctk.CTkFrame(p, fg_color="transparent"); r.pack(fill="x", pady=6)
        ctk.CTkLabel(r, text=self.lang.t("language_switch"), anchor="w", width=220).pack(side="left")
        sw = ctk.CTkSwitch(r, text="", width=50, command=self.toggle_language); sw.pack(side="left")
        if self.lang.current == "SK": sw.select()

        # AI
        p = ctk.CTkFrame(content_frame, fg_color="transparent")
        pages["ai"] = p
        ctk.CTkLabel(p, text=self.lang.t("ai_settings_label"),
                     font=("Arial", 15, "bold")).pack(anchor="w", pady=(0, 4))
        ctk.CTkFrame(p, height=1, fg_color=("gray70", "gray40")).pack(fill="x", pady=(0, 16))
        r = ctk.CTkFrame(p, fg_color="transparent"); r.pack(fill="x", pady=6)
        ctk.CTkLabel(r, text=self.lang.t("provider_label"), anchor="w", width=160).pack(side="left")
        provider_var = ctk.StringVar(value=self.cfg["provider"])
        ctk.CTkSegmentedButton(r, values=["groq", "ollama"], variable=provider_var,
                               command=lambda v: update_prov(v)).pack(side="left")
        dyn = ctk.CTkFrame(p, fg_color="transparent"); dyn.pack(fill="x", pady=8)
        gf = ctk.CTkFrame(dyn, fg_color="transparent")
        of = ctk.CTkFrame(dyn, fg_color="transparent")
        ctk.CTkLabel(gf, text=self.lang.t("api_key_label"), anchor="w").pack(anchor="w", pady=(0, 4))
        api_e = ctk.CTkEntry(gf, placeholder_text=self.lang.t("api_key_placeholder"),
                             width=320, show="*"); api_e.pack(anchor="w", pady=(0, 8))
        if self.cfg["groq_api_key"]: api_e.insert(0, self.cfg["groq_api_key"])
        ctk.CTkLabel(of, text=self.lang.t("ollama_host_label"), anchor="w").pack(anchor="w", pady=(0, 4))
        host_e = ctk.CTkEntry(of, placeholder_text=self.lang.t("ollama_host_placeholder"),
                              width=220); host_e.pack(anchor="w", pady=(0, 8))
        host_e.insert(0, self.cfg["ollama_host"])
        ctk.CTkLabel(of, text=self.lang.t("ollama_port_label"), anchor="w").pack(anchor="w", pady=(0, 4))
        port_e = ctk.CTkEntry(of, width=100); port_e.pack(anchor="w", pady=(0, 8))
        port_e.insert(0, str(self.cfg["ollama_port"]))

        def update_prov(v):
            gf.pack_forget(); of.pack_forget()
            (gf if v == "groq" else of).pack(fill="x")
        update_prov(self.cfg["provider"])

        def save_ai():
            self.cfg["provider"] = provider_var.get()
            self.cfg["groq_api_key"] = api_e.get().strip()
            self.cfg["ollama_host"] = host_e.get().strip()
            try: self.cfg["ollama_port"] = int(port_e.get().strip())
            except ValueError: pass
            config.save(self.cfg)
            self.ai_engine = AIEngine(
                provider=self.cfg["provider"], api_key=self.cfg["groq_api_key"],
                ollama_host=self.cfg["ollama_host"], ollama_port=self.cfg["ollama_port"],
                groq_model=self.cfg["groq_model"], ollama_model=self.cfg["ollama_model"]
            )
            # Update scanner callback as well
            self.scan_engine._ai_query_cb = self.ai_engine.ask

        ctk.CTkButton(p, text=self.lang.t("save_button"), command=save_ai).pack(anchor="w", pady=(12, 0))

        add_nav("appearance", self.lang.t("appearance_label"))
        add_nav("language",   self.lang.t("language_label"))
        add_nav("ai",         self.lang.t("ai_settings_label"))
        show_page("appearance")

    def toggle_theme(self):
        mode = "Light" if ctk.get_appearance_mode() == "Dark" else "Dark"
        ctk.set_appearance_mode(mode)
        self.cfg["theme"] = mode
        config.save(self.cfg)

    def toggle_ai_chat(self):
        if self.ai_chat_visible:
            self.paned.forget(self.ai_frame)
            self.btn_toggle_ai.configure(text=self.lang.t("show_ai"))
            self.ai_chat_visible = False
        else:
            self.paned.add(self.ai_frame, stretch="never", minsize=200, width=340)
            self.btn_toggle_ai.configure(text=self.lang.t("hide_ai"))
            self.ai_chat_visible = True

    def _start_spinner(self):
        self._spinner_index = 0
        self._spinner_active = True
        self.ai_textbox.configure(state="normal")
        tb = self.ai_textbox._textbox
        tb.mark_set("spinner_mark", "end")
        tb.mark_gravity("spinner_mark", "left")
        tb.insert("end", f"Aegix AI:\n{SPINNER_FRAMES[0]} {self.lang.t('spinner_text')}\n\n")
        self.ai_textbox.see("end")
        self.ai_textbox.configure(state="disabled")
        self._spinner_after_id = self.after(80, self._animate_spinner)

    def _animate_spinner(self):
        if not self._spinner_active:
            return
        self._spinner_index = (self._spinner_index + 1) % len(SPINNER_FRAMES)
        self.ai_textbox.configure(state="normal")
        tb = self.ai_textbox._textbox
        tb.delete("spinner_mark", "end")
        tb.insert("end", f"Aegix AI:\n{SPINNER_FRAMES[self._spinner_index]} {self.lang.t('spinner_text')}\n\n")
        self.ai_textbox.see("end")
        self.ai_textbox.configure(state="disabled")
        self._spinner_after_id = self.after(80, self._animate_spinner)

    def _stop_spinner_and_show(self, response):
        self._spinner_active = False
        if self._spinner_after_id:
            self.after_cancel(self._spinner_after_id)
        self.ai_textbox.configure(state="normal")
        tb = self.ai_textbox._textbox
        tb.delete("spinner_mark", "end")
        tb.insert("end", f"Aegix AI:\n{response}\n\n")
        self.ai_textbox.see("end")
        self.ai_textbox.configure(state="disabled")
        self.ai_entry.configure(state="normal")

    def send_message_to_ai(self, event=None):
        user_text = self.ai_entry.get().strip()
        if not user_text:
            return
        self.ai_entry.delete(0, "end")
        self.ai_entry.configure(state="disabled")
        self._write_to_chat(self.lang.t("chat_you"), user_text)
        self._start_spinner()
        threading.Thread(target=self._process_ai, args=(user_text,), daemon=True).start()

    def _process_ai(self, user_text):
        try:
            response = self.ai_engine.ask(user_text)
        except Exception as e:
            response = f"[Error] {e}"
        self.after(0, self._stop_spinner_and_show, response)

    def _write_to_chat(self, sender, text):
        self.ai_textbox.configure(state="normal")
        self.ai_textbox._textbox.insert("end", f"{sender}:\n{text}\n\n")
        self.ai_textbox.see("end")
        self.ai_textbox.configure(state="disabled")

    def append_to_output(self, text):
        self.output_textbox.configure(state="normal")
        self.output_textbox._textbox.insert("end", text + "\n")
        self.output_textbox.see("end")
        self.output_textbox.configure(state="disabled")
