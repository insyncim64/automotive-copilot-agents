# Perception Pipeline Output: Highway Pilot ADAS System

## Pipeline Execution Summary

**Tool**: `adas-perception-pipeline`
**Version**: 3.2.0 (ISO 21448 SOTIF compliant)
**Execution Time**: 74.3 ms (P50), 89.1 ms (P99)
**Status**: SUCCESS

---

## Input Configuration

### Pipeline Configuration

```yaml
pipeline_config:
  name: "Highway_Pilot_Perception_v2.4"
  asil: B
  fusion_architecture: "Late fusion with track-level association"

  sensor_inputs:
    camera:
      id: CAM_FRONT_001
      resolution: [1920, 1080]
      frame_rate_hz: 30
      intrinsics_file: camera_intrinsics.yaml
      extrinsics_file: camera_extrinsics.yaml

    lidar:
      id: LIDAR_FRONT_001
      channels: 128
      scan_rate_hz: 10
      extrinsics_file: lidar_extrinsics.yaml

  fusion_config:
    association_algorithm: "Hungarian"
    tracking_filter: "IMM-Kalman"
    motion_models: [CV, CA, CT]
    confidence_weighting: true

  operating_conditions:
    weather: clear
    lighting: daylight
    road_type: highway
    ego_speed_kmh: 85.0
```

### Processing Parameters

```yaml
processing_params:
  camera_pipeline:
    detector: "YOLOv5x"
    input_size: [640, 640]
    confidence_threshold: 0.45
    iou_threshold: 0.45
    max_detections: 100

  lidar_pipeline:
    detector: "PointPillars"
    voxel_size: [0.16, 0.16, 4.0]
    pillar_size: [0.16, 0.16]
    max_points_per_pillar: 100
    confidence_threshold: 0.5

  tracking:
    update_rate_hz: 30
    max_tracks: 200
    tentative_threshold: 2
    confirmed_miss_threshold: 3
    coasting_max_frames: 5
```

---

## Object Detection Results

### Camera 2D Detections

```yaml
camera_detections:
  frame_id: 12847
  timestamp: "2025-03-24T14:32:18.456Z"
  exposure_ms: 12.3
  gain_db: 18.5

  detections:
    - id: CAM_DET_001
      class: vehicle
      confidence: 0.94
      bbox_2d:
        x_min: 856
        y_min: 412
        x_max: 1124
        y_max: 598
      center_pixel: [990, 505]
      estimated_distance_m: 48.2

    - id: CAM_DET_002
      class: vehicle
      confidence: 0.89
      bbox_2d:
        x_min: 1245
        y_min: 378
        x_max: 1456
        y_max: 512
      center_pixel: [1350, 445]
      estimated_distance_m: 62.5

    - id: CAM_DET_003
      class: pedestrian
      confidence: 0.76
      bbox_2d:
        x_min: 342
        y_min: 489
        x_max: 398
        y_max: 612
      center_pixel: [370, 550]
      estimated_distance_m: 35.8

    - id: CAM_DET_004
      class: traffic_sign
      confidence: 0.91
      bbox_2d:
        x_min: 1567
        y_min: 234
        x_max: 1612
        y_max: 298
      center_pixel: [1589, 266]
      estimated_distance_m: 78.3

  processing_stats:
    inference_time_ms: 18.4
    preprocessing_time_ms: 3.2
    postprocessing_time_ms: 2.1
    total_time_ms: 23.7
```

### LiDAR 3D Detections

