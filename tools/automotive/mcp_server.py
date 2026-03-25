#!/usr/bin/env python3
"""
Automotive MCP Server

Provides Model Context Protocol (MCP) server for automotive development tools
including ADAS perception, AUTOSAR validation, diagnostics, and safety analysis.

Usage:
    python -m automotive.mcp_server

Environment Variables:
    PYTHONPATH: Should include the tools/ directory
"""

import json
import sys
import os
from pathlib import Path
from typing import Any
import hashlib


class AutomotiveMcpServer:
    """MCP server providing automotive tool capabilities."""

    def __init__(self):
        self.workspace_folder = os.environ.get(
            'WORKSPACE_FOLDER',
            str(Path(__file__).parent.parent.parent)
        )
        self.tools_catalog = self._build_tools_catalog()
        self.resources_catalog = self._build_resources_catalog()

    def _build_tools_catalog(self) -> dict:
        """Build the complete tools catalog."""
        return {
            "adas": {
                "perception": {
                    "description": "ADAS perception pipeline tools",
                    "commands": ["perception-pipeline", "perception-test", "perception-eval"]
                },
                "sensor": {
                    "description": "Sensor calibration and fusion",
                    "commands": ["sensor-calibration", "lidar-calibrate", "camera-calibrate", "fusion-validate"]
                },
                "planning": {
                    "description": "Motion planning and scenario testing",
                    "commands": ["scenario-generate", "scenario-replay", "odd-define"]
                }
            },
            "autosar": {
                "classic": {
                    "description": "AUTOSAR Classic Platform tools",
                    "commands": ["swc-generate", "swc-scaffold", "arxml-validate", "rte-check", "bsw-config"]
                },
                "adaptive": {
                    "description": "AUTOSAR Adaptive Platform tools",
                    "commands": ["ecu-extract"]
                }
            },
            "safety": {
                "iso26262": {
                    "description": "ISO 26262 functional safety tools",
                    "commands": ["hara-template", "fmea-generate", "fta-analyze", "asil-decompose", "pmhf-calculate"]
                },
                "sotif": {
                    "description": "ISO 21448 SOTIF tools",
                    "commands": ["sotif-hazard-scenario", "sotif-audit"]
                }
            },
            "security": {
                "iso21434": {
                    "description": "ISO 21434 cybersecurity tools",
                    "commands": ["tara-analyze", "vuln-scan", "crypto-audit", "sbom-generate"]
                },
                "certificates": {
                    "description": "PKI and certificate management",
                    "commands": ["certificate-manage"]
                }
            },
            "diagnostics": {
                "uds": {
                    "description": "UDS diagnostic services",
                    "commands": ["uds-scan", "dtc-read", "ecu-diagnose"]
                },
                "obd": {
                    "description": "OBD-II live data",
                    "commands": ["obd-live-data"]
                },
                "flash": {
                    "description": "ECU flashing and calibration",
                    "commands": ["ecu-flash", "flash-sequence", "calibration-flash"]
                }
            },
            "testing": {
                "hil": {
                    "description": "Hardware-in-the-Loop testing",
                    "commands": ["hil-setup", "hil-launch"]
                },
                "sil": {
                    "description": "Software-in-the-Loop testing",
                    "commands": ["sil-run", "sil-test"]
                },
                "coverage": {
                    "description": "Test coverage analysis",
                    "commands": ["coverage-report", "mcdc-check"]
                }
            },
            "network": {
                "can": {
                    "description": "CAN bus analysis",
                    "commands": ["can-monitor", "network-sim"]
                },
                "ethernet": {
                    "description": "Automotive Ethernet tools",
                    "commands": ["ethernet-diag", "doip-scan", "someip-discover"]
                }
            },
            "battery": {
                "bms": {
                    "description": "Battery Management System tools",
                    "commands": ["soh-estimate", "cell-balance", "thermal-profile", "degradation-predict"]
                },
                "charging": {
                    "description": "Charging simulation and analysis",
                    "commands": ["charging-simulate", "charging-curve", "grid-impact"]
                }
            },
            "compliance": {
                "aspice": {
                    "description": "ASPICE audit tools",
                    "commands": ["aspice-audit"]
                },
                "homologation": {
                    "description": "Regulatory compliance checks",
                    "commands": ["homologation-check", "unr155-assess", "iso26262-checklist", "misra-report"]
                }
            }
        }

    def _build_resources_catalog(self) -> dict:
        """Build the resources catalog."""
        return {
            "standards": {
                "iso26262": {
                    "path": f"{self.workspace_folder}/knowledge-base/standards/iso-26262",
                    "description": "ISO 26262 Functional Safety standard documentation"
                },
                "iso21434": {
                    "path": f"{self.workspace_folder}/knowledge-base/standards/iso-21434",
                    "description": "ISO 21434 Cybersecurity standard documentation"
                },
                "iso21448": {
                    "path": f"{self.workspace_folder}/knowledge-base/standards/iso-21448",
                    "description": "ISO 21448 SOTIF standard documentation"
                },
                "autosar": {
                    "path": f"{self.workspace_folder}/knowledge-base/standards/autosar",
                    "description": "AUTOSAR Classic and Adaptive platform specifications"
                },
                "aspice": {
                    "path": f"{self.workspace_folder}/knowledge-base/standards/aspice",
                    "description": "Automotive SPICE process assessment model"
                }
            },
            "templates": {
                "safety": {
                    "path": f"{self.workspace_folder}/templates/safety",
                    "description": "Safety analysis templates (HARA, FMEA, FTA)"
                },
                "security": {
                    "path": f"{self.workspace_folder}/templates/security",
                    "description": "Security analysis templates (TARA, threat catalog)"
                },
                "autosar": {
                    "path": f"{self.workspace_folder}/templates/autosar",
                    "description": "AUTOSAR SWC and BSW templates"
                }
            }
        }

    def handle_initialize(self, params: dict) -> dict:
        """Handle MCP initialize request."""
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True}
            },
            "serverInfo": {
                "name": "automotive-tools",
                "version": "1.0.0",
                "description": "Automotive development tools MCP server"
            }
        }

    def handle_tools_list(self, params: dict) -> dict:
        """Handle tools/list request."""
        tools = []
        tool_id = 0

        for category, subcategories in self.tools_catalog.items():
            for subcategory, tools_info in subcategories.items():
                for command in tools_info.get("commands", []):
                    tool_id += 1
                    tools.append({
                        "name": f"{category}-{subcategory}-{command}",
                        "description": f"{tools_info['description']} - {command}",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "project_path": {
                                    "type": "string",
                                    "description": "Path to the project directory"
                                },
                                "output_path": {
                                    "type": "string",
                                    "description": "Path for output files"
                                },
                                "options": {
                                    "type": "object",
                                    "description": "Command-specific options"
                                }
                            },
                            "required": ["project_path"]
                        }
                    })

        return {"tools": tools}

    def handle_resources_list(self, params: dict) -> dict:
        """Handle resources/list request."""
        resources = []

        for category, items in self.resources_catalog.items():
            for name, info in items.items():
                resources.append({
                    "uri": f"automotive://{category}/{name}",
                    "name": f"{category}-{name}",
                    "description": info["description"],
                    "mimeType": "text/markdown"
                })

        return {"resources": resources}

    def handle_tool_call(self, name: str, arguments: dict) -> dict:
        """Handle tools/call request."""
        # Parse tool name: category-subcategory-command
        parts = name.split("-", 2)
        if len(parts) != 3:
            return {
                "content": [{"type": "text", "text": f"Invalid tool name format: {name}"}],
                "isError": True
            }

        category, subcategory, command = parts

        # Validate tool exists
        if category not in self.tools_catalog:
            return {
                "content": [{"type": "text", "text": f"Unknown category: {category}"}],
                "isError": True
            }
        if subcategory not in self.tools_catalog[category]:
            return {
                "content": [{"type": "text", "text": f"Unknown subcategory: {subcategory}"}],
                "isError": True
            }
        if command not in self.tools_catalog[category][subcategory].get("commands", []):
            return {
                "content": [{"type": "text", "text": f"Unknown command: {command}"}],
                "isError": True
            }

        # For now, return a stub response
        # In production, this would invoke the actual tool implementation
        project_path = arguments.get("project_path", ".")
        output_path = arguments.get("output_path", "output")

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""Tool invoked successfully: {name}

