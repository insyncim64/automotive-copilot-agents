# FMEA: BMS Overcurrent Protection

## Component-Level Analysis

### Current Sensor (Shunt + Amplifier)

| Failure Mode | Cause | Effect | S | O | D | RPN |
|-------------|-------|--------|---|---|---|-----|
| Under-reporting current | Calibration drift, temperature effect | Overcurrent not detected | 9 | 3 | 4 | 108 |
| Stuck-at-zero output | Open circuit, wire break | No current measurement | 9 | 2 | 3 | 54 |
| Signal noise | EMI, poor grounding | False overcurrent triggers | 5 | 4 | 3 | 60 |
| Offset error | Amplifier drift, aging | Inaccurate current reading | 6 | 3 | 4 | 72 |
| Gain error | Reference voltage drift | Scaled current reading error | 6 | 2 | 4 | 48 |

**Current Controls**:
- Prevention: Temperature-compensated calibration, shielded cables, precision reference
- Detection: Plausibility check (compare with motor controller current), range check (0-5V)

**Recommended Actions**:
- Add redundant current measurement via Hall sensor (ASIL C requirement)
- Implement diagnostic self-test at startup (measures shunt resistance)
- Add EMI filtering on sensor input lines

---

### ADC Converter

| Failure Mode | Cause | Effect | S | O | D | RPN |
|-------------|-------|--------|---|---|---|-----|
| Incorrect conversion | Reference voltage drift | Wrong current reading | 8 | 2 | 4 | 64 |
| Stuck conversion | Clock failure, register corruption | No current update | 9 | 2 | 5 | 90 |
| Missing codes | DAC ladder fault | Non-monotonic response | 7 | 2 | 5 | 70 |
| Channel crosstalk | Multiplexer leakage | Wrong channel reading | 7 | 2 | 4 | 56 |
| Sample-and-hold failure | Capacitor leakage | Inaccurate sampling | 7 | 2 | 5 | 70 |

**Current Controls**:
- Prevention: Precision voltage reference, watchdog monitoring, clean power supply
- Detection: ADC self-test (internal reference), range check on results, CRC on configuration

**Recommended Actions**:
- Use external precision reference (REF3033, 0.1% accuracy)
- Add redundant ADC channel for critical measurements
- Implement continuous background calibration

---

### Safety MCU

| Failure Mode | Cause | Effect | S | O | D | RPN |
|-------------|-------|--------|---|---|---|-----|
| Software hang | Infinite loop, stack overflow | No overcurrent detection | 9 | 2 | 3 | 54 |
| Memory corruption | SEU, aging, EMI | Incorrect threshold comparison | 9 | 3 | 4 | 108 |
| Watchdog failure | Clock drift, WDG config error | No reset on hang | 9 | 2 | 4 | 72 |
| Program counter jump | SEU, EMI | Execute wrong code path | 9 | 2 | 5 | 90 |
| Register corruption | SEU, power glitch | Incorrect PWM output | 8 | 2 | 4 | 64 |
| Clock failure | Oscillator drift, PLL unlock | Timing violation | 9 | 1 | 3 | 27 |

**Current Controls**:
- Prevention: MISRA C compliance, stack monitoring, MPU, ECC on RAM/Flash
- Detection: External watchdog (10ms timeout), lockstep core comparison, CRC on RAM/Flash, program flow monitoring

**Recommended Actions**:
- Enable lockstep core comparison (if available on target MCU)
- Implement redundant computation for critical calculations
- Add periodic self-test of all safety mechanisms

---

### Contactor Driver

| Failure Mode | Cause | Effect | S | O | D | RPN |
|-------------|-------|--------|---|---|---|-----|
| Fails to open | MOSFET short, coil open, driver fault | Contactor remains closed | 9 | 2 | 3 | 54 |
| Spontaneous open | Gate driver fault, EMI, undervoltage | Loss of propulsion | 7 | 2 | 4 | 56 |
| Delayed opening | Gate resistance too high, weak driver | Exceeds FTTI (100ms) | 9 | 2 | 4 | 72 |
| Partial engagement | Contact weld, mechanical binding | High contact resistance, heating | 7 | 2 | 3 | 42 |
| Feedback stuck | Aux contact weld, wire break | Incorrect state indication | 6 | 2 | 4 | 48 |

**Current Controls**:
- Prevention: High-side + low-side driver, flyback diode, conformal coating
- Detection: Contactor feedback (auxiliary contact), coil resistance check at startup, current sense on driver output

**Recommended Actions**:
- Add dual-channel contactor drive (redundant MOSFETs in series)
- Implement contactor weld detection via pre-charge resistor monitoring
- Add periodic contactor exercise (open/close cycle during maintenance)

