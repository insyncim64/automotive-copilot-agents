# Automotive Copilot Agents - Windows Setup Script
# Installs automotive copilot agents to .github/copilot/ directory
# Append-safe: never modifies existing content

param(
    [string]$ProjectPath = $PWD,
    [switch]$DryRun,
    [switch]$Status,
    [switch]$Uninstall,
    [switch]$NoBackup
)

$ErrorActionPreference = "Stop"

# ============================================================================
# Configuration
# ============================================================================
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = if ($ProjectPath) { $ProjectPath } else { $SCRIPT_DIR }
$COPILOT_PATH = Join-Path $PROJECT_ROOT ".github\copilot"
$SOURCE_PATH = Join-Path $PROJECT_ROOT ".github\copilot"
$MANIFEST_FILE = Join-Path $PROJECT_ROOT ".github\copilot\.install.manifest.json"
$LOG_FILE = Join-Path $SCRIPT_DIR "setup.log"

# Colors for output
$Color_Info = "Cyan"
$Color_Success = "Green"
$Color_Warning = "Yellow"
$Color_Error = "Red"

# ============================================================================
# Helper Functions
# ============================================================================

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Color_Info
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor $Color_Success
}

function Write-Warning-Message {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor $Color_Warning
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Color_Error
}

function Get-DirectorySize {
    param([string]$Path)
    if (Test-Path $Path) {
        $items = Get-ChildItem -Path $Path -Recurse -File
        return ($items | Measure-Object -Property Length -Sum).Sum
    }
    return 0
}

function Get-FileCount {
    param([string]$Path, [string]$Filter = "*")
    if (Test-Path $Path) {
        return (Get-ChildItem -Path $Path -Filter $Filter -Recurse -File).Count
    }
    return 0
}

function Format-FileSize {
    param([long]$Size)
    if ($Size -gt 1GB) { return "{0:N2} GB" -f ($Size / 1GB) }
    if ($Size -gt 1MB) { return "{0:N2} MB" -f ($Size / 1MB) }
    if ($Size -gt 1KB) { return "{0:N2} KB" -f ($Size / 1KB) }
    return "{0} B" -f $Size
}

function Test-IsAdmin {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ============================================================================
# Logging Function
# ============================================================================

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    try {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $logEntry = "$timestamp - $Level - $Message"
        Add-Content -Path $LOG_FILE -Value $logEntry -Encoding UTF8 -ErrorAction SilentlyContinue
    } catch {
        # Silent failure - logging should not block installation
    }
}

# ============================================================================
# Installation Functions
# ============================================================================

