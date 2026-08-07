#!/usr/bin/env bash
#
# SessionStart hook: keep the installed secure-webapp skill current.
#
# Register it with:  node scripts/setup-session-hook.js
#
# Modes (first match wins):
#   $SECURE_WEBAPP_UPDATE_MODE
#   mode=<value> in ~/.claude/secure-webapp-update.conf
#   default: auto
#
#   auto   - install newer releases in the background, report next session
#   notify - report that a newer release exists; never installs
#   off    - do nothing
#
# Always exits 0. A failure here must never block session startup.

set -uo pipefail

# Resolve the skill root from this script's own location so the hook works for
# whichever client it was installed under (.claude, .codex, .gemini).
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SKILL_DIR=$(dirname "$SCRIPT_DIR")
VERSION_FILE="$SKILL_DIR/VERSION"

STATE_DIR="$HOME/.claude"
CONF_FILE="$STATE_DIR/secure-webapp-update.conf"
STAMP_FILE="$STATE_DIR/.secure-webapp-update-check"
RESULT_FILE="$STATE_DIR/.secure-webapp-update-result"
LOCK_DIR="$STATE_DIR/.secure-webapp-update.lock"
LOG_FILE="$STATE_DIR/secure-webapp-update.log"

REMOTE_URL="https://raw.githubusercontent.com/hov172/secure-webapp-skill/main/VERSION"
INSTALL_PKG="github:hov172/secure-webapp-skill"
THROTTLE_SECONDS=86400
LOCK_STALE_SECONDS=900
FETCH_TIMEOUT=4

log_entry() {
    printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" >> "$LOG_FILE" 2>/dev/null || true
}

emit_json() {
    # emit_json <systemMessage> <additionalContext>
    if command -v jq >/dev/null 2>&1; then
        jq -n --arg msg "$1" --arg ctx "$2" \
            '{systemMessage: $msg, hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
    else
        printf '{"systemMessage":"%s","hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$1" "$2"
    fi
}

resolve_mode() {
    local mode="${SECURE_WEBAPP_UPDATE_MODE:-}"
    if [ -z "$mode" ] && [ -f "$CONF_FILE" ]; then
        mode=$(sed -n 's/^[[:space:]]*mode[[:space:]]*=[[:space:]]*\([a-z]*\).*/\1/p' "$CONF_FILE" | tail -1)
    fi
    case "$mode" in
        notify|auto|off) printf '%s' "$mode" ;;
        *) printf 'auto' ;;
    esac
}

MODE=$(resolve_mode)
[ "$MODE" = "off" ] && exit 0

# Not installed -> nothing to update.
[ -f "$VERSION_FILE" ] || exit 0

mkdir -p "$STATE_DIR" 2>/dev/null

# An auto-install from a previous session reports its result here, exactly once.
if [ -f "$RESULT_FILE" ]; then
    result=$(cat "$RESULT_FILE" 2>/dev/null)
    rm -f "$RESULT_FILE" 2>/dev/null
    if [ -n "$result" ]; then
        emit_json "secure-webapp skill: $result" \
            "The secure-webapp skill was auto-updated in the background: $result. The running install now reflects that version."
        exit 0
    fi
fi

now=$(date +%s)
if [ -f "$STAMP_FILE" ]; then
    last=$(cat "$STAMP_FILE" 2>/dev/null || echo 0)
    case "$last" in
        ''|*[!0-9]*) last=0 ;;
    esac
    [ $((now - last)) -lt "$THROTTLE_SECONDS" ] && exit 0
fi

local_version=$(tr -d '[:space:]' < "$VERSION_FILE")
remote_version=$(curl -fsS --max-time "$FETCH_TIMEOUT" "$REMOTE_URL" 2>/dev/null | tr -d '[:space:]')

# Network failure or a garbage response: stay quiet, and do not burn the
# throttle window so the next session retries.
[ -n "$remote_version" ] || exit 0
case "$remote_version" in
    [0-9]*) ;;
    *) exit 0 ;;
esac

printf '%s' "$now" > "$STAMP_FILE"

# Only act when the remote is strictly newer.
[ "$local_version" = "$remote_version" ] && exit 0
newest=$(printf '%s\n%s\n' "$local_version" "$remote_version" | sort -V | tail -1)
[ "$newest" = "$remote_version" ] || exit 0

