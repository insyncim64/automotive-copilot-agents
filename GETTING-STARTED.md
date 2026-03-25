# Getting Started with Automotive Copilot Agents

> Quick start guide for setting up and using the Automotive Copilot Agents MCP server infrastructure for GitHub Copilot integration.

## Prerequisites

- **Node.js** >= 18.0.0 (for TypeScript knowledge server)
- **Python** >= 3.9 (for automotive tools server)
- **GitHub Copilot** subscription with agent access
- **Git** for version control

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url> automotive-copilot-agents
cd automotive-copilot-agents
```

### 2. Install Dependencies

#### TypeScript Knowledge Server

```bash
cd knowledge-base
npm install
npm run build
cd ..
```

#### Python Tools Server

The Python server uses standard library modules only - no additional installation required.

### 3. Verify Installation

Test the TypeScript knowledge server:

```bash
cd knowledge-base
node dist/knowledge-server.js
```

You should see the server start and wait for STDIO input (press `Ctrl+C` to exit).

Test the Python tools server:

```bash
cd tools/automotive
python mcp_server.py
```

Same behavior - server waits for STDIO input.

## MCP Server Configuration

The MCP servers are configured in `mcp.json` at the project root:

```json
{
  "servers": {
    "automotive-tools": {
      "command": "python",
      "args": ["-m", "automotive.mcp_server"],
      "cwd": "${workspaceFolder}/tools",
      "description": "Automotive development tools MCP server"
    },
    "automotive-knowledge": {
      "command": "node",
      "args": ["dist/knowledge-server.js"],
      "cwd": "${workspaceFolder}/knowledge-base",
      "description": "Automotive knowledge base MCP server"
    }
  }
}
```

### Available Servers

| Server | Technology | Purpose |
|--------|------------|---------|
| `automotive-tools` | Python 3.9+ | ADAS, AUTOSAR, Diagnostics, Safety, Security tools |
| `automotive-knowledge` | TypeScript/Node.js | ISO 26262, ISO 21434, AUTOSAR, ASPICE documentation |

## Available Tools

### automotive-tools Server

The tools server provides **80+ automotive development commands** across 11 categories:

#### ADAS & Perception
- `adas-perception-pipeline` - Run ADAS perception pipeline
- `adas-perception-test` - Execute perception tests
- `adas-sensor-calibration` - Calibrate sensors (LiDAR, camera, radar)

#### AUTOSAR
- `autosar-swc-generate` - Generate software components
- `autosar-arxml-validate` - Validate ARXML configuration
- `autosar-bsw-config` - Configure basic software

#### Safety (ISO 26262)
- `safety-hara-template` - Generate HARA templates
- `safety-fmea-generate` - Create FMEA analysis
- `safety-fta-analyze` - Perform fault tree analysis
- `safety-asil-decompose` - ASIL decomposition tool

#### Security (ISO 21434)
- `security-tara-analyze` - TARA threat analysis
- `security-vuln-scan` - Vulnerability scanning
- `security-crypto-audit` - Cryptographic audit

#### Diagnostics
- `diagnostics-uds-scan` - UDS diagnostic services
- `diagnostics-dtc-read` - Read diagnostic trouble codes
- `diagnostics-ecu-flash` - ECU firmware flashing

#### Testing
- `testing-hil-setup` - Hardware-in-the-Loop configuration
- `testing-sil-run` - Software-in-the-Loop execution
- `testing-coverage-report` - Test coverage analysis

#### Network
- `network-can-monitor` - CAN bus monitoring
- `network-ethernet-diag` - Automotive Ethernet diagnostics
- `network-someip-discover` - SOME/IP service discovery

#### Battery & EV
- `battery-soh-estimate` - State of Health estimation
- `battery-cell-balance` - Cell balancing control
- `battery-thermal-profile` - Thermal management

#### Compliance
- `compliance-aspice-audit` - ASPICE process audit
- `compliance-homologation-check` - Regulatory compliance

### automotive-knowledge Server

The knowledge server provides access to **8 documentation resources**:

#### Standards (5)
| Resource URI | Description |
|-------------|-------------|
| `automotive://standards/iso26262` | ISO 26262 Functional Safety |
| `automotive://standards/iso21434` | ISO 21434 Cybersecurity |
| `automotive://standards/iso21448` | ISO 21448 SOTIF |
| `automotive://standards/autosar` | AUTOSAR platform specs |
| `automotive://standards/aspice` | Automotive SPICE |

