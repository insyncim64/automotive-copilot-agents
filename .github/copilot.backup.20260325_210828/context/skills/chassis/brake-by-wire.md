# Skill: Brake-by-Wire Control Systems

## When to Activate
- User asks about brake-by-wire system architecture or design
- User needs to implement electronic brake actuation without mechanical linkage
- User requests pedal feel simulation and emulation algorithms
- User is developing fail-operational braking systems for EV/AV platforms
- User needs ISO 26262 ASIL D safety mechanisms for brake systems
- User asks about redundancy management and fallback strategies
- User is implementing AUTOSAR Classic components for brake control

## Standards Compliance
- ISO 26262:2018 (Functional Safety) - ASIL D for primary braking
- ASPICE Level 3 - Model-based development process
- AUTOSAR 4.4 - Brake system domain architecture
- ISO 21434:2021 (Cybersecurity) - Brake command authentication
- UN ECE R13-H - Braking performance requirements
- UN ECE R155 - Cybersecurity management system
- ISO 13849 - Safety of machinery (for industrial brake systems)

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Pedal travel | 0-120 | mm |
| Pedal force | 0-2000 | N |
| Master cylinder pressure | 0-250 | bar |
| Wheel cylinder pressure | 0-220 | bar |
| Brake torque | 0-5000 | Nm per wheel |
| Deceleration | 0-12 | m/s² |
| System latency | <50 | ms |
| Redundancy level | Dual/Triple | - |
| Fallback mode | Hydraulic/Mechanical | - |

## Brake-by-Wire Architecture

```
+------------------------------------------------------------------+
|                    Brake-by-Wire System                           |
|                                                                   |
|  +------------------+     +------------------+                   |
|  | Pedal Simulator  |     | Pedal Unit ECU   |                   |
|  |                  |     |                  |                   |
|  | - Elastic body   |---->| - Pedal travel   |                   |
|  | - Damper         |     | - Force sensor   |                   |
|  | - Spring         |     | - Brake request  |                   |
|  +------------------+     +--------+---------+                   |
|                                    | Brake Request (CAN FD)      |
|                           +--------v---------+                   |
|                           | Chassis Domain   |                   |
|                           | Controller       |                   |
|                           |                  |                   |
|                           | - Brake logic    |                   |
|                           | - Distribution   |                   |
|                           | - Blending       |                   |
|                           +--+-----------+---+                   |
|                              |           |                       |
|         +--------------------+           +--------------------+  |
|         |                                     |                 |
|  +------v----------+                  +-------v------+          |
|  | Front Axle      |                  | Rear Axle    |          |
|  | Brake Module    |                  | Brake Module |          |
|  |                 |                  |              |          |
|  | - Pressure gen  |                  | - Pressure   |          |
|  | - Solenoid ctrl |                  | - Solenoid   |          |
|  | - Motor ctrl    |                  | - Motor      |          |
|  +--------+--------+                  +-------+------+          |
|           |                                    |                |
|  +--------v--------+                  +--------v------+         |
|  | Front Brake     |                  | Rear Brake    |         |
|  | Calipers        |                  | Calipers      |         |
|  | (Electromech.)  |                  | (Electromech.)|         |
|  +-----------------+                  +---------------+         |
|                                                                   |
|  +------------------+     +------------------+                   |
|  | Redundancy Unit  |     | Hydraulic        |                   |
|  |                  |     | Fallback         |                   |
|  | - Dual supply    |     |                  |                   |
|  | - Cross-monitor  |     | - Accumulator    |                   |
|  | - Vote logic     |     | - Isolation      |                   |
|  +------------------+     +------------------+                   |
+------------------------------------------------------------------+
```

## Pedal Feel Simulation

### Pedal Unit Sensing

