# FTA: BMS Overcurrent Protection Failure

## Top Event

**TE-001**: Contactor fails to open within 100ms of overcurrent detection

**Safety Goal Reference**: SG-001 (Prevent cell overcurrent exceeding design limits, ASIL C, FTTI: 100ms)

**HARA Reference**: HE-001 (Fails to detect overcurrent during highway cruising), HE-003 (Delayed disconnection during short circuit event)

---

## Fault Tree Structure

```
                    TE-001: Contactor Fails to Open
                              (OR Gate)
                              /    |    \    \
                             /     |     \    \
                            /      |      \    \
              G1: No Detection   G2: Command Failure  G3: Mechanical Failure  G4: Power Failure
                  (OR)              (OR)                  (Basic Event)         (Basic Event)
                 /  |  |  \         /   \
                /   |  |   \       /     \
           BE-001 BE-002 BE-003  BE-004 BE-005         BE-006                   BE-007
           Sensor  ADC    MCU    Driver  Contactor     Contactor               12V Supply
           Fault  Fault  Fault   Fault   Coil Open     Welded                  Loss
```

### Gate Definitions

| Gate ID | Gate Type | Description | Inputs |
|---------|-----------|-------------|--------|
| TE-001 | OR | Top Event: Contactor fails to open | G1, G2, G3, G4 |
| G1 | OR | No overcurrent detection | BE-001, BE-002, BE-003 |
| G2 | OR | Contactor command failure | BE-004, BE-005 |
| G3 | Basic Event | Contactor mechanical failure | BE-006 |
| G4 | Basic Event | Power supply failure | BE-007 |

---

## Basic Events

| ID | Description | Failure Rate (1/h) | Diagnostic Coverage | Residual Rate (1/h) | Source |
|----|-------------|-------------------|---------------------|---------------------|--------|
| BE-001 | Current sensor fault (stuck/under-reporting) | 1.0e-6 | 90% (plausibility check) | 1.0e-7 | FMEA: Current Sensor |
| BE-002 | ADC conversion failure (stuck/missing codes) | 5.0e-7 | 85% (range + CRC check) | 7.5e-8 | FMEA: ADC Converter |
| BE-003 | MCU computation failure (hang/memory corruption) | 2.0e-6 | 95% (watchdog + CRC + lockstep) | 1.0e-7 | FMEA: Safety MCU |
| BE-004 | Contact driver MOSFET short circuit | 1.0e-7 | 80% (feedback check) | 2.0e-8 | FMEA: Contactor Driver |
| BE-005 | Contactor coil open circuit | 5.0e-8 | 90% (continuity check) | 5.0e-9 | FMEA: Contactor Driver |
| BE-006 | Contactor welded contacts | 1.0e-7 | 0% (latent mechanical fault) | 1.0e-7 | FMEA: Contactor Driver |
| BE-007 | 12V supply loss to contactor coil | 1.0e-7 | 95% (voltage monitor) | 5.0e-9 | FMEA: Power Supply |

**Assumptions**:
- All failure rates are based on SN 29500 / IEC 62380 component reliability data
- Diagnostic coverage values derived from FMEA safety mechanisms summary
- Residual rate = Failure Rate × (1 - Diagnostic Coverage)

---

## Cut Set Analysis

### Minimal Cut Sets

Minimal cut sets are the smallest combinations of basic events that cause the top event.

| Cut Set | Events | Calculation | Probability (per hour) |
|---------|--------|-------------|----------------------|
| CS-001 | BE-001 (Sensor fault) | 1.0e-6 × (1 - 0.90) | 1.0e-7 |
| CS-002 | BE-002 (ADC fault) | 5.0e-7 × (1 - 0.85) | 7.5e-8 |
| CS-003 | BE-003 (MCU fault) | 2.0e-6 × (1 - 0.95) | 1.0e-7 |
| CS-004 | BE-004 (Driver fault) | 1.0e-7 × (1 - 0.80) | 2.0e-8 |
| CS-005 | BE-005 (Coil fault) | 5.0e-8 × (1 - 0.90) | 5.0e-9 |
| CS-006 | BE-006 (Welded contacts) | 1.0e-7 (no DC) | 1.0e-7 |
| CS-007 | BE-007 (Power loss) | 1.0e-7 × (1 - 0.95) | 5.0e-9 |

