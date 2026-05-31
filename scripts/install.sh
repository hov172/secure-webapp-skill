#!/usr/bin/env bash
set -e

# Determine installation mode and flags.
INSTALL_DIR="$HOME/.claude/skills"
FORCE=0
for arg in "$@"; do
    case "$arg" in
        --local) INSTALL_DIR="$PWD/.claude/skills" ;;
        --codex) INSTALL_DIR="$HOME/.codex/skills" ;;
        --local-codex) INSTALL_DIR="$PWD/.codex/skills" ;;
        --gemini) INSTALL_DIR="$HOME/.gemini/skills" ;;
        --local-gemini) INSTALL_DIR="$PWD/.gemini/skills" ;;
        --force) FORCE=1 ;;
    esac
done

echo "Installing secure-webapp skill..."
mkdir -p "$INSTALL_DIR"

# Download the latest release asset.
TEMP_DIR=$(mktemp -d)
echo "Downloading latest release..."
curl -sL "https://github.com/hov172/secure-webapp-skill/releases/latest/download/secure-webapp.skill" -o "$TEMP_DIR/secure-webapp.skill"

# Compare the packaged version with what is already installed and skip when current.
NEW_VER=$(unzip -p "$TEMP_DIR/secure-webapp.skill" secure-webapp/VERSION 2>/dev/null | tr -d '[:space:]' || true)
CUR_VER=$(tr -d '[:space:]' < "$INSTALL_DIR/secure-webapp/VERSION" 2>/dev/null || true)

if [ "$FORCE" -eq 0 ] && [ -n "$NEW_VER" ] && [ "$NEW_VER" = "$CUR_VER" ]; then
    echo "Already up to date (version $CUR_VER) at $INSTALL_DIR/secure-webapp"
    echo "Use --force to reinstall anyway."
    rm -rf "$TEMP_DIR"
    exit 0
fi

echo "Unpacking into $INSTALL_DIR..."
# The zip contains a top-level secure-webapp directory, so unpacking it
# into skills/ will correctly create skills/secure-webapp/
unzip -q -o "$TEMP_DIR/secure-webapp.skill" -d "$INSTALL_DIR"

rm -rf "$TEMP_DIR"

echo "✅ Installation complete!"
echo "Installed version ${NEW_VER:-unknown} to: $INSTALL_DIR/secure-webapp"
