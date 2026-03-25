# Skill: Battery Management System (BMS)

## When to Activate
- User asks about BMS algorithm design or implementation
- User needs SOC/SOH estimation guidance (EKF, coulomb counting, aging models)
- User requests cell balancing strategy (active vs passive)
- User is designing battery safety mechanisms or diagnostics
- User needs thermal management control for battery packs

## Standards Compliance
- ISO 26262 ASIL C/D (battery safety functions)
- ASPICE Level 3
- AUTOSAR 4.4 Classic Platform
- ISO 21434 (cybersecurity for battery systems)
- UN GTR No. 20 (battery safety for electric vehicles)
- SAE J1798 (battery system testing)

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Cell count (series) | 48-150 | cells (96S typical for EV) |
| Nominal pack voltage | 350-800 | V |
| Pack capacity | 40-200 | kWh |
| SOC accuracy target | ±2 (EKF), ±5 (CC) | % |
| SOH accuracy target | ±3 | % |
| Balancing current (passive) | 100-500 | mA |
| Balancing current (active) | 1-5 | A |
| Voltage uniformity target | < 50 | mV |
| Update rate (SOC) | 1-10 | Hz |
| Operating temperature | -20 to 60 | °C |

## BMS System Architecture

```
+-------------------------------------------------------------------+
|                      BMS Application Layer                         |
|  +----------------+  +----------------+  +----------------+       |
|  | SOC Estimation |  | SOH Prediction |  | Cell Balancing |       |
|  | (EKF/UKF/ML)   |  | (Aging Models) |  | (Active/Passive)|      |
|  +----------------+  +----------------+  +----------------+       |
|  +----------------+  +----------------+  +----------------+       |
|  | Thermal Mgmt   |  | Safety Monitor |  | Diagnostics    |       |
|  | Control        |  | (ISO 26262)    |  | (DTC storage)  |       |
|  +----------------+  +----------------+  +----------------+       |
+-----------------------------------|-------------------------------+
|                                   v                               |
|  +------------------------------------------------------------+  |
|  |              AUTOSAR RTE (Generated)                       |  |
|  +------------------------------------------------------------+  |
+-----------------------------------|-------------------------------+
|                          BSW Layer                                |
|  +--------+  +--------+  +--------+  +--------+  +--------+     |
|  |  ADC   |  |  CAN   |  |  PWM   |  |  NVM   |  |  DEM   |     |
|  +--------+  +--------+  +--------+  +--------+  +--------+     |
+-----------------------------------|-------------------------------+
|                      Hardware (MCU + AFE)                         |
|  +-------------+  +-------------+  +-------------+               |
|  |  Cell Voltage|  |  Current    |  | Temperature|               |
|  |  (AFE)       |  |  Shunt/Hall |  |  (NTC)     |               |
|  +-------------+  +-------------+  +-------------+               |
+-------------------------------------------------------------------+
```

## State of Charge (SOC) Estimation

### Coulomb Counting (Baseline)

```c
/* Simple coulomb counting with efficiency correction */
typedef struct {
    float nominal_capacity_ah;
    float soc;
    float charge_efficiency;
    float discharge_efficiency;
} CoulombCounter_t;

void coulomb_counter_init(CoulombCounter_t* cc,
                           float nominal_capacity_ah,
                           float initial_soc) {
    cc->nominal_capacity_ah = nominal_capacity_ah;
    cc->soc = initial_soc;
    cc->charge_efficiency = 0.98f;    /* 2% loss during charging */
    cc->discharge_efficiency = 1.0f;   /* No loss during discharge */
}

void coulomb_counter_update(CoulombCounter_t* cc,
                             float current_a,
                             float dt_s) {
    /* Positive current = discharge, negative = charge */
    float efficiency = (current_a > 0.0f) ?
                        cc->discharge_efficiency : cc->charge_efficiency;

    /* delta_soc = -(I * dt * efficiency) / (3600 * Q_nominal) */
    float delta_soc = -(current_a * dt_s * efficiency) /
                       (3600.0f * cc->nominal_capacity_ah);

    cc->soc += delta_soc;

    /* Clamp to valid range [0, 1] */
    if (cc->soc > 1.0f) {
        cc->soc = 1.0f;
    } else if (cc->soc < 0.0f) {
        cc->soc = 0.0f;
    }
}

float coulomb_counter_get_soc(const CoulombCounter_t* cc) {
    return cc->soc;
}
```

