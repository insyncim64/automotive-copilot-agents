---
name: chassis-abs-control
description: "Use when: Skill: ABS Control for Automotive Chassis Systems topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: ABS Control for Automotive Chassis Systems

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/chassis/abs-control.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate
- User asks about anti-lock braking system (ABS) algorithms or implementation
- User needs wheel slip control strategies for braking systems
- User is developing brake pressure modulation or hydraulic control
- User requests ABS integration with ESC/EBD systems
- User needs ISO 26262 ASIL D safety mechanisms for brake systems
- User asks about AUTOSAR implementation patterns for chassis control
- User is implementing fail-operational brake-by-wire systems

## Standards Compliance
- ISO 26262:2018 (Functional Safety) - ASIL D for primary brake control
- ASPICE Level 3 - Model-based development process
- AUTOSAR 4.4 - Chassis domain architecture
- ISO 21434:2021 (Cybersecurity) - Brake command authentication
- SAE J1979 - OBD-II brake system PIDs
- UN ECE R13-H - ABS performance requirements
- UN ECE R155 - Cybersecurity management system

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Slip ratio target | 10-30 | percentage |
| Wheel speed | 0-300 | km/h |
| Brake pressure | 0-200 | bar |
| Pressure modulation frequency | 5-20 | Hz |
| ABS cycle time | 1-5 | ms |
| Deceleration | 0-12 | m/s² |
| Road friction coefficient | 0.1-1.2 | μ |
| System voltage | 9-16 | V |
| Operating temperature | -40 to 125 | °C |

## ABS Architecture

```
+----------------------------------------------------------+
|                    ABS Control ECU                        |
|  +------------------+  +------------------+              |
|  |  Slip Controller |  |  Pressure Ctrl   |              |
|  +------------------+  +------------------+              |
|           |                     |                        |
|  +------------------+  +------------------+              |
|  |  Wheel Speed     |  |  Valve Driver    |             |
|  |  Processing      |  |  (H-bridge)      |             |
|  +------------------+  +------------------+              |
+--------------------------|-------------------------------+
                           |
         +-----------------+-----------------+
         |                 |                 |
+--------v--------+ +------v------+ +--------v--------+
|  Front Left     | | Front Right | | Rear Left/Right |
|  Wheel Speed    | | Wheel Speed | | Wheel Speed     |
|  Sensor         | | Sensor      | | Sensors         |
+-----------------+ +-------------+ +-----------------+
         |                 |                 |
+--------v--------+ +------v------+ +--------v--------+
|  FL Solenoid    | | FR Solenoid | | RL/RR Solenoids |
|  Valve          | | Valve       | | Valves          |
+-----------------+ +-------------+ +-----------------+
```

## Wheel Slip Control

### Slip Ratio Calculation