Category: {category}
Subcategory: {subcategory}
Command: {command}
Project Path: {project_path}
Output Path: {output_path}

This is a stub response. In production, this would execute the actual tool.
To implement the full tool, create a Python module at:
tools/automotive/{category}/{subcategory}/{command.replace('-', '_')}.py
"""
                }
            ],
            "isError": False
        }

    def handle_resource_read(self, uri: str) -> dict:
        """Handle resources/read request."""
        # Parse URI: automotive://category/name
        if not uri.startswith("automotive://"):
            return {
                "contents": [],
                "isError": True
            }

        path = uri.replace("automotive://", "")
        parts = path.split("/", 1)
        if len(parts) != 2:
            return {
                "contents": [],
                "isError": True
            }

        category, name = parts

        if category not in self.resources_catalog:
            return {
                "contents": [],
                "isError": True
            }
        if name not in self.resources_catalog[category]:
            return {
                "contents": [],
                "isError": True
            }

        resource_info = self.resources_catalog[category][name]
        resource_path = resource_info["path"]

        # Try to read the resource file
        try:
            # Look for index.md or README.md in the resource directory
            for filename in ["index.md", "README.md", "overview.md"]:
                file_path = Path(resource_path) / filename
                if file_path.exists():
                    content = file_path.read_text(encoding="utf-8")
                    return {
                        "contents": [
                            {
                                "uri": uri,
                                "mimeType": "text/markdown",
                                "text": content
                            }
                        ]
                    }

            # If no index file found, list directory contents
            if Path(resource_path).exists():
                files = list(Path(resource_path).glob("*.md"))
                content = f"# {resource_info['description']}\n\n"
                content += f"## Available Files\n\n"
                for f in sorted(files):
                    content += f"- {f.name}\n"
                return {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "text/markdown",
                            "text": content
                        }
                    ]
                }

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/markdown",
                        "text": f"# {resource_info['description']}\n\nResource path: {resource_path}\n\nDirectory not found. Create this directory and add documentation files."
                    }
                ]
            }
        except Exception as e:
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/markdown",
                        "text": f"Error reading resource: {str(e)}"
                    }
                ],
                "isError": True
            }

    def process_message(self, message: dict) -> dict:
        """Process an MCP message and return response."""
        method = message.get("method", "")
        params = message.get("params", {})
        msg_id = message.get("id")

        try:
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "tools/list":
                result = self.handle_tools_list(params)
            elif method == "tools/call":
                tool_name = params.get("name", "")
                tool_args = params.get("arguments", {})
                result = self.handle_tool_call(tool_name, tool_args)
            elif method == "resources/list":
                result = self.handle_resources_list(params)
            elif method == "resources/read":
                uri = params.get("uri", "")
                result = self.handle_resource_read(uri)
            elif method == "notifications/initialized":
                # No response needed for notifications
                return None
            else:
                result = {"error": {"code": -32601, "message": f"Method not found: {method}"}}

            if msg_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": result
                }
            return None

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    def run_stdio(self):
        """Run the MCP server using stdio transport."""
        buffer = ""

        for line in sys.stdin:
            buffer += line

            # Process complete messages
            while "\n" in buffer:
                msg_str, buffer = buffer.split("\n", 1)
                if not msg_str.strip():
                    continue

                try:
                    message = json.loads(msg_str)
                    response = self.process_message(message)

                    if response:
                        # Write response to stdout
                        print(json.dumps(response), flush=True)

                except json.JSONDecodeError as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)


def main():
    """Main entry point."""
    server = AutomotiveMcpServer()
    server.run_stdio()


if __name__ == "__main__":
    main()
