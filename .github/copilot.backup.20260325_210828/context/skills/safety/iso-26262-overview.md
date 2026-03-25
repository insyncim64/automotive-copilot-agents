# Skill: ISO 26262 Functional Safety Compliance

## When to Activate
- User asks about ISO 26262 compliance or functional safety requirements
- User needs ASIL determination or decomposition guidance
- User requests HARA, FMEA, or FTA analysis support
- User is developing safety cases or verifying safety goals
- User needs safety mechanism implementation patterns

## Standards Compliance
- ISO 26262-1:2018 through ISO 26262-12:2018 (all 12 parts)
- ISO 26262-6: Product development at software level
- ISO 26262-8: Supporting processes (verification, tool qualification)
- ISO 26262-9: ASIL-oriented and safety-oriented analyses
- MISRA C:2012 / MISRA C++:2008 (coding guidelines)
- ASPICE Level 3
- ISO 21448 (SOTIF) integration
- ISO/SAE 21434 (Cybersecurity interface)

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| ASIL levels | QM, A, B, C, D | safety integrity |
| SPFM target (ASIL D) | > 99 | % single-point fault metric |
| LFM target (ASIL D) | > 90 | % latent fault metric |
| PMHF target (ASIL D) | < 10 | FIT (failures in 10⁹ hours) |
| PMHF target (ASIL B/C) | < 100 | FIT |
| Statement coverage (ASIL D) | 100 | % |
| Branch coverage (ASIL D) | 100 | % |
| MC/DC coverage (ASIL D) | 100 | % |
| FTTI | 10-500 | ms (fault tolerant time interval) |

## ASIL Determination

### Severity (S) - Impact of Hazardous Event

| Class | Description | Example |
|-------|-------------|---------|
| S0 | No injuries | Minor annoyance (wiper malfunction) |
| S1 | Light/moderate injuries | Airbag non-deployment in low-speed collision |
| S2 | Severe/life-threatening injuries | Unintended braking at highway speed |
| S3 | Life-threatening/fatal injuries | Total brake failure at highway speed |

### Exposure (E) - Probability of Operational Situation

| Class | Description | Probability | Example |
|-------|-------------|-------------|---------|
| E0 | Incredibly unlikely | < 0.1% of operating time | Test mode only |
| E1 | Very low probability | 0.1% to 1% | Parking maneuvers |
| E2 | Low probability | 1% to 10% | City driving |
| E3 | Medium probability | 10% to 50% | Rural roads |
| E4 | High probability | > 50% | Highway cruising |

### Controllability (C) - Driver's Ability to Avoid Harm

| Class | Description | Driver Action | Example |
|-------|-------------|---------------|---------|
| C0 | Controllable in general | Simple avoidance | Single wiper inoperative |
| C1 | Simply controllable | 99% can avoid | ABS degradation (one wheel) |
| C2 | Normally controllable | 90% can avoid | Power steering assist loss |
| C3 | Difficult/uncontrollable | < 90% can avoid | Total brake failure |

### ASIL Determination Table

```
Severity │  Exposure    Controllability
    S    │  E4 E3 E2 E1 │  C1    C2    C3
─────────┼──────────────┼────────────────────
   S1    │  A  A  QM QM │  QM    QM    A
   S2    │  B  B  A  A  │  A     B     C
   S3    │  C  C  B  B  │  B     C     D
```

Legend:
- **QM**: Quality Management only (no ASIL required)
- **ASIL A**: Lowest safety integrity
- **ASIL B**: Medium-low safety integrity
- **ASIL C**: Medium-high safety integrity
- **ASIL D**: Highest safety integrity

### ASIL Requirements Summary

