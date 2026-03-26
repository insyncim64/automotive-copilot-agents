---
name: ev-thermal-management
description: "Use when: Skill: EV Thermal Management for Battery Systems topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: EV Thermal Management for Battery Systems

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/ev/thermal-management.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate
- User asks about battery thermal management strategies for EV systems
- User needs to implement cooling/heating control algorithms for battery packs
- User requests heat pump control strategies or thermal modeling approaches
- User is developing temperature regulation systems for battery safety
- User needs AUTOSAR implementation patterns for thermal management
- User asks about ISO 26262 safety mechanisms for thermal control
- User requests thermal runaway detection and prevention strategies
- User needs PID or model-based thermal control implementations

## Standards Compliance
- ISO 26262:2018 (Functional Safety) - ASIL C/D for thermal control
- ASPICE Level 3 - Model-based development process
- AUTOSAR 4.4 - Thermal management domain architecture
- ISO 21434:2021 (Cybersecurity) - Thermal command authentication
- SAE J1979 - OBD-II thermal PIDs
- UN ECE R155 - Cybersecurity management system
- ISO 6469-3 - EV safety specifications (thermal hazards)
- UL 2580 - Battery safety with thermal requirements

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Cell temperature | -40 to 85 | °C |
| Coolant temperature | -40 to 105 | °C |
| Ambient temperature | -40 to 55 | °C |
| Target temperature | 15 to 35 | °C |
| Cooling power | 0 to 15 | kW |
| Heating power | 0 to 8 | kW |
| Coolant flow rate | 0 to 50 | L/min |
| Thermal conductivity | 0.1 to 500 | W/(m·K) |
| Thermal resistance | 0.001 to 10 | K/W |
| Heat capacity | 500 to 1500 | J/(kg·K) |

## Thermal Management Architecture

```
+----------------------------------------------------------+
|           Thermal Management Controller                   |
|  +------------------+  +------------------+              |
|  |  Temperature Ctrl |  |  Heat Pump Ctrl  |            |
|  +------------------+  +------------------+              |
|           |                     |                        |
|  +------------------+  +------------------+              |
|  |  Thermal Model   |  |  Fault Detection |             |
|  +------------------+  +------------------+              |
+--------------------------|-------------------------------+
                           |
         +-----------------+-----------------+
         |                 |                 |
+--------v--------+ +------v------+ +--------v--------+
|  Cooling System | | Heating Sys | | Heat Pump       |
|  (Liquid/Air)   | | (PTC/Heat)  | | (Refrigerant)   |
+-----------------+ +-------------+ +-----------------+
```

## Temperature Control Strategy

### PID-Based Thermal Control

```c
/* Battery thermal control - PID controller */
typedef struct {
    float target_temp_c;
    float current_temp_c;
    float integral_error;
    float previous_error;
    float kp;
    float ki;
    float kd;
    float output_min;
    float output_max;
    float dt;
} ThermalPidController_t;

typedef struct {
    float coolant_flow_rate;
    float compressor_speed;
    float ptc_power;
    bool cooling_active;
    bool heating_active;
} ThermalCommand_t;

/* PID thermal controller */
ThermalPidController_t g_thermal_pid = {
    .target_temp_c = 25.0f,
    .current_temp_c = 25.0f,
    .integral_error = 0.0f,
    .previous_error = 0.0f,
    .kp = 2.0f,
    .ki = 0.1f,
    .kd = 0.5f,
    .output_min = 0.0f,
    .output_max = 100.0f,
    .dt = 0.1f  /* 100ms cycle */
};

/* Anti-windup PID implementation */
ThermalCommand_t compute_thermal_command(const ThermalPidController_t* ctrl) {
    ThermalCommand_t cmd = {0};

    /* Compute error */
    float error = ctrl->target_temp_c - ctrl->current_temp_c;

    /* Proportional term */
    float p_term = ctrl->kp * error;

    /* Integral term with anti-windup */
    float integral = ctrl->integral_error + (error * ctrl->dt);

    /* Derivative term */
    float derivative = (error - ctrl->previous_error) / ctrl->dt;

    /* Compute raw output */
    float raw_output = p_term + (ctrl->ki * integral) + (ctrl->kd * derivative);

    /* Apply output limits with anti-windup */
    float clamped_output;
    if (raw_output > ctrl->output_max) {
        clamped_output = ctrl->output_max;
        /* Anti-windup: don't integrate when saturated */
        integral = ctrl->integral_error;
    } else if (raw_output < ctrl->output_min) {
        clamped_output = ctrl->output_min;
        integral = ctrl->integral_error;
    } else {
        clamped_output = raw_output;
    }

    /* Determine cooling vs heating based on error sign */
    if (error > 0.5f) {
        /* Need cooling */
        cmd.cooling_active = true;
        cmd.heating_active = false;
        cmd.coolant_flow_rate = map_value(clamped_output, 0.0f, 100.0f, 0.0f, 50.0f);
        cmd.compressor_speed = map_value(clamped_output, 0.0f, 100.0f, 0.0f, 6000.0f);
        cmd.ptc_power = 0.0f;
    } else if (error < -0.5f) {
        /* Need heating */
        cmd.cooling_active = false;
        cmd.heating_active = true;
        cmd.coolant_flow_rate = map_value(clamped_output, 0.0f, 100.0f, 0.0f, 30.0f);
        cmd.compressor_speed = 0.0f;
        cmd.ptc_power = map_value(clamped_output, 0.0f, 100.0f, 0.0f, 8000.0f);
    } else {
        /* Deadband - maintain current state */
        cmd.coolant_flow_rate = 5.0f;  /* Minimum circulation */
        cmd.compressor_speed = 0.0f;
        cmd.ptc_power = 0.0f;
    }

    /* Update controller state */
    g_thermal_pid.integral_error = integral;
    g_thermal_pid.previous_error = error;

    return cmd;
}

/* Lookup table mapping for value conversion */
float map_value(float x, float in_min, float in_max, float out_min, float out_max) {
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}
```