```c
/* Wheel slip ratio computation - fundamental ABS parameter */
typedef struct {
    float wheel_speed_fl;      /* Front left wheel speed */
    float wheel_speed_fr;      /* Front right wheel speed */
    float wheel_speed_rl;      /* Rear left wheel speed */
    float wheel_speed_rr;      /* Rear right wheel speed */
    float vehicle_speed_ref;   /* Estimated vehicle speed */
    float road_friction_est;   /* Estimated road friction coefficient */
} WheelSpeeds_t;

typedef struct {
    float slip_ratio_fl;       /* Front left slip ratio */
    float slip_ratio_fr;       /* Front right slip ratio */
    float slip_ratio_rl;       /* Rear left slip ratio */
    float slip_ratio_rr;       /* Rear right slip ratio */
    float slip_ratio_avg;      /* Average slip ratio */
    float slip_rate_fl;        /* Front left slip rate (derivative) */
    float slip_rate_fr;        /* Front right slip rate */
    float slip_rate_rl;        /* Rear left slip rate */
    float slip_rate_rr;        /* Rear right slip rate */
} SlipInfo_t;

/* Compute slip ratio for each wheel
 * Slip ratio = (V_vehicle - V_wheel) / V_vehicle * 100%
 * Positive slip = braking (wheel slower than vehicle)
 */
SlipInfo_t compute_slip_ratios(const WheelSpeeds_t* speeds) {
    SlipInfo_t slip = {0};
    static float prev_slip_fl = 0.0f, prev_slip_fr = 0.0f;
    static float prev_slip_rl = 0.0f, prev_slip_rr = 0.0f;
    const float dt = 0.001f;  /* 1ms cycle time */

    /* Avoid division by zero at low speeds */
    float ref_speed = fmaxf(speeds->vehicle_speed_ref, 1.0f);

    /* Compute slip ratio for each wheel */
    slip.slip_ratio_fl = (ref_speed - speeds->wheel_speed_fl) / ref_speed * 100.0f;
    slip.slip_ratio_fr = (ref_speed - speeds->wheel_speed_fr) / ref_speed * 100.0f;
    slip.slip_ratio_rl = (ref_speed - speeds->wheel_speed_rl) / ref_speed * 100.0f;
    slip.slip_ratio_rr = (ref_speed - speeds->wheel_speed_rr) / ref_speed * 100.0f;

    /* Compute slip rate (time derivative for trend detection) */
    slip.slip_rate_fl = (slip.slip_ratio_fl - prev_slip_fl) / dt;
    slip.slip_rate_fr = (slip.slip_ratio_fr - prev_slip_fr) / dt;
    slip.slip_rate_rl = (slip.slip_ratio_rl - prev_slip_rl) / dt;
    slip.slip_rate_rr = (slip.slip_ratio_rr - prev_slip_rr) / dt;

    /* Store for next cycle */
    prev_slip_fl = slip.slip_ratio_fl;
    prev_slip_fr = slip.slip_ratio_fr;
    prev_slip_rl = slip.slip_ratio_rl;
    prev_slip_rr = slip.slip_ratio_rr;

    /* Average slip ratio for overall control */
    slip.slip_ratio_avg = (slip.slip_ratio_fl + slip.slip_ratio_fr +
                           slip.slip_ratio_rl + slip.slip_ratio_rr) / 4.0f;

    return slip;
}
```

### Target Slip Ratio Optimization

```c
/* Peak friction detection and target slip optimization */
typedef struct {
    float slip_ratio;
    float friction_coefficient;
    float friction_slope;      /* d(mu)/d(slip) */
    bool peak_detected;
} FrictionCurve_t;

/* Tire friction curve model (Burckhardt model) */
float compute_friction_coefficient(float slip_ratio, float road_type) {
    /* Burckhardt parameters for different road surfaces */
    static const float road_params[3][3] = {
        /* {c1, c2, c3} - dry asphalt */
        {1.28f, 23.99f, 0.48f},
        /* {c1, c2, c3} - wet asphalt */
        {1.00f, 15.00f, 0.45f},
        /* {c1, c2, c3} - ice/snow */
        {0.20f, 5.00f, 0.30f}
    };

    const float* params = road_params[(int)road_type];
    const float c1 = params[0];
    const float c2 = params[1];
    const float c3 = params[2];

    /* Burckhardt equation: mu = c1 * (1 - exp(-c2 * slip)) - c3 * slip */
    float slip_decimal = slip_ratio / 100.0f;
    float friction = c1 * (1.0f - expf(-c2 * slip_decimal)) - c3 * slip_decimal;

    return friction;
}

/* Find optimal slip ratio for peak friction */
float find_optimal_slip_ratio(float road_type) {
    /* Scan slip ratio from 0% to 30% in 1% steps */
    float best_slip = 15.0f;
    float best_friction = 0.0f;

    for (float slip = 5.0f; slip <= 30.0f; slip += 1.0f) {
        float friction = compute_friction_coefficient(slip, road_type);
        if (friction > best_friction) {
            best_friction = friction;
            best_slip = slip;
        }
    }

    return best_slip;
}
```

## Pressure Modulation Control

### Three-Phase ABS Cycle