| Aspect | ASIL QM | ASIL A | ASIL B | ASIL C | ASIL D |
|--------|---------|--------|--------|--------|--------|
| Software Unit Testing | Recommended | + (some coverage) | ++ (branch coverage) | +++ (MC/DC) | +++ (MC/DC + boundary) |
| Static Code Analysis | Optional | + | ++ | +++ | +++ |
| Code Reviews | Basic | + | ++ | +++ | +++ |
| FMEA | Optional | + | ++ | +++ | +++ |
| FTA | Not required | Optional | + | ++ | +++ |
| Hardware Diagnostic Coverage | None | > 60% | > 80% | > 90% | > 99% |
| PMHF Target | N/A | < 1000 FIT | < 100 FIT | < 100 FIT | < 10 FIT |

## V-Model Safety Lifecycle

### Left Side (Decomposition)

```
┌─────────────────────────────────────────────┐
│         Concept Phase (Part 3)              │
│  • Item Definition                          │
│  • HARA → Safety Goals → ASIL               │
│  • Functional Safety Concept                │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    System Design (Part 4)                   │
│  • Technical Safety Concept                 │
│  • System Architecture                      │
│  • Safety Requirements Allocation           │
└────────┬──────────────────┬─────────────────┘
         │                  │
         ▼                  ▼
┌──────────────────┐  ┌──────────────────────┐
│  HW Design       │  │  SW Design           │
│  (Part 5)        │  │  (Part 6)            │
│  • HW Safety Req │  │  • SW Safety Req     │
│  • HW Arch       │  │  • SW Arch           │
│  • HW Design     │  │  • SW Unit Design    │
└────────┬─────────┘  └──────────┬───────────┘
         │                       │
         ▼                       ▼
┌──────────────────┐  ┌──────────────────────┐
│  HW Implement    │  │  SW Implement        │
│  • PCB Design    │  │  • Coding            │
│  • Component     │  │  • Unit Testing      │
└────────┬─────────┘  └──────────┬───────────┘
         │                       │
         └───────────┬───────────┘
                     │
```

### Right Side (Integration & Verification)

```
                     │
                     ▼
┌─────────────────────────────────────────────┐
│    HW/SW Integration (Part 6)               │
│  • Integration Testing                      │
│  • Interface Verification                   │
│  • Safety Mechanism Testing                 │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    System Integration (Part 4)              │
│  • System Testing                           │
│  • Safety Validation                        │
│  • FTTI Verification                        │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│    Vehicle Integration (Part 4)             │
│  • Vehicle-level Testing                    │
│  • Safety Goal Verification                 │
│  • Release for Production                   │
└─────────────────────────────────────────────┘
```

## Safety Goal Development

### Item Definition Template

```yaml
item_name: "Electronic Stability Control (ESC)"
item_id: "ESC-001"
boundaries:
  physical:
    - ECU_ESC_main
    - Wheel_speed_sensors x4
    - Steering_angle_sensor
    - Yaw_rate_sensor
    - Lateral_acceleration_sensor
    - Hydraulic_modulator
  functional:
    - Vehicle_dynamics_control
    - Brake_pressure_modulation
    - Engine_torque_reduction
  interfaces:
    - CAN_powertrain (500 kbps)
    - CAN_chassis (500 kbps)
    - LIN_sensors (19.2 kbps)
    - Brake_pressure_lines (hydraulic)
assumptions:
  - Tire_grip_coefficient > 0.3
  - Sensor_supply_voltage: 5V ± 0.25V
  - Operating_temperature: -40°C to +85°C
  - Vehicle_speed: 0 to 200 km/h
dependencies:
  - ABS_system (provides wheel speed data)
  - Engine_control (accepts torque reduction commands)
  - Brake_system (hydraulic pressure supply)
```

### Safety Goal Template

