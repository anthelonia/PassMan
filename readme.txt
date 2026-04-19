# PassMan 🛡️

A lightweight, secure password manager for Linux enthusiasts. 

PassMan uses **PBKDF2HMAC** for key derivation and **Fernet (AES-128)** for encryption. 
Everything is locked behind a single Master Password. 
If you forget it, your passwords are gone forever—just the way it should be.

---

## 🔒 Security & Privacy

* **Local Only:** This repository contains only the application code.
* **No Cloud Leaks:** The `passwords.enc` file is explicitly ignored via `.gitignore`. Your encrypted database never leaves your machine.
* **Master Password:** Your data is only decrypted in memory when you provide the correct master password.

---

## ✨ Features

* **Visual Expiry:** Passwords turn red if they are older than 180 days.
* **Quick Copy:** Click any entry to copy the password and get a toast notification.
* **Clean UI:** Built with Tkinter, featuring a dark Catppuccin-inspired theme.

---

## 🚀 Installation

```bash
git clone [https://github.com/anthelonia/passman.git](https://github.com/anthelonia/passman.git)
cd passman
chmod +x install.sh
./install.sh

---

## 💻 Syncing across devices

Since passwords.enc is not pushed to GitHub for security reasons, to sync your passwords you must:

Copy the passwords.enc file manually to your second device (via USB, Syncthing, etc.).

Place it in the same folder as passman.py.
