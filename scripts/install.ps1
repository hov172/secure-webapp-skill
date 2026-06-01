#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Install or update the secure-webapp skill on Windows (no Node.js required).
.DESCRIPTION
    Downloads the latest released secure-webapp.skill archive, compares its
    bundled VERSION with what is already installed, and unpacks only when a
    newer version is available (use -Force to reinstall anyway). For Codex and
    Gemini it also points the agent's instruction file (AGENTS.md / GEMINI.md)
    at the installed SKILL.md, since those clients do not auto-load skills/.
.PARAMETER Client
    Which agent to install for: claude (default), codex, or gemini.
.PARAMETER Local
    Install into the current directory instead of the user profile.
.PARAMETER Force
    Reinstall even when the installed version matches the released version.
.PARAMETER NoWire
    Skip writing the AGENTS.md / GEMINI.md discovery pointer.
.EXAMPLE
    pwsh -File scripts/install.ps1 -Client codex
#>
param(
    [ValidateSet('claude', 'codex', 'gemini')]
    [string]$Client = 'claude',
    [switch]$Local,
    [switch]$Force,
    [switch]$NoWire
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$base = if ($Local) { (Get-Location).Path } else { $env:USERPROFILE }
$installDir = Join-Path $base (Join-Path ".$Client" 'skills')
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

function Set-Discovery {
    if ($NoWire -or $Client -eq 'claude') { return }

    $disc = if ($Client -eq 'codex') { 'AGENTS.md' } else { 'GEMINI.md' }
    if ($Local) {
        $file = Join-Path (Get-Location).Path $disc
        $rel = ".$Client/skills/secure-webapp/SKILL.md"
    } else {
        $file = Join-Path (Join-Path $env:USERPROFILE ".$Client") $disc
        $rel = 'skills/secure-webapp/SKILL.md'
    }
    $importLine = if ($Client -eq 'gemini') { "@$rel`n`n" } else { '' }

    $block = @"
<!-- secure-webapp:begin (managed by the secure-webapp installer) -->
## secure-webapp skill

$($importLine)The **secure-webapp** skill (OWASP-grounded web-app security guidance) is installed at ``$rel``. When working on web-app code or design involving auth, sessions, tokens (JWT/OAuth/OIDC), user input, DB queries, file uploads, API endpoints, cookies/CORS/CSP/CSRF, security headers, secrets, redirects, SSRF, logging, dependencies, or threat modeling, read that ``SKILL.md`` and follow it, loading only the ``references/*.md`` it routes to.

Explicit modes: ``$secure-webapp audit | quick-check | harden | remediate | design-review | report | update | maintain``.
<!-- secure-webapp:end -->
"@

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $file) | Out-Null
    $existing = ''
    if (Test-Path $file) { $existing = Get-Content -Raw $file }
    $pattern = '(?s)<!-- secure-webapp:begin.*?<!-- secure-webapp:end -->\r?\n?'
    if ($existing -match $pattern) {
        $existing = [regex]::Replace($existing, $pattern, '')
    }
    $existing = $existing.TrimEnd()
    $content = if ($existing) { "$existing`n`n$block" } else { $block }
    Set-Content -Path $file -Value $content -NoNewline
    Write-Host "Wired discovery -> $file"
}

$tmp = Join-Path $env:TEMP ("secure-webapp-" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$archive = Join-Path $tmp 'secure-webapp.skill'

Write-Host "Downloading latest release..."
Invoke-WebRequest -Uri 'https://github.com/hov172/secure-webapp-skill/releases/latest/download/secure-webapp.skill' -OutFile $archive

# Read the version bundled in the downloaded archive.
$newVer = $null
try {
    $zip = [System.IO.Compression.ZipFile]::OpenRead($archive)
    $entry = $zip.GetEntry('secure-webapp/VERSION')
    if ($entry) {
        $reader = New-Object System.IO.StreamReader($entry.Open())
        $newVer = $reader.ReadToEnd().Trim()
        $reader.Close()
    }
    $zip.Dispose()
} catch { }

$curVerPath = Join-Path $installDir 'secure-webapp\VERSION'
$curVer = if (Test-Path $curVerPath) { (Get-Content $curVerPath -Raw).Trim() } else { $null }

if (-not $Force -and $newVer -and ($newVer -eq $curVer)) {
    Write-Host "Already up to date (version $curVer) at $installDir\secure-webapp"
    Set-Discovery
    Write-Host "Use -Force to reinstall anyway."
    Remove-Item -Recurse -Force $tmp
    exit 0
}

Write-Host "Unpacking into $installDir..."
# Expand-Archive expects a .zip extension; the .skill archive is a zip.
$zipCopy = "$archive.zip"
Copy-Item $archive $zipCopy
Expand-Archive -Path $zipCopy -DestinationPath $installDir -Force
Remove-Item -Recurse -Force $tmp

Set-Discovery

Write-Host "Installation complete. Version $newVer at $installDir\secure-webapp"
