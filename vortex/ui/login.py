import json
import os
import webbrowser
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from core import BASE_DIR, DATA_DIR

CONFIG_FILE = DATA_DIR / "config.json"
ENV_FILE = BASE_DIR / ".env"

# ── Palette (matches dashboard) ─────────────────────────────────────
BG            = "#090909"
BG_INPUT      = "#111111"
BG_BTN        = "#7c3aed"
BG_BTN_HOV    = "#6d28d9"
FG            = "#f0f0f0"
FG_MUTED      = "#555555"
FG_LABEL      = "#888888"
ACCENT        = "#7c3aed"
ACCENT_BRIGHT = "#a855f7"
FONT_TITLE    = ("Segoe UI", 20, "bold")
FONT_SUB      = ("Segoe UI", 9)
FONT_LABEL    = ("Segoe UI", 9, "bold")
FONT_INPUT    = ("Segoe UI", 10)
FONT_BTN      = ("Segoe UI", 10, "bold")
FONT_MONO     = ("Consolas", 8)


def get_saved_token():
    return "standalone_active"


class VortexLogin:
    def __init__(self):
        self.profile_data = {}
        self.root = None
        self.body_frame = None

        # Form string variables
        self.agreement_accepted = None
        self.gemini_key_var = None
        self.ollama_model_var = None
        self.wake_word_var = None

        self.name_var = None
        self.location_var = None
        self.role_var = None
        self.focus_var = None
        self.apps_var = None

    def is_setup_complete(self) -> bool:
        # Check config.json profile
        config_data = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                pass
        prof = config_data.get("profile", {})
        if not prof or not prof.get("name"):
            return False

        # Check .env GEMINI_API_KEY
        if not ENV_FILE.exists():
            return False

        gemini_key = ""
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        gemini_key = line.split("=", 1)[1].strip()
        except Exception:
            pass

        if not gemini_key or gemini_key == "your_gemini_api_key_here":
            return False

        return True

    def prompt(self):
        # 1. Skip setup if already completed
        if self.is_setup_complete():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    self.profile_data = config_data.get("profile", {})
                    return self.profile_data
            except Exception:
                pass

        # 2. Otherwise load existing fields to pre-populate (if any)
        config_data = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                pass
        prof = config_data.get("profile", {})

        # Parse saved .env keys
        saved_gemini_key = ""
        saved_ollama_model = "gemma3:4b"
        saved_wake = "vortex"
        if ENV_FILE.exists():
            try:
                with open(ENV_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k, v = k.strip(), v.strip()
                        if k == "GEMINI_API_KEY":
                            saved_gemini_key = v
                        elif k == "OLLAMA_MODEL":
                            saved_ollama_model = v
                        elif k == "VORTEX_WAKE_WORD":
                            saved_wake = v
            except Exception:
                pass

        # Initialize Tkinter
        self.root = tk.Tk()
        self.root.title("Vortex — Onboarding Setup Wizard")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.overrideredirect(True)

        W, H = 450, 600
        sx = self.root.winfo_screenwidth()
        sy = self.root.winfo_screenheight()
        self.root.geometry(f"{W}x{H}+{(sx - W) // 2}+{(sy - H) // 2}")

        # Setup Variables
        self.agreement_accepted = tk.BooleanVar(value=False)
        self.gemini_key_var = tk.StringVar(value=saved_gemini_key)
        self.ollama_model_var = tk.StringVar(value=saved_ollama_model)
        self.wake_word_var = tk.StringVar(value=saved_wake)

        self.name_var = tk.StringVar(value=prof.get("name", "Heerav Amin"))
        self.location_var = tk.StringVar(value=prof.get("location", "Mumbai"))
        self.role_var = tk.StringVar(value=prof.get("role", "CS student"))
        self.focus_var = tk.StringVar(value=", ".join(prof.get("weak_areas", ["DSA recursion", "system design"])))
        self.apps_var = tk.StringVar(value=", ".join(prof.get("favorite_apps", ["VSCode", "Cursor", "Ollama", "Docker"])))

        # ── Top Bar (Draggable, Frameless) ───────────────────────────
        top = tk.Frame(self.root, bg="#0d0d0d", height=38)
        top.pack(fill="x")
        top.pack_propagate(False)

        # Drag setup
        self._dx = self._dy = 0
        top.bind("<ButtonPress-1>", lambda e: setattr(self, "_dx", e.x) or setattr(self, "_dy", e.y))
        top.bind("<B1-Motion>", lambda e: self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}"))

        tk.Label(top, text="⬤ VORTEX AI SYSTEM SETUP", bg="#0d0d0d", fg=ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=14)

        x_btn = tk.Button(top, text="✕", bg="#0d0d0d", fg="#333333", bd=0,
                          font=("Segoe UI", 12), cursor="hand2",
                          activebackground="#0d0d0d", activeforeground="#ef4444",
                          command=self.root.destroy)
        x_btn.pack(side="right", padx=10)
        x_btn.bind("<Enter>", lambda e: x_btn.configure(fg="#ef4444"))
        x_btn.bind("<Leave>", lambda e: x_btn.configure(fg="#333333"))

        # Accent border line
        tk.Frame(self.root, bg=ACCENT, height=1).pack(fill="x")

        # ── Body Frame ────────────────────────────────────────────────
        self.body_frame = tk.Frame(self.root, bg=BG)
        self.body_frame.pack(fill="both", expand=True, padx=32, pady=16)

        # Start with Step 1
        self.show_step_1_agreement()

        self.root.mainloop()
        return self.profile_data

    def clear_body(self):
        for widget in self.body_frame.winfo_children():
            widget.destroy()

    def show_step_1_agreement(self):
        self.clear_body()

        tk.Label(self.body_frame, text="VORTEX AI OS SETUP", bg=BG, fg=FG, font=FONT_TITLE).pack(anchor="w")
        tk.Label(self.body_frame, text="STEP 1: LICENSE & PRIVACY AGREEMENT", bg=BG, fg=FG_MUTED, font=FONT_MONO).pack(anchor="w", pady=(2, 10))

        # Agreement Text Box
        agreement_text = (
            "VORTEX PERSONAL AI OPERATING SYSTEM - END USER AGREEMENT\n\n"
            "By setting up and running Vortex, you acknowledge and agree to the following terms:\n\n"
            "1. LOCAL PRIVACY & SCREEN OCR BUFFER:\n"
            "Vortex operates primarily as a localized workflow helper. Your voice command audio feeds, local "
            "files, system process trees, SQLite memory, and screenshot buffers (saved locally at "
            "'data/last_screenshot.png') are stored exclusively on this machine. Vortex does not upload "
            "private system assets or screenshot captures to external analytics servers.\n\n"
            "2. CLOUD AI ROUTING (GEMINI API):\n"
            "To process complex planning decisions (Planner V2) and perform grounded search queries, Vortex "
            "routes structured text tokens to Google Gemini API servers. Your usage of these models is "
            "governed by Google's standard developer API terms. To use this, you must provide a valid "
            "Gemini API key.\n\n"
            "3. LOCAL AI FALLBACK (OLLAMA):\n"
            "If internet access is unavailable or cloud rate limits are reached, Vortex will fallback to a "
            "local SLM (e.g. gemma3:4b or llama3.2) served via Ollama (http://localhost:11434). Running offline "
            "models requires Ollama to be installed and running on your system.\n\n"
            "4. WINDOWS OS INTEGRATION & COMMAND EXECUTION:\n"
            "Vortex leverages Windows COM interfaces (pycaw), shell scripts, and system process managers "
            "to perform requested actions (e.g., launching apps, adjusting master volume, searching files, "
            "and terminating tasks). Ensure you understand system commands when using prompt automation."
        )

        text_frame = tk.Frame(self.body_frame, bg=BG_INPUT, bd=1, highlightbackground="#222222", highlightthickness=1)
        text_frame.pack(fill="both", expand=True, pady=10)

        scrollbar = tk.Scrollbar(text_frame, width=10)
        scrollbar.pack(side="right", fill="y")

        tb = tk.Text(text_frame, bg=BG_INPUT, fg=FG, font=("Consolas", 9), wrap="word",
                     bd=0, yscrollcommand=scrollbar.set, padx=8, pady=8, insertbackground=ACCENT)
        tb.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=tb.yview)

        tb.insert("1.0", agreement_text)
        tb.configure(state="disabled")

        # Agreement Checkbox Frame
        check_frame = tk.Frame(self.body_frame, bg=BG)
        check_frame.pack(fill="x", pady=10)

        cb = tk.Checkbutton(
            check_frame, text="I Accept the Onboarding Agreement & Privacy Policy",
            variable=self.agreement_accepted, bg=BG, fg=FG, selectcolor=BG,
            activebackground=BG, activeforeground=FG, font=FONT_SUB, bd=0,
            command=lambda: next_btn.configure(
                state="normal" if self.agreement_accepted.get() else "disabled",
                bg=BG_BTN if self.agreement_accepted.get() else "#333333"
            )
        )
        cb.pack(anchor="w")

        # Bottom Button navigation
        nav_frame = tk.Frame(self.body_frame, bg=BG)
        nav_frame.pack(fill="x", side="bottom", pady=10)

        next_btn = tk.Button(
            nav_frame, text="NEXT STEP ➔", bg="#333333", fg="white", bd=0,
            font=FONT_BTN, cursor="hand2", relief="flat", state="disabled",
            command=self.show_step_2_models
        )
        next_btn.pack(side="right", ipady=8, ipadx=24)

    def show_step_2_models(self):
        self.clear_body()

        tk.Label(self.body_frame, text="VORTEX AI OS SETUP", bg=BG, fg=FG, font=FONT_TITLE).pack(anchor="w")
        tk.Label(self.body_frame, text="STEP 2: MODEL & KEY CONFIGURATION", bg=BG, fg=FG_MUTED, font=FONT_MONO).pack(anchor="w", pady=(2, 10))

        # Gemini API Key Field
        tk.Label(self.body_frame, text="GEMINI API KEY (REQUIRED FOR CLOUD PLANNERS)", bg=BG, fg=FG_LABEL, font=("Consolas", 8), anchor="w").pack(fill="x", pady=(10, 0))
        key_frame = tk.Frame(self.body_frame, bg=BG_INPUT, highlightthickness=1, highlightbackground="#222222", highlightcolor=ACCENT)
        key_frame.pack(fill="x", pady=(2, 4), ipady=2)
        key_entry = tk.Entry(key_frame, bg=BG_INPUT, fg=FG, insertbackground=ACCENT, font=FONT_INPUT, bd=0, textvariable=self.gemini_key_var)
        key_entry.pack(fill="x", padx=10, pady=5)
        key_entry.bind("<FocusIn>", lambda _: key_frame.configure(highlightbackground=ACCENT))
        key_entry.bind("<FocusOut>", lambda _: key_frame.configure(highlightbackground="#222222"))

        # Link to Google AI Studio
        link_lbl = tk.Label(self.body_frame, text="Get a free Gemini API key from Google AI Studio", bg=BG, fg=ACCENT_BRIGHT, font=FONT_SUB, cursor="hand2")
        link_lbl.pack(anchor="w", pady=(0, 10))
        link_lbl.bind("<Button-1>", lambda _: webbrowser.open("https://aistudio.google.com/apikey"))

        # Ollama Fallback model choice
        tk.Label(self.body_frame, text="OFFLINE OLLAMA MODEL FALLBACK", bg=BG, fg=FG_LABEL, font=("Consolas", 8), anchor="w").pack(fill="x", pady=(10, 0))

        radio_frame = tk.Frame(self.body_frame, bg=BG)
        radio_frame.pack(fill="x", pady=(5, 10))

        models = [
            ("gemma3:4b (Recommended Offline Brain)", "gemma3:4b"),
            ("llama3.2:1b (Fast / Low Memory)", "llama3.2:1b"),
            ("Disable Ollama Fallback (Cloud Only)", "none")
        ]

        for text, val in models:
            rb = tk.Radiobutton(
                radio_frame, text=text, variable=self.ollama_model_var, value=val,
                bg=BG, fg=FG, selectcolor=BG, activebackground=BG, activeforeground=FG,
                font=FONT_SUB, bd=0, anchor="w", pady=4
            )
            rb.pack(fill="x")

        # Wake Word Configuration
        tk.Label(self.body_frame, text="WAKE WORD", bg=BG, fg=FG_LABEL, font=("Consolas", 8), anchor="w").pack(fill="x", pady=(10, 0))
        wake_frame = tk.Frame(self.body_frame, bg=BG_INPUT, highlightthickness=1, highlightbackground="#222222", highlightcolor=ACCENT)
        wake_frame.pack(fill="x", pady=(2, 10), ipady=2)
        wake_entry = tk.Entry(wake_frame, bg=BG_INPUT, fg=FG, insertbackground=ACCENT, font=FONT_INPUT, bd=0, textvariable=self.wake_word_var)
        wake_entry.pack(fill="x", padx=10, pady=5)
        wake_entry.bind("<FocusIn>", lambda _: wake_frame.configure(highlightbackground=ACCENT))
        wake_entry.bind("<FocusOut>", lambda _: wake_frame.configure(highlightbackground="#222222"))

        # Navigation
        nav_frame = tk.Frame(self.body_frame, bg=BG)
        nav_frame.pack(fill="x", side="bottom", pady=10)

        back_btn = tk.Button(
            nav_frame, text="⮌ BACK", bg="#222222", fg=FG, bd=0,
            font=FONT_BTN, cursor="hand2", relief="flat",
            command=self.show_step_1_agreement
        )
        back_btn.pack(side="left", ipady=8, ipadx=24)

        next_btn = tk.Button(
            nav_frame, text="NEXT STEP ➔", bg=BG_BTN, fg="white", bd=0,
            font=FONT_BTN, cursor="hand2", relief="flat",
            command=self.show_step_3_profile
        )
        next_btn.pack(side="right", ipady=8, ipadx=24)
        next_btn.bind("<Enter>", lambda e: next_btn.configure(bg=BG_BTN_HOV))
        next_btn.bind("<Leave>", lambda e: next_btn.configure(bg=BG_BTN))

    def show_step_3_profile(self):
        self.clear_body()

        tk.Label(self.body_frame, text="VORTEX AI OS SETUP", bg=BG, fg=FG, font=FONT_TITLE).pack(anchor="w")
        tk.Label(self.body_frame, text="STEP 3: PERSONAL PROFILE CONTEXT", bg=BG, fg=FG_MUTED, font=FONT_MONO).pack(anchor="w", pady=(2, 10))

        # Inputs helper
        def make_profile_field(label, textvar):
            tk.Label(self.body_frame, text=label, bg=BG, fg=FG_LABEL, font=("Consolas", 8), anchor="w").pack(fill="x", pady=(6, 0))
            frame = tk.Frame(self.body_frame, bg=BG_INPUT, highlightthickness=1, highlightbackground="#222222", highlightcolor=ACCENT)
            frame.pack(fill="x", pady=(2, 4), ipady=2)
            entry = tk.Entry(frame, bg=BG_INPUT, fg=FG, insertbackground=ACCENT, font=FONT_INPUT, bd=0, textvariable=textvar)
            entry.pack(fill="x", padx=10, pady=5)
            entry.bind("<FocusIn>", lambda _: frame.configure(highlightbackground=ACCENT))
            entry.bind("<FocusOut>", lambda _: frame.configure(highlightbackground="#222222"))
            return entry

        make_profile_field("FULL NAME", self.name_var)
        make_profile_field("LOCATION", self.location_var)
        make_profile_field("PROFESSION / ROLE", self.role_var)
        make_profile_field("FOCUS TOPICS / WEAK AREAS (Comma separated)", self.focus_var)
        make_profile_field("FAVORITE TOOLS / APPS (Comma separated)", self.apps_var)

        # Status text
        status_lbl = tk.Label(self.body_frame, text="Context is saved locally to configure your personal AI OS link.", bg=BG, fg="#2a2a2a", font=("Consolas", 8))
        status_lbl.pack(pady=(10, 0))

        # Navigation
        nav_frame = tk.Frame(self.body_frame, bg=BG)
        nav_frame.pack(fill="x", side="bottom", pady=10)

        back_btn = tk.Button(
            nav_frame, text="⮌ BACK", bg="#222222", fg=FG, bd=0,
            font=FONT_BTN, cursor="hand2", relief="flat",
            command=self.show_step_2_models
        )
        back_btn.pack(side="left", ipady=8, ipadx=24)

        done_btn = tk.Button(
            nav_frame, text="COMPLETE SETUP ✓", bg=BG_BTN, fg="white", bd=0,
            font=FONT_BTN, cursor="hand2", relief="flat",
            command=self.save_and_finish
        )
        done_btn.pack(side="right", ipady=8, ipadx=14)
        done_btn.bind("<Enter>", lambda e: done_btn.configure(bg=BG_BTN_HOV))
        done_btn.bind("<Leave>", lambda e: done_btn.configure(bg=BG_BTN))

    def save_and_finish(self):
        gemini_key = self.gemini_key_var.get().strip()
        ollama_model = self.ollama_model_var.get().strip()
        wake_word = self.wake_word_var.get().strip() or "vortex"

        name = self.name_var.get().strip()
        location = self.location_var.get().strip()
        role = self.role_var.get().strip()
        focus = [x.strip() for x in self.focus_var.get().split(",") if x.strip()]
        apps = [x.strip() for x in self.apps_var.get().split(",") if x.strip()]

        # Validation
        if not gemini_key:
            messagebox.showwarning("Vortex Setup", "Gemini API key is required to utilize cloud features.\nPlease return to step 2 and paste a valid key.")
            return

        if not name:
            messagebox.showwarning("Vortex Setup", "Please specify your name to initialize your personalization profile.")
            return

        # 1. Update the .env file
        env_data = {}
        if ENV_FILE.exists():
            try:
                with open(ENV_FILE, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            env_data[k.strip()] = v.strip()
            except Exception:
                pass

        env_data["GEMINI_API_KEY"] = gemini_key
        env_data["OLLAMA_MODEL"] = ollama_model
        env_data["VORTEX_WAKE_WORD"] = wake_word
        env_data["ENABLE_PLANNER_V2"] = "true"
        if "EDGE_TTS_VOICE" not in env_data:
            env_data["EDGE_TTS_VOICE"] = "en-US-JennyNeural"
        if "LOG_LEVEL" not in env_data:
            env_data["LOG_LEVEL"] = "INFO"

        try:
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                for k, v in env_data.items():
                    f.write(f"{k}={v}\n")
        except Exception as e:
            messagebox.showerror("Vortex Setup", f"Failed to save environmental parameters into .env file: {e}")
            return

        # 2. Update config.json profile
        config_data = {}
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                pass

        config_data["profile"] = {
            "name": name,
            "location": location,
            "role": role,
            "weak_areas": focus,
            "favorite_apps": apps,
            "routine": config_data.get("profile", {}).get("routine", {"09:00": "coding", "14:00": "LeetCode"}),
            "style": config_data.get("profile", {}).get("style", "PEP8 Python, React/Next.js fullstack")
        }

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)
            self.profile_data = config_data["profile"]
        except Exception as e:
            messagebox.showerror("Vortex Setup", f"Failed to save user profile configuration: {e}")
            return

        # Success: close Tkinter window
        self.root.destroy()


__all__ = ["get_saved_token", "VortexLogin"]
