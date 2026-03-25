#!/usr/bin/env node
"use strict";
/**
 * Automotive Knowledge Base MCP Server
 *
 * Provides Model Context Protocol (MCP) server for accessing
 * automotive standards and templates documentation.
 *
 * Usage:
 *   npm run build
 *   node dist/knowledge-server.js
 *
 * Environment Variables:
 *   WORKSPACE_FOLDER: Path to the project root
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const readline = __importStar(require("readline"));
class AutomotiveKnowledgeServer {
    workspaceFolder;
    resourcesCatalog;
    constructor() {
        this.workspaceFolder = process.env.WORKSPACE_FOLDER ||
            path.resolve(__dirname, '..', '..');
        this.resourcesCatalog = this._buildResourcesCatalog();
    }
    _buildResourcesCatalog() {
        const standardsPath = path.join(this.workspaceFolder, 'knowledge-base', 'standards');
        const templatesPath = path.join(this.workspaceFolder, 'knowledge-base', 'templates');
        return {
            standards: {
                iso26262: {
                    uri: 'automotive://standards/iso26262',
                    name: 'standards-iso26262',
                    description: 'ISO 26262 Functional Safety standard documentation',
                    mimeType: 'text/markdown',
                    path: path.join(standardsPath, 'iso-26262')
                },
                iso21434: {
                    uri: 'automotive://standards/iso21434',
                    name: 'standards-iso21434',
                    description: 'ISO 21434 Cybersecurity standard documentation',
                    mimeType: 'text/markdown',
                    path: path.join(standardsPath, 'iso-21434')
                },
                iso21448: {
                    uri: 'automotive://standards/iso21448',
                    name: 'standards-iso21448',
                    description: 'ISO 21448 SOTIF standard documentation',
                    mimeType: 'text/markdown',
                    path: path.join(standardsPath, 'iso-21448')
                },
                autosar: {
                    uri: 'automotive://standards/autosar',
                    name: 'standards-autosar',
                    description: 'AUTOSAR Classic and Adaptive platform specifications',
                    mimeType: 'text/markdown',
                    path: path.join(standardsPath, 'autosar')
                },
                aspice: {
                    uri: 'automotive://standards/aspice',
                    name: 'standards-aspice',
                    description: 'Automotive SPICE process assessment model',
                    mimeType: 'text/markdown',
                    path: path.join(standardsPath, 'aspice')
                }
            },
            templates: {
                safety: {
                    uri: 'automotive://templates/safety',
                    name: 'templates-safety',
                    description: 'Safety analysis templates (HARA, FMEA, FTA)',
                    mimeType: 'text/markdown',
                    path: path.join(templatesPath, 'safety')
                },
                security: {
                    uri: 'automotive://templates/security',
                    name: 'templates-security',
                    description: 'Security analysis templates (TARA, threat catalog)',
                    mimeType: 'text/markdown',
                    path: path.join(templatesPath, 'security')
                },
                autosar: {
                    uri: 'automotive://templates/autosar',
                    name: 'templates-autosar',
                    description: 'AUTOSAR SWC and BSW templates',
                    mimeType: 'text/markdown',
                    path: path.join(templatesPath, 'autosar')
                }
            }
        };
    }
    handleInitialize(_params) {
        return {
            protocolVersion: '2024-11-05',
            capabilities: {
                resources: { subscribe: true, listChanged: true },
                tools: { listChanged: true },
                prompts: { listChanged: true }
            },
            serverInfo: {
                name: 'automotive-knowledge',
                version: '1.0.0',
                description: 'Automotive knowledge base MCP server'
            }
        };
    }
    handleResourcesList(_params) {
        const resources = [];
        for (const [_category, items] of Object.entries(this.resourcesCatalog)) {
            for (const [_name, info] of Object.entries(items)) {
                resources.push({
                    uri: info.uri,
                    name: info.name,
                    description: info.description,
                    mimeType: info.mimeType
                });
            }
        }
        return { resources };
    }
    handleResourceRead(uri) {
        // Parse URI: automotive://category/name
        if (!uri.startsWith('automotive://')) {
            return {
                contents: [],
                isError: true
            };
        }
        const pathPart = uri.replace('automotive://', '');
        const parts = pathPart.split('/', 1);
        if (parts.length < 1) {
            return { contents: [], isError: true };
        }
        const [category, name] = pathPart.split('/');
        if (!this.resourcesCatalog[category] || !this.resourcesCatalog[category][name]) {
            return {
                contents: [],
                isError: true
            };
        }
        const resourceInfo = this.resourcesCatalog[category][name];
        const resourcePath = resourceInfo.path;
        try {
            // Look for index.md or README.md
            for (const filename of ['index.md', 'README.md', 'overview.md']) {
                const filePath = path.join(resourcePath, filename);
                if (fs.existsSync(filePath)) {
                    const content = fs.readFileSync(filePath, 'utf-8');
                    return {
                        contents: [{
                                uri,
                                mimeType: 'text/markdown',
                                text: content
                            }]
                    };
                }
            }
            // List directory contents if no index file
            if (fs.existsSync(resourcePath)) {
                const files = fs.readdirSync(resourcePath)
                    .filter(f => f.endsWith('.md'))
                    .sort();
                let content = `# ${resourceInfo.description}\n\n`;
                content += `## Available Files\n\n`;
                for (const f of files) {
                    content += `- ${f}\n`;
                }
                return {
                    contents: [{
                            uri,
                            mimeType: 'text/markdown',
                            text: content
                        }]
                };
            }
            // Directory doesn't exist yet - provide helpful message
            return {
                contents: [{
                        uri,
                        mimeType: 'text/markdown',
                        text: `# ${resourceInfo.description}\n\nResource path: ${resourcePath}\n\nDirectory not found. Create this directory and add documentation files.`
                    }]
            };
        }
        catch (error) {
            return {
                contents: [{
                        uri,
                        mimeType: 'text/markdown',
                        text: `Error reading resource: ${error instanceof Error ? error.message : String(error)}`
                    }],
                isError: true
            };
        }
    }
    handleToolsList(_params) {
        // Knowledge server provides documentation lookup tools
        return {
            tools: [
                {
                    name: 'search-standards',
                    description: 'Search automotive standards documentation (ISO 26262, ISO 21434, AUTOSAR, ASPICE)',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            query: {
                                type: 'string',
                                description: 'Search query string'
                            },
                            standard: {
                                type: 'string',
                                description: 'Filter by standard (iso26262, iso21434, autosar, aspice)',
                                enum: ['iso26262', 'iso21434', 'iso21448', 'autosar', 'aspice']
                            }
                        },
                        required: ['query']
                    }
                },
                {
                    name: 'get-template',
                    description: 'Retrieve a specific safety or security template',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            templateType: {
                                type: 'string',
                                description: 'Template category',
                                enum: ['hara', 'fmea', 'fta', 'tara', 'autosar-swc']
                            }
                        },
                        required: ['templateType']
                    }
                },
                {
                    name: 'list-resources',
                    description: 'List all available knowledge resources',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            category: {
                                type: 'string',
                                description: 'Filter by category',
                                enum: ['standards', 'templates']
                            }
                        }
                    }
                }
            ]
        };
    }
    handleToolCall(name, args) {
        switch (name) {
            case 'search-standards':
                return this._handleSearchStandards(args);
            case 'get-template':
                return this._handleGetTemplate(args);
            case 'list-resources':
                return this._handleListResources(args);
            default:
                return {
                    content: [{ type: 'text', text: `Unknown tool: ${name}` }],
                    isError: true
                };
        }
    }
    _handleSearchStandards(args) {
        const query = args?.query || '';
        const standard = args?.standard;
        let results = [];
        const standardsToSearch = standard ? [standard] : Object.keys(this.resourcesCatalog.standards);
        for (const std of standardsToSearch) {
            const resourcePath = this.resourcesCatalog.standards[std]?.path;
            if (resourcePath && fs.existsSync(resourcePath)) {
                const mdFiles = fs.readdirSync(resourcePath)
                    .filter(f => f.endsWith('.md'));
                for (const file of mdFiles) {
                    const filePath = path.join(resourcePath, file);
                    const content = fs.readFileSync(filePath, 'utf-8');
                    // Simple keyword search (case-insensitive)
                    if (content.toLowerCase().includes(query.toLowerCase())) {
                        results.push(`Found in ${std}/${file}`);
                    }
                }
            }
        }
        return {
            content: [{
                    type: 'text',
                    text: results.length > 0
                        ? `Search results for "${query}":\n\n${results.join('\n')}`
                        : `No results found for "${query}". Standards directories may be empty.`
                }],
            isError: false
        };
    }
    _handleGetTemplate(args) {
        const templateType = args?.templateType;
        if (!templateType) {
            return {
                content: [{ type: 'text', text: 'Missing required parameter: templateType' }],
                isError: true
            };
        }
        const templatePath = path.join(this.workspaceFolder, 'knowledge-base', 'templates', 'safety', `${templateType}.md`);
        if (fs.existsSync(templatePath)) {
            const content = fs.readFileSync(templatePath, 'utf-8');
            return {
                content: [{ type: 'text', text: content }],
                isError: false
            };
        }
        return {
            content: [{
                    type: 'text',
                    text: `Template '${templateType}' not found. Available templates should be placed in knowledge-base/templates/safety/`
                }],
            isError: false
        };
    }
    _handleListResources(args) {
        const category = args?.category;
        let output = '# Available Knowledge Resources\n\n';
        if (!category || category === 'standards') {
            output += '## Standards\n\n';
            for (const [name, info] of Object.entries(this.resourcesCatalog.standards)) {
                output += `- **${name}**: ${info.description}\n`;
                output += `  Path: ${info.path}\n\n`;
            }
        }
        if (!category || category === 'templates') {
            output += '## Templates\n\n';
            for (const [name, info] of Object.entries(this.resourcesCatalog.templates)) {
                output += `- **${name}**: ${info.description}\n`;
                output += `  Path: ${info.path}\n\n`;
            }
        }
        return {
            content: [{ type: 'text', text: output }],
            isError: false
        };
    }
    processMessage(message) {
        const method = message.method || '';
        const params = message.params || {};
        const id = message.id;
        try {
            let result;
            switch (method) {
                case 'initialize':
                    result = this.handleInitialize(params);
                    break;
                case 'resources/list':
                    result = this.handleResourcesList(params);
                    break;
                case 'resources/read':
                    result = this.handleResourceRead(params.uri || '');
                    break;
                case 'tools/list':
                    result = this.handleToolsList(params);
                    break;
                case 'tools/call':
                    result = this.handleToolCall(params.name || '', params.arguments || {});
                    break;
                case 'notifications/initialized':
                    return null;
                default:
                    result = {
                        error: { code: -32601, message: `Method not found: ${method}` }
                    };
            }
            if (id !== null && id !== undefined) {
                return {
                    jsonrpc: '2.0',
                    id,
                    result
                };
            }
            return null;
        }
        catch (error) {
            return {
                jsonrpc: '2.0',
                id,
                error: {
                    code: -32603,
                    message: `Internal error: ${error instanceof Error ? error.message : String(error)}`
                }
            };
        }
    }
    runStdio() {
        const rl = readline.createInterface({
            input: process.stdin,
            crlfDelay: Infinity
        });
        let buffer = '';
        rl.on('line', (line) => {
            buffer += line + '\n';
            // Process complete messages
            while (buffer.includes('\n')) {
                const [msgStr, ...rest] = buffer.split('\n');
                buffer = rest.join('\n');
                if (!msgStr.trim())
                    continue;
                try {
                    const message = JSON.parse(msgStr);
                    const response = this.processMessage(message);
                    if (response) {
                        console.log(JSON.stringify(response));
                    }
                }
                catch (error) {
                    const errorResponse = {
                        jsonrpc: '2.0',
                        id: null,
                        error: {
                            code: -32700,
                            message: `Parse error: ${error instanceof Error ? error.message : String(error)}`
                        }
                    };
                    console.log(JSON.stringify(errorResponse));
                }
            }
        });
    }
}
// Main entry point
function main() {
    const server = new AutomotiveKnowledgeServer();
    server.runStdio();
}
main();
//# sourceMappingURL=knowledge-server.js.map