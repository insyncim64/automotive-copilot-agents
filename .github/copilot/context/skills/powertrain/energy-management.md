# Skill: Energy Management for Automotive Powertrain

## When to Activate
- User asks about energy management strategies for powertrain systems
- User needs to implement power distribution or torque allocation algorithms
- User requests hybrid vehicle control strategies (HEV/PHEV)
- User is developing fuel efficiency optimization systems
- User needs AUTOSAR implementation patterns for energy management
- User asks about ISO 26262 safety mechanisms for energy control

## Standards Compliance
- ISO 26262:2018 (Functional Safety) - ASIL C/D for torque control
- ASPICE Level 3 - Model-based development process
- AUTOSAR 4.4 - Powertrain domain architecture
- ISO 21434:2021 (Cybersecurity) - Torque command authentication
- SAE J1979 - OBD-II energy management PIDs
- UN ECE R155 - Cybersecurity management system

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Battery SOC | 0-100 | percentage |
| Motor torque request | -150 to +150 | Nm |
| Engine torque request | 0-400 | Nm |
| Power distribution | Dynamic allocation | percentage |
| Regenerative braking | 0-200 | kW |
| Fuel consumption | 0-15 | L/100km |
| System voltage | 9-16 | V |
| Temperature range | -40 to 125 | °C |

## Energy Management Architecture

```
+----------------------------------------------------------+
|              Energy Management Controller                 |
|  +------------------+  +------------------+              |
|  |  Power Distribution |  Torque Management |            |
|  +------------------+  +------------------+              |
|           |                     |                        |
|  +------------------+  +------------------+              |
|  |  SOC Estimator   |  |  Efficiency Opt. |             |
|  +------------------+  +------------------+              |
+--------------------------|-------------------------------+
                           |
         +-----------------+-----------------+
         |                 |                 |
+--------v--------+ +------v------+ +--------v--------+
|  Engine Control | | Motor Ctrl  | | Battery Mgmt    |
|  (ECM)          | | (MCU)       | | (BMS)           |
+-----------------+ +-------------+ +-----------------+
```

## Power Distribution Strategy

### Rule-Based Power Split

```c
/* Hybrid power distribution - rule-based controller */
typedef struct {
    float driver_power_request_kw;
    float battery_soc_percent;
    float vehicle_speed_kmh;
    float engine_temp_c;
    bool ev_mode_requested;
} PowerRequest_t;

typedef struct {
    float engine_power_kw;
    float motor_power_kw;
    float generator_power_kw;
    bool engine_on;
} PowerDistribution_t;

PowerDistribution_t compute_power_split(const PowerRequest_t* req) {
    PowerDistribution_t dist = {0};

    /* EV mode: battery only if SOC sufficient and low power request */
    if (req->ev_mode_requested ||
        (req->battery_soc_percent > 40.0f &&
         req->driver_power_request_kw < 30.0f &&
         req->vehicle_speed_kmh < 60.0f)) {
        dist.engine_on = false;
        dist.motor_power_kw = req->driver_power_request_kw;
        return dist;
    }

    /* Series hybrid: engine generates electricity only */
    if (req->battery_soc_percent < 20.0f) {
        dist.engine_on = true;
        dist.engine_power_kw = 40.0f;  /* Optimal BSFC point */
        dist.generator_power_kw = 35.0f;
        dist.motor_power_kw = req->driver_power_request_kw;
        return dist;
    }

    /* Parallel hybrid: both engine and motor for high power */
    if (req->driver_power_request_kw > 50.0f) {
        dist.engine_on = true;
        dist.engine_power_kw = req->driver_power_request_kw * 0.7f;
        dist.motor_power_kw = req->driver_power_request_kw * 0.3f;
        return dist;
    }

    /* Normal operation: engine primary, motor assist */
    dist.engine_on = true;
    dist.engine_power_kw = req->driver_power_request_kw;
    dist.motor_power_kw = 0.0f;
    return dist;
}
```

