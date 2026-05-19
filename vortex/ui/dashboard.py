import logging
import time
import tkinter as tk
from tkinter import scrolledtext
from typing import Callable, Optional


# ── Colour palette ──────────────────────────────────────────────────
BG_ROOT       = "#0a0a0a"
BG_TOPBAR     = "#111111"
BG_CHAT       = "#0f0f0f"
BG_INPUT_ROW  = "#111111"
BG_ENTRY      = "#1a1a1a"
BG_SEND       = "#7c3aed"
BG_SEND_HOV   = "#6d28d9"

ACCENT        = "#7c3aed"
ACCENT_BRIGHT = "#a855f7"
ACCENT_CYAN   = "#22d3ee"
ACCENT_BLUE   = "#60a5fa"
FG_PRIMARY    = "#eeeeee"
FG_MUTED      = "#555555"
FG_DIM        = "#2a2a2a"
FG_STATUS     = "#7c3aed"

FONT_CHAT_B   = ("Segoe UI", 10, "bold")
FONT_CHAT     = ("Segoe UI", 10)
FONT_TIME     = ("Consolas", 7)
FONT_TITLE    = ("Segoe UI", 11, "bold")
FONT_MONO     = ("Consolas", 8)
FONT_INPUT    = ("Segoe UI", 11)
FONT_ORB      = ("Segoe UI", 16)
FONT_SEND_BTN = ("Segoe UI", 12, "bold")