```yaml
lidar_detections:
  frame_id: 4283
  timestamp: "2025-03-24T14:32:18.467Z"
  scan_duration_ms: 8.2
  point_count: 187432

  detections:
    - id: LIDAR_DET_001
      class: vehicle
      confidence: 0.91
      bbox_3d:
        center: [50.1, -1.9, 0.6]  # ISO 8855: X-forward, Y-left, Z-up
        dimensions: [4.6, 1.9, 1.6]  # L, W, H
        yaw_rad: 0.02
      velocity: [0.3, 0.0, 0.0]  # m/s (Doppler)
      point_count: 847

    - id: LIDAR_DET_002
      class: vehicle
      confidence: 0.87
      bbox_3d:
        center: [62.8, -5.2, 0.8]
        dimensions: [4.8, 2.0, 1.7]
        yaw_rad: -0.05
      velocity: [-2.1, 0.8, 0.0]
      point_count: 623

    - id: LIDAR_DET_003
      class: pedestrian
      confidence: 0.82
      bbox_3d:
        center: [35.2, 8.4, 0.2]
        dimensions: [0.7, 0.6, 1.8]
        yaw_rad: 1.57
      velocity: [1.2, -0.3, 0.0]
      point_count: 34

    - id: LIDAR_DET_004
      class: unknown
      confidence: 0.64
      bbox_3d:
        center: [78.5, 12.3, 1.2]
        dimensions: [1.2, 0.8, 1.5]
        yaw_rad: 0.0
      velocity: [0.0, 0.0, 0.0]
      point_count: 18
      note: "Roadside debris or signpost"

  processing_stats:
    voxelization_time_ms: 4.8
    backbone_inference_ms: 22.1
    detection_head_ms: 3.4
    postprocessing_ms: 2.8
    total_time_ms: 33.1
```

### Fused Object List

```yaml
fused_objects:
  frame_id: 12847
  timestamp: "2025-03-24T14:32:18.530Z"
  fusion_latency_ms: 4.2

  objects:
    - id: FUSED_OBJ_001
      class: vehicle
      confidence: 0.93
      fused_state:
        position: [50.15, -1.85, 0.55]  # m
        velocity: [0.3, 0.0, 0.0]  # m/s
        dimensions: [4.6, 1.9, 1.6]  # m
        yaw_rad: 0.02
      sensor_contributions:
        camera:
          detection_id: CAM_DET_001
          confidence: 0.94
          weight: 0.644
        lidar:
          detection_id: LIDAR_DET_001
          confidence: 0.91
          weight: 0.704
      fusion_quality:
        position_uncertainty_m: 0.12
        velocity_uncertainty_ms: 0.08
        class_agreement: true

    - id: FUSED_OBJ_002
      class: vehicle
      confidence: 0.88
      fused_state:
        position: [62.8, -5.2, 0.8]
        velocity: [-2.1, 0.8, 0.0]
        dimensions: [4.8, 2.0, 1.7]
        yaw_rad: -0.05
      sensor_contributions:
        camera:
          detection_id: CAM_DET_002
          confidence: 0.89
          weight: 0.623
        lidar:
          detection_id: LIDAR_DET_002
          confidence: 0.87
          weight: 0.696
      fusion_quality:
        position_uncertainty_m: 0.18
        velocity_uncertainty_ms: 0.15
        class_agreement: true

    - id: FUSED_OBJ_003
      class: pedestrian
      confidence: 0.79
      fused_state:
        position: [35.4, 8.3, 0.15]
        velocity: [1.1, -0.2, 0.0]
        dimensions: [0.65, 0.55, 1.75]
        yaw_rad: 1.52
      sensor_contributions:
        camera:
          detection_id: CAM_DET_003
          confidence: 0.76
          weight: 0.532
        lidar:
          detection_id: LIDAR_DET_003
          confidence: 0.82
          weight: 0.656
      fusion_quality:
        position_uncertainty_m: 0.24
        velocity_uncertainty_ms: 0.22
        class_agreement: true

    - id: FUSED_OBJ_004
      class: traffic_sign
      confidence: 0.91
      fused_state:
        position: [78.3, 12.1, 1.3]
        velocity: [0.0, 0.0, 0.0]
        dimensions: [0.5, 0.6, 0.8]
        yaw_rad: -0.15
      sensor_contributions:
        camera:
          detection_id: CAM_DET_004
          confidence: 0.91
          weight: 0.637
        lidar:
          detection_id: null
          confidence: null
          weight: null
          note: "No LiDAR detection - camera-only track"
      fusion_quality:
        position_uncertainty_m: 0.45
        velocity_uncertainty_ms: null
        class_agreement: null
        single_sensor_track: true
```

---

## Object Tracking Results

### Active Track List

