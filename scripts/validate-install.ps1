# Automotive Copilot Agents - Installation Validation Script
# Validates the integrity and completeness of installed agents
# Append-safe: read-only validation, no modifications

param(
    [string]$ProjectPath = $PWD,
    [switch]$Verbose,
    [switch]$Fix,
    [string]$OutputFormat = "text"  # text, json, junit
)

$ErrorActionPreference = "Stop"

# ============================================================================
# Configuration
# ============================================================================
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_ROOT = if ($ProjectPath) { $ProjectPath } else { $SCRIPT_DIR }
$COPILOT_PATH = Join-Path $PROJECT_ROOT ".github\copilot"
$MANIFEST_FILE = Join-Path $PROJECT_ROOT ".github\copilot\.install.manifest.json"

# Minimum expected content
$MIN_AGENTS = 5        # At least 5 agents for MVP
$MIN_SKILLS = 10       # At least 10 skill context files
$MIN_KNOWLEDGE = 20    # At least 20 knowledge files

# Colors for output
$Color_Info = "Cyan"
$Color_Success = "Green"
$Color_Warning = "Yellow"
$Color_Error = "Red"

# ============================================================================
# Validation Results Structure
# ============================================================================
$ValidationResult = @{
    "timestamp" = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "project_path" = $PROJECT_ROOT
    "copilot_path" = $COPILOT_PATH
    "overall_status" = "PASS"
    "checks" = @()
    "warnings" = @()
    "errors" = @()
}

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

function Add-ValidationCheck {
    param(
        [string]$Name,
        [string]$Description,
        [bool]$Passed,
        [string]$Details = "",
        [string]$Severity = "error"  # error, warning, info
    )

    $check = @{
        "name" = $Name
        "description" = $Description
        "passed" = $Passed
        "details" = $Details
        "severity" = $Severity
        "timestamp" = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }

    $ValidationResult.checks += $check

    if (-not $Passed) {
        if ($Severity -eq "error") {
            $ValidationResult.errors += "$Name : $Details"
            $ValidationResult.overall_status = "FAIL"
        } elseif ($Severity -eq "warning") {
            $ValidationResult.warnings += "$Name : $Details"
        }
    }

    return $Passed
}

function Get-FileCount {
    param([string]$Path, [string]$Filter = "*.md")
    if (Test-Path $Path) {
        return (Get-ChildItem -Path $Path -Filter $Filter -Recurse -File).Count
    }
    return 0
}

