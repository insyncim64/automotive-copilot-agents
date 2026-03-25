# Getting Started with Automotive Copilot Agents

Quick start guide for setting up and using the automotive-copilot-agents framework for ADAS, AUTOSAR, and cybersecurity development.

## Prerequisites

### Software Requirements

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | MCP server runtime, workflow tools |
| Node.js | 18+ | Knowledge base server |
| Git | 2.40+ | Version control |
| Docker | 24+ | Simulation testing containers |
| CMake | 3.25+ | ECU build system |

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 8 cores | 16 cores |
| RAM | 16 GB | 32 GB |
| GPU | N/A | NVIDIA RTX 4090 (for offline evaluation) |
| Storage | 100 GB SSD | 500 GB NVMe SSD |

### Optional: Self-Hosted Runners

For vehicle integration testing and ECU flashing:

```yaml
# Register self-hosted runner
cd automotive-copilot-agents
./config.sh --url https://github.com/your-org/automotive-copilot-agents \
            --token YOUR_PAT \
            --name vehicle-test-runner \
            --labels self-hosted,vehicle-test,hil-bench
```

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-org/automotive-copilot-agents.git
cd automotive-copilot-agents
```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install MCP server dependencies
pip install -r requirements-mcp.txt

# Install workflow tool dependencies
pip install -r requirements-workflow.txt
```

### 3. Install Node.js Dependencies

```bash
# Install knowledge base server dependencies
cd knowledge-base
npm install
npm run build
cd ..
```

### 4. Configure MCP Servers

The MCP configuration is defined in `mcp.json` at the repository root:

```json
{
  "servers": {
    "automotive-tools": {
      "command": "python",
      "args": ["-m", "automotive.mcp_server"],
      "cwd": "${workspaceFolder}/tools",
      "env": {"PYTHONPATH": "${workspaceFolder}/tools"}
    },
    "automotive-knowledge": {
      "command": "node",
      "args": ["dist/knowledge-server.js"],
      "cwd": "${workspaceFolder}/knowledge-base"
    }
  }
}
```

### 5. Verify Installation

```bash
# Test MCP server startup
python -m automotive.mcp_server --health-check

# Test knowledge server
cd knowledge-base && node dist/knowledge-server.js --health-check
```

## Available Tools

### ADAS Domain

| Tool | Command | Description |
|------|---------|-------------|
| Perception Pipeline | `adas:perception-pipeline` | Run camera/radar perception on input data |
| Perception Evaluation | `adas:perception-eval` | Compute detection/tracking metrics |
| Sensor Calibration | `adas:sensor-calibration` | Calibrate camera/radar extrinsics |
| Scenario Generation | `adas:scenario-generate` | Generate test scenarios (adverse weather, rare objects) |

### AUTOSAR Domain

| Tool | Command | Description |
|------|---------|-------------|
| ARXML Validation | `autosar:arxml-validate` | Validate ARXML against R22-11 schema |
| SWC Generation | `autosar:swc-generate` | Generate SWC stub code from ARXML |
| RTE Configuration | `autosar:rte-check` | Validate RTE generation configuration |
| BSW Configuration | `autosar:bsw-config` | Configure Basic Software modules |

### Safety Domain

| Tool | Command | Description |
|------|---------|-------------|
| ISO 26262 HARA | `safety:hara-analyze` | Hazard Analysis and Risk Assessment |
| FMEA | `safety:fmea-generate` | Failure Mode and Effects Analysis |
| FTA | `safety:fta-generate` | Fault Tree Analysis |
| SOTIF | `safety:sotif-analyze` | Safety of Intended Functionality (ISO 21448) |

### Security Domain

| Tool | Command | Description |
|------|---------|-------------|
| TARA Analysis | `security:tara-analyze` | Threat Analysis and Risk Assessment (ISO 21434) |
| Vulnerability Scan | `security:vuln-scan` | Scan dependencies for CVEs |
| Crypto Audit | `security:crypto-audit` | Audit cryptographic algorithm usage |
| SBOM Generation | `security:sbom-generate` | Software Bill of Materials |
| Certificate Management | `security:certificate-manage` | Manage PKI certificates |

## Running Example Projects

### ADAS Perception Demo

```bash
cd examples/adas-perception-demo

# Run perception pipeline on sample data
python scripts/run-demo.sh --mode local

# Visualize detection results
python scripts/visualize-results.py --input results/offline/

# Trigger GitHub Actions workflow
gh workflow run adas-perception-validation.yaml
```

### AUTOSAR RTE Generation Demo

```bash
cd examples/autosar-swc-demo

# Validate ARXML schema
python scripts/validate-arxml.py \
  --input arxml/ \
  --schema config/autosar/AUTOSAR_R22-11.xsd \
  --output validation-report.json

# Generate RTE
./scripts/generate-rte.sh \
  --input arxml/ \
  --config config/rte/rte-generation-config.yaml \
  --output generated/rte/ \
  --log generation.log

# Trigger GitHub Actions workflow
gh workflow run autosar-rte-generation.yaml
```

