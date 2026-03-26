---
name: powertrain-battery-management
description: "Use when: Skill: Battery Management for Automotive Powertrain topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: Battery Management for Automotive Powertrain

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/powertrain/battery-management.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate
- User asks about battery management system (BMS) design or implementation
- User needs SOC/SOH estimation algorithms for lithium-ion batteries
- User requests cell balancing strategies or thermal management
- User is developing BMS for EV/HEV applications
- User needs AUTOSAR implementation patterns for battery control
- User asks about ISO 26262 safety mechanisms for high-voltage batteries

## Standards Compliance
- ISO 26262:2018 (Functional Safety) - ASIL C/D for contactor control
- ASPICE Level 3 - Model-based development process
- AUTOSAR 4.4 - Battery domain architecture
- ISO 21434:2021 (Cybersecurity) - BMS diagnostic protection
- SAE J1772 - EV charging communication
- SAE J1979 - OBD-II battery PIDs
- UN GTR No. 20 - Battery durability and safety
- ISO 12405 - Battery pack test specifications

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Cell voltage | 2.5-4.2 | V (Li-ion NMC) |
| Pack voltage | 200-800 | V |
| SOC | 0-100 | percentage |
| SOH | 0-100 | percentage |
| Cell temperature | -40 to 60 | °C |
| Current | -500 to +500 | A (negative=discharge) |
| Balance threshold | 5-50 | mV |
| Insulation resistance | >500 | Ω/V |
| Contactor precharge time | 100-500 | ms |

## BMS Architecture

```
+----------------------------------------------------------+
|              Battery Management System                    |
|  +------------------+  +------------------+              |
|  |  SOC Estimator   |  |  SOH Estimator   |              |
|  +------------------+  +------------------+              |
|           |                     |                        |
|  +------------------+  +------------------+              |
|  |  Cell Balancing  |  |  Thermal Mgmt    |             |
|  +------------------+  +------------------+              |
|           |                     |                        |
|  +------------------+  +------------------+              |
|  |  Contactor Ctrl  |  |  Insulation Mon  |             |
|  +------------------+  +------------------+              |
+--------------------------|-------------------------------+
                           |
         +-----------------+-----------------+
         |                 |                 |
+--------v--------+ +------v------+ +--------v--------+
|  Cell Monitor   | | Current Sns | | Temp Sensors    |
|  (96 channels)  | | (Hall/Shunt)| | (NTC/PT1000)    |
+-----------------+ +-------------+ +-----------------+
```

## SOC Estimation

### Coulomb Counting with OCV Correction

