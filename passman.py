import os
import json
import base64
import datetime
import tkinter as tk
from tkinter import messagebox
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet

DIR_PATH = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(DIR_PATH, "passwords.enc")

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
        super().__init__(parent, relief="flat", bg="#2e1065", bd=0)
        self.site = site
        self.data = data
        self.app = app
        self.is_flipped = False
        self.show_pass = False
        self.pack(fill="x", pady=6, padx=10, ipady=10)
        self.build_front()

    def build_front(self):
        for w in self.winfo_children(): w.destroy()
        self.configure(bg="#2e1065", cursor="hand2")
        lbl = tk.Label(self, text=self.site, font=("Arial", 14, "bold"), bg="#2e1065", fg="white", cursor="hand2")
        lbl.pack(pady=15)
        lbl.bind("<Button-1>", self.flip)
        self.bind("<Button-1>", self.flip)

    def flip(self, event=None):
        self.is_flipped = True
        for w in self.winfo_children(): w.destroy()
        self.configure(bg="#1e1e2e", cursor="arrow")

        tk.Label(self, text=self.site.upper(), font=("Arial", 10, "bold"), bg="#1e1e2e", fg="#a855f7").pack(anchor="w", padx=10, pady=(5,0))
        tk.Label(self, text=f"LOGIN: {self.data.get('user', '')}", bg="#1e1e2e", fg="white", font=("Arial", 10)).pack(anchor="w", padx=10)

        pf = tk.Frame(self, bg="#1e1e2e", cursor="hand2")
        pf.pack(fill="x", padx=10, pady=2)
        
        self.pvar = tk.StringVar(value="********")
        tk.Label(pf, text="PASSWORD: ", bg="#1e1e2e", fg="white", font=("Arial", 10), cursor="hand2").pack(side="left")
        tk.Label(pf, textvariable=self.pvar, bg="#1e1e2e", fg="#f38ba8", font=("Courier", 10, "bold"), cursor="hand2").pack(side="left")
        
        tk.Button(pf, text="👁", command=self.toggle_pass, bg="#313244", fg="white", relief="flat", width=2, cursor="hand2").pack(side="right")

        date_str = self.data.get("date", "Brak")
        color = "#a6e3a1" 
        if date_str != "Brak":
            try:
                d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                if (datetime.datetime.now() - d).days > 180:
                    color = "#f38ba8"
            except: pass

        tk.Label(self, text=f"ADDED: {date_str}", fg=color, bg="#1e1e2e", font=("Arial", 8, "bold")).pack(anchor="w", padx=10, pady=(0,5))

        for w in [self, pf]:
            w.bind("<Button-1>", self.copy_pass)

    def toggle_pass(self):
        self.show_pass = not self.show_pass
        self.pvar.set(self.data.get("pass", "") if self.show_pass else "********")

    def copy_pass(self, event=None):
        self.app.clipboard_clear()
        self.app.clipboard_append(self.data.get("pass", ""))
        self.app.show_toast()

class PassManApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PassMan")
        self.geometry("400x650")
        self.configure(bg="#11111b")
        
        try:
            img = tk.PhotoImage(file=os.path.join(DIR_PATH, "passmanico.png"))
            self.iconphoto(False, img)
        except: pass

        self.db = None
        self.f = None
        self.salt = None

        self.login_frame = tk.Frame(self, bg="#11111b")
        self.login_frame.pack(expand=True)

        tk.Label(self.login_frame, text="Hasło Główne", font=("Arial", 14, "bold"), bg="#11111b", fg="white").pack(pady=10)
        self.mp_entry = tk.Entry(self.login_frame, show="*", font=("Arial", 14), justify="center")
        self.mp_entry.pack(pady=10)
        self.mp_entry.bind('<Return>', lambda e: self.login())

        btn_text = "Odblokuj" if os.path.exists(DB_FILE) else "Utwórz Sejf"
        tk.Button(self.login_frame, text=btn_text, command=self.login, bg="#8b5cf6", fg="white", font=("Arial", 12, "bold"), relief="flat", cursor="hand2").pack(pady=20)

        self.toast = tk.Label(self, text="Skopiowano do schowka!", bg="#a6e3a1", fg="black", font=("Arial", 10, "bold"), padx=10, pady=5)

    def show_toast(self):
        self.toast.place(relx=0.5, rely=0.92, anchor="center")
        self.after(2000, self.toast.place_forget)

    def login(self):
        mp = self.mp_entry.get()
        if not mp: return
        
        if not os.path.exists(DB_FILE):
            init_db(mp)

        db, f = load_db(mp)
        if db is None:
            messagebox.showerror("Błąd", "Błędne hasło główne!")
            return

        self.db = db
        self.f = f
        with open(DB_FILE, "rb") as file:
            self.salt = file.read(16)

        self.login_frame.destroy()
        self.show_main()

    def show_main(self):
        top = tk.Frame(self, bg="#1e1e2e", pady=15, padx=15)
        top.pack(fill="x")

        tk.Label(top, text="DODAJ NOWY WPIS", bg="#1e1e2e", fg="#a855f7", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,5))
        
        row1 = tk.Frame(top, bg="#1e1e2e")
        row1.pack(fill="x", pady=2)
        self.s_ent = tk.Entry(row1, width=15); self.s_ent.pack(side="left", padx=(0,5), fill="x", expand=True)
        self.u_ent = tk.Entry(row1, width=15); self.u_ent.pack(side="left", fill="x", expand=True)
        
        row2 = tk.Frame(top, bg="#1e1e2e")
        row2.pack(fill="x", pady=4)
        self.p_ent = tk.Entry(row2, show="*"); self.p_ent.pack(side="left", padx=(0,5), fill="x", expand=True)
        tk.Button(row2, text="Dodaj", command=self.add_entry, bg="#8b5cf6", fg="white", relief="flat", font=("Arial", 9, "bold"), cursor="hand2").pack(side="left", ipadx=5)

        self.s_ent.insert(0, "Serwis"); self.u_ent.insert(0, "Login"); self.p_ent.insert(0, "Hasło")

        canvas = tk.Canvas(self, bg="#11111b", highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scroll_frame = tk.Frame(canvas, bg="#11111b")

        self.scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind('<Configure>', configure_canvas_width)

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=(10,0), pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)

        self.refresh_list()

    def refresh_list(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        for site, data in self.db.items():
            PasswordCard(self.scroll_frame, site, data, self)

    def add_entry(self):
        s, u, p = self.s_ent.get(), self.u_ent.get(), self.p_ent.get()
        if s and u and p and s != "Serwis":
            self.db[s] = {
                "user": u, 
                "pass": p, 
                "date": datetime.datetime.now().strftime("%Y-%m-%d")
            }
            save_db(self.db, self.f, self.salt)
            self.refresh_list()
            self.s_ent.delete(0, tk.END); self.u_ent.delete(0, tk.END); self.p_ent.delete(0, tk.END)

if __name__ == "__main__":
    app = PassManApp()
    app.mainloop()