if [ "$MODE" = "notify" ]; then
    emit_json \
        "secure-webapp skill: v$remote_version available (installed v$local_version). Run \`\$secure-webapp update\` to upgrade." \
        "A newer secure-webapp skill release is available: v$remote_version (installed v$local_version). If the user works with this skill or asks about it, offer to run \`\$secure-webapp update\` (which runs npx --yes $INSTALL_PKG --global). Do not run it unprompted."
    exit 0
fi

# ---- auto mode ----

# Take the lock before forking. The owning timestamp is written by THIS process,
# so a competitor can never observe a created-but-unowned lock; an empty stamp
# means "acquired microseconds ago", which is the freshest lock possible.
if mkdir "$LOCK_DIR" 2>/dev/null; then
    date +%s > "$LOCK_DIR/ts" 2>/dev/null
else
    lock_ts=$(cat "$LOCK_DIR/ts" 2>/dev/null)
    case "$lock_ts" in
        ''|*[!0-9]*)
            log_entry "SKIP locked just_acquired"
            exit 0
            ;;
    esac
    lock_age=$((now - lock_ts))
    if [ "$lock_age" -gt "$LOCK_STALE_SECONDS" ]; then
        log_entry "STALE_LOCK age=${lock_age}s - reclaiming"
        rm -rf "$LOCK_DIR" 2>/dev/null
        mkdir "$LOCK_DIR" 2>/dev/null || { log_entry "SKIP lock_contested"; exit 0; }
        date +%s > "$LOCK_DIR/ts" 2>/dev/null
    else
        log_entry "SKIP locked age=${lock_age}s"
        exit 0
    fi
fi

# The installer overwrites this very file mid-run, and bash reads a script
# incrementally -- continuing to execute from a replaced file is undefined.
# Run the install from a detached copy that nothing rewrites.
RUNNER=$(mktemp "${TMPDIR:-/tmp}/secure-webapp-update.XXXXXX") || {
    rm -rf "$LOCK_DIR" 2>/dev/null
    log_entry "FAILED mktemp"
    exit 0
}

cat > "$RUNNER" <<'RUNNER_EOF'
#!/usr/bin/env bash
trap 'rm -rf "$SWA_LOCK_DIR" 2>/dev/null; rm -f "$0" 2>/dev/null' EXIT

stamp() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" >> "$SWA_LOG" 2>/dev/null || true; }

# Hooks can inherit a minimal PATH that lacks node; mirror the installer's fallback.
command -v npx >/dev/null 2>&1 || export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v npx >/dev/null 2>&1; then
    stamp "FAILED npx_not_found"
    printf 'auto-update FAILED: npx not found - see %s' "$SWA_LOG" > "$SWA_RESULT" 2>/dev/null
    exit 0
fi

stamp "UPDATING $SWA_FROM -> $SWA_TO"
if npx --yes "$SWA_PKG" --global >> "$SWA_LOG" 2>&1; then
    installed=$(tr -d '[:space:]' < "$SWA_VERSION_FILE" 2>/dev/null)
    stamp "UPDATED to=$installed"
    printf 'auto-updated to v%s (was v%s)' "$installed" "$SWA_FROM" > "$SWA_RESULT" 2>/dev/null
else
    stamp "FAILED install_exit_nonzero"
    printf 'auto-update to v%s FAILED - see %s' "$SWA_TO" "$SWA_LOG" > "$SWA_RESULT" 2>/dev/null
fi
RUNNER_EOF

SWA_LOCK_DIR="$LOCK_DIR" \
SWA_LOG="$LOG_FILE" \
SWA_RESULT="$RESULT_FILE" \
SWA_VERSION_FILE="$VERSION_FILE" \
SWA_PKG="$INSTALL_PKG" \
SWA_FROM="$local_version" \
SWA_TO="$remote_version" \
    nohup bash "$RUNNER" >/dev/null 2>&1 &

emit_json \
    "secure-webapp skill: installing v$remote_version in the background (was v$local_version)." \
    "The secure-webapp skill is auto-updating to v$remote_version in the background. Files under the skill directory are being replaced during this session; the new version takes effect next session. Do not run the updater again."
exit 0
