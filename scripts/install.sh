#!/usr/bin/env bash
set -e

echo "Installing secure-webapp skill..."

# Determine installation mode (global by default unless local flag is passed)
INSTALL_DIR="$HOME/.claude/skills"
if [ "$1" = "--local" ]; then
    INSTALL_DIR="$PWD/.claude/skills"
elif [ "$1" = "--codex" ]; then
    INSTALL_DIR="$HOME/.codex/skills"
elif [ "$1" = "--local-codex" ]; then
    INSTALL_DIR="$PWD/.codex/skills"
fi

mkdir -p "$INSTALL_DIR"

# Download the latest release asset
TEMP_DIR=$(mktemp -d)
echo "Downloading latest release..."
curl -sL "https://github.com/hov172/secure-webapp-skill/releases/latest/download/secure-webapp.skill" -o "$TEMP_DIR/secure-webapp.skill"

echo "Unpacking into $INSTALL_DIR..."
# The zip contains a top-level secure-webapp directory, so unpacking it
# into skills/ will correctly create skills/secure-webapp/
unzip -q -o "$TEMP_DIR/secure-webapp.skill" -d "$INSTALL_DIR"

rm -rf "$TEMP_DIR"

echo "✅ Installation complete!"
echo "Installed to: $INSTALL_DIR/secure-webapp"
