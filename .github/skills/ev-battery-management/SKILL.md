---
name: ev-battery-management
description: "Use when: Skill: EV Battery Management Systems topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: EV Battery Management Systems

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/ev/battery-management.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate
- User asks about battery management system (BMS) algorithms for EV applications
- User needs to implement SOC (State of Charge) estimation algorithms
- User requests SOH (State of Health) estimation or battery aging models
- User is developing cell balancing strategies (passive/active)
- User needs equivalent circuit model implementations for battery simulation
- User asks about ISO 26262 safety mechanisms for BMS functions
- User requests fault detection and diagnostics for battery systems
- User needs contactor control and precharge sequence implementations
- User asks about insulation monitoring and high-voltage safety

## Standards Compliance
- ISO 26262:2018 (Functional Safety) - ASIL C/D for BMS functions
- ASPICE Level 3 - Model-based development process
- AUTOSAR 4.4 - BMS domain architecture
- ISO 21434:2021 (Cybersecurity) - BMS command authentication
- SAE J1979 - OBD-II battery PIDs
- SAE J2954 - Wireless charging communication
- UN ECE R155 - Cybersecurity management system
- ISO 6469-3 - EV safety specifications (electrical hazards)
- UL 2580 - Battery safety standards
- IEC 62660 - Secondary lithium-ion cell safety

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Cell voltage | 2.0 to 4.5 | V |
| Pack voltage | 200 to 800 | V |
| Cell temperature | -40 to 85 | °C |
| Pack current | -500 to +500 | A |
| State of Charge (SOC) | 0 to 100 | % |
| State of Health (SOH) | 0 to 100 | % |
| State of Power (SOP) | 0 to 500 | kW |
| Cell balance threshold | 1 to 50 | mV |
| Insulation resistance | 0 to 10000 | kΩ |
| Contact resistance | 0 to 100 | mΩ |

## BMS Architecture

```
+----------------------------------------------------------+
|              Battery Management Controller                |
|  +------------------+  +------------------+              |
|  |  SOC Estimator   |  |  SOH Estimator   |             |
|  +------------------+  +------------------+              |
|           |                     |                        |
|  +------------------+  +------------------+              |
|  |  Cell Balancer   |  |  Fault Manager   |             |
|  +------------------+  +------------------+              |
+--------------------------|-------------------------------+
                           |
         +-----------------+-----------------+
         |                 |                 |
+--------v--------+ +------v------+ +--------v--------+
|  Cell Monitor   | | Contactor   | | Insulation      |
|  (AFE/ADC)      | | Controller  | | Monitor         |
+-----------------+ +-------------+ +-----------------+
```

## SOC Estimation

### Coulomb Counting Method

```c
/* Coulomb counting SOC estimation with compensation */
typedef struct {
    float soc_percent;
    float current_a;
    float capacity_ah;
    float coulombic_efficiency;
    float self_discharge_rate;
    float temperature_c;
    uint32_t last_update_ms;
    bool initialized;
} CoulombCountingSoc_t;

typedef struct {
    float nominal_capacity_ah;
    float max_capacity_ah;
    float min_capacity_ah;
    float temperature_coeffs[5];  /* Capacity vs temp */
    float rate_coeffs[5];         /* Capacity vs C-rate */
} BatteryCharacteristics_t;

/* Initialize SOC estimator */
void soc_coulomb_init(CoulombCountingSoc_t* estimator,
                       float initial_soc,
                       const BatteryCharacteristics_t* characteristics) {
    estimator->soc_percent = fmaxf(0.0f, fminf(100.0f, initial_soc));
    estimator->current_a = 0.0f;
    estimator->capacity_ah = characteristics->nominal_capacity_ah;
    estimator->coulombic_efficiency = 0.99f;  /* 99% efficiency */
    estimator->self_discharge_rate = 0.0001f;  /* per hour */
    estimator->temperature_c = 25.0f;
    estimator->last_update_ms = 0U;
    estimator->initialized = true;
}

/* Update SOC using coulomb counting */
float soc_coulomb_update(CoulombCountingSoc_t* estimator,
                          float current_a,
                          float temperature_c,
                          uint32_t current_time_ms) {

    if (!estimator->initialized) {
        return estimator->soc_percent;
    }

    /* Calculate time delta */
    float dt_hours;
    if (estimator->last_update_ms > 0U) {
        dt_hours = (current_time_ms - estimator->last_update_ms) / 3600000.0f;
    } else {
        dt_hours = 0.001f;  /* Default 1 second */
    }
    estimator->last_update_ms = current_time_ms;

    /* Apply temperature compensation to capacity */
    float temp_factor = 1.0f + 0.005f * (temperature_c - 25.0f);
    float effective_capacity = estimator->capacity_ah * temp_factor;

    /* Calculate charge transferred */
    float charge_ah = current_a * dt_hours;

    /* Apply coulombic efficiency for charging */
    if (current_a > 0.0f) {
        charge_ah *= estimator->coulombic_efficiency;
    }

    /* Update SOC */
    float delta_soc = (charge_ah / effective_capacity) * 100.0f;
    estimator->soc_percent += delta_soc;

    /* Apply self-discharge (small correction) */
    float self_discharge = estimator->self_discharge_rate * dt_hours * 100.0f;
    estimator->soc_percent -= self_discharge;

    /* Clamp to valid range */
    estimator->soc_percent = fmaxf(0.0f, fminf(100.0f, estimator->soc_percent));

    /* Store current for next iteration */
    estimator->current_a = current_a;
    estimator->temperature_c = temperature_c;

    return estimator->soc_percent;
}
```

### Extended Kalman Filter (EKF) SOC Estimation

