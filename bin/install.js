#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');

const args = process.argv.slice(2);
const isGlobal = args.includes('--global') || args.includes('-g');
const force = args.includes('--force');
const checkOnly = args.includes('--check');
const noWire = args.includes('--no-wire');

// Supported AI-agent clients and their config directory names.
const CLIENTS = {
    claude: '.claude',
    codex: '.codex',
    gemini: '.gemini',
};

// Per-client instruction file the agent reads to discover the skill.
// Claude Code auto-discovers ~/.claude/skills, so it needs no wiring.
const DISCOVERY = {
    codex: 'AGENTS.md',
    gemini: 'GEMINI.md',
};

const sourceDir = path.join(__dirname, '..');

// Files and directories to copy from the package into an install. This must
// stay in sync with scripts/package_skill.py so that an `npx` install and a
// released .skill archive produce the same tree — $secure-webapp maintain and
// scripts/setup-auto-update.js both depend on scripts/ being present.
const itemsToCopy = [
    'SKILL.md',
    'AGENTS.md',
    'GEMINI.md',
    'VERSION',
    'references',
    'assets',
    'agents',
    'scripts',
    'LICENSE',
    'LICENSE.txt',
];

// Maintainer-only files that live under scripts/ but are not part of an install.
// Mirrors the exclusions in scripts/package_skill.py.
const EXCLUDED_FROM_COPY = new Set([
    'scripts/README.md',
    'scripts/install.sh',
    'scripts/install.ps1',
]);

const BLOCK_BEGIN = '<!-- secure-webapp:begin (managed by the secure-webapp installer) -->';
const BLOCK_END = '<!-- secure-webapp:end -->';

function readVersion(file) {
    try {
        return fs.readFileSync(file, 'utf8').trim();
    } catch (_) {
        return null;
    }
}

function sourceVersion() {
    const fromFile = readVersion(path.join(sourceDir, 'VERSION'));
    if (fromFile) return fromFile;
    try {
        return require(path.join(sourceDir, 'package.json')).version || null;
    } catch (_) {
        return null;
    }
}

function isExcluded(src) {
    const rel = path.relative(sourceDir, src).split(path.sep).join('/');
    if (EXCLUDED_FROM_COPY.has(rel)) return true;
    const base = path.basename(src);
    return base === '__pycache__' || base === '.DS_Store' || base.endsWith('.pyc');
}

function copyRecursiveSync(src, dest) {
    if (isExcluded(src)) return;
    const exists = fs.existsSync(src);
    const stats = exists && fs.statSync(src);
    const isDirectory = exists && stats.isDirectory();

    if (isDirectory) {
        if (!fs.existsSync(dest)) {
            fs.mkdirSync(dest, { recursive: true });
        }
        fs.readdirSync(src).forEach(function (childItemName) {
            copyRecursiveSync(path.join(src, childItemName), path.join(dest, childItemName));
        });
    } else if (exists) {
        if (!fs.existsSync(path.dirname(dest))) {
            fs.mkdirSync(path.dirname(dest), { recursive: true });
        }
        fs.copyFileSync(src, dest);
    }
}

function targetDirFor(client, base) {
    return path.join(base, CLIENTS[client], 'skills', 'secure-webapp');
}

function detectClients(base) {
    return Object.keys(CLIENTS).filter((c) => fs.existsSync(targetDirFor(c, base)));
}

function installTo(targetDir, srcVer) {
    const installedVer = readVersion(path.join(targetDir, 'VERSION'));

    if (checkOnly) {
        if (srcVer && installedVer === srcVer) {
            console.log(`  up to date (${installedVer}) - ${targetDir}`);
        } else {
            console.log(`  update available (${installedVer || 'not installed'} -> ${srcVer || 'unknown'}) - ${targetDir}`);
        }
        return;
    }

    if (!force && srcVer && installedVer === srcVer) {
        console.log(`  already up to date (${installedVer}) - ${targetDir}`);
        return;
    }

    if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
    }
    for (const item of itemsToCopy) {
        const srcPath = path.join(sourceDir, item);
        const destPath = path.join(targetDir, item);
        if (fs.existsSync(srcPath)) {
            copyRecursiveSync(srcPath, destPath);
        } else {
            console.warn(`  warning: could not find ${item} to install`);
        }
    }
    console.log(`  installed ${srcVer || ''} (was ${installedVer || 'not installed'}) - ${targetDir}`);
}