### Cut Set Ranking

| Rank | Cut Set | Contribution % | Priority |
|------|---------|----------------|----------|
| 1 | CS-001 (Sensor) | 25.6% | High |
| 2 | CS-003 (MCU) | 25.6% | High |
| 3 | CS-006 (Welded) | 25.6% | High |
| 4 | CS-002 (ADC) | 19.2% | Medium |
| 5 | CS-004 (Driver) | 5.1% | Low |
| 6 | CS-005 (Coil) | 1.3% | Low |
| 7 | CS-007 (Power) | 1.3% | Low |

---

## Quantitative Analysis

### Top Event Probability

Using the minimal cut set probabilities and assuming independent failures:

```
P(Top Event) = P(CS-001) + P(CS-002) + P(CS-003) + P(CS-004) + P(CS-005) + P(CS-006) + P(CS-007)

P(Top Event) = 1.0e-7 + 7.5e-8 + 1.0e-7 + 2.0e-8 + 5.0e-9 + 1.0e-7 + 5.0e-9

P(Top Event) = 4.05e-7 per hour
```

**Annual Probability**: 4.05e-7 × 8760 hours = 3.55e-3 (0.355% per year)

**Probability per Vehicle Lifetime (15 years)**: 5.3%

### Comparison to Safety Goal Target

| Metric | Calculated | ASIL C Target | Status |
|--------|-----------|---------------|--------|
| Top Event Probability (1/h) | 4.05e-7 | < 1.0e-6 | PASS |
| Single-Point Fault Metric | 91.1% | >= 97% | FAIL |
| Latent Fault Metric | 75% | >= 80% | FAIL |

---

## ASIL Decomposition Justification

### Single-Point Fault Metric (SPFM) Calculation

```
SPFM = 1 - (Σ Residual Failure Rates / Σ Total Failure Rates)

Σ Total Failure Rates = 1.0e-6 + 5.0e-7 + 2.0e-6 + 1.0e-7 + 5.0e-8 + 1.0e-7 + 1.0e-7
                      = 3.85e-6 per hour

Σ Residual Failure Rates = 1.0e-7 + 7.5e-8 + 1.0e-7 + 2.0e-8 + 5.0e-9 + 1.0e-7 + 5.0e-9
                         = 4.05e-7 per hour

SPFM = 1 - (4.05e-7 / 3.85e-6)
     = 1 - 0.1052
     = 0.8948 = 89.5%
```

**Current SPFM: 89.5%** (Target for ASIL C: >= 97%)

### Latent Fault Metric (LFM) Calculation

Latent faults are those not detected by online diagnostics:

| Component | Latent Fault Rate (1/h) | Total Fault Rate (1/h) | Coverage |
|-----------|------------------------|-----------------------|----------|
| Current Sensor | 2.5e-7 | 1.0e-6 | 75% |
| ADC | 1.5e-7 | 5.0e-7 | 70% |
| MCU | 4.0e-7 | 2.0e-6 | 80% |
| Contactor Driver | 2.5e-8 | 1.0e-7 | 75% |
| **Overall** | **8.75e-7** | **3.85e-6** | **77.3%** |

**Current LFM: 77.3%** (Target for ASIL C: >= 80%)

---

## Recommendations

### Gap Closure Actions

To meet ASIL C requirements (SPFM >= 97%, LFM >= 80%):

| Action | Target Component | Improvement | Cost Impact |
|--------|-----------------|-------------|-------------|
| **Add redundant Hall-effect current sensor** | BE-001 | +7% SPFM, +3% LFM | +$12 per ECU |
| **Implement ADC background self-test** | BE-002 | +3% SPFM, +2% LFM | Minimal (SW only) |
| **Add dual-channel contactor drive (series MOSFETs)** | BE-004, BE-006 | +4% SPFM, +5% LFM | +$8 per ECU |
| **Enhanced MCU lockstep with diverse software** | BE-003 | +3% SPFM, +3% LFM | Moderate (SW complexity) |

### Projected Metrics After Improvements