### Optimization-Based Power Split (ECMS)

```c
/* Equivalent Consumption Minimization Strategy */
typedef struct {
    float fuel_mass_rate_kg_s;
    float battery_power_kw;
    float motor_efficiency;
    float engine_efficiency;
} CostFunction_t;

/* ECMS cost function: minimize equivalent fuel consumption */
float compute_equivalent_fuel_rate(
    float engine_fuel_rate,
    float battery_power,
    float equivalence_factor) {

    /* Convert electric power to equivalent fuel */
    float battery_fuel_equivalent = 0.0f;

    if (battery_power > 0.0f) {
        /* Discharging: add equivalent fuel cost */
        battery_fuel_equivalent = battery_power * equivalence_factor;
    } else {
        /* Charging: subtract (regenerative benefit) */
        battery_fuel_equivalent = battery_power * equivalence_factor * 0.7f;
    }

    return engine_fuel_rate + battery_fuel_equivalent;
}

/* Optimal torque split via gradient descent */
typedef struct {
    float engine_torque_nm;
    float motor_torque_nm;
    float total_fuel_rate;
} OptimalSplit_t;

OptimalSplit_t optimize_torque_split(
    float total_torque_request,
    float engine_speed,
    float battery_soc) {

    OptimalSplit_t optimal = {0};
    float min_fuel = FLT_MAX;

    /* Discretize torque split: 0% to 100% in 5% steps */
    for (float motor_ratio = 0.0f; motor_ratio <= 1.0f; motor_ratio += 0.05f) {
        float motor_torque = total_torque_request * motor_ratio;
        float engine_torque = total_torque_request * (1.0f - motor_ratio);

        /* Check constraints */
        if (!is_torque_feasible(engine_torque, engine_speed, ENGINE)) {
            continue;
        }
        if (!is_torque_feasible(motor_torque, engine_speed, MOTOR)) {
            continue;
        }

        /* Compute fuel consumption */
        float fuel_rate = compute_instantaneous_fuel(
            engine_torque, engine_speed);

        /* SOC sustainability constraint */
        float soc_penalty = compute_soc_penalty(battery_soc, motor_torque);
        float total_cost = fuel_rate + soc_penalty;

        if (total_cost < min_fuel) {
            min_fuel = total_cost;
            optimal.engine_torque_nm = engine_torque;
            optimal.motor_torque_nm = motor_torque;
            optimal.total_fuel_rate = fuel_rate;
        }
    }

    return optimal;
}
```

## Torque Management

### Torque Request Arbitration

```c
/* Torque arbitration - multiple sources, single output */
typedef enum {
    TORQUE_SOURCE_DRIVER,      /* Accelerator pedal */
    TORQUE_SOURCE_CRUISE,      /* Adaptive cruise control */
    TORQUE_SOURCE_AEB,         /* Autonomous emergency braking */
    TORQUE_SOURCE_ESC,         /* Electronic stability control */
    TORQUE_SOURCE_LIMP_HOME,   /* Degraded mode */
    TORQUE_SOURCE_COUNT
} TorqueSource_t;

typedef struct {
    float torque_request_nm;
    float torque_rate_limit;
    uint32_t source_valid_mask;
    TorqueSource_t active_source;
} TorqueArbiter_t;

/* Priority-based torque arbitration */
float arbitrate_torque_request(const TorqueArbiter_t* arbiter) {
    /* Safety-critical sources have highest priority */

    /* AEB override: emergency braking */
    if (arbiter->source_valid_mask & (1U << TORQUE_SOURCE_AEB)) {
        return -200.0f;  /* Maximum braking torque */
    }

    /* ESC override: stability intervention */
    if (arbiter->source_valid_mask & (1U << TORQUE_SOURCE_ESC)) {
        return arbiter->torque_request_nm;  /* ESC determines torque */
    }

    /* Limp home mode */
    if (arbiter->source_valid_mask & (1U << TORQUE_SOURCE_LIMP_HOME)) {
        return fminf(arbiter->torque_request_nm, 100.0f);
    }

    /* Cruise control */
    if (arbiter->source_valid_mask & (1U << TORQUE_SOURCE_CRUISE)) {
        return arbiter->torque_request_nm;
    }

    /* Default: driver request */
    return arbiter->torque_request_nm;
}
```

