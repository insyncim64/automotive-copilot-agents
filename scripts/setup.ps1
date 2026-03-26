# Automotive Copilot Agents - Windows Setup Script
# Installs automotive copilot configuration from this template repo into a target project's .github/ directory
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
$SOURCE_REPO_ROOT = [System.IO.Path]::GetFullPath((Join-Path $SCRIPT_DIR ".."))
$TARGET_PROJECT_ROOT = if ($ProjectPath) { [System.IO.Path]::GetFullPath($ProjectPath) } else { (Get-Location).Path }
$SOURCE_GITHUB_PATH = Join-Path $SOURCE_REPO_ROOT ".github"
$SOURCE_COPILOT_PATH = Join-Path $SOURCE_GITHUB_PATH "copilot"
$TARGET_GITHUB_PATH = Join-Path $TARGET_PROJECT_ROOT ".github"
$COPILOT_PATH = Join-Path $TARGET_GITHUB_PATH "copilot"
$MANIFEST_FILE = Join-Path $COPILOT_PATH ".install.manifest.json"
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

function Copy-FileSafe {
    param(
        [string]$SourceFile,
        [string]$DestinationFile
    )

    if (!(Test-Path $SourceFile)) {
        Write-Warning-Message "Source file not found: $SourceFile (skipping)"
        return 0
    }

    $destDir = Split-Path $DestinationFile -Parent
    if (!(Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }

    if (!(Test-Path $DestinationFile)) {
        Copy-Item -Path $SourceFile -Destination $DestinationFile -Force
        return 1
    }

    $sourceSize = (Get-Item $SourceFile).Length
    $targetSize = (Get-Item $DestinationFile).Length
    if ($sourceSize -ne $targetSize) {
        Copy-Item -Path $SourceFile -Destination $DestinationFile -Force
        return 1
    }

    return 0
}

function Create-Manifest {
    param([string]$ManifestPath)

    $manifest = @{
        "version" = "1.0.0"
        "install_date" = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        "project_path" = $TARGET_PROJECT_ROOT
        "source_repo_path" = $SOURCE_REPO_ROOT
        "copilot_path" = $COPILOT_PATH
        "installed_components" = @()
    }

    # Scan installed components
    $components = @()

    $targetAgentsPath = Join-Path $TARGET_GITHUB_PATH "agents"
    if (Test-Path $targetAgentsPath) {
        $agentFiles = Get-ChildItem -Path $targetAgentsPath -Filter "*.agent.md" -File
        foreach ($file in $agentFiles) {
            $components += @{
                "type" = "agent"
                "name" = $file.BaseName
                "path" = $file.FullName
            }
        }
    }

    $targetInstructionsPath = Join-Path $TARGET_GITHUB_PATH "instructions"
    if (Test-Path $targetInstructionsPath) {
        $instructionFiles = Get-ChildItem -Path $targetInstructionsPath -Filter "*.instructions.md" -File
        foreach ($file in $instructionFiles) {
            $components += @{
                "type" = "instruction"
                "name" = $file.BaseName
                "path" = $file.FullName
            }
        }
    }

    $targetPromptsPath = Join-Path $TARGET_GITHUB_PATH "prompts"
    if (Test-Path $targetPromptsPath) {
        $promptFiles = Get-ChildItem -Path $targetPromptsPath -Filter "*.prompt.md" -File
        foreach ($file in $promptFiles) {
            $components += @{
                "type" = "prompt"
                "name" = $file.BaseName
                "path" = $file.FullName
            }
        }
    }

    $targetSkillsPath = Join-Path $TARGET_GITHUB_PATH "skills"
    if (Test-Path $targetSkillsPath) {
        $skillFiles = Get-ChildItem -Path $targetSkillsPath -Filter "SKILL.md" -Recurse -File
        foreach ($file in $skillFiles) {
            $components += @{
                "type" = "skill"
                "name" = Split-Path (Split-Path $file.FullName -Parent) -Leaf
                "path" = $file.FullName
            }
        }
    }

    $workspaceInstructionPath = Join-Path $TARGET_GITHUB_PATH "copilot-instructions.md"
    if (Test-Path $workspaceInstructionPath) {
        $components += @{
            "type" = "workspace-instruction"
            "name" = "copilot-instructions"
            "path" = $workspaceInstructionPath
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

    if (!(Test-Path $TARGET_GITHUB_PATH)) {
        Write-Warning-Message "Automotive Copilot Agents NOT installed"
        Write-Log "Status check complete: NOT installed" -Level "WARNING"
        Write-Host ""
        Write-Host "Run: .\setup.ps1"
        return
    }

    # Count components
    $agentCount = Get-FileCount (Join-Path $TARGET_GITHUB_PATH "agents") "*.agent.md"
    $instructionCount = Get-FileCount (Join-Path $TARGET_GITHUB_PATH "instructions") "*.instructions.md"
    $promptCount = Get-FileCount (Join-Path $TARGET_GITHUB_PATH "prompts") "*.prompt.md"
    $skillCount = Get-FileCount (Join-Path $TARGET_GITHUB_PATH "skills") "SKILL.md"
    $contextCount = Get-FileCount (Join-Path $COPILOT_PATH "context") "*.md"
    $knowledgeCount = Get-FileCount (Join-Path $COPILOT_PATH "knowledge") "*.md"
    $totalSize = Get-DirectorySize $TARGET_GITHUB_PATH

    Write-Success "Automotive Copilot Agents INSTALLED"
    Write-Host ""
    Write-Host "Installation Summary:" -ForegroundColor $Color_Info
    Write-Host "  Location: $TARGET_GITHUB_PATH"
    Write-Host ""
    Write-Host "Components:" -ForegroundColor $Color_Info
    Write-Host "  Agents:       $agentCount"
    Write-Host "  Instructions: $instructionCount"
    Write-Host "  Prompts:      $promptCount"
    Write-Host "  Skills:       $skillCount"
    Write-Host "  Context:      $contextCount"
    Write-Host "  Knowledge:    $knowledgeCount"
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
        Get-ChildItem -Path (Join-Path $TARGET_GITHUB_PATH "agents") -Filter "*.agent.md" -File |
            ForEach-Object { Write-Host "  - $($_.BaseName)" }
        Write-Host ""
    }

    # List skill categories
    if ($skillCount -gt 0) {
        Write-Host "Skill Categories:" -ForegroundColor $Color_Info
        Get-ChildItem -Path (Join-Path $TARGET_GITHUB_PATH "skills") -Directory |
            ForEach-Object {
                $count = Get-FileCount $_.FullName "SKILL.md"
                Write-Host "  - $($_.Name): $count files"
            }
        Write-Host ""
    }

    # Check VS Code integration
    $vscodeSettingsPath = Join-Path $TARGET_PROJECT_ROOT ".vscode\settings.json"
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

    Write-Log "Status check complete: INSTALLED ($agentCount agents, $instructionCount instructions, $skillCount skills, $contextCount context, $knowledgeCount knowledge)"
}

# ============================================================================
# Command: Uninstall
# ============================================================================

function Invoke-Uninstall {
    Write-Info "Starting uninstallation..."
    Write-Log "Starting uninstallation"
    Write-Host ""

    if (!(Test-Path $MANIFEST_FILE)) {
        Write-Warning-Message "Nothing to uninstall - install manifest not found: $MANIFEST_FILE"
        Write-Log "Nothing to uninstall - install manifest not found" -Level "WARNING"
        return
    }

    # Confirm uninstall
    $confirm = Read-Host "Are you sure you want to remove all automotive copilot agents? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Info "Uninstall cancelled"
        Write-Log "Uninstall cancelled by user"
        return
    }

    $manifest = Get-Content $MANIFEST_FILE | ConvertFrom-Json
    $removedCount = 0
    foreach ($component in $manifest.installed_components) {
        if ($component.path -and (Test-Path $component.path)) {
            Remove-Item -Path $component.path -Force -ErrorAction SilentlyContinue
            if (!(Test-Path $component.path)) {
                $removedCount++
            }
        }
    }

    if (Test-Path $MANIFEST_FILE) {
        Remove-Item -Path $MANIFEST_FILE -Force -ErrorAction SilentlyContinue
    }

    # Remove now-empty directories for installed layout where possible.
    $cleanupDirs = @(
        (Join-Path $TARGET_GITHUB_PATH "agents"),
        (Join-Path $TARGET_GITHUB_PATH "instructions"),
        (Join-Path $TARGET_GITHUB_PATH "prompts"),
        (Join-Path $TARGET_GITHUB_PATH "skills"),
        (Join-Path $COPILOT_PATH "context"),
        (Join-Path $COPILOT_PATH "knowledge"),
        $COPILOT_PATH
    )
    foreach ($dir in $cleanupDirs) {
        if ((Test-Path $dir) -and ((Get-ChildItem -Path $dir -Force -ErrorAction SilentlyContinue).Count -eq 0)) {
            Remove-Item -Path $dir -Force -ErrorAction SilentlyContinue
        }
    }

    Write-Success "Automotive Copilot Agents uninstalled"
    Write-Log "Uninstallation complete, removed components: $removedCount"
    Write-Host ""
    Write-Info "Removed components tracked by install manifest"
    Write-Info "Your .vscode/settings.json and unrelated project files are unchanged"
}

# ============================================================================
# Command: Install
# ============================================================================

function Invoke-Install {
    Write-Info "Starting installation..."
    Write-Log "Starting installation"
    Write-Host ""

    # Verify source directory
    if (!(Test-Path $SOURCE_GITHUB_PATH)) {
        Write-Error-Message "Source directory not found: $SOURCE_GITHUB_PATH"
        Write-Error-Message "Make sure you're running this script from the automotive-copilot-agents repository"
        Write-Log "Source directory not found: $SOURCE_GITHUB_PATH" -Level "ERROR"
        exit 1
    }
    Write-Log "Source validated: $SOURCE_GITHUB_PATH"

    # Display what will be installed
    $sourceAgents = Get-FileCount (Join-Path $SOURCE_GITHUB_PATH "agents") "*.agent.md"
    $sourceInstructions = Get-FileCount (Join-Path $SOURCE_GITHUB_PATH "instructions") "*.instructions.md"
    $sourcePrompts = Get-FileCount (Join-Path $SOURCE_GITHUB_PATH "prompts") "*.prompt.md"
    $sourceSkills = Get-FileCount (Join-Path $SOURCE_GITHUB_PATH "skills") "SKILL.md"
    $sourceContext = Get-FileCount (Join-Path $SOURCE_COPILOT_PATH "context") "*.md"
    $sourceKnowledge = Get-FileCount (Join-Path $SOURCE_COPILOT_PATH "knowledge") "*.md"
    $sourceSize = Get-DirectorySize $SOURCE_GITHUB_PATH

    Write-Host "Source Content:" -ForegroundColor $Color_Info
    Write-Host "  Agents:       $sourceAgents"
    Write-Host "  Instructions: $sourceInstructions"
    Write-Host "  Prompts:      $sourcePrompts"
    Write-Host "  Skills:       $sourceSkills"
    Write-Host "  Context:      $sourceContext"
    Write-Host "  Knowledge:    $sourceKnowledge"
    Write-Host "  Total Size:   $(Format-FileSize $sourceSize)"
    Write-Host ""

    if ($DryRun) {
        Write-Info "DRY RUN MODE - No changes will be made"
        Write-Host ""
        Write-Host "Source template: $SOURCE_GITHUB_PATH"
        Write-Host "Would install to: $TARGET_GITHUB_PATH"
        Write-Host ""

        if (Test-Path $TARGET_GITHUB_PATH) {
            Write-Warning-Message "Target .github directory already exists - files will be merged"
            $existingAgents = Get-FileCount (Join-Path $TARGET_GITHUB_PATH "agents") "*.agent.md"
            if ($existingAgents -gt 0) {
                Write-Host "  Existing agents: $existingAgents (will be preserved)"
            }
        } else {
            Write-Info "Target directory will be created"
        }

        return
    }

    # Perform installation
    # Backup existing target .github if it exists and -NoBackup not specified
    if ((Test-Path $TARGET_GITHUB_PATH) -and (-not $NoBackup)) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backupPath = "$TARGET_GITHUB_PATH.backup.$timestamp"
        Write-Info "Creating backup: $backupPath"
        Write-Log "Creating backup: $backupPath"
        Copy-Item -Path $TARGET_GITHUB_PATH -Destination $backupPath -Recurse -Force
        Write-Log "Backup created successfully: $backupPath"
        Write-Host ""
    }

    Write-Info "Installing to: $TARGET_GITHUB_PATH"
    Write-Host ""

    # Copy components
    $copiedCount = 0

    # Copy workspace instruction
    $count = Copy-FileSafe -SourceFile (Join-Path $SOURCE_GITHUB_PATH "copilot-instructions.md") -DestinationFile (Join-Path $TARGET_GITHUB_PATH "copilot-instructions.md")
    Write-Success "Copied $count workspace instruction file"
    Write-Log "Copied $count workspace instruction file"
    $copiedCount += $count

    # Copy agent profiles
    if (Test-Path (Join-Path $SOURCE_GITHUB_PATH "agents")) {
        $count = Copy-Safe -Source (Join-Path $SOURCE_GITHUB_PATH "agents") -Destination (Join-Path $TARGET_GITHUB_PATH "agents")
        Write-Success "Copied $count agent files"
        Write-Log "Copied $count agent files"
        $copiedCount += $count
    }

    # Copy canonical instructions
    if (Test-Path (Join-Path $SOURCE_GITHUB_PATH "instructions")) {
        $count = Copy-Safe -Source (Join-Path $SOURCE_GITHUB_PATH "instructions") -Destination (Join-Path $TARGET_GITHUB_PATH "instructions")
        Write-Success "Copied $count instruction files"
        Write-Log "Copied $count instruction files"
        $copiedCount += $count
    }

    # Copy prompts
    if (Test-Path (Join-Path $SOURCE_GITHUB_PATH "prompts")) {
        $count = Copy-Safe -Source (Join-Path $SOURCE_GITHUB_PATH "prompts") -Destination (Join-Path $TARGET_GITHUB_PATH "prompts")
        Write-Success "Copied $count prompt files"
        Write-Log "Copied $count prompt files"
        $copiedCount += $count
    }

    # Copy skills
    if (Test-Path (Join-Path $SOURCE_GITHUB_PATH "skills")) {
        $count = Copy-Safe -Source (Join-Path $SOURCE_GITHUB_PATH "skills") -Destination (Join-Path $TARGET_GITHUB_PATH "skills")
        Write-Success "Copied $count skill files"
        Write-Log "Copied $count skill files"
        $copiedCount += $count
    }

    # Copy copilot context
    if (Test-Path (Join-Path $SOURCE_COPILOT_PATH "context")) {
        $count = Copy-Safe -Source (Join-Path $SOURCE_COPILOT_PATH "context") -Destination (Join-Path $COPILOT_PATH "context")
        Write-Success "Copied $count context files"
        Write-Log "Copied $count context files"
        $copiedCount += $count
    }

    # Copy knowledge base
    if (Test-Path (Join-Path $SOURCE_COPILOT_PATH "knowledge")) {
        $count = Copy-Safe -Source (Join-Path $SOURCE_COPILOT_PATH "knowledge") -Destination (Join-Path $COPILOT_PATH "knowledge")
        Write-Success "Copied $count knowledge files"
        Write-Log "Copied $count knowledge files"
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
    Write-Host "1. Restart VS Code (or reload window) to refresh GitHub Copilot customization discovery"
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