function Get-DirectorySize {
    param([string]$Path)
    if (Test-Path $Path) {
        $items = Get-ChildItem -Path $Path -Recurse -File
        return ($items | Measure-Object -Property Length -Sum).Sum
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

function Test-FileNotEmpty {
    param([string]$Path)
    if (Test-Path $Path) {
        $file = Get-Item $Path
        return $file.Length -gt 0
    }
    return $false
}

function Test-FileHasContent {
    param([string]$Path, [string]$RequiredPattern)
    if (Test-Path $Path) {
        $content = Get-Content $Path -Raw
        return $content -match $RequiredPattern
    }
    return $false
}

# ============================================================================
# Validation Checks
# ============================================================================

function Invoke-ValidationChecks {
    Write-Info "Starting validation..."
    Write-Host ""

    # -------------------------------------------------------------------------
    # Check 1: Copilot Directory Exists
    # -------------------------------------------------------------------------
    Write-Host "Checking directory structure..." -ForegroundColor $Color_Info
    $dirExists = Test-Path $COPILOT_PATH
    Add-ValidationCheck `
        -Name "Copilot Directory" `
        -Description ".github/copilot directory exists" `
        -Passed $dirExists `
        -Details $(if ($dirExists) { "Found at $COPILOT_PATH" } else { "Directory not found" })

    if (-not $dirExists) {
        Write-Error-Message ".github/copilot directory not found"
        Write-Host "Run: .\setup.ps1 to install"
        return
    }
    Write-Success "Copilot directory found"
    Write-Host ""

    # -------------------------------------------------------------------------
    # Check 2: Manifest File Exists
    # -------------------------------------------------------------------------
    Write-Host "Checking installation manifest..." -ForegroundColor $Color_Info
    $manifestExists = Test-Path $MANIFEST_FILE
    Add-ValidationCheck `
        -Name "Installation Manifest" `
        -Description ".install.manifest.json exists" `
        -Passed $manifestExists `
        -Details $(if ($manifestExists) { "Found" } else { "Missing - install may be incomplete" }) `
        -Severity $(if ($manifestExists) { "info" } else { "warning" })

    if ($manifestExists) {
        Write-Success "Manifest file found"
    } else {
        Write-Warning-Message "Manifest file missing"
    }
    Write-Host ""

    # -------------------------------------------------------------------------
    # Check 3: Agent Count Validation
    # -------------------------------------------------------------------------
    Write-Host "Validating agents..." -ForegroundColor $Color_Info
    $agentPath = Join-Path $COPILOT_PATH "instructions"
    $agentCount = Get-FileCount $agentPath "*.md"
    $agentMinMet = $agentCount -ge $MIN_AGENTS

    Add-ValidationCheck `
        -Name "Agent Count" `
        -Description "Minimum agent count ($MIN_AGENTS)" `
        -Passed $agentMinMet `
        -Details "$agentCount agents found"

    if ($agentMinMet) {
        Write-Success "Agent count: $agentCount (minimum: $MIN_AGENTS)"
    } else {
        Write-Warning-Message "Agent count below minimum: $agentCount < $MIN_AGENTS"
    }

    # List agents
    if ($Verbose -and (Test-Path $agentPath)) {
        Write-Host "  Installed agents:" -ForegroundColor $Color_Info
        Get-ChildItem -Path $agentPath -Filter "*.md" -File | ForEach-Object {
            Write-Host "    - $($_.BaseName)"
        }
    }
    Write-Host ""

    # -------------------------------------------------------------------------
    # Check 4: Skill Context Validation
    # -------------------------------------------------------------------------
    Write-Host "Validating skills..." -ForegroundColor $Color_Info
    $contextPath = Join-Path $COPILOT_PATH "context"
    $skillCount = Get-FileCount $contextPath "*.md"
    $skillMinMet = $skillCount -ge $MIN_SKILLS

    Add-ValidationCheck `
        -Name "Skill Context Count" `
        -Description "Minimum skill count ($MIN_SKILLS)" `
        -Passed $skillMinMet `
        -Details "$skillCount skill files found"

    if ($skillMinMet) {
        Write-Success "Skill count: $skillCount (minimum: $MIN_SKILLS)"
    } else {
        Write-Warning-Message "Skill count below minimum: $skillCount < $MIN_SKILLS"
    }

    # List skill categories
    if ($Verbose -and (Test-Path $contextPath)) {
        Write-Host "  Skill categories:" -ForegroundColor $Color_Info
        Get-ChildItem -Path $contextPath -Directory | ForEach-Object {
            $count = Get-FileCount $_.FullName "*.md"
            Write-Host "    - $($_.Name): $count files"
        }
    }
    Write-Host ""

    # -------------------------------------------------------------------------
    # Check 5: Knowledge Base Validation
    # -------------------------------------------------------------------------
    Write-Host "Validating knowledge base..." -ForegroundColor $Color_Info
    $knowledgePath = Join-Path $COPILOT_PATH "knowledge"
    $knowledgeCount = Get-FileCount $knowledgePath "*.md"
    $knowledgeMinMet = $knowledgeCount -ge $MIN_KNOWLEDGE

    Add-ValidationCheck `
        -Name "Knowledge Base Count" `
        -Description "Minimum knowledge count ($MIN_KNOWLEDGE)" `
        -Passed $knowledgeMinMet `
        -Details "$knowledgeCount knowledge files found"

    if ($knowledgeMinMet) {
        Write-Success "Knowledge count: $knowledgeCount (minimum: $MIN_KNOWLEDGE)"
    } else {
        Write-Warning-Message "Knowledge count below minimum: $knowledgeCount < $MIN_KNOWLEDGE"
    }

    # List knowledge categories
    if ($Verbose -and (Test-Path $knowledgePath)) {
        Write-Host "  Knowledge categories:" -ForegroundColor $Color_Info
        Get-ChildItem -Path $knowledgePath -Directory | ForEach-Object {
            $count = Get-FileCount $_.FullName "*.md"
            Write-Host "    - $($_.Name): $count files"
        }
    }
    Write-Host ""

    # -------------------------------------------------------------------------
    # Check 6: File Size Validation (No Empty Files)
    # -------------------------------------------------------------------------
    Write-Host "Validating file integrity..." -ForegroundColor $Color_Info
    $emptyFiles = @()

    if (Test-Path $COPILOT_PATH) {
        $allFiles = Get-ChildItem -Path $COPILOT_PATH -Filter "*.md" -Recurse -File
        foreach ($file in $allFiles) {
            if ($file.Length -eq 0) {
                $emptyFiles += $file.FullName
            }
        }
    }

    $noEmptyFiles = ($emptyFiles.Count -eq 0)
    Add-ValidationCheck `
        -Name "File Integrity" `
        -Description "No empty markdown files" `
        -Passed $noEmptyFiles `
        -Details $(if ($noEmptyFiles) { "All files have content" } else { "$($emptyFiles.Count) empty files found" })

    if ($noEmptyFiles) {
        Write-Success "All files have content"
    } else {
        Write-Warning-Message "$($emptyFiles.Count) empty files found:"
        foreach ($emptyFile in $emptyFiles) {
            Write-Warning-Message "  - $emptyFile"
        }

        if ($Fix) {
            Write-Host "  Removing empty files..." -ForegroundColor $Color_Info
            foreach ($emptyFile in $emptyFiles) {
                Remove-Item -Path $emptyFile -Force
                Write-Host "  Removed: $emptyFile"
            }
        }
    }
    Write-Host ""

    # -------------------------------------------------------------------------
    # Check 7: Agent Format Validation
    # -------------------------------------------------------------------------
    Write-Host "Validating agent format..." -ForegroundColor $Color_Info
    $malformedAgents = @()

    if (Test-Path $agentPath) {
        $agentFiles = Get-ChildItem -Path $agentPath -Filter "*.md" -File
        foreach ($agentFile in $agentFiles) {
            $content = Get-Content $agentFile.FullName -Raw
            # Check for required sections
            if ($content -notmatch "^# .+") {
                $malformedAgents += $agentFile.FullName
            } elseif ($content -notmatch "## When to Activate") {
                $malformedAgents += $agentFile.FullName
            }
        }
    }

    $agentsWellFormed = ($malformedAgents.Count -eq 0)
    Add-ValidationCheck `
        -Name "Agent Format" `
        -Description "Agents follow required format" `
        -Passed $agentsWellFormed `
        -Details $(if ($agentsWellFormed) { "All agents well-formed" } else { "$($malformedAgents.Count) malformed agents" }) `
        -Severity "warning"

    if ($agentsWellFormed) {
        Write-Success "All agents follow required format"
    } else {
        Write-Warning-Message "$($malformedAgents.Count) agents may be malformed:"
        foreach ($malformed in $malformedAgents) {
            Write-Warning-Message "  - $(Split-Path $malformed -Leaf)"
        }
    }
    Write-Host ""

    # -------------------------------------------------------------------------
    # Check 8: Total Installation Size
    # -------------------------------------------------------------------------
    Write-Host "Checking installation size..." -ForegroundColor $Color_Info
    $totalSize = Get-DirectorySize $COPILOT_PATH
    $sizeFormatted = Format-FileSize $totalSize

    Write-Success "Total installation size: $sizeFormatted"
    Write-Host ""

    # -------------------------------------------------------------------------
    # Check 9: VS Code Integration Check
    # -------------------------------------------------------------------------
    Write-Host "Checking VS Code integration..." -ForegroundColor $Color_Info
    $vscodeSettingsPath = Join-Path $PROJECT_ROOT ".vscode\settings.json"
    $vscodeFound = Test-Path $vscodeSettingsPath

    Add-ValidationCheck `
        -Name "VS Code Settings" `
        -Description ".vscode/settings.json exists" `
        -Passed $vscodeFound `
        -Details $(if ($vscodeFound) { "Found" } else { "Not found - will use global Copilot settings" }) `
        -Severity "info"

    if ($vscodeFound) {
        try {
            $vscodeSettings = Get-Content $vscodeSettingsPath | ConvertFrom-Json
            if ($vscodeSettings."github.copilot.chat.codeGeneration.enabled") {
                Write-Success "Copilot Chat enabled in workspace settings"
            } else {
                Write-Warning-Message "Copilot Chat not explicitly enabled (may use global setting)"
            }
        } catch {
            Write-Warning-Message "Could not parse .vscode/settings.json"
        }
    } else {
        Write-Info "No workspace settings found - Copilot will use global configuration"
    }
    Write-Host ""

    # -------------------------------------------------------------------------
    # Check 10: Manifest Consistency (if manifest exists)
    # -------------------------------------------------------------------------
    if ($manifestExists) {
        Write-Host "Validating manifest consistency..." -ForegroundColor $Color_Info
        try {
            $manifest = Get-Content $MANIFEST_FILE | ConvertFrom-Json
            $manifestComponentCount = $manifest.installed_components.Count

            # Count actual files
            $actualCount = $agentCount + $skillCount + $knowledgeCount

            $manifestMatches = ($manifestComponentCount -eq $actualCount)

            Add-ValidationCheck `
                -Name "Manifest Consistency" `
                -Description "Manifest matches installed files" `
                -Passed $manifestMatches `
                -Details "Manifest: $manifestComponentCount components, Actual: $actualCount files" `
                -Severity "info"

            if ($manifestMatches) {
                Write-Success "Manifest consistent with installation"
            } else {
                Write-Warning-Message "Manifest may be out of sync (run setup.ps1 to update)"
            }
        } catch {
            Write-Warning-Message "Could not parse manifest file"
        }
        Write-Host ""
    }
}

