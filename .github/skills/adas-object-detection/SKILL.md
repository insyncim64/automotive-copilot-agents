---
name: adas-object-detection
description: "Use when: Skill: Object Detection for ADAS topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: Object Detection for ADAS

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/adas/object-detection.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate
- User asks about object detection algorithms (2D/3D)
- User requests camera, radar, or LiDAR-based detection implementation
- User needs guidance on CNN architectures, anchor boxes, or NMS
- User is designing perception stacks for ADAS/AD

## Standards Compliance
- ISO 26262 ASIL B/D (depending on function)
- ASPICE Level 3
- AUTOSAR 4.4 Classic/Adaptive
- ISO 21434 (Cybersecurity)
- ISO 21448 (SOTIF) - limitations of ML-based perception

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Input resolution | 512x512 to 1920x1200 | pixels |
| Inference latency | < 30 (ASIL B), < 10 (ASIL D) | ms |
| Detection classes | 8-20 (vehicle, pedestrian, cyclist, etc.) | categories |
| NMS IoU threshold | 0.3-0.6 | intersection over union |
| Confidence threshold | 0.3-0.7 | probability |
| Max detections per frame | 50-200 | objects |

## Detection Architectures

### Camera-Based (2D)
| Architecture | Use Case | mAP | Latency |
|-------------|----------|-----|---------|
| YOLOv5/v8 | Real-time detection | 50-55% | < 10 ms |
| Faster R-CNN | High accuracy | 60-65% | 50-100 ms |
| EfficientDet | Edge deployment | 55-60% | 20-40 ms |
| CenterNet | Anchor-free | 55-58% | 15-25 ms |

### LiDAR-Based (3D)
| Architecture | Use Case | mAP | Latency |
|-------------|----------|-----|---------|
| PointPillars | Production ADAS | 65-70% | 20-30 ms |
| SECOND | High accuracy | 70-75% | 50-80 ms |
| CenterFusion | Camera-LiDAR fusion | 72-78% | 40-60 ms |
| VoxelNet | Voxel-based | 68-72% | 60-100 ms |

### Radar-Based (4D Imaging)
- Range-Doppler processing
- Elevation capability (4D radar)
- Point cloud generation
- Fusion with camera/LiDAR recommended

## Core Competencies

### Data Preprocessing
```
Camera:
  - Lens undistortion (Brown-Conrady model)
  - Color space conversion (RGB -> YUV/HSV)
  - Normalization (mean/std per channel)
  - Data augmentation (Mosaic, MixUp for training)

LiDAR:
  - Ground plane removal (RANSAC)
  - Voxelization (voxel size: 0.1-0.2m)
  - Point cloud normalization
  - ROI filtering (0-150m range typical)

Radar:
  - CFAR (Constant False Alarm Rate) detection
  - Clustering (DBSCAN)
  - Doppler velocity de-aliasing
```

### Anchor Box Design
```
K-means clustering for anchor box optimization:
- Number of anchors: 9-15 typical
- Scale ranges: [8, 16, 32, 64, 128] pixels
- Aspect ratios: [0.5, 1.0, 2.0] for 2D
- 3D anchors: include orientation (yaw)

Example (KITTI dataset):
  anchors = [
    [0.6, 1.3, 0.9],    # pedestrian
    [0.8, 1.8, 0.7],    # cyclist
    [1.5, 3.5, 1.5],    # car
    [2.5, 8.0, 3.0],    # truck/bus
  ]  # (width, length, height) in meters
```

### Non-Maximum Suppression (NMS)
```python
def nms(boxes, scores, iou_threshold=0.5):
    """
    Standard NMS for removing duplicate detections.

    Args:
        boxes: Nx4 array [x1, y1, x2, y2]
        scores: N array of confidence scores
        iou_threshold: IoU above which to suppress

    Returns:
        indices: Keep indices after NMS
    """
    x1, y1, x2, y2 = boxes.T
    areas = (x2 - x1) * (y2 - y1)
    order = scores.argsort()[::-1]

    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(i)

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter)

        order = order[1:][iou < iou_threshold]

    return keep
```

### Post-Processing for ADAS
```
Distance Estimation (monocular camera):
  distance_m = (focal_length_px * object_height_m) / bbox_height_px

Bearing Angle:
  bearing_rad = (center_x_px - principal_point_x) / focal_length_px

Velocity Estimation (multi-frame):
  velocity_ms = (position_t2 - position_t1) / delta_t

Time-to-Collision (TTC):
  ttc_s = distance_m / relative_velocity_ms
```

## SOTIF Considerations (ISO 21448)

### Known Triggering Conditions
| Condition | Impact | Mitigation |
|-----------|--------|------------|
| Low light (< 1 lux) | Reduced detection range | IR illuminator, radar fusion |
| Direct sunlight/glare | Saturated pixels, missed detections | Sun position awareness, HDR |
| Heavy rain/snow | Occlusion, false positives | Radar-primary mode, temporal filtering |
| Dark clothing at night | Pedestrian detection failure | IR camera, reduced speed |
| Construction zones | Unexpected objects | ODD restriction, driver monitoring |
| Adversarial patterns | Intentional misclassification | Multi-sensor fusion, anomaly detection |

### Performance Degradation Awareness
```c
typedef struct {
    float visibility_score;      /* 0.0-1.0 from image statistics */
    float lighting_quality;      /* 0.0-1.0 from luminance histogram */
    float weather_confidence;    /* 0.0-1.0 from droplet detection */
    float overall_capability;    /* Combined metric */
} PerceptionCapability_t;

/* Adapt ADAS behavior based on capability */
if (capability.overall_capability < 0.5f) {
    /* Request driver takeover or reduce speed */
    request_driver_intervention();
}
```

## Approach

1. **Define use case and ODD**
   - Target object classes (vehicle, pedestrian, cyclist, debris)
   - Operating conditions (day/night, weather, road types)
   - Performance requirements (detection range, latency)

2. **Select architecture** based on constraints
   - Embedded (Jetson, Xavier): PointPillars, YOLOv5s
   - Desktop training: Larger models (EfficientDet-D7, Swin Transformer)
   - ASIL requirements: Redundant architectures, diverse algorithms

3. **Training pipeline**
   - Dataset selection (KITTI, nuScenes, Waymo, internal data)
   - Annotation quality control (IoU > 0.7 ground truth)
   - Domain adaptation (synthetic -> real, day -> night)

4. **Validation** per ISO 26262
   - Scenario-based testing (Euro NCAP, C-NCAP protocols)
   - Corner case coverage (occlusion, truncation, rare objects)
   - Back-to-back testing (model vs. deployed code)

## Deliverables

- Trained model weights (ONNX/TensorRT format)
- Inference code with optimization (FP16/INT8 quantization)
- Test report with metrics (mAP, precision-recall, confusion matrix)
- SOTIF documentation (known limitations, triggering conditions)

## Related Context
- @context/skills/safety/iso-26262-overview.md
- @context/skills/safety/sotif-development-rules.md
- @context/skills/adas/sensor-fusion.md
- @context/skills/adas/perception-pipeline.md
- @context/skills/ai-ml/neural-network-validation.md
- @context/skills/security/adversarial-ml-protection.md

## Tools Required
- PyTorch/TensorFlow (model training)
- TensorRT/OpenVINO (inference optimization)
- Labelbox/CVAT (annotation tools)
- MLflow/Weights & Biases (experiment tracking)
- Vector CANoe (HIL validation)