### Extended Kalman Filter (Production Grade)

```c
/* EKF-based SOC estimation with 2RC equivalent circuit model */
typedef struct {
    /* State vector: [SOC, V1, V2] */
    float x[3];

    /* State covariance (3x3) */
    float P[3][3];

    /* Process noise covariance */
    float Q[3][3];

    /* Measurement noise covariance */
    float R;

    /* Battery parameters (from calibration) */
    float nominal_capacity_ah;
    const float* ocv_soc_lut;  /* [soc, ocv] pairs */
    size_t ocv_lut_size;
    const float* r0_lut;       /* Ohmic resistance vs SOC */
    size_t r0_lut_size;

    /* Sampling time */
    float dt;
} SocEkf_t;

/* Lookup table interpolation */
static float interpolate_lut(float x, const float* lut, size_t size) {
    /* Find bracketing indices */
    if (x <= lut[0]) {
        return lut[1];
    }
    if (x >= lut[(size - 1) * 2]) {
        return lut[(size - 1) * 2 + 1];
    }

    /* Binary search for interval */
    size_t lo = 0, hi = size - 1;
    while (hi - lo > 1) {
        size_t mid = (lo + hi) / 2;
        if (lut[mid * 2] <= x) {
            lo = mid;
        } else {
            hi = mid;
        }
    }

    /* Linear interpolation */
    float x0 = lut[lo * 2];
    float x1 = lut[hi * 2];
    float y0 = lut[lo * 2 + 1];
    float y1 = lut[hi * 2 + 1];

    return y0 + (y1 - y0) * (x - x0) / (x1 - x0);
}

void ekf_soc_init(SocEkf_t* ekf,
                   float nominal_capacity_ah,
                   float initial_soc,
                   const float* ocv_lut,
                   size_t ocv_size) {
    /* Initialize state: [SOC, V1, V2] */
    ekf->x[0] = initial_soc;
    ekf->x[1] = 0.0f;
    ekf->x[2] = 0.0f;

    /* Initialize covariance (diagonal) */
    ekf->P[0][0] = 0.01f; ekf->P[0][1] = 0.0f; ekf->P[0][2] = 0.0f;
    ekf->P[1][0] = 0.0f;  ekf->P[1][1] = 0.01f; ekf->P[1][2] = 0.0f;
    ekf->P[2][0] = 0.0f;  ekf->P[2][1] = 0.0f;  ekf->P[2][2] = 0.01f;

    /* Process noise (tune based on model accuracy) */
    ekf->Q[0][0] = 1e-6f; ekf->Q[0][1] = 0.0f; ekf->Q[0][2] = 0.0f;
    ekf->Q[1][0] = 0.0f;  ekf->Q[1][1] = 1e-4f; ekf->Q[1][2] = 0.0f;
    ekf->Q[2][0] = 0.0f;  ekf->Q[2][1] = 0.0f;  ekf->Q[2][2] = 1e-4f;

    /* Measurement noise (voltage sensor noise) */
    ekf->R = 1e-4f;

    ekf->nominal_capacity_ah = nominal_capacity_ah;
    ekf->ocv_soc_lut = ocv_lut;
    ekf->ocv_lut_size = ocv_size;
    ekf->dt = 1.0f;  /* 1 second default */
}

void ekf_soc_predict(SocEkf_t* ekf, float current_a, float dt_s) {
    ekf->dt = dt_s;

    float soc = ekf->x[0];
    float v1 = ekf->x[1];
    float v2 = ekf->x[2];

    /* Get RC parameters at current SOC */
    float r1 = interpolate_lut(soc, ekf->r0_lut + 2, ekf->r0_lut_size);
    float c1 = 1000.0f;  /* Simplified: constant */
    float r2 = interpolate_lut(soc, ekf->r0_lut + 4, ekf->r0_lut_size);
    float c2 = 5000.0f;  /* Simplified: constant */

    /* Time constants */
    float tau1 = r1 * c1;
    float tau2 = r2 * c2;

    /* SOC dynamics: d(SOC)/dt = -I / (3600 * Q_nom) */
    float soc_new = soc - (current_a * dt_s) / (3600.0f * ekf->nominal_capacity_ah);

    /* Clamp SOC */
    if (soc_new > 1.0f) soc_new = 1.0f;
    if (soc_new < 0.0f) soc_new = 0.0f;

    /* RC dynamics: V(t) = exp(-t/tau)*V(0) + (1-exp(-t/tau))*R*I */
    float exp1 = expf(-dt_s / tau1);
    float exp2 = expf(-dt_s / tau2);

    float v1_new = exp1 * v1 + (1.0f - exp1) * r1 * current_a;
    float v2_new = exp2 * v2 + (1.0f - exp2) * r2 * current_a;

    /* Update state */
    ekf->x[0] = soc_new;
    ekf->x[1] = v1_new;
    ekf->x[2] = v2_new;

    /* State transition Jacobian F (for covariance propagation) */
    /* F = [[1, 0, 0], [0, exp1, 0], [0, 0, exp2]] */
    float f11 = 1.0f, f22 = exp1, f33 = exp2;

    /* P = F * P * F^T + Q (simplified for diagonal F) */
    float P_new[3][3];
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            float fi = (i == 0) ? f11 : ((i == 1) ? f22 : f33);
            float fj = (j == 0) ? f11 : ((j == 1) ? f22 : f33);
            P_new[i][j] = fi * fj * ekf->P[i][j] + ekf->Q[i][j];
        }
    }

    /* Copy back */
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            ekf->P[i][j] = P_new[i][j];
        }
    }
}

/* Numerical derivative of OCV w.r.t. SOC */
static float docv_dsoc(SocEkf_t* ekf, float soc) {
    const float delta = 0.01f;
    float soc_plus = (soc + delta < 1.0f) ? soc + delta : 1.0f;
    float soc_minus = (soc - delta > 0.0f) ? soc - delta : 0.0f;

    float ocv_plus = interpolate_lut(soc_plus, ekf->ocv_soc_lut, ekf->ocv_lut_size);
    float ocv_minus = interpolate_lut(soc_minus, ekf->ocv_soc_lut, ekf->ocv_lut_size);

    return (ocv_plus - ocv_minus) / (soc_plus - soc_minus + 1e-10f);
}

void ekf_soc_update(SocEkf_t* ekf, float voltage_meas, float current_a) {
    float soc = ekf->x[0];
    float v1 = ekf->x[1];
    float v2 = ekf->x[2];

    /* Get parameters */
    float r0 = interpolate_lut(soc, ekf->r0_lut, ekf->r0_lut_size);
    float ocv = interpolate_lut(soc, ekf->ocv_soc_lut, ekf->ocv_lut_size);

    /* Measurement model: V = OCV - I*R0 - V1 - V2 */
    float v_pred = ocv - current_a * r0 - v1 - v2;

    /* Innovation (measurement residual) */
    float y = voltage_meas - v_pred;

    /* Measurement Jacobian H = [dOCV/dSOC, -1, -1] */
    float h[3];
    h[0] = docv_dsoc(ekf, soc);
    h[1] = -1.0f;
    h[2] = -1.0f;

    /* Innovation covariance S = H * P * H^T + R */
    float s = ekf->R;
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            s += h[i] * ekf->P[i][j] * h[j];
        }
    }

    /* Kalman gain K = P * H^T / S */
    float k[3];
    for (int i = 0; i < 3; i++) {
        k[i] = 0.0f;
        for (int j = 0; j < 3; j++) {
            k[i] += ekf->P[i][j] * h[j];
        }
        k[i] /= s;
    }

    /* Update state: x = x + K * y */
    for (int i = 0; i < 3; i++) {
        ekf->x[i] += k[i] * y;
    }

    /* Clamp SOC */
    if (ekf->x[0] > 1.0f) ekf->x[0] = 1.0f;
    if (ekf->x[0] < 0.0f) ekf->x[0] = 0.0f;

    /* Update covariance: P = (I - K*H) * P */
    float ikh[3][3];
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            ikh[i][j] = (i == j) ? 1.0f : 0.0f;
            for (int l = 0; l < 3; l++) {
                ikh[i][j] -= k[i] * h[l];
            }
        }
    }

    float P_new[3][3] = {0};
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            for (int l = 0; l < 3; l++) {
                P_new[i][j] += ikh[i][l] * ekf->P[l][j];
            }
        }
    }

    /* Copy back */
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            ekf->P[i][j] = P_new[i][j];
        }
    }
}

float ekf_soc_get(const SocEkf_t* ekf) {
    return ekf->x[0];
}

float ekf_soc_get_uncertainty(const SocEkf_t* ekf) {
    /* Return standard deviation of SOC estimate */
    return sqrtf(ekf->P[0][0]);
}
```

