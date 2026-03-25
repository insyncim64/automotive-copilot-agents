# BMS Safety Analysis Example

> Complete example demonstrating ISO 26262 functional safety analysis for a Battery Management System (BMS) overcurrent protection function using MCP safety tools.

## Overview

This example project demonstrates how to use the Automotive Copilot Agents MCP servers to perform a complete safety analysis for a Battery Management System (BMS) overcurrent protection function.

### Use Case: BMS Overcurrent Protection

**Function**: Detect pack current exceeding 500A and disconnect the main contactor within 100ms to prevent thermal runaway.

**Safety Goal**: Prevent battery thermal runaway due to overcurrent conditions (ASIL C).

### Tools Used

This example uses the following MCP tools from the `automotive-tools` server:

| Tool | Purpose | ISO 26262 Reference |
|------|---------|---------------------|
| `safety-hara-template` | Generate HARA template | Part 3, Section 5 |
| `safety-fmea-generate` | Create FMEA analysis | Part 6, Section 8 |
| `safety-fta-analyze` | Perform fault tree analysis | Part 4, Section 7 |
| `safety-asil-decompose` | ASIL decomposition | Part 9, Section 5 |

And from the `automotive-knowledge` server:

| Tool | Purpose |
|------|---------|
| `get-template` | Retrieve safety templates (hara, fmea, fta) |
| `search-standards` | Search ISO 26262 documentation |

## Step-by-Step Workflow

### Step 1: Generate HARA Template

The Hazard Analysis and Risk Assessment (HARA) identifies hazardous events and determines ASIL levels.

#### Invoke via GitHub Copilot

```
@workspace Use the safety-hara-template tool to generate a HARA for BMS overcurrent protection
```

#### MCP Tool Invocation

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "safety-hara-template",
    "arguments": {
      "function": "overcurrent_protection",
      "system": "battery_management_system",
      "asil_target": "C"
    }
  }
}
```

#### Expected Output

```markdown
# HARA: BMS Overcurrent Protection

## Item Definition
- **Item**: Battery Management System (BMS)
- **Function**: Overcurrent protection (detect >500A, disconnect within 100ms)
- **Operating Modes**: Normal driving, fast charging, regenerative braking

## Hazardous Events

| ID | Malfunction | Operational Situation | Hazardous Event |
|----|-------------|----------------------|-----------------|
| HE-001 | Fails to detect overcurrent | Highway cruising, hard acceleration | Battery thermal runaway |
| HE-002 | False positive disconnection | High-speed highway driving | Loss of propulsion |
| HE-003 | Delayed disconnection (>100ms) | Short circuit event | Cell damage, fire risk |

## Risk Classification

| ID | Severity (S) | Exposure (E) | Controllability (C) | ASIL |
|----|-------------|--------------|---------------------|------|
| HE-001 | S3 (life-threatening) | E3 (occasional) | C3 (difficult) | C |
| HE-002 | S2 (moderate injury) | E2 (low probability) | C2 (normally controllable) | A |
| HE-003 | S3 (life-threatening) | E3 (occasional) | C3 (difficult) | C |

## Safety Goals

| ID | Safety Goal | ASIL | FTTI |
|----|-------------|------|------|
| SG-001 | Prevent cell overcurrent exceeding design limits | C | 100ms |
| SG-002 | Avoid unintended contactor opening during normal operation | A | 500ms |
```

### Step 2: Generate FMEA

Failure Mode and Effects Analysis (FMEA) identifies potential failure modes at the component level.

#### Invoke via GitHub Copilot

```
@workspace Use the safety-fmea-generate tool to create an FMEA for the BMS overcurrent protection function
```

#### MCP Tool Invocation

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "safety-fmea-generate",
    "arguments": {
      "function": "overcurrent_protection",
      "parent_hara": ["HE-001", "HE-003"],
      "components": ["current_sensor", "adc_converter", "safety_mcu", "contactor_driver"]
    }
  }
}
```

#### Expected Output

