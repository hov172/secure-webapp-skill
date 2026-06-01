#!/usr/bin/env bash
set -e

# Determine installation mode and flags.
INSTALL_DIR="$HOME/.claude/skills"
CLIENT="claude"
LOCAL=0
FORCE=0
NO_WIRE=0
for arg in "$@"; do
    case "$arg" in
        --local) INSTALL_DIR="$PWD/.claude/skills"; CLIENT="claude"; LOCAL=1 ;;
        --codex) INSTALL_DIR="$HOME/.codex/skills"; CLIENT="codex" ;;
        --local-codex) INSTALL_DIR="$PWD/.codex/skills"; CLIENT="codex"; LOCAL=1 ;;
        --gemini) INSTALL_DIR="$HOME/.gemini/skills"; CLIENT="gemini" ;;
        --local-gemini) INSTALL_DIR="$PWD/.gemini/skills"; CLIENT="gemini"; LOCAL=1 ;;
        --force) FORCE=1 ;;
        --no-wire) NO_WIRE=1 ;;
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
CUR_VER=""
if [ -f "$INSTALL_DIR/secure-webapp/VERSION" ]; then
    CUR_VER=$(tr -d '[:space:]' < "$INSTALL_DIR/secure-webapp/VERSION")
fi

# Point Codex/Gemini at the installed skill (they do not auto-load skills/).
wire_discovery() {
    [ "$NO_WIRE" -eq 1 ] && return 0
    [ "$CLIENT" = "claude" ] && return 0

    local disc rel import_line file
    if [ "$CLIENT" = "codex" ]; then disc="AGENTS.md"; else disc="GEMINI.md"; fi
    if [ "$LOCAL" -eq 1 ]; then
        file="$PWD/$disc"
        rel=".$CLIENT/skills/secure-webapp/SKILL.md"
    else
        file="$HOME/.$CLIENT/$disc"
        rel="skills/secure-webapp/SKILL.md"
    fi
    import_line=""
    [ "$CLIENT" = "gemini" ] && import_line="@$rel"$'\n\n'

    local block
    block="<!-- secure-webapp:begin (managed by the secure-webapp installer) -->
## secure-webapp skill

${import_line}The **secure-webapp** skill (OWASP-grounded web-app security guidance) is installed at \`${rel}\`. When working on web-app code or design involving auth, sessions, tokens (JWT/OAuth/OIDC), user input, DB queries, file uploads, API endpoints, cookies/CORS/CSP/CSRF, security headers, secrets, redirects, SSRF, logging, dependencies, or threat modeling, read that \`SKILL.md\` and follow it, loading only the \`references/*.md\` it routes to.

Explicit modes: \`\$secure-webapp audit | quick-check | harden | remediate | design-review | report | update | maintain\`.
<!-- secure-webapp:end -->"

    mkdir -p "$(dirname "$file")"
    if [ -f "$file" ] && grep -q 'secure-webapp:begin' "$file"; then
        awk 'BEGIN{s=0} /secure-webapp:begin/{s=1} s==0{print} /secure-webapp:end/{s=0}' "$file" > "$file.swtmp"
        mv "$file.swtmp" "$file"
    fi
    { [ -s "$file" ] && printf '\n'; printf '%s\n' "$block"; } >> "$file"
    echo "Wired discovery -> $file"
}

if [ "$FORCE" -eq 0 ] && [ -n "$NEW_VER" ] && [ "$NEW_VER" = "$CUR_VER" ]; then
    echo "Already up to date (version $CUR_VER) at $INSTALL_DIR/secure-webapp"
    wire_discovery
    echo "Use --force to reinstall anyway."
    rm -rf "$TEMP_DIR"
    exit 0
fi

echo "Unpacking into $INSTALL_DIR..."
# The zip contains a top-level secure-webapp directory, so unpacking it
# into skills/ will correctly create skills/secure-webapp/
unzip -q -o "$TEMP_DIR/secure-webapp.skill" -d "$INSTALL_DIR"

rm -rf "$TEMP_DIR"

wire_discovery

echo "✅ Installation complete!"
echo "Installed version ${NEW_VER:-unknown} to: $INSTALL_DIR/secure-webapp"