```c
/* ABS pressure modulation states */
typedef enum {
    ABS_STATE_INCREASE,      /* Pressure increase - apply brake */
    ABS_STATE_HOLD,          /* Pressure hold - maintain current */
    ABS_STATE_DECREASE,      /* Pressure decrease - release brake */
    ABS_STATE_OFF            /* ABS inactive - normal braking */
} AbsState_t;

typedef struct {
    AbsState_t state_fl;
    AbsState_t state_fr;
    AbsState_t state_rl;
    AbsState_t state_rr;
    float target_pressure_fl;
    float target_pressure_fr;
    float target_pressure_rl;
    float target_pressure_rr;
    uint32_t abs_active_time_ms;
} AbsControl_t;

/* ABS state machine for each wheel */
AbsState_t abs_state_machine(
    float current_slip,
    float target_slip,
    float slip_rate,
    float current_pressure,
    float pressure_error) {

    /* Hysteresis bands to prevent chattering */
    const float slip_hysteresis = 3.0f;      /* ±3% slip tolerance */
    const float slip_rate_threshold = 50.0f; /* %/s */

    /* State transition logic */
    if (current_slip < (target_slip - slip_hysteresis)) {
        /* Slip too low - can apply more brake pressure */
        return ABS_STATE_INCREASE;
    }
    else if (current_slip > (target_slip + slip_hysteresis)) {
        /* Slip too high - must reduce pressure to prevent lockup */
        return ABS_STATE_DECREASE;
    }
    else if (slip_rate > slip_rate_threshold) {
        /* Slip increasing too fast - preemptive decrease */
        return ABS_STATE_DECREASE;
    }
    else if (slip_rate < -slip_rate_threshold) {
        /* Slip decreasing too fast - preemptive increase */
        return ABS_STATE_INCREASE;
    }
    else {
        /* Within tolerance band - hold current pressure */
        return ABS_STATE_HOLD;
    }
}
```

### PID Pressure Controller

```c
/* PID controller for brake pressure modulation */
typedef struct {
    float kp;                /* Proportional gain */
    float ki;                /* Integral gain */
    float kd;                /* Derivative gain */
    float integral_sum;      /* Accumulated integral */
    float prev_error;        /* Previous error for derivative */
    float integral_limit;    /* Anti-windup limit */
    float output_limit;      /* Output saturation limit */
} PidController_t;

typedef struct {
    PidController_t pid_fl;
    PidController_t pid_fr;
    PidController_t pid_rl;
    PidController_t pid_rr;
} AbsPidControllers_t;

static AbsPidControllers_t g_abs_controllers = {
    .pid_fl = {
        .kp = 2.5f,
        .ki = 0.1f,
        .kd = 0.05f,
        .integral_sum = 0.0f,
        .prev_error = 0.0f,
        .integral_limit = 50.0f,
        .output_limit = 180.0f
    },
    /* Initialize other wheels similarly */
};

/* PID computation for brake pressure */
float pid_compute_pressure(
    PidController_t* ctrl,
    float setpoint_pressure,
    float actual_pressure,
    float dt) {

    /* Compute error */
    float error = setpoint_pressure - actual_pressure;

    /* Proportional term */
    float p_term = ctrl->kp * error;

    /* Integral term with anti-windup */
    ctrl->integral_sum += error * dt;
    ctrl->integral_sum = fminf(fmaxf(ctrl->integral_sum, -ctrl->integral_limit),
                                ctrl->integral_limit);
    float i_term = ctrl->ki * ctrl->integral_sum;

    /* Derivative term (on measurement to avoid derivative kick) */
    float derivative = (actual_pressure - ctrl->prev_error) / dt;
    float d_term = -ctrl->kd * derivative;  /* Negative: derivative on measurement */

    /* Store for next cycle */
    ctrl->prev_error = actual_pressure;

    /* Compute total output */
    float output = p_term + i_term + d_term;

    /* Output saturation */
    output = fminf(fmaxf(output, 0.0f), ctrl->output_limit);

    return output;
}
```

## Hydraulic Unit Control

