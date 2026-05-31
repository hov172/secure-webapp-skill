#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Install or update the secure-webapp skill on Windows (no Node.js required).
.DESCRIPTION
    Downloads the latest released secure-webapp.skill archive, compares its
    bundled VERSION with what is already installed, and unpacks only when a
    newer version is available (use -Force to reinstall anyway).
.PARAMETER Client
    Which agent to install for: claude (default), codex, or gemini.
.PARAMETER Local
    Install into the current directory instead of the user profile.
.PARAMETER Force
    Reinstall even when the installed version matches the released version.
.EXAMPLE
    pwsh -File scripts/install.ps1
.EXAMPLE
    pwsh -File scripts/install.ps1 -Client codex
.EXAMPLE
    pwsh -File scripts/install.ps1 -Client gemini -Local
#>
param(
    [ValidateSet('claude', 'codex', 'gemini')]
    [string]$Client = 'claude',
    [switch]$Local,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$base = if ($Local) { (Get-Location).Path } else { $env:USERPROFILE }
$installDir = Join-Path $base (Join-Path ".$Client" 'skills')
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

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

Write-Host "Installation complete. Version $newVer at $installDir\secure-webapp"
