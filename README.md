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
  <a href="#whats-inside"><img src="https://img.shields.io/badge/Agents-15-green" alt="15 Agents" /></a>
  <a href="#whats-inside"><img src="https://img.shields.io/badge/Skills-30-teal" alt="30 Skills" /></a>
  <a href="#whats-inside"><img src="https://img.shields.io/badge/Context-38-orange" alt="38 Context Files" /></a>
  <a href="#whats-inside"><img src="https://img.shields.io/badge/Knowledge-117-blue" alt="117 Knowledge Files" /></a>
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
> This project adapts the original automotive AI agent framework for GitHub Copilot customizations, providing domain-expert assistance directly in your IDE through workspace instructions, agents, skills, prompts, context, and knowledge grounding.

---

## Why This Exists

Automotive software engineering is one of the most complex and regulated domains in the world. Engineers juggle **ISO 26262 functional safety**, **AUTOSAR architectures**, **MISRA compliance**, **cybersecurity standards**, and **real-time embedded constraints** -- all while shipping on aggressive timelines.

**Automotive Copilot Agents** turns GitHub Copilot into a domain-expert assistant that understands the automotive stack from silicon to cloud. Instead of spending hours looking up ASIL decomposition rules or AUTOSAR naming conventions, you get instant, standards-compliant guidance woven directly into your development workflow.

One install. Minimal manual setup. Your target project's `.github` customization layer is updated in a controlled, append-safe way.

```
Before:  "How do I structure an FMEA for this BMS module?" -> 2 hours of research
After:   Select the functional safety agent, attach ISO 26262 grounding, and ask for an ASIL-D BMS FMEA -> 2 minutes
```

---

## Quick Start

### Windows (PowerShell)

```powershell
# 1. Navigate to the project
cd C:\path\to\automotive-copilot-agents

# 2. Preview installation (no changes made)
.\scripts\setup.ps1 -ProjectPath C:\path\to\your-project -DryRun

# 3. Install the .github customization package to your project
.\scripts\setup.ps1 -ProjectPath C:\path\to\your-project

# 4. Validate installation
.\scripts\validate-install.ps1 -ProjectPath C:\path\to\your-project

# 5. Restart VS Code, select an automotive agent in Copilot Chat, and attach grounding files when needed
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
.\scripts\setup.ps1 -ProjectPath C:\path\to\your-project -Status

# Run validation with verbose output
.\scripts\validate-install.ps1 -ProjectPath C:\path\to\your-project -Verbose

# Export validation results as JSON
.\scripts\validate-install.ps1 -ProjectPath C:\path\to\your-project -OutputFormat json
```

### Using the Customizations

Once installed, you can combine multiple Copilot customization surfaces in one chat:

- Select a domain agent explicitly in the Copilot UI when you want a specialist persona
- Let repository and file-scoped instructions apply automatically when relevant
- Run prompt files and skills as slash commands for focused workflows
- Attach context or knowledge files to ground the answer in standards or domain references

Example prompts:

```
Select the automotive-functional-safety-engineer agent, then ask: Generate HARA for battery over-voltage protection
Select the automotive-cybersecurity-engineer agent, then ask: Perform TARA for OTA update system
Select the automotive-autosar-architect agent, then ask: Design AUTOSAR Adaptive service for camera fusion
Select the automotive-battery-bms-engineer agent, then ask: Implement SOC estimation using EKF
Select the automotive-adas-planning-engineer agent, then ask: Design path planning for highway lane change
Select the automotive-adas-control-engineer agent, then ask: Implement lateral control with MPC
Select the automotive-powertrain-control-engineer agent, then ask: Design torque management strategy
Select the automotive-chassis-systems-engineer agent, then ask: Implement ESC control algorithm
Select the automotive-diagnostics-engineer agent, then ask: Implement UDS Service 0x22 ReadDataByIdentifier
```

To ground an answer with project references, attach a context or knowledge file first, then ask your question. For example:

```text
Select the automotive-functional-safety-engineer agent.
Attach .github/copilot/knowledge/standards/iso26262/2-conceptual.md.
Use .github/copilot/knowledge/standards/iso26262/2-conceptual.md as grounding.
Derive an ASIL rationale for battery over-voltage detection.
```

---

## What's Inside

| Component | Count | Location | Description |
|-----------|------:|----------|-------------|
| **Workspace Instruction** | 1 | `.github/copilot-instructions.md` | Always-on workspace guidance |
| **Agents** | 15 | `.github/agents/` | Reusable specialized agent profiles with trigger metadata |
| **Instructions** | 15 | `.github/instructions/` | Canonical instruction content for automotive domains |
| **Prompts** | 3 | `.github/prompts/` | Reusable task templates |
| **Skills** | 30 | `.github/skills/` | Modular skill packages with focused workflows |
| **Context Files** | 38 | `.github/copilot/context/` | Attachment-ready domain grounding |
| **Knowledge Base** | 117 | `.github/copilot/knowledge/` | Standards, processes, and technology reference docs |

### How It Integrates

