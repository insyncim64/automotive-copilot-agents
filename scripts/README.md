# Automotive Copilot Agents - Installation Scripts

> Installation, setup, and validation scripts for deploying GitHub Copilot custom instructions for automotive software development.

## Overview

This directory contains cross-platform installation and validation scripts for the Automotive Copilot Agents project. The scripts support Windows (PowerShell), Linux, and macOS (Bash).

| Script | Platform | Purpose |
|--------|----------|---------|
| `setup.ps1` | Windows | Install, update, or uninstall copilot agents |
| `setup.sh` | Linux/macOS | Install, update, or uninstall copilot agents |
| `validate-install.ps1` | Windows | Validate installation integrity |
| `validate-install.sh` | Linux/macOS | Validate installation integrity |

---

## Quick Start

### Windows (PowerShell)

```powershell
# Navigate to project root
cd C:\path\to\automotive-copilot-agents

# Install agents
.\scripts\setup.ps1

# Validate installation
.\scripts\validate-install.ps1
```

### Linux/macOS (Bash)

```bash
# Navigate to project root
cd /path/to/automotive-copilot-agents

# Make scripts executable (first time only)
chmod +x scripts/*.sh

# Install agents
./scripts/setup.sh

# Validate installation
./scripts/validate-install.sh
```

---

## Setup Script Usage

### PowerShell: setup.ps1

#### Installation

```powershell
# Basic installation
.\scripts\setup.ps1

# Install to specific project path
.\scripts\setup.ps1 -ProjectPath "C:\path\to\target\project"

# Preview installation without making changes
.\scripts\setup.ps1 -DryRun

# Show current installation status
.\scripts\setup.ps1 -Status

# Uninstall agents
.\scripts\setup.ps1 -Uninstall
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-ProjectPath` | String | Current directory | Target project path for installation |
| `-DryRun` | Switch | False | Preview installation without copying files |
| `-Status` | Switch | False | Show current installation status |
| `-Uninstall` | Switch | False | Remove installed agents |

#### Output

```
========================================
  Automotive Copilot Agents Setup
  Version 1.0.0
========================================

[INFO] Starting installation...

Source Content:
  Agents:       12
  Skills:       24 (context files)
  Knowledge:    48 (reference docs)
  Total Size:   2.45 MB

[INFO] Installing to: C:\project\.github\copilot

[OK] Copied 12 agent instruction files
[OK] Copied 24 skill context files
[OK] Copied 48 knowledge files

[OK] Installation complete! (84 files copied)

[INFO] Created installation manifest

================================================================
Next Steps:

1. Restart VS Code to activate GitHub Copilot integration

2. Verify installation:
   .\scripts\setup.ps1 -Status

3. Start using automotive agents in Copilot Chat:
   - Ask about sensor fusion: 'How do I implement EKF for camera-radar fusion?'
   - Ask about safety: 'What ASIL-D requirements apply to brake control?'
   - Ask about AUTOSAR: 'Show me an AUTOSAR Adaptive service definition'

4. Uninstall (if needed):
   .\scripts\setup.ps1 -Uninstall
================================================================
```

---

### Bash: setup.sh

#### Installation

```bash
# Basic installation
./scripts/setup.sh

# Install to specific project path
./scripts/setup.sh --project /path/to/target/project

# Preview installation without making changes
./scripts/setup.sh --dry-run

# Show current installation status
./scripts/setup.sh --status

# Uninstall agents
./scripts/setup.sh --uninstall

# Show help
./scripts/setup.sh --help
```

#### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--dry-run` | | Preview installation without copying files |
| `--status` | | Show current installation status |
| `--uninstall` | | Remove installed agents |
| `--project PATH` | | Target project path for installation |
| `--help` | `-h` | Show help message |

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (source not found, copy failed) |

---

## Validation Script Usage

### PowerShell: validate-install.ps1

#### Validation

```powershell
# Basic validation
.\scripts\validate-install.ps1

# Verbose output with file listings
.\scripts\validate-install.ps1 -Verbose

# Attempt to fix common issues (e.g., remove empty files)
.\scripts\validate-install.ps1 -Fix

# Export results as JSON
.\scripts\validate-install.ps1 -OutputFormat json

# Export results as JUnit XML
.\scripts\validate-install.ps1 -OutputFormat junit

# Validate specific project path
.\scripts\validate-install.ps1 -ProjectPath "C:\path\to\target\project"
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-ProjectPath` | String | Current directory | Path to validate |
| `-Verbose` | Switch | False | Show detailed validation output |
| `-Fix` | Switch | False | Attempt to fix common issues |
| `-OutputFormat` | String | text | Output format: text, json, junit |