```c
/* Pedal unit sensor readings */
typedef struct {
    float travel_mm;           /* 0-120 mm pedal travel */
    float force_n;             /* 0-2000 N pedal force */
    float rate_mm_s;           /* Pedal application rate */
    uint8_t sensor_status;     /* Sensor health flags */
    uint32_t timestamp_ms;     /* Sample timestamp */
} PedalInput_t;

/* Pedal brake request calculation */
typedef struct {
    float brake_request_pct;   /* 0-100% brake request */
    float brake_request_bar;   /* Equivalent hydraulic pressure */
    uint8_t pedal_status;      /* PEDAL_OK, PEDAL_FAULT, etc. */
    bool emergency_brake;      /* Panic brake detected */
} BrakeRequest_t;

/* Brake request computation with pedal feel mapping */
BrakeRequest_t compute_brake_request(const PedalInput_t* pedal) {
    BrakeRequest_t request = {0};

    /* Sensor validation */
    if (pedal->sensor_status != SENSOR_OK) {
        request.pedal_status = PEDAL_FAULT;
        return request;
    }

    /* Check for emergency brake (high force, high rate) */
    if (pedal->force_n > PANIC_FORCE_THRESHOLD_N &&
        pedal->rate_mm_s > PANIC_RATE_THRESHOLD_MM_S) {
        request.emergency_brake = true;
    }

    /* Map pedal travel to brake request (non-linear curve) */
    /* Typical: 20% deadband, then progressive increase */
    if (pedal->travel_mm < PEDAL_DEADBAND_MM) {
        request.brake_request_pct = 0.0f;
    } else {
        float normalized = (pedal->travel_mm - PEDAL_DEADBAND_MM) /
                           (PEDAL_MAX_TRAVEL_MM - PEDAL_DEADBAND_MM);

        /* Apply progressive curve for better pedal feel */
        request.brake_request_pct = 100.0f * progressive_curve(normalized);
    }

    /* Map to equivalent hydraulic pressure (for brake blending) */
    request.brake_request_bar = request.brake_request_pct *
                                 MAX_MASTER_CYLINDER_PRESSURE_BAR / 100.0f;

    request.pedal_status = PEDAL_OK;
    return request;
}

/* Progressive pedal feel curve */
float progressive_curve(float normalized_input) {
    /* Three-stage curve: initial soft, mid linear, end firm */
    if (normalized_input < 0.3f) {
        /* Soft initial stage for comfort */
        return normalized_input * 0.7f;
    } else if (normalized_input < 0.7f) {
        /* Linear mid stage */
        return 0.21f + (normalized_input - 0.3f) * 1.0f;
    } else {
        /* Firm end stage for maximum braking */
        return 0.61f + (normalized_input - 0.7f) * 1.3f;
    }
}
```

### Pedal Feel Emulation

```c
/* Pedal simulator actuator control */
typedef struct {
    float target_force_n;      /* Target pedal reaction force */
    float actual_force_n;      /* Measured force from load cell */
    float damper_current_a;    /* Damper actuator current */
    float spring_stiffness;    /* Emulated spring constant */
} PedalSimulator_t;

static PedalSimulator_t g_pedal_sim = {
    .spring_stiffness = 15.0f  /* N/mm - configurable */
};

/* Compute pedal feel reaction force */
float compute_pedal_reaction_force(float travel_mm, float rate_mm_s) {
    float force = 0.0f;

    /* Spring force component */
    force += g_pedal_sim.spring_stiffness * travel_mm;

    /* Damper force component (velocity-dependent) */
    if (rate_mm_s > 0.0f) {
        /* Compression damping */
        force += 0.5f * rate_mm_s;
    } else {
        /* Rebound damping (typically higher) */
        force += 0.8f * rate_mm_s;
    }

    /* Progressive end-stop emulation */
    if (travel_mm > PEDAL_SOFT_STOP_MM) {
        float penetration = travel_mm - PEDAL_SOFT_STOP_MM;
        force += 50.0f * penetration * penetration;  /* Quadratic stiffening */
    }

    /* Limit to maximum feel force */
    return fminf(force, MAX_PEDAL_FORCE_N);
}

/* Pedal simulator closed-loop control */
void control_pedal_simulator(const PedalSimulator_t* cmd) {
    /* Force control loop (1 kHz) */
    float force_error = cmd->target_force_n - cmd->actual_force_n;

    /* Simple P-controller for damper current */
    float damper_cmd = force_error * PEDAL_FORCE_GAIN;

    /* Current limit */
    damper_cmd = fminf(fmaxf(damper_cmd, 0.0f), MAX_DAMPER_CURRENT_A);

    /* Apply PWM to damper actuator */
    set_damper_pwm(damper_cmd / MAX_DAMPER_CURRENT_A * 100.0f);
}
```

## Electronic Brake Actuation

### Electro-Hydraulic Brake (EHB)