```yaml
safety_goal_id: "SG-ESC-001"
item: "ESC-001"
hazard: "Unintended ESC activation causing loss of vehicle control"
hazardous_event: "ESC applies asymmetric braking while cornering at highway speed"
asil: "ASIL-D"
asil_derivation:
  severity: "S3"  # Life-threatening
  exposure: "E4"  # Highway driving > 50% of time
  controllability: "C3"  # Difficult to control at high speed
safety_state: "ESC_disabled_safe_mode"
ftti: "150 ms"  # Fault Tolerant Time Interval
safe_state_description: |
  ESC system transitions to disabled state where:
  - No brake pressure modulation occurs
  - Driver has full manual braking control
  - Warning lamp illuminated
  - DTC stored for service
  - Base ABS functionality maintained
verification_criteria:
  - No_unintended_ESC_activation_in_1000_test_runs
  - FTTI_verified_through_fault_injection
  - Safe_state_reached_within_150ms
  - Warning_lamp_activation_confirmed
```

## ASIL Decomposition

### Decomposition Rules

**Valid ASIL-D Decomposition:**
- ASIL-D(D) = ASIL-C(D) + ASIL-A(D)
- ASIL-D(D) = ASIL-B(D) + ASIL-B(D)
- ASIL-D(D) = ASIL-B(D) + ASIL-A(D) [with additional safety mechanisms]

**Requirements:**
1. Elements must be sufficiently independent
2. Both elements monitored for failures
3. Dependent failures analyzed (DFA)
4. Common cause failures addressed
5. No single point of failure

**Example - Brake-by-Wire ASIL-D Decomposition:**

```yaml
safety_requirement: "Brake_command_processing"
original_asil: "ASIL-D(D)"
decomposition:
  element_1:
    function: "Primary_brake_command_path"
    asil: "ASIL-B(D)"
    implementation: "Microcontroller_core_0"
    safety_mechanisms:
      - Program_flow_monitoring
      - RAM_test
      - CRC_on_commands
  element_2:
    function: "Secondary_brake_command_path"
    asil: "ASIL-B(D)"
    implementation: "Microcontroller_core_1"
    safety_mechanisms:
      - Dual_core_lockstep
      - Cross_comparison
      - Watchdog
independence_measures:
  - Separate_memory_partitions
  - Separate_power_supplies
  - Different_code_implementations
  - Independent_watchdogs
dependent_failure_analysis:
  - EMI_susceptibility_analyzed
  - Common_power_rail_protected
  - Temperature_effects_mitigated
```

## Safety Mechanisms and Patterns

### Redundancy Patterns

#### 1oo2 Homogeneous Redundancy (C Code)

```c
typedef struct {
    float value;
    bool valid;
    uint32_t timestamp_us;
} SensorReading_t;

typedef enum {
    VOTER_OK,
    VOTER_MISMATCH,
    VOTER_SINGLE_FAULT
} VoterResult_t;

/* 1oo2 voter with plausibility check */
VoterResult_t voter_1oo2(const SensorReading_t* sensor_a,
                          const SensorReading_t* sensor_b,
                          float tolerance,
                          float* voted_output) {
    if (!sensor_a->valid && !sensor_b->valid) {
        return VOTER_SINGLE_FAULT;  /* Both failed */
    }
    if (!sensor_a->valid) {
        *voted_output = sensor_b->value;
        return VOTER_OK;  /* Use sensor B */
    }
    if (!sensor_b->valid) {
        *voted_output = sensor_a->value;
        return VOTER_OK;  /* Use sensor A */
    }

    /* Both valid - check agreement */
    float diff = fabsf(sensor_a->value - sensor_b->value);
    if (diff <= tolerance) {
        *voted_output = (sensor_a->value + sensor_b->value) / 2.0f;
        return VOTER_OK;
    } else {
        /* Mismatch - enter safe state */
        *voted_output = SAFE_DEFAULT_VALUE;
        return VOTER_MISMATCH;
    }
}
```

#### Dual-Core Lockstep Monitor