```yaml
active_tracks:
  timestamp: "2025-03-24T14:32:18.530Z"
  total_tracks: 47
  confirmed_tracks: 42
  tentative_tracks: 3
  coasting_tracks: 2

  tracks:
    - track_id: TRK_0042
      state: CONFIRMED
      class: vehicle
      age_frames: 18
      consecutive_hits: 18
      consecutive_misses: 0

      kinematic_state:
        position: [50.15, -1.85, 0.55]
        velocity: [0.3, 0.0, 0.0]
        acceleration: [0.02, 0.0, 0.0]
        yaw_rad: 0.02
        yaw_rate_rads: 0.0

      imm_filter:
        active_model: CV
        model_probabilities:
          CV: 0.87
          CA: 0.10
          CT: 0.03
        innovation_norm: 1.24
        innovation_gate: 2.5

      trajectory_history:
        - {t_ms: 0, pos: [49.85, -1.85, 0.55], vel: [0.3, 0.0, 0.0]}
        - {t_ms: 33, pos: [49.95, -1.85, 0.55], vel: [0.3, 0.0, 0.0]}
        - {t_ms: 66, pos: [50.05, -1.85, 0.55], vel: [0.3, 0.0, 0.0]}
        - {t_ms: 100, pos: [50.15, -1.85, 0.55], vel: [0.3, 0.0, 0.0]}

      relative_to_ego:
        distance_m: 50.2
        bearing_deg: -2.1
        ttca_s: 167.3  # Time to closest approach

    - track_id: TRK_0038
      state: CONFIRMED
      class: vehicle
      age_frames: 24
      consecutive_hits: 24
      consecutive_misses: 0

      kinematic_state:
        position: [62.8, -5.2, 0.8]
        velocity: [-2.1, 0.8, 0.0]
        acceleration: [-0.15, 0.05, 0.0]
        yaw_rad: -0.05
        yaw_rate_rads: -0.02

      imm_filter:
        active_model: CA
        model_probabilities:
          CV: 0.25
          CA: 0.68
          CT: 0.07
        innovation_norm: 1.87
        innovation_gate: 2.5

      relative_to_ego:
        distance_m: 63.2
        bearing_deg: -4.7
        ttca_s: 28.4
        lane_relative: "Left adjacent lane, moving slower"

    - track_id: TRK_0051
      state: CONFIRMED
      class: pedestrian
      age_frames: 8
      consecutive_hits: 8
      consecutive_misses: 0

      kinematic_state:
        position: [35.4, 8.3, 0.15]
        velocity: [1.1, -0.2, 0.0]
        acceleration: [0.05, -0.01, 0.0]
        yaw_rad: 1.52
        yaw_rate_rads: 0.0

      imm_filter:
        active_model: CV
        model_probabilities:
          CV: 0.72
          CA: 0.18
          CT: 0.10
        innovation_norm: 0.94
        innovation_gate: 2.5

      relative_to_ego:
        distance_m: 36.9
        bearing_deg: 13.4
        ttca_s: null
        risk_level: LOW
        note: "Pedestrian on shoulder, walking parallel"

    - track_id: TRK_0019
      state: TENTATIVE
      class: unknown
      age_frames: 1
      consecutive_hits: 1
      consecutive_misses: 0

      kinematic_state:
        position: [125.3, -18.7, 2.1]
        velocity: [0.0, 0.0, 0.0]
        acceleration: [0.0, 0.0, 0.0]
        yaw_rad: 0.0
        yaw_rate_rads: 0.0

      imm_filter:
        active_model: CV
        model_probabilities:
          CV: 0.90
          CA: 0.08
          CT: 0.02
        innovation_norm: null
        innovation_gate: 2.5

      note: "New detection - needs 1 more hit for confirmation"
```

### Track Statistics

```yaml
track_statistics:
  total_active: 47
  by_class:
    vehicle: 38
    pedestrian: 5
    cyclist: 2
    traffic_sign: 1
    unknown: 1

  by_state:
    confirmed: 42
    tentative: 3
    coasting: 2

  by_motion_model:
    CV: 35  # Constant velocity (steady motion)
    CA: 9   # Constant acceleration (braking/accelerating)
    CT: 3   # Coordinated turn (lane change/curve)

  quality_metrics:
    avg_track_age_frames: 14.3
    avg_consecutive_hits: 12.8
    track_id_switches_total: 2
    fragmentation_rate: 0.8  # Per track average
```

---

## Free Space Detection

### Drivable Area Analysis