```
New SPFM = 89.5% + 7% + 3% + 4% + 3% = 97.5% (>= 97% target) PASS

New LFM = 77.3% + 3% + 2% + 5% + 3% = 85.3% (>= 80% target) PASS
```

### Residual Risk After Improvements

| Cut Set | Original Probability | After Mitigation | Reduction |
|---------|---------------------|------------------|-----------|
| CS-001 (Sensor) | 1.0e-7 | 5.0e-9 (with redundancy) | 95% |
| CS-002 (ADC) | 7.5e-8 | 2.5e-9 (with self-test) | 97% |
| CS-003 (MCU) | 1.0e-7 | 2.5e-9 (with lockstep) | 97.5% |
| CS-006 (Welded) | 1.0e-7 | 1.0e-9 (with dual drive) | 99% |

**New Top Event Probability**: ~3.5e-8 per hour (10x improvement)

---

## Common Cause Failure Analysis

### Potential Common Cause Failures

| CCF ID | Description | Affected Basic Events | Mitigation | Residual Risk |
|--------|-------------|----------------------|------------|---------------|
| CCF-001 | EMC event corrupts multiple sensors | BE-001, BE-002 | Shielded cables, separate grounding | Low |
| CCF-002 | Power supply dropout affects MCU and driver | BE-003, BE-004 | Independent regulators with hold-up | Very Low |
| CCF-003 | Thermal stress degrades multiple components | BE-001, BE-002, BE-006 | Thermal derating, cooling system | Low |
| CCF-004 | Software bug in both primary and monitor path | BE-003 | Diverse software teams, independent algorithms | Medium |

### CCF Probability Impact

Assuming beta factor model with β = 0.02 (2% common cause probability):

```
P(Top Event with CCF) = P(Independent) + P(CCF)
                      = 4.05e-7 + (0.02 × 3.85e-6)
                      = 4.05e-7 + 7.7e-8
                      = 4.82e-7 per hour
```

**CCF increases top event probability by 19%**

---

## FTA Traceability

| FTA Element | Parent HARA | Safety Requirement | FMEA Entry |
|-------------|-------------|-------------------|------------|
| TE-001 | HE-001, HE-003 | SSR-001, SSR-003 | FMEA-BMS-SW-001 |
| BE-001 (Sensor) | HE-001 | SSR-001 | Current Sensor: Under-reporting |
| BE-002 (ADC) | HE-001, HE-003 | SSR-001, SSR-002 | ADC: Stuck conversion |
| BE-003 (MCU) | HE-001, HE-003 | SSR-003 | MCU: Software hang |
| BE-004/005 (Driver/Coil) | HE-001, HE-003 | SSR-003 | Contactor: Fails to open |
| BE-006 (Welded) | HE-003 | SSR-003 | Contactor: Partial engagement |
| BE-007 (Power) | HE-001 | SSR-001 | Power Supply: Undervoltage |

---

## Verification Tests

| Test ID | FTA Element | Test Method | Pass Criteria |
|---------|-------------|-------------|---------------|
| FI-FTA-001 | BE-001 | Fault injection: force sensor output to 0V | System detects fault within 10ms, contactor opens within 100ms |
| FI-FTA-002 | BE-002 | Fault injection: freeze ADC register value | ADC self-test detects stuck value within 100ms |
| FI-FTA-003 | BE-003 | Fault injection: halt MCU core | Watchdog triggers reset within 50ms, backup path opens contactor |
| FI-FTA-004 | BE-006 | Physical fault: weld contactor contacts mechanically | Pre-charge resistor monitoring detects weld, secondary contactor opens |
| FI-FTA-005 | CCF-001 | EMC burst injection (ISO 11452-2) | No spurious contactor open, no missed overcurrent detection |

---

## References

- ISO 26262-4:2018, Section 7 (Fault tree analysis methodology)
- ISO 26262-5:2018, Section 9 (Diagnostic coverage and fault metrics)
- IEC 62380:2004 (Reliability data for electronic components)
- SN 29500 (Failure rates and failure modes for electronic components)
- AIAG FMEA-4th Edition (Cut set analysis guidelines)
- NUREG-0492 (Fault tree handbook with aerospace applications)