### Solenoid Valve Driver

```c
/* High-side/low-side H-bridge driver for solenoid valves */
typedef struct {
    uint8_t high_side_pwm;   /* PWM duty cycle 0-100% */
    bool low_side_enable;    /* Enable low-side switch */
    bool diagnostics_enable; /* Enable current sense */
} ValveDriverCmd_t;

typedef struct {
    float actual_current_a;  /* Measured coil current */
    bool open_circuit_fault;
    bool short_circuit_fault;
    bool overtemp_fault;
    uint16_t temperature_c;  /* Driver temperature */
} ValveDriverStatus_t;

/* Solenoid valve control with current regulation */
ValveDriverCmd_t control_solenoid_valve(
    float target_pressure_bar,
    float actual_pressure_bar,
    ValveDriverStatus_t* status) {

    ValveDriverCmd_t cmd = {0};

    /* Check for faults */
    if (status->open_circuit_fault ||
        status->short_circuit_fault ||
        status->overtemp_fault) {
        /* Fault detected - disable valve */
        cmd.high_side_pwm = 0U;
        cmd.low_side_enable = false;
        return cmd;
    }

    /* Compute required PWM based on pressure error */
    float pressure_error = target_pressure_bar - actual_pressure_bar;

    /* Deadband to prevent valve chatter */
    const float deadband_bar = 2.0f;
    if (fabsf(pressure_error) < deadband_bar) {
        cmd.high_side_pwm = 0U;  /* Hold position */
    }
    else if (pressure_error > 0.0f) {
        /* Need to increase pressure - open inlet valve */
        float pwm_duty = pressure_error * 2.0f;  /* Gain factor */
        cmd.high_side_pwm = (uint8_t)fminf(fmaxf(pwm_duty, 10.0f), 95.0f);
    }
    else {
        /* Need to decrease pressure - open outlet valve */
        float pwm_duty = -pressure_error * 3.0f;  /* Higher gain for release */
        cmd.high_side_pwm = (uint8_t)fminf(fmaxf(pwm_duty, 15.0f), 95.0f);
    }

    cmd.low_side_enable = (cmd.high_side_pwm > 0U);

    return cmd;
}
```

### Pump Motor Control

```c
/* ABS hydraulic pump motor control */
typedef struct {
    bool motor_enable;
    uint8_t target_speed_pwm;
    bool run_continuous;
} PumpMotorCmd_t;

typedef struct {
    bool motor_running;
    uint16_t actual_speed_rpm;
    float motor_current_a;
    bool overcurrent_fault;
    bool stalled_fault;
} PumpMotorStatus_t;

/* Pump motor control to maintain hydraulic pressure */
PumpMotorCmd_t control_pump_motor(
    float target_pressure_bar,
    float actual_pressure_bar,
    PumpMotorStatus_t* status) {

    PumpMotorCmd_t cmd = {0};

    /* Fault check */
    if (status->overcurrent_fault || status->stalled_fault) {
        cmd.motor_enable = false;
        return cmd;
    }

    /* Pressure-based pump control */
    const float pump_activation_threshold_bar = 150.0f;
    const float pump_deactivation_threshold_bar = 180.0f;

    if (actual_pressure_bar < pump_activation_threshold_bar) {
        /* Pressure low - run pump */
        cmd.motor_enable = true;
        cmd.target_speed_pwm = 80U;  /* 80% PWM */
        cmd.run_continuous = true;
    }
    else if (actual_pressure_bar > pump_deactivation_threshold_bar) {
        /* Pressure sufficient - stop pump */
        cmd.motor_enable = false;
        cmd.target_speed_pwm = 0U;
        cmd.run_continuous = false;
    }
    else {
        /* Hysteresis band - maintain current state */
        cmd.motor_enable = status->motor_running;
        cmd.target_speed_pwm = status->motor_running ? 60U : 0U;
    }

    return cmd;
}
```

## ISO 26262 Safety Mechanisms

### Sensor Plausibility Check