class VortexDashboard:
    """
    Premium pure-black overlay dashboard for Vortex AI OS.
    Frameless, always-on-top, bottom-right position.
    Chat at top, input row pinned to bottom.
    """

    def __init__(
        self,
        on_submit: Callable[[str], None],
        on_quit: Optional[Callable[[], None]] = None,
        on_toggle_continuous: Optional[Callable[[bool], None]] = None,
    ):
        self._on_submit            = on_submit
        self._on_quit_callback     = on_quit
        self._on_toggle_continuous = on_toggle_continuous
        self._root:         Optional[tk.Tk]                    = None
        self._chat_box:     Optional[scrolledtext.ScrolledText] = None
        self._entry:        Optional[tk.Entry]                 = None
        self._status_label: Optional[tk.Label]                 = None
        self._orb_dot:      Optional[tk.Label]                 = None
        self._cont_btn:     Optional[tk.Button]                = None
        self._continuous_on = False
        self._pulse_state   = False
        self._drag_x = self._drag_y = 0

    # ── public API (thread-safe) ────────────────────────────────────

    def start(self) -> None:
        self._run()

    def stop(self) -> None:
        if self._root:
            self._root.after(0, self._root.destroy)

    def add_message(self, sender: str, text: str) -> None:
        if self._chat_box:
            self._chat_box.after(0, self._append_text, sender, text)

    def set_status(self, text: str, color: str = FG_STATUS) -> None:
        if self._status_label:
            self._status_label.after(
                0, lambda: self._status_label.configure(text=f"● {text.upper()}", fg=color)
            )

    # ── internal ────────────────────────────────────────────────────

    def _append_text(self, sender: str, text: str) -> None:
        if not self._chat_box:
            return
        ts  = time.strftime("%H:%M")
        box = self._chat_box
        box.configure(state="normal")
        box.insert("end", f"{ts}  ", "ts")
        box.insert("end", f"{sender.upper()}\n", sender.lower())
        clean = str(text).replace("\r", "").strip()
        box.insert("end", f"{clean}\n\n", "body")
        box.see("end")
        box.configure(state="disabled")

    # ── build UI ────────────────────────────────────────────────────

    def _run(self) -> None:
        try:
            root = tk.Tk()
            self._root = root
            root.title("Vortex AI OS")
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            # NO alpha — avoids the desktop bleed-through bug on Windows
            root.configure(bg=BG_ROOT)
            root.resizable(False, False)

            W, H = 450, 595
            sx   = root.winfo_screenwidth()
            sy   = root.winfo_screenheight()
            # subtract taskbar height (~48px) + margin so input row is never hidden
            root.geometry(f"{W}x{H}+{sx - W - 24}+{sy - H - 90}")

            # ── TOP BAR ─────────────────────────────────────────────
            topbar = tk.Frame(root, bg=BG_TOPBAR, height=46)
            topbar.pack(fill="x", side="top")
            topbar.pack_propagate(False)

            topbar.bind("<ButtonPress-1>", self._start_drag)
            topbar.bind("<B1-Motion>",      self._do_drag)

            # orb + title (left side)
            left = tk.Frame(topbar, bg=BG_TOPBAR)
            left.pack(side="left", padx=14)
            left.bind("<ButtonPress-1>", self._start_drag)
            left.bind("<B1-Motion>",      self._do_drag)

            self._orb_dot = tk.Label(left, text="⬤", bg=BG_TOPBAR, fg=ACCENT,
                                     font=("Segoe UI", 10))
            self._orb_dot.pack(side="left", padx=(0, 6))

            tk.Label(left, text="VORTEX", bg=BG_TOPBAR, fg=FG_PRIMARY,
                     font=FONT_TITLE).pack(side="left")

            tk.Label(left, text="  AI OS", bg=BG_TOPBAR, fg=FG_MUTED,
                     font=("Segoe UI", 9)).pack(side="left")

            # close (right side)
            close_btn = tk.Button(
                topbar, text="✕", bg=BG_TOPBAR, fg="#404040",
                activebackground=BG_TOPBAR, activeforeground="#ef4444",
                font=("Segoe UI", 13), bd=0, cursor="hand2",
                command=self._on_close,
            )
            close_btn.pack(side="right", padx=12)
            close_btn.bind("<Enter>", lambda e: close_btn.configure(fg="#ef4444"))
            close_btn.bind("<Leave>", lambda e: close_btn.configure(fg="#404040"))

            # accent line under topbar
            tk.Frame(root, bg=ACCENT, height=1).pack(fill="x")

            # ── STATUS ROW ──────────────────────────────────────────
            status_row = tk.Frame(root, bg=BG_ROOT)
            status_row.pack(fill="x", padx=14, pady=(6, 2))

            self._status_label = tk.Label(
                status_row, text="● SYSTEM ONLINE",
                bg=BG_ROOT, fg=ACCENT, font=FONT_MONO,
            )
            self._status_label.pack(side="left")

            self._cont_btn = tk.Button(
                status_row, text="○  CONTINUOUS OFF",
                bg=BG_ROOT, fg=FG_MUTED, bd=0, relief="flat",
                activebackground=BG_ROOT, activeforeground=ACCENT_CYAN,
                font=FONT_MONO, cursor="hand2",
                command=self._toggle_continuous,
            )
            self._cont_btn.pack(side="right")

            # thin divider above chat
            tk.Frame(root, bg="#1e1e1e", height=1).pack(fill="x")

            # ── INPUT ROW — packed FIRST so tkinter reserves space ───
            # (must come before expand=True chat box or it gets zero height)
            tk.Frame(root, bg="#1e1e1e", height=1).pack(fill="x", side="bottom")

            input_row = tk.Frame(root, bg=BG_INPUT_ROW, height=56)
            input_row.pack(fill="x", side="bottom")
            input_row.pack_propagate(False)

            # entry wrapper with violet focus glow
            entry_wrap = tk.Frame(
                input_row,
                bg=BG_ENTRY,
                highlightthickness=1,
                highlightbackground="#2a2a2a",
                highlightcolor=ACCENT,
            )
            entry_wrap.pack(fill="x", expand=True, padx=(12, 8), pady=10, side="left")

            self._entry = tk.Entry(
                entry_wrap,
                bg=BG_ENTRY, fg=FG_PRIMARY,
                insertbackground=ACCENT,
                font=FONT_INPUT, bd=0,
                highlightthickness=0,
            )
            self._entry.pack(fill="both", expand=True, padx=10, ipady=6)
            self._entry.bind("<FocusIn>",
                             lambda e: entry_wrap.configure(highlightbackground=ACCENT))
            self._entry.bind("<FocusOut>",
                             lambda e: entry_wrap.configure(highlightbackground="#2a2a2a"))
            self._entry.bind("<Return>", lambda _: self._send())
            self._entry.focus_set()

            # send button
            send_btn = tk.Button(
                input_row, text="▶",
                bg=BG_SEND, fg="white",
                activebackground=BG_SEND_HOV, activeforeground="white",
                font=FONT_SEND_BTN, bd=0, relief="flat",
                cursor="hand2", command=self._send,
            )
            send_btn.pack(side="right", padx=(0, 12), pady=10, ipadx=12, ipady=2)
            send_btn.bind("<Enter>", lambda e: send_btn.configure(bg=BG_SEND_HOV))
            send_btn.bind("<Leave>", lambda e: send_btn.configure(bg=BG_SEND))

            # ── EMOJI & STICKER KEYBOARD BAR ───
            emoji_bar = tk.Frame(root, bg="#141414", height=34)
            emoji_bar.pack(fill="x", side="bottom")
            emoji_bar.pack_propagate(False)

            # Scrollable/packed emoji buttons
            emojis = ["😊", "🚀", "💡", "🔥", "💻", "🎉", "❤️", "👍"]
            stickers = [
                ("(づ｡◕‿‿◕｡)づ", "HUG"),
                ("(⌐■_■)", "DEAL"),
                ("(╯°□°)╯︵ ┻━┻", "FLIP"),
                ("⚡ BOOM!", "⚡"),
                ("✨ MAGIC!", "✨")
            ]

            for em in emojis:
                btn = tk.Button(
                    emoji_bar, text=em, bg="#141414", fg=FG_PRIMARY,
                    activebackground="#2a2a2a", activeforeground=ACCENT_BRIGHT,
                    font=("Segoe UI", 11), bd=0, relief="flat", cursor="hand2",
                    command=lambda char=em: self._insert_emoji(char)
                )
                btn.pack(side="left", padx=2, pady=2)
                btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#2a2a2a"))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#141414"))

            # Divider
            tk.Label(emoji_bar, text="│", bg="#141414", fg=FG_MUTED).pack(side="left", padx=2)

            for st_text, st_label in stickers:
                btn = tk.Button(
                    emoji_bar, text=st_label, bg="#1a1a1a", fg="#a855f7",
                    activebackground="#2a2a2a", activeforeground="white",
                    font=("Segoe UI", 8, "bold"), bd=0, relief="flat", cursor="hand2",
                    command=lambda char=st_text: self._insert_emoji(char)
                )
                btn.pack(side="left", padx=2, pady=4, ipadx=4)
                btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#7c3aed", fg="white"))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#1a1a1a", fg="#a855f7"))

            # ── CHAT AREA — packed LAST, fills all remaining space ───
            self._chat_box = scrolledtext.ScrolledText(
                root,
                bg=BG_CHAT, fg=FG_PRIMARY,
                font=FONT_CHAT,
                bd=0, relief="flat",
                padx=16, pady=14,
                state="disabled", wrap="word",
                selectbackground=ACCENT,
                insertbackground=FG_PRIMARY,
            )
            self._chat_box.pack(fill="both", expand=True)

            # text tags
            self._chat_box.tag_configure("you",    foreground=ACCENT_BLUE,   font=FONT_CHAT_B)
            self._chat_box.tag_configure("vortex", foreground=ACCENT_BRIGHT, font=FONT_CHAT_B)
            self._chat_box.tag_configure("system", foreground=FG_MUTED,      font=FONT_CHAT_B)
            self._chat_box.tag_configure("body",   foreground=FG_PRIMARY,    font=FONT_CHAT)
            self._chat_box.tag_configure("ts",     foreground=FG_MUTED,      font=FONT_TIME)

            try:
                self._chat_box.vbar.configure(
                    bg="#1a1a1a", troughcolor=BG_ROOT,
                    activebackground=ACCENT, width=5,
                    relief="flat", bd=0,
                )
            except Exception:
                pass

            self._orb_bottom = None
            self._pulse()

            root.protocol("WM_DELETE_WINDOW", self._on_close)
            root.mainloop()

        except Exception as e:
            logging.exception("Dashboard UI failed to start: %s", e)

    # ── drag ────────────────────────────────────────────────────────

    def _start_drag(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _do_drag(self, e):
        self._root.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    # ── actions ─────────────────────────────────────────────────────

    def _insert_emoji(self, char: str):
        if not self._entry:
            return
        self._entry.insert(tk.INSERT, char)
        self._entry.focus_set()

    def _send(self):
        text = self._entry.get().strip()
        if not text:
            return
        self._entry.delete(0, "end")
        # NOTE: do NOT echo here — orchestrator calls ui_callback("You", ...) already
        try:
            self._on_submit(text)
        except Exception:
            logging.exception("Dashboard submit failed")

    def _toggle_continuous(self):
        self._continuous_on = not self._continuous_on
        if self._continuous_on:
            self._cont_btn.configure(text="⬤  CONTINUOUS ON",  fg=ACCENT_CYAN)
        else:
            self._cont_btn.configure(text="○  CONTINUOUS OFF", fg=FG_MUTED)
        if self._on_toggle_continuous:
            self._on_toggle_continuous(self._continuous_on)

    def _pulse(self):
        if not self._root:
            return
        self._pulse_state = not self._pulse_state
        c = ACCENT_BRIGHT if self._pulse_state else ACCENT
        if self._orb_dot:
            self._orb_dot.configure(fg=c)
        self._root.after(900, self._pulse)

    def _on_close(self):
        if self._on_quit_callback:
            self._on_quit_callback()
        self.stop()


__all__ = ["VortexDashboard"]