```
Target Project/.github/
  copilot-instructions.md             # workspace-level always-on behavior
  agents/                             # reusable agent profiles
  instructions/                       # canonical instruction files
  prompts/                            # reusable prompt templates
  skills/                             # skill packages
  copilot/
  context/                          # attachable context files
    knowledge/                        # attachable reference corpus for grounding
```

The installer copies this template repository's `.github/` structure into the target project's `.github/` folder. In the current layout, `.github/copilot/` is reserved for `context/` and `knowledge/`, while agents, instructions, prompts, and skills live directly under `.github/`.

---

## How Activation Works

Each customization surface serves a different purpose:

| Surface | Location | How It Activates | Best Use |
|--------|----------|------------------|----------|
| **Workspace Instruction** | `.github/copilot-instructions.md` | Always loaded for the workspace | Global engineering priorities and discovery rules |
| **Instruction** | `.github/instructions/*.instructions.md` | Automatically applied when the active task or file matches the instruction scope | Domain guidance for relevant files and tasks |
| **Agent** | `.github/agents/*.agent.md` | Explicitly selected in the Copilot UI | Force a specialized domain persona |
| **Skill** | `.github/skills/*/SKILL.md` | Manually invoked in chat as a slash command (for example `/skill-name`) | Focused repeatable workflows |
| **Prompt** | `.github/prompts/*.prompt.md` | Manually invoked in chat as a slash command (for example `/prompt-name`) | Structured one-shot tasks |
| **Context** | `.github/copilot/context/**` | Attached manually as chat context | Lightweight domain grounding |
| **Knowledge** | `.github/copilot/knowledge/**` | Attached manually to chat | Deep standards/process/technology grounding |

### Agents

Use agents when you want to force Copilot into a specific automotive specialist mode. Select the agent explicitly in the Copilot interface before sending your request:

```text
Select automotive-diagnostics-engineer, then ask: Implement UDS Service 0x19 for DTC readout
Select automotive-functional-safety-engineer, then ask: Review this safety requirement for ISO 26262 compliance
```

### Instructions

Instructions are not usually invoked manually. They are the canonical guidance files Copilot uses automatically when the task or file type matches the instruction metadata. For example, editing AUTOSAR XML, embedded C, or safety documents can pull in different instruction sets automatically.

### Skills

Skills are modular reusable workflows. Use them when you want a focused capability rather than a whole persona. They complement agents and instructions rather than replacing them.

In Copilot Chat, invoke skills as slash commands (`/skill-name`) and optionally attach additional context or knowledge files.

### Prompts

Prompts are reusable task templates. Use them when you want a structured request format for repeated tasks such as controller generation, ASIL validation, or BMS architecture creation.

In VS Code, enable prompt files and invoke them directly as slash commands (`/prompt-name`). You can also run a prompt via the command palette or prompt editor actions.

Examples:

```text
/generate-acc-controller to draft a longitudinal ACC controller.
/validate-asil-compliance to review this requirement set.
/create-bms-architecture to scaffold an EV battery management architecture.
```

### Context

Context files are lightweight grounding assets. Use them when you want to narrow the answer to a specific topic, such as sensor fusion or ISO 26262 overview material. Attach them manually to Copilot Chat as supporting context.

Examples from `.github/copilot/context/CONTEXT-REFERENCE.md`:

```text
Attach .github/copilot/context/skills/adas/sensor-fusion.md, then ask: Explain a late-fusion pipeline for camera-radar perception
Attach .github/copilot/context/skills/autosar/classic-platform.md, then ask: Show a CAN stack configuration strategy
Attach .github/copilot/context/skills/safety/iso-26262-overview.md, then ask: Summarize ASIL decomposition constraints
```

### Knowledge

Knowledge files are deeper reference documents. They are best used as explicit grounding input when you need standards-aligned output, implementation depth, or reference-style detail.

---

## How To Ground Prompts With Knowledge

Knowledge files are not assumed automatically. To use them effectively, add them to the chat as context before asking for output.

In practice, this usually means one of these flows in Copilot Chat:

- Use `Add Context` and attach the file from `.github/copilot/knowledge/...`
- Drag the knowledge markdown file into the chat input
- Reference the exact path in the prompt and explicitly tell Copilot to use it as grounding

### Recommended workflow

1. Pick the right domain persona or workflow surface.
2. Attach one or more knowledge files from `.github/copilot/knowledge/`.
3. Tell Copilot to use those files as grounding.
4. Ask for the deliverable you want.

### Which knowledge depth to use

| File Level | Use Case |
|-----------|----------|
| `1-overview.md` | Quick orientation or terminology |
| `2-conceptual.md` | Design discussions and framework explanations |
| `3-detailed.md` | Implementation guidance and technical analysis |
| `4-reference.md` | Checklist, API, or specification-style answers |
| `5-advanced.md` | Optimization, edge cases, expert patterns |

### Grounded prompt examples

Agent + knowledge:

```text
Select automotive-functional-safety-engineer.
Attach .github/copilot/knowledge/standards/iso26262/3-detailed.md.
Use .github/copilot/knowledge/standards/iso26262/3-detailed.md as grounding.
Generate technical safety requirements for battery over-voltage detection.
```