```c
/* ASIL D: Wheel speed sensor plausibility */
typedef enum {
    SENSOR_VALID,
    SENSOR_OUT_OF_RANGE,
    SENSOR_STUCK_AT,
    SENSOR_IMPLAUSIBLE,
    SENSOR_TIMEOUT
} SensorValidation_t;

typedef struct {
    float wheel_speed;
    uint32_t timestamp_ms;
    uint16_t signal_counter;
} WheelSpeedSample_t;

SensorValidation_t validate_wheel_speed_sensor(
    const WheelSpeedSample_t* current,
    const WheelSpeedSample_t* previous,
    float vehicle_speed_ref) {

    /* Range check: 0-300 km/h */
    if (current->wheel_speed < 0.0f || current->wheel_speed > 300.0f) {
        return SENSOR_OUT_OF_RANGE;
    }

    /* Stuck-at detection: same value for > 500ms */
    const uint32_t stuck_threshold_ms = 500U;
    if ((current->timestamp_ms - previous->timestamp_ms) > stuck_threshold_ms) {
        if (fabsf(current->wheel_speed - previous->wheel_speed) < 0.1f) {
            return SENSOR_STUCK_AT;
        }
    }

    /* Plausibility vs. vehicle reference */
    /* Individual wheel speed should not differ from vehicle speed by > 50 km/h */
    if (fabsf(current->wheel_speed - vehicle_speed_ref) > 50.0f) {
        return SENSOR_IMPLAUSIBLE;
    }

    /* Cross-check with other wheels (all wheels should be within 20 km/h of each other) */
    /* This check performed at system level */

    /* Counter check (if applicable) */
    uint16_t expected_counter = (previous->signal_counter + 1U) & 0x0FU;
    if (current->signal_counter != expected_counter) {
        /* Allow one missed message */
        if (current->signal_counter != ((expected_counter + 1U) & 0x0FU)) {
            return SENSOR_TIMEOUT;
        }
    }

    return SENSOR_VALID;
}
```

### Dual-Channel Architecture

```c
/* ASIL D: Dual-channel ABS with comparison */
typedef struct {
    float slip_ratio_primary;
    float slip_ratio_monitor;
    float pressure_command_primary;
    float pressure_command_monitor;
    bool disagreement_flag;
} DualChannelAbs_t;

static DualChannelAbs_t g_dual_channel_abs = {0};

/* Compare primary and monitor channel computations */
bool dual_channel_comparison(
    float primary_value,
    float monitor_value,
    float tolerance) {

    float diff = fabsf(primary_value - monitor_value);
    return (diff <= tolerance);
}

/* Execute dual-channel ABS computation */
float compute_abs_pressure_dual_channel(
    const WheelSpeeds_t* speeds,
    const SlipInfo_t* slip_info) {

    /* Channel 1: Primary computation */
    const float target_slip_primary = 20.0f;
    float slip_error_primary = target_slip_primary - slip_info->slip_ratio_avg;
    float pressure_primary = slip_error_primary * 3.0f;  /* Simple P-controller */

    /* Channel 2: Monitor computation (diverse algorithm) */
    const float target_slip_monitor = 18.0f;  /* Slightly different target */
    float slip_error_monitor = target_slip_monitor - slip_info->slip_ratio_avg;
    float pressure_monitor = slip_error_monitor * 2.8f;  /* Different gain */

    /* Compare outputs */
    const float comparison_tolerance_bar = 10.0f;
    g_dual_channel_abs.disagreement_flag =
        !dual_channel_comparison(pressure_primary, pressure_monitor,
                                  comparison_tolerance_bar);

    if (g_dual_channel_abs.disagreement_flag) {
        /* Enter safe state: reduced braking */
        return 50.0f;  /* Degraded pressure limit */
    }

    /* Use primary output if channels agree */
    return pressure_primary;
}
```

### Fail-Operational Design

