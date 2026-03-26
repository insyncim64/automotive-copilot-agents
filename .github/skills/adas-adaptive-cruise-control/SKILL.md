---
name: adas-adaptive-cruise-control
description: "Use when: Skill: Adaptive Cruise Control (ACC) topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: Adaptive Cruise Control (ACC)

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/adas/adaptive-cruise-control.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate
- User asks about ACC algorithm design or implementation
- User needs longitudinal control guidance (PID, MPC)
- User requests ACC testing, validation, or calibration support
- User is designing stop-and-go ACC or full-speed range ACC systems

## Standards Compliance
- ISO 26262 ASIL C/D (longitudinal control)
- ASPICE Level 3
- AUTOSAR 4.4 Classic Platform
- ISO 21434 (Cybersecurity for actuator control)
- UN R157 (ALKS - Automated Lane Keeping Systems)

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Following distance (time gap) | 1.0 - 3.0 | seconds |
| Speed setpoint range | 0 - 180 | km/h |
| Max acceleration | 2.0 - 3.5 | m/s² |
| Max deceleration (comfort) | 2.5 - 3.5 | m/s² |
| Max deceleration (emergency) | 5.0 - 8.0 | m/s² |
| Jerk limit (comfort) | 2.0 - 5.0 | m/s³ |
| Standstill delay | 1.0 - 3.0 | seconds |
| Cut-in detection time | < 200 | ms |

## ACC System Architecture

```
+-------------------+     +------------------+     +------------------+
|   Perception      |     |   ACC Manager    |     |   Actuator       |
|                   |     |                  |     |                  |
| - Radar target    |---->| - State machine  |---->| - Engine torque  |
| - Camera vehicle  |     | - Distance ctrl  |     | - Brake pressure |
| - Cut-in detection|     | - Speed control  |     | - Retarder       |
+-------------------+     +------------------+     +------------------+
                                  |
                                  v
                          +------------------+
                          |   HMI Interface  |
                          |                  |
                          | - Set speed      |
                          | - Set distance   |
                          | - Driver override|
                          +------------------+
```

## Control Strategies

### PID Control (Production Common)
```c
typedef struct {
    float kp;        /* Proportional gain */
    float ki;        /* Integral gain */
    float kd;        /* Derivative gain */
    float integral;  /* Integral term accumulator */
    float prev_error;/* Previous error for derivative */
    float output_min;/* Minimum output (-max brake) */
    float output_max;/* Maximum output (+max accel) */
} PidController_t;

float pid_update(PidController_t* pid, float error, float dt) {
    /* Proportional term */
    float p_term = pid->kp * error;

    /* Integral term (with anti-windup) */
    pid->integral += error * dt;
    pid->integral = fmaxf(-1.0f, fminf(1.0f, pid->integral));
    float i_term = pid->ki * pid->integral;

    /* Derivative term */
    float d_term = pid->kd * (error - pid->prev_error) / dt;
    pid->prev_error = error;

    /* Sum with saturation */
    float output = p_term + i_term + d_term;
    return fmaxf(pid->output_min, fminf(pid->output_max, output));
}
```

### Model Predictive Control (Advanced)
```
MPC Formulation:

Minimize: sum(||x - x_ref||_Q^2 + ||u||_R^2 + ||Δu||_S^2)
Subject to:
  - x_k+1 = A*x_k + B*u_k (vehicle dynamics)
  - u_min <= u <= u_max (actuator limits)
  - Δu_min <= Δu <= Δu_max (rate limits)
  - d >= d_safe (distance constraint)

Prediction horizon: 10-20 steps (1-2 seconds)
Control horizon: 3-5 steps
Solve time: < 50 ms (embedded QP solver)
```

### Two-Level Control (Distance + Speed)
```
Distance Control Mode (leading vehicle detected):
  - Maintain time gap: d_ref = v_ego * time_gap + d_standstill
  - Smooth following behavior
  - Cut-in/cut-out response

Speed Control Mode (no leading vehicle):
  - Maintain driver set speed
  - Respect road speed limits (from camera/navigation)
  - Curve speed adaptation (optional)
```

