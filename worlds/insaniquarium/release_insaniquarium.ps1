<#
.SYNOPSIS
    Builds and publishes a GitHub Release for the Insaniquarium Deluxe APWorld.

.DESCRIPTION
    Automates the release workflow for Insaniquarium Deluxe in Archipelago:
    1. Reads version and game metadata from archipelago.json.
    2. Auto-locates Python and builds the .apworld package (via build_insaniquarium.py).
    3. Stages release assets (.apworld, Insaniquarium.yaml, and source code zip).
    4. Generates formatted markdown release notes tailored for Archipelago.
    5. Publishes a GitHub Release with assets attached using the GitHub CLI (gh).

.PARAMETER Version
    Override the release version (e.g. "0.1.0"). Defaults to world_version in archipelago.json.

.PARAMETER Tag
    Override the git tag name (e.g. "release-insaniquarium-v0.1.0").

.PARAMETER Title
    Override the release title. Defaults to "Insaniquarium Deluxe v<Version>".

.PARAMETER NotesFile
    Path to a markdown file to use as the release notes description.

.PARAMETER Notes
    Inline string of release notes to use.

.PARAMETER Draft
    Create the release as an unpublished draft on GitHub.

.PARAMETER Prerelease
    Mark the release as a pre-release on GitHub.

.PARAMETER SkipBuild
    Skip re-building the .apworld archive and use existing build output.

.PARAMETER LocalOnly
    Stage assets and generate release notes locally without uploading to GitHub.

.PARAMETER AllowDirty
    Allow running even if the git working tree has uncommitted modifications.

.PARAMETER Python
    Custom path to python.exe if not automatically discovered.

.PARAMETER Target
    Git branch or commit to associate with the release tag (defaults to current branch).

.EXAMPLE
    .\release_insaniquarium.ps1
    # Builds apworld and creates release with default version from archipelago.json

.EXAMPLE
    .\release_insaniquarium.ps1 -Draft
    # Builds and creates a draft release on GitHub for inspection before publishing

.EXAMPLE
    .\release_insaniquarium.ps1 -LocalOnly
    # Packages assets and writes release notes locally without publishing to GitHub
#>

[CmdletBinding()]
param (
    [string]$Version,
    [string]$Tag,
    [string]$Title,
    [string]$NotesFile,
    [string]$Notes,
    [switch]$Draft,
    [switch]$Prerelease,
    [switch]$SkipBuild,
    [switch]$LocalOnly,
    [switch]$AllowDirty,
    [string]$Python,
    [string]$Target
)

$ErrorActionPreference = "Stop"

function Log-Info    ([string]$Msg) { Write-Host "[*] $Msg" -ForegroundColor Cyan }
function Log-Success ([string]$Msg) { Write-Host "[+] $Msg" -ForegroundColor Green }
function Log-Warn    ([string]$Msg) { Write-Host "[!] $Msg" -ForegroundColor Yellow }
function Log-Error   ([string]$Msg) { Write-Host "[-] $Msg" -ForegroundColor Red }

# -----------------------------------------------------------------------------
# 1. Path Resolution
# -----------------------------------------------------------------------------
$scriptDir = $PSScriptRoot
$worldDir = $scriptDir
$repoRoot = (Resolve-Path "$worldDir\..\..").Path
$manifestPath = Join-Path $worldDir "archipelago.json"
$yamlSrcPath = Join-Path $worldDir "Insaniquarium.yaml"
$buildScript = Join-Path $worldDir "build_insaniquarium.py"
$buildOutputDir = Join-Path $repoRoot "build\apworlds"
$apworldBuildPath = Join-Path $buildOutputDir "insaniquarium.apworld"

Write-Host "==================================================" -ForegroundColor Magenta
Write-Host "  Insaniquarium Deluxe APWorld Release Tool       " -ForegroundColor Magenta
Write-Host "==================================================" -ForegroundColor Magenta

if (-not (Test-Path $manifestPath)) {
    Log-Error "archipelago.json not found at $manifestPath"
    exit 1
}