```c
/* EHB pressure generation unit */
typedef struct {
    float target_pressure_bar;
    float actual_pressure_bar;
    float motor_speed_rpm;
    float pump_temperature_c;
    uint8_t valve_positions[4];  /* IN/OUT per wheel */
} EhbUnit_t;

/* Pressure control for electro-hydraulic brake */
typedef struct {
    float kp;              /* Proportional gain */
    float ki;              /* Integral gain */
    float kd;              /* Derivative gain */
    float integral_max;    /* Anti-windup limit */
    float prev_error;      /* Previous error for D term */
    float integral_sum;    /* Accumulated integral */
} PressurePid_t;

static PressurePid_t g_ehb_pid[EHB_AXLE_COUNT] = {
    [0] = { .kp = 2.5f, .ki = 0.8f, .kd = 0.1f, .integral_max = 50.0f },
    [1] = { .kp = 2.5f, .ki = 0.8f, .kd = 0.1f, .integral_max = 50.0f }
};

/* EHB pressure control loop (5 ms cycle) */
void ehb_pressure_control(EhbUnit_t* ehb, uint8_t axle_id,
                           float target_pressure, float dt) {
    PressurePid_t* pid = &g_ehb_pid[axle_id];

    /* Compute error */
    float error = target_pressure - ehb->actual_pressure_bar;

    /* Proportional term */
    float p_term = pid->kp * error;

    /* Integral term with anti-windup */
    pid->integral_sum += error * dt;
    pid->integral_sum = fminf(fmaxf(pid->integral_sum, -pid->integral_max),
                               pid->integral_max);
    float i_term = pid->ki * pid->integral_sum;

    /* Derivative term */
    float d_term = pid->kd * (error - pid->prev_error) / dt;
    pid->prev_error = error;

    /* Compute motor command */
    float motor_cmd = p_term + i_term + d_term;

    /* Motor speed command (RPM proportional to pressure rate) */
    float target_rpm = motor_cmd * EHB_PRESSURE_TO_RPM_GAIN;
    ehb->motor_speed_rpm = fminf(fmaxf(target_rpm, 0.0f), MAX_PUMP_RPM);

    /* Valve position control for pressure hold/release */
    if (error > PRESSURE_HOLD_THRESHOLD_BAR) {
        /* Need to increase pressure - open inlet, close outlet */
        set_inlet_valve(axle_id, VALVE_OPEN);
        set_outlet_valve(axle_id, VALVE_CLOSE);
    } else if (error < -PRESSURE_RELEASE_THRESHOLD_BAR) {
        /* Need to decrease pressure - close inlet, open outlet */
        set_inlet_valve(axle_id, VALVE_CLOSE);
        set_outlet_valve(axle_id, VALVE_OPEN);
    } else {
        /* Hold pressure - close both valves */
        set_inlet_valve(axle_id, VALVE_CLOSE);
        set_outlet_valve(axle_id, VALVE_CLOSE);
    }
}
```

### Electromechanical Brake (EMB)

```c
/* EMB caliper actuator model */
typedef struct {
    float target_clamp_force_n;
    float actual_clamp_force_n;
    float motor_position_rad;
    float motor_speed_rad_s;
    float motor_current_a;
    float caliper_temperature_c;
    float pad_wear_mm;
} EmbCaliper_t;

/* EMB clamp force control */
void emb_clamp_force_control(EmbCaliper_t* caliper,
                              float target_force, float dt) {
    /* Cascade control: outer force loop, inner position loop */

    /* Force loop (1 ms) */
    float force_error = target_force - caliper->actual_clamp_force_n;

    /* Convert force error to position target via stiffness model */
    float stiffness_per_mm = CALIPER_STIFFNESS_N_MM;
    float position_offset = force_error / stiffness_per_mm;
    float target_position = caliper->motor_position_rad + position_offset;

    /* Position loop (5 ms, inner loop) */
    float position_error = target_position - caliper->motor_position_rad;

    /* Compute motor torque command */
    float torque_cmd = position_error * EMB_POSITION_GAIN;

    /* Current limit based on temperature */
    float max_current = get_current_limit_for_temp(caliper->caliper_temperature_c);
    float current_cmd = fminf(torque_cmd / MOTOR_TORQUE_CONSTANT, max_current);

    /* Apply motor current */
    caliper->motor_current_a = current_cmd;

    /* Clamp force estimation (from motor current or direct sensor) */
    caliper->actual_clamp_force_n = estimate_clamp_force(caliper);
}

/* Clamp force estimation from motor current */
float estimate_clamp_force(const EmbCaliper_t* caliper) {
    /* Force from motor torque through gear reduction */
    float motor_torque = caliper->motor_current_a * MOTOR_TORQUE_CONSTANT;
    float gearbox_torque = motor_torque * GEAR_REDUCTION_RATIO;

    /* Account for efficiency losses */
    float effective_torque = gearbox_torque * GEARBOX_EFFICIENCY;

    /* Convert to linear clamp force via ball screw */
    float screw_lead_m = BALL_SCREW_LEAD_MM / 1000.0f;
    float clamp_force = (2.0f * M_PI * effective_torque) / screw_lead_m;

    /* Account for pad wear (reduces effective force) */
    float wear_factor = 1.0f - (caliper->pad_wear_mm / MAX_PAD_WEAR_MM);
    clamp_force *= wear_factor;

    return clamp_force;
}
```

