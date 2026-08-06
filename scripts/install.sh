#!/usr/bin/env bash
set -e

# Determine installation mode and flags.
INSTALL_DIR="$HOME/.claude/skills"
CLIENT="claude"
LOCAL=0
FORCE=0
NO_WIRE=0
NO_VERIFY=0
for arg in "$@"; do
    case "$arg" in
        --local) INSTALL_DIR="$PWD/.claude/skills"; CLIENT="claude"; LOCAL=1 ;;
        --codex) INSTALL_DIR="$HOME/.codex/skills"; CLIENT="codex" ;;
        --local-codex) INSTALL_DIR="$PWD/.codex/skills"; CLIENT="codex"; LOCAL=1 ;;
        --gemini) INSTALL_DIR="$HOME/.gemini/skills"; CLIENT="gemini" ;;
        --local-gemini) INSTALL_DIR="$PWD/.gemini/skills"; CLIENT="gemini"; LOCAL=1 ;;
        --force) FORCE=1 ;;
        --no-wire) NO_WIRE=1 ;;
        --no-verify) NO_VERIFY=1 ;;
    esac
done

# Verify the downloaded archive against the SHA256SUMS published with the same
# release. Fails closed: a mismatch, a missing sums file, or no available hash
# tool aborts the install. --no-verify is the documented escape hatch.
verify_checksum() {
    local archive="$1" sums="$2"
    if [ "$NO_VERIFY" -eq 1 ]; then
        echo "⚠️  Skipping checksum verification (--no-verify)."
        return 0
    fi
    if [ ! -s "$sums" ]; then
        echo "❌ Could not download SHA256SUMS for this release; refusing to install."
        echo "   Re-run with --no-verify to override."
        return 1
    fi

    local expected actual
    expected=$(awk '$2 ~ /secure-webapp\.skill$/ {print $1; exit}' "$sums")
    if [ -z "$expected" ]; then
        echo "❌ SHA256SUMS has no entry for secure-webapp.skill; refusing to install."
        return 1
    fi

    if command -v sha256sum >/dev/null 2>&1; then
        actual=$(sha256sum "$archive" | awk '{print $1}')
    elif command -v shasum >/dev/null 2>&1; then
        actual=$(shasum -a 256 "$archive" | awk '{print $1}')
    else
        echo "❌ No sha256sum or shasum available to verify the download."
        echo "   Install one, or re-run with --no-verify to override."
        return 1
    fi

    if [ "$actual" != "$expected" ]; then
        echo "❌ Checksum mismatch — refusing to install."
        echo "   expected: $expected"
        echo "   actual:   $actual"
        return 1
    fi
    echo "Checksum verified (sha256 ${actual:0:16}...)."
}

echo "Installing secure-webapp skill..."
mkdir -p "$INSTALL_DIR"

# Download the latest release asset.
TEMP_DIR=$(mktemp -d)
RELEASE_BASE="https://github.com/hov172/secure-webapp-skill/releases/latest/download"
echo "Downloading latest release..."
curl -fsSL "$RELEASE_BASE/secure-webapp.skill" -o "$TEMP_DIR/secure-webapp.skill"
curl -fsSL "$RELEASE_BASE/SHA256SUMS" -o "$TEMP_DIR/SHA256SUMS" || true

if ! verify_checksum "$TEMP_DIR/secure-webapp.skill" "$TEMP_DIR/SHA256SUMS"; then
    rm -rf "$TEMP_DIR"
    exit 1
fi

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

${import_line}The **secure-webapp** skill (OWASP-grounded web-app security guidance) is installed at \`${rel}\`. When working on web-app code or design involving auth, sessions, tokens (JWT/OAuth/OIDC), user input, DB queries, file uploads, API endpoints, cookies/CORS/CSP/CSRF, security headers, secrets, redirects, SSRF, logging, dependencies, threat modeling, or LLM/AI features (prompt construction, RAG, agent tools, MCP servers), read that \`SKILL.md\` and follow it, loading only the \`references/*.md\` it routes to.

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