```yaml
free_space:
  timestamp: "2025-03-24T14:32:18.530Z"
  method: "LiDAR ground segmentation + camera semantic segmentation"

  ego_lane:
    left_boundary:
      type: lane_marking
      marking_type: dashed
      distance_m: 1.85
      confidence: 0.94
      visibility: "visible"

    right_boundary:
      type: lane_marking
      marking_type: solid
      distance_m: 1.92
      confidence: 0.91
      visibility: "visible"

    drivable_width_m: 3.77
    lane_curvature: 0.002  # rad/m (nearly straight)
    lane_gradient: 0.01    # 1% uphill

  adjacent_lanes:
    left_lane:
      occupied: true
      nearest_vehicle_distance_m: 63.2
      relative_speed_ms: -2.4  # Slower than ego

    right_lane:
      occupied: false
      nearest_vehicle_distance_m: null

  free_space_polygon:
    coordinates: [
      [0.0, -2.0],    # Ego rear-left
      [0.0, 2.0],     # Ego rear-right
      [150.0, 2.5],   # Front-right (right boundary)
      [150.0, -2.5],  # Front-left (left boundary)
    ]
    unit: "meters"
    confidence: 0.89

  obstacles_in_path:
    - track_id: TRK_0042
      distance_m: 50.2
      lateral_offset_m: -1.85
      in_ego_lane: true
      ttca_s: 167.3

  clearance_analysis:
    clear_distance_ahead_m: 50.2
    safe_stopping_distance_m: 42.5  # At 85 km/h, 2.5s TTC
    margin_m: 7.7
    status: SAFE
```

---

## Lane Marking Detection

### Lane Detection Results

```yaml
lane_detection:
  timestamp: "2025-03-24T14:32:18.530Z"
  camera_source: CAM_FRONT_001
  algorithm: "Deep lane segmentation + polynomial fitting"

  detected_markings:
    - id: LANE_001
      type: ego_left_boundary
      marking_style: dashed
      color: white
      condition: good

      polynomial_fit:
        order: 3
        coefficients:
          c0: -1.85   # Lateral offset at ego (m)
          c1: 0.002   # Heading (rad)
          c2: 0.0001  # Curvature (1/m)
          c3: 0.0     # Curvature rate (1/m^2)

      confidence: 0.94
      visibility_range_m: [0.5, 85.0]
      occlusions: []

    - id: LANE_002
      type: ego_right_boundary
      marking_style: solid
      color: white
      condition: good

      polynomial_fit:
        order: 3
        coefficients:
          c0: 1.92
          c1: 0.001
          c2: 0.0001
          c3: 0.0

      confidence: 0.91
      visibility_range_m: [0.5, 78.0]
      occlusions: []

  lane_topology:
    current_lane:
      lane_id: L2  # Lane 2 of 4 (left to right)
      lane_type: general_purpose
      direction: forward

    lane_changes_available:
      - direction: left
        permitted: true
        marking_type: dashed
        adjacent_lane: L1
        traffic_present: true

      - direction: right
        permitted: false
        marking_type: solid
        adjacent_lane: L3
        traffic_present: false

  road_geometry:
    curvature_100m: 0.5  # deg/100m (gentle curve)
    superelevation: 0.02  # 2% bank
    grade: 0.01  # 1% uphill

  hd_map_alignment:
    map_matched: true
    map_lane_id: "HW-101-L2"
    localization_confidence: 0.96
```

---

## Pipeline Performance Metrics

### Latency Breakdown

```yaml
latency_analysis:
  frame_id: 12847
  pipeline_stage_latency:
    camera_capture: 12.1
    lidar_capture: 8.2
    camera_preprocessing: 3.2
    lidar_preprocessing: 4.8
    camera_detection: 18.4
    lidar_detection: 22.1
    association: 4.1
    tracking_filter: 2.3
    output_serialization: 1.1

  total_latency:
    p50_ms: 74.3
    p90_ms: 82.7
    p95_ms: 86.4
    p99_ms: 89.1
    worst_case_ms: 94.2

  budget_analysis:
    budget_ms: 100.0
    p50_utilization: 74.3%
    p99_utilization: 89.1%
    worst_case_utilization: 94.2%
    status: WITHIN_BUDGET

  bottleneck_analysis:
    slowest_stage: "LiDAR detection (22.1ms)"
    second_slowest: "Camera detection (18.4ms)"
    optimization_opportunity: "Consider TensorRT optimization for PointPillars"
```