### Model-Based Predictive Thermal Control

```c
/* Lumped parameter thermal model for prediction */
typedef struct {
    float cell_mass_kg;
    float cell_specific_heat;
    float coolant_mass_kg;
    float coolant_specific_heat;
    float thermal_resistance_cell_coolant;
    float thermal_resistance_coolant_ambient;
    float cell_temperature;
    float coolant_temperature;
    float ambient_temperature;
    float internal_heat_generation_w;
} LumpedThermalModel_t;

/* Thermal model state update */
void update_thermal_model(LumpedThermalModel_t* model, float dt) {
    /* Cell thermal dynamics */
    float dTcell_dt = (
        - (model->cell_temperature - model->coolant_temperature)
          / model->thermal_resistance_cell_coolant
        + model->internal_heat_generation_w
    ) / (model->cell_mass_kg * model->cell_specific_heat);

    /* Coolant thermal dynamics */
    float dTcoolant_dt = (
        (model->cell_temperature - model->coolant_temperature)
          / model->thermal_resistance_cell_coolant
        - (model->coolant_temperature - model->ambient_temperature)
          / model->thermal_resistance_coolant_ambient
    ) / (model->coolant_mass_kg * model->coolant_specific_heat);

    /* Euler integration */
    model->cell_temperature += dTcell_dt * dt;
    model->coolant_temperature += dTcoolant_dt * dt;

    /* Physical limits */
    model->cell_temperature = fmaxf(-40.0f, fminf(85.0f, model->cell_temperature));
    model->coolant_temperature = fmaxf(-40.0f, fminf(105.0f, model->coolant_temperature));
}

/* Model Predictive Control (MPC) for thermal management */
typedef struct {
    float prediction_horizon_s;
    float control_horizon_s;
    float weight_temp_error;
    float weight_energy_usage;
    float weight_comfort;
} MpcConfig_t;

typedef struct {
    float predicted_temp[10];
    float optimal_coolant_flow[10];
    float optimal_compressor_speed[10];
    float cost_function;
} MpcResult_t;

/* Simplified MPC - single step optimization */
MpcResult_t compute_mpc_thermal_control(
    const LumpedThermalModel_t* model,
    const MpcConfig_t* config,
    float target_temp) {

    MpcResult_t result = {0};
    float min_cost = FLT_MAX;
    float best_flow = 0.0f;
    float best_speed = 0.0f;

    /* Discretize control space */
    for (float flow = 0.0f; flow <= 50.0f; flow += 5.0f) {
        for (float speed = 0.0f; speed <= 6000.0f; speed += 500.0f) {
            /* Simulate model forward */
            LumpedThermalModel_t sim_model = *model;
            sim_model.thermal_resistance_coolant_ambient =
                1.0f / (0.01f * flow + 0.001f * speed + 0.1f);

            float cost = 0.0f;
            float dt = config->prediction_horizon_s / 10.0f;

            for (int i = 0; i < 10; i++) {
                update_thermal_model(&sim_model, dt);

                /* Temperature tracking cost */
                float temp_error = sim_model.cell_temperature - target_temp;
                cost += config->weight_temp_error * temp_error * temp_error;

                /* Energy usage cost */
                cost += config->weight_energy_usage * (flow * 0.1f + speed * 0.0001f);

                result.predicted_temp[i] = sim_model.cell_temperature;
            }

            if (cost < min_cost) {
                min_cost = cost;
                best_flow = flow;
                best_speed = speed;
            }
        }
    }

    result.optimal_coolant_flow[0] = best_flow;
    result.optimal_compressor_speed[0] = best_speed;
    result.cost_function = min_cost;

    return result;
}
```