```c
/* EKF-based SOC estimation using equivalent circuit model */
typedef struct {
    /* States: [SOC, V1, V2] for 2RC model */
    float x[3];       /* State vector */
    float P[3][3];    /* Error covariance matrix */
    float Q[3][3];    /* Process noise covariance */
    float R;          /* Measurement noise covariance */

    /* Battery parameters */
    float capacity_ah;
    float r0;         /* Ohmic resistance */
    float r1;         /* RC pair 1 resistance */
    float c1;         /* RC pair 1 capacitance */
    float r2;         /* RC pair 2 resistance */
    float c2;         /* RC pair 2 capacitance */

    /* OCV-SOC lookup table */
    float ocv_table[11];  /* OCV at 0%, 10%, ..., 100% */

    /* State */
    float soc_estimate;
    float voltage_estimate;
    bool initialized;
} EfkSocEstimator_t;

/* Initialize EKF SOC estimator */
void ekf_soc_init(EfkSocEstimator_t* ekf,
                   const BatteryCharacteristics_t* characteristics) {

    /* Initialize states */
    ekf->x[0] = 50.0f;  /* Initial SOC guess */
    ekf->x[1] = 0.0f;   /* V1 = 0 */
    ekf->x[2] = 0.0f;   /* V2 = 0 */

    /* Initialize covariance */
    ekf->P[0][0] = 100.0f;  /* High uncertainty in SOC */
    ekf->P[1][1] = 1.0f;
    ekf->P[2][2] = 1.0f;
    /* Off-diagonal = 0 */
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            if (i != j) ekf->P[i][j] = 0.0f;
        }
    }

    /* Process noise (tunable) */
    ekf->Q[0][0] = 0.0001f;  /* SOC process noise */
    ekf->Q[1][1] = 0.001f;   /* V1 process noise */
    ekf->Q[2][2] = 0.001f;   /* V2 process noise */

    /* Measurement noise (voltage measurement variance) */
    ekf->R = 0.01f;

    /* Battery parameters */
    ekf->capacity_ah = characteristics->nominal_capacity_ah;
    ekf->r0 = 0.002f;  /* 2 milliohms */
    ekf->r1 = 0.001f;
    ekf->c1 = 10000.0f;
    ekf->r2 = 0.0005f;
    ekf->c2 = 1000.0f;

    /* OCV-SOC table (example for NMC chemistry) */
    float ocv_init[11] = {3.0f, 3.5f, 3.6f, 3.7f, 3.75f, 3.8f,
                          3.85f, 3.9f, 4.0f, 4.1f, 4.2f};
    memcpy(ekf->ocv_table, ocv_init, sizeof(ocv_init));

    ekf->initialized = true;
}

/* Lookup OCV from SOC using linear interpolation */
float ekf_lookup_ocv(const EfkSocEstimator_t* ekf, float soc) {
    /* Convert SOC to index (0-10) */
    float index = soc / 10.0f;
    int idx_low = (int)index;
    int idx_high = idx_low + 1;

    /* Boundary checks */
    if (idx_low < 0) { idx_low = 0; idx_high = 1; }
    if (idx_high > 10) { idx_low = 9; idx_high = 10; }

    /* Linear interpolation */
    float frac = index - idx_low;
    return ekf->ocv_table[idx_low] +
           frac * (ekf->ocv_table[idx_high] - ekf->ocv_table[idx_low]);
}

/* EKF predict and update cycle */
float ekf_soc_update(EfkSocEstimator_t* ekf,
                      float current_a,
                      float measured_voltage_v,
                      float dt) {

    if (!ekf->initialized) {
        return ekf->soc_estimate;
    }

    /* ===== PREDICT STEP ===== */

    /* State transition (discrete time) */
    float soc = ekf->x[0];
    float v1 = ekf->x[1];
    float v2 = ekf->x[2];

    /* SOC dynamics: SOC(k) = SOC(k-1) - (I * dt) / (3600 * Q) */
    float soc_new = soc - (current_a * dt) / (3600.0f * ekf->capacity_ah);
    soc_new = fmaxf(0.0f, fminf(100.0f, soc_new));

    /* V1 dynamics: V1(k) = V1(k-1)*exp(-dt/R1C1) + I*R1*(1-exp(-dt/R1C1)) */
    float tau1 = ekf->r1 * ekf->c1;
    float exp1 = expf(-dt / tau1);
    float v1_new = v1 * exp1 + current_a * ekf->r1 * (1.0f - exp1);

    /* V2 dynamics */
    float tau2 = ekf->r2 * ekf->c2;
    float exp2 = expf(-dt / tau2);
    float v2_new = v2 * exp2 + current_a * ekf->r2 * (1.0f - exp2);

    /* Update state vector */
    ekf->x[0] = soc_new;
    ekf->x[1] = v1_new;
    ekf->x[2] = v2_new;

    /* State transition matrix A (Jacobian) */
    float A[3][3] = {
        {1.0f, 0.0f, 0.0f},
        {0.0f, exp1, 0.0f},
        {0.0f, 0.0f, exp2}
    };

    /* Predicted covariance: P = A * P * A' + Q */
    float P_pred[3][3];
    matrix_multiply_3x3(A, ekf->P, P_pred);
    float P_temp[3][3];
    matrix_transpose_3x3(A, P_temp);
    matrix_multiply_3x3(P_pred, P_temp, P_pred);

    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            ekf->P[i][j] = P_pred[i][j] + ekf->Q[i][j];
        }
    }

    /* ===== UPDATE STEP ===== */

    /* Measurement model: V = OCV(SOC) - I*R0 - V1 - V2 */
    float ocv = ekf_lookup_ocv(ekf, soc_new);
    float voltage_pred = ocv - current_a * ekf->r0 - v1_new - v2_new;

    /* Innovation (measurement residual) */
    float innovation = measured_voltage_v - voltage_pred;

    /* Observation matrix H (Jacobian of h(x)) */
    float dOCV_dSOC = compute_ocv_slope(ekf, soc_new);
    float H[3] = {-dOCV_dSOC, -1.0f, -1.0f};

    /* Innovation covariance: S = H * P * H' + R */
    float S = ekf->R;
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            S += H[i] * ekf->P[i][j] * H[j];
        }
    }

    /* Kalman gain: K = P * H' / S */
    float K[3];
    for (int i = 0; i < 3; i++) {
        K[i] = 0.0f;
        for (int j = 0; j < 3; j++) {
            K[i] += ekf->P[i][j] * H[j];
        }
        K[i] /= S;
    }

    /* Update state: x = x + K * innovation */
    for (int i = 0; i < 3; i++) {
        ekf->x[i] += K[i] * innovation;
    }

    /* Update covariance: P = (I - K*H) * P */
    float KH[3][3];
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            KH[i][j] = K[i] * H[j];
        }
    }

    float I_KH[3][3];
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            I_KH[i][j] = (i == j) ? 1.0f : 0.0f;
            I_KH[i][j] -= KH[i][j];
        }
    }

    matrix_multiply_3x3(I_KH, ekf->P, ekf->P);

    /* Store estimates */
    ekf->soc_estimate = fmaxf(0.0f, fminf(100.0f, ekf->x[0]));
    ekf->voltage_estimate = voltage_pred;

    return ekf->soc_estimate;
}

/* Matrix operations for 3x3 matrices */
void matrix_multiply_3x3(const float A[3][3], const float B[3][3],
                          float C[3][3]) {
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            C[i][j] = 0.0f;
            for (int k = 0; k < 3; k++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
}

void matrix_transpose_3x3(const float A[3][3], float AT[3][3]) {
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            AT[i][j] = A[j][i];
        }
    }
}

float compute_ocv_slope(const EfkSocEstimator_t* ekf, float soc) {
    /* Numerical derivative of OCV-SOC curve */
    float delta = 1.0f;
    float ocv1 = ekf_lookup_ocv(ekf, soc - delta);
    float ocv2 = ekf_lookup_ocv(ekf, soc + delta);
    return (ocv2 - ocv1) / (2.0f * delta);
}
```

### OCV-SOC Lookup Table Method

