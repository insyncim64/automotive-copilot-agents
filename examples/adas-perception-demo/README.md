# ADAS Perception Pipeline Demo

This example project demonstrates the ADAS perception validation workflow for an automotive camera-based object detection system.

## Overview

This demo showcases:
- Multi-sensor fusion (camera + radar)
- Real-time object detection and tracking
- ASIL-B safety classification
- End-to-end validation from dataset to vehicle integration

## Project Structure

```
adas-perception-demo/
├── README.md
├── config/
│   ├── perception-config.yaml      # Perception pipeline configuration
│   ├── sensor-calibration.yaml     # Camera/radar extrinsics
│   └── kpis.yaml                   # Performance thresholds
├── models/
│   └── placeholder.txt             # Place your trained model here
├── data/
│   ├── raw/                        # Raw sensor data
│   └── annotations/                # Ground truth labels
├── scenarios/
│   ├── nominal/                    # Normal driving scenarios
│   ├── weather/                    # Adverse weather scenarios
│   └── rare-objects/               # Edge case scenarios
└── scripts/
    ├── run-demo.sh                 # Demo execution script
    └── visualize-results.py        # Results visualization
```

## Prerequisites

1. **Hardware Requirements**:
   - GPU with CUDA support (for offline evaluation)
   - Self-hosted runner with ECU interface (for vehicle integration)

2. **Software Requirements**:
   - Python 3.10+
   - CUDA 11.7+ (for GPU runner)
   - Docker (for simulation testing)

3. **GitHub Actions Setup**:
   - Configure `gpu-latest` runner for offline evaluation
   - Configure `self-hosted` runner for vehicle integration
   - Set up `vehicle-test-bench` environment

## Configuration

### perception-config.yaml

```yaml
pipeline:
  input_sources:
    - type: camera
      name: front_camera
      resolution: [1920, 1080]
      fps: 30
    - type: radar
      name: front_radar
      max_range_m: 200
      update_rate_hz: 20

  detection:
    model: models/perception/latest
    confidence_threshold: 0.5
    iou_threshold: 0.45
    max_detections: 100

  tracking:
    algorithm: deep_sort
    max_age: 30
    min_confidence: 0.3

  safety:
    asil_level: ASIL-B
    latency_budget_ms: 100
    redundancy_check: true
```

### kpis.yaml

```yaml
detection_metrics:
  min_precision: 0.85
  min_recall: 0.80
  min_f1_score: 0.82

tracking_metrics:
  min_mota: 0.75
  min_motp: 0.80
  max_id_switches: 10

latency:
  max_end_to_end_ms: 100
  max_perception_ms: 50
  max_fusion_ms: 20

robustness:
  min_accuracy_rain: 0.70
  min_accuracy_fog: 0.65
  min_accuracy_night: 0.75
```

## Running the Demo

### Local Testing

```bash
# Run perception pipeline on sample data
python scripts/run-demo.sh --mode local

# Visualize detection results
python scripts/visualize-results.py --input results/offline/
```

### GitHub Actions Workflow

The demo uses the `adas-perception-validation.yaml` workflow:

```yaml
# Trigger manually via GitHub UI
# Go to Actions > ADAS Perception Validation > Run workflow

# Or trigger via git push:
git add config/ data/ models/
git commit -m "Update perception model to v2.4.0"
git push origin develop
```

### Workflow Execution

The workflow executes 5 stages:

1. **Dataset Preparation** (5-10 min)
   - Validates dataset coverage
   - Checks annotation quality (>90% inter-annotator agreement)
   - Generates dataset statistics

2. **Offline Evaluation** (15-30 min, GPU)
   - Runs inference on test dataset
   - Computes detection metrics (precision, recall, F1)
   - Computes tracking metrics (MOTA, MOTP)
   - Compares against baseline

3. **Simulation Testing** (20-40 min)
   - Nominal scenarios (highway, urban, parking)
   - Adverse weather (rain, fog, snow)
   - Rare objects (construction zones, animals)
   - Latency validation (<100ms)

4. **Vehicle Integration** (1-2 hours, self-hosted)
   - ECU flashing
   - Test track scenarios
   - Urban road test
   - Resource monitoring

5. **Release Approval** (5 min)
   - Compiles validation summary
   - Checks open issues
   - Generates release recommendation

## Expected Results

After successful execution, you'll find:

```
results/
├── offline/
│   ├── metrics-detection.json    # Precision: 0.87, Recall: 0.84
│   ├── metrics-tracking.json     # MOTA: 0.78, MOTP: 0.82
│   └── regression-report.md      # No regression detected
├── simulation/
│   ├── nominal/                  # All scenarios passed
│   ├── weather/                  # Rain: PASS, Fog: PASS
│   └── rare/                     # 95% success rate
├── vehicle/
│   ├── test-track/               # 50/50 scenarios passed
│   ├── urban/                    # 48/50 scenarios passed
│   └── resource-usage.json       # CPU: 65%, Memory: 2.1GB
└── validation-summary.md         # Overall: READY FOR RELEASE
```

## Using MCP Tools

This demo leverages the following MCP tools:

```bash
# Run perception pipeline
adas:perception-pipeline --config config/perception-config.yaml

# Evaluate perception performance
adas:perception-eval --results results/offline/

# Calibrate sensors
adas:sensor-calibration --camera front_camera --radar front_radar

# Generate test scenarios
adas:scenario-generate --type adverse-weather --count 10
```

## Troubleshooting

### Common Issues

1. **GPU runner unavailable**
   - Ensure `gpu-latest` runner is registered
   - Check CUDA driver version compatibility

2. **Vehicle integration fails**
   - Verify `self-hosted` runner connectivity
   - Check ECU target configuration in environment variables

3. **Latency exceeds budget**
   - Review model complexity
   - Check sensor synchronization
   - Optimize fusion algorithm

### Getting Help

- Review workflow logs in GitHub Actions
- Check `validation-summary.md` for detailed error messages
- Consult ISO 26262 compliance documentation for safety requirements

## Next Steps

After successful demo execution:

1. Review `validation-summary.md` for release readiness
2. Address any open issues from the validation report
3. Proceed to production deployment workflow
4. Document lessons learned in project wiki

## References

- [ADAS Perception Validation Workflow](../../.github/workflows/adas-perception-validation.yaml)
- [ISO 26262 Functional Safety](../../knowledge-base/standards/iso-26262/)
- [SOTIF (ISO 21448)](../../knowledge-base/standards/iso-21448/)