## Heat Pump Control

### Vapor Compression Cycle Control

```c
/* Heat pump operating modes */
typedef enum {
    HEAT_PUMP_OFF,
    HEAT_PUMP_COOLING,
    HEAT_PUMP_HEATING,
    HEAT_PUMP_DEHUMIDIFY,
    HEAT_PUMP_DEFROST
} HeatPumpMode_t;

typedef struct {
    HeatPumpMode_t mode;
    float evaporator_temp_c;
    float condenser_temp_c;
    float suction_pressure_bar;
    float discharge_pressure_bar;
    float compressor_speed_rpm;
    float expansion_valve_opening_percent;
    float refrigerant_mass_flow_kg_s;
    float cop;  /* Coefficient of Performance */
} HeatPumpState_t;

/* Heat pump controller */
typedef struct {
    HeatPumpState_t state;
    float target_evaporator_temp_c;
    float target_condenser_temp_c;
    float max_discharge_pressure_bar;
    float min_suction_pressure_bar;
} HeatPumpController_t;

/* Heat pump control algorithm */
HeatPumpState_t control_heat_pump(
    HeatPumpController_t* controller,
    float ambient_temp_c,
    float cabin_temp_request_c) {

    HeatPumpState_t* state = &controller->state;

    switch (state->mode) {
        case HEAT_PUMP_COOLING:
            /* Control evaporator temperature for cooling */
            if (state->evaporator_temp_c > controller->target_evaporator_temp_c) {
                /* Increase compressor speed */
                state->compressor_speed_rpm = fminf(
                    state->compressor_speed_rpm + 200.0f, 6000.0f);
            } else if (state->evaporator_temp_c < controller->target_evaporator_temp_c) {
                /* Decrease compressor speed */
                state->compressor_speed_rpm = fmaxf(
                    state->compressor_speed_rpm - 200.0f, 1000.0f);
            }

            /* Control expansion valve for superheat */
            float superheat = state->evaporator_temp_c -
                              pressure_to_saturation_temp(state->suction_pressure_bar);
            if (superheat < 5.0f) {
                /* Open valve to increase superheat */
                state->expansion_valve_opening_percent = fminf(
                    state->expansion_valve_opening_percent + 2.0f, 95.0f);
            } else if (superheat > 10.0f) {
                /* Close valve to decrease superheat */
                state->expansion_valve_opening_percent = fmaxf(
                    state->expansion_valve_opening_percent - 2.0f, 5.0f);
            }
            break;

        case HEAT_PUMP_HEATING:
            /* Control condenser temperature for heating */
            if (state->condenser_temp_c < controller->target_condenser_temp_c) {
                state->compressor_speed_rpm = fminf(
                    state->compressor_speed_rpm + 200.0f, 6000.0f);
            } else {
                state->compressor_speed_rpm = fmaxf(
                    state->compressor_speed_rpm - 200.0f, 1000.0f);
            }
            break;

        case HEAT_PUMP_DEFROST:
            /* Reverse cycle to defrost evaporator */
            if (state->evaporator_temp_c < 0.0f) {
                state->compressor_speed_rpm = 3000.0f;
                state->expansion_valve_opening_percent = 50.0f;
            } else {
                /* Defrost complete - return to normal mode */
                state->mode = HEAT_PUMP_COOLING;
            }
            break;

        default:
            state->compressor_speed_rpm = 0.0f;
            state->expansion_valve_opening_percent = 0.0f;
            break;
    }

    /* Safety limits */
    if (state->discharge_pressure_bar > controller->max_discharge_pressure_bar) {
        state->compressor_speed_rpm *= 0.8f;  /* Reduce speed */
    }
    if (state->suction_pressure_bar < controller->min_suction_pressure_bar) {
        state->compressor_speed_rpm *= 0.8f;
    }

    /* Calculate COP */
    float cooling_capacity = state->refrigerant_mass_flow_kg_s * 200000.0f;  /* Simplified */
    float power_input = state->compressor_speed_rpm * 0.5f;  /* Simplified */
    state->cop = (power_input > 0.0f) ? (cooling_capacity / power_input) : 0.0f;

    return *state;
}

/* Pressure to saturation temperature lookup */
float pressure_to_saturation_temp(float pressure_bar) {
    /* Simplified R134a saturation table */
    static const struct {
        float pressure;
        float temp;
    } saturation_table[] = {
        {1.0f, -26.4f}, {2.0f, -10.1f}, {3.0f, 0.6f},
        {4.0f, 8.9f}, {5.0f, 15.7f}, {6.0f, 21.6f},
        {7.0f, 26.7f}, {8.0f, 31.3f}, {9.0f, 35.5f},
        {10.0f, 39.4f}, {11.0f, 43.0f}, {12.0f, 46.3f}
    };

    /* Linear interpolation */
    for (size_t i = 0; i < sizeof(saturation_table)/sizeof(saturation_table[0]) - 1; i++) {
        if (pressure_bar >= saturation_table[i].pressure &&
            pressure_bar <= saturation_table[i+1].pressure) {
            float ratio = (pressure_bar - saturation_table[i].pressure) /
                         (saturation_table[i+1].pressure - saturation_table[i].pressure);
            return saturation_table[i].temp +
                   ratio * (saturation_table[i+1].temp - saturation_table[i].temp);
        }
    }

    return -10.0f;  /* Default */
}
```