```c
/* OCV-SOC relationship for battery characterization */
typedef struct {
    float soc_points[21];    /* SOC: 0%, 5%, 10%, ..., 100% */
    float ocv_charge[21];    /* OCV during charging */
    float ocv_discharge[21]; /* OCV during discharging */
    float hysteresis_factor;
} OcvSocLookupTable_t;

/* Initialize OCV-SOC table from characterization data */
void ocv_table_init(OcvSocLookupTable_t* table) {
    /* Example data for NMC 811 chemistry */
    const float soc_init[21] = {0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50,
                                55, 60, 65, 70, 75, 80, 85, 90, 95, 100};
    const float ocv_charge_init[21] = {3.0f, 3.45f, 3.55f, 3.62f, 3.68f, 3.72f,
                                       3.76f, 3.79f, 3.82f, 3.85f, 3.87f,
                                       3.89f, 3.91f, 3.94f, 3.97f, 4.01f,
                                       4.05f, 4.10f, 4.15f, 4.20f, 4.25f};

    memcpy(table->soc_points, soc_init, sizeof(soc_init));
    memcpy(table->ocv_charge, ocv_charge_init, sizeof(ocv_charge_init));

    /* Discharge OCV typically slightly lower due to hysteresis */
    for (int i = 0; i < 21; i++) {
        table->ocv_discharge[i] = ocv_charge_init[i] - 0.015f;
    }

    table->hysteresis_factor = 0.5f;  /* Blend charge/discharge curves */
}

/* Get SOC from OCV measurement */
float ocv_to_soc(const OcvSocLookupTable_t* table,
                  float ocv_measured,
                  bool charging) {

    const float* ocv_array = charging ? table->ocv_charge : table->ocv_discharge;

    /* Find bracketing indices */
    for (int i = 0; i < 20; i++) {
        if (ocv_measured >= ocv_array[i] &&
            ocv_measured <= ocv_array[i+1]) {

            /* Linear interpolation */
            float ratio = (ocv_measured - ocv_array[i]) /
                         (ocv_array[i+1] - ocv_array[i]);
            return table->soc_points[i] +
                   ratio * (table->soc_points[i+1] - table->soc_points[i]);
        }
    }

    /* Extrapolation for out-of-range values */
    if (ocv_measured < ocv_array[0]) {
        return 0.0f;
    }
    return 100.0f;
}
```

## SOH Estimation

### Capacity Fade SOH

```c
/* SOH estimation based on capacity fade */
typedef struct {
    float nominal_capacity_ah;
    float current_capacity_ah;
    float cycle_count;
    float total_energy_throughput_kwh;
    float avg_temperature_c;
    uint32_t last_calibration_soc;
    float last_calibration_voltage;
    bool calibration_valid;
} CapacityFadeSoh_t;

typedef struct {
    float nominal_capacity_ah;
    float end_of_life_capacity_ah;  /* Typically 80% of nominal */
    float cycles_to_eol;
    float temperature_acceleration;
} SohParameters_t;

/* Initialize SOH estimator */
void soh_capacity_init(CapacityFadeSoh_t* soh,
                        const SohParameters_t* params) {
    soh->nominal_capacity_ah = params->nominal_capacity_ah;
    soh->current_capacity_ah = params->nominal_capacity_ah;
    soh->cycle_count = 0.0f;
    soh->total_energy_throughput_kwh = 0.0f;
    soh->avg_temperature_c = 25.0f;
    soh->last_calibration_soc = 0.0f;
    soh->last_calibration_voltage = 0.0f;
    soh->calibration_valid = false;
}

/* Update SOH based on usage */
void soh_capacity_update(CapacityFadeSoh_t* soh,
                          float current_a,
                          float pack_voltage_v,
                          float temperature_c,
                          float dt_hours) {

    /* Accumulate energy throughput */
    float energy_kwh = (pack_voltage_v * current_a * dt_hours) / 1000.0f;
    if (energy_kwh > 0.0f) {
        soh->total_energy_throughput_kwh += energy_kwh;
    }

    /* Update cycle count (1 full charge+discharge = 1 cycle) */
    float capacity_throughput_ah = fabsf(current_a) * dt_hours;
    soh->cycle_count += capacity_throughput_ah / (2.0f * soh->nominal_capacity_ah);

    /* Temperature-weighted aging */
    float temp_factor = expf(0.05f * (temperature_c - 25.0f));  /* Arrhenius-like */
    soh->avg_temperature_c = 0.99f * soh->avg_temperature_c +
                             0.01f * temperature_c * temp_factor;

    /* Calculate current capacity based on empirical model */
    /* Capacity fade = k1 * sqrt(cycles) + k2 * energy + k3 * temp_factor */
    float k1 = 0.02f;  /* 2% fade at 100 cycles */
    float k2 = 0.0001f;  /* per kWh throughput */
    float k3 = 0.001f;  /* per degree above 25C */

    float capacity_fade = k1 * sqrtf(soh->cycle_count) +
                          k2 * soh->total_energy_throughput_kwh +
                          k3 * fmaxf(0.0f, soh->avg_temperature_c - 25.0f);

    soh->current_capacity_ah = soh->nominal_capacity_ah * (1.0f - capacity_fade);
}

/* Calculate SOH percentage */
float soh_capacity_get_percent(const CapacityFadeSoh_t* soh,
                                float end_of_life_capacity) {

    float soh_percent = (soh->current_capacity_ah / soh->nominal_capacity_ah) * 100.0f;
    return fmaxf(0.0f, fminf(100.0f, soh_percent));
}

/* OCV-based capacity calibration (when SOC crosses wide range) */
void soh_calibrate_capacity(CapacityFadeSoh_t* soh,
                             float soc_start,
                             float soc_end,
                             float charge_added_ah) {

    /* Only calibrate if SOC change is significant */
    float soc_delta = fabsf(soc_end - soc_start);
    if (soc_delta < 20.0f) {
        return;  /* Not enough delta for accurate calibration */
    }

    /* Capacity = charge_added / (soc_end - soc_start) */
    float measured_capacity = charge_added_ah / (soc_delta / 100.0f);

    /* Low-pass filter the measurement */
    soh->current_capacity_ah = 0.8f * soh->current_capacity_ah +
                                0.2f * measured_capacity;

    soh->calibration_valid = true;
}
```

### Resistance Growth SOH

```c
/* SOH estimation based on internal resistance growth */
typedef struct {
    float nominal_resistance_mohm;
    float current_resistance_mohm;
    float resistance_history[10];
    uint8_t resistance_samples;
} ResistanceGrowthSoh_t;

/* Measure internal resistance using current pulse */
float measure_internal_resistance(float voltage_before,
                                   float voltage_during,
                                   float current_before,
                                   float current_during) {

    float dv = voltage_during - voltage_before;
    float di = current_during - current_before;

    if (fabsf(di) < 0.1f) {
        return -1.0f;  /* Invalid measurement */
    }

    /* R = dV / dI (in milliohms) */
    return (dv / di) * 1000.0f;
}

/* Update resistance-based SOH */
void soh_resistance_update(ResistanceGrowthSoh_t* soh,
                            float measured_resistance_mohm) {

    if (measured_resistance_mohm < 0.0f) {
        return;  /* Invalid measurement */
    }

    /* Store in history buffer */
    if (soh->resistance_samples < 10) {
        soh->resistance_history[soh->resistance_samples] = measured_resistance_mohm;
        soh->resistance_samples++;
    } else {
        /* Shift buffer */
        for (int i = 0; i < 9; i++) {
            soh->resistance_history[i] = soh->resistance_history[i+1];
        }
        soh->resistance_history[9] = measured_resistance_mohm;
    }

    /* Calculate average */
    float sum = 0.0f;
    for (uint8_t i = 0; i < soh->resistance_samples; i++) {
        sum += soh->resistance_history[i];
    }
    soh->current_resistance_mohm = sum / soh->resistance_samples;
}

/* Calculate SOH from resistance */
float soh_resistance_get_percent(const ResistanceGrowthSoh_t* soh,
                                  float end_of_life_resistance_mohm) {

    float resistance_ratio = (soh->current_resistance_mohm - soh->nominal_resistance_mohm) /
                             (end_of_life_resistance_mohm - soh->nominal_resistance_mohm);

    float soh_percent = (1.0f - resistance_ratio) * 100.0f;
    return fmaxf(0.0f, fminf(100.0f, soh_percent));
}
```