# -----------------------------------------------------------------------------
# 2. Read Metadata & Versioning
# -----------------------------------------------------------------------------
try {
    $manifest = Get-Content -Path $manifestPath -Raw -Encoding utf8 | ConvertFrom-Json
}
catch {
    Log-Error "Failed to parse archipelago.json: $_"
    exit 1
}

$gameName = $manifest.game
$minApVersion = $manifest.minimum_ap_version
$worldVersion = $manifest.world_version

if (-not $Version) {
    $Version = $worldVersion
}

if (-not $Tag) {
    $Tag = "release-insaniquarium-v$Version"
}

if (-not $Title) {
    $Title = "$gameName v$Version"
}

Log-Info "Game:             $gameName"
Log-Info "Version:          $Version (minimum AP: $minApVersion)"
Log-Info "Release Tag:      $Tag"
Log-Info "Release Title:    $Title"

# -----------------------------------------------------------------------------
# 3. Git Status & Remote Checks
# -----------------------------------------------------------------------------
try {
    $gitBranch = (git -C $repoRoot rev-parse --abbrev-ref HEAD 2>$null).Trim()
}
catch {
    $gitBranch = "main"
}

if (-not $Target) {
    $Target = $gitBranch
}
Log-Info "Target Branch:    $Target"

try {
    $dirtyFiles = git -C $repoRoot status --porcelain
    if ($dirtyFiles -and -not $AllowDirty) {
        Log-Warn "You have uncommitted git changes in your working tree:"
        $dirtyFiles | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkYellow }
        Log-Warn "Commit or stash your changes before releasing, or pass -AllowDirty to proceed."
        exit 1
    }
}
catch {
    Log-Warn "Unable to check git working tree status."
}

# Get origin repo URL to generate release URLs
try {
    $remoteUrl = (git -C $repoRoot remote get-url origin 2>$null).Trim()
    if ($remoteUrl -match 'github\.com[:/]([^/]+)/([^.]+)(\.git)?') {
        $repoOwner = $Matches[1]
        $repoName = $Matches[2]
        $repoWebUrl = "https://github.com/$repoOwner/$repoName"
    }
    else {
        $repoWebUrl = "https://github.com/benyoung32/Archipelago"
    }
}
catch {
    $repoWebUrl = "https://github.com/benyoung32/Archipelago"
}

# -----------------------------------------------------------------------------
# 4. GitHub CLI (gh) Pre-flight Check
# -----------------------------------------------------------------------------
$ghCli = Get-Command gh -ErrorAction SilentlyContinue

if (-not $LocalOnly) {
    if (-not $ghCli) {
        Log-Warn "GitHub CLI ('gh') is not installed or not in PATH."
        Log-Warn "Install gh from https://cli.github.com or run with -LocalOnly to prepare files locally."
        exit 1
    }

    # Verify gh auth
    $authCheck = gh auth status 2>&1
    if ($LASTEXITCODE -ne 0) {
        Log-Warn "GitHub CLI is not authenticated."
        Log-Warn "Please run:  gh auth login"
        Log-Warn "Alternatively run with -LocalOnly to package assets without uploading."
        exit 1
    }
}

# -----------------------------------------------------------------------------
# 5. Locate Python Executable & Build APWorld
# -----------------------------------------------------------------------------
function Find-PythonExe {
    param ([string]$UserPath)
    if ($UserPath -and (Test-Path $UserPath)) {
        return (Resolve-Path $UserPath).Path
    }
    # Check if python in PATH runs
    try {
        $ver = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) { return "python" }
    }
    catch {}

    # Probe typical local Python installations
    $candidates = @(
        "$env:LOCALAPPDATA\Python\bin\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "C:\Program Files\Python314\python.exe",
        "C:\Program Files\Python313\python.exe",
        "C:\Program Files\Python312\python.exe"
    )
    foreach ($cand in $candidates) {
        $resolved = Get-Item $cand -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($resolved -and (Test-Path $resolved.FullName)) {
            return $resolved.FullName
        }
    }
    return "python"
}

