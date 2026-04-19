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

---

## ⚠️ Known limitations
 
This is a local, single-user app built on Python and Tkinter. Some things can't be fixed at the application level—here's what to be aware of:
 
**Clipboard.** Tkinter runs via XWayland on Hyprland, which means the clipboard isn't isolated from other X11 apps. The 30-second auto-clear helps, but during that window another process could technically read it. Don't use this on a machine you don't trust.
 
**Memory.** When unlocked, your passwords live in Python's memory. Python doesn't let you securely wipe RAM—setting a variable to `None` removes the reference, but the garbage collector decides when to actually clear it. This is a Python limitation, not something fixable here. Close the app when you're done with it, and encrypt your swap partition (`/etc/crypttab`).
 
**Keyloggers.** The master password goes through a normal text field. If something is already logging your keystrokes, there's nothing an app can do about that.
 
**Master password.** There's no recovery. Forget the password, lose everything—on purpose. Use a passphrase you'll remember, or write it down and keep it somewhere physically safe.
 
**Swap/hibernation.** If your system hibernates while PassMan is open, decrypted data may end up on disk. Encrypt your swap or just close the app before walking away.
