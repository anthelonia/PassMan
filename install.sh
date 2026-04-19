#!/bin/bash
echo "Installing PassMan 🛡️..."

sudo pacman -S --needed python-cryptography python-tcl

DIR=$(pwd)
BIN_PATH=$DIR/passman.py
ICON_PATH=$DIR/passmanico.png

cat << EOT > ~/.local/share/applications/passman.desktop
[Desktop Entry]
Name=PassMan
Exec=python3 $BIN_PATH
Icon=$ICON_PATH
Type=Application
Terminal=false
Categories=Utility;Security;
EOT

chmod +x passman.py
echo "All done."