```c
/* State of Charge estimation - combined method */
typedef struct {
    float soc_percent;           /* Current SOC estimate */
    float coulomb_soc;           /* Coulomb counting result */
    float ocv_soc;               /* OCV-based correction */
    float cell_voltage_v;        /* Average cell voltage */
    float pack_current_a;        /* Pack current (positive=charge) */
    float temperature_c;         /* Average temperature */
    uint32_t time_since_rest_ms; /* Time since last rest */
} SocEstimator_t;

/* Main SOC update - 1ms cycle */
void soc_update(SocEstimator_t* est, float dt_s) {
    /* Coulomb counting: SOC += (I * dt) / Capacity */
    const float capacity_ah = BATTERY_PACK_CAPACITY_AH;
    const float delta_soc = (est->pack_current_a * dt_s) / (capacity_ah * 3600.0f);
    est->coulomb_soc += delta_soc * 100.0f;  /* Convert to percentage */

    /* Clamp coulomb SOC */
    est->coulomb_soc = fmaxf(0.0f, fminf(100.0f, est->coulomb_soc));

    /* OCV correction only at rest (|I| < threshold for >30 min) */
    if (fabsf(est->pack_current_a) < REST_CURRENT_THRESHOLD_A &&
        est->time_since_rest_ms > MIN_REST_TIME_MS) {

        est->ocv_soc = soc_from_ocv(est->cell_voltage_v, est->temperature_c);

        /* Blend coulomb counting with OCV (trust OCV more at rest) */
        est->soc_percent = est->coulomb_soc * 0.9f + est->ocv_soc * 0.1f;
    } else {
        /* During operation, trust coulomb counting primarily */
        est->soc_percent = est->coulomb_soc;
        est->time_since_rest_ms = 0U;
    }
}

/* OCV-SOC lookup with temperature compensation */
static const float s_ocv_table[][2] = {
    /* OCV (V), SOC (%) - typical NMC chemistry */
    {3.0f,   0.0f},
    {3.5f,  10.0f},
    {3.65f, 20.0f},
    {3.75f, 30.0f},
    {3.85f, 40.0f},
    {3.95f, 50.0f},
    {4.0f,  60.0f},
    {4.05f, 70.0f},
    {4.1f,  80.0f},
    {4.15f, 90.0f},
    {4.2f, 100.0f}
};

float soc_from_ocv(float ocv_v, float temperature_c) {
    /* Temperature compensation: OCV shifts ~1mV/°C */
    const float temp_comp = (temperature_c - 25.0f) * 0.001f;
    const float compensated_ocv = ocv_v - temp_comp;

    /* Linear interpolation in OCV table */
    for (size_t i = 0; i < ARRAY_SIZE(s_ocv_table) - 1; i++) {
        if (compensated_ocv >= s_ocv_table[i][0] &&
            compensated_ocv <= s_ocv_table[i+1][0]) {

            const float ratio = (compensated_ocv - s_ocv_table[i][0]) /
                                (s_ocv_table[i+1][0] - s_ocv_table[i][0]);
            return s_ocv_table[i][1] + ratio *
                   (s_ocv_table[i+1][1] - s_ocv_table[i][1]);
        }
    }
    return (compensated_ocv < s_ocv_table[0][0]) ? 0.0f : 100.0f;
}
```

### Extended Kalman Filter for SOC

```c
/* EKF-based SOC estimation for improved accuracy */
typedef struct {
    float x[2];      /* State: [SOC, V_rc] */
    float P[2][2];   /* State covariance */
    float Q[2][2];   /* Process noise */
    float R;         /* Measurement noise */
} SocEkf_t;

/* State transition model */
static void ekf_predict(SocEkf_t* ekf, float current_a, float dt_s) {
    const float capacity_ah = BATTERY_PACK_CAPACITY_AH;

    /* State prediction: x[k|k-1] = f(x[k-1], u) */
    const float soc_dot = -current_a / (capacity_ah * 3600.0f);
    ekf->x[0] += soc_dot * dt_s * 100.0f;  /* SOC change in % */
    ekf->x[1] *= expf(-dt_s / RC_TIME_CONSTANT_S);  /* V_rc decay */

    /* Jacobian F = df/dx */
    const float F[2][2] = {
        {1.0f, 0.0f},
        {0.0f, expf(-dt_s / RC_TIME_CONSTANT_S)}
    };

    /* Covariance prediction: P[k|k-1] = F*P*F' + Q */
    float P_pred[2][2];
    for (int i = 0; i < 2; i++) {
        for (int j = 0; j < 2; j++) {
            P_pred[i][j] = ekf->Q[i][j];
            for (int k = 0; k < 2; k++) {
                for (int l = 0; l < 2; l++) {
                    P_pred[i][j] += F[i][k] * ekf->P[k][l] * F[j][l];
                }
            }
        }
    }
    memcpy(ekf->P, P_pred, sizeof(ekf->P));
}

/* Measurement update */
static void ekf_update(SocEkf_t* ekf, float measured_voltage_v, float current_a) {
    /* Measurement model: h(x) = OCV(SOC) + V_rc + I*R */
    const float ocv = ocv_from_soc(ekf->x[0]);
    const float predicted_voltage = ocv + ekf->x[1] + current_a * CELL_RESISTANCE_MOHM / 1000.0f;

    /* Innovation: y = z - h(x) */
    const float innovation = measured_voltage_v - predicted_voltage;

    /* Jacobian H = dh/dx = [dOCV/dSOC, 1] */
    const float dOcv_dSoc = compute_ocv_gradient(ekf->x[0]);
    const float H[2] = {dOcv_dSoc, 1.0f};

    /* Innovation covariance: S = H*P*H' + R */
    float S = ekf->R;
    for (int i = 0; i < 2; i++) {
        for (int j = 0; j < 2; j++) {
            S += H[i] * ekf->P[i][j] * H[j];
        }
    }

    /* Kalman gain: K = P*H' / S */
    float K[2];
    for (int i = 0; i < 2; i++) {
        K[i] = 0.0f;
        for (int j = 0; j < 2; j++) {
            K[i] += ekf->P[i][j] * H[j];
        }
        K[i] /= S;
    }

    /* State update: x = x + K*y */
    for (int i = 0; i < 2; i++) {
        ekf->x[i] += K[i] * innovation;
    }

    /* Covariance update: P = (I - K*H)*P */
    float I_KH[2][2] = {{1.0f, 0.0f}, {0.0f, 1.0f}};
    for (int i = 0; i < 2; i++) {
        for (int j = 0; j < 2; j++) {
            for (int k = 0; k < 2; k++) {
                I_KH[i][j] -= K[i] * H[k];
            }
        }
    }

    float P_updated[2][2];
    for (int i = 0; i < 2; i++) {
        for (int j = 0; j < 2; j++) {
            P_updated[i][j] = 0.0f;
            for (int k = 0; k < 2; k++) {
                P_updated[i][j] += I_KH[i][k] * ekf->P[k][j];
            }
        }
    }
    memcpy(ekf->P, P_updated, sizeof(ekf->P));
}
```

