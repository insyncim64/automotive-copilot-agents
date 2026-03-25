# HARA: BMS Overcurrent Protection

## Item Definition

- **Item**: Battery Management System (BMS)
- **Function**: Overcurrent protection (detect >500A, disconnect within 100ms)
- **Operating Modes**:
  - Normal driving
  - Fast charging (DC)
  - AC charging
  - Regenerative braking
  - Parked/Standby

## Hazardous Events

| ID | Malfunction | Operational Situation | Hazardous Event |
|----|-------------|----------------------|-----------------|
| HE-001 | Fails to detect overcurrent | Highway cruising, hard acceleration | Battery thermal runaway |
| HE-002 | False positive disconnection | High-speed highway driving | Loss of propulsion |
| HE-003 | Delayed disconnection (>100ms) | Short circuit event | Cell damage, fire risk |
| HE-004 | Overcurrent during DC fast charging | Charging station fault | Cell degradation, thermal event |
| HE-005 | Spontaneous contactor open | Normal driving, no fault | Loss of propulsion in traffic |

## Risk Classification

| ID | Severity (S) | Exposure (E) | Controllability (C) | ASIL |
|----|-------------|--------------|---------------------|------|
| HE-001 | S3 (life-threatening) | E3 (occasional) | C3 (difficult) | C |
| HE-002 | S2 (moderate injury) | E2 (low probability) | C2 (normally controllable) | A |
| HE-003 | S3 (life-threatening) | E3 (occasional) | C3 (difficult) | C |
| HE-004 | S3 (life-threatening) | E4 (frequent) | C2 (normally controllable) | B |
| HE-005 | S2 (moderate injury) | E3 (occasional) | C2 (normally controllable) | A |

## Safety Goals

| ID | Safety Goal | ASIL | FTTI |
|----|-------------|------|------|
| SG-001 | Prevent cell overcurrent exceeding design limits | C | 100ms |
| SG-002 | Avoid unintended contactor opening during normal operation | A | 500ms |
| SG-003 | Ensure overcurrent detection within fault tolerant time interval | C | 10ms |
| SG-004 | Maintain safe state after fault detection until explicit reset | C | N/A |

## Safety Requirements (Derived from Safety Goals)

| ID | Safety Requirement | Parent SG | ASIL |
|----|-------------------|-----------|------|
| SSR-001 | The BMS shall measure pack current at minimum 1kHz sampling rate | SG-001 | C |
| SSR-002 | The BMS shall detect pack current exceeding 500A within 10ms | SG-003 | C |
| SSR-003 | The BMS shall command main contactor open within 100ms of overcurrent detection | SG-001 | C |
| SSR-004 | The BMS shall validate current sensor plausibility against motor controller current | SG-001 | B |
| SSR-005 | The BMS shall not command contactor open unless overcurrent confirmed by redundant path | SG-002 | A |
| SSR-006 | The BMS shall store fault code with freeze frame data upon overcurrent event | SG-004 | A |

## Assumptions of Use

1. Main contactor is normally-open (fails safe)
2. Current sensor has independent plausibility check (motor controller)
3. BMS has watchdog monitoring with 10ms timeout
4. System voltage remains within 200V-450V operating range

## References

- ISO 26262-3:2018, Section 5 (HARA methodology)
- ISO 26262-9:2018, Section 5 (ASIL decomposition)
