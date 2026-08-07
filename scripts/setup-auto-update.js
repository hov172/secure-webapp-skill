#!/usr/bin/env node

/**
 * Cross-platform opt-in background auto-update for the secure-webapp skill.
 *
 * Registers a scheduled job that runs the version-checked installer
 * (`npx --yes github:hov172/secure-webapp-skill --global`) on a timer. Because
 * the installer skips clients that are already current, running it on a
 * schedule is cheap and only does work when a new version is published.
 *
 *   node scripts/setup-auto-update.js            # enable (weekly)
 *   node scripts/setup-auto-update.js --daily    # enable (daily)
 *   node scripts/setup-auto-update.js --check     # show the plan, change nothing
 *   node scripts/setup-auto-update.js --disable   # remove the scheduled job
 *
 * Platforms: macOS (launchd), Windows (Task Scheduler), Linux (cron).
 */

const os = require('os');
const fs = require('fs');
const path = require('path');
const { execFileSync, execSync } = require('child_process');

const args = process.argv.slice(2);
const disable = args.includes('--disable');
const checkOnly = args.includes('--check');
const daily = args.includes('--daily');
const cadence = daily ? 'daily' : 'weekly';

const LABEL = 'com.hov172.secure-webapp-update';
const TASK = 'secure-webapp-update';
const UPDATE_ARGS = ['--yes', 'github:hov172/secure-webapp-skill', '--global'];

// Scheduled jobs run with a minimal PATH: launchd gives them /usr/bin:/bin:
// /usr/sbin:/sbin and cron is no better. Writing npx's absolute path is enough
// to *find* npx, but npx is itself a `#!/usr/bin/env node` script, so node must
// also be resolvable from PATH or the job dies at the shebang with
// "env: node: No such file or directory". Always export a PATH containing the
// interpreter's own directory.
const BASE_PATH = ['/usr/local/bin', '/usr/bin', '/bin', '/usr/sbin', '/sbin'];

function log(msg) {
    console.log(msg);
}

function which(name) {
    try {
        const cmd = process.platform === 'win32' ? `where ${name}` : `command -v ${name}`;
        const out = execSync(cmd, { encoding: 'utf8' }).split(/\r?\n/)[0].trim();
        return out || name;
    } catch (_) {
        return name;
    }
}

// PATH for the scheduled job: the directory holding npx, the directory holding
// the node binary running this script (nvm/fnm/volta keep them apart), then the
// standard system locations. De-duplicated, order preserved.
function jobPath(npxPath) {
    const dirs = [path.dirname(npxPath), path.dirname(process.execPath), ...BASE_PATH];
    return [...new Set(dirs)].join(':');
}

// Scheduled failures are invisible unless the job writes somewhere. Without a
// log a broken job looks healthy in `launchctl list` indefinitely.
function logFile() {
    return path.join(os.homedir(), 'Library', 'Logs', `${LABEL}.log`);
}