```c
/* Primary core executes control algorithm */
/* Monitor core checks results via shared memory */

typedef struct {
    uint32_t sequence;
    float torque_request_nm;
    uint32_t crc32;
    bool valid;
} CoreOutput_t;

/* Monitor core verification */
bool monitor_verify(const CoreOutput_t* primary,
                     const CoreOutput_t* secondary,
                     uint32_t expected_seq) {
    /* Check sequence number */
    if (primary->sequence != expected_seq) {
        return false;
    }

    /* Check CRC */
    uint32_t computed_crc = crc32_compute(
        (const uint8_t*)&primary->sequence,
        sizeof(uint32_t) + sizeof(float));
    if (computed_crc != primary->crc32) {
        return false;
    }

    /* Cross-check with secondary (diverse implementation) */
    float diff = fabsf(primary->torque_request_nm -
                       secondary->torque_request_nm);
    if (diff > TORQUE_TOLERANCE_NM) {
        return false;
    }

    return true;
}
```

### Watchdog Mechanisms

#### Window Watchdog with Timing Constraints

```c
#define WATCHDOG_WINDOW_START_US   500U
#define WATCHDOG_WINDOW_END_US     2000U
#define WATCHDOG_TIMEOUT_US        5000U

typedef struct {
    uint32_t last_service_time_us;
    bool system_ready;
} WatchdogState_t;

bool service_window_watchdog(WatchdogState_t* state,
                              uint32_t current_time_us) {
    /* Check system ready */
    if (!state->system_ready) {
        return false;
    }

    /* Calculate time since last service */
    uint32_t elapsed = current_time_us - state->last_service_time_us;

    /* Too early (before window opens) */
    if (elapsed < WATCHDOG_WINDOW_START_US) {
        report_watchdog_fault(WATCHDOG_FAULT_TOO_EARLY);
        return false;
    }

    /* Too late (after window closes) */
    if (elapsed > WATCHDOG_WINDOW_END_US) {
        report_watchdog_fault(WATCHDOG_FAULT_TOO_LATE);
        return false;
    }

    /* Valid service - update timestamp */
    state->last_service_time_us = current_time_us;
    reset_watchdog_hardware();
    return true;
}
```

### CRC Mechanisms

#### CRC-16-CCITT Calculation

```c
/* CRC-16-CCITT: polynomial 0x1021, init 0xFFFF */
uint16_t crc16_ccitt(const uint8_t* data, size_t length) {
    uint16_t crc = 0xFFFFU;
    const uint16_t polynomial = 0x1021U;

    for (size_t i = 0U; i < length; i++) {
        crc ^= (uint16_t)data[i] << 8U;
        for (uint8_t bit = 0U; bit < 8U; bit++) {
            if ((crc & 0x8000U) != 0U) {
                crc = (crc << 1U) ^ polynomial;
            } else {
                crc = crc << 1U;
            }
        }
    }
    return crc;
}

/* AUTOSAR E2E Profile 1 protection */
typedef struct {
    uint8_t counter;      /* 4-bit rolling counter */
    uint8_t data_id;      /* Message identifier */
    uint8_t crc;          /* CRC-8 SAE J1850 */
} E2E_Protection_t;

uint8_t e2e_compute_crc_profile1(const uint8_t* data,
                                  uint8_t length,
                                  uint8_t data_id,
                                  uint8_t counter) {
    uint8_t crc = 0xFFU;  /* Initial value */
    crc = crc8_update(crc, data_id);
    for (uint8_t i = 0U; i < length; i++) {
        crc = crc8_update(crc, data[i]);
    }
    crc = crc8_update(crc, counter);
    return crc ^ 0xFFU;  /* XOR with final value */
}
```

### Memory Protection

#### Stack Canary Overflow Detection

```c
/* Stack canary pattern (placed between stack and local variables) */
#define STACK_CANARY_VALUE  0xDEADBEEFU
#define CANARY_WORDS        4U

typedef struct {
    uint32_t canary[CANARY_WORDS];
    uint32_t stack_high_water_mark;
} StackProtection_t;

/* Initialize canary at task startup */
void stack_protection_init(StackProtection_t* protection) {
    for (uint8_t i = 0U; i < CANARY_WORDS; i++) {
        protection->canary[i] = STACK_CANARY_VALUE;
    }
    protection->stack_high_water_mark = 0U;
}

/* Check for stack overflow (call periodically) */
bool stack_check_overflow(const StackProtection_t* protection) {
    for (uint8_t i = 0U; i < CANARY_WORDS; i++) {
        if (protection->canary[i] != STACK_CANARY_VALUE) {
            report_stack_overflow(i);
            return true;  /* Overflow detected */
        }
    }
    return false;
}
```

