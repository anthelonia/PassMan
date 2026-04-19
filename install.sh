#!/bin/bash
echo "Installing PassMan 🛡️..."

sudo pacman -S --needed python tk

DIR=$(pwd)
VENV_DIR="$DIR/venv"

if [ ! -d "$VENV_DIR" ]; then
    echo "Tworzenie piaskownicy (venv)..."
    python3 -m venv "$VENV_DIR"
fi

echo "Pobieranie CustomTkinter i Cryptography..."
"$VENV_DIR/bin/pip" install customtkinter cryptography

BIN_PATH="$DIR/passman.py"
ICON_PATH="$DIR/passmanico.png"

cat << EOT > ~/.local/share/applications/passman.desktop
[Desktop Entry]
Name=PassMan
Exec="$VENV_DIR/bin/python3" "$BIN_PATH"
Icon=$ICON_PATH
Type=Application
Terminal=false
Categories=Utility;Security;
EOT

chmod +x passman.py
echo "All done."