## Cooling System Control

### Liquid Cooling Strategy

```c
/* Liquid cooling system configuration */
typedef struct {
    float pump_speed_rpm;
    float valve_opening_percent;
    float radiator_fan_speed_rpm;
    float coolant_temp_c;
    float flow_rate_lpm;
    bool pump_enabled;
    bool fan_enabled;
} LiquidCoolingSystem_t;

typedef struct {
    float target_coolant_temp_c;
    float max_cell_temp_c;
    float min_cell_temp_c;
    float temp_spread_limit_c;
} LiquidCoolingConfig_t;

/* Liquid cooling controller */
LiquidCoolingSystem_t control_liquid_cooling(
    const float cell_temps_c[96],
    int cell_count,
    const LiquidCoolingConfig_t* config) {

    LiquidCoolingSystem_t system = {0};

    /* Find max, min, and average cell temperature */
    float max_temp = -40.0f;
    float min_temp = 100.0f;
    float sum_temp = 0.0f;

    for (int i = 0; i < cell_count; i++) {
        if (cell_temps_c[i] > max_temp) max_temp = cell_temps_c[i];
        if (cell_temps_c[i] < min_temp) min_temp = cell_temps_c[i];
        sum_temp += cell_temps_c[i];
    }

    float avg_temp = sum_temp / cell_count;
    float temp_spread = max_temp - min_temp;

    system.pump_enabled = true;
    system.fan_enabled = true;

    /* Pump speed based on average temperature */
    if (avg_temp < 20.0f) {
        system.pump_speed_rpm = 1000.0f;  /* Minimum circulation */
        system.coolant_temp_c = avg_temp + 2.0f;
    } else if (avg_temp < 30.0f) {
        system.pump_speed_rpm = 2000.0f;
        system.coolant_temp_c = avg_temp + 3.0f;
    } else if (avg_temp < 40.0f) {
        system.pump_speed_rpm = 3500.0f;
        system.coolant_temp_c = avg_temp + 5.0f;
    } else {
        system.pump_speed_rpm = 5000.0f;  /* Maximum */
        system.coolant_temp_c = avg_temp + 8.0f;
    }

    /* Radiator fan speed based on coolant temperature */
    if (system.coolant_temp_c > 35.0f) {
        system.radiator_fan_speed_rpm = map_value(
            system.coolant_temp_c, 35.0f, 55.0f, 1000.0f, 4000.0f);
    } else {
        system.radiator_fan_speed_rpm = 500.0f;  /* Minimum */
    }

    /* Flow distribution valve (for multi-zone cooling) */
    if (temp_spread > config->temp_spread_limit_c) {
        /* Increase flow to hotter zones */
        system.valve_opening_percent = 80.0f;
    } else {
        system.valve_opening_percent = 50.0f;  /* Balanced */
    }

    /* Calculate actual flow rate */
    system.flow_rate_lpm = system.pump_speed_rpm * 0.01f;

    return system;
}
```

## Thermal Runaway Detection

### Early Warning System

