# Skill: FMEA (Failure Mode and Effects Analysis)

## Standards Compliance

- ISO 26262 ASIL C/D
- ASPICE Level 3
- AUTOSAR 4.4
- ISO 21434

## Core Competencies

Expert in FMEA methodology for automotive safety systems.

## Key Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| Severity (S) | 1-10 | 10 = catastrophic, 1 = no effect |
| Occurrence (O) | 1-10 | 10 = inevitable, 1 = extremely unlikely |
| Detection (D) | 1-10 | 10 = no detection, 1 = certain detection |
| RPN | 1-1000 | S × O × D (Risk Priority Number) |
| Action threshold | RPN > 100 | Mandatory action plan required |
| Severity threshold | S ≥ 9 | Safety mechanism required regardless of RPN |

## Domain-Specific Content

### FMEA Hierarchy

```
System FMEA (concept phase)
    |
    +-- Hardware FMEA (system/HW design)
    |     |
    |     +-- Component-level failure modes
    |     +-- Interface failure modes
    |
    +-- Software FMEA (SW design)
          |
          +-- Function-level failure modes
          +-- Data flow failure modes
          +-- Interface failure modes
```

### Software FMEA Failure Mode Categories

| Category | Failure Mode | Description |
|----------|-------------|-------------|
| **Value** | Incorrect output | Wrong computation result |
| **Value** | Out of range | Output exceeds valid bounds |
| **Value** | Stuck-at | Output frozen at last valid value |
| **Timing** | Too early | Output produced before expected |
| **Timing** | Too late | Output produced after deadline |
| **Timing** | Never | Output never produced |
| **Sequence** | Wrong order | Operations executed out of sequence |
| **Sequence** | Repeated | Same operation executed multiple times |
| **Sequence** | Skipped | Required operation not executed |
| **Communication** | Lost message | CAN/Ethernet frame not received |
| **Communication** | Corrupted message | Data integrity compromised |
| **Communication** | Delayed message | Frame arrives after deadline |

### FMEA Entry Template

```yaml
fmea_entry:
  id: FMEA-BMS-SW-001
  component: "Cell Voltage Monitor Module"
  function: "Read ADC and compute cell voltages for all 96 cells"

  failure_mode: "Incorrect cell voltage computation"
  failure_cause:
    - "ADC calibration data corrupted in NVM"
    - "Integer overflow in scaling calculation"
    - "Wrong ADC channel mapping after hardware revision"

  local_effect: "Reported cell voltage differs from actual by > 50 mV"
  system_effect: "Over-voltage protection threshold not triggered"
  vehicle_effect: "Cell may exceed safe voltage, risk of thermal event"

  severity: 9        # 1-10 scale (9 = safety-critical)
  occurrence: 4      # 1-10 scale (4 = occasional)
  detection: 3       # 1-10 scale (3 = high detection probability)
  rpn: 108           # S * O * D

  current_controls:
    prevention:
      - "NVM CRC check on calibration data at startup"
      - "Static analysis (MISRA) catches overflow patterns"
    detection:
      - "Runtime plausibility check (cross-check adjacent cells)"
      - "Range check on computed voltage (2.5V - 4.3V per cell)"
```

### FMEA Review Rules

- FMEA must be reviewed at every design change affecting the analyzed function
- RPN above 100 requires mandatory action plan with deadline
- Severity 9-10 items require safety mechanism regardless of RPN
- All failure modes must trace to at least one test case
- FMEA must be updated with field return data quarterly

### Safety Mechanism Coverage

| ASIL | Single-Point Fault Metric | Latent Fault Metric |
|------|--------------------------|---------------------|
| ASIL B | >= 90% | >= 60% |
| ASIL C | >= 97% | >= 80% |
| ASIL D | >= 99% | >= 90% |

## Implementation Approach

1. Analyze requirements against automotive standards
2. Design solution following AUTOSAR patterns
3. Implement with safety and security considerations
4. Validate per ISO 26262 requirements

## Deliverables

- Technical specification
- Implementation (C/C++/Model)
- Test cases and results
- Safety documentation

## Constraints

- ISO 26262 functional safety compliance
- Real-time performance requirements
- Resource constraints (CPU/Memory)
- AUTOSAR architecture adherence

## Required Tools

- MATLAB/Simulink
- Vector CANoe/CANalyzer
- Static analyzer (Polyspace/Klocwork)
- AUTOSAR toolchain

## Metadata

- **Author**: Automotive Claude Code Agents
- **Last Updated**: 2026-03-19
- **Maturity**: Production
- **Complexity**: Intermediate

## Related Context

- @context/skills/safety/iso-26262-overview.md
- @context/skills/safety/asil-decomposition.md
- @context/skills/safety/fta.md
- @context/skills/safety/safety-monitoring.md