## State of Health (SOH) Prediction

### Semi-Empirical Aging Model

```c
/* SOH estimator with combined calendar and cycle aging */
typedef struct {
    /* Current health state */
    float current_capacity_ah;
    float current_resistance_ohm;

    /* Nominal values */
    float nominal_capacity_ah;
    float initial_resistance_ohm;

    /* Aging model parameters */
    float calendar_aging_rate;    /* per day */
    float cycle_aging_rate;       /* per EFC */
    float activation_energy;      /* eV */
    float temp_ref_c;             /* Reference temperature */

    /* Cycle accumulation */
    float equivalent_full_cycles;
    uint32_t total_cycles;

    /* Time tracking */
    uint32_t start_timestamp_s;
} SohEstimator_t;

/* Cycle data for aging calculation */
typedef struct {
    float depth_of_discharge;     /* 0.0 to 1.0 */
    float avg_current_rate;       /* C-rate */
    float avg_temperature_c;
    uint32_t timestamp_s;
} CycleData_t;

void soh_estimator_init(SohEstimator_t* est,
                         float nominal_capacity_ah,
                         float initial_resistance_ohm) {
    est->nominal_capacity_ah = nominal_capacity_ah;
    est->current_capacity_ah = nominal_capacity_ah;
    est->initial_resistance_ohm = initial_resistance_ohm;
    est->current_resistance_ohm = initial_resistance_ohm;

    /* Aging parameters (calibrated for NMC cells) */
    est->calendar_aging_rate = 2.5e-5f;   /* 2.5% per 1000 days */
    est->cycle_aging_rate = 5.0e-5f;      /* 5% per 1000 EFC */
    est->activation_energy = 0.3f;        /* eV */
    est->temp_ref_c = 25.0f;

    est->equivalent_full_cycles = 0.0f;
    est->total_cycles = 0;
    est->start_timestamp_s = 0;
}

/* Arrhenius temperature factor for aging acceleration */
static float arrhenius_factor(float temp_c, float temp_ref_c, float activation_ev) {
    const float k_boltzmann = 8.617e-5f;  /* eV/K */
    float temp_k = temp_c + 273.15f;
    float temp_ref_k = temp_ref_c + 273.15f;

    return expf((activation_ev / k_boltzmann) * (1.0f / temp_ref_k - 1.0f / temp_k));
}

/* Calculate Equivalent Full Cycle with stress factors */
static float calculate_efc(const CycleData_t* cycle,
                            float temp_ref_c,
                            float activation_ev) {
    /* Base EFC from DOD */
    float base_efc = cycle->depth_of_discharge;

    /* DOD stress factor (Wöhler curve concept) */
    float dod_stress = powf(cycle->depth_of_discharge, 1.5f);

    /* C-rate stress factor */
    float c_rate_stress = 1.0f + 0.5f * fabsf(cycle->avg_current_rate - 1.0f);

    /* Temperature stress factor (Arrhenius) */
    float temp_stress = arrhenius_factor(cycle->avg_temperature_c,
                                          temp_ref_c, activation_ev);

    return base_efc * dod_stress * c_rate_stress * temp_stress;
}

void soh_estimator_add_cycle(SohEstimator_t* est,
                              const CycleData_t* cycle) {
    /* Calculate equivalent full cycle */
    float efc = calculate_efc(cycle, est->temp_ref_c, est->activation_energy);
    est->equivalent_full_cycles += efc;
    est->total_cycles++;

    /* Initialize start time if not set */
    if (est->start_timestamp_s == 0) {
        est->start_timestamp_s = cycle->timestamp_s;
    }

    /* Update capacity based on aging */
    /* Cycle aging */
    float cycle_fade = est->cycle_aging_rate * est->equivalent_full_cycles;

    /* Calendar aging */
    uint32_t elapsed_s = cycle->timestamp_s - est->start_timestamp_s;
    float days_elapsed = (float)elapsed_s / 86400.0f;
    float calendar_fade = est->calendar_aging_rate * days_elapsed;

    /* Combined fade */
    float total_fade = cycle_fade + calendar_fade;

    /* Update capacity (minimum 60% of nominal) */
    est->current_capacity_ah = est->nominal_capacity_ah * (1.0f - total_fade);
    if (est->current_capacity_ah < est->nominal_capacity_ah * 0.6f) {
        est->current_capacity_ah = est->nominal_capacity_ah * 0.6f;
    }

    /* Update resistance (increases as SOH decreases) */
    float soh = est->current_capacity_ah / est->nominal_capacity_ah;
    float resistance_multiplier = 1.0f / sqrtf(soh);
    est->current_resistance_ohm = est->initial_resistance_ohm * resistance_multiplier;
}

float soh_estimator_get_soh(const SohEstimator_t* est) {
    return est->current_capacity_ah / est->nominal_capacity_ah;
}

/* Predict Remaining Useful Life */
typedef struct {
    float remaining_efc;
    float remaining_days;
    bool valid;
} RulPrediction_t;

RulPrediction_t soh_estimator_predict_rul(const SohEstimator_t* est,
                                           float eol_threshold) {
    RulPrediction_t result = {0};

    float current_soh = soh_estimator_get_soh(est);

    /* Already at or below EOL */
    if (current_soh <= eol_threshold) {
        result.remaining_efc = 0.0f;
        result.remaining_days = 0.0f;
        result.valid = true;
        return result;
    }

    /* Capacity fade remaining to EOL */
    float fade_remaining = current_soh - eol_threshold;

    /* Estimate fade per EFC */
    if (est->equivalent_full_cycles > 0.0f) {
        float fade_per_efc = (1.0f - current_soh) / est->equivalent_full_cycles;
        result.remaining_efc = fade_remaining / (fade_per_efc + 1e-10f);
    } else {
        result.remaining_efc = 1e6f;  /* Unknown - large number */
    }

    /* Estimate remaining days based on recent usage */
    /* (Assumes ~1 EFC per day for typical usage) */
    if (est->total_cycles > 10) {
        float efc_per_day = est->equivalent_full_cycles /
                            ((float)est->total_cycles + 1e-10f);
        result.remaining_days = result.remaining_efc / (efc_per_day + 1e-10f);
    } else {
        result.remaining_days = 1e6f;  /* Unknown */
    }

    result.valid = true;
    return result;
}
```