Agent + context + knowledge:

```text
Select automotive-adas-perception-engineer.
Attach .github/copilot/context/skills/adas/sensor-fusion.md.
Attach .github/copilot/knowledge/standards/iso21448-sotif/2-conceptual.md.
Use both attached files as grounding.
Propose a sensor-fusion validation strategy for poor-weather object detection.
```

Prompt template + knowledge:

```text
Open Attach Context > Prompt and choose validate-asil-compliance.
Attach .github/copilot/knowledge/standards/iso26262/4-reference.md.
Ground the answer with .github/copilot/knowledge/standards/iso26262/4-reference.md.
Review this requirement set for missing ASIL work products.
```

Skill + knowledge:

```text
Use the diagnostics-uds skill/workflow.
Attach .github/copilot/knowledge/standards/autosar-classic/3-detailed.md.
Ground the answer with .github/copilot/knowledge/standards/autosar-classic/3-detailed.md.
Design a UDS 0x22 implementation compatible with AUTOSAR DCM integration.
```

### Good grounding habits

- Attach only the files relevant to the current task.
- Prefer one or two focused knowledge files over attaching a whole category.
- Combine a specialist agent with one deep knowledge file when you need standards-aligned output.
- Use context files for topic framing and knowledge files for authoritative depth.

---

## Domains Covered

| Domain | Agent | What You Get |
|--------|-------|-------------|
| **Functional Safety** | automotive-functional-safety-engineer | HARA, FMEA, FTA, ASIL decomposition, ISO 26262 lifecycle, safety cases |
| **Cybersecurity** | automotive-cybersecurity-engineer | TARA, ISO 21434 compliance, SecOC, secure boot, PKI, intrusion detection |
| **AUTOSAR Architecture** | automotive-autosar-architect | Classic/Adaptive platform design, SWC scaffolding, RTE generation, BSW config |
| **Battery & BMS** | automotive-battery-bms-engineer | SOC/SOH estimation, cell balancing, thermal management, ISO 12405 compliance |
| **ADAS Planning** | automotive-adas-planning-engineer | Path planning, trajectory generation, behavioral prediction, SOTIF analysis |
| **ADAS Control** | automotive-adas-control-engineer | Lateral/longitudinal control, MPC, sensor fusion, perception pipelines |
| **Powertrain** | automotive-powertrain-control-engineer | Engine/transmission control, torque management, emissions compliance |
| **Chassis Systems** | automotive-chassis-systems-engineer | ESC, ABS, EPS, suspension control, vehicle dynamics |
| **Diagnostics** | automotive-diagnostics-engineer | UDS (ISO 14229), OBD-II, DTC management, DoIP, flash programming |

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
  .github/
    copilot-instructions.md    # Workspace-level behavior and discovery guidance
    agents/                    # 15 reusable agent profiles
      automotive-functional-safety-engineer.agent.md
      automotive-cybersecurity-engineer.agent.md
      automotive-autosar-architect.agent.md
      ...
    instructions/              # 15 canonical instruction files
      automotive-functional-safety-engineer.instructions.md
      automotive-cybersecurity-engineer.instructions.md
      automotive-autosar-architect.instructions.md
      ...
    prompts/                   # 3 reusable prompt templates
      validate-asil-compliance.prompt.md
      generate-acc-controller.prompt.md
      create-bms-architecture.prompt.md
    skills/                    # 30 skill packages
      safety-iso-26262-overview/
        SKILL.md
      diagnostics-uds/
        SKILL.md
      ...
    copilot/
      context/                 # 38 attachable context files
        CONTEXT-REFERENCE.md
        adas/
        skills/
      knowledge/               # 117 standards/process/technology docs
        standards/
        processes/
        technologies/
        tools/
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

- **Copies** the template repository's `.github/` content into a target project's `.github/`
- **Never overwrites** existing files with the same content
- **Updates** files that have changed
- **Adds** new files without removing existing ones
- **Tracks** installed components in `.github/copilot/.install.manifest.json`
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
| 1 | GitHub Customization Layout Exists | Error | Verifies required `.github/` structure is present |
| 2 | Manifest File Exists | Warning | Verifies `.install.manifest.json` present |
| 3 | Agent Count | Error | Minimum 5 agents required (15 installed) |
| 4 | Skill/Context Count | Warning | Verifies skill and context assets are present |
| 5 | Knowledge Count | Warning | Verifies knowledge corpus is present |
| 6 | File Integrity | Error | Checks for empty markdown files |
| 7 | Customization Format | Warning | Verifies required sections/frontmatter present |
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
| `.github/` customization files missing | Run `setup.ps1` or `setup.sh` |
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
- [.github/agents/](.github/agents/) - Agent profiles
- [.github/instructions/](.github/instructions/) - Canonical instructions
- [.github/prompts/](.github/prompts/) - Reusable prompt templates
- [.github/skills/](.github/skills/) - Reusable skills
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