## SOH Estimation

### Capacity Fade Method

```c
/* State of Health - capacity-based estimation */
typedef struct {
    float nominal_capacity_ah;    /* Rated capacity at BOL */
    float current_capacity_ah;    /* Estimated current capacity */
    float soh_percent;            /* SOH = current/nominal * 100 */
    uint32_t full_charge_cycles;  /* Cycle count for tracking */
    float initial_resistance_mohm; /* Resistance at BOL */
    float current_resistance_mohm; /* Current internal resistance */
} SohEstimator_t;

/* Capacity estimation via coulomb counting over full charge */
void soh_update_capacity(SohEstimator_t* soh,
                         float soc_start, float soc_end,
                         float charged_ah) {
    /* Only update after significant SOC change (>50%) */
    const float soc_delta = fabsf(soc_end - soc_start);
    if (soc_delta < 50.0f) {
        return;
    }

    /* Capacity = charged_AH / SOC_delta */
    const float estimated_capacity = charged_ah / (soc_delta / 100.0f);

    /* Low-pass filter to smooth estimates */
    soh->current_capacity_ah =
        soh->current_capacity_ah * 0.9f + estimated_capacity * 0.1f;

    /* Update SOH */
    soh->soh_percent = (soh->current_capacity_ah / soh->nominal_capacity_ah) * 100.0f;
}

/* Resistance growth method (complementary to capacity) */
void soh_update_resistance(SohEstimator_t* soh,
                           float delta_v, float current_a) {
    /* R = ΔV / I (during current step) */
    if (fabsf(current_a) < 10.0f) {
        return;  /* Current too low for accurate R measurement */
    }

    const float measured_resistance = fabsf(delta_v / current_a) * 1000.0f;  /* mΩ */

    /* Low-pass filter */
    soh->current_resistance_mohm =
        soh->current_resistance_mohm * 0.95f + measured_resistance * 0.05f;

    /* Resistance-based SOH (resistance doubles at EOL typically) */
    const float resistance_soh =
        100.0f * (1.0f - (soh->current_resistance_mohm - soh->initial_resistance_mohm) /
                            soh->initial_resistance_mohm);

    /* Use minimum of capacity SOH and resistance SOH */
    soh->soh_percent = fminf(soh->soh_percent, resistance_soh);
}
```