### Torque Smoothing Filter

```c
/* First-order low-pass filter for torque smoothing */
typedef struct {
    float filtered_torque_nm;
    float alpha;  /* Filter coefficient (0.0 to 1.0) */
} TorqueFilter_t;

TorqueFilter_t g_torque_filter = {
    .filtered_torque_nm = 0.0f,
    .alpha = 0.3f  /* Tunable: higher = faster response */
};

float apply_torque_filter(float raw_torque, float dt) {
    /* Adaptive filter based on torque rate */
    float torque_rate = fabsf(raw_torque - g_torque_filter.filtered_torque_nm);

    /* Faster response for sudden changes */
    if (torque_rate > 50.0f) {
        g_torque_filter.alpha = 0.7f;
    } else if (torque_rate > 20.0f) {
        g_torque_filter.alpha = 0.5f;
    } else {
        g_torque_filter.alpha = 0.3f;
    }

    /* First-order filter */
    g_torque_filter.filtered_torque_nm =
        g_torque_filter.alpha * raw_torque +
        (1.0f - g_torque_filter.alpha) * g_torque_filter.filtered_torque_nm;

    return g_torque_filter.filtered_torque_nm;
}
```

## Regenerative Braking

### Blended Braking Strategy

```c
/* Blend regenerative and friction braking */
typedef struct {
    float total_brake_request_nm;
    float vehicle_speed_kmh;
    float battery_soc_percent;
    float battery_temp_c;
    float motor_speed_rpm;
} BrakeRequest_t;

typedef struct {
    float regen_brake_nm;
    float friction_brake_nm;
    bool regen_available;
} BlendedBrake_t;

BlendedBrake_t compute_blended_braking(const BrakeRequest_t* req) {
    BlendedBrake_t result = {0};

    /* Check regen availability */
    result.regen_available = true;

    /* Regen unavailable conditions */
    if (req->battery_soc_percent > 95.0f) {
        result.regen_available = false;  /* Battery full */
    }
    if (req->battery_temp_c > 50.0f) {
        result.regen_available = false;  /* Battery over-temp */
    }
    if (req->motor_speed_rpm > MAX_MOTOR_SPEED_RPM) {
        result.regen_available = false;  /* Motor overspeed */
    }
    if (req->vehicle_speed_kmh < 3.0f) {
        result.regen_available = false;  /* Too slow for regen */
    }

    if (!result.regen_available) {
        result.friction_brake_nm = req->total_brake_request_nm;
        return result;
    }

    /* Maximum regen torque (speed-dependent) */
    float max_regen = compute_max_regen_torque(
        req->motor_speed_rpm, req->battery_temp_c);

    /* Apply regen up to limit, friction fills remainder */
    result.regen_brake_nm = fminf(req->total_brake_request_nm, max_regen);
    result.friction_brake_nm = req->total_brake_request_nm - result.regen_brake_nm;

    /* Smooth transition to prevent jerk */
    result.regen_brake_nm = apply_brake_blend_filter(result.regen_brake_nm);

    return result;
}
```

## Fuel Efficiency Optimization

### Engine Start/Stop Strategy