## State Machine

```
┌─────────────────────────────────────────────────────────────┐
│                      ACC State Machine                       │
└─────────────────────────────────────────────────────────────┘

[OFF] ──driver press──> [STANDBY] ──set button──> [ACTIVE]
  ▲                        ▲                           │
  │                        │                           │
  └────cancel button───────┘                           ▼
                                            [DISTANCE_CONTROL]
                                                    │
                                                    │ vehicle lost
                                                    ▼
                                            [SPEED_CONTROL]
                                                    │
                                                    │ driver brake
                                                    ▼
                                             [OVERRIDE] ──> [ACTIVE]
                                                    │
                                                    │ fault
                                                    ▼
                                            [FAULT] ──> [STANDBY]
```

### State Transitions (AUTOSAR Pattern)
```c
typedef enum {
    ACC_STATE_OFF,
    ACC_STATE_STANDBY,
    ACC_STATE_ACTIVE,
    ACC_STATE_DISTANCE_CONTROL,
    ACC_STATE_SPEED_CONTROL,
    ACC_STATE_OVERRIDE,
    ACC_STATE_FAULT
} AccState_t;

AccState_t acc_transition(
    AccState_t current_state,
    AccInputs_t* inputs,
    AccDiagnostics_t* diag) {

    switch (current_state) {
        case ACC_STATE_OFF:
            if (inputs->acc_button_pressed) {
                if (diag->system_ready && inputs->speed_valid) {
                    return ACC_STATE_STANDBY;
                }
            }
            break;

        case ACC_STATE_STANDBY:
            if (inputs->set_button_pressed && inputs->speed >= MIN_ACC_SPEED_KMH) {
                return ACC_STATE_ACTIVE;
            }
            if (inputs->cancel_button || inputs->brake_pressed) {
                return ACC_STATE_OFF;
            }
            break;

        case ACC_STATE_ACTIVE:
        case ACC_STATE_DISTANCE_CONTROL:
        case ACC_STATE_SPEED_CONTROL:
            if (diag->fault_detected) {
                return ACC_STATE_FAULT;
            }
            if (inputs->brake_pressed || inputs->clutch_pressed) {
                return ACC_STATE_OVERRIDE;
            }
            if (inputs->cancel_button) {
                return ACC_STATE_STANDBY;
            }
            /* Transition between distance/speed control based on target */
            if (inputs->target_vehicle_valid) {
                return ACC_STATE_DISTANCE_CONTROL;
            } else {
                return ACC_STATE_SPEED_CONTROL;
            }
            break;

        case ACC_STATE_OVERRIDE:
            if (diag->fault_detected) {
                return ACC_STATE_FAULT;
            }
            if (!inputs->brake_pressed && !inputs->clutch_pressed) {
                return ACC_STATE_ACTIVE;  /* Resume */
            }
            break;

        case ACC_STATE_FAULT:
            if (!diag->fault_present && inputs->ignition_cycle) {
                return ACC_STATE_STANDBY;
            }
            break;

        default:
            return ACC_STATE_FAULT;
    }

    return current_state;
}
```

## Target Selection Algorithm

```python
def select_target_vehicle(tracks: List[VehicleTrack],
                           ego_lane: LaneInfo,
                           curve_radius: float) -> Optional[VehicleTrack]:
    """
    Select the relevant lead vehicle for ACC control.

    Criteria:
    1. Same lane or lane overlap > 50%
    2. Relative velocity indicates slower or stationary
    3. Closest valid target in longitudinal distance
    4. Hysteresis to prevent oscillation
    """
    valid_targets = []

    for track in tracks:
        # Check lateral position (lane membership)
        lateral_offset = track.lateral_position - ego_lane.centerline
        if abs(lateral_offset) > LANE_WIDTH_M / 2.0:
            continue  # Not in lane

        # Check relative velocity (must be relevant threat)
        if track.relative_velocity > EGO_VELOCITY + 5.0:
            continue  # Moving away

        # Check longitudinal distance (within ACC range)
        if track.longitudinal_distance > MAX_ACC_RANGE_M:
            continue

        # Calculate probability of being in ego path
        path_probability = calculate_lane_overlap(track, ego_lane, curve_radius)
        if path_probability < 0.5:
            continue

        valid_targets.append((track, track.longitudinal_distance, path_probability))

    if not valid_targets:
        return None

    # Select closest target with highest probability
    valid_targets.sort(key=lambda x: (x[1], -x[2]))
    return valid_targets[0][0]
```