## Cell Balancing

### Passive Balancing Controller

```c
/* Passive cell balancing with resistor dissipation */
typedef struct {
    uint8_t num_cells;
    float balance_threshold_v;    /* Start balancing when delta V > threshold */
    float target_delta_v;         /* Target voltage difference */
    float balance_current_a;      /* Balancing current (fixed for passive) */
    uint32_t balance_mask;        /* Bitmask: 1 = balancing active */
} PassiveBalancer_t;

void passive_balancer_init(PassiveBalancer_t* bal,
                            uint8_t num_cells,
                            float balance_threshold_v,
                            float balance_current_a) {
    bal->num_cells = num_cells;
    bal->balance_threshold_v = balance_threshold_v;
    bal->target_delta_v = 0.01f;  /* 10 mV target */
    bal->balance_current_a = balance_current_a;
    bal->balance_mask = 0;
}

/* Calculate which cells need balancing */
uint32_t passive_balancer_compute(PassiveBalancer_t* bal,
                                   const float* cell_voltages) {
    /* Calculate mean voltage */
    float sum = 0.0f;
    for (uint8_t i = 0; i < bal->num_cells; i++) {
        sum += cell_voltages[i];
    }
    float mean_voltage = sum / (float)bal->num_cells;

    /* Determine balancing mask */
    uint32_t mask = 0;
    float max_delta = 0.0f;

    for (uint8_t i = 0; i < bal->num_cells; i++) {
        float delta = cell_voltages[i] - mean_voltage;
        if (delta > bal->balance_threshold_v) {
            mask |= (1U << i);
            if (delta > max_delta) {
                max_delta = delta;
            }
        }
    }

    bal->balance_mask = mask;
    return mask;
}

/* Check if balancing is complete */
bool passive_balancer_is_complete(const PassiveBalancer_t* bal,
                                   const float* cell_voltages) {
    float min_v = cell_voltages[0];
    float max_v = cell_voltages[0];

    for (uint8_t i = 1; i < bal->num_cells; i++) {
        if (cell_voltages[i] < min_v) min_v = cell_voltages[i];
        if (cell_voltages[i] > max_v) max_v = cell_voltages[i];
    }

    return (max_v - min_v) <= bal->target_delta_v;
}

/* Estimate time to complete balancing */
float passive_balancer_time_to_complete(const PassiveBalancer_t* bal,
                                         const float* cell_voltages,
                                         float cell_capacity_ah) {
    float max_v = cell_voltages[0];
    float min_v = cell_voltages[0];

    for (uint8_t i = 1; i < bal->num_cells; i++) {
        if (cell_voltages[i] > max_v) max_v = cell_voltages[i];
        if (cell_voltages[i] < min_v) min_v = cell_voltages[i];
    }

    float voltage_to_remove = max_v - min_v - bal->target_delta_v;
    if (voltage_to_remove <= 0.0f) {
        return 0.0f;
    }

    /* Simplified: time = delta_Q / I_balance */
    /* delta_Q approximated from voltage difference and cell impedance */
    float estimated_charge_imbalance_ah = voltage_to_remove * cell_capacity_ah / 0.5f;
    float time_hours = estimated_charge_imbalance_ah / bal->balance_current_a;

    return time_hours * 60.0f * 60.0f;  /* Return seconds */
}
```