## Hardware Metrics

### Single-Point Fault Metric (SPFM)

```
SPFM = (1 - ΣλSPF / ΣλTotal) × 100%

Target:
- ASIL B: > 90%
- ASIL C: > 97%
- ASIL D: > 99%

Where:
- λSPF = Single-point fault failure rate
- λTotal = Total failure rate
```

### Latent Fault Metric (LFM)

```
LFM = (1 - ΣλLF / (ΣλLF + ΣλRF + ΣλDet)) × 100%

Target:
- ASIL B: > 60%
- ASIL C: > 80%
- ASIL D: > 90%

Where:
- λLF = Latent fault failure rate
- λRF = Residual fault failure rate
- λDet = Detected fault failure rate
```

### Probabilistic Metric for Random Hardware Failures (PMHF)

```
PMHF = Σ(λi × failure_rate) FIT

Target:
- ASIL B: < 100 FIT
- ASIL C: < 100 FIT
- ASIL D: < 10 FIT

FIT = Failures In Time (1 FIT = 1 failure in 10⁹ hours)
```

## FMEA/FTA Analysis

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
  rpn: 108           # S * O * D (Risk Priority Number)

  safety_mechanism: "SM-BMS-003 (Plausibility check with 50 mV threshold)"
  safety_goal_ref: "SG-BMS-001"
```

### FTA Quantitative Analysis (Python)

```python
import math

def fit_to_probability(fit: float, hours: float) -> float:
    """Convert FIT to probability of failure over operating hours."""
    lambda_per_hour = fit / 1e9
    return 1 - math.exp(-lambda_per_hour * hours)

def probability_to_fit(prob: float, hours: float) -> float:
    """Convert probability to FIT."""
    if prob >= 1.0:
        return float('inf')
    lambda_per_hour = -math.log(1 - prob) / hours
    return lambda_per_hour * 1e9

# AND gate: P(A AND B) = P(A) * P(B)
# OR gate: P(A OR B) = P(A) + P(B) - P(A)*P(B)

def and_gate_prob(probabilities: list) -> float:
    """Calculate AND gate output probability."""
    result = 1.0
    for p in probabilities:
        result *= p
    return result

def or_gate_prob(probabilities: list) -> float:
    """Calculate OR gate output probability."""
    result = 0.0
    for p in probabilities:
        result = result + p - (result * p)
    return result

# Example: Unintended braking top event
# Top = (SW_Fault AND HW_Monitor_Fault) OR (Sensor_Fault OR Actuator_Fault)
sw_fault = fit_to_probability(10.0, 10000)  # 10 FIT
hw_monitor = fit_to_probability(1.0, 10000)  # 1 FIT
sensor = fit_to_probability(100.0, 10000)   # 100 FIT
actuator = fit_to_probability(50.0, 10000)  # 50 FIT

