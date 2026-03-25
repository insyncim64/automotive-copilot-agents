# Skill: Multi-Sensor Fusion for ADAS

## Standards Compliance
- ISO 26262 ASIL C/D
- ISO 21448 SOTIF
- AUTOSAR 4.4

## Overview

Multi-sensor fusion combines measurements from camera, radar, LiDAR, and ultrasonic sensors to achieve robust object detection and tracking beyond the capability of any single sensor.

## Fusion Architectures

### 1. Early Fusion (Feature-Level)

Combine raw or pre-processed data before detection:

```
Camera Image + LiDAR Point Cloud → Feature Extraction → Detection → Tracking
```

**Pros:** Maximum information sharing, better small object detection
**Cons:** High bandwidth, complex synchronization, computationally intensive

**Use Cases:**
- Camera-LiDAR深度融合 for 3D detection
- Radar heatmap projection to image plane

### 2. Late Fusion (Track-Level)

Combine independent detections/tracks from each sensor:

```
Camera → Detection ─┬
Radar → Detection ──┼→ Fusion → Tracking
LiDAR → Detection ─┘
```

**Pros:** Modular, fault-tolerant, lower bandwidth
**Cons:** May miss cross-sensor correlations

**Use Cases:**
- Production L2/L3 systems
- Systems requiring graceful degradation

### 3. Central Fusion (Measurement-Level)

Combine raw measurements in a common state space:

```
Camera Measurements ─┬
Radar Measurements ──┼→ Central Tracker → Object List
LiDAR Measurements ──┘
```

**Pros:** Optimal estimation, handles sensor disagreements
**Cons:** Requires accurate sensor calibration, complex association

## Kalman Filtering

### Extended Kalman Filter (EKF)

For non-linear state transition or measurement models:

```cpp
/**
 * EKF State Vector for Object Tracking
 * State: [x, y, z, vx, vy, vz, ax, ay, az]
 */
struct EKFState {
    Eigen::Vector9f state;          // Position, velocity, acceleration
    Eigen::Matrix9f covariance;     // Uncertainty
    Eigen::Matrix9f process_noise;  // Model uncertainty
};

class MultiSensorEKF {
public:
    /**
     * Prediction step with constant acceleration model
     * @param dt Time step in seconds
     * @safety Validates dt bounds before computation
     */
    void predict(float dt) {
        // Validate time step
        if (dt <= 0.0f || dt > 0.5f) {
            Dem_ReportErrorStatus(DTC_EKF_INVALID_DT);
            return;
        }

        // State transition matrix for constant acceleration
        Eigen::Matrix9f F;
        F.setIdentity();
        F(0,3) = dt;  F(0,6) = 0.5f * dt * dt;  // x += vx*dt + 0.5*ax*dt^2
        F(1,4) = dt;  F(1,7) = 0.5f * dt * dt;  // y += vy*dt + 0.5*ay*dt^2
        F(2,5) = dt;  F(2,8) = 0.5f * dt * dt;  // z += vz*dt + 0.5*az*dt^2
        F(3,6) = dt;  // vx += ax*dt
        F(4,7) = dt;  // vy += ay*dt
        F(5,8) = dt;  // vz += az*dt

        // Predict state
        state_ = F * state_;

        // Predict covariance
        covariance_ = F * covariance_ * F.transpose() + process_noise_;
    }

    /**
     * Update with camera bearing measurement
     * @param azimuth Horizontal angle in radians
     * @param elevation Vertical angle in radians
     * @return Innovation norm (for association)
     */
    float update_camera(float azimuth, float elevation) {
        // Measurement function: h(x) = [atan2(y,x), atan2(z,sqrt(x^2+y^2))]
        const float range_xy = std::sqrt(state_(0)*state_(0) + state_(1)*state_(1));
        const float predicted_azimuth = std::atan2(state_(1), state_(0));
        const float predicted_elevation = std::atan2(state_(2), range_xy);

        // Innovation (measurement residual)
        Eigen::Vector2f innovation;
        innovation << normalize_angle(azimuth - predicted_azimuth),
                      normalize_angle(elevation - predicted_elevation);

        // Jacobian of measurement function
        Eigen::Matrix29f H = compute_camera_jacobian(state_);

        // Innovation covariance
        Eigen::Matrix2f S = H * covariance_ * H.transpose() + measurement_noise_camera_;

        // Kalman gain
        Eigen::Matrix92f K = covariance_ * H.transpose() * S.inverse();

        // Validate innovation (3-sigma gate)
        const float innovation_norm = innovation.norm();
        if (innovation_norm > MAX_INNOVATION_THRESHOLD) {
            Dem_ReportErrorStatus(DTC_EKF_CAMERA_INNOVATION_LARGE);
            return innovation_norm;
        }

        // Update state and covariance
        state_ += K * innovation;
        covariance_ = (Eigen::Matrix9f::Identity() - K * H) * covariance_;

        return innovation_norm;
    }

    /**
     * Update with radar range+Doppler measurement
     * @param range Range in meters
     * @param range_rate Radial velocity in m/s
     */
    float update_radar(float range, float range_rate) {
        const float r = std::sqrt(state_(0)*state_(0) + state_(1)*state_(1) + state_(2)*state_(2));
        const float r_dot = (state_(0)*state_(3) + state_(1)*state_(4) + state_(2)*state_(5)) / r;

        Eigen::Vector2f innovation;
        innovation << range - r, range_rate - r_dot;

        Eigen::Matrix29f H = compute_radar_jacobian(state_);
        Eigen::Matrix2f S = H * covariance_ * H.transpose() + measurement_noise_radar_;
        Eigen::Matrix29f K = covariance_ * H.transpose() * S.inverse();

        state_ += K * innovation;
        covariance_ = (Eigen::Matrix9f::Identity() - K * H) * covariance_;

        return innovation.norm();
    }

    /**
     * Update with LiDAR position measurement
     * @param position 3D position in sensor frame
     */
    float update_lidar(const Eigen::Vector3f& position) {
        Eigen::Vector3f innovation = position - state_.head<3>();
        Eigen::Matrix39f H;
        H.leftCols<3>().setIdentity();
        H.rightCols<6>().setZero();

        Eigen::Matrix3f S = H * covariance_ * H.transpose() + measurement_noise_lidar_;
        Eigen::Matrix93f K = covariance_ * H.transpose() * S.inverse();

        state_ += K * innovation;
        covariance_ = (Eigen::Matrix9f::Identity() - K * H) * covariance_;

        return innovation.norm();
    }

private:
    EKFState state_;
    Eigen::Matrix3f measurement_noise_camera_;
    Eigen::Matrix2f measurement_noise_radar_;
    Eigen::Matrix3f measurement_noise_lidar_;

    static constexpr float MAX_INNOVATION_THRESHOLD = 3.0f;  // 3-sigma gate
};
```

### Unscented Kalman Filter (UKF)

Better handling of highly non-linear models:

```cpp
/**
 * UKF Sigma Point Generation
 * For 9-dimensional state vector
 */
struct UKFParameters {
    static constexpr int STATE_DIM = 9;
    static constexpr int SIGMA_COUNT = 2 * STATE_DIM + 1;  // 19 sigma points

    float alpha = 0.001f;    // Spread of sigma points
    float beta = 2.0f;       // Prior knowledge (2 for Gaussian)
    float kappa = 0.0f;      // Secondary scaling
    float lambda;            // Combined scaling parameter

    UKFParameters() : lambda(alpha * alpha * (STATE_DIM + kappa) - STATE_DIM) {}

    /**
     * Compute weights for mean and covariance
     */
    void compute_weights(Eigen::VectorXf& weights_mean, Eigen::VectorXf& weights_cov) {
        weights_mean.resize(SIGMA_COUNT);
        weights_cov.resize(SIGMA_COUNT);

        weights_mean(0) = lambda / (STATE_DIM + lambda);
        weights_cov(0) = weights_mean(0) + (1.0f - alpha * alpha + beta);
        weights_mean(0) = weights_cov(0);  // Often set equal

        for (int i = 1; i < SIGMA_COUNT; i++) {
            weights_mean(i) = 1.0f / (2.0f * (STATE_DIM + lambda));
            weights_cov(i) = weights_mean(i);
        }
    }
};
```

### Information Filter (Inverse Covariance)

Preferred for multi-sensor fusion with independent measurements:

```cpp
/**
 * Information Filter - works with inverse covariance (information matrix)
 * Advantage: Fusion is additive for independent measurements
 */
class InformationFilter {
public:
    void update(const Eigen::MatrixXf& H, const Eigen::VectorXf& z,
                const Eigen::MatrixXf& R) {
        // Information matrix contribution from this measurement
        Eigen::MatrixXf I_state = H.transpose() * R.inverse() * H;
        Eigen::VectorXf i_state = H.transpose() * R.inverse() * z;

        // Additive update (no matrix inversion needed!)
        information_matrix_ += I_state;
        information_vector_ += i_state;
    }

    /**
     * Recover state estimate (requires inversion)
     * Only needed when output is required
     */
    Eigen::VectorXf get_state() const {
        return information_matrix_.ldlt().solve(information_vector_);
    }

    Eigen::MatrixXf get_covariance() const {
        return information_matrix_.inverse();
    }

private:
    Eigen::MatrixXf information_matrix_;  // P^(-1)
    Eigen::VectorXf information_vector_;  // P^(-1) * x
};
```

## Multi-Target Tracking

### Joint Probabilistic Data Association (JPDA)

For moderate clutter environments:

```cpp
/**
 * JPDA Association Probabilities
 * Computes probability that each measurement originated from the track
 */
struct JPDAAssociation {
    int track_id;
    std::vector<int> measurement_indices;
    std::vector<float> association_probabilities;  // Beta_j values

    /**
     * Compute association probabilities using Gaussian likelihood
     * @param innovations Innovation vectors for each measurement
     * @param S Innovation covariance matrix
     * @param Pd Detection probability
     * @param lambda Clutter density (measurements per unit volume)
     */
    void compute_probabilities(const std::vector<Eigen::VectorXf>& innovations,
                                const Eigen::MatrixXf& S,
                                float Pd, float lambda) {
        const int m = innovations.size();

        // Compute likelihoods for each measurement
        std::vector<float> likelihoods(m + 1);  // +1 for no detection
        likelihoods[0] = 1.0f - Pd;  // Null hypothesis

        for (int j = 0; j < m; j++) {
            // Gaussian likelihood
            const float exponent = -0.5f * innovations[j].dot(S.ldlt().solve(innovations[j]));
            likelihoods[j + 1] = Pd * std::exp(exponent) / std::sqrt(std::pow(2.0f * M_PI, S.rows()) * S.determinant());
        }

        // Normalize to get probabilities
        const float sum = std::accumulate(likelihoods.begin(), likelihoods.end(), 0.0f);
        for (int j = 0; j <= m; j++) {
            association_probabilities[j] = likelihoods[j] / sum;
        }
    }

    /**
     * Compute fused state estimate weighted by association probabilities
     */
    Eigen::VectorXf compute_fused_state(const std::vector<Eigen::VectorXf>& predicted_states) {
        Eigen::VectorXf fused_state = Eigen::VectorXf::Zero(predicted_states[0].size());

        for (size_t j = 0; j < predicted_states.size(); j++) {
            fused_state += association_probabilities[j] * predicted_states[j];
        }

        return fused_state;
    }
};
```

### Multiple Hypothesis Tracking (MHT)

For high-clutter, high-ambiguity scenarios:

```cpp
/**
 * MHT Hypothesis Tree
 * Maintains multiple association hypotheses over time
 */
struct MHTHypothesis {
    int hypothesis_id;
    int parent_id;                    // Parent hypothesis (for N-scan pruning)
    float log_likelihood;             // Cumulative log-likelihood
    std::vector<int> associations;    // Measurement associations at each time step

    /**
     * Update hypothesis with new association
     */
    void extend(int new_measurement_id, float measurement_likelihood) {
        associations.push_back(new_measurement_id);
        log_likelihood += std::log(measurement_likelihood + 1e-10f);
    }

    /**
     * Compute posterior probability given all hypotheses
     */
    float compute_posterior(const std::vector<MHTHypothesis>& all_hypotheses) const {
        float max_log_likelihood = all_hypotheses[0].log_likelihood;
        for (const auto& h : all_hypotheses) {
            max_log_likelihood = std::max(max_log_likelihood, h.log_likelihood);
        }

        // Numerically stable softmax
        float sum_exp = 0.0f;
        for (const auto& h : all_hypotheses) {
            sum_exp += std::exp(h.log_likelihood - max_log_likelihood);
        }

        return std::exp(log_likelihood - max_log_likelihood) / sum_exp;
    }
};

class MultipleHypothesisTracker {
public:
    /**
     * N-scan pruning - keep only top K hypotheses after N frames
     */
    void prune_hypotheses(int n_scan, int max_hypotheses) {
        if (hypotheses_.size() <= static_cast<size_t>(max_hypotheses)) {
            return;
        }

        // Sort by log-likelihood
        std::sort(hypotheses_.begin(), hypotheses_.end(),
                  [](const MHTHypothesis& a, const MHTHypothesis& b) {
                      return a.log_likelihood > b.log_likelihood;
                  });

        // Keep top K
        hypotheses_.resize(max_hypotheses);

        // N-scan back pruning: remove hypotheses with poor ancestors
        if (n_scan > 0 && hypotheses_.size() > 1) {
            perform_nscan_pruning(n_scan);
        }
    }

private:
    std::vector<MHTHypothesis> hypotheses_;

    void perform_nscan_pruning(int n_scan) {
        // Group hypotheses by ancestor N frames back
        std::map<int, std::vector<size_t>> ancestor_groups;
        for (size_t i = 0; i < hypotheses_.size(); i++) {
            int ancestor_id = get_ancestor_id(hypotheses_[i], n_scan);
            ancestor_groups[ancestor_id].push_back(i);
        }

        // Keep only best hypothesis per ancestor group
        std::vector<size_t> keep_indices;
        for (const auto& [ancestor, indices] : ancestor_groups) {
            const size_t best_idx = indices[get_best_hypothesis(indices)];
            keep_indices.push_back(best_idx);
        }

        // Rebuild hypothesis list
        std::vector<MHTHypothesis> pruned;
        for (size_t idx : keep_indices) {
            pruned.push_back(hypotheses_[idx]);
        }
        hypotheses_ = std::move(pruned);
    }
};
```

## Sensor Extrinsic Calibration

### Target-Based Calibration

Using known calibration patterns:

```yaml
# Calibration configuration
calibration_config:
  checkerboard:
    rows: 9
    columns: 6
    square_size_mm: 30.0

  lidar_reflectors:
    count: 4
    positions_file: "reflector_positions.yaml"

  procedure:
    1_capture: "Collect synchronized camera images and LiDAR scans"
    2_detect: "Detect checkerboard corners and reflector centroids"
    3_optimize: "Minimize reprojection + point-to-plane error"
    4_validate: "Verify reprojection error < 0.5 pixels"
```

### Target-Less Calibration

Using natural scene features:

```cpp
/**
 * Online Calibration Optimization
 * Minimizes geometric consistency error without calibration target
 */
class OnlineCalibrationOptimizer {
public:
    /**
     * Cost function for camera-LiDAR calibration
     * Minimizes distance between LiDAR points and camera edges
     */
    float compute_edge_alignment_cost(
        const Eigen::Matrix4f& extrinsic_transform,
        const PointCloud& lidar_points,
        const EdgeMap& camera_edges) {

        float total_cost = 0.0f;
        int inlier_count = 0;

        for (const auto& point : lidar_points) {
            // Transform point to camera frame
            Eigen::Vector4f point_camera = extrinsic_transform * point.homogeneous();
            if (point_camera(2) <= 0.0f) continue;  // Behind camera

            // Project to image
            const float u = fx_ * point_camera(0) / point_camera(2) + cx_;
            const float v = fy_ * point_camera(1) / point_camera(2) + cy_;

            if (!is_in_image(u, v)) continue;

            // Distance to nearest edge
            const float edge_distance = camera_edges.distance_to_edge(u, v);
            if (edge_distance < edge_threshold_) {
                total_cost += edge_distance * edge_distance;
                inlier_count++;
            }
        }

        return (inlier_count > 0) ? total_cost / inlier_count : 1e6f;
    }

    /**
     * Optimize extrinsic parameters using Levenberg-Marquardt
     */
    Eigen::Matrix4f optimize(const Eigen::Matrix4f& initial_guess) {
        Eigen::Matrix4f result = initial_guess;

        for (int iteration = 0; iteration < max_iterations_; iteration++) {
            // Compute Jacobian numerically
            Eigen::Matrix<float, 6, 1> gradient;
            Eigen::Matrix<float, 6, 6> jacobian;
            compute_numerical_derivative(result, gradient, jacobian);

            // Levenberg-Marquardt update
            Eigen::Matrix<float, 6, 6> H = jacobian.transpose() * jacobian;
            H.diagonal().array() += lambda_;  // Damping

            Eigen::Matrix<float, 6, 1> delta = H.ldlt().solve(-gradient);

            // Apply update (SE(3) exponential map)
            result = result * se3_exp(delta);

            // Check convergence
            if (delta.norm() < convergence_threshold_) {
                break;
            }

            // Adjust damping
            lambda_ *= (gradient.norm() < prev_gradient_norm_) ? 0.5f : 2.0f;
            prev_gradient_norm_ = gradient.norm();
        }

        return result;
    }
};
```