## Brake Blending (Regenerative + Friction)

### Blended Braking Strategy

```c
/* Brake blending for EV/HEV vehicles */
typedef struct {
    float total_brake_request_bar;
    float vehicle_speed_kmh;
    float battery_soc_percent;
    float motor_speed_rpm;
    float motor_temperature_c;
    float regen_available;  /* Boolean flag */
} BlendedBrakeInput_t;

typedef struct {
    float regen_brake_bar;      /* Regenerative braking component */
    float friction_brake_bar;   /* Friction braking component */
    float regen_limit_bar;      /* Maximum available regen */
    uint8_t blend_mode;         /* NORMAL, REGEN_LIMITED, FRICTION_ONLY */
} BlendedBrakeOutput_t;

/* Brake blending algorithm */
BlendedBrakeOutput_t compute_brake_blend(const BlendedBrakeInput_t* input) {
    BlendedBrakeOutput_t output = {0};

    /* Calculate maximum available regenerative braking */
    output.regen_limit_bar = compute_regen_limit(
        input->battery_soc_percent,
        input->motor_speed_rpm,
        input->motor_temperature_c,
        input->vehicle_speed_kmh
    );

    /* Determine blend mode */
    if (output.regen_limit_bar <= 0.0f) {
        output.blend_mode = FRICTION_ONLY;
    } else if (output.regen_limit_bar < input->total_brake_request_bar) {
        output.blend_mode = REGEN_LIMITED;
    } else {
        output.blend_mode = NORMAL;
    }

    /* Compute blend based on mode */
    switch (output.blend_mode) {
        case NORMAL:
            /* Regen can satisfy full request */
            output.regen_brake_bar = input->total_brake_request_bar;
            output.friction_brake_bar = 0.0f;
            break;

        case REGEN_LIMITED:
            /* Use max regen, friction fills remainder */
            output.regen_brake_bar = output.regen_limit_bar;
            output.friction_brake_bar =
                input->total_brake_request_bar - output.regen_limit_bar;
            break;

        case FRICTION_ONLY:
            /* No regen available */
            output.regen_brake_bar = 0.0f;
            output.friction_brake_bar = input->total_brake_request_bar;
            break;
    }

    /* Smooth transition to prevent jerk */
    apply_blend_filter(&output);

    return output;
}

/* Regen limit calculation */
float compute_regen_limit(float soc, float motor_rpm,
                           float motor_temp, float vehicle_speed) {
    float limit_bar = MAX_REGEN_PRESSURE_BAR;

    /* Battery SOC limit (reduce regen when near full) */
    if (soc > REGEN_SOC_THRESHOLD_HIGH) {
        float reduction = (soc - REGEN_SOC_THRESHOLD_HIGH) /
                          (100.0f - REGEN_SOC_THRESHOLD_HIGH);
        limit_bar *= (1.0f - reduction);
    }

    /* Motor speed limit (regen ineffective at very low speed) */
    if (motor_rpm < REGEN_MIN_RPM) {
        limit_bar *= (motor_rpm / REGEN_MIN_RPM);
    }

    /* Motor temperature limit (reduce regen when hot) */
    if (motor_temp > REGEN_TEMP_THRESHOLD) {
        float reduction = (motor_temp - REGEN_TEMP_THRESHOLD) /
                          (MOTOR_MAX_TEMP - REGEN_TEMP_THRESHOLD);
        limit_bar *= (1.0f - reduction);
    }

    /* Vehicle speed limit (ABS intervention at very low speed) */
    if (vehicle_speed < REGEN_MIN_SPEED_KMH) {
        limit_bar = 0.0f;  /* Switch to friction only below threshold */
    }

    return limit_bar;
}
```

## ISO 26262 Safety Mechanisms

### Sensor Redundancy and Plausibility

