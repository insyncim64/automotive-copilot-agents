# ADAS Perception Pipeline Example

This example demonstrates a complete **ADAS perception pipeline workflow** using MCP (Model Context Protocol) tools for camera/LiDAR calibration, sensor fusion, perception evaluation, and scenario testing.

## Workflow Overview

The ADAS perception pipeline follows a **6-stage workflow**:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    ADAS Perception Pipeline Workflow                     │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Stage 1: ODD Definition                                                 │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ Tool: adas-odd-define                                           │     │
│  │ Output: 01-odd-definition.md                                    │     │
│  │ - Operational Design Domain specification                       │     │
│  │ - Road types, speed ranges, weather conditions                  │     │
│  │ - Traffic participant types                                     │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                    │                                    │
│                                    v                                    │
│  Stage 2: Sensor Calibration                                             │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ Tools: adas-camera-calibrate, adas-lidar-calibrate              │     │
│  │ Output: 02-sensor-calibration-report.md                         │     │
│  │ - Camera intrinsics (focal length, principal point, distortion) │     │
│  │ - Camera extrinsics (rotation, translation to vehicle frame)    │     │
│  │ - LiDAR extrinsics (6-DoF pose)                                 │     │
│  │ - Multi-sensor time synchronization                             │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                    │                                    │
│                                    v                                    │
│  Stage 3: Sensor Fusion Configuration                                    │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ Tool: adas-sensor-fusion                                        │     │
│  │ Output: 03-sensor-fusion-config.md                              │     │
│  │ - Fusion architecture (early/late fusion)                       │     │
│  │ - Association algorithm (Hungarian, JPDA)                       │     │
│  │ - Tracking filter (Kalman, IMM)                                 │     │
│  │ - Confidence weighting                                          │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                    │                                    │
│                                    v                                    │
│  Stage 4: Perception Pipeline Execution                                  │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ Tool: adas-perception-pipeline                                  │     │
│  │ Output: 04-perception-pipeline-output.md                        │     │
│  │ - Object detection (camera, lidar, fused)                       │     │
│  │ - Object tracking (IDs, trajectories)                           │     │
│  │ - Free space detection                                          │     │
│  │ - Lane marking detection                                        │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                    │                                    │
│                                    v                                    │
│  Stage 5: Perception Evaluation                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ Tool: adas-perception-eval                                      │     │
│  │ Output: 05-perception-evaluation-report.md                      │     │
│  │ - Precision/Recall/F1-score                                     │     │
│  │ - MOTA/MOTP (Multi-Object Tracking metrics)                     │     │
│  │ - Latency analysis                                              │     │
│  │ - Ground truth comparison                                       │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                    │                                    │
│                                    v                                    │
│  Stage 6: Scenario Validation                                            │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │ Tool: adas-scenario-replay, adas-fusion-validate                │     │
│  │ Output: 06-scenario-validation-report.md                        │     │
│  │ - Critical scenario coverage                                    │     │
│  │ - Edge case detection                                           │     │
│  │ - Fusion algorithm validation                                   │     │
│  │ - ODD compliance verification                                   │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## MCP Tools Used

| Tool | Stage | Purpose |
|------|-------|---------|
| `adas-odd-define` | 1 | Define Operational Design Domain |
| `adas-camera-calibrate` | 2 | Camera intrinsic/extrinsic calibration |
| `adas-lidar-calibrate` | 2 | LiDAR extrinsic calibration |
| `adas-sensor-fusion` | 3 | Configure sensor fusion pipeline |
| `adas-perception-pipeline` | 4 | Execute perception algorithms |
| `adas-perception-eval` | 5 | Evaluate perception performance |
| `adas-scenario-replay` | 6 | Replay critical scenarios |
| `adas-fusion-validate` | 6 | Validate fusion algorithm |

## Directory Structure

```
adas-perception-pipeline/
├── README.md                              # This file
├── mcp-invocations.json                   # JSON-RPC 2.0 tool invocations
├── 01-odd-definition.md                   # ODD specification
├── 02-sensor-calibration-report.md        # Camera + LiDAR calibration results
├── 03-sensor-fusion-config.md             # Fusion architecture configuration
├── 04-perception-pipeline-output.md       # Pipeline execution results
├── 05-perception-evaluation-report.md     # Precision/Recall/MOTA metrics
└── 06-scenario-validation-report.md       # Scenario coverage analysis
```

## Usage

### Prerequisites

- ADAS MCP tools installed (see `../../README.md`)
- Sensor dataset (camera images + LiDAR point clouds)
- Ground truth annotations for evaluation
- Calibration targets (checkerboard for camera, reflectors for LiDAR)

### Running the Workflow