```markdown
# FMEA: BMS Overcurrent Protection

## Component-Level Analysis

### Current Sensor (Shunt + Amplifier)

| Failure Mode | Cause | Effect | S | O | D | RPN |
|-------------|-------|--------|---|---|---|-----|
| Under-reporting current | Calibration drift, temperature effect | Overcurrent not detected | 9 | 3 | 4 | 108 |
| Stuck-at-zero output | Open circuit, wire break | No current measurement | 9 | 2 | 3 | 54 |
| Signal noise | EMI, poor grounding | False overcurrent triggers | 5 | 4 | 3 | 60 |

**Current Controls**:
- Prevention: Temperature-compensated calibration, shielded cables
- Detection: Plausibility check (compare with motor controller current)

**Recommended Actions**:
- Add redundant current measurement via Hall sensor
- Implement diagnostic self-test at startup

### ADC Converter

| Failure Mode | Cause | Effect | S | O | D | RPN |
|-------------|-------|--------|---|---|---|-----|
| Incorrect conversion | Reference voltage drift | Wrong current reading | 8 | 2 | 4 | 64 |
| Stuck conversion | Clock failure, register corruption | No current update | 9 | 2 | 5 | 90 |

**Current Controls**:
- Prevention: Precision voltage reference, watchdog monitoring
- Detection: ADC self-test, range check on results

### Safety MCU

| Failure Mode | Cause | Effect | S | O | D | RPN |
|-------------|-------|--------|---|---|---|-----|
| Software hang | Infinite loop, stack overflow | No overcurrent detection | 9 | 2 | 3 | 54 |
| Memory corruption | SEU, aging | Incorrect threshold comparison | 9 | 3 | 4 | 108 |
| Watchdog failure | Clock drift, WDG config error | No reset on hang | 9 | 2 | 4 | 72 |

**Current Controls**:
- Prevention: MISRA C compliance, stack monitoring, MPU
- Detection: External watchdog, lockstep core (if available), CRC on RAM

### Contactor Driver

| Failure Mode | Cause | Effect | S | O | D | RPN |
|-------------|-------|--------|---|---|---|-----|
| Fails to open | MOSFET short, coil open | Contactor remains closed | 9 | 2 | 3 | 54 |
| Spontaneous open | Gate driver fault, EMI | Loss of propulsion | 7 | 2 | 4 | 56 |

**Current Controls**:
- Prevention: High-side + low-side driver, flyback diode
- Detection: Contactor feedback (auxiliary contact), coil resistance check

## Safety Mechanisms Summary

| Mechanism | Fault Coverage | Detection Latency |
|-----------|---------------|-------------------|
| Current sensor plausibility | 85% | 10ms |
| ADC range + CRC check | 90% | 1ms |
| External watchdog | 95% | 50ms |
| Contactor feedback | 99% | 5ms |
```

### Step 3: Perform FTA

Fault Tree Analysis (FTA) provides a top-down view of fault combinations.

#### Invoke via GitHub Copilot

```
@workspace Use the safety-fta-analyze tool to perform a fault tree analysis for BMS overcurrent protection failure
```

#### MCP Tool Invocation

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "safety-fta-analyze",
    "arguments": {
      "top_event": "Overcurrent protection failure - contactor fails to open",
      "branches": ["sensor_failure", "mcu_failure", "driver_failure", "power_failure"],
      "quantitative": true
    }
  }
}
```

#### Expected Output

```markdown
# FTA: BMS Overcurrent Protection Failure

## Top Event
**TE-001**: Contactor fails to open within 100ms of overcurrent detection

## Fault Tree Structure

```
                    TE-001: Contactor Fails to Open
                              (OR Gate)
                              /    |    \
                             /     |     \
                            /      |      \
              G1: No Detection   G2: Command Failure  G3: Mechanical Failure
                  (OR)              (OR)                  (Basic Event)
                 /  |  \           /   \
                /   |   \         /     \
           BE-001 BE-002 BE-003  BE-004 BE-005         BE-006
           Sensor  ADC    MCU    Driver  Contactor     Contactor
           Fault  Fault  Fault   Fault   Coil Open     Welded
```

## Basic Events

| ID | Description | Failure Rate (1/h) | Diagnostic Coverage |
|----|-------------|-------------------|---------------------|
| BE-001 | Current sensor fault | 1.0e-6 | 90% (plausibility) |
| BE-002 | ADC conversion failure | 5.0e-7 | 85% (self-test) |
| BE-003 | MCU computation failure | 2.0e-6 | 95% (watchdog + CRC) |
| BE-004 | Driver MOSFET short | 1.0e-7 | 80% (feedback) |
| BE-005 | Contactor coil open | 5.0e-8 | 90% (continuity check) |
| BE-006 | Contactor welded contacts | 1.0e-7 | 0% (latent) |

## Quantitative Analysis

**Cut Sets** (minimum combinations causing top event):

| Cut Set | Events | Probability (per hour) |
|---------|--------|----------------------|
| CS-001 | BE-001 | 1.0e-7 (after DC) |
| CS-002 | BE-002 | 7.5e-8 (after DC) |
| CS-003 | BE-003 | 1.0e-7 (after DC) |
| CS-004 | BE-004 | 2.0e-8 (after DC) |
| CS-005 | BE-005 | 5.0e-9 (after DC) |
| CS-006 | BE-006 | 1.0e-7 (no DC) |

**Top Event Probability**: 4.45e-7 per hour

**ASIL Decomposition Justification**:
- Single-point fault metric: 97.7% (meets ASIL C requirement of 97%)
- Latent fault metric: 88.9% (meets ASIL C requirement of 80%)

## Recommendations

