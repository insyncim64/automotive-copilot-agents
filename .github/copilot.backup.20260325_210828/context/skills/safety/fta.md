# Skill: FTA (Fault Tree Analysis)

## Standards Compliance

- ISO 26262 ASIL C/D
- ASPICE Level 3
- AUTOSAR 4.4
- ISO 21434

## Core Competencies

Expert in FTA methodology for automotive safety systems.

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Top event probability target (ASIL D) | < 1e-8 | Per operating hour |
| Top event probability target (ASIL C) | < 1e-7 | Per operating hour |
| Top event probability target (ASIL B) | < 1e-6 | Per operating hour |
| Minimum cut set | N/A | Smallest combination of basic events causing top event |
| Common cause factor (β) | 0.01 - 0.1 | For dependent failure analysis |

## Domain-Specific Content

### Fault Tree Construction

```
Top Event: "Battery thermal runaway"
(Undesired system-level event linked to safety goal)
           |
     +-----+-----+
     |   OR Gate  |
     +-----+-----+
           |
     +-----+----------+
     |                 |
Cell Over-Voltage   Cell Over-Temperature
     |                 |
+----+----+      +----+----+
| OR Gate |      | OR Gate |
+----+----+      +----+----+
     |                 |
+----+----+      +----+-------+
|         |      |            |
BMS       Charger Cooling    BMS Temp
Failure   Fault  Failure     Mismatch
```

### Gate Types

| Gate | Symbol | Logic |
|------|--------|-------|
| OR | ∪ | Output occurs if ANY input occurs |
| AND | ∩ | Output occurs if ALL inputs occur |
| INHIBIT | Conditional | Output occurs if input occurs AND condition is met |
| VOTING (m-out-of-n) | k/N | Output occurs if m or more of n inputs occur |

### Quantitative Analysis

```yaml
fault_tree:
  top_event:
    id: FT-BMS-001
    description: "Battery thermal runaway"
    target_probability: 1e-8  # per operating hour

  gates:
    - id: G1
      type: OR
      inputs: [BE-001, BE-002]
      description: "Cell over-voltage OR cell over-temperature"

    - id: G2
      type: AND
      inputs: [BE-003, BE-004]
      description: "SW monitor failure AND HW monitor failure"

  basic_events:
    - id: BE-001
      description: "BMS software fails to detect over-voltage"
      failure_rate: 1e-5  # per hour (before safety mechanism)
      safety_mechanism: "SM-BMS-003"
      diagnostic_coverage: 0.99
      residual_rate: 1e-7  # after safety mechanism

    - id: BE-003
      description: "Software overcurrent monitor failure"
      failure_rate: 1e-4
      safety_mechanism: "SM-BMS-005"
      diagnostic_coverage: 0.95
      residual_rate: 5e-6
```

### Calculation Rules

**OR Gate Probability:**
```
P(OR) = 1 - Π(1 - P_i)  for independent events
For small probabilities: P(OR) ≈ Σ P_i
```

**AND Gate Probability:**
```
P(AND) = Π P_i  for independent events
```

**With Safety Mechanisms:**
```
Residual failure rate = Base failure rate × (1 - Diagnostic Coverage)
```

### FTA Rules

- Top event must link directly to a safety goal violation
- Minimum cut sets must be identified and documented
- Common cause failures must be modeled as shared basic events
- Quantitative analysis required for ASIL C and D
- FTA must be consistent with FMEA (same failure modes)
- Updated whenever architecture changes

### Minimum Cut Set Analysis

| Cut Set | Components | Probability | Contribution |
|---------|-----------|-------------|--------------|
| C1 | BE-001, BE-004 | 5e-13 | Primary risk |
| C2 | BE-002, BE-005 | 2e-12 | Secondary risk |
| C3 | BE-003 (single) | 1e-7 | Dominant risk |

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
- @context/skills/safety/fmea.md
- @context/skills/safety/safety-monitoring.md