### Throughput Statistics

```yaml
throughput:
  measurement_duration_s: 300.0  # 5 minute sample
  frames_processed: 9000
  average_fps: 30.0
  target_fps: 30.0

  dropped_frames:
    total: 3
    camera_drops: 2
    lidar_drops: 1
    drop_rate: 0.033%

  frame_timing_jitter:
    mean_ms: 33.33
    std_ms: 0.42
    max_jitter_ms: 2.1

  cpu_gpu_utilization:
    cpu_avg: 45.2%
    cpu_max: 78.4%
    gpu_avg: 62.1%
    gpu_max: 89.3%
    memory_avg_mb: 2847
    memory_max_mb: 3412
```

---

## Sample Output Data Structures

### C++ Output Structure

```cpp
// Perception pipeline output structure
struct PerceptionOutput {
    uint64_t timestamp_us;
    uint32_t frame_id;

    // Fused object list
    struct FusedObject {
        uint32_t object_id;
        ObjectType type;
        float confidence;

        // State in vehicle coordinates (ISO 8855)
        Eigen::Vector3f position;  // [x, y, z] in meters
        Eigen::Vector3f velocity;  // [vx, vy, vz] in m/s
        Eigen::Vector3f dimensions;  // [length, width, height] in meters
        float yaw_rad;
        float yaw_rate_rads;

        // Uncertainty
        Eigen::Matrix3f position_covariance;
        Eigen::Matrix3f velocity_covariance;

        // Track info
        uint32_t track_id;
        TrackState track_state;  // TENTATIVE, CONFIRMED, COASTING
        uint16_t age_frames;
        uint16_t consecutive_hits;
    };
    std::vector<FusedObject> objects;

    // Lane markings
    struct LaneMarking {
        LaneType type;
        MarkingStyle style;
        float lateral_offset_m;
        std::array<float, 4> polynomial_coeffs;  // c0, c1, c2, c3
        float confidence;
        float visibility_range_m;
    };
    LaneMarking left_boundary;
    LaneMarking right_boundary;

    // Free space
    struct FreeSpace {
        std::vector<Eigen::Vector2f> polygon;  // 2D polygon in vehicle frame
        float clear_distance_ahead_m;
        bool is_safe;
    };
    FreeSpace free_space;

    // Pipeline health
    struct PipelineHealth {
        float total_latency_ms;
        bool within_budget;
        uint16_t dropped_frame_count;
        float cpu_utilization;
        float gpu_utilization;
    };
    PipelineHealth health;
};
```

### ROS 2 Message Example

```yaml
# ROS 2 message publication
topic: /perception/output
msg_type: automotive_perception_msgs/msg/PerceptionPipelineOutput

header:
  stamp: {sec: 1711291938, nanosec: 530000000}
  frame_id: "base_link"

objects:
  - id: 42
    class: VEHICLE
    pose:
      position: {x: 50.15, y: -1.85, z: 0.55}
      orientation: {x: 0.0, y: 0.0, z: 0.02, w: 0.9998}
    twist:
      linear: {x: 0.3, y: 0.0, z: 0.0}
    dimensions: {x: 4.6, y: 1.9, z: 1.6}
    confidence: 0.93
    track_id: 42
    track_state: CONFIRMED

  - id: 38
    class: VEHICLE
    pose:
      position: {x: 62.8, y: -5.2, z: 0.8}
      orientation: {x: 0.0, y: 0.0, z: -0.05, w: 0.9987}
    twist:
      linear: {x: -2.1, y: 0.8, z: 0.0}
    dimensions: {x: 4.8, y: 2.0, z: 1.7}
    confidence: 0.88
    track_id: 38
    track_state: CONFIRMED

lanes:
  - type: EGO_LEFT
    marking_style: DASHED
    lateral_offset: -1.85
    confidence: 0.94

free_space:
  polygon: [{x: 0.0, y: -2.0}, {x: 0.0, y: 2.0}, ...]
  clear_distance: 50.2
  is_safe: true

pipeline_status:
  latency_ms: 74.3
  within_budget: true
  fps: 30.0
```

