<#
.SYNOPSIS
    Builds and publishes a GitHub Release for the Insaniquarium Deluxe APWorld.

.DESCRIPTION
    Automates the release workflow for Insaniquarium Deluxe in Archipelago:
    1. Reads version and game metadata from archipelago.json.
    2. Auto-locates Python and builds the .apworld package (via build_insaniquarium.py).
    3. Stages release assets (.apworld, Insaniquarium.yaml, APWorld source code zip, and WinFish code zip).
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

.PARAMETER PatchNotesFile
    Path to a markdown file containing changelog/patch notes to embed into release_notes.md (defaults to worlds/insaniquarium/patch_notes.md).

.PARAMETER Draft
    Create the release as an unpublished draft on GitHub.

.PARAMETER Prerelease
    Mark the release as a pre-release on GitHub.

.PARAMETER SkipBuild
    Skip re-building the .apworld archive and use existing build output.

.PARAMETER SkipWinFish
    Skip packaging and attaching the WinFish source code zip archive.

.PARAMETER WinFishDir
    Override path to the WinFish source code directory. Defaults to auto-discovering WinFish adjacent to Archipelago.

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
    [string]$PatchNotesFile,
    [switch]$Draft,
    [switch]$Prerelease,
    [switch]$SkipBuild,
    [switch]$SkipWinFish,
    [string]$WinFishDir,
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
$defaultPatchNotes = Join-Path $worldDir "patch_notes.md"
$patchNotesPath = if ($PatchNotesFile) { $PatchNotesFile } else { $defaultPatchNotes }

function Find-WinFishDir {
    param ([string]$UserPath)
    if ($UserPath -and (Test-Path $UserPath)) {
        $resolved = (Resolve-Path $UserPath).Path
        if (Test-Path (Join-Path $resolved "WinFish.sln")) {
            return $resolved
        }
        if (Test-Path (Join-Path $resolved "WinFish\WinFish.sln")) {
            return (Resolve-Path (Join-Path $resolved "WinFish")).Path
        }
        return $resolved
    }

    if ($env:WINFISH_DIR -and (Test-Path $env:WINFISH_DIR)) {
        $envPath = (Resolve-Path $env:WINFISH_DIR).Path
        if (Test-Path (Join-Path $envPath "WinFish.sln")) {
            return $envPath
        }
        if (Test-Path (Join-Path $envPath "WinFish\WinFish.sln")) {
            return (Resolve-Path (Join-Path $envPath "WinFish")).Path
        }
    }

    $candidates = @(
        (Join-Path $repoRoot "..\WinFish\WinFish"),
        (Join-Path $repoRoot "..\WinFish"),
        (Join-Path $repoRoot "..\..\WinFish\WinFish"),
        (Join-Path $repoRoot "..\..\WinFish"),
        (Join-Path $worldDir "WinFish"),
        (Join-Path $repoRoot "WinFish")
    )
    foreach ($cand in $candidates) {
        if (Test-Path $cand) {
            $candPath = (Resolve-Path $cand).Path
            if (Test-Path (Join-Path $candPath "WinFish.sln")) {
                return $candPath
            }
            if (Test-Path (Join-Path $candPath "WinFish\WinFish.sln")) {
                return (Resolve-Path (Join-Path $candPath "WinFish")).Path
            }
        }
    }
    return $null
}

$resolvedWinFishDir = if (-not $SkipWinFish) { Find-WinFishDir $WinFishDir } else { $null }

if ($WinFishDir -and -not $resolvedWinFishDir) {
    Log-Error "Specified WinFish directory not found: $WinFishDir"
    exit 1
}

if (-not $SkipWinFish -and -not $resolvedWinFishDir) {
    Log-Error "WinFish directory not found. Please provide -WinFishDir or clone WinFish adjacent to Archipelago (or pass -SkipWinFish to exclude)."
    exit 1
}

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
if ($resolvedWinFishDir) {
    Log-Info "WinFish Dir:      $resolvedWinFishDir"
}

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