function escapeRe(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Codex and Gemini do not auto-load ~/.<client>/skills, so point their
// instruction file (AGENTS.md / GEMINI.md) at the installed SKILL.md. Global
// installs wire the client config dir; project-local installs wire the project
// root file the agent reads.
function discoveryFileFor(client, base) {
    return isGlobal
        ? path.join(base, CLIENTS[client], DISCOVERY[client])
        : path.join(base, DISCOVERY[client]);
}

function discoveryBlock(client, discoveryFile, targetDir) {
    const rel = path.relative(path.dirname(discoveryFile), path.join(targetDir, 'SKILL.md')) || 'SKILL.md';
    const relPosix = rel.split(path.sep).join('/');
    const trigger =
        'web-app code or design involving auth, sessions, tokens (JWT/OAuth/OIDC), user input, ' +
        'DB queries, file uploads, API endpoints, cookies/CORS/CSP/CSRF, security headers, secrets, ' +
        'redirects, SSRF, logging, dependencies, or threat modeling';
    const modes = '`$secure-webapp audit | quick-check | harden | remediate | design-review | report | update | maintain`';
    // Gemini supports `@path` context imports; Codex reads the file directly.
    const importLine = client === 'gemini' ? `@${relPosix}\n\n` : '';
    return [
        BLOCK_BEGIN,
        '## secure-webapp skill',
        '',
        `${importLine}The **secure-webapp** skill (OWASP-grounded web-app security guidance) is installed at \`${relPosix}\`. ` +
            `When working on ${trigger}, read that \`SKILL.md\` and follow it, loading only the \`references/*.md\` it routes to.`,
        '',
        `Explicit modes: ${modes}.`,
        BLOCK_END,
        '',
    ].join('\n');
}

function wireDiscovery(client, base, targetDir) {
    if (!DISCOVERY[client]) return; // Claude auto-discovers; nothing to wire.
    const file = discoveryFileFor(client, base);
    const block = discoveryBlock(client, file, targetDir);
    let existing = '';
    try {
        existing = fs.readFileSync(file, 'utf8');
    } catch (_) {}
    const re = new RegExp(`${escapeRe(BLOCK_BEGIN)}[\\s\\S]*?${escapeRe(BLOCK_END)}\\n?`);
    let next;
    if (re.test(existing)) {
        next = existing.replace(re, block);
    } else {
        next = existing ? existing.replace(/\s*$/, '\n\n') + block : block;
    }
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, next);
    console.log(`  wired discovery -> ${file}`);
}

function main() {
    const base = isGlobal ? os.homedir() : process.cwd();
    const srcVer = sourceVersion();

    // Explicit client flags win. Otherwise update every client already present,
    // and fall back to Claude for a first-time install.
    let clients = Object.keys(CLIENTS).filter((c) => args.includes(`--${c}`));
    if (clients.length === 0) {
        const detected = detectClients(base);
        clients = detected.length ? detected : ['claude'];
    }

    console.log(
        `secure-webapp ${srcVer || ''} -> ${isGlobal ? 'global' : 'project-local'} install (${clients.join(', ')})`
    );

    try {
        for (const client of clients) {
            const targetDir = targetDirFor(client, base);
            installTo(targetDir, srcVer);
            if (!checkOnly && !noWire) {
                wireDiscovery(client, base, targetDir);
            }
        }
        if (checkOnly) {
            console.log('\nCheck complete. Re-run without --check to apply updates.');
        } else {
            console.log('\n✅ Done.');
            if (!isGlobal) {
                console.log('Note: project-local install. Use --global for a system-wide install.');
            }
        }
    } catch (error) {
        console.error('❌ Installation failed:', error.message);
        process.exit(1);
    }
}

main();