#### Output Example

```
========================================
  Automotive Copilot Agents Validation
  Version 1.0.0
========================================

[INFO] Starting validation...

Checking directory structure...
[OK] Copilot directory found

Checking installation manifest...
[OK] Manifest file found

Validating agents...
[OK] Agent count: 12 (minimum: 5)

Validating skills...
[OK] Skill count: 24 (minimum: 10)

Validating knowledge base...
[OK] Knowledge count: 48 (minimum: 20)

Validating file integrity...
[OK] All files have content

Validating agent format...
[OK] All agents follow required format

Checking installation size...
[OK] Total installation size: 2.45 MB

Checking VS Code integration...
[OK] Copilot Chat enabled in workspace settings

Validating manifest consistency...
[OK] Manifest consistent with installation

================================================================
  VALIDATION SUMMARY
================================================================

Total Checks:  10
Passed:        10

VALIDATION PASSED
Installation is complete and valid.

================================================================
```

---

### Bash: validate-install.sh

#### Validation

```bash
# Basic validation
./scripts/validate-install.sh

# Verbose output with file listings
./scripts/validate-install.sh --verbose

# Attempt to fix common issues
./scripts/validate-install.sh --fix

# Export results as JSON
./scripts/validate-install.sh --format json

# Export results as JUnit XML
./scripts/validate-install.sh --format junit

# Validate specific project path
./scripts/validate-install.sh --project /path/to/target/project

# Show help
./scripts/validate-install.sh --help
```

#### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Show detailed validation output |
| `--fix` | | Attempt to fix common issues |
| `--format FORMAT` | | Output format: text, json, junit |
| `--project PATH` | | Path to validate |
| `--help` | `-h` | Show help message |

#### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Validation passed |
| 1 | Validation failed |

---

## Validation Checks

Both validation scripts perform the following checks:

| # | Check | Severity | Description |
|---|-------|----------|-------------|
| 1 | Copilot Directory Exists | Error | Verifies `.github/copilot/` directory is present |
| 2 | Manifest File Exists | Warning | Verifies `.install.manifest.json` is present |
| 3 | Agent Count | Error | Verifies minimum 5 agent instruction files |
| 4 | Skill Count | Warning | Verifies minimum 10 skill context files |
| 5 | Knowledge Count | Warning | Verifies minimum 20 knowledge files |
| 6 | File Integrity | Error | Checks for empty markdown files |
| 7 | Agent Format | Warning | Verifies agents have required sections |
| 8 | Installation Size | Info | Reports total size of installation |
| 9 | VS Code Integration | Info | Checks for workspace settings |
| 10 | Manifest Consistency | Info | Verifies manifest matches actual files |

---

## Output Formats

### Text (Default)

Human-readable colored output suitable for terminal display.

### JSON

Machine-readable format for CI/CD integration:

```json
{
  "timestamp": "2026-03-23 10:30:00",
  "project_path": "/path/to/project",
  "copilot_path": "/path/to/project/.github/copilot",
  "overall_status": "PASS",
  "checks_passed": 10,
  "checks_failed": 0,
  "warnings_count": 0,
  "errors_count": 0
}
```

### JUnit XML

Compatible with CI/CD test reporting:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="AutomotiveCopilotValidation" tests="10" failures="0">
  <testsuite name="InstallationValidation" tests="10" failures="0">
    <testcase name="Copilot Directory" classname="Validation" time="0.001"/>
    <!-- Additional test cases -->
  </testsuite>