### Active Balancing (Capacitor Shuttle)

```c
/* Active cell balancing with capacitor charge shuttling */
typedef struct {
    uint8_t num_cells;
    float balance_threshold_v;
    float max_balance_current_a;
    uint8_t source_cell;        /* Cell to transfer FROM */
    uint8_t target_cell;        /* Cell to transfer TO */
    bool balancing_active;
} ActiveBalancer_t;

void active_balancer_init(ActiveBalancer_t* bal,
                           uint8_t num_cells,
                           float max_balance_current_a) {
    bal->num_cells = num_cells;
    bal->balance_threshold_v = 0.02f;  /* 20 mV threshold for active */
    bal->max_balance_current_a = max_balance_current_a;
    bal->source_cell = 0;
    bal->target_cell = 0;
    bal->balancing_active = false;
}

/* Determine optimal charge transfer for active balancing */
bool active_balancer_compute(ActiveBalancer_t* bal,
                              const float* cell_voltages,
                              uint8_t* from_cell,
                              uint8_t* to_cell,
                              float* duty_cycle) {
    /* Find highest and lowest cells */
    uint8_t highest = 0, lowest = 0;
    float max_v = cell_voltages[0];
    float min_v = cell_voltages[0];

    for (uint8_t i = 1; i < bal->num_cells; i++) {
        if (cell_voltages[i] > max_v) {
            max_v = cell_voltages[i];
            highest = i;
        }
        if (cell_voltages[i] < min_v) {
            min_v = cell_voltages[i];
            lowest = i;
        }
    }

    /* Check if balancing needed */
    float delta_v = max_v - min_v;
    if (delta_v <= bal->balance_threshold_v) {
        bal->balancing_active = false;
        return false;
    }

    /* Set transfer parameters */
    bal->source_cell = highest;
    bal->target_cell = lowest;
    bal->balancing_active = true;

    /* Calculate duty cycle (proportional to voltage difference) */
    /* Higher delta = higher duty cycle = more charge transfer */
    float normalized_delta = (delta_v - bal->balance_threshold_v) / 0.1f;
    if (normalized_delta > 1.0f) normalized_delta = 1.0f;

    *from_cell = highest;
    *to_cell = lowest;
    *duty_cycle = normalized_delta * 0.8f;  /* Max 80% duty cycle */

    return true;
}
```