```c
/* Thermal runaway detection states */
typedef enum {
    TR_STATE_NORMAL,
    TR_STATE_WARNING,
    TR_STATE_CRITICAL,
    TR_STATE_RUNAWAY_DETECTED
} ThermalRunawayState_t;

typedef struct {
    ThermalRunawayState_t state;
    float cell_temp_c;
    float temp_rate_of_change;
    float voltage_deviation;
    float gas_concentration_ppm;
    uint32_t warning_timestamp_ms;
    bool vent_detected;
} ThermalRunawayDetector_t;

typedef struct {
    float temp_threshold_c;
    float temp_rate_threshold;
    float voltage_dev_threshold;
    float gas_threshold_ppm;
    float confirmation_window_ms;
} ThermalRunawayConfig_t;

/* Multi-sensor thermal runaway detection */
ThermalRunawayState_t detect_thermal_runaway(
    ThermalRunawayDetector_t* detector,
    const ThermalRunawayConfig_t* config,
    float cell_voltage_v,
    float nominal_voltage_v) {

    uint32_t current_time_ms = get_system_time_ms();

    /* Check temperature threshold */
    bool temp_exceeded = detector->cell_temp_c > config->temp_threshold_c;

    /* Check temperature rate of change */
    bool temp_rate_exceeded = detector->temp_rate_of_change > config->temp_rate_threshold;

    /* Check voltage deviation (internal short detection) */
    detector->voltage_deviation = fabsf(cell_voltage_v - nominal_voltage_v);
    bool voltage_anomaly = detector->voltage_deviation > config->voltage_dev_threshold;

    /* Check gas sensor (if equipped) */
    bool gas_detected = detector->gas_concentration_ppm > config->gas_threshold_ppm;

    /* State machine */
    switch (detector->state) {
        case TR_STATE_NORMAL:
            if (temp_exceeded || temp_rate_exceeded || voltage_anomaly) {
                detector->state = TR_STATE_WARNING;
                detector->warning_timestamp_ms = current_time_ms;
            }
            break;

        case TR_STATE_WARNING:
            /* Confirm warning persists */
            if ((current_time_ms - detector->warning_timestamp_ms) >
                config->confirmation_window_ms) {
                if (temp_exceeded && temp_rate_exceeded) {
                    detector->state = TR_STATE_CRITICAL;
                }
            } else if (!temp_exceeded && !temp_rate_exceeded && !voltage_anomaly) {
                detector->state = TR_STATE_NORMAL;
            }
            break;

        case TR_STATE_CRITICAL:
            if (gas_detected || detector->vent_detected ||
                detector->temp_rate_of_change > (config->temp_rate_threshold * 2.0f)) {
                detector->state = TR_STATE_RUNAWAY_DETECTED;
            }
            break;

        case TR_STATE_RUNAWAY_DETECTED:
            /* Latching state - requires manual reset */
            break;
    }

    return detector->state;
}

/* Thermal runaway mitigation actions */
typedef struct {
    bool disconnect_contactors;
    bool activate_fire_suppression;
    bool notify_driver;
    bool enable_maximum_cooling;
    bool isolate_thermal_zone;
    uint8_t severity_level;
} ThermalRunawayResponse_t;

ThermalRunawayResponse_t generate_thermal_response(
    ThermalRunawayState_t state) {

    ThermalRunawayResponse_t response = {0};

    switch (state) {
        case TR_STATE_NORMAL:
            response.severity_level = 0;
            break;

        case TR_STATE_WARNING:
            response.notify_driver = true;
            response.severity_level = 1;
            break;

        case TR_STATE_CRITICAL:
            response.disconnect_contactors = true;
            response.notify_driver = true;
            response.enable_maximum_cooling = true;
            response.isolate_thermal_zone = true;
            response.severity_level = 2;
            break;

        case TR_STATE_RUNAWAY_DETECTED:
            response.disconnect_contactors = true;
            response.activate_fire_suppression = true;
            response.notify_driver = true;
            response.enable_maximum_cooling = true;
            response.isolate_thermal_zone = true;
            response.severity_level = 3;
            break;
    }

    return response;
}
```

## Thermal Modeling

### Lumped Parameter Model

