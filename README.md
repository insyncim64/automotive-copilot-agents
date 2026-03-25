<p align="center">
  <img src="docs/assets/banner.png" alt="Automotive Copilot Agents" width="800" />
</p>

<h1 align="center">Automotive Copilot Agents</h1>

<p align="center">
  <strong>The automotive engineer's AI-powered command center for GitHub Copilot</strong>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT" /></a>
  <a href="https://github.com/features/copilot"><img src="https://img.shields.io/badge/Built%20for-GitHub%20Copilot-7C3AED" alt="Built for GitHub Copilot" /></a>
  <a href="#domains-covered"><img src="https://img.shields.io/badge/Agents-9-green" alt="9 Agents" /></a>
  <a href="#whats-inside"><img src="https://img.shields.io/badge/Context-7-orange" alt="7 Context Files" /></a>
  <a href="#whats-inside"><img src="https://img.shields.io/badge/Knowledge-60+-blue" alt="60+ Knowledge Files" /></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> |
  <a href="#why-this-exists">Why This Exists</a> |
  <a href="#whats-inside">What's Inside</a> |
  <a href="#domains-covered">Domains</a> |
  <a href="#validation">Validation</a> |
  <a href="README_CN.md">中文说明</a>
</p>

---

> **Ported from** [automotive-claude-code-agents](https://github.com/theja0473/automotive-claude-code-agents) by Yuxin Zhang
>
> This project adapts the original automotive AI agent framework for GitHub Copilot Custom Instructions, providing domain-expert assistance directly in your IDE through @-mention activation.

---

## Why This Exists

Automotive software engineering is one of the most complex and regulated domains in the world. Engineers juggle **ISO 26262 functional safety**, **AUTOSAR architectures**, **MISRA compliance**, **cybersecurity standards**, and **real-time embedded constraints** -- all while shipping on aggressive timelines.

**Automotive Copilot Agents** turns GitHub Copilot into a domain-expert assistant that understands the automotive stack from silicon to cloud. Instead of spending hours looking up ASIL decomposition rules or AUTOSAR naming conventions, you get instant, standards-compliant guidance woven directly into your development workflow.

One install. Zero config. Your existing workspace stays untouched.

```
Before:  "How do I structure an FMEA for this BMS module?" -> 2 hours of research
After:   @automotive-functional-safety-engineer "Generate FMEA for overcurrent protection in ASIL-D BMS" -> 2 minutes
```

---

## Quick Start

### Windows (PowerShell)

```powershell
# 1. Navigate to the project
cd C:\path\to\automotive-copilot-agents

# 2. Preview installation (no changes made)
.\scripts\setup.ps1 -DryRun

# 3. Install agents to your project
.\scripts\setup.ps1

# 4. Validate installation
.\scripts\validate-install.ps1

# 5. Restart VS Code and use @-mention activation
# In Copilot Chat: @automotive-functional-safety-engineer Help me design ISO 26262 ASIL-D compliant BMS
```

### Linux/macOS (Bash)

```bash
# 1. Navigate to the project
cd /path/to/automotive-copilot-agents

# 2. Make scripts executable (first time only)
chmod +x scripts/*.sh

# 3. Preview installation
./scripts/setup.sh --dry-run

# 4. Install agents
./scripts/setup.sh

# 5. Validate installation
./scripts/validate-install.sh
```

### Verify Installation

```bash
# Check installation status
.\scripts\setup.ps1 -Status

# Run validation with verbose output
.\scripts\validate-install.ps1 -Verbose

# Export validation results as JSON
.\scripts\validate-install.ps1 -OutputFormat json
```

### Using the Agents

Once installed, activate agents in GitHub Copilot Chat using @-mention:

```
@automotive-functional-safety-engineer Generate HARA for battery over-voltage protection
@automotive-cybersecurity-engineer Perform TARA for OTA update system
@automotive-autosar-architect Design AUTOSAR Adaptive service for camera fusion
@automotive-battery-bms-engineer Implement SOC estimation using EKF
@automotive-adas-planning-engineer Design path planning for highway lane change
@automotive-adas-control-engineer Implement lateral control with MPC
@automotive-powertrain-control-engineer Design torque management strategy
@automotive-chassis-systems-engineer Implement ESC control algorithm
@automotive-diagnostics-engineer Implement UDS Service 0x22 ReadDataByIdentifier
```

---

## What's Inside

| Component | Count | Location | Description |
|-----------|------:|----------|-------------|
| **Agents** | 9 | `.github/copilot/instructions/` | Specialized AI personas for automotive domains |
| **Context Files** | 7 | `.github/copilot/context/adas/` | ADAS-specific context and reference data |
| **Knowledge Base** | 60+ | `.github/copilot/knowledge/` | Standards, processes, and technology reference docs |

### How It Integrates

```
Your Project                          +  Automotive Copilot Agents
                                      |
.github/                              |
  copilot/                            |
    instructions/      (untouched)    |  automotive-*.md agents added
    context/           (untouched)    |  adas/ context files added
    knowledge/         (untouched)    |  standards/, processes/, technologies/ added
```

---

## Domains Covered

| Domain | Agent | What You Get |
|--------|-------|-------------|
| **Functional Safety** | @automotive-functional-safety-engineer | HARA, FMEA, FTA, ASIL decomposition, ISO 26262 lifecycle, safety cases |
| **Cybersecurity** | @automotive-cybersecurity-engineer | TARA, ISO 21434 compliance, SecOC, secure boot, PKI, intrusion detection |
| **AUTOSAR Architecture** | @automotive-autosar-architect | Classic/Adaptive platform design, SWC scaffolding, RTE generation, BSW config |
| **Battery & BMS** | @automotive-battery-bms-engineer | SOC/SOH estimation, cell balancing, thermal management, ISO 12405 compliance |
| **ADAS Planning** | @automotive-adas-planning-engineer | Path planning, trajectory generation, behavioral prediction, SOTIF analysis |
| **ADAS Control** | @automotive-adas-control-engineer | Lateral/longitudinal control, MPC, sensor fusion, perception pipelines |
| **Powertrain** | @automotive-powertrain-control-engineer | Engine/transmission control, torque management, emissions compliance |
| **Chassis Systems** | @automotive-chassis-systems-engineer | ESC, ABS, EPS, suspension control, vehicle dynamics |
| **Diagnostics** | @automotive-diagnostics-engineer | UDS (ISO 14229), OBD-II, DTC management, DoIP, flash programming |

### Standards Coverage

| Standard | Coverage | What It Provides |
|----------|----------|-----------------|
| ISO 26262 (Functional Safety) | Full lifecycle | ASIL classification, HARA, FMEA, FTA, safety case templates |
| ISO 21434 (Cybersecurity) | Full lifecycle | TARA methodology, SecOC, secure boot, incident response |
| ISO 21448 (SOTIF) | Sensor/perception | Triggering condition analysis, ODD definition, validation |
| AUTOSAR Classic R22-11 | BSW + RTE | Module naming, API patterns, configuration templates |
| AUTOSAR Adaptive R22-11 | ara::\* APIs | Service design, execution management, communication |
| MISRA C:2012 / C++:2023 | All rules | Violation detection, deviation templates, CI gates |
| ASPICE v3.1 | SWE.1-6 | Process templates, work products, traceability |
| UN R155 / R156 | Cybersecurity/OTA | CSMS requirements, OTA security, update management |

---

## Project Structure

```
automotive-copilot-agents/
  .github/copilot/
    instructions/              # 9 agent definition files
      automotive-functional-safety-engineer.md
      automotive-cybersecurity-engineer.md
      automotive-autosar-architect.md
      automotive-battery-bms-engineer.md
      automotive-adas-planning-engineer.md
      automotive-adas-control-engineer.md
      automotive-powertrain-control-engineer.md
      automotive-chassis-systems-engineer.md
      automotive-diagnostics-engineer.md
    context/
      adas/                    # ADAS-specific context
        sensor-fusion.md
        camera-processing.md
        radar-processing.md
        lidar-processing.md
        object-tracking.md
        calibration.md
        sotif-testing.md
    knowledge/
      standards/               # Standards reference library
        iso26262/              # Functional safety (5 files)
        autosar-classic/       # AUTOSAR Classic (5 files)
        autosar-adaptive/      # AUTOSAR Adaptive (5 files)
        iso21434/              # Cybersecurity (5 files)
        iso21448-sotif/        # SOTIF (5 files)
        aspice/                # ASPICE (5 files)
        misra/                 # MISRA guidelines (5 files)
        unr155/                # UN R155 (5 files)
        china-standards/       # China mandatory standards
      processes/               # Development processes
        ci-cd/                 # CI/CD pipelines (5 files)
        code-review/           # Code review guidelines (5 files)
        fmea/                  # FMEA methodology (5 files)
      technologies/            # Technology reference
        battery-management/    # BMS technologies (5 files)
        sensor-fusion/         # Fusion algorithms (5 files)
        autonomous-driving/    # AD technologies (5 files)
        v2x/                   # V2X communication (5 files)
        ota-updates/           # OTA systems (5 files)
        hil-testing/           # HIL test setups (5 files)
  scripts/
    setup.ps1                  # Windows installer
    setup.sh                   # Linux/macOS installer
    validate-install.ps1       # Windows validation
    validate-install.sh        # Linux/macOS validation
    README.md                  # Script documentation
  README.md                    # This file
```

---

## Installation

### Append-Safe Guarantee

The installation scripts are designed to be safe for repeated use:

- **Never overwrites** existing files with the same content
- **Updates** files that have changed
- **Adds** new files without removing existing ones
- **Tracks** all installed files in `.install.manifest.json`
- **Supports** clean uninstall via `-Uninstall` flag

### Installation Parameters

#### PowerShell (setup.ps1)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-ProjectPath` | String | Current directory | Target project for installation |
| `-DryRun` | Switch | False | Preview without making changes |
| `-Status` | Switch | False | Show current installation status |
| `-Uninstall` | Switch | False | Remove installed agents |

#### Bash (setup.sh)

| Option | Short | Description |
|--------|-------|-------------|
| `--dry-run` | | Preview without making changes |
| `--status` | | Show current installation status |
| `--uninstall` | | Remove installed agents |
| `--project PATH` | | Target project for installation |
| `--help` | `-h` | Show help message |

---

## Validation

The validation scripts perform 10 comprehensive checks:

| # | Check | Severity | Description |
|---|-------|----------|-------------|
| 1 | Copilot Directory Exists | Error | Verifies `.github/copilot/` directory present |
| 2 | Manifest File Exists | Warning | Verifies `.install.manifest.json` present |
| 3 | Agent Count | Error | Minimum 5 agents required (9 installed) |
| 4 | Skill/Context Count | Warning | Minimum 10 context files (7 installed) |
| 5 | Knowledge Count | Warning | Minimum 20 knowledge files (60+ installed) |
| 6 | File Integrity | Error | Checks for empty markdown files |
| 7 | Agent Format | Warning | Verifies required sections present |
| 8 | Installation Size | Info | Reports total size |
| 9 | VS Code Integration | Info | Checks workspace settings |
| 10 | Manifest Consistency | Info | Verifies manifest matches files |

### Validation Parameters

#### PowerShell (validate-install.ps1)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-ProjectPath` | String | Current directory | Path to validate |
| `-Verbose` | Switch | False | Detailed output with file listings |
| `-Fix` | Switch | False | Attempt to fix common issues |
| `-OutputFormat` | String | text | Format: text, json, junit |

#### Bash (validate-install.sh)

| Option | Short | Description |
|--------|-------|-------------|
| `--verbose` | `-v` | Detailed output |
| `--fix` | | Fix common issues |
| `--format FORMAT` | | Format: text, json, junit |
| `--project PATH` | | Path to validate |
| `--help` | `-h` | Show help |

---

## CI/CD Integration

### GitHub Actions

```yaml
- name: Validate Copilot Agents Installation
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
  displayName: 'Validate Copilot Agents Installation'

- task: PublishTestResults@2
  inputs:
    testResultsFiles: 'validation-results.xml'
    testRunTitle: 'Copilot Agents Installation Validation'
```

### Jenkins

```groovy
stage('Validate Copilot Agents') {
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

### Validation Fails

| Issue | Solution |
|-------|----------|
| `.github/copilot/` missing | Run `setup.ps1` or `setup.sh` |
| Agent count below minimum | Ensure source has at least 5 agent files |
| Empty files detected | Run with `--fix` to remove empty files |
| Manifest mismatch | Re-run setup to regenerate manifest |

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

---

## Related Documentation

- [scripts/README.md](scripts/README.md) - Installation and validation script documentation
- [.github/copilot/instructions/](.github/copilot/instructions/) - Agent definitions
- [.github/copilot/context/](.github/copilot/context/) - Context files
- [.github/copilot/knowledge/](.github/copilot/knowledge/) - Knowledge base

---

## License

[MIT License](LICENSE) -- free for commercial and personal use.

Copyright (c) 2026 Automotive Copilot Agents Contributors

Original project: [automotive-claude-code-agents](https://github.com/theja0473/automotive-claude-code-agents)

---

<p align="center">
  <sub>Built with care for the automotive engineering community.</sub><br/>
  <sub>If this project helps your work, consider giving it a star.</sub>
</p>