## Safety Mechanisms

### Plausibility Checks
```c
typedef struct {
    float radar_range_m;
    float camera_range_m;
    float range_discrepancy_max;  /* e.g., 5.0 m */
} CrossCheck_t;

bool plausibility_check_akk(AccInputs_t* inputs) {
    /* Radar-Camera cross-validation */
    if (inputs->radar_target_valid && inputs->camera_target_valid) {
        float discrepancy = fabsf(inputs->radar_range - inputs->camera_range);
        if (discrepancy > inputs->cross_check.range_discrepancy_max) {
            report_plausibility_fault(FAULT_RADAR_CAMERA_MISMATCH);
            return false;
        }
    }

    /* Physical limit check */
    if (inputs->target_relative_accel < -10.0f ||
        inputs->target_relative_accel > 5.0f) {
        report_plausibility_fault(FAULT_IMPLAUSIBLE_ACCEL);
        return false;
    }

    /* Rate-of-change check */
    static float prev_range = 0.0f;
    float range_rate = fabsf(inputs->target_range - prev_range) / DT;
    if (range_rate > MAX_PHYSICAL_RANGE_RATE) {
        report_plausibility_fault(FAULT_RANGE_JUMP);
        return false;
    }
    prev_range = inputs->target_range;

    return true;
}
```

### Fallback Strategy
```
Degradation Levels:

Level 0 (Normal): Full ACC functionality
Level 1 (Degraded): Radar unavailable, camera-only (reduced confidence)
Level 2 (Degraded): Camera unavailable, radar-only (no curve adaptation)
Level 3 (Fallback): Safe speed reduction, request driver takeover
Level 4 (Safe State): ACC OFF, warn driver, apply gentle deceleration if needed
```

## Approach

1. **Define system requirements** from customer/V-model
   - Speed range (0-180 km/h for full-speed range)
   - Time gap settings (3-5 levels typically)
   - Comfort vs. sport mode calibration

2. **Design control architecture** following AUTOSAR patterns
   - SWC interfaces (Rte_Read/Rte_Write)
   - Runnable timing (10-20 ms typical)
   - NVM storage for driver preferences

3. **Implement** with safety mechanisms
   - Input validation and signal quality checks
   - End-to-end protection on actuator commands
   - Watchdog monitoring

4. **Calibrate** for desired behavior
   - PID gains for comfort (jerk limits)
   - Time gap vs. speed scheduling
   - Cut-in detection sensitivity

5. **Validate** per ISO 26262 and NCAP protocols
   - Cut-in scenarios (near/far, slow/fast)
   - Lead vehicle braking scenarios
   - Curve negotiation
   - Stop-and-go traffic

## Deliverables

- Control algorithm specification (Simulink model)
- Production code (C with MISRA compliance)
- Calibration parameter files (.a2l, .hex)
- Test report (MIL/SIL/HIL with scenario coverage)
- Safety documentation (FMEA, FTA, HARA)

## Related Context
- @context/skills/safety/iso-26262-overview.md
- @context/skills/safety/safety-mechanisms-patterns.md
- @context/skills/powertrain/longitudinal-control.md
- @context/skills/chassis/brake-control.md
- @context/skills/adas/sensor-fusion.md
- @context/skills/testing/scenario-based-testing.md

## Tools Required
- MATLAB/Simulink (model-based design)
- ATI Vision or ETAS INCA (calibration)
- dSPACE or ETAS HIL (hardware-in-loop testing)
- Vector CANoe (network analysis)
- IPG CarMaker or VTD (scenario simulation)