### TARA Analysis Demo

```bash
cd examples/tara-analysis-demo

# Run complete TARA workflow
python scripts/run-tara.sh \
  --architecture architecture/ \
  --output security/ \
  --report security/tara-report.md

# Trigger GitHub Actions workflow
gh workflow run security-tara.yaml
```

## GitHub Actions Workflows

### Workflow Overview

| Workflow | Purpose | Trigger |
|----------|---------|---------|
| `adas-perception-validation.yaml` | ADAS perception pipeline validation | Push to develop, PR to main |
| `autosar-rte-generation.yaml` | AUTOSAR RTE generation | Push to develop/release, PR |
| `security-tara.yaml` | Security TARA analysis | Push to main/develop, quarterly review |

### Manual Trigger

```bash
# Trigger workflow manually
gh workflow run <workflow-file.yaml> \
  --ref <branch-name> \
  --field <input-field>=<value>

# Example: Trigger ADAS validation
gh workflow run adas-perception-validation.yaml \
  --ref develop \
  --field model_version=v2.4.0
```

### Workflow Status

```bash
# View workflow runs
gh run list --workflow <workflow-file.yaml>

# View specific run details
gh run view <run-id> --log
```

## Project Structure

```
automotive-copilot-agents/
├── .github/workflows/       # GitHub Actions workflows
│   ├── adas-perception-validation.yaml
│   ├── autosar-rte-generation.yaml
│   └── security-tara.yaml
├── docs/                    # Documentation
│   ├── GETTING-STARTED.md
│   └── AGENT-CATALOG.md
├── examples/                # Example projects
│   ├── adas-perception-demo/
│   ├── autosar-swc-demo/
│   └── tara-analysis-demo/
├── knowledge-base/          # ISO standards, templates
│   ├── standards/
│   └── templates/
├── tools/                   # MCP servers, workflow tools
│   ├── automotive.mcp_server/
│   └── workflow-tools/
└── mcp.json                 # MCP configuration
```

## Configuration Reference

### ADAS Perception Config

```yaml
# config/perception-config.yaml
pipeline:
  input_sources:
    - type: camera
      name: front_camera
      resolution: [1920, 1080]
      fps: 30
    - type: radar
      name: front_radar
      max_range_m: 200
      update_rate_hz: 20

  detection:
    model: models/perception/latest
    confidence_threshold: 0.5
    iou_threshold: 0.45
    max_detections: 100

  safety:
    asil_level: ASIL-B
    latency_budget_ms: 100
```

### AUTOSAR RTE Config

```yaml
# config/rte/rte-generation-config.yaml
rte_generation:
  mode: full
  autosar_version: R22-11
  platform: Classic

  swc_list:
    - name: EngCtrlSwComponentType
      arxml: arxml/software-components/engine-control.arxml

  port_configuration:
    queued_ports:
      - port: RP_VehicleSpeed
        queue_size: 2
        overwrite_oldest: true

  safety_level: ASIL-B
```

### Security Risk Matrix

```yaml
# config/security/risk-matrix.yaml
matrix:
  type: 5x5
  impact_levels:
    1: negligible
    2: minor
    3: moderate
    4: major
    5: catastrophic
  feasibility_levels:
    1: very_high
    2: high
    3: moderate
    4: low
    5: very_low
  treatment_strategy:
    CRITICAL: mitigate_immediately
    HIGH: mitigate_short_term
    MEDIUM: mitigate_long_term
    LOW: accept_or_monitor
```

## Troubleshooting

### Common Issues

#### MCP Server Not Starting

```bash
# Check Python version
python --version  # Must be 3.10+

# Verify dependencies
pip install -r requirements-mcp.txt --upgrade

# Check server health
python -m automotive.mcp_server --health-check
```

#### Workflow Fails on GPU Runner

```bash
# Verify GPU runner availability
gh run list --workflow adas-perception-validation.yaml

# Check CUDA version compatibility
nvidia-smi  # Must support CUDA 11.7+

# Review workflow logs
gh run view <run-id> --log
```

#### ARXML Validation Errors

```bash
# Verify schema version
python scripts/validate-arxml.py \
  --input arxml/ \
  --schema config/autosar/AUTOSAR_R22-11.xsd \
  --output validation-report.json

# Check validation report for specific errors
cat validation-report.json | jq '.errors[]'
```

### Getting Help

- **Documentation**: `docs/` folder for detailed guides
- **Example Projects**: `examples/` for working implementations
- **GitHub Issues**: Report bugs or request features
- **Knowledge Base**: `knowledge-base/standards/` for ISO/AUTOSAR references

## Next Steps

1. **Explore Agent Catalog**: See `docs/AGENT-CATALOG.md` for available agents
2. **Run Example Projects**: Follow demo guides in `examples/` folders
3. **Trigger Workflows**: Use GitHub Actions for automated validation
4. **Customize Tools**: Extend MCP tools for your specific use case