# ============================================================================
# Output Generation
# ============================================================================

function Write-Summary {
    Write-Host ""
    Write-Host "================================================================"
    Write-Host "  VALIDATION SUMMARY"
    Write-Host "================================================================"
    Write-Host ""

    $totalChecks = $ValidationResult.checks.Count
    $passedChecks = ($ValidationResult.checks | Where-Object { $_.passed }).Count
    $failedChecks = $totalChecks - $passedChecks

    Write-Host "Total Checks:  $totalChecks"
    Write-Host "Passed:        $passedChecks" -ForegroundColor $Color_Success
    if ($failedChecks -gt 0) {
        Write-Host "Failed:        $failedChecks" -ForegroundColor $Color_Error
    }
    Write-Host ""

    if ($ValidationResult.warnings.Count -gt 0) {
        Write-Host "Warnings:        $($ValidationResult.warnings.Count)" -ForegroundColor $Color_Warning
    }

    Write-Host ""

    if ($ValidationResult.overall_status -eq "PASS") {
        Write-Success "VALIDATION PASSED"
        Write-Host "Installation is complete and valid."
    } else {
        Write-Error-Message "VALIDATION FAILED"
        Write-Host "Installation has issues that need attention."
        Write-Host ""
        Write-Host "Errors:"
        foreach ($error in $ValidationResult.errors) {
            Write-Host "  - $error" -ForegroundColor $Color_Error
        }
    }

    Write-Host ""
    Write-Host "================================================================"
}