## Safety Mechanisms

### Cell Voltage Plausibility Check

```c
/* ISO 26262 safety mechanism: Cross-check cell voltages */
typedef struct {
    float max_cell_voltage_v;
    float min_cell_voltage_v;
    float max_delta_v;
    float max_rate_of_change_v_s;
    float prev_avg_voltage;
} CellVoltageMonitor_t;

typedef enum {
    CELL_VOLT_OK,
    CELL_VOLT_OVERVOLTAGE,
    CELL_VOLT_UNDERVOLTAGE,
    CELL_VOLT_MISMATCH,
    CELL_VOLT_SENSOR_FAULT,
    CELL_VOLT_RATE_FAULT
} CellVoltageStatus_t;

CellVoltageStatus_t cell_voltage_monitor_check(
    CellVoltageMonitor_t* mon,
    const float* cell_voltages,
    uint8_t num_cells,
    float dt_s) {

    /* Find min, max, and average */
    float min_v = cell_voltages[0];
    float max_v = cell_voltages[0];
    float sum_v = 0.0f;
    uint8_t fault_count = 0;

    for (uint8_t i = 0; i < num_cells; i++) {
        /* Check for sensor fault (out of ADC range) */
        if (cell_voltages[i] < 0.5f || cell_voltages[i] > 5.0f) {
            fault_count++;
        }

        if (cell_voltages[i] < min_v) min_v = cell_voltages[i];
        if (cell_voltages[i] > max_v) max_v = cell_voltages[i];
        sum_v += cell_voltages[i];
    }

    /* Multiple sensor faults */
    if (fault_count >= 2) {
        return CELL_VOLT_SENSOR_FAULT;
    }

    float avg_v = sum_v / (float)num_cells;

    /* Over/under voltage check */
    if (max_v > mon->max_cell_voltage_v) {
        return CELL_VOLT_OVERVOLTAGE;
    }
    if (min_v < mon->min_cell_voltage_v) {
        return CELL_VOLT_UNDERVOLTAGE;
    }

    /* Cell-to-cell mismatch check */
    float delta_v = max_v - min_v;
    if (delta_v > mon->max_delta_v) {
        return CELL_VOLT_MISMATCH;
    }

    /* Rate of change check (all cells should change together) */
    float delta_avg = fabsf(avg_v - mon->prev_avg_voltage);
    float max_rate = mon->max_rate_of_change_v_s * dt_s;
    if (delta_avg > max_rate) {
        return CELL_VOLT_RATE_FAULT;
    }

    mon->prev_avg_voltage = avg_v;
    return CELL_VOLT_OK;
}
```

