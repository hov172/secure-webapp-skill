#!/usr/bin/env node

/**
 * Opt-in SessionStart update check for the secure-webapp skill.
 *
 * Registers scripts/session-start-update-check.sh as a Claude Code SessionStart
 * hook in ~/.claude/settings.json. The hook compares the installed VERSION
 * against the published one and -- depending on mode -- either reports that a
 * newer release exists or installs it in the background.
 *
 *   node scripts/setup-session-hook.js                # enable (mode: auto)
 *   node scripts/setup-session-hook.js --mode=notify  # enable, report only
 *   node scripts/setup-session-hook.js --check        # show the plan, change nothing
 *   node scripts/setup-session-hook.js --disable      # remove the hook
 *
 * This is the session-start counterpart to setup-auto-update.js, which
 * schedules the same installer on a timer instead.
 */

const os = require('os');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const disable = args.includes('--disable');
const checkOnly = args.includes('--check');

const MODES = ['auto', 'notify', 'off'];
const modeArg = args.find((a) => a.startsWith('--mode='));
const mode = modeArg ? modeArg.slice('--mode='.length) : 'auto';

const CLAUDE_DIR = path.join(os.homedir(), '.claude');
const SETTINGS = path.join(CLAUDE_DIR, 'settings.json');
const CONF = path.join(CLAUDE_DIR, 'secure-webapp-update.conf');
const HOOK = path.join(__dirname, 'session-start-update-check.sh');
const STATUS = 'Checking secure-webapp version...';

function log(msg) {
    console.log(msg);
}

function readSettings() {
    if (!fs.existsSync(SETTINGS)) return {};
    const raw = fs.readFileSync(SETTINGS, 'utf8');
    if (!raw.trim()) return {};
    // A malformed settings.json silently disables every setting in it. Never
    // overwrite one we could not parse.
    return JSON.parse(raw);
}

// Our entry is identified by the hook filename, so a moved install is still
// recognized and replaced rather than duplicated.
function isOurs(entry) {
    return (
        entry &&
        typeof entry.command === 'string' &&
        entry.command.includes('session-start-update-check.sh')
    );
}

function stripOurs(sessionStart) {
    return sessionStart
        .map((group) => ({
            ...group,
            hooks: (group.hooks || []).filter((h) => !isOurs(h)),
        }))
        .filter((group) => (group.hooks || []).length > 0);
}

function writeConfMode(value) {
    const body = [
        '# secure-webapp skill update behavior, read by the SessionStart hook at',
        '# <skill>/scripts/session-start-update-check.sh',
        '#',
        '#   auto   - install newer releases in the background at session start (default)',
        '#   notify - report that a newer release exists; never installs',
        '#   off    - disable the check entirely',
        '#',
        '# The SECURE_WEBAPP_UPDATE_MODE environment variable overrides this file.',
        '# Checks are throttled to once per 24h; activity is logged to',
        '# ~/.claude/secure-webapp-update.log',
        '',
        `mode=${value}`,
        '',
    ].join('\n');
    fs.writeFileSync(CONF, body);
}

function main() {
    if (!MODES.includes(mode)) {
        console.error(`❌ Unknown --mode=${mode}. Expected one of: ${MODES.join(', ')}`);
        process.exit(1);
    }
    if (!fs.existsSync(HOOK)) {
        console.error(`❌ Hook script not found: ${HOOK}`);
        process.exit(1);
    }

    let settings;
    try {
        settings = readSettings();
    } catch (error) {
        console.error(`❌ Could not parse ${SETTINGS}: ${error.message}`);
        console.error('   Fix the JSON first - this script will not overwrite it.');
        process.exit(1);
    }

    const hooks = settings.hooks || {};
    const sessionStart = Array.isArray(hooks.SessionStart) ? hooks.SessionStart : [];
    const installed = sessionStart.some((g) => (g.hooks || []).some(isOurs));

    if (checkOnly) {
        log(`settings: ${SETTINGS}`);
        log(`hook:     ${HOOK}`);
        log(`state:    ${installed ? 'registered' : 'not registered'}`);
        log(`mode:     ${fs.existsSync(CONF) ? `${CONF} (existing)` : `${mode} (would be written)`}`);
        log('\nCheck complete. Re-run without --check to apply.');
        return;
    }

    if (disable) {
        if (!installed) {
            log('SessionStart update check is not registered - nothing to do.');
            return;
        }
        const next = stripOurs(sessionStart);
        const nextHooks = { ...hooks };
        if (next.length) nextHooks.SessionStart = next;
        else delete nextHooks.SessionStart;
        const nextSettings = { ...settings, hooks: nextHooks };
        if (!Object.keys(nextHooks).length) delete nextSettings.hooks;
        fs.writeFileSync(SETTINGS, `${JSON.stringify(nextSettings, null, 2)}\n`);
        log(`✅ Removed the SessionStart update check from ${SETTINGS}`);
        log('   ~/.claude/secure-webapp-update.conf was left in place.');
        return;
    }

    // Replace any previous entry so re-running never stacks duplicates.
    const cleaned = stripOurs(sessionStart);
    const entry = { type: 'command', command: HOOK, timeout: 10, statusMessage: STATUS };
    const nextSessionStart = cleaned.length
        ? [{ ...cleaned[0], hooks: [...cleaned[0].hooks, entry] }, ...cleaned.slice(1)]
        : [{ hooks: [entry] }];

    const nextSettings = {
        ...settings,
        hooks: { ...hooks, SessionStart: nextSessionStart },
    };

    if (!fs.existsSync(CLAUDE_DIR)) fs.mkdirSync(CLAUDE_DIR, { recursive: true });
    fs.writeFileSync(SETTINGS, `${JSON.stringify(nextSettings, null, 2)}\n`);
    if (!fs.existsSync(CONF) || modeArg) writeConfMode(mode);

    log(`✅ ${installed ? 'Updated' : 'Registered'} the SessionStart update check`);
    log(`   settings: ${SETTINGS}`);
    log(`   hook:     ${HOOK}`);
    log(`   mode:     ${mode}  (change it in ${CONF})`);
    log('\nIt takes effect in your next Claude Code session.');
    log('Checks are throttled to once per 24h; see ~/.claude/secure-webapp-update.log');
}

main();