```bash
# Option 1: Run individual tools sequentially
adas-odd-define --output 01-odd-definition.yaml
adas-camera-calibrate --images calibration_images/ --output camera_intrinsics.yaml
adas-lidar-calibrate --pointclouds calibration_scans/ --output lidar_extrinsics.yaml
adas-sensor-fusion --config fusion_config.yaml --output 03-fusion-config.md
adas-perception-pipeline --data dataset/ --config pipeline.yaml --output 04-pipeline-output.md
adas-perception-eval --results 04-pipeline-output.md --ground-truth gt/ --output 05-evaluation.md
adas-scenario-replay --scenarios critical_scenarios.yaml --output 06-validation.md

# Option 2: Use the automation script (recommended)
python ../../tools/mcp_automation.py \
    --config mcp-invocations.json \
    --output-dir ./ \
    --dataset /path/to/dataset/
```

### Expected Outputs

| File | Description | Size (approx.) |
|------|-------------|----------------|
| `01-odd-definition.md` | ODD specification with road types, conditions | 5-10 KB |
| `02-sensor-calibration-report.md` | Calibration parameters for all sensors | 15-25 KB |
| `03-sensor-fusion-config.md` | Fusion architecture and parameters | 8-12 KB |
| `04-perception-pipeline-output.md` | Detection/tracking results | 30-50 KB |
| `05-perception-evaluation-report.md` | Metrics and ground truth comparison | 20-30 KB |
| `06-scenario-validation-report.md` | Scenario coverage and edge cases | 15-20 KB |

## ODD Definition (Stage 1)

The ODD (Operational Design Domain) defines where and when the ADAS system is designed to operate:

```yaml
odd:
  name: "Highway_Pilot_ODD"
  version: "1.0"

  road_types:
    - highway: { min_lanes: 2, max_lanes: 4, median: required }
    - expressway: { min_lanes: 2, access: controlled }

  speed_range:
    min_kmh: 0
    max_kmh: 130

  weather_conditions:
    - clear: { visibility_km: ">10" }
    - rain_light: { precipitation_mm_h: "<5" }
    - rain_moderate: { precipitation_mm_h: "5-15" }
    - fog_light: { visibility_km: "1-5" }

  lighting_conditions:
    - daylight
    - dusk
    - dawn
    - artificial_lighting

  geographic_constraints:
    lane_markings: [solid, dashed, double]
    curvature_max_deg: 15
    gradient_max_percent: 8

  exclusions:
    - construction_zones
    - unpaved_roads
    - toll_stations
    - tunnels_without_lighting
```

## Sensor Calibration (Stage 2)

### Camera Calibration

Camera calibration determines intrinsic and extrinsic parameters:

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| Focal length x | f_x | 912.4 | px |
| Focal length y | f_y | 913.1 | px |
| Principal point x | c_x | 965.2 | px |
| Principal point y | c_y | 542.8 | px |
| Radial distortion k1 | k1 | -0.312 | - |
| Radial distortion k2 | k2 | 0.124 | - |
| Tangential distortion p1 | p1 | 0.0012 | - |
| Tangential distortion p2 | p2 | -0.0008 | - |

### LiDAR Calibration

LiDAR extrinsic calibration (6-DoF pose relative to vehicle frame):

```
Rotation (quaternion): [0.9998, -0.0142, 0.0089, -0.0121]
Translation: [1.42, -0.15, 2.18] m

Rotation matrix:
[[ 0.9997, -0.0245,  0.0031],
 [ 0.0246,  0.9995, -0.0189],
 [-0.0026,  0.0190,  0.9998]]
```

## Sensor Fusion (Stage 3)

### Fusion Architecture

```
┌─────────────────┐    ┌─────────────────┐
│  Camera Stream  │    │  LiDAR Stream   │
│   (30 FPS)      │    │   (10 Hz)       │
└────────┬────────┘    └────────┬────────┘
         │                      │
         v                      v
┌─────────────────┐    ┌─────────────────┐
│  2D Detection   │    │  3D Detection   │
│   (YOLOv5)      │    │  (PointPillars) │
└────────┬────────┘    └────────┬────────┘
         │                      │
         │    ┌─────────────┐   │
         └───>│  Association│<──┘
              │  (Hungarian)│
              └──────┬──────┘
                     │
                     v
              ┌─────────────┐
              │ Fusion Gate │
              │ Confidence  │
              │ Weighting   │
              └──────┬──────┘
                     │
                     v
              ┌─────────────┐
              │ Multi-Object│
              │ Tracker     │
              │ (Imm-Kalman)│
              └──────┬──────┘
                     │
                     v
              ┌─────────────┐
              │ Fused Track │
              │ List        │
              └─────────────┘
```

### Association Algorithm

- **Method**: Hungarian algorithm with IoU + velocity cost
- **Cost function**: `cost = 0.6 * (1-IoU) + 0.3 * vel_diff + 0.1 * class_mismatch`
- **Gating threshold**: IoU > 0.2, velocity diff < 15 m/s

### Tracking Filter