## BMS State Machine

```c
/* BMS main state machine per ISO 26262 */
typedef enum {
    BMS_STATE_INIT,
    BMS_STATE_STANDBY,
    BMS_STATE_PRECHARGE,
    BMS_STATE_READY,
    BMS_STATE_CHARGING,
    BMS_STATE_DISCHARGING,
    BMS_STATE_FAULT,
    BMS_STATE_SAFE_SHUTDOWN
} BmsState_t;

typedef enum {
    BMS_FAULT_NONE = 0,
    BMS_FAULT_OVERVOLTAGE = (1 << 0),
    BMS_FAULT_UNDERVOLTAGE = (1 << 1),
    BMS_FAULT_OVERCURRENT = (1 << 2),
    BMS_FAULT_OVERTEMP = (1 << 3),
    BMS_FAULT_ISOLOW = (1 << 4),
    BMS_FAULT_SENSOR_FAULT = (1 << 5)
} BmsFault_t;

BmsState_t bms_state_machine(BmsState_t current_state,
                              BmsFault_t active_faults,
                              bool ignition_on,
                              bool precharge_complete,
                              bool charger_connected) {
    switch (current_state) {
        case BMS_STATE_INIT:
            if (active_faults == BMS_FAULT_NONE) {
                return BMS_STATE_STANDBY;
            }
            return BMS_STATE_FAULT;

        case BMS_STATE_STANDBY:
            if (!ignition_on && !charger_connected) {
                return BMS_STATE_INIT;
            }
            if (ignition_on && precharge_complete) {
                return BMS_STATE_READY;
            }
            if (charger_connected) {
                return BMS_STATE_CHARGING;
            }
            if (active_faults != BMS_FAULT_NONE) {
                return BMS_STATE_FAULT;
            }
            break;

        case BMS_STATE_PRECHARGE:
            if (precharge_complete) {
                return BMS_STATE_READY;
            }
            if (active_faults != BMS_FAULT_NONE) {
                return BMS_STATE_FAULT;
            }
            break;

        case BMS_STATE_READY:
        case BMS_STATE_DISCHARGING:
            if (!ignition_on) {
                return BMS_STATE_STANDBY;
            }
            if (active_faults != BMS_FAULT_NONE) {
                return BMS_STATE_FAULT;
            }
            if (charger_connected && !ignition_on) {
                return BMS_STATE_CHARGING;
            }
            break;

        case BMS_STATE_CHARGING:
            if (!charger_connected) {
                return BMS_STATE_STANDBY;
            }
            if (active_faults != BMS_FAULT_NONE) {
                return BMS_STATE_FAULT;
            }
            break;

        case BMS_STATE_FAULT:
            /* Fault state requires explicit reset */
            if (active_faults == BMS_FAULT_NONE && !ignition_on) {
                return BMS_STATE_STANDBY;
            }
            break;

        default:
            return BMS_STATE_FAULT;
    }

    return current_state;
}

/* Safe state entry action */
void bms_enter_safe_state(void) {
    /* ISO 26262 safe state: Open contactors, disable HV */
    open_main_contactor();
    open_precharge_contactor();
    disable_hv_interlock();

    /* Store fault information */
    store_freeze_frame();

    /* Notify vehicle via CAN */
    send_bms_status_can(0x00, BMS_STATUS_SAFE_STATE);
}
```