```c
/* 3-state lumped thermal model for battery pack */
typedef struct {
    /* States */
    float cell_core_temp_c;
    float cell_surface_temp_c;
    float coolant_temp_c;

    /* Parameters */
    float cell_core_mass_kg;
    float cell_surface_mass_kg;
    float coolant_mass_kg;
    float cell_specific_heat_j_kgk;
    float coolant_specific_heat_j_kgk;
    float core_surface_thermal_resistance_k_w;
    float surface_coolant_thermal_resistance_k_w;
    float coolant_ambient_thermal_resistance_k_w;

    /* Inputs */
    float heat_generation_w;
    float ambient_temp_c;
    float coolant_flow_rate_lpm;
} LumpedThermalPack_t;

/* State-space representation */
void update_lumped_thermal_pack(
    LumpedThermalPack_t* pack,
    float dt) {

    /* Update coolant-ambient resistance based on flow rate */
    float flow_conductance = pack->coolant_flow_rate_lpm * 2.0f;
    float effective_coolant_ambient_resistance =
        1.0f / (1.0f/pack->coolant_ambient_thermal_resistance_k_w + flow_conductance);

    /* Cell core dynamics */
    float core_surface_heat_flow =
        (pack->cell_core_temp_c - pack->cell_surface_temp_c) /
        pack->core_surface_thermal_resistance_k_w;

    float dTcore_dt = (pack->heat_generation_w - core_surface_heat_flow) /
                      (pack->cell_core_mass_kg * pack->cell_specific_heat_j_kgk);

    /* Cell surface dynamics */
    float surface_coolant_heat_flow =
        (pack->cell_surface_temp_c - pack->coolant_temp_c) /
        pack->surface_coolant_thermal_resistance_k_w;

    float dTsurface_dt = (core_surface_heat_flow - surface_coolant_heat_flow) /
                         (pack->cell_surface_mass_kg * pack->cell_specific_heat_j_kgk);

    /* Coolant dynamics */
    float coolant_ambient_heat_flow =
        (pack->coolant_temp_c - pack->ambient_temp_c) /
        effective_coolant_ambient_resistance;

    float dTcoolant_dt = (surface_coolant_heat_flow - coolant_ambient_heat_flow) /
                         (pack->coolant_mass_kg * pack->coolant_specific_heat_j_kgk);

    /* Euler integration with stability check */
    float max_dt = compute_thermal_stability_limit(pack);
    float actual_dt = fminf(dt, max_dt);

    pack->cell_core_temp_c += dTcore_dt * actual_dt;
    pack->cell_surface_temp_c += dTsurface_dt * actual_dt;
    pack->coolant_temp_c += dTcoolant_dt * actual_dt;

    /* Physical limits */
    constrain_temperature(&pack->cell_core_temp_c, -40.0f, 120.0f);
    constrain_temperature(&pack->cell_surface_temp_c, -40.0f, 120.0f);
    constrain_temperature(&pack->coolant_temp_c, -40.0f, 105.0f);
}

/* Compute maximum stable time step */
float compute_thermal_stability_limit(const LumpedThermalPack_t* pack) {
    float thermal_mass_core = pack->cell_core_mass_kg * pack->cell_specific_heat_j_kgk;
    float thermal_mass_surface = pack->cell_surface_mass_kg * pack->cell_specific_heat_j_kgk;
    float thermal_mass_coolant = pack->coolant_mass_kg * pack->coolant_specific_heat_j_kgk;

    float tau_core = thermal_mass_core * pack->core_surface_thermal_resistance_k_w;
    float tau_surface = thermal_mass_surface * pack->surface_coolant_thermal_resistance_k_w;
    float tau_coolant = thermal_mass_coolant * pack->coolant_ambient_thermal_resistance_k_w;

    float min_tau = fminf(tau_core, fminf(tau_surface, tau_coolant));

    return min_tau * 0.1f;  /* 10% of smallest time constant */
}

void constrain_temperature(float* temp, float min, float max) {
    if (*temp < min) *temp = min;
    if (*temp > max) *temp = max;
}
```

### Distributed Thermal Model

```c
/* 1D distributed thermal model for battery module */
#define THERMAL_NODES 10

typedef struct {
    float node_temps_c[THERMAL_NODES];
    float node_mass_kg[THERMAL_NODES];
    float inter_node_thermal_resistance_k_w;
    float node_specific_heat_j_kgk;
    float node_heat_generation_w[THERMAL_NODES];
    float boundary_temp_c;
    float boundary_thermal_resistance_k_w;
} DistributedThermalModel_t;

/* Finite difference thermal update */
void update_distributed_thermal(
    DistributedThermalModel_t* model,
    float dt) {

    float new_temps[THERMAL_NODES];

    for (int i = 0; i < THERMAL_NODES; i++) {
        float heat_in = 0.0f;
        float heat_out = 0.0f;

        /* Heat from previous node */
        if (i > 0) {
            heat_in = (model->node_temps_c[i-1] - model->node_temps_c[i]) /
                      model->inter_node_thermal_resistance_k_w;
        }

        /* Heat from next node */
        if (i < THERMAL_NODES - 1) {
            heat_out = (model->node_temps_c[i] - model->node_temps_c[i+1]) /
                       model->inter_node_thermal_resistance_k_w;
        }

        /* Boundary conditions */
        if (i == 0) {
            heat_in += (model->boundary_temp_c - model->node_temps_c[i]) /
                       model->boundary_thermal_resistance_k_w;
        }
        if (i == THERMAL_NODES - 1) {
            heat_out += (model->node_temps_c[i] - model->boundary_temp_c) /
                        model->boundary_thermal_resistance_k_w;
        }

        /* Internal heat generation */
        float internal = model->node_heat_generation_w[i];

        /* Temperature update */
        float thermal_mass = model->node_mass_kg[i] * model->node_specific_heat_j_kgk;
        new_temps[i] = model->node_temps_c[i] +
                       (heat_in - heat_out + internal) * dt / thermal_mass;
    }

    /* Copy new temperatures */
    for (int i = 0; i < THERMAL_NODES; i++) {
        model->node_temps_c[i] = constrainf(new_temps[i], -40.0f, 120.0f);
    }
}

float constrainf(float x, float min, float max) {
    return fmaxf(min, fminf(max, x));
}
```

## AUTOSAR Implementation

### Thermal Management SwComponent