#### Templates (3)
| Resource URI | Description |
|-------------|-------------|
| `automotive://templates/safety` | HARA, FMEA, FTA templates |
| `automotive://templates/security` | TARA, threat catalog |
| `automotive://templates/autosar` | SWC and BSW templates |

#### Available Tools
- `search-standards` - Search across all standards documentation
- `get-template` - Retrieve specific safety/security templates
- `list-resources` - List all available knowledge resources

## Usage with GitHub Copilot

### Invoking Tools via Copilot Chat

Ask Copilot to use specific tools:

```
@workspace Use the safety-fmea-generate tool to create a FMEA for the BMS overcurrent protection function
```

```
@workspace Search the ISO 26262 standards for ASIL decomposition guidelines
```

### Example Workflows

#### 1. Create a Safety Analysis

```
1. Ask Copilot: "Generate a HARA template for battery management system"
2. Copilot invokes: safety-hara-template tool
3. Review generated template in workspace
4. Customize for your specific system
```

#### 2. Validate AUTOSAR Configuration

```
1. Ask Copilot: "Validate my ARXML configuration for the brake controller"
2. Copilot invokes: autosar-arxml-validate tool
3. Review validation report
4. Fix any reported issues
```

#### 3. Search Standards Documentation

```
1. Ask Copilot: "What does ISO 26262 say about software unit testing for ASIL D?"
2. Copilot invokes: search-standards tool with query
3. Review relevant excerpts from standards
4. Apply guidance to your implementation
```

## Project Structure

```
automotive-copilot-agents/
├── knowledge-base/              # TypeScript MCP server
│   ├── src/
│   │   └── knowledge-server.ts  # Main server implementation
│   ├── dist/
│   │   └── knowledge-server.js  # Compiled output
│   ├── standards/               # Standards documentation (to be populated)
│   │   ├── iso-26262/
│   │   ├── iso-21434/
│   │   ├── iso-21448/
│   │   ├── autosar/
│   │   └── aspice/
│   └── templates/               # Template files (to be populated)
│       ├── safety/
│       ├── security/
│       └── autosar/
├── tools/
│   └── automotive/              # Python MCP server
│       ├── __init__.py
│       └── mcp_server.py        # Main server implementation
├── .github/
│   └── copilot/                 # GitHub Copilot configuration (Phase 4)
│       ├── instructions/
│       ├── personas/
│       ├── context/
│       └── knowledge/
├── mcp.json                     # MCP server configuration
├── GETTING-STARTED.md           # This file
└── MIGRATION-PLAN.md            # Migration strategy document
```

## Environment Variables

### WORKSPACE_FOLDER

Both servers support the `WORKSPACE_FOLDER` environment variable to locate resources:

```bash
# Linux/macOS
export WORKSPACE_FOLDER=/path/to/automotive-copilot-agents

# Windows
set WORKSPACE_FOLDER=C:\path\to\automotive-copilot-agents
```

If not set, servers default to the parent directory of the script location.

## Troubleshooting

### TypeScript Server Won't Start

**Error: Cannot find module**
```bash
cd knowledge-base
npm install
npm run build
```

**Error: Permission denied**
```bash
chmod +x dist/knowledge-server.js
```

### Python Server Won't Start

**Error: No module named automotive**
```bash
cd tools
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m automotive.mcp_server
```

### MCP Tools Not Appearing in Copilot

1. Verify `mcp.json` is in the workspace root
2. Check server paths are correct (use absolute paths if needed)
3. Restart Copilot agent
4. Check server logs for startup errors

### Standards Search Returns No Results

The standards directories are initially empty. Populate them with your organization's standards documentation:

```bash
mkdir -p knowledge-base/standards/iso-26262
# Add markdown files with your standards content
```

## Next Steps

1. **Populate Knowledge Base**: Add your organization's standards and templates to the `standards/` and `templates/` directories

2. **Configure GitHub Copilot**: Set up `.github/copilot/` with custom instructions and personas (see Phase 4 in MIGRATION-PLAN.md)

3. **Create Example Projects**: Build example automotive projects demonstrating tool usage

4. **Explore Available Skills**: Review the `skills/` directory for specialized automotive capabilities

5. **Review Safety Rules**: Familiarize yourself with `.claude/rules/` for automotive safety and security coding standards

## Support

For issues or questions:
- Check `MIGRATION-PLAN.md` for overall strategy
- Review server source code in `knowledge-base/src/` and `tools/automotive/`
- Consult ISO 26262, ISO 21434, and AUTOSAR documentation via the knowledge server

## License

MIT License - See LICENSE file for details.