## Cell Balancing

### Passive (Dissipative) Balancing

```c
/* Passive cell balancing - bleed excess charge from high cells */
typedef struct {
    uint16_t cell_voltages_mv[96];  /* 96S battery pack */
    uint8_t balance_switch[96];     /* 0=off, 1=on */
    uint16_t balance_threshold_mv;  /* Start balancing if delta > threshold */
    uint16_t hysteresis_mv;         /* Hysteresis to prevent chattering */
    uint8_t balancing_active;       /* Global balancing enable */
} CellBalancer_t;

/* Balance control algorithm - 100ms cycle */
void balance_control(CellBalancer_t* bal) {
    /* Find min and max cell voltages */
    uint16_t min_cell_mv = UINT16_MAX;
    uint16_t max_cell_mv = 0;
    uint8_t max_cell_idx = 0;

    for (uint8_t i = 0; i < 96; i++) {
        if (bal->cell_voltages_mv[i] < min_cell_mv) {
            min_cell_mv = bal->cell_voltages_mv[i];
        }
        if (bal->cell_voltages_mv[i] > max_cell_mv) {
            max_cell_mv = bal->cell_voltages_mv[i];
            max_cell_idx = i;
        }
    }

    const uint16_t delta_mv = max_cell_mv - min_cell_mv;

    /* Enable balancing if delta exceeds threshold with hysteresis */
    if (delta_mv > (bal->balance_threshold_mv + bal->hysteresis_mv)) {
        bal->balancing_active = 1;
    } else if (delta_mv < bal->balance_threshold_mv) {
        bal->balancing_active = 0;
    }

    /* Clear all switches first */
    memset(bal->balance_switch, 0, sizeof(bal->balance_switch));

    /* Enable bleed resistors for cells above average */
    if (bal->balancing_active) {
        const uint16_t avg_cell_mv = (min_cell_mv + max_cell_mv) / 2U;
        for (uint8_t i = 0; i < 96; i++) {
            if (bal->cell_voltages_mv[i] > avg_cell_mv) {
                bal->balance_switch[i] = 1;
            }
        }
    }
}

/* Thermal management for balancing - prevent overheating */
void balance_thermal_limit(CellBalancer_t* bal, float temp_c) {
    /* Reduce balance current at high temperature */
    if (temp_c > 45.0f) {
        /* Disable balancing above 45°C */
        bal->balancing_active = 0;
        memset(bal->balance_switch, 0, sizeof(bal->balance_switch));
    } else if (temp_c > 35.0f) {
        /* Reduce duty cycle between 35-45°C */
        const uint8_t duty_cycle = (uint8_t)((45.0f - temp_c) * 10.0f);
        apply_pwm_duty_cycle(bal->balance_switch, duty_cycle);
    }
}
```

### Active (Non-Dissipative) Balancing

```c
/* Active cell balancing - transfer charge between cells */
typedef enum {
    BALANCE_MODE_IDLE,
    BALANCE_MODE_CELL_TO_PACK,   /* High cell -> Pack bus */
    BALANCE_MODE_PACK_TO_CELL,   /* Pack bus -> Low cell */
    BALANCE_MODE_CELL_TO_CELL    /* High cell -> Low cell (bidirectional) */
} ActiveBalanceMode_t;

typedef struct {
    uint16_t cell_voltages_mv[96];
    ActiveBalanceMode_t mode;
    uint8_t source_cell;    /* Cell to transfer FROM */
    uint8_t dest_cell;      /* Cell to transfer TO */
    uint16_t target_current_ma;  /* Balance current setpoint */
    float actual_current_a;      /* Measured transfer current */
} ActiveBalancer_t;

/* Active balancing scheduler */
void active_balance_schedule(ActiveBalancer_t* bal) {
    /* Find highest and lowest cells */
    uint8_t high_cell = 0, low_cell = 0;
    uint16_t max_mv = 0, min_mv = UINT16_MAX;

    for (uint8_t i = 0; i < 96; i++) {
        if (bal->cell_voltages_mv[i] > max_mv) {
            max_mv = bal->cell_voltages_mv[i];
            high_cell = i;
        }
        if (bal->cell_voltages_mv[i] < min_mv) {
            min_mv = bal->cell_voltages_mv[i];
            low_cell = i;
        }
    }

    /* Enable active balancing if delta > 20mV (more aggressive than passive) */
    if ((max_mv - min_mv) > 20) {
        bal->mode = BALANCE_MODE_CELL_TO_CELL;
        bal->source_cell = high_cell;
        bal->dest_cell = low_cell;
        bal->target_current_ma = 500;  /* 500mA balance current */
    } else {
        bal->mode = BALANCE_MODE_IDLE;
    }
}
```