if (-not $SkipBuild) {
    Log-Info "Locating Python and building APWorld package..."
    if (-not (Test-Path $buildScript)) {
        Log-Error "Build script not found: $buildScript"
        exit 1
    }

    $pythonExe = Find-PythonExe $Python
    Log-Info "Using Python:     $pythonExe"

    & $pythonExe "$buildScript" --skip-generate

    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $apworldBuildPath)) {
        Log-Error "Failed to build APWorld package!"
        exit 1
    }
}
else {
    Log-Info "Skipping build step (-SkipBuild specified). Using existing $apworldBuildPath"
}

if (-not (Test-Path $apworldBuildPath)) {
    Log-Error "APWorld package not found at $apworldBuildPath. Run without -SkipBuild."
    exit 1
}

if (-not (Test-Path $yamlSrcPath)) {
    Log-Error "Options YAML template not found at $yamlSrcPath"
    exit 1
}

# -----------------------------------------------------------------------------
# 6. Stage Release Assets
# -----------------------------------------------------------------------------
$stagingDir = Join-Path $repoRoot "build\releases\insaniquarium-v$Version"
if (-not (Test-Path $stagingDir)) {
    New-Item -ItemType Directory -Path $stagingDir -Force | Out-Null
}

$stagedApworld   = Join-Path $stagingDir "insaniquarium.apworld"
$stagedYaml      = Join-Path $stagingDir "Insaniquarium.yaml"
$stagedSourceZip = Join-Path $stagingDir "insaniquarium-source-v$Version.zip"
$stagedNotes     = Join-Path $stagingDir "release_notes.md"

Copy-Item -Path $apworldBuildPath -Destination $stagedApworld -Force
Copy-Item -Path $yamlSrcPath -Destination $stagedYaml -Force

Log-Success "Staged apworld:    $stagedApworld ($((Get-Item $stagedApworld).Length.ToString('N0')) bytes)"
Log-Success "Staged yaml:       $stagedYaml"

# Build source code zip archive
Log-Info "Creating source code zip archive ($((Split-Path $stagedSourceZip -Leaf)))..."
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

if (Test-Path $stagedSourceZip) {
    Remove-Item -Path $stagedSourceZip -Force
}

$zipStream = [System.IO.File]::Open($stagedSourceZip, [System.IO.FileMode]::Create)
$archive = New-Object System.IO.Compression.ZipArchive($zipStream, [System.IO.Compression.ZipArchiveMode]::Create)