## Approach

1. **Define battery parameters** from cell datasheet and pack configuration
   - OCV-SOC curve at multiple temperatures
   - Internal resistance (R0, R1, C1, R2, C2)
   - Maximum charge/discharge currents
   - Temperature operating limits

2. **Design SOC/SOH estimators** following Kalman filter patterns
   - Tune process and measurement noise covariances
   - Validate against reference discharge cycles
   - Implement fault detection for sensor plausibility

3. **Implement cell balancing** strategy based on pack requirements
   - Passive for cost-sensitive applications (< 2 hours balance time)
   - Active for large packs with high energy efficiency requirements

4. **Validate per ISO 26262** with fault injection testing
   - Inject sensor faults (stuck, offset, noise)
   - Verify safe state transitions within FTTI
   - Document diagnostic coverage (>90% for ASIL C/D)

## Deliverables

- SOC/SOH algorithm specification (Simulink model + C code)
- Cell balancing controller implementation
- Safety manual with ASIL decomposition
- Test report (MIL/SIL/HIL with fault injection coverage)
- Calibration parameter files (.a2l format)

## Related Context
- @context/skills/safety/iso-26262-overview.md
- @context/skills/security/iso-21434-compliance.md
- @context/skills/powertrain/thermal-management.md
- @context/skills/diagnostics/uds-iso14229.md
- @context/skills/autosar/classic-platform.md

## Tools Required
- MATLAB/Simulink (algorithm development)
- ATI Vision or ETAS INCA (calibration)
- Vector CANoe (HIL testing)
- Battery cycler (Arbin, Maccor for cell characterization)
- Thermal chamber (temperature-dependent testing)