and_path = and_gate_prob([sw_fault, hw_monitor])
top_event = or_gate_prob([and_path, sensor, actuator])
print(f"Top event probability: {top_event:.2e}")
```

## Safety Validation

### Validation Methods by ASIL

| Method | ASIL A | ASIL B | ASIL C | ASIL D |
|--------|--------|--------|--------|--------|
| Requirements review | + | ++ | ++ | +++ |
| Design review | + | ++ | +++ | +++ |
| Simulation testing | + | ++ | +++ | +++ |
| Prototype testing | ++ | +++ | +++ | +++ |
| Field testing | ++ | +++ | +++ | +++ |
| Fault injection | Optional | + | ++ | +++ |
| Back-to-back comparison | Optional | + | ++ | +++ |

### Safety Case Structure

```
Safety Case Document
├── 1. Item Definition
│   ├── System boundaries
│   ├── Assumptions
│   └── Dependencies
├── 2. Hazard Analysis (HARA)
│   ├── Hazard identification
│   ├── Risk assessment (S, E, C)
│   └── ASIL determination
├── 3. Safety Goals
│   ├── Safety goal definition
│   ├── Safe state definition
│   └── FTTI specification
├── 4. Functional Safety Concept
│   ├── Functional safety requirements
│   ├── Safety mechanisms
│   └── Requirement allocation
├── 5. Technical Safety Concept
│   ├── Safety architecture
│   ├── Technical safety requirements
│   └── HW/SW allocation
├── 6. Safety Analysis
│   ├── FMEA/FMEDA results
│   ├── FTA results
│   ├── DFA results
│   └── PMHF calculation
├── 7. Verification Evidence
│   ├── Test results
│   ├── Review records
│   └── Analysis reports
├── 8. Validation Evidence
│   ├── Safety goal verification
│   ├── FTTI verification
│   └── Field data
└── 9. Confirmation Measures
    ├── Functional safety audit
    ├── Independent assessment
    └── Confirmation review
```

## Tool Qualification

### Tool Confidence Levels (TCL)

| TCL | Tool Impact | Examples |
|-----|-------------|----------|
| TCL1 | No impact on safety | Documentation editors |
| TCL2 | Can introduce errors | Compilers without verification |
| TCL3 | High risk of undetected errors | Code generators, static analyzers |

### Recommended ASIL-D Qualified Tools

- MATLAB/Simulink (with IEC Certification Kit)
- SCADE Suite (qualified per ISO 26262)
- TargetLink (qualified code generator)
- Polyspace (static analyzer)
- LDRA (unit test + coverage)
- Vector CANoe/CANalyzer (HIL testing)

## Approach

1. **Item Definition and HARA** (Concept Phase)
   - Define system boundaries, interfaces, assumptions
   - Identify hazardous events in operational context
   - Classify severity, exposure, controllability
   - Determine ASIL and derive safety goals

2. **Functional Safety Concept** (System Design)
   - Allocate safety goals to system elements
   - Define safety mechanisms and safe states
   - Specify FTTI for each safety goal
   - Document functional safety requirements

3. **Technical Safety Concept** (HW/SW Design)
   - Decompose ASIL where applicable (with DFA)
   - Allocate requirements to hardware and software
   - Define architectural patterns (redundancy, monitoring)
   - Specify interfaces and resource constraints

4. **Implementation and Verification**
   - Code per MISRA guidelines with safety annotations
   - Unit test with coverage per ASIL (MC/DC for D)
   - Integrate and test safety mechanisms
   - Fault injection to verify fault detection

5. **Safety Validation**
   - Verify safety goals in vehicle context
   - Validate FTTI through testing
   - Compile safety case evidence
   - Independent safety assessment

## Deliverables

- Item definition with boundaries and assumptions
- HARA report with ASIL determination
- Safety goals with FTTI specification
- Functional and technical safety concepts
- FMEA/FTA/FMEDA analysis reports
- Safety case with verification evidence
- Safety manual for integrators

## Related Context
- @context/skills/safety/safety-mechanisms-patterns.md
- @context/skills/safety/fmea-fta-analysis.md
- @context/skills/safety/sotif-development-rules.md
- @context/skills/automotive-safety/asil-decomposition-rules.md
- @context/skills/security/iso-21434-compliance.md
- @context/skills/autosar/classic-platform.md
- @context/skills/testing/structural-coverage-criteria.md

## Tools Required
- Enterprise Architect or similar (HARA, FMEA documentation)
- MATLAB/Simulink (model-based safety analysis)
- Polyspace or QAC (static analysis for MISRA)
- LDRA or VectorCAST (coverage measurement)
- dSPACE or ETAS (HIL fault injection)
- Isograph or ReliaSoft (FTA/FMEDA quantitative analysis)
