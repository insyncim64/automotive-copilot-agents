---
name: adas-sensor-fusion
description: "Use when: Skill: Sensor Fusion for ADAS topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: Sensor Fusion for ADAS

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/adas/sensor-fusion.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate
- User asks about multi-sensor fusion (camera, radar, LiDAR)
- User requests sensor fusion algorithm implementation
- User needs calibration, synchronization, or object tracking guidance
- User is designing ADAS perception pipelines

## Standards Compliance
- ISO 26262 ASIL B/D (depending on function)
- ASPICE Level 3
- AUTOSAR 4.4 Classic/Adaptive
- ISO 21434 (Cybersecurity)
- ISO 21448 (SOTIF)

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Sensor update rates | Camera: 30-60, Radar: 10-20, LiDAR: 10-20 | Hz |
| Fusion latency budget | < 50 | ms |
| Object tracking capacity | 100-256 | simultaneous objects |
| Association gate | 2.0-3.5 | sigma (Mahalanobis distance) |
| Track confirmation threshold | 3-5 | consecutive detections |
| Track coasting limit | 5-10 | missed frames |

## Fusion Architecture Levels

### Level 1: Raw Data Fusion
- Combines raw sensor data before feature extraction
- Requires precise temporal/spatial alignment
- Maximum information retention
- High bandwidth requirements

### Level 2: Feature-Level Fusion
- Each sensor extracts features independently
- Features combined in common reference frame
- Balance of bandwidth and accuracy
- Most common in production ADAS

### Level 3: Object-Level Fusion
- Each sensor produces object lists
- Fusion performs track-to-track association
- Lower bandwidth, modular architecture
- Robust to individual sensor failures

## Core Competencies

### Sensor Models
```
Camera:
  - 2D bounding boxes, lane markings, traffic signs
  - High angular resolution, no direct range
  - Affected by lighting, weather, occlusion

Radar:
  - Range, range-rate (Doppler), azimuth
  - 4D imaging: elevation capability
  - Robust in adverse weather, lower angular resolution

LiDAR:
  - 3D point cloud, high-accuracy range
  - 360° or forward-facing FOV
  - Affected by rain, snow, fog, dust
```

### Fusion Algorithms
| Algorithm | Use Case | Complexity | ASIL Suitability |
|-----------|----------|------------|------------------|
| Kalman Filter (EKF/UKF) | State estimation | Low-Medium | ASIL B/D |
| Particle Filter | Non-Gaussian, multi-modal | High | ASIL B |
| Hungarian Algorithm | Data association | Medium | ASIL B |
| JPDA | Multi-target association | High | ASIL B |
| Deep Learning (PointPillars, CenterFusion) | End-to-end fusion | Very High | QM (explainability challenge) |

### Calibration Requirements
```
Extrinsic Calibration:
  - Rotation matrix R (3x3) between sensors
  - Translation vector t (x, y, z) in meters
  - Accuracy: < 0.1° rotation, < 5 cm translation

Intrinsic Calibration:
  - Camera: focal length, principal point, distortion
  - Radar: range bias, azimuth offset
  - LiDAR: beam angles, range offset

Temporal Synchronization:
  - Hardware trigger (PTP/IEEE 1588)
  - Timestamp alignment < 1 ms
  - Motion compensation for ego vehicle
```

## Approach

1. **Analyze requirements** against automotive standards
   - Identify ASIL level from HARA
   - Define ODD and triggering conditions (SOTIF)
   - Establish performance KPIs (detection rate, false positive rate)

2. **Design solution** following AUTOSAR patterns
   - Define SWC interfaces (Sender-Receiver ports)
   - Specify runnable entities and timing (10-100 ms)
   - Allocate to ECU (Classic vs. Adaptive platform)

3. **Implement** with safety and security considerations
   - Input validation and plausibility checks
   - End-to-end protection (AUTOSAR E2E)
   - Secure boot and runtime integrity

4. **Validate** per ISO 26262 requirements
   - Requirements-based testing (100% coverage)
   - Fault injection (sensor failure modes)
   - Back-to-back testing (model vs. code)

## Deliverables

- Technical specification (interface definitions, timing budgets)
- Implementation (C/C++/Model with MISRA compliance)
- Test cases and results (SIL/HIL with coverage reports)
- Safety documentation (FMEA, FTA, safety manual)

## Related Context
- @context/skills/safety/iso-26262-overview.md
- @context/skills/safety/safety-mechanisms-patterns.md
- @context/skills/security/iso-21434-compliance.md
- @context/skills/adas/object-detection.md
- @context/skills/adas/adaptive-cruise-control.md
- @context/skills/sotif/triggering-condition-analysis.md

## Tools Required
- MATLAB/Simulink (algorithm development)
- Vector CANoe/CANalyzer (network analysis)
- Static analyzer (Polyspace/Klocwork for MISRA)
- AUTOSAR toolchain (DaVinci, EB Tresos)
- Sensor simulation (Carla, VTD, IPG CarMaker)