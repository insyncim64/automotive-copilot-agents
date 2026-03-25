# GitHub Copilot Context Reference

Automotive domain skills converted to GitHub Copilot context file format for @-mention support.

## Directory Structure

```
.github/copilot/context/skills/
├── adas/
│   ├── adaptive-cruise-control.md      # ACC algorithm design and longitudinal control
│   ├── object-detection.md             # Camera/LiDAR/radar-based detection
│   └── sensor-fusion.md                # Multi-sensor fusion pipelines
├── autosar/
│   ├── adaptive-platform.md            # AUTOSAR Adaptive development
│   └── classic-platform.md             # AUTOSAR Classic BSW/RTE configuration
├── battery/
│   └── bms.md                          # Battery management systems
├── network/
│   └── can-protocol.md                 # CAN bus communication
├── safety/
│   ├── iso-26262-overview.md           # Functional safety compliance
│   └── safety-mechanisms-patterns.md   # Safety patterns and mechanisms
└── security/
    ├── iso-21434-compliance.md         # Cybersecurity compliance (ISO 21434)
    └── ota-update-security.md          # OTA security patterns
```

## Converted Skills

### ADAS (Advanced Driver Assistance Systems)

| Context File | When to Use |
|--------------|-------------|
| `@adas/adaptive-cruise-control` | ACC algorithm design, longitudinal control (PID/MPC), stop-and-go systems |
| `@adas/object-detection` | Camera/LiDAR/radar detection, CNN architectures, NMS, anchor boxes |
| `@adas/sensor-fusion` | Multi-sensor fusion, Kalman filtering, perception pipelines |

### AUTOSAR

| Context File | When to Use |
|--------------|-------------|
| `@autosar/classic-platform` | AUTOSAR Classic ECU configuration, BSW modules, RTE generation, ARXML |
| `@autosar/adaptive-platform` | AUTOSAR Adaptive services, ara::com, execution management |

### Battery & Powertrain

| Context File | When to Use |
|--------------|-------------|
| `@battery/bms` | Battery management, SOC/SOH estimation, cell balancing, thermal management |

### Functional Safety

| Context File | When to Use |
|--------------|-------------|
| `@safety/iso-26262-overview` | ASIL classification, HARA, FMEA/FTA, safety requirements, ISO 26262 compliance |
| `@safety/safety-mechanisms-patterns` | E2E protection, plausibility checks, watchdogs, safe state design |

### Cybersecurity

| Context File | When to Use |
|--------------|-------------|
| `@security/iso-21434-compliance` | TARA, threat modeling (STRIDE), SecOC, HSM, secure boot, UN R155 CSMS |
| `@security/ota-update-security` | OTA package signing, anti-rollback, secure update workflows |

### Network & Communication

| Context File | When to Use |
|--------------|-------------|
| `@network/can-protocol` | CAN bus analysis, message design, bus load optimization |

## Usage Examples

### Mentioning Context in Chat

```
@autosar/classic-platform How do I configure the CAN stack for a dual-controller setup?

@safety/iso-26262-overview What ASIL level applies to electronic power steering?

@security/iso-21434-compliance Help me perform TARA for the gateway ECU

@adas/sensor-fusion What's the best approach for camera-radar fusion in adverse weather?
```

### Context File Format

Each context file follows this structure:

```markdown
# Skill: <Domain Name>

## When to Activate
- Trigger scenarios for this skill

## Standards Compliance
- Relevant standards and regulations

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| ... | ... | ... |

## Domain-Specific Content
- Architecture diagrams
- Code patterns
- Implementation guides
- Configuration examples

## Related Context
- @context/skills/other-skill.md
- Cross-references to related skills
```

## Maintenance

### Adding New Context Files

1. Create file at `.github/copilot/context/skills/<domain>/<skill>.md`
2. Follow the standard format above
3. Add entry to this CONTEXT-REFERENCE.md
4. Update any related context cross-references

### Review Checklist

- [ ] When to Activate section covers primary use cases
- [ ] Standards Compliance lists all relevant regulations
- [ ] Key Parameters table includes measurable quantities with units
- [ ] Code examples are MISRA-compliant and safety-annotated
- [ ] Related Context references are bidirectional where applicable

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-23 | Initial release: 8 skills converted |
