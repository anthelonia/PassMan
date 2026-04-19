import os
import json
import base64
import datetime
import random
import string
import tkinter as tk
import customtkinter as ctk
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DIR_PATH, "passwords.enc")

# Security
AUTO_LOCK_MS      = 300_000
CLIPBOARD_CLEAR_MS = 30_000
MAX_ATTEMPTS      = 5

COLORS = {
    "bg":     "#110A1A",
    "card":   "#1E122D",
    "accent": "#8b5cf6",
    "border": "#7E22CE",
    "text":   "#E2D6F5",
    "error":  "#f38ba8",
    "warn":   "#f9e2af"
}

ctk.set_appearance_mode("dark")


# Crypto

def get_key(master_password, salt):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000)
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))

def init_db(master_password):
    salt = os.urandom(16)
    f = Fernet(get_key(master_password, salt))
    with open(DB_FILE, "wb") as file:
        file.write(salt + f.encrypt(b"{}"))

def load_db(master_password):
    if not os.path.exists(DB_FILE): return None, None
    with open(DB_FILE, "rb") as file: data = file.read()
    salt, encrypted = data[:16], data[16:]
    f = Fernet(get_key(master_password, salt))
    try: return json.loads(f.decrypt(encrypted)), f
    except Exception: return None, None

def save_db(db, f, salt):
    with open(DB_FILE, "wb") as file:
        file.write(salt + f.encrypt(json.dumps(db).encode()))


# Card