function Copy-Safe {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$Filter = "*"
    )

    if (!(Test-Path $Source)) {
        Write-Warning-Message "Source not found: $Source (skipping)"
        return 0
    }

    # Create destination directory if it doesn't exist
    $destDir = Split-Path $Destination -Parent
    if (!(Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }

    # Copy files (append-safe: won't overwrite unless -Force)
    $sourceItems = Get-ChildItem -Path $Source -Filter $Filter -Recurse -File
    $copiedCount = 0

    foreach ($item in $sourceItems) {
        $relativePath = $item.FullName.Substring($Source.Length).TrimStart('\')
        $targetPath = Join-Path $Destination $relativePath
        $targetDir = Split-Path $targetPath -Parent

        if (!(Test-Path $targetDir)) {
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }

        # Only copy if file doesn't exist or is different
        if (!(Test-Path $targetPath)) {
            Copy-Item -Path $item.FullName -Destination $targetPath -Force
            $copiedCount++
        } else {
            # Compare file sizes - if different, copy
            $sourceSize = (Get-Item $item.FullName).Length
            $targetSize = (Get-Item $targetPath).Length
            if ($sourceSize -ne $targetSize) {
                Copy-Item -Path $item.FullName -Destination $targetPath -Force
                $copiedCount++
            }
        }
    }

    return $copiedCount
}

function Create-Manifest {
    param([string]$ManifestPath)

    $manifest = @{
        "version" = "1.0.0"
        "install_date" = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        "project_path" = $PROJECT_ROOT
        "copilot_path" = $COPILOT_PATH
        "installed_components" = @()
    }

    # Scan installed components
    $components = @()

    if (Test-Path (Join-Path $COPILOT_PATH "instructions")) {
        $agentFiles = Get-ChildItem -Path (Join-Path $COPILOT_PATH "instructions") -Filter "*.md" -File
        foreach ($file in $agentFiles) {
            $components += @{
                "type" = "agent"
                "name" = $file.BaseName
                "path" = $file.FullName
            }
        }
    }

    if (Test-Path (Join-Path $COPILOT_PATH "context")) {
        $contextFiles = Get-ChildItem -Path (Join-Path $COPILOT_PATH "context") -Filter "*.md" -Recurse -File
        foreach ($file in $contextFiles) {
            $relativePath = $file.FullName.Substring($COPILOT_PATH.Length).TrimStart('\')
            $components += @{
                "type" = "context"
                "name" = $file.BaseName
                "category" = Split-Path (Split-Path $relativePath -Parent) -Leaf
                "path" = $file.FullName
            }
        }
    }

    if (Test-Path (Join-Path $COPILOT_PATH "knowledge")) {
        $knowledgeFiles = Get-ChildItem -Path (Join-Path $COPILOT_PATH "knowledge") -Filter "*.md" -Recurse -File
        foreach ($file in $knowledgeFiles) {
            $relativePath = $file.FullName.Substring($COPILOT_PATH.Length).TrimStart('\')
            $pathParts = $relativePath.Split('\')
            $components += @{
                "type" = "knowledge"
                "name" = $file.BaseName
                "category" = $pathParts[1]
                "subcategory" = if ($pathParts.Length -gt 2) { $pathParts[2] } else { "general" }
                "path" = $file.FullName
            }
        }
    }

    $manifest["installed_components"] = $components

    # Write manifest
    $manifest | ConvertTo-Json -Depth 10 | Out-File -FilePath $ManifestPath -Encoding UTF8

    return $components.Count
}

# ============================================================================
# Command: Status
# ============================================================================

function Invoke-Status {
    Write-Info "Checking installation status..."
    Write-Log "Checking installation status"
    Write-Host ""

    if (!(Test-Path $COPILOT_PATH)) {
        Write-Warning-Message "Automotive Copilot Agents NOT installed"
        Write-Log "Status check complete: NOT installed" -Level "WARNING"
        Write-Host ""
        Write-Host "Run: .\setup.ps1"
        return
    }

    # Count components
    $agentCount = Get-FileCount (Join-Path $COPILOT_PATH "instructions") "*.md"
    $skillCount = Get-FileCount (Join-Path $COPILOT_PATH "context") "*.md"
    $knowledgeCount = Get-FileCount (Join-Path $COPILOT_PATH "knowledge") "*.md"
    $totalSize = Get-DirectorySize $COPILOT_PATH

    Write-Success "Automotive Copilot Agents INSTALLED"
    Write-Host ""
    Write-Host "Installation Summary:" -ForegroundColor $Color_Info
    Write-Host "  Location: $COPILOT_PATH"
    Write-Host ""
    Write-Host "Components:" -ForegroundColor $Color_Info
    Write-Host "  Agents:       $agentCount"
    Write-Host "  Skills:       $skillCount (context files)"
    Write-Host "  Knowledge:    $knowledgeCount (reference docs)"
    Write-Host "  Total Size:   $(Format-FileSize $totalSize)"
    Write-Host ""

    # Check for manifest
    if (Test-Path $MANIFEST_FILE) {
        $manifest = Get-Content $MANIFEST_FILE | ConvertFrom-Json
        Write-Host "Manifest:" -ForegroundColor $Color_Info
        Write-Host "  Version:      $($manifest.version)"
        Write-Host "  Installed:    $($manifest.install_date)"
        Write-Host ""
    }

    # List agents
    if ($agentCount -gt 0) {
        Write-Host "Installed Agents:" -ForegroundColor $Color_Info
        Get-ChildItem -Path (Join-Path $COPILOT_PATH "instructions") -Filter "*.md" -File |
            ForEach-Object { Write-Host "  - $($_.BaseName)" }
        Write-Host ""
    }

    # List skill categories
    if ($skillCount -gt 0) {
        Write-Host "Skill Categories:" -ForegroundColor $Color_Info
        Get-ChildItem -Path (Join-Path $COPILOT_PATH "context") -Directory |
            ForEach-Object {
                $count = Get-FileCount $_.FullName "*.md"
                Write-Host "  - $($_.Name): $count files"
            }
        Write-Host ""
    }

    # Check VS Code integration
    $vscodeSettingsPath = Join-Path $PROJECT_ROOT ".vscode\settings.json"
    if (Test-Path $vscodeSettingsPath) {
        $vscodeSettings = Get-Content $vscodeSettingsPath | ConvertFrom-Json
        Write-Host "VS Code Integration:" -ForegroundColor $Color_Info

        if ($vscodeSettings."github.copilot.chat.codeGeneration.enabled") {
            Write-Success "  Copilot Chat enabled"
        } else {
            Write-Warning-Message "  Copilot Chat may need manual enable"
        }
    } else {
        Write-Info "  No .vscode/settings.json found (will use global Copilot settings)"
    }

    Write-Host ""
    Write-Host "To uninstall: .\setup.ps1 -Uninstall"

    Write-Log "Status check complete: INSTALLED ($agentCount agents, $skillCount skills, $knowledgeCount knowledge)"
}

# ============================================================================
# Command: Uninstall
# ============================================================================

function Invoke-Uninstall {
    Write-Info "Starting uninstallation..."
    Write-Log "Starting uninstallation"
    Write-Host ""

    if (!(Test-Path $COPILOT_PATH)) {
        Write-Warning-Message "Nothing to uninstall - .github\copilot does not exist"
        Write-Log "Nothing to uninstall - .github\copilot does not exist" -Level "WARNING"
        return
    }

    # Confirm uninstall
    $confirm = Read-Host "Are you sure you want to remove all automotive copilot agents? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Info "Uninstall cancelled"
        Write-Log "Uninstall cancelled by user"
        return
    }

    # Remove .github/copilot directory
    Write-Info "Removing: $COPILOT_PATH"
    Write-Log "Removing copilot directory: $COPILOT_PATH"
    Remove-Item -Path $COPILOT_PATH -Recurse -Force

    Write-Success "Automotive Copilot Agents uninstalled"
    Write-Log "Uninstallation complete"
    Write-Host ""
    Write-Info "Note: This only removes the .github/copilot directory"
    Write-Info "Your .vscode/settings.json and other project files are unchanged"
}

# ============================================================================
# Command: Install
# ============================================================================

function Invoke-Install {
    Write-Info "Starting installation..."
    Write-Log "Starting installation"
    Write-Host ""

    # Verify source directory
    if (!(Test-Path $SOURCE_PATH)) {
        Write-Error-Message "Source directory not found: $SOURCE_PATH"
        Write-Error-Message "Make sure you're running this script from the project root"
        Write-Log "Source directory not found: $SOURCE_PATH" -Level "ERROR"
        exit 1
    }
    Write-Log "Source validated: $SOURCE_PATH"

    # Display what will be installed
    $sourceAgents = Get-FileCount (Join-Path $SOURCE_PATH "instructions") "*.md"
    $sourceSkills = Get-FileCount (Join-Path $SOURCE_PATH "context") "*.md"
    $sourceKnowledge = Get-FileCount (Join-Path $SOURCE_PATH "knowledge") "*.md"
    $sourceSize = Get-DirectorySize $SOURCE_PATH

    Write-Host "Source Content:" -ForegroundColor $Color_Info
    Write-Host "  Agents:       $sourceAgents"
    Write-Host "  Skills:       $sourceSkills (context files)"
    Write-Host "  Knowledge:    $sourceKnowledge (reference docs)"
    Write-Host "  Total Size:   $(Format-FileSize $sourceSize)"
    Write-Host ""

    if ($DryRun) {
        Write-Info "DRY RUN MODE - No changes will be made"
        Write-Host ""
        Write-Host "Would install to: $COPILOT_PATH"
        Write-Host ""

        if (Test-Path $COPILOT_PATH) {
            Write-Warning-Message "Target directory already exists - files will be merged"
            $existingAgents = Get-FileCount (Join-Path $COPILOT_PATH "instructions") "*.md"
            if ($existingAgents -gt 0) {
                Write-Host "  Existing agents: $existingAgents (will be preserved)"
            }
        } else {
            Write-Info "Target directory will be created"
        }

        return
    }

    # Perform installation
    # Backup existing installation if it exists and -NoBackup not specified
    if ((Test-Path $COPILOT_PATH) -and (-not $NoBackup)) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupPath = "$COPILOT_PATH.backup.$timestamp"
        Write-Info "Creating backup: $backupPath"
        Write-Log "Creating backup: $backupPath"
        Copy-Item -Path $COPILOT_PATH -Destination $backupPath -Recurse -Force
        Write-Log "Backup created successfully: $backupPath"
        Write-Host ""
    }

    Write-Info "Installing to: $COPILOT_PATH"
    Write-Host ""

    # Copy components
    $copiedCount = 0

    # Copy instructions (agents)
    if (Test-Path (Join-Path $SOURCE_PATH "instructions")) {
        $count = Copy-Safe -Source (Join-Path $SOURCE_PATH "instructions") -Destination (Join-Path $COPILOT_PATH "instructions")
        Write-Success "Copied $count agent instruction files"
        Write-Log "Copied $count agent instruction files"
        $copiedCount += $count
    }

    # Copy context (skills)
    if (Test-Path (Join-Path $SOURCE_PATH "context")) {
        $count = Copy-Safe -Source (Join-Path $SOURCE_PATH "context") -Destination (Join-Path $COPILOT_PATH "context")
        Write-Success "Copied $count skill context files"
        Write-Log "Copied $count skill context files"
        $copiedCount += $count
    }

    # Copy knowledge base
    if (Test-Path (Join-Path $SOURCE_PATH "knowledge")) {
        $count = Copy-Safe -Source (Join-Path $SOURCE_PATH "knowledge") -Destination (Join-Path $COPILOT_PATH "knowledge")
        Write-Success "Copied $count knowledge files"
        Write-Log "Copied $count knowledge files"
        $copiedCount += $count
    }

    # Copy triggers
    if (Test-Path (Join-Path $SOURCE_PATH "triggers")) {
        $count = Copy-Safe -Source (Join-Path $SOURCE_PATH "triggers") -Destination (Join-Path $COPILOT_PATH "triggers")
        Write-Success "Copied $count trigger files"
        Write-Log "Copied $count trigger files"
        $copiedCount += $count
    }

    # Copy personas
    if (Test-Path (Join-Path $SOURCE_PATH "personas")) {
        $count = Copy-Safe -Source (Join-Path $SOURCE_PATH "personas") -Destination (Join-Path $COPILOT_PATH "personas")
        Write-Success "Copied $count persona files"
        Write-Log "Copied $count persona files"
        $copiedCount += $count
    }

    Write-Host ""
    Write-Success "Installation complete! ($copiedCount files copied)"
    Write-Log "Installation complete: $copiedCount files copied"
    Write-Host ""

    # Create manifest
    $manifestCount = Create-Manifest -ManifestPath $MANIFEST_FILE
    Write-Info "Created installation manifest"
    Write-Log "Manifest created with $manifestCount components"

    Write-Host ""
    Write-Host "================================================================"
    Write-Host "Next Steps:" -ForegroundColor $Color_Info
    Write-Host ""
    Write-Host "1. Restart VS Code to activate GitHub Copilot integration"
    Write-Host ""
    Write-Host "2. Verify installation:"
    Write-Host "   .\setup.ps1 -Status"
    Write-Host ""
    Write-Host "3. Start using automotive agents in Copilot Chat:"
    Write-Host "   - Ask about sensor fusion: 'How do I implement EKF for camera-radar fusion?'"
    Write-Host "   - Ask about safety: 'What ASIL-D requirements apply to brake control?'"
    Write-Host "   - Ask about AUTOSAR: 'Show me an AUTOSAR Adaptive service definition'"
    Write-Host ""
    Write-Host "4. Uninstall (if needed):"
    Write-Host "   .\setup.ps1 -Uninstall"
    Write-Host "================================================================"
}

# ============================================================================
# Main Entry Point
# ============================================================================

Write-Host ""
Write-Host "========================================"
Write-Host "  Automotive Copilot Agents Setup"
Write-Host "  Version 1.0.0"
Write-Host "========================================"
Write-Host ""

try {
    if ($Status) {
        Invoke-Status
    } elseif ($Uninstall) {
        Invoke-Uninstall
    } else {
        Invoke-Install
    }
} catch {
    Write-Error-Message "Installation failed: $_"
    Write-Host ""
    Write-Host "Troubleshooting:"
    Write-Host "  - Run with -DryRun to preview changes"
    Write-Host "  - Run with -Status to check current state"
    Write-Host "  - Ensure PowerShell execution policy allows scripts:"
    Write-Host "    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass"
    exit 1
}