---

## Interface Failure Modes

### CAN Communication Interface

| Failure Mode | Cause | Effect | S | O | D | RPN |
|-------------|-------|--------|---|---|---|-----|
| Message loss | Bus-off, CRC error | No current data | 8 | 3 | 3 | 72 |
| Message corruption | EMI, ground shift | Wrong current value | 8 | 2 | 4 | 64 |
| Delayed message | Bus overload, priority issue | Stale current data | 7 | 3 | 3 | 63 |
| Counter stuck | Software fault in sender | No update detection | 6 | 2 | 4 | 48 |

**Current Controls**:
- Prevention: CAN FD with improved CRC, shielded twisted pair, proper termination
- Detection: Alive counter (rolling counter), CRC check, timeout monitoring (100ms)

---

### Power Supply Interface

| Failure Mode | Cause | Effect | S | O | D | RPN |
|-------------|-------|--------|---|---|---|-----|
| Undervoltage | Battery low, high load | MCU brownout | 8 | 3 | 3 | 72 |
| Overvoltage | Load dump, regulator fail | Component damage | 8 | 2 | 4 | 64 |
| Voltage ripple | Regulator instability | ADC measurement error | 6 | 3 | 4 | 72 |
| Reverse polarity | Jump start error | Permanent damage | 9 | 1 | 2 | 18 |

**Current Controls**:
- Prevention: TVS diode, reverse polarity protection, bulk capacitance
- Detection: Voltage monitoring (UVLO/OVLO), periodic ADC reference check

---

## Safety Mechanisms Summary

| Mechanism | Fault Coverage | Detection Latency | Diagnostic Type |
|-----------|---------------|-------------------|-----------------|
| Current sensor plausibility | 85% | 10ms | Online, active |
| ADC range + CRC check | 90% | 1ms | Online, passive |
| External watchdog | 95% | 50ms | Online, active |
| Contactor feedback | 99% | 5ms | Online, active |
| Lockstep core comparison | 98% | 1 cycle | Online, continuous |
| ECC on RAM/Flash | 99% | Immediate | Online, continuous |
| Alive counter on CAN | 95% | 100ms | Online, passive |
| Power supply monitoring | 90% | 1ms | Online, continuous |

## Diagnostic Coverage Analysis

| Component | Single-Point Faults | Detected | Coverage % | Latent Faults | Detected | Coverage % |
|-----------|--------------------|----------|------------|-------------|----------|------------|
| Current Sensor | 12 | 11 | 91.7% | 4 | 3 | 75% |
| ADC Converter | 8 | 7 | 87.5% | 3 | 2 | 66.7% |
| Safety MCU | 15 | 14 | 93.3% | 5 | 4 | 80% |
| Contactor Driver | 10 | 9 | 90% | 4 | 3 | 75% |
| **Overall** | **45** | **41** | **91.1%** | **16** | **12** | **75%** |

**ASIL C Requirements** (per ISO 26262-5):
- Single-point fault metric: >= 97% (Current: 91.1% - needs improvement)
- Latent fault metric: >= 80% (Current: 75% - needs improvement)

**Gap Closure Actions**:
1. Add redundant current sensing (Hall effect in parallel with shunt) -> +5% coverage
2. Implement ADC background self-test -> +3% coverage
3. Add dual-channel contactor drive -> +4% coverage
4. Enhanced MCU lockstep with diverse software -> +3% coverage

**Projected coverage after improvements**:
- Single-point fault metric: 91.1% + 15% = 97.6% (meets ASIL C)
- Latent fault metric: 75% + 10% = 85% (meets ASIL C)

---

## FMEA Traceability

| FMEA Entry | Parent HARA | Safety Requirement | Safety Mechanism |
|------------|-------------|-------------------|------------------|
| Current Sensor: Under-reporting | HE-001, HE-003 | SSR-001, SSR-002 | SM-001 (Plausibility) |
| ADC: Stuck conversion | HE-001, HE-003 | SSR-001, SSR-003 | SM-002 (Range+CRC) |
| MCU: Software hang | HE-001, HE-003 | SSR-003 | SM-003 (Watchdog) |
| Contactor: Fails to open | HE-001, HE-003 | SSR-003 | SM-004 (Feedback) |
| CAN: Message loss | HE-001 | SSR-004 | SM-005 (Alive counter) |

---

## References

- ISO 26262-6:2018, Section 8 (Software FMEA)
- ISO 26262-5:2018, Section 9 (Diagnostic coverage metrics)
- AIAG FMEA-4th Edition (Automotive Industry Action Group)