## Thermal Management

### Air Cooling Strategy

```c
/* Battery thermal management with air cooling */
typedef struct {
    float cell_temp_c;           /* Average cell temperature */
    float max_cell_temp_c;       /* Maximum single cell temp */
    uint8_t fan_speed_percent;   /* 0-100% */
    uint8_t ac_compressor_on;    /* A/C for cooling */
    float coolant_flow_rate;     /* L/min for liquid cooling */
} ThermalManager_t;

/* Thermal control - 1s cycle */
void thermal_control(ThermalManager_t* therm) {
    /* Cooling stages */
    if (therm->max_cell_temp_c > 45.0f) {
        /* Critical: Max cooling */
        therm->fan_speed_percent = 100;
        therm->ac_compressor_on = 1;
        therm->coolant_flow_rate = 10.0f;  /* Max flow */
    } else if (therm->max_cell_temp_c > 38.0f) {
        /* High: Active cooling */
        therm->fan_speed_percent = 80;
        therm->ac_compressor_on = 1;
        therm->coolant_flow_rate = 7.0f;
    } else if (therm->max_cell_temp_c > 32.0f) {
        /* Medium: Fan only */
        therm->fan_speed_percent = 60;
        therm->ac_compressor_on = 0;
        therm->coolant_flow_rate = 5.0f;
    } else if (therm->max_cell_temp_c > 25.0f) {
        /* Low: Minimal cooling */
        therm->fan_speed_percent = 30;
        therm->ac_compressor_on = 0;
        therm->coolant_flow_rate = 3.0f;
    } else {
        /* Off: No cooling needed */
        therm->fan_speed_percent = 0;
        therm->ac_compressor_on = 0;
        therm->coolant_flow_rate = 0.0f;
    }

    /* Heating in cold weather (PTC heater) */
    if (therm->cell_temp_c < 10.0f) {
        therm->ac_compressor_on = 0;  /* Disable A/C */
        enable_ptc_heater(50.0f);      /* 50% heater power */
    }
}
```

## Contactor Control

### Precharge and Safety Sequence