function macSetup() {
    const npx = which('npx');
    const plistPath = path.join(os.homedir(), 'Library', 'LaunchAgents', `${LABEL}.plist`);
    const calendar = daily
        ? '    <key>Hour</key><integer>9</integer>\n    <key>Minute</key><integer>0</integer>'
        : '    <key>Weekday</key><integer>0</integer>\n    <key>Hour</key><integer>9</integer>\n    <key>Minute</key><integer>0</integer>';

    if (checkOnly) {
        log(`Platform : macOS (launchd)`);
        log(`Plist    : ${plistPath}`);
        log(`Schedule : ${cadence} at 09:00`);
        log(`Command  : ${npx} ${UPDATE_ARGS.join(' ')}`);
        log(`PATH     : ${jobPath(npx)}`);
        log(`Log      : ${logFile()}`);
        return;
    }
    const uid = process.getuid();
    const domainTarget = `gui/${uid}/${LABEL}`;
    if (disable) {
        try { execFileSync('launchctl', ['bootout', domainTarget], { stdio: 'ignore' }); } catch (_) {}
        try { execFileSync('launchctl', ['unload', plistPath], { stdio: 'ignore' }); } catch (_) {}
        if (fs.existsSync(plistPath)) fs.unlinkSync(plistPath);
        log(`Disabled launchd auto-update: ${plistPath}`);
        return;
    }

    const plist = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${npx}</string>
    <string>${UPDATE_ARGS[0]}</string>
    <string>${UPDATE_ARGS[1]}</string>
    <string>${UPDATE_ARGS[2]}</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>${jobPath(npx)}</string>
  </dict>
  <key>StartCalendarInterval</key>
  <dict>
${calendar}
  </dict>
  <key>StandardOutPath</key><string>${logFile()}</string>
  <key>StandardErrorPath</key><string>${logFile()}</string>
  <key>RunAtLoad</key><false/>
</dict>
</plist>
`;
    fs.mkdirSync(path.dirname(plistPath), { recursive: true });
    fs.mkdirSync(path.dirname(logFile()), { recursive: true });
    fs.writeFileSync(plistPath, plist);
    // Prefer the modern bootstrap API; `launchctl load` is deprecated and a
    // silent no-op on recent macOS. Fall back to `load -w` on older systems.
    try { execFileSync('launchctl', ['bootout', domainTarget], { stdio: 'ignore' }); } catch (_) {}
    try {
        execFileSync('launchctl', ['bootstrap', `gui/${uid}`, plistPath], { stdio: 'ignore' });
    } catch (_) {
        try { execFileSync('launchctl', ['unload', plistPath], { stdio: 'ignore' }); } catch (_) {}
        execFileSync('launchctl', ['load', '-w', plistPath], { stdio: 'ignore' });
    }
    log(`Enabled ${cadence} auto-update via launchd: ${plistPath}`);
}

function winSetup() {
    const tr = 'cmd /c npx --yes github:hov172/secure-webapp-skill --global';
    if (checkOnly) {
        log(`Platform : Windows (Task Scheduler)`);
        log(`Task     : ${TASK}`);
        log(`Schedule : ${cadence} at 09:00`);
        log(`Command  : ${tr}`);
        return;
    }
    if (disable) {
        try { execFileSync('schtasks', ['/Delete', '/TN', TASK, '/F'], { stdio: 'inherit' }); } catch (_) {}
        log(`Disabled scheduled task: ${TASK}`);
        return;
    }
    const schedule = daily ? ['/SC', 'DAILY'] : ['/SC', 'WEEKLY'];
    execFileSync('schtasks', ['/Create', '/TN', TASK, ...schedule, '/ST', '09:00', '/TR', tr, '/F'], { stdio: 'inherit' });
    log(`Enabled ${cadence} auto-update via Task Scheduler: ${TASK}`);
}

function linuxSetup() {
    const npx = which('npx');
    const cronLog = path.join(os.homedir(), '.cache', `${TASK}.log`);
    const expr = daily ? '0 9 * * *' : '0 9 * * 0';
    // Same shebang trap as launchd: cron's PATH will not contain node, so set
    // PATH inline. Errors go to a log rather than /dev/null so a failing job is
    // discoverable instead of silently doing nothing.
    const entry = `${expr} PATH=${jobPath(npx)} ${npx} ${UPDATE_ARGS.join(' ')} >>${cronLog} 2>&1 # ${TASK}`;
    if (checkOnly) {
        log(`Platform : Linux (cron)`);
        log(`Schedule : ${cadence} at 09:00`);
        log(`Crontab  : ${entry}`);
        log(`Log      : ${cronLog}`);
        return;
    }
    if (!disable) fs.mkdirSync(path.dirname(cronLog), { recursive: true });
    let current = '';
    try { current = execSync('crontab -l', { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }); } catch (_) {}
    const kept = current.split('\n').filter((line) => line && !line.includes(`# ${TASK}`));
    if (!disable) kept.push(entry);
    const next = kept.join('\n') + (kept.length ? '\n' : '');
    execSync('crontab -', { input: next });
    log(disable ? `Disabled cron auto-update (${TASK})` : `Enabled ${cadence} auto-update via cron: ${entry}`);
}

function main() {
    if (checkOnly) log('[--check] showing plan only; no changes will be made.\n');
    switch (process.platform) {
        case 'darwin':
            return macSetup();
        case 'win32':
            return winSetup();
        default:
            return linuxSetup();
    }
}

main();