```c
/* Automatic engine start/stop for fuel saving */
typedef struct {
    bool vehicle_stopped;
    float stop_duration_s;
    float brake_pedal_force;
    float battery_soc;
    float cabin_temp_request;
    float engine_temp;
} StopCondition_t;

bool should_stop_engine(const StopCondition_t* cond) {
    /* All conditions must be met for auto-stop */
    if (!cond->vehicle_stopped) return false;
    if (cond->stop_duration_s < 0.5f) return false;  /* Debounce */
    if (cond->brake_pedal_force < MIN_BRAKE_FORCE) return false;
    if (cond->battery_soc < 60.0f) return false;  /* Need charge margin */
    if (cond->engine_temp < 70.0f) return false;  /* Warm-up phase */

    /* Climate control priority */
    if (cond->cabin_temp_request > 25.0f) return false;  /* A/C needed */
    if (cond->cabin_temp_request < 15.0f) return false;  /* Heating needed */

    return true;
}

bool should_restart_engine(const StopCondition_t* cond) {
    /* Any condition triggers restart */
    if (!cond->vehicle_stopped) return true;  /* Driver wants to move */
    if (cond->brake_pedal_force < RELEASE_BRAKE_FORCE) return true;
    if (cond->battery_soc < 50.0f) return true;  /* Need charging */
    if (cond->cabin_temp_request > 26.0f) return true;  /* A/C demand */
    if (cond->cabin_temp_request < 14.0f) return true;  /* Heat demand */

    return false;
}
```

## AUTOSAR Implementation

### Software Component Design

```xml
<!-- EnergyManager SwComponentType (ARXML) -->
<APPLICATION-SW-COMPONENT-TYPE>
  <SHORT-NAME>EnergyManager</SHORT-NAME>

  <!-- Port Interfaces -->
  <PORTS>
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>DriverDemandPort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/DriverDemand_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <R-PORT-PROTOTYPE>
      <SHORT-NAME>BatteryStatePort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/BatteryState_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <P-PORT-PROTOTYPE>
      <SHORT-NAME>EngineCommandPort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/EngineCommand_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>

    <P-PORT-PROTOTYPE>
      <SHORT-NAME>MotorCommandPort</Short-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/MotorCommand_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>
  </PORTS>

  <!-- Internal Behavior -->
  <INTERNAL-BEHAVIOR>
    <RUNNABLE-ENTITIES>
      <RUNNABLE-ENTITY>
        <SHORT-NAME>EnergyControl_10ms</SHORT-NAME>
        <BEGIN-PERIOD>0.01</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>
    </RUNNABLE-ENTITIES>
  </INTERNAL-BEHAVIOR>
</APPLICATION-SW-COMPONENT-TYPE>
```

### Runnable Implementation

```c
/* Energy Management Runnable - 10ms cycle */
#include "Rte_EnergyManager.h"

void EnergyManager_EnergyControl_10ms_Runnable(void) {
    /* Read inputs from R-ports */
    DriverDemand_t driver_demand;
    Rte_Read_EnergyManager_DriverDemandPort_Value(&driver_demand);

    BatteryState_t battery_state;
    Rte_Read_EnergyManager_BatteryStatePort_Value(&battery_state);

    /* Compute optimal power split */
    PowerRequest_t power_req = {
        .driver_power_request_kw = driver_demand.torque_nm * driver_demand.speed_rpm / 9550.0f,
        .battery_soc_percent = battery_state.soc,
        .vehicle_speed_kmh = driver_demand.vehicle_speed,
        .engine_temp_c = battery_state.engine_temp
    };

    PowerDistribution_t power_dist = compute_power_split(&power_req);

    /* Torque arbitration and limiting */
    float final_engine_torque = limit_engine_torque(
        power_dist.engine_power_kw, driver_demand.speed_rpm);
    float final_motor_torque = limit_motor_torque(
        power_dist.motor_power_kw, driver_demand.speed_rpm);

    /* Write outputs to P-ports */
    Rte_Write_EnergyManager_EngineCommandPort_Torque(
        final_engine_torque);
    Rte_Write_EnergyManager_MotorCommandPort_Torque(
        final_motor_torque);

    /* Update energy metrics */
    update_energy_metrics(&power_dist, &battery_state);
}
```

## Safety Mechanisms (ISO 26262)