```c
/* High-voltage contactor control with precharge */
typedef enum {
    HV_STATE_OFF,
    HV_STATE_PRECHARGING,
    HV_STATE_PRECHARGE_COMPLETE,
    HV_STATE_ON,
    HV_STATE_DISCHARGING,
    HV_STATE_FAULT
} HvState_t;

typedef struct {
    HvState_t state;
    uint32_t precharge_start_ms;
    float dc_link_voltage_v;
    float pack_voltage_v;
    uint8_t main_positive;      /* Main positive contactor */
    uint8_t main_negative;      /* Main negative contactor */
    uint8_t precharge_contactor;
    uint8_t discharge_contactor;
} ContactorController_t;

/* Contactor state machine - 10ms cycle */
void contactor_fsm(ContactorController_t* ctrl) {
    switch (ctrl->state) {
        case HV_STATE_OFF:
            /* All contactors open */
            ctrl->main_positive = 0;
            ctrl->main_negative = 0;
            ctrl->precharge_contactor = 0;
            ctrl->discharge_contactor = 0;
            break;

        case HV_STATE_PRECHARGING:
            /* Close negative, enable precharge */
            ctrl->main_negative = 1;
            ctrl->precharge_contactor = 1;
            ctrl->main_positive = 0;

            /* Monitor DC link voltage */
            const float voltage_ratio = ctrl->dc_link_voltage_v / ctrl->pack_voltage_v;
            const uint32_t elapsed = get_time_ms() - ctrl->precharge_start_ms;

            /* Precharge complete when V_dc_link > 90% V_pack or timeout */
            if (voltage_ratio > 0.9f) {
                ctrl->state = HV_STATE_PRECHARGE_COMPLETE;
            } else if (elapsed > PRECHARGE_TIMEOUT_MS) {
                ctrl->state = HV_STATE_FAULT;
                report_dtc(DTC_PRECHARGE_FAILURE);
            }
            break;

        case HV_STATE_PRECHARGE_COMPLETE:
            /* Close main positive, open precharge */
            ctrl->main_positive = 1;
            ctrl->precharge_contactor = 0;
            ctrl->state = HV_STATE_ON;
            break;

        case HV_STATE_ON:
            /* Normal operation - monitor for faults */
            if (fault_detected()) {
                ctrl->state = HV_STATE_DISCHARGING;
            }
            break;

        case HV_STATE_DISCHARGING:
            /* Open main contactors, enable discharge resistor */
            ctrl->main_positive = 0;
            ctrl->main_negative = 0;
            ctrl->discharge_contactor = 1;

            /* Wait for DC link to discharge below 60V */
            if (ctrl->dc_link_voltage_v < 60.0f) {
                ctrl->discharge_contactor = 0;
                ctrl->state = HV_STATE_OFF;
            }
            break;

        case HV_STATE_FAULT:
            /* Emergency open all contactors */
            ctrl->main_positive = 0;
            ctrl->main_negative = 0;
            ctrl->precharge_contactor = 0;
            /* Discharge only if safe */
            if (insulation_ok()) {
                ctrl->discharge_contactor = 1;
            }
            break;
    }
}
```

## ISO 26262 Safety Mechanisms

### Contactor Weld Detection

```c
/* ASIL D: Contactor weld detection */
typedef struct {
    uint8_t contactor_command;    /* 0=open, 1=close */
    uint8_t contactor_feedback;   /* 0=open, 1=closed */
    uint32_t weld_detection_time_ms;
    uint8_t weld_fault;
} ContactorMonitor_t;

void contactor_weld_check(ContactorMonitor_t* mon, float pack_current_a) {
    /* Check for weld: command=open but feedback=closed AND current=0 */
    if (mon->contactor_command == 0 && mon->contactor_feedback == 1) {
        /* Contactor should be open but feedback says closed */
        /* Verify with current: if |I| < threshold, likely welded */
        if (fabsf(pack_current_a) < 1.0f) {
            mon->weld_detection_time_ms += 10;  /* 10ms cycle */

            if (mon->weld_detection_time_ms > WELD_CONFIRMATION_MS) {
                mon->weld_fault = 1;
                report_dtc(DTC_CONTACTOR_WELD);
                enter_safe_state(SAFE_STATE_LOCKOUT);
            }
        } else {
            /* Current flowing - contactor not actually welded */
            mon->weld_detection_time_ms = 0;
        }
    } else {
        mon->weld_detection_time_ms = 0;
        mon->weld_fault = 0;
    }
}
```

### Insulation Monitoring

```c
/* ASIL C: Insulation resistance monitoring */
typedef struct {
    float positive_to_chassis_v;
    float negative_to_chassis_v;
    float pack_voltage_v;
    float insulation_resistance_ohm;
    uint8_t insulation_fault;
} InsulationMonitor_t;

void insulation_check(InsulationMonitor_t* ins) {
    /* Calculate insulation resistance using voltage divider method */
    /* R_iso = (V_p + V_n) / V_pack * R_known - R_known */
    const float R_known = 100000.0f;  /* 100kΩ test resistor */

    ins->insulation_resistance_ohm =
        ((ins->positive_to_chassis_v + ins->negative_to_chassis_v) /
         ins->pack_voltage_v) * R_known - R_known;

    /* ISO 6469-3: Minimum 500 Ω/V for B-class voltage */
    const float min_resistance = ins->pack_voltage_v * 500.0f;

    if (ins->insulation_resistance_ohm < min_resistance) {
        ins->insulation_fault = 1;
        report_dtc(DTC_INSULATION_FAULT);

        /* Open contactors if insulation critically low */
        if (ins->insulation_resistance_ohm < min_resistance * 0.5f) {
            open_hv_contactors();
        }
    } else {
        ins->insulation_fault = 0;
    }
}
```

