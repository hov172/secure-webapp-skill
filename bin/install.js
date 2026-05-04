#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const os = require('os');

const args = process.argv.slice(2);
const isGlobal = args.includes('--global') || args.includes('-g');
const isCodex = args.includes('--codex');

const clientFolder = isCodex ? '.codex' : '.claude';
const baseDir = isGlobal ? os.homedir() : process.cwd();
const targetDir = path.join(baseDir, clientFolder, 'skills', 'secure-webapp');

console.log(`Installing secure-webapp skill to: ${targetDir}`);

// Files and directories to copy from the package
const itemsToCopy = [
    'SKILL.md',
    'references',
    'assets',
    'agents',
    'license.txt'
];

function copyRecursiveSync(src, dest) {
    const exists = fs.existsSync(src);
    const stats = exists && fs.statSync(src);
    const isDirectory = exists && stats.isDirectory();
    
    if (isDirectory) {
        if (!fs.existsSync(dest)) {
            fs.mkdirSync(dest, { recursive: true });
        }
        fs.readdirSync(src).forEach(function(childItemName) {
            copyRecursiveSync(path.join(src, childItemName), path.join(dest, childItemName));
        });
    } else if (exists) {
        if (!fs.existsSync(path.dirname(dest))) {
            fs.mkdirSync(path.dirname(dest), { recursive: true });
        }
        fs.copyFileSync(src, dest);
    }
}

try {
    const sourceDir = path.join(__dirname, '..');
    
    // Create target directory if it doesn't exist
    if (!fs.existsSync(targetDir)) {
        fs.mkdirSync(targetDir, { recursive: true });
    }

    // Copy items
    for (const item of itemsToCopy) {
        const srcPath = path.join(sourceDir, item);
        const destPath = path.join(targetDir, item);
        
        if (fs.existsSync(srcPath)) {
            copyRecursiveSync(srcPath, destPath);
        } else {
            console.warn(`Warning: Could not find ${item} to install.`);
        }
    }
    
    console.log('✅ Installation complete!');
    console.log('\nTo verify:');
    console.log(`  ls -la ${targetDir}/SKILL.md`);
    if (!isGlobal) {
        console.log('\nNote: This was a project-local install. Use --global for a system-wide install.');
    }
} catch (error) {
    console.error('❌ Installation failed:', error.message);
    process.exit(1);
}