- **Filter type**: Interacting Multiple Model (IMM) Kalman Filter
- **Motion models**: Constant velocity, constant acceleration, maneuvering
- **Process noise**: Adaptive based on innovation
- **Update rate**: 30 Hz (camera-synchronized)

## Perception Evaluation (Stage 5)

### Detection Metrics

| Class | Precision | Recall | F1-Score | AP@0.5 |
|-------|-----------|--------|----------|--------|
| Vehicle | 0.942 | 0.918 | 0.930 | 0.927 |
| Pedestrian | 0.891 | 0.856 | 0.873 | 0.864 |
| Cyclist | 0.867 | 0.823 | 0.844 | 0.831 |
| Traffic Sign | 0.923 | 0.945 | 0.934 | 0.941 |

### Tracking Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| MOTA (Multi-Object Tracking Accuracy) | 0.847 | >0.80 | PASS |
| MOTP (Multi-Object Tracking Precision) | 0.912 | >0.85 | PASS |
| IDF1 (Identity F1-Score) | 0.823 | >0.75 | PASS |
| Mostly Tracked (%) | 78.5 | >70 | PASS |
| Mostly Lost (%) | 4.2 | <10 | PASS |
| Fragmentation (avg per track) | 1.3 | <2 | PASS |

### Latency Analysis

| Stage | Latency (ms) | Budget (ms) | Status |
|-------|-------------|-------------|--------|
| Camera capture | 12 | 16.7 | OK |
| LiDAR capture | 8 | 20 | OK |
| Camera preprocessing | 3 | 5 | OK |
| LiDAR preprocessing | 5 | 8 | OK |
| 2D detection (GPU) | 18 | 25 | OK |
| 3D detection (GPU) | 22 | 30 | OK |
| Association | 4 | 8 | OK |
| Tracking filter | 2 | 5 | OK |
| **Total (P50)** | **74** | **100** | OK |
| **Total (P99)** | **89** | **100** | OK |

## Scenario Validation (Stage 6)

### Scenario Categories Tested

| Category | Count | Coverage | Critical Scenarios |
|----------|-------|----------|-------------------|
| Highway cut-in | 24 | 92% | 3 |
| Emergency braking | 18 | 88% | 5 |
| Lane change | 31 | 95% | 2 |
| Construction zone | 12 | 75% | 4 |
| Adverse weather | 15 | 82% | 3 |
| Night driving | 20 | 90% | 2 |
| **Total** | **120** | **87%** | **19** |

### Critical Scenario Analysis

| Scenario ID | Description | Perception Failure | Root Cause | Mitigation |
|-------------|-------------|-------------------|------------|------------|
| CS-001 | Vehicle cut-in at 100 km/h, rain | Missed detection for 300ms | Radar clutter | Improve rain filtering |
| CS-002 | Pedestrian crossing at dusk | False negative | Low contrast | Add thermal camera |
| CS-003 | Cyclist in blind spot | Track ID switch | Occlusion | Improve association logic |

## Integration with Functional Safety

### ISO 26262 Compliance

The ADAS perception pipeline supports ISO 26262 ASIL-B (QM for some components) development:

- **HARA input**: ODD definition identifies hazardous scenarios
- **FMEA input**: Sensor fusion config identifies failure modes
- **FTA input**: Perception evaluation identifies top events
- **Validation**: Scenario validation provides evidence for safety case

### SOTIF (ISO 21448) Compliance

- **Triggering conditions**: ODD definition + scenario catalog
- **Known limitations**: Documented in evaluation report
- **Unknown unsafe**: Minimized through extensive scenario testing

## References

- ISO 26262:2018 - Road vehicles - Functional safety
- ISO 21448:2022 - Road vehicles - Safety of the Intended Functionality (SOTIF)
- ISO 34501:2021 - Scenario-based safety evaluation framework
- KITTI Vision Benchmark Suite - http://www.cvlibs.net/datasets/kitti/
- nuScenes Dataset - https://www.nuscenes.org/
- Apollo SOTIF Framework - https://github.com/ApolloAuto/apollo

## Tool Execution Metadata

| Tool | Version | AUTOSAR/ISO Standard | Status |
|------|---------|---------------------|--------|
| adas-odd-define | 2.1.0 | ISO 21448, ISO 34501 | Success |
| adas-camera-calibrate | 1.8.2 | ISO 16505 | Success |
| adas-lidar-calibrate | 1.5.0 | ISO 16505 | Success |
| adas-sensor-fusion | 2.3.1 | ISO 26262-3 | Success |
| adas-perception-pipeline | 3.2.0 | ISO 21448 | Success |
| adas-perception-eval | 2.0.4 | ISO 8000-61 | Success |
| adas-scenario-replay | 1.4.0 | ISO 34502 | Success |
| adas-fusion-validate | 1.2.0 | ISO 26262-9 | Success |

---

**Generated by automotive-copilot-agents v2.1.0**
**Last updated**: 2026-03-24