---

## Quality Assurance Checks

### Detection Quality

```yaml
detection_quality:
  check_name: "DET_001 - Detection count plausibility"
  expected_range: [10, 100]
  actual: 47
  status: PASS

  check_name: "DET_002 - Position range validation"
  threshold: "All detections within [0, 250]m"
  violations: 0
  status: PASS

  check_name: "DET_003 - Velocity plausibility"
  threshold: "All velocities within [-50, +50] m/s"
  violations: 0
  status: PASS

  check_name: "DET_004 - Dimension plausibility"
  threshold: "All dimensions within physical limits"
  violations: 0
  status: PASS
```

### Tracking Quality

```yaml
tracking_quality:
  check_name: "TRK_001 - Track continuity"
  threshold: "ID switches < 1% per frame"
  actual: 0.04%  # 2 switches / 47 tracks
  status: PASS

  check_name: "TRK_002 - Fragmentation rate"
  threshold: "< 2.0 per track average"
  actual: 0.8
  status: PASS

  check_name: "TRK_003 - Innovation gate"
  threshold: "All innovations < 2.5 sigma"
  violations: 0
  status: PASS

  check_name: "TRK_004 - Track age distribution"
  expected: "> 80% confirmed tracks"
  actual: 89.4%  # 42/47
  status: PASS
```

### Fusion Quality

```yaml
fusion_quality:
  check_name: "FUS_001 - Cross-sensor agreement"
  threshold: "Position disagreement < 5m"
  max_disagreement_m: 0.45
  status: PASS

  check_name: "FUS_002 - Single-sensor tracks"
  threshold: "< 10% of tracks"
  actual: 2.1%  # 1/47
  status: PASS

  check_name: "FUS_003 - Class agreement"
  threshold: "> 95% agreement rate"
  actual: 97.9%  # 46/47
  status: PASS
```

---

## Recommendations

### Priority 1 (Real-time Operation)

- [x] Pipeline latency within 100ms budget (P99: 89.1ms)
- [x] Detection quality meets requirements
- [x] Tracking continuity acceptable (ID switches: 0.04%)
- [x] Fusion quality validated

**Status**: Ready for perception evaluation (Stage 5)

### Priority 2 (Performance Optimization)

- [ ] Optimize PointPillars inference (current: 22.1ms, target: < 18ms)
- [ ] Consider multi-scale inference for distant pedestrians
- [ ] Implement early exit for low-confidence detections
- [ ] Profile memory allocation patterns

### Priority 3 (Quality Improvements)

- [ ] Add camera-LiDAR temporal alignment refinement
- [ ] Implement adaptive confidence based on weather
- [ ] Add occlusion reasoning for dense traffic
- [ ] Consider transformer-based association

---

## Next Steps

1. **Proceed to perception evaluation** using `adas-perception-eval` tool
2. **Compare against ground truth** annotations for precision/recall analysis
3. **Compute MOTA/MOTP** tracking metrics
4. **Validate against ODD requirements** from Stage 1

---

## Pipeline Tool Metadata

| Tool | Version | Standard | Status |
|------|---------|----------|--------|
| adas-perception-pipeline | 3.2.0 | ISO 21448 | Success |

- **Pipeline Duration**: 74.3ms (P50), 89.1ms (P99)
- **Input Files**: fusion_config.yaml, camera_intrinsics.yaml, lidar_extrinsics.yaml
- **Output Files**: perception_output.yaml, tracks.json, lanes.json, free_space.json
- **Objects Tracked**: 47 (38 vehicles, 5 pedestrians, 2 cyclists, 2 other)
- **Exit Code**: 0 (Success)

---

## References

- ISO 21448:2022 - Safety of the Intended Functionality (SOTIF)
- ISO 8855:2013 - Road vehicles - Vehicle dynamics and road-holding ability - Vocabulary
- KITTI Vision Benchmark Suite - http://www.cvlibs.net/datasets/kitti/
- nuScenes Dataset - https://www.nuscenes.org/
- Apollo Perception Stack - https://github.com/ApolloAuto/apollo

---

**Generated by automotive-copilot-agents v2.1.0**
**Document ID**: PERC-HP-004
**Revision**: 1.0
**Date**: 2026-03-24