```c
/* Dual redundant pedal sensor comparison */
typedef struct {
    float travel_sensor_1_mm;
    float travel_sensor_2_mm;
    float force_sensor_1_n;
    float force_sensor_2_n;
    uint8_t sensor_status[4];
} RedundantPedalSensors_t;

typedef struct {
    bool valid;
    float travel_mm;
    float force_n;
    uint8_t fault_flags;
} ValidatedPedalInput_t;

/* ASIL D sensor validation */
ValidatedPedalInput_t validate_pedal_sensors(
    const RedundantPedalSensors_t* sensors) {

    ValidatedPedalInput_t result = {0};
    result.fault_flags = 0;

    /* Check individual sensor health */
    bool sensor1_ok = (sensors->sensor_status[0] == SENSOR_OK) &&
                      (sensors->sensor_status[1] == SENSOR_OK);
    bool sensor2_ok = (sensors->sensor_status[2] == SENSOR_OK) &&
                      (sensors->sensor_status[3] == SENSOR_OK);

    /* Plausibility check between redundant sensors */
    float travel_diff = fabsf(sensors->travel_sensor_1_mm -
                               sensors->travel_sensor_2_mm);
    float force_diff = fabsf(sensors->force_sensor_1_n -
                              sensors->force_sensor_2_n);

    bool travel_plausible = (travel_diff < PEDAL_SENSOR_MAX_DIFF_MM);
    bool force_plausible = (force_diff < FORCE_SENSOR_MAX_DIFF_N);

    /* Cross-check travel vs force (via pedal curve) */
    float expected_force = compute_pedal_reaction_force(
        sensors->travel_sensor_1_mm, 0.0f);
    float force_curve_diff = fabsf(sensors->force_sensor_1_n - expected_force);
    bool curve_plausible = (force_curve_diff < PEDAL_CURVE_MAX_DIFF_N);

    /* Determine output validity */
    if (sensor1_ok && sensor2_ok && travel_plausible &&
        force_plausible && curve_plausible) {
        result.valid = true;
        /* Use average of redundant sensors */
        result.travel_mm = (sensors->travel_sensor_1_mm +
                            sensors->travel_sensor_2_mm) / 2.0f;
        result.force_n = (sensors->force_sensor_1_n +
                          sensors->force_sensor_2_n) / 2.0f;
    } else {
        result.valid = false;

        /* Log specific faults */
        if (!sensor1_ok) result.fault_flags |= FAULT_SENSOR_1_HEALTH;
        if (!sensor2_ok) result.fault_flags |= FAULT_SENSOR_2_HEALTH;
        if (!travel_plausible) result.fault_flags |= FAULT_TRAVEL_MISMATCH;
        if (!force_plausible) result.fault_flags |= FAULT_FORCE_MISMATCH;
        if (!curve_plausible) result.fault_flags |= FAULT_CURVE_PLAUSIBILITY;

        /* Use degraded mode (single sensor if available) */
        if (sensor1_ok) {
            result.travel_mm = sensors->travel_sensor_1_mm;
            result.force_n = sensors->force_sensor_1_n;
        } else if (sensor2_ok) {
            result.travel_mm = sensors->travel_sensor_2_mm;
            result.force_n = sensors->force_sensor_2_n;
        }
    }

    return result;
}
```

### Dual-Channel Architecture

```c
/* Dual-channel brake computation for ASIL D */
typedef struct {
    /* Primary channel (computes brake commands) */
    float primary_brake_pressure_bar;
    uint8_t primary_status;
    uint32_t primary_sequence;

    /* Monitor channel (independent verification) */
    float monitor_brake_pressure_bar;
    uint8_t monitor_status;
    uint32_t monitor_sequence;

    /* Comparison result */
    bool agreement;
    float discrepancy_bar;
} DualChannelResult_t;

/* ASIL D dual-channel brake computation */
DualChannelResult_t compute_brake_dual_channel(
    const ValidatedPedalInput_t* pedal,
    const VehicleState_t* vehicle) {

    DualChannelResult_t result = {0};

    /* PRIMARY CHANNEL - Main brake algorithm */
    result.primary_brake_pressure_bar = compute_brake_pressure_primary(
        pedal->travel_mm, pedal->force_n, vehicle);
    result.primary_status = CHANNEL_OK;
    result.primary_sequence++;

    /* MONITOR CHANNEL - Independent computation */
    /* Different algorithm or simplified model */
    result.monitor_brake_pressure_bar = compute_brake_pressure_monitor(
        pedal->travel_mm, vehicle);
    result.monitor_status = CHANNEL_OK;
    result.monitor_sequence++;

    /* Cross-channel comparison */
    result.discrepancy_bar = fabsf(
        result.primary_brake_pressure_bar -
        result.monitor_brake_pressure_bar);

    /* Agreement threshold depends on pressure level */
    float agreement_threshold = fmaxf(
        result.primary_brake_pressure_bar * DISCREPANCY_PERCENT,
        DISCREPANCY_MINIMUM_BAR);

    result.agreement = (result.discrepancy_bar < agreement_threshold);

    if (!result.agreement) {
        /* Log disagreement for diagnostics */
        log_dual_channel_disagreement(result.discrepancy_bar);

        /* Enter safe state if discrepancy is large */
        if (result.discrepancy_bar > CRITICAL_DISCREPANCY_BAR) {
            result.primary_status = CHANNEL_DISAGREEMENT;
        }
    }

    return result;
}

/* Safe output selection from dual channels */
float select_safe_brake_output(const DualChannelResult_t* result) {
    if (result->agreement &&
        result->primary_status == CHANNEL_OK &&
        result->monitor_status == CHANNEL_OK) {
        /* Channels agree - use primary output */
        return result->primary_brake_pressure_bar;
    } else if (result->primary_status == CHANNEL_OK) {
        /* Monitor failed or disagreement - use primary with reduced authority */
        return result->primary_brake_pressure_bar * DEGRADED_AUTHORITY_FACTOR;
    } else if (result->monitor_status == CHANNEL_OK) {
        /* Primary failed - use monitor with reduced authority */
        return result->monitor_brake_pressure_bar * DEGRADED_AUTHORITY_FACTOR;
    } else {
        /* Both failed - zero brake request (safe state) */
        return 0.0f;
    }
}
```