1. **Add redundant current sensing** (Hall sensor in parallel with shunt)
2. **Implement contactor weld detection** via pre-charge resistor monitoring
3. **Add dual-channel contactor drive** (redundant MOSFETs in series)
```

### Step 4: ASIL Decomposition

Decompose ASIL C requirement into redundant elements with lower ASIL.

#### Invoke via GitHub Copilot

```
@workspace Use the safety-asil-decompose tool to decompose the ASIL C overcurrent protection requirement
```

#### MCP Tool Invocation

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "safety-asil-decompose",
    "arguments": {
      "safety_requirement": "SR-BMS-001: Disconnect battery within 100ms of overcurrent detection",
      "original_asil": "C",
      "decomposition_approach": "redundant_monitor",
      "element1": "software_overcurrent_monitor",
      "element2": "hardware_overcurrent_limiter"
    }
  }
}
```

#### Expected Output

```markdown
# ASIL Decomposition: BMS Overcurrent Protection

## Safety Requirement
**SR-BMS-001**: The BMS shall disconnect the battery within 100ms of detecting overcurrent exceeding 500A.

**Original ASIL**: C

## Decomposition Scheme

```
ASIL C(D) -> ASIL B(C) + ASIL A(C)

Element 1: Software Overcurrent Monitor    [ASIL B(C)]
  - Main MCU (Cortex-R5) runs control loop at 1ms
  - ADC samples current sensor at 10kHz
  - Compares against 500A threshold
  - Commands contactor open via CAN

Element 2: Hardware Overcurrent Limiter    [ASIL A(C)]
  - Analog comparator with dedicated shunt
  - Fixed threshold (hardware-set by resistor divider)
  - Direct GPIO drive to contactor (independent of MCU)
  - No software involvement
```

## Independence Argument

| Aspect | Element 1 (SW) | Element 2 (HW) | Independent? |
|--------|---------------|----------------|--------------|
| Sensor | ADC channel 0 (shunt) | Dedicated comparator (separate shunt) | YES |
| Processor | Main MCU (Cortex-R5) | No processor (pure analog) | YES |
| Power supply | 3.3V digital LDO | 5V analog LDO | YES |
| Communication | CAN bus | N/A (direct GPIO) | YES |
| Software | Yes (C code, MISRA) | None | YES |
| Development team | SW Team A | HW Team B | YES |

## Common Cause Failure Analysis

| CCF Category | Identified Risk | Mitigation | Residual Risk |
|-------------|-----------------|------------|---------------|
| Hardware | Shared 12V battery supply | Independent regulators with separate fuses | Negligible |
| Environmental | EMC event affects both | Separate shielding, different PCB zones | Low |
| Systematic | Both teams use same schematic tool | Independent review, different simulation tools | Low |
| Process | Same safety engineer reviews | Second safety engineer review for HW path | Low |

## Dependent Failure Analysis Reference
**DFA-BMS-001**: See separate DFA report for detailed CCF and cascading failure analysis.

## Verification Plan

| Test | Element | Method | Expected Result |
|------|---------|--------|-----------------|
| FI-SW-001 | SW Monitor | Fault injection: skip overcurrent check | HW path triggers independently |
| FI-HW-001 | HW Limiter | Fault injection: disable comparator | SW path triggers independently |
| CCF-EMC-001 | Both | EMC burst injection (ISO 11452-2) | Both paths immune or safe state |
| TIMING-001 | Both | Measure reaction time from fault to contactor open | <100ms for each path independently |

## Conclusion

The ASIL B(C) + ASIL A(C) decomposition is valid per ISO 26262 Part 9 because:
1. Each element independently satisfies the safety requirement
2. Sufficient independence measures are in place (different sensors, processors, power)
3. Common cause failures are mitigated to acceptable risk levels
4. Dependent failure analysis confirms no single point of failure
```

## Related Standards

Search the ISO 26262 knowledge base for additional guidance:

```
@workspace Search the ISO 26262 standards for HARA methodology guidelines
@workspace Search the ISO 26262 standards for FMEA best practices
@workspace Search the ISO 26262 standards for ASIL decomposition examples
```

## Next Steps

After completing the safety analysis:

1. **Implement safety mechanisms** in code per FMEA recommendations
2. **Create unit tests** for each failure mode detection
3. **Perform fault injection testing** in HIL environment
4. **Update safety manual** with decomposition rationale
5. **Trace to requirements** in your project management tool

## File Structure

```
examples/bms-safety-analysis/
├── README.md                    # This file
├── 01-hara-output.md            # HARA template output
├── 02-fmea-output.md            # FMEA analysis output
├── 03-fta-output.md             # Fault tree analysis output
├── 04-asil-decomposition.md     # ASIL decomposition output
└── mcp-invocations.json         # All MCP tool invocations for automation
```

## References

- [GETTING-STARTED.md](../../GETTING-STARTED.md) - MCP server setup and usage
- ISO 26262-3:2018 - HARA methodology
- ISO 26262-6:2018 - Software FMEA
- ISO 26262-4:2018 - System-level FTA
- ISO 26262-9:2018 - ASIL decomposition