### Torque Plausibility Check

```c
/* ASIL D: Torque request validation */
typedef struct {
    float torque_request_nm;
    float speed_rpm;
    uint8_t rolling_counter;
    uint16_t crc;
} TorqueMessage_t;

typedef enum {
    TORQUE_VALID,
    TORQUE_CRC_ERROR,
    TORQUE_COUNTER_ERROR,
    TORQUE_RANGE_ERROR,
    TORQUE_RATE_ERROR
} TorqueValidation_t;

TorqueValidation_t validate_torque_request(
    const TorqueMessage_t* msg,
    TorqueMessage_t* prev_msg) {

    /* CRC check */
    uint16_t computed_crc = compute_torque_crc(msg);
    if (computed_crc != msg->crc) {
        return TORQUE_CRC_ERROR;
    }

    /* Rolling counter check */
    uint8_t expected_counter = (prev_msg->rolling_counter + 1U) & 0x0FU;
    if (msg->rolling_counter != expected_counter) {
        /* Allow one missed message */
        if (msg->rolling_counter != ((expected_counter + 1U) & 0x0FU)) {
            return TORQUE_COUNTER_ERROR;
        }
    }

    /* Range check */
    if (msg->torque_request_nm < -200.0f || msg->torque_request_nm > 400.0f) {
        return TORQUE_RANGE_ERROR;
    }

    /* Rate check (max 500 Nm/s) */
    float dt = 0.01f;  /* 10ms cycle */
    float torque_rate = fabsf(msg->torque_request_nm - prev_msg->torque_request_nm) / dt;
    if (torque_rate > 500.0f) {
        return TORQUE_RATE_ERROR;
    }

    return TORQUE_VALID;
}

/* Safe state on fault detection */
void enter_torque_safe_state(TorqueValidation_t fault) {
    switch (fault) {
        case TORQUE_CRC_ERROR:
        case TORQUE_COUNTER_ERROR:
            /* Communication fault - request zero torque */
            request_safe_torque(0.0f);
            break;

        case TORQUE_RANGE_ERROR:
        case TORQUE_RATE_ERROR:
            /* Implausible request - use degraded torque */
            request_safe_torque(DEGRADED_TORQUE_LIMIT_NM);
            break;

        default:
            break;
    }

    /* Report fault to diagnostics */
    Dem_ReportErrorStatus(DEM_EVENT_TORQUE_FAULT, DEM_EVENT_STATUS_FAILED);
}
```

## Approach

1. **Define energy management strategy**
   - Select rule-based or optimization-based approach
   - Tune parameters for fuel economy vs. drivability
   - Define operating mode transitions

2. **Implement torque management**
   - Arbitrate multiple torque sources
   - Apply rate limiting and smoothing
   - Implement plausibility checks

3. **Develop regenerative braking**
   - Blend regen and friction braking
   - Implement smooth transition logic
   - Handle edge cases (low SOC, cold battery)

4. **Integrate with AUTOSAR**
   - Design SwComponent with appropriate ports
   - Configure runnables and timing
   - Generate RTE and integrate

5. **Validate and calibrate**
   - MIL/SIL testing of control algorithms
   - HIL testing with production ECU
   - Vehicle calibration for drivability

## Deliverables

- Energy management strategy specification
- Control algorithm implementation (C/Model)
- AUTOSAR SWC integration code
- Calibration parameter database
- Test results (MIL/SIL/HIL/Vehicle)
- ISO 26262 safety case documentation

## Related Context
- @context/skills/powertrain/battery-management.md
- @context/skills/autosar/classic-platform.md
- @context/skills/safety/iso-26262-overview.md
- @context/skills/chassis/abs-control.md

## Tools Required
- MATLAB/Simulink (algorithm development)
- Vector CANoe/CANalyzer (network analysis)
- ETAS INCA (calibration)
- dSPACE HIL (hardware-in-loop testing)
- Static analyzer (Polyspace/Klocwork)