## Cell Balancing

### Passive (Dissipative) Balancing

```c
/* Passive cell balancing controller */
typedef struct {
    float cell_voltages[96];
    uint8_t cell_count;
    float balance_threshold_mv;
    float balance_hysteresis_mv;
    uint8_t balance_fet_state[96];  /* 0=off, 1=on */
    float balance_current_ma;
    uint32_t balance_start_time_ms;
    bool balancing_active;
} PassiveBalancer_t;

typedef struct {
    float target_voltage_mv;
    float max_balance_time_s;
    float min_soc_for_balance;
    float max_temperature_c;
} PassiveBalancerConfig_t;

/* Initialize passive balancer */
void passive_balancer_init(PassiveBalancer_t* balancer,
                            const PassiveBalancerConfig_t* config) {

    balancer->cell_count = 96;
    balancer->balance_threshold_mv = 10.0f;  /* Start balancing at 10mV difference */
    balancer->balance_hysteresis_mv = 2.0f;  /* Stop at 2mV below target */
    balancer->balance_current_ma = 100.0f;   /* 100mA bleed current */
    balancer->balancing_active = false;

    for (uint8_t i = 0; i < balancer->cell_count; i++) {
        balancer->balance_fet_state[i] = 0;
        balancer->cell_voltages[i] = 0.0f;
    }
}

/* Passive balancing control algorithm */
void passive_balancer_update(PassiveBalancer_t* balancer,
                              const float cell_voltages[],
                              uint8_t cell_count,
                              float avg_soc,
                              float max_temperature_c,
                              const PassiveBalancerConfig_t* config) {

    if (cell_count != balancer->cell_count) {
        return;
    }

    /* Check enable conditions */
    bool enable_conditions_met = true;

    if (avg_soc < config->min_soc_for_balance) {
        enable_conditions_met = false;  /* Don't balance at low SOC */
    }
    if (max_temperature_c > config->max_temperature_c) {
        enable_conditions_met = false;  /* Don't balance if too hot */
    }

    if (!enable_conditions_met) {
        /* Turn off all balance FETs */
        for (uint8_t i = 0; i < cell_count; i++) {
            balancer->balance_fet_state[i] = 0;
        }
        balancer->balancing_active = false;
        return;
    }

    /* Find max and min cell voltage */
    float max_voltage = cell_voltages[0];
    float min_voltage = cell_voltages[0];
    uint8_t max_cell_index = 0;

    for (uint8_t i = 1; i < cell_count; i++) {
        if (cell_voltages[i] > max_voltage) {
            max_voltage = cell_voltages[i];
            max_cell_index = i;
        }
        if (cell_voltages[i] < min_voltage) {
            min_voltage = cell_voltages[i];
        }
    }

    float voltage_spread = max_voltage - min_voltage;

    /* Determine balancing target */
    float target_voltage = max_voltage - balancer->balance_hysteresis_mv;

    /* Control individual cell balance FETs */
    for (uint8_t i = 0; i < cell_count; i++) {
        if (cell_voltages[i] > target_voltage) {
            /* Turn on balance FET for this cell */
            balancer->balance_fet_state[i] = 1;
        } else {
            balancer->balance_fet_state[i] = 0;
        }
    }

    balancer->balancing_active = (voltage_spread > balancer->balance_threshold_mv);
}

/* Get balancing status for diagnostics */
typedef struct {
    float voltage_spread_mv;
    uint8_t cells_balancing;
    float estimated_balance_time_s;
} BalancingStatus_t;

BalancingStatus_t get_balancing_status(const PassiveBalancer_t* balancer,
                                        const float cell_voltages[]) {

    BalancingStatus_t status = {0};

    /* Calculate voltage spread */
    float max_v = cell_voltages[0];
    float min_v = cell_voltages[0];

    for (uint8_t i = 1; i < balancer->cell_count; i++) {
        if (cell_voltages[i] > max_v) max_v = cell_voltages[i];
        if (cell_voltages[i] < min_v) min_v = cell_voltages[i];
    }

    status.voltage_spread_mv = (max_v - min_v) * 1000.0f;

    /* Count cells actively balancing */
    status.cells_balancing = 0;
    for (uint8_t i = 0; i < balancer->cell_count; i++) {
        if (balancer->balance_fet_state[i]) {
            status.cells_balancing++;
        }
    }

    /* Estimate time to balance (simplified) */
    if (status.cells_balancing > 0 && balancer->balance_current_ma > 0.0f) {
        /* t = C * dV / I (very approximate) */
        float delta_v_v = status.voltage_spread_mv / 1000.0f;
        float cell_capacity_ah = 50.0f;  /* Example */
        status.estimated_balance_time_s =
            (cell_capacity_ah * delta_v_v) / (balancer->balance_current_ma / 1000.0f);
    }

    return status;
}
```

### Active (Non-Dissipative) Balancing

