---
name: adas-automated-parking
description: "Use when: Skill: Automated Parking System Development topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: Automated Parking System Development

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/adas/automated-parking.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## Standards Compliance

- ISO 26262 ASIL C/D
- ASPICE Level 3
- AUTOSAR 4.4
- ISO 21434

## Core Competencies

Expert in automated parking system development for automotive applications.

## Key System Parameters

| Parameter | Range | Unit |
|-----------|-------|------|
| Parking space detection range | 0.5 - 5.0 | m |
| Lateral accuracy | < 10 | cm |
| Longitudinal accuracy | < 15 | cm |
| Maximum steering angle | 30 - 45 | deg |
| Operating speed | 0 - 15 | km/h |
| Ultrasonic sensor range | 0.2 - 4.5 | m |
| Camera FOV | 120 - 190 | deg |

## Domain-Specific Content

### Parking Maneuver Types

1. **Parallel Parking**
   - Rear-end first or nose-in
   - Requires precise lateral control
   - Typical space margin: 0.5 - 0.8m buffer

2. **Perpendicular Parking**
   - Forward or reverse entry
   - Requires accurate centering
   - Typical space width: 2.5 - 3.0m

3. **Angle Parking**
   - 45° or 60° angle entry
   - Common in retail parking lots
   - Requires path planning with curved trajectory

### Sensor Suite

- **Ultrasonic Sensors**: 8-12 sensors for proximity detection
- **Surround View Cameras**: 4+ cameras for bird's-eye view
- **Radar**: Short-range radar for object detection
- **IMU**: Vehicle orientation and trajectory tracking

### Control Architecture

```
+------------------+     +------------------+     +------------------+
| Perception Layer | --> | Planning Layer   | --> | Control Layer    |
| - Space detect   |     | - Path planning  |     | - Steering ctrl  |
| - Object detect  |     | - Trajectory gen |     | - Speed ctrl     |
| - Localization   |     | - Collision check|     | - Gear selection |
+------------------+     +------------------+     +------------------+
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
- @context/skills/adas/object-detection.md
- @context/skills/safety/iso-26262-overview.md
- @context/skills/autosar/classic-platform.md