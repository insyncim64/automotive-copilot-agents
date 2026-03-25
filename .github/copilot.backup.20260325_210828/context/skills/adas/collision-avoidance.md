# Skill: Collision Avoidance System Development

## Standards Compliance

- ISO 26262 ASIL C/D
- ASPICE Level 3
- AUTOSAR 4.4
- ISO 21434

## Core Competencies

Expert in collision avoidance system development for automotive applications.

## Key System Parameters

| Parameter | Range | Unit |
|-----------|-------|------|
| Detection range (forward) | 0.5 - 200 | m |
| Detection range (rear) | 0.2 - 50 | m |
| Time-to-collision (TTC) | 0.5 - 5.0 | s |
| AEB activation speed | 5 - 80 | km/h |
| FCW warning time | 1.5 - 3.0 | s |
| Braking deceleration | 0.3 - 0.8 | g |
| System latency | < 100 | ms |

## Domain-Specific Content

### Collision Avoidance Functions

1. **Forward Collision Warning (FCW)**
   - Visual, audible, and haptic warnings
   - Escalating alert levels based on TTC
   - Driver response monitoring

2. **Automatic Emergency Braking (AEB)**
   - Partial braking for warning escalation
   - Full emergency braking if driver unresponsive
   - Pedestrian and cyclist detection

3. **Rear Collision Warning**
   - Cross-traffic alert during reversing
   - Rear-end collision mitigation
   - Active braking if needed

4. **Lane Change Assistance**
   - Blind spot monitoring integration
   - Side collision warning
   - Emergency lane keeping

### Sensor Fusion Architecture

- **Primary Sensors**: Front radar, front camera
- **Secondary Sensors**: Corner radars, side cameras
- **Supporting Sensors**: Ultrasonic, IMU, wheel speed

### Threat Assessment Algorithm

```
1. Object Detection & Classification
        ↓
2. Trajectory Prediction (EKF/UKF)
        ↓
3. Time-to-Collision Calculation
        ↓
4. Risk Assessment (TTC, distance, relative velocity)
        ↓
5. Mitigation Strategy Selection
        ↓
6. Actuator Command (Brake/Steer/Warning)
```

## Implementation Approach

1. Analyze requirements against automotive standards
2. Design solution following AUTOSAR patterns
3. Implement with safety and security considerations
4. Validate per ISO 26262 requirements

## Deliverables

- Technical specification
- Implementation (C/C++/Model)
- Test cases and results
- Safety documentation

## Constraints

- ISO 26262 functional safety compliance
- Real-time performance requirements
- Resource constraints (CPU/Memory)
- AUTOSAR architecture adherence

## Required Tools

- MATLAB/Simulink
- Vector CANoe/CANalyzer
- Static analyzer (Polyspace/Klocwork)
- AUTOSAR toolchain

## Metadata

- **Author**: Automotive Claude Code Agents
- **Last Updated**: 2026-03-19
- **Maturity**: Production
- **Complexity**: Intermediate

## Related Context

- @context/skills/adas/sensor-fusion.md
- @context/skills/adas/object-tracking.md
- @context/skills/safety/iso-26262-overview.md
- @context/skills/safety/sotif.md