### Fail-Operational Design

```c
/* Brake system operational modes */
typedef enum {
    BRAKE_MODE_NORMAL,         /* Full brake-by-wire with regen blending */
    BRAKE_MODE_DEGRADED,       /* Reduced authority, friction only */
    BRAKE_MODE_FALLBACK,       /* Hydraulic fallback activated */
    BRAKE_MODE_SAFE_STOP,      /* Emergency deceleration to stop */
    BRAKE_MODE_PARK            /* Parking brake applied */
} BrakeSystemMode_t;

/* Mode determination based on system health */
BrakeSystemMode_t determine_brake_mode(
    const DualChannelResult_t* dual_channel,
    const SystemHealth_t* health) {

    /* Check for critical faults */
    if (health->dual_power_supply_fault ||
        health->communication_bus_off ||
        health->critical_sensor_failure) {
        /* Multiple critical faults - activate hydraulic fallback */
        return BRAKE_MODE_FALLBACK;
    }

    if (!dual_channel->agreement ||
        dual_channel->discrepancy_bar > CRITICAL_DISCREPANCY_BAR) {
        /* Channel disagreement - degraded mode */
        return BRAKE_MODE_DEGRADED;
    }

    if (health->single_sensor_fault ||
        health->single_actuator_fault) {
        /* Single fault - degraded but operational */
        return BRAKE_MODE_DEGRADED;
    }

    /* All systems nominal */
    return BRAKE_MODE_NORMAL;
}

/* Degraded mode control strategy */
void apply_degraded_mode_control(BrakeCommand_t* cmd) {
    /* Reduce maximum brake authority */
    cmd->max_pressure_bar = DEGRADED_MAX_PRESSURE_BAR;

    /* Disable regenerative braking (use friction only) */
    cmd->regen_enabled = false;

    /* Increase following distance warning threshold */
    cmd->warning_distance_multiplier = 1.5f;

    /* Notify driver of degraded mode */
    set_warning_message(WARNING_BRAKE_DEGRADED);
}

/* Hydraulic fallback activation */
void activate_hydraulic_fallback(void) {
    /* Open isolation valves to connect pedal to wheel cylinders */
    set_isolation_valves(FALLBACK_ISOLATION_OPEN);

    /* Disable pressure generation units */
    disable_ehb_units();

    /* Alert driver */
    set_warning_message(WARNING_BRAKE_FALLBACK_ACTIVE);

    /* Log fallback activation event */
    log_fallback_activation();
}
```

## AUTOSAR Implementation

### Software Component Design

```xml
<!-- BrakeByWire SwComponentType (ARXML) -->
<APPLICATION-SW-COMPONENT-TYPE>
  <SHORT-NAME>BrakeByWireController</SHORT-NAME>
  <DESCRIPTION>
    Brake-by-wire control with pedal emulation, brake blending,
    and ISO 26262 ASIL D safety mechanisms.
  </DESCRIPTION>

  <!-- Port Interfaces -->
  <PORTS>
    <!-- Brake Pedal Input -->
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>PedalInputPort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/PedalSensor_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <!-- Vehicle State Input -->
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>VehicleStatePort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/VehicleState_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <!-- Brake Command Output -->
    <P-PORT-PROTOTYPE>
      <SHORT-NAME>BrakeCommandPort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/BrakeCommand_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>

    <!-- Hydraulic Unit Command -->
    <P-PORT-PROTOTYPE>
      <SHORT-NAME>HydraulicUnitCommandPort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/HydraulicUnit_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>
  </PORTS>

  <!-- Internal Behavior -->
  <INTERNAL-BEHAVIOR>
    <RUNNABLE-ENTITIES>
      <!-- Pedal Processing - 5ms -->
      <RUNNABLE-ENTITY>
        <SHORT-NAME>PedalProcessing_5ms</SHORT-NAME>
        <BEGIN-PERIOD>0.005</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>

      <!-- Brake Control - 5ms -->
      <RUNNABLE-ENTITY>
        <SHORT-NAME>BrakeControl_5ms</SHORT-NAME>
        <BEGIN-PERIOD>0.005</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>

      <!-- Safety Monitor - 10ms -->
      <RUNNABLE-ENTITY>
        <SHORT-NAME>SafetyMonitor_10ms</SHORT-NAME>
        <BEGIN-PERIOD>0.010</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>
    </RUNNABLE-ENTITIES>
  </INTERNAL-BEHAVIOR>
</APPLICATION-SW-COMPONENT-TYPE>
```