```c
/* Degraded mode operation on fault detection */
typedef enum {
    ABS_MODE_NORMAL,         /* Full ABS functionality */
    ABS_MODE_DEGRADED,       /* Reduced functionality */
    ABS_MODE_MANUAL,         /* No ABS, manual braking only */
    ABS_MODE_FAILED          /* Complete failure - safe state */
} AbsOperatingMode_t;

AbsOperatingMode_t g_abs_mode = ABS_MODE_NORMAL;

/* Determine operating mode based on fault status */
AbsOperatingMode_t determine_abs_mode(
    uint32_t fault_mask,
    SensorValidation_t sensor_status) {

    /* Critical faults: disable ABS completely */
    if (fault_mask & FAULT_MASK_CRITICAL) {
        return ABS_MODE_FAILED;
    }

    /* Single sensor fault: degraded mode */
    if (sensor_status == SENSOR_STUCK_AT ||
        sensor_status == SENSOR_IMPLAUSIBLE) {
        return ABS_MODE_DEGRADED;
    }

    /* Multiple sensor faults: manual mode */
    uint8_t fault_count = count_set_bits(fault_mask);
    if (fault_count >= 2U) {
        return ABS_MODE_MANUAL;
    }

    /* No faults: normal operation */
    return ABS_MODE_NORMAL;
}

/* Apply degraded mode control strategy */
float apply_degraded_mode_control(
    float normal_pressure,
    AbsOperatingMode_t mode,
    uint8_t failed_wheel_mask) {

    switch (mode) {
        case ABS_MODE_NORMAL:
            return normal_pressure;

        case ABS_MODE_DEGRADED:
            /* Reduce maximum pressure in degraded mode */
            return fminf(normal_pressure, 120.0f);

        case ABS_MODE_MANUAL:
            /* No pressure modulation - direct pedal feel */
            return normal_pressure * 0.8f;  /* Conservative limit */

        case ABS_MODE_FAILED:
        default:
            /* Safe state: no active pressure control */
            return 0.0f;
    }
}
```

## AUTOSAR Implementation

### Software Component Design

```xml
<!-- AbsController SwComponentType (ARXML) -->
<APPLICATION-SW-COMPONENT-TYPE>
  <SHORT-NAME>AbsController</SHORT-NAME>

  <!-- Port Interfaces -->
  <PORTS>
    <!-- R-Ports: Receive wheel speed from sensors -->
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>WheelSpeed_FL_Port</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/WheelSpeed_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <R-PORT-PROTOTYPE>
      <SHORT-NAME>WheelSpeed_FR_Port</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/WheelSpeed_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <!-- R-Port: Vehicle speed reference -->
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>VehicleSpeedRef_Port</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/VehicleSpeed_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <!-- P-Ports: Send valve commands -->
    <P-PORT-PROTOTYPE>
      <SHORT-NAME>ValveCommand_FL_Port</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/ValveCommand_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>

    <P-PORT-PROTOTYPE>
      <SHORT-NAME>ValveCommand_FR_Port</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/ValveCommand_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>

    <!-- P-Port: Pump motor command -->
    <P-PORT-PROTOTYPE>
      <SHORT-NAME>PumpMotorCommand_Port</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/PumpMotor_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>
  </PORTS>

  <!-- Internal Behavior -->
  <INTERNAL-BEHAVIOR>
    <RUNNABLE-ENTITIES>
      <RUNNABLE-ENTITY>
        <SHORT-NAME>AbsControl_2ms</SHORT-NAME>
        <BEGIN-PERIOD>0.002</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>

      <RUNNABLE-ENTITY>
        <SHORT-NAME>AbsDiagnostics_10ms</SHORT-NAME>
        <BEGIN-PERIOD>0.01</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>
    </RUNNABLE-ENTITIES>
  </INTERNAL-BEHAVIOR>
</APPLICATION-SW-COMPONENT-TYPE>
```

### Runnable Implementation