### Thermal Runaway Detection

```c
/* ASIL D: Early thermal runaway detection */
typedef struct {
    float cell_temp_c[96];
    float cell_voltage_v[96];
    float max_temp_rate;        /* Max dT/dt */
    uint8_t thermal_runaway_warning;
    uint8_t thermal_runaway_detected;
} ThermalRunawayMonitor_t;

void thermal_runaway_check(ThermalRunawayMonitor_t* mon) {
    static float prev_max_temp = 0.0f;
    const float dt_s = 1.0f;  /* 1s cycle */

    /* Find maximum cell temperature */
    float max_temp = 0.0f;
    for (uint8_t i = 0; i < 96; i++) {
        if (mon->cell_temp_c[i] > max_temp) {
            max_temp = mon->cell_temp_c[i];
        }
    }

    /* Calculate temperature rate of change */
    mon->max_temp_rate = (max_temp - prev_max_temp) / dt_s;
    prev_max_temp = max_temp;

    /* Early warning: dT/dt > 1°C/s */
    if (mon->max_temp_rate > 1.0f) {
        mon->thermal_runaway_warning = 1;
        notify_driver(DRIVER_WARNING_THERMAL);
    }

    /* Critical: dT/dt > 5°C/s OR T > 80°C */
    if (mon->max_temp_rate > 5.0f || max_temp > 80.0f) {
        mon->thermal_runaway_detected = 1;
        report_dtc(DTC_THERMAL_RUNAWAY);

        /* Emergency actions */
        open_hv_contactors();
        activate_fire_suppression();
        notify_emergency_services();
    }
}
```

## AUTOSAR Implementation

### BMS Software Component

```xml
<!-- BmsController SwComponentType (ARXML) -->
<APPLICATION-SW-COMPONENT-TYPE>
  <SHORT-NAME>BmsController</SHORT-NAME>

  <!-- Port Interfaces -->
  <PORTS>
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>CellVoltagePort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/CellVoltage_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <R-PORT-PROTOTYPE>
      <SHORT-NAME>PackCurrentPort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/PackCurrent_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <P-PORT-PROTOTYPE>
      <SHORT-NAME>SocPort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/Soc_IF
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
        <SHORT-NAME>BmsMain_10ms</SHORT-NAME>
        <BEGIN-PERIOD>0.01</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>

      <RUNNABLE-ENTITY>
        <SHORT-NAME>SocEstimation_100ms</SHORT-NAME>
        <BEGIN-PERIOD>0.1</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>
    </RUNNABLE-ENTITIES>
  </INTERNAL-BEHAVIOR>
</APPLICATION-SW-COMPONENT-TYPE>
```

### BMS Runnable Implementation