## Performance Benchmarks

| Metric | Early Fusion | Late Fusion | Central Fusion |
|--------|-------------|-------------|----------------|
| Detection mAP | 0.92 | 0.87 | 0.89 |
| Tracking MOTA | 0.85 | 0.80 | 0.83 |
| Latency (ms) | 80-120 | 40-60 | 50-80 |
| Robustness (occlusion) | High | Medium | High |
| Computational Cost | Very High | Low | Medium |
| Bandwidth | Very High | Low | Medium |

## Safety Mechanisms

### Plausibility Checks

```cpp
/**
 * Cross-sensor plausibility validation
 * Detects and isolates faulty sensors
 */
struct SensorFusionSafetyMonitor {
    static bool validate_fusion_output(const FusedObjectList& fused,
                                        const ObjectList& camera,
                                        const ObjectList& radar,
                                        const ObjectList& lidar) {
        // Check 1: Fused objects must have support from at least 2 sensors
        for (const auto& obj : fused.objects) {
            int sensor_support = 0;
            if (has_camera_support(obj, camera)) sensor_support++;
            if (has_radar_support(obj, radar)) sensor_support++;
            if (has_lidar_support(obj, lidar)) sensor_support++;

            if (sensor_support < 2) {
                Dem_ReportErrorStatus(DTC_FUSION_INSUFFICIENT_SENSOR_SUPPORT);
                return false;
            }
        }

        // Check 2: Velocity plausibility (physical limits)
        for (const auto& obj : fused.objects) {
            if (obj.velocity.norm() > MAX_OBJECT_SPEED_MPS) {
                Dem_ReportErrorStatus(DTC_FUSION_IMPLAUSIBLE_VELOCITY);
                return false;
            }
        }

        // Check 3: Temporal consistency
        if (!check_temporal_consistency(fused, previous_fused_)) {
            Dem_ReportErrorStatus(DTC_FUSION_TEMPORAL_INCONSISTENCY);
            return false;
        }

        return true;
    }

    /**
     * Sensor health monitoring
     */
    static SensorHealthStatus monitor_sensor_health(
        const SensorMeasurements& measurements,
        float time_window_s = 10.0f) {

        SensorHealthStatus health;

        // Camera health: Check for saturation, motion blur, occlusion
        health.camera_healthy = check_camera_health(measurements.camera);

        // Radar health: Check for multipath, interference, noise floor
        health.radar_healthy = check_radar_health(measurements.radar);

        // LiDAR health: Check for attenuation, saturation, missing points
        health.lidar_healthy = check_lidar_health(measurements.lidar);

        // Cross-sensor agreement
        health.agreement_score = compute_cross_sensor_agreement(measurements);

        return health;
    }
};
```

## References

- @knowledge/standards/iso26262/2-conceptual.md - ASIL decomposition for fusion systems
- @knowledge/standards/iso21448/1-overview.md - SOTIF triggering conditions in fusion
- @context/skills/adas/object-tracking.md - Tracking algorithm details
- @context/skills/adas/calibration.md - Calibration procedures

## Related Context Files

- @context/skills/adas/camera-processing.md - Camera detection inputs
- @context/skills/adas/radar-processing.md - Radar measurement models
- @context/skills/adas/lidar-processing.md - LiDAR point cloud processing
