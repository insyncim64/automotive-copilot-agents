# Automotive Copilot Knowledge Base Index

> Central index of all available knowledge areas for GitHub Copilot context.

**Last Updated**: 2026-03-23
**Total Files**: 114 markdown files across 4 categories

---

## Category Summary

| Category | Directories | Files | Complete (5-level) |
|----------|-------------|-------|-------------------|
| Standards | 9 | 41 | 8/9 |
| Processes | 5 | 15 | 3/5 |
| Technologies | 11 | 52 | 10/11 |
| Tools | 4 | 6 | 1/4 |

---

## Standards (41 files)

Complete automotive standards documentation with 5-level structure.

### Complete 5-Level Documentation

| Standard | Levels | Description |
|----------|--------|-------------|
| `iso26262/` | 1-5 | Functional safety for road vehicles |
| `autosar-classic/` | 1-5 | AUTOSAR Classic Platform architecture |
| `autosar-adaptive/` | 1-5 | AUTOSAR Adaptive Platform for HPC |
| `iso21434/` | 1-5 | Cybersecurity engineering |
| `iso21448-sotif/` | 1-5 | Safety of the Intended Functionality |
| `aspice/` | 1-5 | Automotive SPICE process assessment |
| `misra/` | 1-5 | MISRA coding guidelines |
| `unr155/` | 1-5 | UN Regulation 155 (CSMS) |

### Incomplete

| Standard | Levels | Missing |
|----------|--------|---------|
| `china-standards/` | - | All levels (placeholder only) |

---

## Processes (15 files)

Development process and workflow documentation.

### Complete 5-Level Documentation

| Process | Levels | Description |
|---------|--------|-------------|
| `ci-cd/` | 1-5 | CI/CD pipeline rules for automotive |
| `code-review/` | 1-5 | Code review guidelines and checklists |
| `fmea/` | 1-5 | FMEA execution guidelines |

### Incomplete (Placeholders)

| Process | Status |
|---------|--------|
| `v-model/` | Empty placeholder |
| `agile-safety/` | Empty placeholder |

---

## Technologies (51 files)

Technical domain knowledge for automotive systems.

### Complete 5-Level Documentation

| Technology | Levels | Description |
|------------|--------|-------------|
| `battery-management/` | 1-5 | BMS architecture and algorithms |
| `sensor-fusion/` | 1-5 | Multi-sensor fusion techniques |
| `autonomous-driving/` | 1-5 | ADAS and automated driving |
| `v2x/` | 1-5 | Vehicle-to-everything communication |
| `ota-updates/` | 1-5 | Over-the-air update systems |
| `hil-testing/` | 1-5 | Hardware-in-the-loop testing |
| `sil-testing/` | 1-5 | Software-in-the-loop testing |
| `digital-twin/` | 1-5 | Digital twin for automotive |
| `ev-charging/` | 1-5 | EV charging infrastructure |
| `yocto/` | 1-5 | Embedded Linux build system |

### Partial

| Technology | Levels | Description |
|------------|--------|-------------|
| `kubernetes/` | 1 | Overview only |
| `yocto/` | 1-5 | Complete 5-level documentation |

---

## Tools (6 files)

Tool-specific documentation and configurations.

### Complete 5-Level Documentation

| Tool | Levels | Description |
|------|--------|-------------|
| `canoe/` | 1-5 | Vector CANoe usage and automation |

### Partial

| Tool | Levels | Description |
|------|--------|-------------|
| `socketcan/` | 1 | Overview only |

### Incomplete (Placeholders)

| Tool | Status |
|------|--------|
| `vector-toolchain/` | Empty placeholder |
| `opensource-alternatives/` | Empty placeholder |

---

## Cross-Reference Links

### By ASIL Relevance

**ASIL D Critical**:
- @knowledge/standards/iso26262/
- @knowledge/standards/misra/
- @knowledge/processes/fmea/
- @knowledge/technologies/battery-management/

**Cybersecurity**:
- @knowledge/standards/iso21434/
- @knowledge/standards/unr155/
- @knowledge/technologies/ota-updates/

**AUTOSAR**:
- @knowledge/standards/autosar-classic/
- @knowledge/standards/autosar-adaptive/

**Testing & Validation**:
- @knowledge/technologies/hil-testing/
- @knowledge/technologies/sil-testing/
- @knowledge/processes/code-review/

---

## Usage Guidelines

### For Copilot Context

Use `@knowledge/` mentions to reference specific areas:

```
@knowledge/standards/iso26262/2-conceptual.md - ASIL decomposition
@knowledge/technologies/battery-management/3-detailed.md - SOC algorithms
@knowledge/processes/ci-cd/1-overview.md - Pipeline setup
```

### Documentation Priority

Per MIGRATION-PLAN.md section 9.3, Level 1-3 docs are prioritized:
- Level 1 (Overview): Quick orientation
- Level 2 (Conceptual): Understanding key concepts
- Level 3 (Detailed): Implementation guidance

Level 4-5 (Reference, Advanced) added based on demand.

---

## Migration Status

**Phase 1 Complete**:
- [x] Directory structure created
- [x] Standards migration (41 files)
- [x] Processes migration (15 files)
- [x] Technologies migration (51 files)
- [x] Tools migration (6 files)
- [x] Knowledge index created

**Pending**:
- [ ] China standards content (regional compliance)
- [ ] V-model process documentation
- [ ] Agile safety integration guides
- [ ] Vector toolchain integration
- [ ] Open source alternatives catalog

---

## Related Files

- [MIGRATION-PLAN.md](../../MIGRATION-PLAN.md) - Full migration strategy
- [GETTING-STARTED.md](../../docs/GETTING-STARTED.md) - Setup guide
- [AGENT-CATALOG.md](../../docs/AGENT-CATALOG.md) - Available agents