```c
/* ABS Control Runnable - 2ms cycle */
#include "Rte_AbsController.h"

void AbsController_AbsControl_2ms_Runnable(void) {
    /* Read wheel speeds from R-ports */
    WheelSpeed_t wheel_speed_fl, wheel_speed_fr, wheel_speed_rl, wheel_speed_rr;
    Rte_Read_AbsController_WheelSpeed_FL_Port_Value(&wheel_speed_fl);
    Rte_Read_AbsController_WheelSpeed_FR_Port_Value(&wheel_speed_fr);
    Rte_Read_AbsController_WheelSpeed_RL_Port_Value(&wheel_speed_rl);
    Rte_Read_AbsController_WheelSpeed_RR_Port_Value(&wheel_speed_rr);

    /* Read vehicle speed reference */
    float vehicle_speed_ref;
    Rte_Read_AbsController_VehicleSpeedRef_Port_Value(&vehicle_speed_ref);

    /* Compute slip ratios */
    WheelSpeeds_t speeds = {
        .wheel_speed_fl = wheel_speed_fl,
        .wheel_speed_fr = wheel_speed_fr,
        .wheel_speed_rl = wheel_speed_rl,
        .wheel_speed_rr = wheel_speed_rr,
        .vehicle_speed_ref = vehicle_speed_ref
    };

    SlipInfo_t slip_info = compute_slip_ratios(&speeds);

    /* Validate sensors */
    SensorValidation_t sensor_status_fl = validate_wheel_speed_sensor(
        &wheel_speed_fl, &prev_wheel_speed_fl, vehicle_speed_ref);

    /* Compute target slip ratio based on road estimation */
    float road_type = estimate_road_surface(slip_info.slip_ratio_avg);
    float target_slip = find_optimal_slip_ratio(road_type);

    /* ABS state machine for each wheel */
    AbsState_t state_fl = abs_state_machine(
        slip_info.slip_ratio_fl, target_slip, slip_info.slip_rate_fl,
        g_abs_pressure_fl, g_pressure_error_fl);

    /* Compute pressure command */
    float pressure_cmd_fl = compute_abs_pressure(
        state_fl, slip_info.slip_ratio_fl, target_slip);

    /* Write valve commands to P-ports */
    ValveCommand_t valve_cmd_fl;
    valve_cmd_fl.inlet_valve_pwm = compute_inlet_pwm(pressure_cmd_fl);
    valve_cmd_fl.outlet_valve_pwm = compute_outlet_pwm(pressure_cmd_fl);
    Rte_Write_AbsController_ValveCommand_FL_Port_Value(&valve_cmd_fl);

    /* Update diagnostics */
    update_abs_diagnostics(sensor_status_fl, state_fl);
}
```

## Testing and Validation

### MIL Test Example

```matlab
% MATLAB/Simulink test: ABS response on split-mu surface
function results = test_abs_split_mu_surface()
    % Load model
    model = 'abs_controller_model';
    load_system(model);

    % Configure simulation
    set_param(model, 'StopTime', '5.0');  % 5 seconds
    set_param(model, 'FixedStep', '0.001'); % 1ms step

    % Test scenario: Split-mu braking (left=dry, right=icy)
    simIn = Simulink.SimulationInput(model);
    simIn = simIn.setVariable('initial_speed_kmh', 80.0);
    simIn = simIn.setVariable('road_mu_left', 0.9);   % Dry asphalt
    simIn = simIn.setVariable('road_mu_right', 0.2);  % Ice
    simIn = simIn.setVariable('pedal_force_n', 500);  % Hard braking

    simOut = sim(simIn);

    % Verify no wheel lockup
    wheel_speeds = [simOut.wheel_speed_fl.Data, simOut.wheel_speed_fr.Data];
    vehicle_speed = simOut.vehicle_speed.Data;

    % Check slip ratio stays within bounds (10-30%)
    slip_left = (vehicle_speed - wheel_speeds(:,1)) ./ (vehicle_speed + 0.1);
    slip_right = (vehicle_speed - wheel_speeds(:,2)) ./ (vehicle_speed + 0.1);

    max_slip_left = max(slip_left) * 100;
    max_slip_right = max(slip_right) * 100;

    assert(max_slip_left < 35, 'Left wheel slip exceeded 35%%');
    assert(max_slip_right < 35, 'Right wheel slip exceeded 35%%');

    % Verify stopping distance within acceptable range
    stop_distance = simOut.distance_traveled.Data(end);
    assert(stop_distance < 80, 'Stopping distance too long on split-mu');

    results.passed = true;
    results.max_slip_left = max_slip_left;
    results.max_slip_right = max_slip_right;
    results.stop_distance = stop_distance;
end
```