```c
/* Active cell balancing using flying capacitor or inductor */
typedef enum {
    ACTIVE_BALANCE_IDLE,
    ACTIVE_BALANCE_CELL_TO_PACK,    /* High cell -> Pack */
    ACTIVE_BALANCE_PACK_TO_CELL,    /* Pack -> Low cell */
    ACTIVE_BALANCE_CELL_TO_CELL     /* High cell -> Low cell */
} ActiveBalanceMode_t;

typedef struct {
    float cell_voltages[96];
    uint8_t cell_count;
    ActiveBalanceMode_t mode;
    uint8_t source_cell;
    uint8_t target_cell;
    float transfer_current_a;
    uint32_t transfer_start_time_ms;
    float transferred_charge_ah;
    bool transfer_active;
} ActiveBalancer_t;

typedef struct {
    float min_voltage_diff_mv;
    float max_transfer_current_a;
    float max_transfer_time_s;
    float efficiency;
} ActiveBalancerConfig_t;

/* Active balancing state machine */
void active_balancer_update(ActiveBalancer_t* balancer,
                             const float cell_voltages[],
                             uint8_t cell_count,
                             const ActiveBalancerConfig_t* config) {

    if (balancer->transfer_active) {
        /* Check if transfer complete */
        uint32_t elapsed_ms = get_system_time_ms() - balancer->transfer_start_time_ms;

        if (elapsed_ms > config->max_transfer_time_s * 1000U) {
            /* Stop transfer */
            balancer->transfer_active = false;
            balancer->mode = ACTIVE_BALANCE_IDLE;
            return;
        }

        /* Update transferred charge estimate */
        float dt_hours = 0.001f;  /* 1 second */
        balancer->transferred_charge_ah +=
            balancer->transfer_current_a * config->efficiency * dt_hours;
        return;
    }

    /* Find highest and lowest cells */
    float max_voltage = cell_voltages[0];
    float min_voltage = cell_voltages[0];
    uint8_t max_cell = 0;
    uint8_t min_cell = 0;

    for (uint8_t i = 1; i < cell_count; i++) {
        if (cell_voltages[i] > max_voltage) {
            max_voltage = cell_voltages[i];
            max_cell = i;
        }
        if (cell_voltages[i] < min_voltage) {
            min_voltage = cell_voltages[i];
            min_cell = i;
        }
    }

    float voltage_diff = max_voltage - min_voltage;

    /* Check if balancing needed */
    if (voltage_diff < config->min_voltage_diff_mv / 1000.0f) {
        return;  /* No balancing needed */
    }

    /* Determine optimal balancing mode */
    if (voltage_diff > 0.1f) {
        /* Large difference: cell-to-cell direct transfer */
        balancer->mode = ACTIVE_BALANCE_CELL_TO_CELL;
        balancer->source_cell = max_cell;
        balancer->target_cell = min_cell;
    } else if (max_voltage > (min_voltage + 0.02f)) {
        /* Moderate: high cell to pack */
        balancer->mode = ACTIVE_BALANCE_CELL_TO_PACK;
        balancer->source_cell = max_cell;
        balancer->target_cell = 0xFF;  /* Pack */
    } else {
        /* Small: pack to low cell */
        balancer->mode = ACTIVE_BALANCE_PACK_TO_CELL;
        balancer->source_cell = 0xFF;
        balancer->target_cell = min_cell;
    }

    /* Start transfer */
    balancer->transfer_current_a = config->max_transfer_current_a;
    balancer->transfer_start_time_ms = get_system_time_ms();
    balancer->transferred_charge_ah = 0.0f;
    balancer->transfer_active = true;
}
```

## Equivalent Circuit Models

### 1RC Model

```c
/* First-order RC equivalent circuit model */
typedef struct {
    float soc;
    float v1;           /* Voltage across RC pair */
    float ocv;          /* Open circuit voltage */
    float r0;           /* Ohmic resistance */
    float r1;           /* RC resistance */
    float c1;           /* RC capacitance */
    float temperature_c;
} OneRcModel_t;

/* Initialize 1RC model */
void onerc_init(OneRcModel_t* model,
                 float initial_soc,
                 float temperature_c) {

    model->soc = initial_soc;
    model->v1 = 0.0f;
    model->temperature_c = temperature_c;

    /* Temperature-dependent parameters (example) */
    model->r0 = 0.002f * (1.0f + 0.01f * (25.0f - temperature_c));
    model->r1 = 0.001f * (1.0f + 0.01f * (25.0f - temperature_c));
    model->c1 = 10000.0f;
}

/* Update 1RC model state */
float onerc_update(OneRcModel_t* model,
                    float current_a,  /* Positive = discharge */
                    float dt) {

    /* Update RC voltage */
    float tau = model->r1 * model->c1;
    float dv1_dt = -model->v1 / tau + current_a / model->c1;
    model->v1 += dv1_dt * dt;

    /* Calculate terminal voltage */
    float v_terminal = model->ocv - model->v1 - current_a * model->r0;

    return v_terminal;
}
```

### 2RC Model

```c
/* Second-order RC equivalent circuit model (more accurate) */
typedef struct {
    float soc;
    float v1;           /* Fast dynamics RC */
    float v2;           /* Slow dynamics RC */
    float ocv;
    float r0;
    float r1;
    float c1;
    float r2;
    float c2;
} TwoRcModel_t;

/* Initialize 2RC model */
void tworc_init(TwoRcModel_t* model,
                 float initial_soc,
                 float temperature_c) {

    model->soc = initial_soc;
    model->v1 = 0.0f;
    model->v2 = 0.0f;

    /* Typical parameters for automotive Li-ion cell */
    model->r0 = 0.002f;
    model->r1 = 0.001f;
    model->c1 = 5000.0f;  /* Fast dynamics (~5s time constant) */
    model->r2 = 0.0005f;
    model->c2 = 50000.0f; /* Slow dynamics (~25s time constant) */
}

/* Update 2RC model state */
float tworc_update(TwoRcModel_t* model,
                    float current_a,
                    float dt) {

    /* Update RC voltages */
    float tau1 = model->r1 * model->c1;
    float tau2 = model->r2 * model->c2;

    float dv1_dt = -model->v1 / tau1 + current_a / model->c1;
    float dv2_dt = -model->v2 / tau2 + current_a / model->c2;

    model->v1 += dv1_dt * dt;
    model->v2 += dv2_dt * dt;

    /* Calculate terminal voltage */
    float v_terminal = model->ocv - model->v1 - model->v2 - current_a * model->r0;

    return v_terminal;
}

/* Get model state for diagnostics */
typedef struct {
    float ohmic_drop_v;
    float fast_rc_drop_v;
    float slow_rc_drop_v;
    float total_polarization_v;
} ModelDiagnostics_t;

ModelDiagnostics_t tworc_get_diagnostics(const TwoRcModel_t* model,
                                          float current_a) {

    ModelDiagnostics_t diag;
    diag.ohmic_drop_v = current_a * model->r0;
    diag.fast_rc_drop_v = model->v1;
    diag.slow_rc_drop_v = model->v2;
    diag.total_polarization_v = diag.ohmic_drop_v +
                                 diag.fast_rc_drop_v +
                                 diag.slow_rc_drop_v;
    return diag;
}
```

## Fault Detection and Diagnostics

### Overvoltage/Undervoltage Detection