```xml
<!-- ThermalManager SwComponentType (ARXML) -->
<APPLICATION-SW-COMPONENT-TYPE>
  <SHORT-NAME>ThermalManager</SHORT-NAME>

  <!-- Port Interfaces -->
  <PORTS>
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>TemperatureSensorsPort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/TemperatureSensors_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <R-PORT-PROTOTYPE>
      <SHORT-NAME>DriverDemandPort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/ThermalDemand_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <P-PORT-PROTOTYPE>
      <SHORT-NAME>CoolingCommandPort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/CoolingCommand_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>

    <P-PORT-PROTOTYPE>
      <SHORT-NAME>HeatingCommandPort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/HeatingCommand_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>
  </PORTS>

  <!-- Internal Behavior -->
  <INTERNAL-BEHAVIOR>
    <RUNNABLE-ENTITIES>
      <RUNNABLE-ENTITY>
        <SHORT-NAME>ThermalControl_100ms</SHORT-NAME>
        <BEGIN-PERIOD>0.1</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>

      <RUNNABLE-ENTITY>
        <SHORT-NAME>ThermalModel_50ms</SHORT-NAME>
        <BEGIN-PERIOD>0.05</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>
    </RUNNABLE-ENTITIES>
  </INTERNAL-BEHAVIOR>
</APPLICATION-SW-COMPONENT-TYPE>
```

### Runnable Implementation

```c
/* Thermal Management Runnable - 100ms cycle */
#include "Rte_ThermalManager.h"

void ThermalManager_ThermalControl_100ms_Runnable(void) {
    /* Read temperature sensors */
    TemperatureArray_t temperatures;
    Rte_Read_ThermalManager_TemperatureSensorsPort_Value(&temperatures);

    /* Read driver thermal demand */
    ThermalDemand_t demand;
    Rte_Read_ThermalManager_DriverDemandPort_Value(&demand);

    /* Find max cell temperature */
    float max_cell_temp = find_max_temperature(&temperatures);

    /* Compute thermal command */
    ThermalCommand_t thermal_cmd;
    if (max_cell_temp > 35.0f) {
        thermal_cmd = compute_cooling_command(max_cell_temp, 25.0f);
    } else if (max_cell_temp < 15.0f) {
        thermal_cmd = compute_heating_command(max_cell_temp, 20.0f);
    } else {
        thermal_cmd = compute_maintain_command();
    }

    /* Write cooling command */
    Rte_Write_ThermalManager_CoolingCommandPort_FlowRate(
        thermal_cmd.coolant_flow_rate);
    Rte_Write_ThermalManager_CoolingCommandPort_CompressorSpeed(
        thermal_cmd.compressor_speed);

    /* Write heating command */
    Rte_Write_ThermalManager_HeatingCommandPort_Power(
        thermal_cmd.ptc_power);

    /* Update thermal model for prediction */
    update_thermal_model_prediction(&temperatures, &demand);

    /* Check for thermal faults */
    check_thermal_faults(&temperatures);
}

/* Thermal model runnable - 50ms cycle */
void ThermalManager_ThermalModel_50ms_Runnable(void) {
    TemperatureArray_t temps;
    Rte_Read_ThermalManager_TemperatureSensorsPort_Value(&temps);

    /* Update internal thermal model state */
    g_thermal_model.cell_temperature = compute_average_temperature(&temps);
    update_lumped_thermal_pack(&g_thermal_model, 0.05f);

    /* Log model state for diagnostics */
    log_thermal_model_state(&g_thermal_model);
}
```

## Safety Mechanisms (ISO 26262)

### Temperature Sensor Plausibility

```c
/* ASIL C: Temperature sensor validation */
typedef struct {
    float sensor_values[8];
    uint8_t sensor_count;
    float expected_variance_c;
    uint32_t fault_mask;
} TemperatureSensorArray_t;

typedef enum {
    TEMP_SENSOR_VALID,
    TEMP_SENSOR_STUCK,
    TEMP_SENSOR_OPEN,
    TEMP_SENSOR_SHORT,
    TEMP_SENSOR_IMPLAUSIBLE
} TemperatureSensorFault_t;

/* Multi-sensor plausibility check */
TemperatureSensorArray_t validate_temperature_sensors(
    const TemperatureSensorArray_t* raw_sensors) {

    TemperatureSensorArray_t validated = *raw_sensors;
    validated.fault_mask = 0U;

    /* Check for stuck sensors (no change over time) */
    for (uint8_t i = 0; i < raw_sensors->sensor_count; i++) {
        if (is_sensor_stuck(i)) {
            validated.fault_mask |= (1U << i);
        }
    }

    /* Check for out-of-range values */
    for (uint8_t i = 0; i < raw_sensors->sensor_count; i++) {
        if (raw_sensors->sensor_values[i] < -45.0f ||
            raw_sensors->sensor_values[i] > 125.0f) {
            validated.fault_mask |= (1U << i);
        }
    }

    /* Cross-check redundant sensors */
    if (raw_sensors->sensor_count >= 2) {
        float variance = compute_temperature_variance(
            raw_sensors->sensor_values,
            raw_sensors->sensor_count);

        /* Variance should be within expected bounds */
        if (variance > raw_sensors->expected_variance_c * 3.0f) {
            /* Identify outlier sensor */
            uint8_t outlier = find_temperature_outlier(
                raw_sensors->sensor_values,
                raw_sensors->sensor_count);
            validated.fault_mask |= (1U << outlier);
        }
    }

    /* Replace faulty sensor values with estimated values */
    for (uint8_t i = 0; i < raw_sensors->sensor_count; i++) {
        if (validated.fault_mask & (1U << i)) {
            validated.sensor_values[i] = estimate_sensor_value(i);
        }
    }

    return validated;
}

float compute_temperature_variance(const float* values, uint8_t count) {
    float mean = 0.0f;
    for (uint8_t i = 0; i < count; i++) {
        mean += values[i];
    }
    mean /= count;

    float variance = 0.0f;
    for (uint8_t i = 0; i < count; i++) {
        float diff = values[i] - mean;
        variance += diff * diff;
    }
    variance /= count;

    return variance;
}
```