### HIL Fault Injection Test

```robot
*** Settings ***
Library    HilLibrary    bench_config=chassis_hil_01.yaml
Library    CanBusLibrary    interface=vector    channel=1
Suite Setup    Initialize HIL Bench
Suite Teardown    Shutdown HIL Bench

*** Test Cases ***
ABS Responds To Wheel Speed Sensor Fault
    [Documentation]    Verify ABS enters degraded mode on sensor fault
    [Tags]    safety    asil_d    fault_injection

    # Precondition: ABS active, normal operation
    Set HIL Vehicle Speed    60.0    # km/h
    Wait Until Keyword Succeeds    2s    100ms
    ...    Verify ABS Mode    NORMAL

    # Inject wheel speed sensor fault (stuck-at)
    Inject Sensor Fault    wheel_speed_fl    stuck_at    value=30.0

    # Verify degraded mode within 100ms
    Wait Until Keyword Succeeds    100ms    10ms
    ...    Verify ABS Mode    DEGRADED

    # Verify DTC stored
    Read DTC Via UDS    0xC00101    # Wheel speed sensor FL electrical
    DTC Should Be Active    0xC00101

ABS Maintains Stability On Split-Mu Surface
    [Documentation]    Verify yaw stability during split-mu braking
    [Tags]    performance    abs

    # Set up split-mu surface
    Set Road Friction Left    0.9
    Set Road Friction Right    0.2

    # Apply hard braking from 80 km/h
    Set Brake Pedal Force    500    # N
    Set Initial Speed    80.0    # km/h

    # Verify yaw rate remains bounded
    ${yaw_rate}=    Get Yaw Rate
    Should Be True    ${yaw_rate.abs()} < 15.0
    ...    Yaw rate ${yaw_rate} deg/s exceeds limit
```

## Approach

1. **Define ABS requirements**
   - Braking performance targets (stopping distance, stability)
   - ASIL decomposition (dual-channel, sensor redundancy)
   - Operating conditions (road surfaces, temperatures)

2. **Design control algorithms**
   - Slip ratio computation and target optimization
   - Pressure modulation state machine
   - PID controller tuning for each wheel

3. **Implement safety mechanisms**
   - Sensor plausibility checks
   - Dual-channel comparison logic
   - Fail-operational degraded modes

4. **Integrate with AUTOSAR**
   - Design SwComponent with appropriate ports
   - Configure runnables and timing (2ms cycle)
   - Generate RTE and integrate with BSW

5. **Validate through testing**
   - MIL: Algorithm validation on various road surfaces
   - SIL: Code verification with back-to-back testing
   - HIL: Fault injection and timing verification
   - Vehicle: Winter testing, split-mu validation

## Deliverables

- ABS control strategy specification
- Wheel slip control algorithm implementation
- AUTOSAR SWC integration code
- ISO 26262 safety case documentation
- Test results (MIL/SIL/HIL/Vehicle)
- Calibration parameter database

## Related Context
- @context/skills/chassis/brake-by-wire.md
- @context/skills/chassis/esc-control.md
- @context/skills/safety/iso-26262-overview.md
- @context/skills/autosar/classic-platform.md
- @context/skills/testing/hil-testing.md

## Tools Required
- MATLAB/Simulink (algorithm development)
- Vector CANoe/CANalyzer (network analysis)
- dSPACE HIL (hardware-in-loop testing)
- Static analyzer (Polyspace/Klocwork)
- ETAS INCA (calibration)
- AUTOSAR toolchain (DaVinci Configurator/Developer)