```c
/* Cell voltage fault detection */
typedef struct {
    float cell_voltages[96];
    uint8_t cell_count;
    float overvoltage_threshold_v;
    float undervoltage_threshold_v;
    float overvoltage_delay_ms;
    float undervoltage_delay_ms;
    uint32_t fault_timestamp_ms[96];
    uint16_t fault_flags;
} CellVoltageFaults_t;

#define CELL_OV_FAULT(cell)  (1U << (cell))
#define CELL_UV_FAULT(cell)  (1U << ((cell) + 32))

/* Initialize voltage fault detector */
void cell_faults_init(CellVoltageFaults_t* faults,
                       uint8_t cell_count) {

    faults->cell_count = cell_count;
    faults->overvoltage_threshold_v = 4.25f;
    faults->undervoltage_threshold_v = 2.5f;
    faults->overvoltage_delay_ms = 100.0f;
    faults->undervoltage_delay_ms = 100.0f;
    faults->fault_flags = 0U;

    for (uint8_t i = 0; i < cell_count; i++) {
        faults->fault_timestamp_ms[i] = 0U;
        faults->cell_voltages[i] = 0.0f;
    }
}

/* Update fault detection */
uint16_t cell_faults_update(CellVoltageFaults_t* faults,
                             const float cell_voltages[],
                             uint32_t current_time_ms) {

    uint16_t new_faults = 0U;

    for (uint8_t i = 0; i < faults->cell_count; i++) {
        faults->cell_voltages[i] = cell_voltages[i];

        /* Overvoltage check */
        if (cell_voltages[i] > faults->overvoltage_threshold_v) {
            if (faults->fault_timestamp_ms[i] == 0U) {
                faults->fault_timestamp_ms[i] = current_time_ms;
            } else if ((current_time_ms - faults->fault_timestamp_ms[i]) >
                       faults->overvoltage_delay_ms) {
                faults->fault_flags |= CELL_OV_FAULT(i);
                new_faults |= CELL_OV_FAULT(i);
            }
        } else {
            faults->fault_timestamp_ms[i] = 0U;
            faults->fault_flags &= ~CELL_OV_FAULT(i);
        }

        /* Undervoltage check */
        if (cell_voltages[i] < faults->undervoltage_threshold_v) {
            if (faults->fault_timestamp_ms[i] == 0U) {
                faults->fault_timestamp_ms[i] = current_time_ms;
            } else if ((current_time_ms - faults->fault_timestamp_ms[i]) >
                       faults->undervoltage_delay_ms) {
                faults->fault_flags |= CELL_UV_FAULT(i);
                new_faults |= CELL_UV_FAULT(i);
            }
        } else {
            faults->fault_timestamp_ms[i] = 0U;
            faults->fault_flags &= ~CELL_UV_FAULT(i);
        }
    }

    return new_faults;
}
```

### Overcurrent Detection

```c
/* Pack current fault detection */
typedef struct {
    float charge_current_limit_a;
    float discharge_current_limit_a;
    float charge_peak_limit_a;
    float discharge_peak_limit_a;
    float charge_peak_duration_ms;
    float discharge_peak_duration_ms;
    float measured_current_a;
    uint32_t overcharge_start_ms;
    uint32_t overdischarge_start_ms;
    uint8_t fault_flags;
} PackCurrentFaults_t;

#define CURRENT_OVERCHARGE_CONTINUOUS  0x01
#define CURRENT_OVERDISCHARGE_CONTINUOUS 0x02
#define CURRENT_OVERCHARGE_PEAK      0x04
#define CURRENT_OVERDISCHARGE_PEAK   0x08

/* Initialize current fault detector */
void current_faults_init(PackCurrentFaults_t* faults) {
    faults->charge_current_limit_a = -200.0f;   /* Negative = charge */
    faults->discharge_current_limit_a = 300.0f;
    faults->charge_peak_limit_a = -400.0f;
    faults->discharge_peak_limit_a = 500.0f;
    faults->charge_peak_duration_ms = 5000.0f;
    faults->discharge_peak_duration_ms = 10000.0f;
    faults->measured_current_a = 0.0f;
    faults->overcharge_start_ms = 0U;
    faults->overdischarge_start_ms = 0U;
    faults->fault_flags = 0U;
}

/* Update current fault detection */
uint8_t current_faults_update(PackCurrentFaults_t* faults,
                               float current_a,
                               uint32_t current_time_ms) {

    faults->measured_current_a = current_a;
    uint8_t new_faults = 0U;

    /* Continuous charge current limit */
    if (current_a < faults->charge_current_limit_a) {
        if (faults->overcharge_start_ms == 0U) {
            faults->overcharge_start_ms = current_time_ms;
        } else {
            uint32_t duration = current_time_ms - faults->overcharge_start_ms;
            if (duration > faults->charge_peak_duration_ms) {
                faults->fault_flags |= CURRENT_OVERCHARGE_CONTINUOUS;
                new_faults |= CURRENT_OVERCHARGE_CONTINUOUS;
            }
        }
    } else {
        faults->overcharge_start_ms = 0U;
        faults->fault_flags &= ~CURRENT_OVERCHARGE_CONTINUOUS;
    }

    /* Continuous discharge current limit */
    if (current_a > faults->discharge_current_limit_a) {
        if (faults->overdischarge_start_ms == 0U) {
            faults->overdischarge_start_ms = current_time_ms;
        } else {
            uint32_t duration = current_time_ms - faults->overdischarge_start_ms;
            if (duration > faults->discharge_peak_duration_ms) {
                faults->fault_flags |= CURRENT_OVERDISCHARGE_CONTINUOUS;
                new_faults |= CURRENT_OVERDISCHARGE_CONTINUOUS;
            }
        }
    } else {
        faults->overdischarge_start_ms = 0U;
        faults->fault_flags &= ~CURRENT_OVERDISCHARGE_CONTINUOUS;
    }

    /* Peak current limits (immediate) */
    if (current_a < faults->charge_peak_limit_a) {
        faults->fault_flags |= CURRENT_OVERCHARGE_PEAK;
        new_faults |= CURRENT_OVERCHARGE_PEAK;
    } else {
        faults->fault_flags &= ~CURRENT_OVERCHARGE_PEAK;
    }

    if (current_a > faults->discharge_peak_limit_a) {
        faults->fault_flags |= CURRENT_OVERDISCHARGE_PEAK;
        new_faults |= CURRENT_OVERDISCHARGE_PEAK;
    } else {
        faults->fault_flags &= ~CURRENT_OVERDISCHARGE_PEAK;
    }

    return new_faults;
}
```

### Insulation Monitoring

```c
/* High voltage insulation resistance monitoring */
typedef struct {
    float hv_positive_voltage_v;
    float hv_negative_voltage_v;
    float pack_voltage_v;
    float insulation_resistance_kohm;
    float insulation_fault_threshold_kohm;
    uint32_t fault_start_ms;
    bool insulation_fault;
} InsulationMonitor_t;

/* Calculate insulation resistance using voltage divider method */
float calculate_insulation_resistance(float v_positive,
                                       float v_negative,
                                       float v_pack) {

    /* Simplified calculation assuming symmetric leakage */
    /* R_iso = (V_pack / (V_positive + V_negative)) * R_reference */
    /* This assumes internal reference resistors in the isolation monitor */

    if (fabsf(v_positive + v_negative) < 0.1f) {
        return 10000.0f;  /* Very high resistance (good) */
    }

    float r_reference = 1000.0f;  /* 1 Mohm internal reference */
    float r_iso = (v_pack / (v_positive + v_negative)) * r_reference;

    return r_iso;
}

/* Update insulation monitoring */
bool insulation_monitor_update(InsulationMonitor_t* monitor,
                                float v_positive,
                                float v_negative,
                                float v_pack,
                                uint32_t current_time_ms) {

    monitor->hv_positive_voltage_v = v_positive;
    monitor->hv_negative_voltage_v = v_negative;
    monitor->pack_voltage_v = v_pack;

    /* Calculate insulation resistance */
    monitor->insulation_resistance_kohm =
        calculate_insulation_resistance(v_positive, v_negative, v_pack);

    /* Check for fault */
    if (monitor->insulation_resistance_kohm < monitor->insulation_fault_threshold_kohm) {
        if (monitor->fault_start_ms == 0U) {
            monitor->fault_start_ms = current_time_ms;
        } else {
            /* Fault persists for 500ms before latching */
            if ((current_time_ms - monitor->fault_start_ms) > 500U) {
                monitor->insulation_fault = true;
            }
        }
    } else {
        monitor->fault_start_ms = 0U;
        monitor->insulation_fault = false;
    }

    return monitor->insulation_fault;
}
```