if ($resolvedWinFishDir -and (Test-Path (Join-Path $resolvedWinFishDir ".git"))) {
    try {
        $winFishDirty = git -C $resolvedWinFishDir status --porcelain 2>$null
        if ($winFishDirty -and -not $AllowDirty) {
            Log-Warn "You have uncommitted git changes in your WinFish working tree:"
            $winFishDirty | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkYellow }
            Log-Warn "Commit or stash your changes before releasing, or pass -AllowDirty to proceed."
            exit 1
        }
    }
    catch {
        Log-Warn "Unable to check WinFish git working tree status."
    }
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
        "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe",
        "$env:LOCALAPPDATA\Python\pythoncore-3.13-64\python.exe",
        "$env:LOCALAPPDATA\Python\pythoncore-3.12-64\python.exe",
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

    $stagedApworld = Join-Path $stagingDir "insaniquarium.apworld"
    $stagedYaml = Join-Path $stagingDir "Insaniquarium.yaml"
    $stagedSourceZip = Join-Path $stagingDir "insaniquarium-source-v$Version.zip"
    $stagedWinFishZip = Join-Path $stagingDir "winfish-source-v$Version.zip"
    $stagedReleaseNotes = Join-Path $stagingDir "release_notes.md"
    $stagedNotes        = $stagedReleaseNotes

    # Clean up obsolete release.md if present from prior builds
    $obsoleteReleaseMd = Join-Path $stagingDir "release.md"
    if (Test-Path $obsoleteReleaseMd) {
        Remove-Item -Path $obsoleteReleaseMd -Force
    }

    Copy-Item -Path $apworldBuildPath -Destination $stagedApworld -Force
    Copy-Item -Path $yamlSrcPath -Destination $stagedYaml -Force

    Log-Success "Staged apworld:    $stagedApworld ($((Get-Item $stagedApworld).Length.ToString('N0')) bytes)"
    Log-Success "Staged yaml:       $stagedYaml"

    # Build source code zip archive (following .apignore)
    Log-Info "Creating source code zip archive ($((Split-Path $stagedSourceZip -Leaf)))..."
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem

    if (Test-Path $stagedSourceZip) {
        Remove-Item -Path $stagedSourceZip -Force
    }

    $apignorePath = Join-Path $worldDir ".apignore"
    $apIgnorePatterns = @(
        '__pycache__',
        '*.pyc',
        '.git*',
        '.apignore'
    )
    if (Test-Path $apignorePath) {
        $rawApignore = Get-Content -Path $apignorePath -Encoding utf8
        foreach ($line in $rawApignore) {
            $t = $line.Trim()
            if ($t -and -not $t.StartsWith('#')) {
                $apIgnorePatterns += $t.TrimEnd('/')
            }
        }
    }

    function Test-ApIgnored {
        param (
            [string]$RelPath,
            [string]$FileName,
            [string[]]$Patterns
        )
        $normalizedRel = $RelPath -replace '\\', '/'
        $parts = $normalizedRel.Split('/')
        foreach ($p in $Patterns) {
            $cleanPat = ($p.Trim() -replace '\\', '/').TrimEnd('/')
            if ($cleanPat.StartsWith('!')) { continue }

            foreach ($part in $parts) {
                if ($part -like $cleanPat) {
                    return $true
                }
            }
            if ($normalizedRel -like $cleanPat -or $normalizedRel -like "*/$cleanPat" -or $normalizedRel -like "$cleanPat/*" -or $normalizedRel -like "*/$cleanPat/*") {
                return $true
            }
            if ($FileName -like $cleanPat) {
                return $true
            }
        }
        return $false
    }

    $zipStream = [System.IO.File]::Open($stagedSourceZip, [System.IO.FileMode]::Create)
    $archive = New-Object System.IO.Compression.ZipArchive($zipStream, [System.IO.Compression.ZipArchiveMode]::Create)

    try {
        $allWorldFiles = Get-ChildItem -Path $worldDir -Recurse | Where-Object { -not $_.PSIsContainer }
        $sourceFiles = @()

        foreach ($file in $allWorldFiles) {
            $rel = $file.FullName.Substring($worldDir.Length).TrimStart('\', '/')
            if (-not (Test-ApIgnored -RelPath $rel -FileName $file.Name -Patterns $apIgnorePatterns)) {
                $sourceFiles += @{ File = $file; Rel = $rel }
            }
        }

        Log-Info "Found $($sourceFiles.Count) world files adhering to .apignore"

        foreach ($item in $sourceFiles) {
            # Use forward slashes inside zip for POSIX compatibility
            $entryName = "insaniquarium/" + ($item.Rel -replace '\\', '/')
            [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                $archive,
                $item.File.FullName,
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

    # Build WinFish source code zip archive (following .gitignore)
    if ($resolvedWinFishDir -and -not $SkipWinFish) {
        Log-Info "Creating WinFish source code zip archive ($((Split-Path $stagedWinFishZip -Leaf)))..."

        if (Test-Path $stagedWinFishZip) {
            Remove-Item -Path $stagedWinFishZip -Force
        }

        function Get-WinFishFiles {
            param ([string]$Dir)

            $hasGit = Test-Path (Join-Path $Dir ".git")
            if ($hasGit) {
                try {
                    $gitFiles = git -c core.quotepath=false -C $Dir ls-files --cached --others --exclude-standard 2>$null
                    if ($LASTEXITCODE -eq 0 -and $gitFiles) {
                        $ignoredCached = @(git -c core.quotepath=false -C $Dir ls-files -c -i --exclude-standard 2>$null)
                        $ignoredSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
                        foreach ($ig in $ignoredCached) {
                            if ($ig) { [void]$ignoredSet.Add($ig.Trim()) }
                        }

                        $files = @()
                        foreach ($f in $gitFiles) {
                            $trimmed = $f.Trim()
                            if ($trimmed -and -not $ignoredSet.Contains($trimmed)) {
                                $files += $trimmed
                            }
                        }
                        return $files
                    }
                }
                catch {
                    Log-Warn "git ls-files failed on WinFish directory, falling back to manual gitignore parser."
                }
            }

            $allItems = Get-ChildItem -Path $Dir -Recurse | Where-Object { -not $_.PSIsContainer }
            $files = @()
            foreach ($item in $allItems) {
                $rel = $item.FullName.Substring($Dir.Length).TrimStart('\', '/') -replace '\\', '/'
                if ($rel -match '(^|/)\.git(/|$)') { continue }

                $matched = $false
                foreach ($pat in $ignorePatterns) {
                    $cleanPat = $pat.Trim().TrimEnd('/')
                    if ($cleanPat.StartsWith('!')) {
                        continue
                    }
                    if ($cleanPat.StartsWith('/')) {
                        $rootPat = $cleanPat.Substring(1)
                        if ($rel -like "$rootPat*" -or $rel -like $rootPat) {
                            $matched = $true
                            break
                        }
                    }
                    else {
                        if ($rel -like "*$cleanPat*" -or $item.Name -like $cleanPat) {
                            $matched = $true
                            break
                        }
                    }
                }
                if (-not $matched) {
                    $files += $rel
                }
            }
            return $files
        }

        $winFishFiles = Get-WinFishFiles -Dir $resolvedWinFishDir
        Log-Info "Found $($winFishFiles.Count) WinFish files adhering to .gitignore"

        $wzStream = [System.IO.File]::Open($stagedWinFishZip, [System.IO.FileMode]::Create)
        $wArchive = New-Object System.IO.Compression.ZipArchive($wzStream, [System.IO.Compression.ZipArchiveMode]::Create)

        try {
            foreach ($relPath in $winFishFiles) {
                $fullPath = Join-Path $resolvedWinFishDir $relPath
                if (Test-Path $fullPath -PathType Leaf) {
                    $entryName = "WinFish/" + ($relPath -replace '\\', '/')
                    [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
                        $wArchive,
                        $fullPath,
                        $entryName,
                        [System.IO.Compression.CompressionLevel]::Optimal
                    ) | Out-Null
                }
            }
        }
        finally {
            $wArchive.Dispose()
            $wzStream.Dispose()
        }

        Log-Success "Staged WinFish zip: $stagedWinFishZip ($((Get-Item $stagedWinFishZip).Length.ToString('N0')) bytes)"
    }
    elseif ($SkipWinFish -and (Test-Path $stagedWinFishZip)) {
        Remove-Item -Path $stagedWinFishZip -Force
    }

    # -----------------------------------------------------------------------------
    # 7. Prepare Release Notes & Load Patch Notes
    # -----------------------------------------------------------------------------
    $patchNotesBlock = ""
    if (Test-Path $patchNotesPath) {
        Log-Info "Loading patch notes from $patchNotesPath..."
        $rawPatchNotes = (Get-Content -Path $patchNotesPath -Raw -Encoding utf8).Trim()
        if ($rawPatchNotes) {
            $patchNotesBlock = @"

---

## What's New in v$Version

$rawPatchNotes
"@
        }
    }

    $winFishAssetLine = if (-not $SkipWinFish -and $resolvedWinFishDir -and (Test-Path $stagedWinFishZip)) {
        "`n- **`winfish-source-v$Version.zip`**: Source code of the WinFish Archipelago client."
    }
    else { "" }

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
$patchNotesBlock
---

## Installation & Setup

### For Players & Multiworld Hosts:
1. Download **`insaniquarium.apworld`** from the Assets below.
2. Install the `.apworld`:
   - **Launcher**: Double-click `insaniquarium.apworld` to automatically install it into your Archipelago Launcher.
   - **Manual**: Place `insaniquarium.apworld` into your Archipelago `custom_worlds/` directory (e.g. `C:\ProgramData\Archipelago\custom_worlds`).
3. Download **`Insaniquarium.yaml`** and place it in your Archipelago `Players/` folder.
4. Customize your options (starting tank, egg pieces per level, victory conditions, and trap rates) before generating.

### Playing:
1. Generate your multiworld game.
2. The generator will produce your `.apinsani` patch file.
3. Use the Import button inside the Insaniquarium profile menu to load the provided patch file and input the connection info for your Archipelago server.

---

## Features & Options
- **Starting Tank**: Choose between starting in Tank 1, 2, 3, 4, or random.
- **Egg Checks**: Configurable egg piece checks (1, 2, or all 3 per level).
- **Victory Conditions**: Completing Tanks 1-4 is always required; optionally require Cyrax, Time Trials, or Challenge Mode.
- **Upgrade Availability**: Control when received upgrades become accessible (always, free upon receiving, or normal shop price).
- **Traps**: Optional Alien Attack and Famine traps.

---

## Release Assets
- **`insaniquarium.apworld`**: Archipelago game world package.
- **`Insaniquarium.yaml`**: Player configuration YAML template.
- **`insaniquarium-source-v$Version.zip`**: Source code of the Insaniquarium Deluxe world.$winFishAssetLine
"@
    }

    Set-Content -Path $stagedReleaseNotes -Value $releaseNotesContent -Encoding utf8
    Log-Success "Generated release notes at $stagedReleaseNotes"

    # -----------------------------------------------------------------------------
    # 8. Publish via GitHub CLI
    # -----------------------------------------------------------------------------
    $releaseAssets = @(
        $stagedApworld,
        $stagedYaml,
        $stagedSourceZip
    )
    if (-not $SkipWinFish -and (Test-Path $stagedWinFishZip)) {
        $releaseAssets += $stagedWinFishZip
    }

    if ($LocalOnly) {
        Log-Success "Local staging completed successfully!"
        Write-Host ""
        Write-Host "Files prepared in: $stagingDir" -ForegroundColor Green
        Write-Host "  - insaniquarium.apworld"
        Write-Host "  - Insaniquarium.yaml"
        Write-Host "  - insaniquarium-source-v$Version.zip"
        if (-not $SkipWinFish -and (Test-Path $stagedWinFishZip)) {
            Write-Host "  - $((Split-Path $stagedWinFishZip -Leaf))"
        }
        Write-Host "  - release_notes.md"
        Write-Host ""
        Write-Host "To publish manually later, you can run:" -ForegroundColor DarkGray
        $assetsStr = ($releaseAssets | ForEach-Object { "`"$_`"" }) -join " "
        Write-Host "  gh release create $Tag $assetsStr --title `"$Title`" --notes-file `"$stagedReleaseNotes`" --target `"$Target`"" -ForegroundColor DarkGray
        exit 0
    }

    Log-Info "Publishing release to GitHub ($repoWebUrl)..."

    $ghArgs = @(
        "release", "create", $Tag
    ) + $releaseAssets + @(
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
