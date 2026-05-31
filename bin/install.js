#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');

const args = process.argv.slice(2);
const isGlobal = args.includes('--global') || args.includes('-g');
const force = args.includes('--force');
const checkOnly = args.includes('--check');

// Supported AI-agent clients and their config directory names.
const CLIENTS = {
    claude: '.claude',
    codex: '.codex',
    gemini: '.gemini',
};

const sourceDir = path.join(__dirname, '..');

// Files and directories to copy from the package into an install.
const itemsToCopy = [
    'SKILL.md',
    'AGENTS.md',
    'GEMINI.md',
    'VERSION',
    'references',
    'assets',
    'agents',
    'LICENSE.txt',
];

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

function copyRecursiveSync(src, dest) {
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
            installTo(targetDirFor(client, base), srcVer);
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