### Coolant Flow Monitoring

```c
/* ASIL B: Coolant flow validation */
typedef struct {
    float target_flow_lpm;
    float measured_flow_lpm;
    float pump_current_a;
    uint32_t flow_fault_timestamp_ms;
    bool flow_fault_active;
} CoolantFlowMonitor_t;

typedef enum {
    FLOW_OK,
    FLOW_LOW_WARNING,
    FLOW_LOW_CRITICAL,
    FLOW_SENSOR_FAULT
} FlowStatus_t;

FlowStatus_t monitor_coolant_flow(CoolantFlowMonitor_t* monitor) {
    /* Check flow sensor plausibility */
    if (monitor->measured_flow_lpm < 0.0f ||
        monitor->measured_flow_lpm > 60.0f) {
        return FLOW_SENSOR_FAULT;
    }

    /* Check flow vs pump command */
    float expected_flow = monitor->pump_current_a * 10.0f;  /* Simplified map */
    float flow_error = fabsf(monitor->measured_flow_lpm - expected_flow);

    if (flow_error > 5.0f) {
        /* Pump may be failing or blocked */
        if (!monitor->flow_fault_active) {
            monitor->flow_fault_timestamp_ms = get_system_time_ms();
            monitor->flow_fault_active = true;
        }

        /* Check if fault persists */
        uint32_t fault_duration = get_system_time_ms() -
                                   monitor->flow_fault_timestamp_ms;

        if (fault_duration > 5000U) {
            return FLOW_LOW_CRITICAL;
        }
        return FLOW_LOW_WARNING;
    }

    monitor->flow_fault_active = false;

    /* Check minimum flow requirement */
    if (monitor->measured_flow_lpm < 2.0f) {
        return FLOW_LOW_CRITICAL;
    }

    return FLOW_OK;
}
```

## Approach

1. **Define thermal requirements**
   - Identify operating temperature range
   - Define cooling/heating power requirements
   - Specify thermal gradients and uniformity targets

2. **Develop thermal model**
   - Select lumped vs. distributed model complexity
   - Identify model parameters (mass, specific heat, thermal resistance)
   - Validate model against test data

3. **Design control strategy**
   - Implement PID baseline controller
   - Add model-based predictive control if needed
   - Define operating mode transitions

4. **Implement heat pump control**
   - Configure compressor control
   - Implement expansion valve control
   - Add defrost cycle logic

5. **Integrate with AUTOSAR**
   - Design SwComponent with appropriate ports
   - Configure runnables and timing
   - Generate RTE and integrate

6. **Validate and calibrate**
   - MIL/SIL testing of control algorithms
   - HIL testing with production ECU
   - Vehicle calibration for various climates

## Deliverables

- Thermal management strategy specification
- Thermal model (lumped/distributed) implementation
- Control algorithm code (C/Model)
- AUTOSAR SWC integration code
- Calibration parameter database
- Test results (MIL/SIL/HIL/Vehicle)
- ISO 26262 safety case documentation
- Thermal runaway detection and mitigation strategy

## Related Context
- @context/skills/ev/battery-management.md
- @context/skills/powertrain/battery-management.md
- @context/skills/autosar/classic-platform.md
- @context/skills/safety/iso-26262-overview.md
- @context/skills/hvac/heat-pump-control.md

## Tools Required
- MATLAB/Simulink (thermal modeling)
- Vector CANoe/CANalyzer (network analysis)
- ETAS INCA (calibration)
- dSPACE HIL (hardware-in-loop testing)
- ANSYS Fluent (CFD thermal simulation - optional)
- Star-CCM+ (thermal simulation - optional)
- Static analyzer (Polyspace/Klocwork)
- Thermocouple data acquisition system
- Climate chamber testing equipment