try {
    $sourceFiles = Get-ChildItem -Path $worldDir -Recurse | Where-Object {
        -not $_.PSIsContainer -and
        $_.FullName -notmatch '[\\/]__pycache__([\\/]|$)' -and
        $_.Extension -ne '.pyc' -and
        $_.FullName -notmatch '[\\/]\.git([\\/]|$)'
    }

    foreach ($file in $sourceFiles) {
        $rel = $file.FullName.Substring($worldDir.Length).TrimStart('\', '/')
        # Use forward slashes inside zip for POSIX compatibility
        $entryName = "insaniquarium/" + ($rel -replace '\\', '/')
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive,
            $file.FullName,
            $entryName,
            [System.IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
    }
}
finally {
    $archive.Dispose()
    $zipStream.Dispose()
}

Log-Success "Staged source zip: $stagedSourceZip ($((Get-Item $stagedSourceZip).Length.ToString('N0')) bytes)"

# -----------------------------------------------------------------------------
# 7. Prepare Release Notes
# -----------------------------------------------------------------------------
if ($Notes) {
    $releaseNotesContent = $Notes
}
elseif ($NotesFile -and (Test-Path $NotesFile)) {
    $releaseNotesContent = Get-Content -Path $NotesFile -Raw -Encoding utf8
}
else {
    $releaseNotesContent = @"
# $gameName APWorld v$Version

Archipelago world integration for **Insaniquarium Deluxe** (PopCap / Steam).

## Requirements
- **Archipelago**: [v$minApVersion or newer](https://github.com/ArchipelagoMW/Archipelago/releases)
- **Game**: *Insaniquarium Deluxe* English PC release (Steam / PopCap)
- **APFish**: [Latest Version](https://github.com/benyoung32/WinFish)
---

## Installation & Setup

### For Players & Multiworld Hosts:
1. Download **`insaniquarium.apworld`** from the Assets below.
2. Install the `.apworld`:
   - **Launcher**: Double-click `insaniquarium.apworld` to automatically install it into your Archipelago Launcher.
   - **Manual**: Place `insaniquarium.apworld` into your Archipelago `custom_worlds/` directory (e.g. `C:\ProgramData\Archipelago\custom_worlds`).
3. Download **`Insaniquarium.yaml`** and place it in your Archipelago `Players/` folder.
4. Customize your options (starting tank, egg pieces per level, goal, and trap rates) before generating.

### Playing:
1. Generate your multiworld game.
2. The generator will produce your `.apinsani` patch file.
3. Use the Import button inside the Insaniquarium profile menu to load the provided patch file and input the connection info for your Archipelago server.

---

## Features & Options
- **Starting Tank**: Choose between starting in Tank 1, 2, 3, 4, or random.
- **Egg Checks**: Configurable egg piece checks (1, 2, or all 3 per level).
- **Goal Selection**: Defeat Cyrax, Complete All 4 Tanks, or Full 100% Completion.
- **Traps**: Optional Alien Attack and Famine traps.

---

## Release Assets
- **`insaniquarium.apworld`**: Archipelago game world package.
- **`Insaniquarium.yaml`**: Player configuration YAML template.
- **`insaniquarium-source-v$Version.zip`**: Source code of the Insaniquarium Deluxe world.
"@
}

Set-Content -Path $stagedNotes -Value $releaseNotesContent -Encoding utf8
Log-Success "Generated release notes at $stagedNotes"

# -----------------------------------------------------------------------------
# 8. Publish via GitHub CLI
# -----------------------------------------------------------------------------
if ($LocalOnly) {
    Log-Success "Local staging completed successfully!"
    Write-Host ""
    Write-Host "Files prepared in: $stagingDir" -ForegroundColor Green
    Write-Host "  - insaniquarium.apworld"
    Write-Host "  - Insaniquarium.yaml"
    Write-Host "  - insaniquarium-source-v$Version.zip"
    Write-Host "  - release_notes.md"
    Write-Host ""
    Write-Host "To publish manually later, you can run:" -ForegroundColor DarkGray
    Write-Host "  gh release create $Tag `"$stagedApworld`" `"$stagedYaml`" `"$stagedSourceZip`" --title `"$Title`" --notes-file `"$stagedNotes`" --target `"$Target`"" -ForegroundColor DarkGray
    exit 0
}

Log-Info "Publishing release to GitHub ($repoWebUrl)..."

$ghArgs = @(
    "release", "create", $Tag,
    $stagedApworld,
    $stagedYaml,
    $stagedSourceZip,
    "--title", $Title,
    "--notes-file", $stagedNotes,
    "--target", $Target
)

if ($Draft) {
    $ghArgs += "--draft"
    Log-Info "Flag: Creating as DRAFT release"
}

if ($Prerelease) {
    $ghArgs += "--prerelease"
    Log-Info "Flag: Creating as PRE-RELEASE"
}

try {
    & gh @ghArgs
    if ($LASTEXITCODE -ne 0) {
        Log-Error "GitHub CLI release command returned error code $LASTEXITCODE"
        exit 1
    }
}
catch {
    Log-Error "Failed to execute gh release command: $_"
    exit 1
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "   Release Published Successfully!                " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Direct Release URL:" -ForegroundColor Cyan
Write-Host "  $repoWebUrl/releases/tag/$Tag" -ForegroundColor White
Write-Host ""
Write-Host "Releases Search URL (like Peggle Deluxe):" -ForegroundColor Cyan
Write-Host "  $repoWebUrl/releases?q=insaniquarium&expanded=true#$Tag" -ForegroundColor White
Write-Host ""