</testsuites>
```

---

## CI/CD Integration

### GitHub Actions

```yaml
- name: Validate Copilot Installation
  run: |
    chmod +x scripts/*.sh
    ./scripts/validate-install.sh --format junit --verbose

- name: Publish Validation Results
  uses: actions/upload-artifact@v4
  with:
    name: validation-results
    path: validation-results.xml
```

### Azure DevOps

```yaml
- script: |
    chmod +x scripts/*.sh
    ./scripts/validate-install.sh --format junit --verbose
  displayName: 'Validate Copilot Installation'

- task: PublishTestResults@2
  inputs:
    testResultsFiles: 'validation-results.xml'
    testRunTitle: 'Copilot Installation Validation'
```

### Jenkins

```groovy
stage('Validate Copilot Installation') {
    steps {
        sh './scripts/validate-install.sh --format junit --verbose'
        junit 'validation-results.xml'
    }
}
```

---

## Troubleshooting

### PowerShell Execution Policy

If you receive an error about execution policy:

```powershell
# Allow script execution for current session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Or run with explicit PowerShell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

### Permission Denied (Linux/macOS)

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Or run with bash explicitly
bash scripts/setup.sh
```

### Manifest Out of Sync

If validation reports manifest inconsistency:

```bash
# Re-run setup to update manifest
./scripts/setup.sh
```

### Files Not Copying

The setup scripts use append-safe copying:
- Files that already exist are NOT overwritten
- Files with different sizes ARE copied
- New files ARE copied

To force a clean install:

```bash
# Uninstall first
./scripts/setup.sh --uninstall

# Then reinstall
./scripts/setup.sh
```

### Validation Fails

Common causes:

| Issue | Solution |
|-------|----------|
| `.github/copilot/` directory missing | Run `setup.sh` or `setup.ps1` |
| Agent count below minimum | Ensure source has at least 5 agent files |
| Empty files detected | Run with `--fix` to remove empty files |
| Manifest mismatch | Re-run setup to regenerate manifest |

---

## Logging

Both setup scripts create a log file at `scripts/setup.log` with detailed installation output:

```
2026-03-23 10:30:00 - Starting installation
2026-03-23 10:30:01 - Source validated: /path/to/source
2026-03-23 10:30:01 - Destination: /path/to/.github/copilot
2026-03-23 10:30:02 - Copied: instructions/adas-engineer.md
2026-03-23 10:30:02 - Copied: instructions/safety-engineer.md
...
2026-03-23 10:30:05 - Installation complete: 84 files copied
2026-03-23 10:30:05 - Manifest created
```

---

## Backup and Restore

### Manual Backup

Before updating, manually backup your installation:

```bash
# Backup existing installation
cp -r .github/copilot .github/copilot.backup.$(date +%Y%m%d)

# Or on Windows
Copy-Item -Recurse .github\copilot .github\copilot.backup.$(Get-Date -Format "yyyyMMdd")
```

### Restore from Backup

```bash
# Remove current installation
rm -rf .github/copilot

# Restore backup
mv .github/copilot.backup.YYYYMMDD .github/copilot
```

---

## Platform-Specific Notes

### Windows

- PowerShell 5.1+ required
- Run PowerShell as Administrator if installing to protected directories
- Path separators are backslashes (`\`) in output

### Linux

- Bash 4.0+ required
- Ensure `bc` is installed for file size calculations
- Some distributions may need `coreutils` for `stat` command

### macOS

- Bash 3.2+ (included) or install Bash 5+ via Homebrew
- Use `gstat` from coreutils if default `stat` lacks required options
- File size calculations require `bc`

---

## Architecture

### Directory Structure

```
scripts/
├── setup.ps1              # PowerShell installer
├── setup.sh               # Bash installer
├── validate-install.ps1   # PowerShell validation
├── validate-install.sh    # Bash validation
└── README.md              # This documentation
```

### Installation Flow

```
1. Validate source directory exists
2. Display what will be installed (dry-run mode available)
3. Create .github/copilot/ directory
4. Copy files using append-safe algorithm:
   - Skip if file exists with same size
   - Copy if file doesn't exist
   - Copy if file exists with different size
5. Create .install.manifest.json
6. Display next steps
```

### Validation Flow

```
1. Check directory structure
2. Verify manifest exists
3. Count and validate agents
4. Count and validate skills
5. Count and validate knowledge files
6. Check for empty files
7. Validate agent format
8. Calculate installation size
9. Check VS Code integration
10. Verify manifest consistency
11. Generate summary report
```

---

## Security Considerations

- Scripts do not require elevated privileges for normal installation
- No network access required (offline installation)
- No telemetry or data collection
- Manifest file contains only file paths (no secrets)
- Validation is read-only (except `--fix` which only removes empty files)

---

## Related Documentation

- [MIGRATION-PLAN.md](../MIGRATION-PLAN.md) - Full migration strategy
- [.github/copilot/instructions/](../.github/copilot/instructions/) - Agent definitions
- [.github/copilot/knowledge/](../.github/copilot/knowledge/) - Knowledge base

---

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review validation output for specific errors
3. Run setup with `--dry-run` or `-Verbose` for detailed output
4. Consult installation log at `scripts/setup.log`