## Contactor Control

### Precharge Sequence

```c
/* Contactor control state machine */
typedef enum {
    CONTACTOR_STATE_OPEN,
    CONTACTOR_STATE_PRECHARGE,
    CONTACTOR_STATE_CLOSING,
    CONTACTOR_STATE_CLOSED,
    CONTACTOR_STATE_OPENING,
    CONTACTOR_STATE_FAULT
} ContactorState_t;

typedef struct {
    ContactorState_t state;
    bool main_positive_contactor;
    bool main_negative_contactor;
    bool precharge_contactor;
    float bus_voltage_v;
    float battery_voltage_v;
    uint32_t state_entry_time_ms;
    float precharge_timeout_ms;
    float precharge_complete_threshold_percent;
    uint8_t fault_code;
} ContactorController_t;

/* Initialize contactor controller */
void contactor_controller_init(ContactorController_t* controller) {
    controller->state = CONTACTOR_STATE_OPEN;
    controller->main_positive_contactor = false;
    controller->main_negative_contactor = false;
    controller->precharge_contactor = false;
    controller->bus_voltage_v = 0.0f;
    controller->battery_voltage_v = 0.0f;
    controller->precharge_timeout_ms = 5000.0f;
    controller->precharge_complete_threshold_percent = 95.0f;
    controller->fault_code = 0U;
}

/* Contactor control state machine */
void contactor_controller_update(ContactorController_t* controller,
                                  bool close_command,
                                  float bus_voltage_v,
                                  float battery_voltage_v,
                                  uint32_t current_time_ms) {

    controller->bus_voltage_v = bus_voltage_v;
    controller->battery_voltage_v = battery_voltage_v;

    switch (controller->state) {
        case CONTACTOR_STATE_OPEN:
            if (close_command) {
                /* Start precharge sequence */
                controller->precharge_contactor = true;
                controller->state = CONTACTOR_STATE_PRECHARGE;
                controller->state_entry_time_ms = current_time_ms;
            }
            break;

        case CONTACTOR_STATE_PRECHARGE:
            /* Check if precharge complete */
            float precharge_ratio = bus_voltage_v / battery_voltage_v;
            uint32_t precharge_time = current_time_ms - controller->state_entry_time_ms;

            if (precharge_ratio >= (controller->precharge_complete_threshold_percent / 100.0f)) {
                /* Precharge complete - close main contactors */
                controller->main_positive_contactor = true;
                controller->main_negative_contactor = true;
                controller->precharge_contactor = false;
                controller->state = CONTACTOR_STATE_CLOSED;
            } else if (precharge_time > controller->precharge_timeout_ms) {
                /* Precharge timeout - fault */
                controller->state = CONTACTOR_STATE_FAULT;
                controller->fault_code = 0x01;  /* Precharge timeout */
            }
            break;

        case CONTACTOR_STATE_CLOSED:
            if (!close_command) {
                /* Open contactors */
                controller->main_positive_contactor = false;
                controller->main_negative_contactor = false;
                controller->state = CONTACTOR_STATE_OPEN;
            }
            break;

        case CONTACTOR_STATE_FAULT:
            /* All contactors off, require reset to recover */
            controller->main_positive_contactor = false;
            controller->main_negative_contactor = false;
            controller->precharge_contactor = false;
            break;

        default:
            break;
    }
}

/* Contactor welding detection */
typedef struct {
    bool contactor_command;
    bool contactor_feedback;
    uint32_t mismatch_start_ms;
    bool welding_detected;
} ContactorWeldDetector_t;

bool detect_contactor_weld(ContactorWeldDetector_t* detector,
                            bool command,
                            bool feedback,
                            uint32_t current_time_ms) {

    detector->contactor_command = command;
    detector->contactor_feedback = feedback;

    /* Check for command/feedback mismatch */
    if (command != feedback) {
        if (detector->mismatch_start_ms == 0U) {
            detector->mismatch_start_ms = current_time_ms;
        } else {
            /* Mismatch persists for 100ms - likely weld */
            if ((current_time_ms - detector->mismatch_start_ms) > 100U) {
                if (command == false && feedback == true) {
                    detector->welding_detected = true;
                    return true;
                }
            }
        }
    } else {
        detector->mismatch_start_ms = 0U;
    }

    detector->welding_detected = false;
    return false;
}
```

## AUTOSAR Implementation

### BMS SwComponent

```xml
<!-- BatteryManager SwComponentType (ARXML) -->
<APPLICATION-SW-COMPONENT-TYPE>
  <SHORT-NAME>BatteryManager</SHORT-NAME>

  <!-- Port Interfaces -->
  <PORTS>
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>CellVoltagesPort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/CellVoltages_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <R-PORT-PROTOTYPE>
      <SHORT-NAME>PackCurrentPort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/PackCurrent_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <P-PORT-PROTOTYPE>
      <SHORT-NAME>SocEstimatePort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/SocEstimate_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>

    <P-PORT-PROTOTYPE>
      <SHORT-NAME>SohEstimatePort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/SohEstimate_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>

    <P-PORT-PROTOTYPE>
      <SHORT-NAME>ContactorCommandPort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/ContactorCommand_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>
  </PORTS>

  <!-- Internal Behavior -->
  <INTERNAL-BEHAVIOR>
    <RUNNABLE-ENTITIES>
      <RUNNABLE-ENTITY>
        <SHORT-NAME>SocEstimation_100ms</SHORT-NAME>
        <BEGIN-PERIOD>0.1</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>

      <RUNNABLE-ENTITY>
        <SHORT-NAME>CellBalancing_1000ms</SHORT-NAME>
        <BEGIN-PERIOD>1.0</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>

      <RUNNABLE-ENTITY>
        <SHORT-NAME>FaultDetection_10ms</SHORT-NAME>
        <BEGIN-PERIOD>0.01</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>
    </RUNNABLE-ENTITIES>
  </INTERNAL-BEHAVIOR>
</APPLICATION-SW-COMPONENT-TYPE>
```

### Runnable Implementation