```c
/* BMS Main Runnable - 10ms cycle */
#include "Rte_BmsController.h"

void BmsController_BmsMain_10ms_Runnable(void) {
    /* Read inputs from R-ports */
    CellVoltageArray_t cell_voltages;
    Rte_Read_BmsController_CellVoltagePort_Value(&cell_voltages);

    float pack_current_a;
    Rte_Read_BmsController_PackCurrentPort_Value(&pack_current_a);

    /* Cell monitoring */
    CellStatus_t cell_status;
    cell_status.max_voltage_v = 0.0f;
    cell_status.min_voltage_v = 5.0f;
    cell_status.avg_voltage_v = 0.0f;

    for (uint8_t i = 0; i < 96; i++) {
        const float cell_v = cell_voltages.voltages[i] / 1000.0f;

        if (cell_v > cell_status.max_voltage_v) {
            cell_status.max_voltage_v = cell_v;
            cell_status.max_cell_idx = i;
        }
        if (cell_v < cell_status.min_voltage_v) {
            cell_status.min_voltage_v = cell_v;
            cell_status.min_cell_idx = i;
        }
        cell_status.avg_voltage_v += cell_v;
    }
    cell_status.avg_voltage_v /= 96.0f;

    /* Check faults */
    if (cell_status.max_voltage_v > MAX_CELL_VOLTAGE_V) {
        set_fault_flag(FAULT_OVERVOLTAGE);
    }
    if (cell_status.min_voltage_v < MIN_CELL_VOLTAGE_V) {
        set_fault_flag(FAULT_UNDERVOLTAGE);
    }

    /* Balance control */
    CellBalancer_t balancer;
    memcpy(balancer.cell_voltages_mv, cell_voltages.voltages, sizeof(balancer.cell_voltages_mv));
    balance_control(&balancer);

    /* Write outputs to P-ports */
    Rte_Write_BmsController_BalanceCommandPort_Value(&balancer.balance_switch);
}

/* SOC Estimation Runnable - 100ms cycle */
void BmsController_SocEstimation_100ms_Runnable(void) {
    /* Read inputs */
    float pack_current_a;
    Rte_Read_BmsController_PackCurrentPort_Value(&pack_current_a);

    float avg_cell_voltage_v;
    Rte_Read_BmsController_CellVoltagePort_Average(&avg_cell_voltage_v);

    /* Update SOC */
    static SocEstimator_t soc_est = {0};
    soc_est.pack_current_a = pack_current_a;
    soc_est.cell_voltage_v = avg_cell_voltage_v;
    soc_update(&soc_est, 0.1f);  /* 100ms = 0.1s */

    /* Write SOC output */
    Rte_Write_BmsController_SocPort_Value(soc_est.soc_percent);
}
```

## Approach

1. **Define BMS architecture**
   - Select cell monitoring IC (AFE)
   - Determine communication topology (daisy-chain vs star)
   - Define HV junction box architecture

2. **Implement SOC/SOH estimation**
   - Implement coulomb counting with OCV correction
   - Tune EKF parameters for cell chemistry
   - Validate against reference discharge curves

3. **Develop cell balancing**
   - Select passive vs active balancing
   - Tune balance thresholds and hysteresis
   - Implement thermal limits

4. **Design thermal management**
   - Model thermal behavior (lumped or distributed)
   - Tune cooling/heating control
   - Validate in thermal chamber

5. **Implement safety mechanisms**
   - Contactor control with precharge
   - Insulation monitoring
   - Thermal runaway detection
   - ISO 26262 ASIL-appropriate diagnostics

6. **Integrate with AUTOSAR**
   - Design SwComponent with appropriate ports
   - Configure runnables and timing
   - Generate RTE and integrate

7. **Validate and calibrate**
   - MIL/SIL testing of algorithms
   - HIL testing with production ECU
   - Vehicle calibration for various conditions

## Deliverables

- BMS architecture specification
- SOC/SOH algorithm implementation (C/Model)
- Cell balancing control software
- Thermal management software
- AUTOSAR SWC integration code
- ISO 26262 safety case documentation
- Test results (MIL/SIL/HIL/Vehicle)
- Calibration parameter database

## Related Context
- @context/skills/powertrain/energy-management.md
- @context/skills/autosar/classic-platform.md
- @context/skills/safety/iso-26262-overview.md
- @context/skills/safety/safety-mechanisms-patterns.md
- @context/skills/thermal/battery-thermal.md

## Tools Required
- MATLAB/Simulink (algorithm development)
- Vector CANoe/CANalyzer (network analysis)
- ETAS INCA (calibration)
- dSPACE HIL (hardware-in-loop testing)
- Battery test equipment (Arbin, Maccor)
- Thermal chamber