class PasswordCard(ctk.CTkFrame):
    def __init__(self, parent, site, data, app):
        super().__init__(parent, fg_color=COLORS["card"], corner_radius=15)
        self.site = site
        self.data = data
        self.app = app
        self.is_flipped = False
        self.show_pass = False
        self.bind("<Button-1>", self.animate_flip)
        self.build_front()

    def build_front(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(fg_color=COLORS["card"])
        lbl = ctk.CTkLabel(self, text=self.site, font=("Maple Mono", 14, "bold"),
                            text_color=COLORS["accent"], wraplength=140)
        lbl.pack(expand=True, padx=10, pady=20)
        lbl.bind("<Button-1>", self.animate_flip)

    def animate_flip(self, event=None):
        self.is_flipped = not self.is_flipped
        self.update()
        if self.is_flipped: self.build_back()
        else: self.build_front()

    def build_back(self):
        for w in self.winfo_children(): w.destroy()
        inv_bg = COLORS["accent"]
        inv_fg = COLORS["bg"]
        self.configure(fg_color=inv_bg)

        lbl_title = ctk.CTkLabel(self, text=self.site.upper(), font=("Maple Mono", 11, "bold"),
                                  text_color=inv_fg, wraplength=150)
        lbl_title.pack(pady=(15, 5))
        lbl_title.bind("<Button-1>", self.animate_flip)

        lbl_user = ctk.CTkLabel(self, text=f"LOGIN: {self.data.get('user', '')}",
                                 font=("Maple Mono", 9), text_color=inv_fg, wraplength=140)
        lbl_user.pack(pady=(0, 2))
        lbl_user.bind("<Button-1>", self.animate_flip)

        self.pvar = tk.StringVar(value="********")
        pf_pass = ctk.CTkFrame(self, fg_color="transparent")
        pf_pass.pack()
        ctk.CTkLabel(pf_pass, text="HASŁO: ", font=("Maple Mono", 9), text_color=inv_fg).pack(side="left")
        ctk.CTkLabel(pf_pass, textvariable=self.pvar, font=("Maple Mono", 9, "bold"),
                     text_color=inv_fg, wraplength=100).pack(side="left")

        date_str = self.data.get("date", "N/A")
        date_color = inv_fg
        try:
            d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            if (datetime.datetime.now() - d).days > 180:
                date_color = COLORS["error"]
        except: pass

        lbl_date = ctk.CTkLabel(self, text=f"ADDED: {date_str}", font=("Maple Mono", 8, "bold"),
                                 text_color=date_color)
        lbl_date.pack(pady=(2, 5))

        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.pack(pady=5)
        ctk.CTkButton(btn_f, text="👁", width=30, height=25, fg_color="transparent",
                      hover_color=COLORS["card"], text_color=inv_fg,
                      command=self.toggle_pass).pack(side="left", padx=2)
        ctk.CTkButton(btn_f, text="📋", width=30, height=25, fg_color="transparent",
                      hover_color=COLORS["card"], text_color=inv_fg,
                      command=self.copy_pass).pack(side="left", padx=2)
        ctk.CTkButton(btn_f, text="✎", width=30, height=25, fg_color="transparent",
                      hover_color=COLORS["card"], text_color=inv_fg,
                      command=self.edit_pass).pack(side="left", padx=2)
        ctk.CTkButton(btn_f, text="🗑️", width=30, height=25, fg_color="transparent",
                      hover_color="#3b0000", text_color=COLORS["error"],
                      command=self.delete_entry).pack(side="left", padx=2)

        zoom_btn = ctk.CTkButton(btn_f, text="🔍", width=30, height=25, fg_color="transparent",
                                  hover_color=COLORS["card"], text_color=inv_fg, command=lambda: None)
        zoom_btn.pack(side="left", padx=2)
        zoom_btn.bind("<ButtonPress-1>",   lambda e: self._zoom_in())
        zoom_btn.bind("<ButtonRelease-1>", lambda e: self._zoom_out())

    def toggle_pass(self):
        self.show_pass = not self.show_pass
        self.pvar.set(self.data.get("pass", "") if self.show_pass else "********")

    def copy_pass(self):
        if hasattr(self.app, "_clipboard_job") and self.app._clipboard_job:
            self.app.after_cancel(self.app._clipboard_job)
        self.app.clipboard_clear()
        self.app.clipboard_append(self.data.get("pass", ""))
        self.app.show_toast("Copied! 🪄 (30s)")
        self.app._clipboard_job = self.app.after(CLIPBOARD_CLEAR_MS, self.app.clipboard_clear)

    def edit_pass(self):
        self.app.load_for_edit(self.site, self.data)

    def _zoom_in(self):
        self._zoom_popup = ctk.CTkFrame(
            self.app, fg_color=COLORS["card"], corner_radius=20,
            border_width=2, border_color=COLORS["accent"]
        )
        self._zoom_popup.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.78, relheight=0.42)
        ctk.CTkLabel(self._zoom_popup, text=self.site.upper(),
                     font=("Maple Mono", 30, "bold"), text_color=COLORS["accent"]).pack(pady=(35, 12))
        ctk.CTkLabel(self._zoom_popup, text=f"LOGIN:  {self.data.get('user', '')}",
                     font=("Maple Mono", 20), text_color=COLORS["text"]).pack(pady=4)
        ctk.CTkLabel(self._zoom_popup, text=f"PASSWORD:  {self.data.get('pass', '')}",
                     font=("Maple Mono", 20), text_color=COLORS["text"]).pack(pady=4)
        ctk.CTkLabel(self._zoom_popup, text="release to close",
                     font=("Maple Mono", 10), text_color=COLORS["border"]).pack(pady=(18, 0))

    def _zoom_out(self):
        if hasattr(self, "_zoom_popup") and self._zoom_popup:
            self._zoom_popup.destroy()
            self._zoom_popup = None

    def delete_entry(self):
        dialog = ctk.CTkInputDialog(
            text=f'Type "{self.site}" to confirm deletion:',
            title="⚠️ Delete entry"
        )
        result = dialog.get_input()
        if result == self.site:
            del self.app.db[self.site]
            save_db(self.app.db, self.app.f, self.app.salt)
            self.app.show_toast("🗑️ Deleted!")
            self.app.refresh_list()


# App

class PassManApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PassMan")
        self.geometry("600x850")
        self.configure(fg_color=COLORS["bg"])
        self.db = None
        self.f = None
        self.salt = None
        self.failed_attempts = 0
        self.locked_until = None
        self._clipboard_job = None
        self._lock_job = None

        self._build_login_screen()
        self.bind("<Unmap>", self._on_minimize)

        self.toast = ctk.CTkLabel(self, text="", fg_color=COLORS["accent"], text_color="white",
                                   font=("Maple Mono", 12, "bold"), corner_radius=12,
                                   width=160, height=40)

    # Login

    def _build_login_screen(self):
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.login_frame.pack(expand=True, fill="both")

        ctk.CTkLabel(self.login_frame, text="SECRET_KEY", font=("Maple Mono", 24, "bold"),
                     text_color=COLORS["accent"]).pack(pady=(150, 30))

        self.mp_entry = ctk.CTkEntry(self.login_frame, show="*", font=("Maple Mono", 14),
                                      width=250, height=45, corner_radius=10,
                                      fg_color=COLORS["card"], border_color=COLORS["border"],
                                      border_width=2)
        self.mp_entry.pack(pady=10)
        self.add_focus_highlight(self.mp_entry, COLORS["border"])
        self.mp_entry.bind("<Return>", lambda e: self.login())

        self.show_key_var = ctk.StringVar(value="off")
        ctk.CTkCheckBox(self.login_frame, text="Show Key", variable=self.show_key_var,
                        onvalue="on", offvalue="off", command=self.toggle_login_visibility,
                        fg_color=COLORS["accent"], hover_color=COLORS["accent"],
                        font=("Maple Mono", 12)).pack(pady=10)

        self.error_lbl = ctk.CTkLabel(self.login_frame, text="", text_color=COLORS["error"],
                                       font=("Maple Mono", 12, "bold"))
        self.error_lbl.pack(pady=5)

        ctk.CTkButton(self.login_frame, text="UNLOCK", command=self.login,
                      font=("Maple Mono", 14, "bold"), fg_color=COLORS["accent"],
                      hover_color="#7c4df2", width=200, height=45,
                      corner_radius=10).pack(pady=20)

    def login(self):
        mp = self.mp_entry.get()
        if not mp:
            return
        if self.locked_until and datetime.datetime.now() < self.locked_until:
            remaining = int((self.locked_until - datetime.datetime.now()).total_seconds())
            self.error_lbl.configure(text=f"Too many attempts. Wait {remaining}s")
            return

        self.error_lbl.configure(text="")
        if not os.path.exists(DB_FILE):
            init_db(mp)

        db, f = load_db(mp)
        if db is None:
            self.failed_attempts += 1
            delay = min(2 ** (self.failed_attempts - 1), 60)
            self.locked_until = datetime.datetime.now() + datetime.timedelta(seconds=delay)
            remaining_attempts = max(0, MAX_ATTEMPTS - self.failed_attempts)
            if remaining_attempts > 0:
                self.error_lbl.configure(
                    text=f"Wrong password! Locked {delay}s ({remaining_attempts} attempts left)"
                )
            else:
                self.error_lbl.configure(text=f"Too many failures. Locked {delay}s")
            return

        self.failed_attempts = 0
        self.locked_until = None
        self.db = db
        self.f = f
        with open(DB_FILE, "rb") as file:
            self.salt = file.read(16)
        self.login_frame.destroy()
        self.show_main()

    # Lock

    def _on_minimize(self, event=None):
        if self.db is not None:
            self._trigger_lock()

    def _reset_activity_timer(self, event=None):
        if self._lock_job:
            self.after_cancel(self._lock_job)
        self._lock_job = self.after(AUTO_LOCK_MS, self._trigger_lock)

    def _trigger_lock(self):
        if self.db is None:
            return
        self.db = None
        self.f = None
        if self._clipboard_job:
            self.after_cancel(self._clipboard_job)
            self._clipboard_job = None
        self.clipboard_clear()

        self._lock_overlay = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        self._lock_overlay.place(x=0, y=0, relwidth=1, relheight=1)
        ctk.CTkLabel(self._lock_overlay, text="🔒", font=("Maple Mono", 48)).pack(pady=(120, 5))
        ctk.CTkLabel(self._lock_overlay, text="SESSION LOCKED", font=("Maple Mono", 20, "bold"),
                     text_color=COLORS["accent"]).pack(pady=(0, 30))

        lock_entry = ctk.CTkEntry(self._lock_overlay, show="*", font=("Maple Mono", 14),
                                   width=250, height=45, corner_radius=10,
                                   fg_color=COLORS["card"], border_color=COLORS["border"],
                                   border_width=2)
        lock_entry.pack(pady=10)
        lock_entry.focus()

        self._lock_error = ctk.CTkLabel(self._lock_overlay, text="", text_color=COLORS["error"],
                                         font=("Maple Mono", 12, "bold"))
        self._lock_error.pack(pady=5)

        lock_entry.bind("<Return>", lambda e: self._unlock(lock_entry.get()))
        ctk.CTkButton(self._lock_overlay, text="UNLOCK",
                      command=lambda: self._unlock(lock_entry.get()),
                      font=("Maple Mono", 14, "bold"), fg_color=COLORS["accent"],
                      hover_color="#7c4df2", width=200, height=45, corner_radius=10).pack(pady=20)

    def _unlock(self, mp):
        db, f = load_db(mp)
        if db is None:
            self._lock_error.configure(text="Wrong password!")
            return
        self.db = db
        self.f = f
        with open(DB_FILE, "rb") as file:
            self.salt = file.read(16)
        self._lock_overlay.destroy()
        self._reset_activity_timer()
        self.refresh_list()

    # UI helpers

    def add_focus_highlight(self, widget, default_color):
        widget.bind("<FocusIn>",  lambda e: widget.configure(border_color="#c084fc", border_width=3))
        widget.bind("<FocusOut>", lambda e: widget.configure(border_color=default_color, border_width=2))

    def toggle_login_visibility(self):
        self.mp_entry.configure(show="" if self.show_key_var.get() == "on" else "*")

    def toggle_add_pass_visibility(self):
        self.p_ent.configure(show="" if self.p_ent.cget("show") == "*" else "*")

    def generate_password(self):
        pwd = "".join(random.choice(string.ascii_letters + string.digits + "!@#$%^&*")
                      for _ in range(16))
        self.p_ent.delete(0, tk.END)
        self.p_ent.insert(0, pwd)
        self.p_ent.configure(show="")

    def show_toast(self, msg):
        self.toast.configure(text=msg)
        self.toast.place(relx=0.5, rely=0.9, anchor="center")
        self.after(2000, self.toast.place_forget)

    def load_for_edit(self, site, data):
        self.s_ent.delete(0, tk.END)
        self.s_ent.insert(0, site)
        self.u_ent.delete(0, tk.END)
        self.u_ent.insert(0, data.get("user", ""))
        self.p_ent.delete(0, tk.END)
        self.p_ent.insert(0, data.get("pass", ""))
        self.p_ent.configure(show="")
        self.show_toast("Edit mode ✎")

    # Main view

    def show_main(self):
        self._main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._main_frame.pack(fill="both", expand=True)

        top = ctk.CTkFrame(self._main_frame, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=20)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.refresh_list(self.search_var.get()))

        search_frame = ctk.CTkFrame(top, fg_color=COLORS["card"], corner_radius=12,
                                     border_width=2, border_color=COLORS["card"])
        search_frame.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(search_frame, text="🔍", font=("Maple Mono", 14),
                     text_color=COLORS["accent"], width=35).pack(side="left", padx=(10, 0))
        self.search_ent = ctk.CTkEntry(search_frame, textvariable=self.search_var,
                                        placeholder_text="Search...", font=("Maple Mono", 12),
                                        fg_color="transparent", border_width=0, height=40)
        self.search_ent.pack(side="left", fill="x", expand=True, padx=(4, 10))
        self.search_ent.bind("<FocusIn>",  lambda e: search_frame.configure(
            border_color="#c084fc", fg_color="#241638"))
        self.search_ent.bind("<FocusOut>", lambda e: search_frame.configure(
            border_color=COLORS["card"], fg_color=COLORS["card"]))

        entry_container = ctk.CTkFrame(top, fg_color=COLORS["card"], corner_radius=15)
        entry_container.pack(fill="x")

        self.s_ent = ctk.CTkEntry(entry_container, placeholder_text="Site",
                                   fg_color="transparent", border_width=2,
                                   border_color=COLORS["border"], font=("Maple Mono", 12), height=35)
        self.s_ent.pack(fill="x", padx=15, pady=(15, 5))
        self.add_focus_highlight(self.s_ent, COLORS["border"])

        self.u_ent = ctk.CTkEntry(entry_container, placeholder_text="Username / Email",
                                   fg_color="transparent", border_width=2,
                                   border_color=COLORS["border"], font=("Maple Mono", 12), height=35)
        self.u_ent.pack(fill="x", padx=15, pady=5)
        self.add_focus_highlight(self.u_ent, COLORS["border"])

        pf = ctk.CTkFrame(entry_container, fg_color="transparent")
        pf.pack(fill="x", padx=15, pady=(5, 15))
        self.p_ent = ctk.CTkEntry(pf, placeholder_text="Password", show="*",
                                   fg_color="transparent", border_width=2,
                                   border_color=COLORS["border"], font=("Maple Mono", 12), height=35)
        self.p_ent.pack(side="left", fill="x", expand=True)
        self.add_focus_highlight(self.p_ent, COLORS["border"])
        ctk.CTkButton(pf, text="👁", width=35, height=35, fg_color="transparent",
                      text_color=COLORS["text"], hover_color=COLORS["bg"],
                      command=self.toggle_add_pass_visibility).pack(side="left", padx=2)
        ctk.CTkButton(pf, text="🎲", width=35, height=35, fg_color="transparent",
                      text_color=COLORS["accent"], hover_color=COLORS["bg"],
                      command=self.generate_password).pack(side="left")

        ctk.CTkButton(top, text="SAVE ENTRY", command=self.add_entry, fg_color=COLORS["accent"],
                      hover_color="#7c4df2", font=("Maple Mono", 12, "bold"), height=45,
                      corner_radius=12).pack(fill="x", pady=(15, 0))

        self.scroll_frame = ctk.CTkScrollableFrame(self._main_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.scroll_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.refresh_list()

        self.bind_all("<Motion>", self._reset_activity_timer)
        self.bind_all("<Key>",    self._reset_activity_timer)
        self.bind_all("<Button>", self._reset_activity_timer)
        self._reset_activity_timer()

    def refresh_list(self, query=""):
        if self.db is None:
            return
        for w in self.scroll_frame.winfo_children(): w.destroy()
        q = query.lower()
        filtered = {k: v for k, v in self.db.items() if q in k.lower()}
        for i, (site, data) in enumerate(sorted(filtered.items())):
            card = PasswordCard(self.scroll_frame, site, data, self)
            card.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky="nsew")

    def add_entry(self):
        s = self.s_ent.get()
        u = self.u_ent.get()
        p = self.p_ent.get()
        if s:
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            new_date = current_date
            if s in self.db:
                old_pass = self.db[s].get("pass", "")
                if p == old_pass:
                    new_date = self.db[s].get("date", current_date)
            self.db[s] = {"user": u, "pass": p, "date": new_date}
            save_db(self.db, self.f, self.salt)
            self.show_toast("✨ saved!")
            self.search_var.set("")
            self.refresh_list()
            self.s_ent.delete(0, tk.END)
            self.u_ent.delete(0, tk.END)
            self.p_ent.delete(0, tk.END)
            self.p_ent.configure(show="*")


if __name__ == "__main__":
    PassManApp().mainloop()