```c
/* SOC Estimation Runnable - 100ms cycle */
#include "Rte_BatteryManager.h"

void BatteryManager_SocEstimation_100ms_Runnable(void) {
    /* Read cell voltages */
    CellVoltageArray_t cell_voltages;
    Rte_Read_BatteryManager_CellVoltagesPort_Value(&cell_voltages);

    /* Read pack current */
    float pack_current_a;
    Rte_Read_BatteryManager_PackCurrentPort_Value(&pack_current_a);

    /* Read temperature */
    float pack_temperature_c;
    Rte_Read_BatteryManager_PackTemperaturePort_Value(&pack_temperature_c);

    /* Update EKF SOC estimate */
    float soc = ekf_soc_update(&g_ekf_estimator,
                                pack_current_a,
                                cell_voltages.average_voltage,
                                0.1f);

    /* Write SOC estimate */
    Rte_Write_BatteryManager_SocEstimatePort_SocPercent(soc);

    /* Update SOH estimate (less frequent - every 10th cycle) */
    static uint8_t cycle_counter = 0;
    if (++cycle_counter >= 10) {
        float soh = soh_capacity_get_percent(&g_soh_estimator,
                                              END_OF_LIFE_CAPACITY_AH);
        Rte_Write_BatteryManager_SohEstimatePort_SohPercent(soh);
        cycle_counter = 0;
    }
}

/* Cell Balancing Runnable - 1000ms cycle */
void BatteryManager_CellBalancing_1000ms_Runnable(void) {
    CellVoltageArray_t cell_voltages;
    Rte_Read_BatteryManager_CellVoltagesPort_Value(&cell_voltages);

    /* Update passive balancer */
    passive_balancer_update(&g_passive_balancer,
                            cell_voltages.individual_cells,
                            cell_voltages.cell_count,
                            g_soc_estimate,
                            cell_voltages.max_temperature,
                            &g_balancer_config);

    /* Write balance FET commands */
    BalanceFetArray_t fet_commands;
    memcpy(fet_commands.fet_state,
           g_passive_balancer.balance_fet_state,
           sizeof(fet_commands.fet_state));
    Rte_Write_BatteryManager_BalanceFetCommandPort_Value(&fet_commands);
}

/* Fault Detection Runnable - 10ms cycle */
void BatteryManager_FaultDetection_10ms_Runnable(void) {
    CellVoltageArray_t cell_voltages;
    Rte_Read_BatteryManager_CellVoltagesPort_Value(&cell_voltages);

    float pack_current_a;
    Rte_Read_BatteryManager_PackCurrentPort_Value(&pack_current_a);

    uint32_t current_time_ms = Rte_GetTimestamp_ms();

    /* Update cell voltage faults */
    uint16_t voltage_faults = cell_faults_update(&g_cell_faults,
                                                  cell_voltages.individual_cells,
                                                  current_time_ms);

    /* Update current faults */
    uint8_t current_faults = current_faults_update(&g_current_faults,
                                                    pack_current_a,
                                                    current_time_ms);

    /* Report faults to diagnostics */
    if (voltage_faults != 0U || current_faults != 0U) {
        Dem_ReportErrorStatus(DEM_EVENT_BMS_VOLTAGE_FAULT, DEM_EVENT_STATUS_FAILED);
    }
}
```

## Safety Mechanisms (ISO 26262)

### Redundant SOC Estimation

```c
/* ASIL D: Dual-track SOC estimation with plausibility check */
typedef struct {
    EfkSocEstimator_t ekf_primary;
    CoulombCountingSoc_t coulomb_secondary;
    float soc_primary;
    float soc_secondary;
    float soc_difference;
    bool soc_plausibility_valid;
    uint32_t plausibility_fault_start_ms;
} RedundantSocEstimator_t;

/* Dual-track SOC with cross-checking */
float redundant_soc_update(RedundantSocEstimator_t* estimator,
                            float current_a,
                            float voltage_v,
                            float temperature_c,
                            uint32_t current_time_ms) {

    /* Update both estimators */
    estimator->soc_primary = ekf_soc_update(&estimator->ekf_primary,
                                             current_a,
                                             voltage_v,
                                             0.1f);

    estimator->soc_secondary = soc_coulomb_update(&estimator->coulomb_secondary,
                                                   current_a,
                                                   temperature_c,
                                                   current_time_ms);

    /* Cross-check plausibility */
    estimator->soc_difference = fabsf(estimator->soc_primary -
                                       estimator->soc_secondary);

    if (estimator->soc_difference > 5.0f) {  /* 5% threshold */
        if (estimator->plausibility_fault_start_ms == 0U) {
            estimator->plausibility_fault_start_ms = current_time_ms;
        } else if ((current_time_ms - estimator->plausibility_fault_start_ms) > 1000U) {
            estimator->soc_plausibility_valid = false;
            /* Use conservative estimate */
            return fminf(estimator->soc_primary, estimator->soc_secondary);
        }
    } else {
        estimator->plausibility_fault_start_ms = 0U;
        estimator->soc_plausibility_valid = true;
    }

    /* Return averaged estimate when valid */
    return (estimator->soc_primary + estimator->soc_secondary) / 2.0f;
}
```

## Approach

1. **Define BMS requirements**
   - Identify SOC/SOH accuracy targets
   - Define fault detection response times
   - Specify balancing strategy and thresholds

2. **Characterize battery**
   - Perform OCV-SOC mapping at multiple temperatures
   - Measure internal resistance (HPPC test)
   - Identify capacity and power fade curves

3. **Develop estimation algorithms**
   - Implement coulomb counting baseline
   - Add EKF for drift correction
   - Implement SOH capacity and resistance tracking

4. **Design balancing strategy**
   - Select passive vs. active balancing
   - Define balancing thresholds and timing
   - Implement thermal-aware balancing

5. **Implement fault detection**
   - Configure voltage, current, temperature limits
   - Add debounce and confirmation logic
   - Define fault reactions and safe states

6. **Integrate with AUTOSAR**
   - Design SwComponent with appropriate ports
   - Configure runnables and timing
   - Generate RTE and integrate

7. **Validate and calibrate**
   - MIL/SIL testing of estimation algorithms
   - HIL testing with production ECU
   - Vehicle calibration for accuracy

## Deliverables

- BMS architecture and requirements specification
- SOC/SOH estimation algorithm implementation
- Cell balancing controller code
- Fault detection and diagnostics module
- Equivalent circuit model parameters
- AUTOSAR SWC integration code
- Calibration parameter database
- Test results (MIL/SIL/HIL/Vehicle)
- ISO 26262 safety case documentation

## Related Context
- @context/skills/ev/thermal-management.md
- @context/skills/powertrain/battery-management.md
- @context/skills/battery/bms.md
- @context/skills/autosar/classic-platform.md
- @context/skills/safety/iso-26262-overview.md
- @context/skills/security/iso-21434-cybersecurity.md

## Tools Required
- MATLAB/Simulink (algorithm development)
- Vector CANoe/CANalyzer (network analysis)
- ETAS INCA (calibration)
- dSPACE HIL (hardware-in-loop testing)
- Arbin/BT2000 (battery cycler testing)
- Chroma battery test systems
- Static analyzer (Polyspace/Klocwork)
- Battery characterization equipment (HPPC tester)
- Thermal chamber for temperature testing
- High-precision multimeter for resistance measurement