function Export-Results {
    param([string]$Format)

    switch ($Format) {
        "json" {
            $outputPath = Join-Path $PROJECT_ROOT "validation-results.json"
            $ValidationResult | ConvertTo-Json -Depth 10 | Out-File -FilePath $outputPath -Encoding UTF8
            Write-Host "Results exported to: $outputPath"
        }
        "junit" {
            $outputPath = Join-Path $PROJECT_ROOT "validation-results.xml"
            $xml = [xml]@"
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="AutomotiveCopilotValidation" tests="$($ValidationResult.checks.Count)" failures="$($ValidationResult.errors.Count)">
  <testsuite name="InstallationValidation" tests="$($ValidationResult.checks.Count)" failures="$($ValidationResult.errors.Count)">
$(foreach ($check in $ValidationResult.checks) {
    "    <testcase name=`"$($check.name)`" classname=`"Validation`" time=`"0.001`">"
    if (-not $check.passed) {
        "      <failure message=`"$($check.details)`" />"
    }
    "    </testcase>"
})
  </testsuite>
</testsuites>
"@
            $xml.Save($outputPath)
            Write-Host "Results exported to: $outputPath"
        }
    }
}

# ============================================================================
# Main Entry Point
# ============================================================================

Write-Host ""
Write-Host "========================================"
Write-Host "  Automotive Copilot Agents Validation"
Write-Host "  Version 1.0.0"
Write-Host "========================================"
Write-Host ""

try {
    Invoke-ValidationChecks
    Write-Summary

    if ($OutputFormat -ne "text") {
        Export-Results -Format $OutputFormat
    }

    # Exit with appropriate code
    if ($ValidationResult.overall_status -eq "PASS") {
        exit 0
    } else {
        exit 1
    }
} catch {
    Write-Error-Message "Validation failed with error: $_"
    exit 2
}