### Runnable Implementation

```c
/* Brake-by-Wire Runnable - 5ms cycle */
#include "Rte_BrakeByWireController.h"

void BrakeByWireController_BrakeControl_5ms_Runnable(void) {
    /* Read inputs from R-ports */
    PedalSensor_t pedal_sensor;
    Rte_Read_BrakeByWireController_PedalInputPort_Value(&pedal_sensor);

    VehicleState_t vehicle_state;
    Rte_Read_BrakeByWireController_VehicleStatePort_Value(&vehicle_state);

    /* Validate pedal sensors (ASIL D) */
    ValidatedPedalInput_t validated_pedal =
        validate_pedal_sensors(&pedal_sensor);

    if (!validated_pedal.valid) {
        /* Pedal fault - enter safe state */
        report_pedal_fault(validated_pedal.fault_flags);
        BrakeCommand_t safe_cmd = {
            .pressure_bar = 0.0f,
            .mode = BRAKE_MODE_FALLBACK
        };
        Rte_Write_BrakeByWireController_BrakeCommandPort_Value(&safe_cmd);
        return;
    }

    /* Compute brake request with dual-channel architecture */
    DualChannelResult_t dual_result = compute_brake_dual_channel(
        &validated_pedal, &vehicle_state);

    /* Select safe output */
    float safe_pressure = select_safe_brake_output(&dual_result);

    /* Brake blending (regenerative + friction) */
    BlendedBrakeInput_t blend_input = {
        .total_brake_request_bar = safe_pressure,
        .vehicle_speed_kmh = vehicle_state.speed_kmh,
        .battery_soc_percent = vehicle_state.battery_soc,
        .motor_speed_rpm = vehicle_state.motor_speed,
        .regen_available = vehicle_state.regen_available
    };

    BlendedBrakeOutput_t blend_output =
        compute_brake_blend(&blend_input);

    /* Build brake command */
    BrakeCommand_t brake_cmd = {
        .pressure_bar = blend_output.friction_brake_bar,
        .regen_pressure_bar = blend_output.regen_brake_bar,
        .mode = determine_brake_mode(&dual_result, &vehicle_state.health),
        .timestamp_ms = get_system_time_ms()
    };

    /* Write outputs to P-ports */
    Rte_Write_BrakeByWireController_BrakeCommandPort_Value(&brake_cmd);

    /* Write hydraulic unit command */
    HydraulicUnitCommand_t hu_cmd = {
        .target_pressure_bar = brake_cmd.pressure_bar,
        .valve_commands = compute_valve_positions(&brake_cmd)
    };
    Rte_Write_BrakeByWireController_HydraulicUnitCommandPort_Value(&hu_cmd);
}
```

## Testing

### MIL Test Example

```matlab
% MATLAB test for brake-by-wire pedal blending
function results = test_brake_blend_regenerative_limit()
    % Load brake-by-wire model
    model = 'brake_by_wire_controller';
    load_system(model);

    % Configure simulation
    simIn = Simulink.SimulationInput(model);
    simIn = simIn.setVariable('initial_soc', 85.0);  % High SOC
    simIn = simIn.setVariable('vehicle_speed', 80.0); % km/h
    simIn = simIn.setVariable('pedal_step_time', 1.0);
    simIn = simIn.setVariable('pedal_step_amplitude', 80.0); % % brake

    % Run simulation
    simOut = sim(simIn);

    % Extract signals
    regen_brake = simOut.regen_brake_pressure.Data;
    friction_brake = simOut.friction_brake_pressure.Data;
    total_brake = simOut.total_brake_pressure.Data;
    soc = simOut.battery_soc.Data;

    % Verify regen limited at high SOC
    max_regen = max(regen_brake);
    assert(max_regen < REGEN_LIMIT_HIGH_SOC_BAR, ...
        'Regen should be limited at high SOC');

    % Verify total brake request met
    assert(all(abs(total_brake - (regen_brake + friction_brake)) < 1.0), ...
        'Total brake should equal regen + friction');

    % Verify smooth blending (no pressure step)
    brake_rate = diff(total_brake) / simOut.Time(2);
    assert(max(abs(brake_rate)) < MAX_BRAKE_RATE_BAR_S, ...
        'Brake blending should be smooth');

    results.regen_limited = max_regen;
    results.max_blending_error = max(abs(total_brake - (regen_brake + friction_brake)));
end
```

