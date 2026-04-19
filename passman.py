import os
import json
import base64
import datetime
import random
import string
import tkinter as tk
from tkinter import messagebox
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DIR_PATH, "passwords.enc")

COLORS = {
    "bg": "#110A1A",
    "card": "#1E122D",
    "accent": "#8b5cf6",
    "border": "#7E22CE",
    "text": "#E2D6F5",
    "error": "#f38ba8"
}

def get_key(master_password, salt):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000)
    return base64.urlsafe_b64encode(kdf.derive(master_password.encode()))

def init_db(master_password):
    salt = os.urandom(16)
    key = get_key(master_password, salt)
    f = Fernet(key)
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

class PasswordCard(tk.Frame):
    def __init__(self, parent, site, data, app):
        super().__init__(parent, bg=COLORS["bg"])
        self.site, self.data, self.app = site, data, app
        self.is_flipped = False
        self.show_pass = False
        
        self.inner = tk.Frame(self, bg=COLORS["card"], highlightthickness=2, highlightbackground=COLORS["border"], width=110, height=110)
        self.inner.pack_propagate(False)
        self.inner.pack(expand=True, fill="both", padx=3, pady=3)
        self.inner.bind("<Button-1>", self.flip)
        
        self.build_front()

    def build_front(self):
        for w in self.inner.winfo_children(): w.destroy()
        lbl = tk.Label(self.inner, text=self.site, font=("Maple Mono", 9, "bold"), bg=COLORS["card"], fg=COLORS["accent"], wraplength=90)
        lbl.pack(expand=True)
        lbl.bind("<Button-1>", self.flip)

    def flip(self, event=None):
        self.is_flipped = not self.is_flipped
        if self.is_flipped: self.build_back()
        else: self.build_front()

    def build_back(self):
        for w in self.inner.winfo_children(): w.destroy()
        self.inner.configure(bg="#1a1126")
        
        tk.Label(self.inner, text=f"L: {self.data.get('user', '')[:10]}", bg="#1a1126", fg=COLORS["text"], font=("Maple Mono", 7), wraplength=100).pack(pady=(10,0))
        
        self.pvar = tk.StringVar(value="********")
        tk.Label(self.inner, textvariable=self.pvar, bg="#1a1126", fg=COLORS["accent"], font=("Maple Mono", 7, "bold")).pack()
        
        btn_f = tk.Frame(self.inner, bg="#1a1126")
        btn_f.pack(pady=5)
        tk.Button(btn_f, text="👁", command=self.toggle_pass, bg=COLORS["bg"], fg=COLORS["text"], relief="flat", font=("Arial", 8), width=2).pack(side="left", padx=1)
        tk.Button(btn_f, text="📋", command=self.copy_pass, bg=COLORS["bg"], fg=COLORS["text"], relief="flat", font=("Arial", 8), width=2).pack(side="left")

    def toggle_pass(self):
        self.show_pass = not self.show_pass
        self.pvar.set(self.data.get("pass", "")[:12] if self.show_pass else "********")

    def copy_pass(self):
        self.app.clipboard_clear()
        self.app.clipboard_append(self.data.get("pass", ""))
        self.app.show_toast()

class PassManApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PassMan")
        self.geometry("450x750")
        self.configure(bg=COLORS["bg"])
        self.db, self.f, self.salt = None, None, None

        self.login_frame = tk.Frame(self, bg=COLORS["bg"])
        self.login_frame.pack(expand=True, fill="both")
        tk.Label(self.login_frame, text="SECRET_KEY", font=("Maple Mono", 18, "bold"), bg=COLORS["bg"], fg=COLORS["accent"]).pack(pady=(100, 20))
        entry_f = tk.Frame(self.login_frame, bg=COLORS["border"], padx=2, pady=2)
        entry_f.pack()
        self.mp_entry = tk.Entry(entry_f, show="*", font=("Maple Mono", 14), justify="center", bg=COLORS["card"], fg=COLORS["text"], relief="flat", insertbackground="white")
        self.mp_entry.pack()
        self.setup_entry(self.mp_entry)
        self.mp_entry.bind('<Return>', lambda e: self.login())
        tk.Checkbutton(self.login_frame, text="Pokaż klucz", bg=COLORS["bg"], fg=COLORS["text"], selectcolor=COLORS["bg"], command=self.toggle_login_visibility).pack()
        tk.Button(self.login_frame, text="ODBLOKUJ", command=self.login, bg=COLORS["accent"], fg="white", font=("Maple Mono", 12, "bold"), relief="flat", padx=20, pady=10).pack(pady=30)

    def setup_entry(self, entry, placeholder=""):
        entry.bind("<Control-v>", lambda e: self.paste_text(entry))
        entry.bind("<Control-V>", lambda e: self.paste_text(entry))
        menu = tk.Menu(self, tearoff=0, bg=COLORS["card"], fg=COLORS["text"])
        menu.add_command(label="Wklej", command=lambda: self.paste_text(entry))
        entry.bind("<Button-3>", lambda e: menu.post(e.x_root, e.y_root))
        if placeholder:
            entry.insert(0, placeholder)
            entry.bind("<FocusIn>", lambda e: self.clear_placeholder(entry, placeholder))
            entry.bind("<FocusOut>", lambda e: self.restore_placeholder(entry, placeholder))

    def clear_placeholder(self, entry, placeholder):
        if entry.get() == placeholder: entry.delete(0, tk.END)

    def restore_placeholder(self, entry, placeholder):
        if not entry.get(): entry.insert(0, placeholder)

    def paste_text(self, entry):
        try: entry.insert(tk.INSERT, self.clipboard_get())
        except: pass
        return "break"

    def toggle_login_visibility(self):
        self.mp_entry.configure(show="" if self.mp_entry.cget("show") == "*" else "*")

    def toggle_add_pass_visibility(self):
        self.p_ent.configure(show="" if self.p_ent.cget("show") == "*" else "*")

    def generate_password(self):
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = "".join(random.choice(chars) for _ in range(16))
        self.p_ent.delete(0, tk.END); self.p_ent.insert(0, pwd); self.p_ent.configure(show="")

    def show_toast(self):
        toast = tk.Label(self, text="Copied! 🪄", bg=COLORS["accent"], fg="white", font=("Maple Mono", 10, "bold"), padx=15, pady=8)
        toast.place(relx=0.5, rely=0.92, anchor="center")
        self.after(1500, toast.destroy)

    def login(self):
        mp = self.mp_entry.get()
        if not mp: return
        if not os.path.exists(DB_FILE): init_db(mp)
        db, f = load_db(mp)
        if db is None: return
        self.db, self.f = db, f
        with open(DB_FILE, "rb") as file: self.salt = file.read(16)
        self.login_frame.destroy(); self.show_main()

    def show_main(self):
        top = tk.Frame(self, bg=COLORS["card"], pady=15, padx=15)
        top.pack(fill="x")
        
        search_f = tk.Frame(top, bg=COLORS["card"])
        search_f.pack(fill="x", pady=(0, 10))
        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda n, i, m: self.refresh_list(self.search_var.get()))
        self.search_ent = tk.Entry(search_f, textvariable=self.search_var, bg=COLORS["bg"], fg=COLORS["text"], relief="flat", insertbackground="white")
        self.search_ent.pack(fill="x", ipady=3)
        self.setup_entry(self.search_ent, "Szukaj serwisu...")
        
        self.s_ent = tk.Entry(top, bg=COLORS["bg"], fg=COLORS["text"], relief="flat"); self.s_ent.pack(fill="x", pady=2)
        self.setup_entry(self.s_ent, "Serwis")
        self.u_ent = tk.Entry(top, bg=COLORS["bg"], fg=COLORS["text"], relief="flat"); self.u_ent.pack(fill="x", pady=2)
        self.setup_entry(self.u_ent, "Login")
        pf = tk.Frame(top, bg=COLORS["card"])
        pf.pack(fill="x", pady=2)
        self.p_ent = tk.Entry(pf, bg=COLORS["bg"], fg=COLORS["text"], relief="flat", show="*")
        self.p_ent.pack(side="left", fill="x", expand=True)
        self.setup_entry(self.p_ent, "Hasło")
        tk.Button(pf, text="👁", command=self.toggle_add_pass_visibility, bg=COLORS["bg"], fg=COLORS["text"], relief="flat").pack(side="left", padx=2)
        tk.Button(pf, text="🎲", command=self.generate_password, bg=COLORS["border"], fg="white", relief="flat").pack(side="left")
        tk.Button(top, text="ZAPISZ", command=self.add_entry, bg=COLORS["accent"], fg="white", relief="flat", font=("Maple Mono", 9, "bold")).pack(fill="x", pady=(10,0))

        self.canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        self.scroll_frame = tk.Frame(self.canvas, bg=COLORS["bg"])
        for i in range(3): self.scroll_frame.columnconfigure(i, weight=1)
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.pack(fill="both", expand=True, pady=10)
        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind('<Configure>', lambda e: self.canvas.itemconfig(1, width=e.width))
        self.refresh_list()

    def refresh_list(self, query=""):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        q = query.lower()
        if q == "szukaj serwisu...": q = ""
        filtered = {k: v for k, v in self.db.items() if q in k.lower()}
        for i, (site, data) in enumerate(sorted(filtered.items())):
            PasswordCard(self.scroll_frame, site, data, self).grid(row=i//3, column=i%3, sticky="nsew", padx=2, pady=2)

    def add_entry(self):
        s, u, p = self.s_ent.get(), self.u_ent.get(), self.p_ent.get()
        if s and s != "Serwis":
            self.db[s] = {"user": u, "pass": p, "date": datetime.datetime.now().strftime("%Y-%m-%d")}
            save_db(self.db, self.f, self.salt)
            self.search_var.set("")
            self.refresh_list()
            for e in [self.s_ent, self.u_ent, self.p_ent]: e.delete(0, tk.END)
            self.p_ent.configure(show="*")
            self.restore_placeholder(self.s_ent, "Serwis")
            self.restore_placeholder(self.u_ent, "Login")
            self.restore_placeholder(self.p_ent, "Hasło")

if __name__ == "__main__":
    PassManApp().mainloop()