### HIL Fault Injection Test

```robot
*** Settings ***
Library    HilLibrary    bench_config=brake_hil.yaml
Library    CanBusLibrary    interface=vector    channel=1
Suite Setup    Initialize Brake HIL Bench
Suite Teardown    Shutdown Brake HIL Bench

*** Test Cases ***
Brake-by-Wire Dual Channel Disagreement Detection
    [Documentation]    Verify dual-channel comparison detects faults
    [Tags]    safety    asil_d    regression

    # Precondition: Normal brake operation
    Set Plant Model State    normal_operation
    Verify CAN Signal    BrakeStatus    System_Mode    NORMAL

    # Inject fault: Primary channel sensor offset
    Inject Sensor Fault    primary_pedal_travel    offset    15.0

    # Wait for fault detection
    Sleep    20ms

    # Verify system enters degraded mode
    Verify CAN Signal    BrakeStatus    System_Mode    DEGRADED

    # Verify driver warning activated
    Verify CAN Signal    DashWarning    Brake_Degraded_Warning    TRUE

    # Verify reduced brake authority
    Send CAN Message    0x100    ${PEDAL_50PCT}
    Sleep    50ms
    ${pressure}=    Read CAN Signal    BrakeCommand    Pressure
    Should Be True    ${pressure} < ${DEGRADED_MAX_PRESSURE}
    ...    Brake authority should be reduced in degraded mode

Brake Hydraulic Fallback Activation
    [Documentation]    Verify fallback mode activates on critical fault
    [Tags]    safety    asil_d

    # Precondition: Normal operation
    Set Plant Model State    normal_operation

    # Inject critical fault: Dual power supply failure
    Inject Fault    dual_power_supply    failure

    # Verify fallback activation
    Wait Until Keyword Succeeds    50ms    5ms
    ...    Verify CAN Signal    BrakeStatus    System_Mode    FALLBACK

    # Verify isolation valves open (pedal connected to wheels)
    Verify GPIO    Isolation_Valve    OPEN

    # Verify driver warning
    Verify CAN Signal    DashWarning    Brake_Fallback_Warning    TRUE
```

## Approach

1. **Define brake-by-wire architecture**
   - Select EHB or EMB actuation technology
   - Design pedal feel simulator characteristics
   - Define redundancy strategy (dual/triple)

2. **Implement pedal feel emulation**
   - Calibrate spring/damper characteristics
   - Implement progressive pedal curve
   - Tune force closed-loop control

3. **Develop brake actuation control**
   - Pressure control for EHB systems
   - Clamp force control for EMB systems
   - Implement brake blending algorithm

4. **Implement safety mechanisms**
   - Dual-channel architecture with comparison
   - Sensor plausibility and redundancy
   - Fail-operational fallback strategies

5. **Integrate with AUTOSAR**
   - Design SwComponent with appropriate ports
   - Configure runnables and timing (5ms cycles)
   - Generate RTE and integrate

6. **Validate and calibrate**
   - MIL/SIL testing of control algorithms
   - HIL testing with production ECU
   - Vehicle calibration for pedal feel

## Deliverables

- Brake-by-wire system architecture specification
- Pedal feel calibration data and characteristics
- Brake control algorithm implementation (C/Model)
- Safety manual with dual-channel analysis
- AUTOSAR SWC integration code
- Test results (MIL/SIL/HIL/Vehicle)
- ISO 26262 safety case documentation

## Related Context
- @context/skills/chassis/abs-control.md
- @context/skills/chassis/esc-control.md
- @context/skills/safety/iso-26262-overview.md
- @context/skills/autosar/classic-platform.md
- @context/skills/testing/hil-testing.md

## Tools Required
- MATLAB/Simulink (algorithm development)
- dSPACE/ETAS HIL (hardware-in-loop testing)
- Vector CANoe/CANalyzer (network analysis)
- ETAS INCA (calibration)
- AUTOSAR configuration tools (DaVinci/Configurator)
