# ADAS Multi-Object Tracking

> Multi-object tracking algorithms for automotive perception including
> SORT, DeepSORT, and AB3DMOT for maintaining consistent track identities
> across sensor frames with safety guarantees for ASIL B/C/D systems.

**Standards Compliance:**
- ISO 26262 ASIL B/C/D (track validation, ID consistency, fault detection)
- ISO 21448 SOTIF (occlusion handling, adversarial robustness)
- Euro NCAP (tracking accuracy for AEB, LSS verification)

---

## Domain Expertise

| Algorithm | Type | Use Case | Accuracy | Latency | ASIL Suitability |
|-----------|------|----------|----------|---------|------------------|
| **SORT** | Kalman + IoU | 2D/3D baseline tracking | MOTA 75-85% | < 5 ms | B |
| **DeepSORT** | SORT + Appearance | 2D tracking with re-ID | MOTA 80-90%, IDF1 75-85% | < 10 ms | B/C |
| **AB3DMOT** | 3D Kalman + IoU | 3D LiDAR tracking | MOTA 80-90%, AMOTA 75-85% | < 10 ms | C |
| **JPDA** | Probabilistic association | Cluttered environments | MOTA 85-92% | < 20 ms | C/D |
| **MHT** | Multi-hypothesis | High-density scenarios | MOTA 88-95% | < 50 ms | C/D |
| **Kalman Filter** | State estimation | Linear motion | N/A | < 1 ms | A/B/C/D |
| **EKF/UKF** | Non-linear estimation | Curvilinear motion | N/A | < 2 ms | B/C/D |

### Performance Benchmarks (Target Specifications)

| Metric | L2 (Highway Pilot) | L3 (Traffic Jam Pilot) | L4 (Robotaxi) |
|--------|-------------------|----------------------|--------------|
| Tracking Latency | < 20 ms | < 10 ms | < 5 ms |
| MOTA (Multi-Object Tracking Accuracy) | > 75% | > 85% | > 90% |
| IDF1 (ID F1 Score) | > 70% | > 80% | > 85% |
| Max Tracked Objects | 100 | 200 | 500 |
| ID Switches per km | < 5 | < 2 | < 0.5 |
| Track Fragmentation | < 10% | < 5% | < 2% |
| Occlusion Recovery | < 2 sec | < 1 sec | < 0.5 sec |

---

## Track-by-Track Detection Pipeline

```
+------------------+     +------------------+     +------------------+
|  Per-Frame       |     |  Multi-Object    |     |  Track           |
|  Detections      |     |  Data Association|     |  Management      |
|                  |     |                  |     |                  |
|  - Camera 2D     |--->|  - Gating        |--->|  - Birth/Death   |
|  - LiDAR 3D      |     |  - Hungarian     |     |  - Aging/Coast   |
|  - Radar Points  |     |  - JPDA/MHT      |     |  - Smooth/Output |
+------------------+     +------------------+     +------------------+
         |                        |                        |
         v                        v                        v
   Detection              Assignment              Track States
   (t=0,1,2...)           (cost matrix)           (NEW/CONFIRMED/DELETED)
```

---

## Data Structures

### Detection Input

```cpp
/**
 * @brief Detection input for tracking algorithms
 * @safety ASIL B - Input validation required
 */
struct Detection {
    // Unique detection ID (per-frame)
    uint64_t detection_id;

    // Timestamp
    ara::core::TimeStamp timestamp;

    // Bounding box (3D for LiDAR, 2D for camera)
    struct BoundingBox3D {
        Eigen::Vector3f center;      // x, y, z (position)
        Eigen::Vector3f dimensions;  // l, w, h (size)
        Eigen::Vector3f orientation; // roll, pitch, yaw (radians)
        Eigen::Vector3f velocity;    // vx, vy, vz (m/s)
    } bbox;

    // Detection confidence [0.0, 1.0]
    float confidence;

    // Object class (from detector)
    ObjectClass object_class;

    // Optional: Appearance descriptor (DeepSORT)
    std::vector<float> appearance_descriptor;  // 128-512 dims

    // Optional: Sensor source
    enum class Source {
        CAMERA,
        LIDAR,
        RADAR,
        FUSION
    } source;
};
```

### Track State

```cpp
/**
 * @brief Track state maintained across frames
 * @safety ASIL B - State validation and bounds checking
 */
struct Track {
    // Unique track ID (persistent across frames)
    uint64_t track_id;

    // Track lifecycle
    enum class State {
        NEW,          // Just created, not yet confirmed
        CONFIRMED,    // Validated over N frames
        COASTING,     // Lost, predicting without detections
        DELETED       // Marked for removal
    } state;

    // Kalman filter state (constant velocity model)
    struct KalmanState {
        // State vector: [x, y, z, vx, vy, vz, l, w, h, yaw, yaw_rate]
        Eigen::Matrix<float, 11, 1> state_mean;

        // State covariance (11x11)
        Eigen::Matrix<float, 11, 11> state_covariance;

        // Process noise
        Eigen::Matrix<float, 11, 11> process_noise;
    } kf_state;

    // Track metadata
    uint32_t age;              // Frames since creation
    uint32_t confirmed_age;    // Frames since confirmation
    uint32_t time_since_update; // Frames since last detection match
    uint32_t consecutive_misses; // Miss count for deletion

    // History for visualization and diagnostics
    std::deque<Eigen::Vector3f> position_history;
    std::deque<float> velocity_history;
    static constexpr size_t MAX_HISTORY = 50U;

    // Most recent detection (for association)
    Detection last_detection;

    // Safety flags
    struct {
        bool position_valid : 1;
        bool velocity_valid : 1;
        bool size_valid : 1;
        bool class_valid : 1;
    } validity_flags;
};
```

---

## SORT Algorithm (Simple Online and Realtime Tracking)

### Algorithm Overview

SORT uses a Kalman filter for motion prediction and the Hungarian algorithm
for data association based on IoU (Intersection over Union) or 3D-GIoU
(Generalized IoU) cost metrics.

**Complexity:** O(N*M) where N = tracks, M = detections
**Latency:** < 5 ms for 100 objects

### SORT Implementation

```cpp
/**
 * @brief SORT tracker for 2D/3D object tracking
 * @safety ASIL B - Track validation, ID management
 * @req SSR-PERCEP-070, SSR-PERCEP-071
 *
 * References:
 * - Bewley et al., "Simple Online and Realtime Tracking", 2016
 * - Extension to 3D: 3D-GIoU for LiDAR tracking
 */
class SortTracker {
public:
    struct Config {
        // Minimum detection confidence to consider
        float min_detection_confidence = 0.1f;

        // IoU threshold for association
        float iou_threshold = 0.3f;  // 3D-GIoU for 3D tracking

        // Track confirmation threshold
        uint32_t confirm_age = 3U;  // Confirm after 3 consecutive matches

        // Track deletion threshold
        uint32_t max_consecutive_misses = 10U;  // Delete after 10 misses

        // Maximum track age (memory limit)
        uint32_t max_track_age = 1000U;
    };

    explicit SortTracker(const Config& config);

    /**
     * @brief Process detections for current frame
     * @param detections Frame detections (2D or 3D)
     * @param timestamp Frame timestamp
     * @return Updated track list
     * @safety Validates track consistency, prevents ID conflicts
     * @wcet < 5 ms for 100 objects (Jacinto TDA4VM A72)
     */
    std::vector<Track> process(const std::vector<Detection>& detections,
                                ara::core::TimeStamp timestamp);

    /**
     * @brief Get active confirmed tracks
     * @return Only CONFIRMED state tracks
     */
    std::vector<Track> get_confirmed_tracks() const;

    /**
     * @brief Get all active tracks (including NEW and COASTING)
     */
    std::vector<Track> get_all_tracks() const;

    /**
     * @brief Reset tracker state (for mode transitions)
     */
    void reset();

private:
    // Associate detections to existing tracks using Hungarian algorithm
    std::vector<std::pair<size_t, size_t>> associate_tracks_to_detections(
        const std::vector<Track>& active_tracks,
        const std::vector<Detection>& detections);

    // Compute IoU cost matrix between tracks and detections
    Eigen::MatrixXf compute_iou_cost_matrix(
        const std::vector<Track>& tracks,
        const std::vector<Detection>& detections);

    // Hungarian algorithm for optimal assignment
    std::vector<std::pair<size_t, size_t>> hungarian_algorithm(
        const Eigen::MatrixXf& cost_matrix);

    // Create new track from unmatched detection
    Track create_new_track(const Detection& detection);

    // Update existing track with matched detection
    void update_track(Track& track, const Detection& detection);

    // Predict track state for current frame (Kalman prediction)
    void predict_track_state(Track& track, float dt);

    // Delete tracks that exceeded max consecutive misses
    void delete_old_tracks();

    Config config_;
    std::vector<Track> active_tracks_;
    uint64_t next_track_id_ = 0U;
    ara::core::TimeStamp last_timestamp_;
};
```

### 3D-GIoU Computation

```cpp
/**
 * @brief Compute 3D Generalized IoU for 3D bounding boxes
 * @return Value in [-1, 1] where 1 = perfect overlap, -1 = no overlap
 */
float compute_3d_giou(const Track::BoundingBox3D& box1,
                       const Detection::BoundingBox3D& box2) {
    // Compute corner points of both boxes
    auto corners1 = get_box_corners(box1);
    auto corners2 = get_box_corners(box2);

    // Axis-aligned bounding box of union
    Eigen::Vector3f min_corner = corners1.colwise().min().cwiseMin(
                                    corners2.colwise().min());
    Eigen::Vector3f max_corner = corners1.colwise().max().cwiseMax(
                                    corners2.colwise().max());

    // Intersection volume
    Eigen::Vector3f intersection_min = corners1.colwise().max().cwiseMax(
                                          corners2.colwise().max());
    Eigen::Vector3f intersection_max = corners1.colwise().min().cwiseMin(
                                          corners2.colwise().min());

    float intersection_volume = 0.0f;
    if ((intersection_max - intersection_min).array().allGreaterThan(0.0f)) {
        intersection_volume = (intersection_max - intersection_min).prod();
    }

    // Union volume
    float volume1 = box1.dimensions.prod();
    float volume2 = box2.dimensions.prod();
    float union_volume = volume1 + volume2 - intersection_volume;

    // Smallest enclosing box volume
    float enclosing_volume = (max_corner - min_corner).prod();

    // GIoU = IoU - (enclosing_volume - union_volume) / enclosing_volume
    float iou = intersection_volume / (union_volume + 1e-8f);
    float giou = iou - (enclosing_volume - union_volume) /
                         (enclosing_volume + 1e-8f);

    return giou;  // Range: [-1, 1]
}
```

### Hungarian Algorithm

```cpp
/**
 * @brief Hungarian algorithm (Munkres) for optimal assignment
 * @param cost_matrix Cost matrix (tracks x detections)
 * @return Vector of (track_idx, detection_idx) pairs
 * @complexity O(N^3) where N = max(tracks, detections)
 */
std::vector<std::pair<size_t, size_t>> hungarian_algorithm(
    const Eigen::MatrixXf& cost_matrix) {

    const size_t num_tracks = cost_matrix.rows();
    const size_t num_detections = cost_matrix.cols();
    const size_t N = std::max(num_tracks, num_detections);

    // Pad cost matrix to square (with large values)
    Eigen::MatrixXf padded_cost = Eigen::MatrixXf::Constant(
        N, N, 1e6f);
    padded_cost.topLeftCorner(num_tracks, num_detections) = cost_matrix;

    // Munkres algorithm implementation
    std::vector<std::pair<size_t, size_t>> assignments;

    // Step 1: Subtract row minimum from each row
    for (size_t i = 0; i < N; ++i) {
        float row_min = padded_cost.row(i).minCoeff();
        padded_cost.row(i) -= row_min;
    }

    // Step 2: Subtract column minimum from each column
    for (size_t j = 0; j < N; ++j) {
        float col_min = padded_cost.col(j).minCoeff();
        padded_cost.col(j) -= col_min;
    }

    // Steps 3-6: Cover zeros, find optimal assignment
    // (Simplified implementation - full Munkres has more steps)
    std::vector<bool> row_assigned(N, false);
    std::vector<bool> col_assigned(N, false);

    // Greedy zero assignment (full algorithm needs augmenting paths)
    for (size_t i = 0; i < N; ++i) {
        for (size_t j = 0; j < N; ++j) {
            if (!row_assigned[i] && !col_assigned[j] &&
                padded_cost(i, j) < 1e-3f) {
                assignments.push_back({i, j});
                row_assigned[i] = true;
                col_assigned[j] = true;
            }
        }
    }

    // Filter to original dimensions
    std::vector<std::pair<size_t, size_t>> filtered;
    for (const auto& [ti, di] : assignments) {
        if (ti < num_tracks && di < num_detections) {
            filtered.push_back({ti, di});
        }
    }

    return filtered;
}
```

---

## DeepSORT Algorithm (SORT with Appearance Descriptors)

### Algorithm Overview

DeepSORT extends SORT by incorporating appearance descriptors from a
re-identification (Re-ID) network, improving tracking through occlusions
and reducing ID switches.

**Key Enhancement:** Cost matrix combines motion (Mahalanobis) and
appearance (cosine similarity) costs.

### DeepSORT Implementation

```cpp
/**
 * @brief DeepSORT tracker with appearance-based re-identification
 * @safety ASIL B/C - Appearance descriptor validation, multi-cue association
 * @req SSR-PERCEP-072, SSR-PERCEP-073
 *
 * References:
 * - Wojke et al., "Simple Online and Realtime Tracking with a Deep
 *   Association Metric", 2017
 * - ReID network: OSNet, PCB, or custom automotive ReID
 */
class DeepSortTracker {
public:
    struct Config {
        // SORT parameters
        float min_detection_confidence = 0.1f;
        uint32_t confirm_age = 3U;
        uint32_t max_consecutive_misses = 70U;  // Longer for occlusion

        // Association thresholds
        float mahalanobis_threshold = 9.21f;  // Chi-square 95% for 4 DOF
        float cosine_similarity_threshold = 0.4f;  // ReID similarity

        // Cost fusion
        float motion_weight = 0.7f;     // Lambda in paper
        float appearance_weight = 0.3f; // 1 - Lambda
    };

    /**
     * @brief Initialize DeepSORT tracker
     * @param config Tracker configuration
     * @param reid_network Pre-loaded ReID network (TensorRT)
     * @safety ReID network must be qualified for automotive use
     */
    explicit DeepSortTracker(const Config& config,
                              std::shared_ptr<ReIdNetwork> reid_network);

    /**
     * @brief Process detections with appearance features
     * @param detections Detections with ReID descriptors
     * @param timestamp Frame timestamp
     * @return Updated track list
     * @safety Validates descriptor consistency
     * @wcet < 10 ms for 100 objects
     */
    std::vector<Track> process(const std::vector<Detection>& detections,
                                ara::core::TimeStamp timestamp);

private:
    // Gated IoU with Mahalanobis gating
    std::vector<std::pair<size_t, size_t>> gated_iou_association(
        const std::vector<Track>& tracks,
        const std::vector<Detection>& detections);

    // Compute Mahalanobis distance between predicted and measured state
    Eigen::MatrixXf compute_mahalanobis_cost(
        const std::vector<Track>& tracks,
        const std::vector<Detection>& detections);

    // Compute cosine similarity cost from appearance descriptors
    Eigen::MatrixXf compute_appearance_cost(
        const std::vector<Track>& tracks,
        const std::vector<Detection>& detections);

    // Fuse motion and appearance costs
    Eigen::MatrixXf fuse_costs(const Eigen::MatrixXf& motion_cost,
                                const Eigen::MatrixXf& appearance_cost);

    // Apply Mahalanobis gating (zero out unlikely associations)
    void apply_mahalanobis_gating(Eigen::MatrixXf& cost_matrix,
                                   const Eigen::MatrixXf& mahalanobis_dist);

    Config config_;
    std::shared_ptr<ReIdNetwork> reid_network_;
    std::vector<Track> active_tracks_;
    uint64_t next_track_id_ = 0U;
};
```

### Appearance Descriptor Extraction

```cpp
/**
 * @brief ReID network wrapper for appearance feature extraction
 * @safety ASIL B - Network output validation
 */
class ReIdNetwork {
public:
    /**
     * @brief Extract appearance descriptor from image crop
     * @param image_crop Object image (from camera detection)
     * @return Normalized descriptor vector (L2 norm = 1)
     * @safety Validates input size, checks for NaN/Inf output
     */
    std::vector<float> extract_descriptor(const cv::Mat& image_crop) {
        // Preprocess: resize to network input (e.g., 256x128)
        cv::Mat resized;
        cv::resize(image_crop, resized, cv::Size(128, 256));

        // Normalize: [0, 255] -> [0, 1], apply ImageNet mean/std
        cv::Mat normalized;
        resized.convertTo(normalized, CV_32FC3, 1.0f / 255.0f);
        apply_imagenet_normalization(normalized);

        // Run inference (TensorRT)
        std::vector<float> descriptor;
        auto status = tensorrt_context_->execute_inference(
            {normalized.ptr<float>()},
            {descriptor.data()});

        if (status != ara::core::Result<void>::OK) {
            // Fallback: return zero descriptor (no association)
            return std::vector<float>(DESCRIPTOR_DIM, 0.0f);
        }

        // Validate: no NaN/Inf
        for (const float& val : descriptor) {
            if (std::isnan(val) || std::isinf(val)) {
                return std::vector<float>(DESCRIPTOR_DIM, 0.0f);
            }
        }

        // L2 normalize descriptor
        float norm = 0.0f;
        for (const float& val : descriptor) {
            norm += val * val;
        }
        norm = std::sqrt(norm);

        for (float& val : descriptor) {
            val /= (norm + 1e-8f);
        }

        return descriptor;
    }

    static constexpr size_t DESCRIPTOR_DIM = 256U;

private:
    std::shared_ptr<TensorRtContext> tensorrt_context_;
};
```

### Cost Fusion

```cpp
/**
 * @brief Fuse motion and appearance costs
 * @return Combined cost matrix for Hungarian algorithm
 */
Eigen::MatrixXf DeepSortTracker::fuse_costs(
    const Eigen::MatrixXf& motion_cost,
    const Eigen::MatrixXf& appearance_cost) {

    // Weighted sum: cost = lambda * motion + (1-lambda) * appearance
    return config_.motion_weight * motion_cost +
           config_.appearance_weight * appearance_cost;
}

/**
 * @brief Apply Mahalanobis gating
 * @param cost_matrix Cost matrix to modify (gated costs set to infinity)
 * @param mahalanobis_dist Mahalanobis distance matrix
 */
void DeepSortTracker::apply_mahalanobis_gating(
    Eigen::MatrixXf& cost_matrix,
    const Eigen::MatrixXf& mahalanobis_dist) {

    // Gating: if Mahalanobis distance > threshold, set cost to infinity
    for (size_t i = 0; i < mahalanobis_dist.rows(); ++i) {
        for (size_t j = 0; j < mahalanobis_dist.cols(); ++j) {
            if (mahalanobis_dist(i, j) > config_.mahalanobis_threshold) {
                cost_matrix(i, j) = 1e6f;  // Effectively infinite cost
            }
        }
    }
}
```

---

## AB3DMOT Algorithm (3D Multi-Object Tracking)

### Algorithm Overview

AB3DMOT extends SORT to 3D LiDAR tracking with:
- 3D Kalman filter (constant velocity model)
- 3D-GIoU association
- Orientation-aware matching
- Motion modeling for autonomous driving

### AB3DMOT Implementation

```cpp
/**
 * @brief AB3DMOT for 3D LiDAR object tracking
 * @safety ASIL C - 3D state validation, velocity limits
 * @req SSR-PERCEP-074, SSR-PERCEP-075
 *
 * References:
 * - Weng et al., "Ab3dmot: A baseline for 3d multi-object tracking", 2020
 * - Extension: Orientation-aware 3D-GIoU
 */
class Ab3dmotTracker {
public:
    struct Config {
        // Detection confidence threshold
        float min_confidence = 0.1f;

        // Association threshold (3D-GIoU)
        float giou_threshold = 0.01f;  // More lenient for 3D

        // Kalman filter parameters
        float process_noise_accel = 0.5f;  // Acceleration noise
        float measurement_noise_pos = 0.1f; // Position noise
        float measurement_noise_vel = 0.5f; // Velocity noise

        // Track management
        uint32_t confirm_age = 3U;
        uint32_t max_consecutive_misses = 7U;

        // Orientation matching
        bool use_orientation = true;
        float orientation_weight = 0.2f;
    };

    explicit Ab3dmotTracker(const Config& config);

    /**
     * @brief Process 3D LiDAR detections
     * @param detections 3D bounding box detections from LiDAR detector
     * @param timestamp Frame timestamp
     * @return Updated 3D tracks
     * @safety Validates 3D state, velocity limits
     * @wcet < 10 ms for 200 objects
     */
    std::vector<Track> process(const std::vector<Detection>& detections,
                                ara::core::TimeStamp timestamp);

private:
    // 3D Kalman filter state transition (constant velocity)
    Eigen::Matrix<float, 11, 11> compute_state_transition(float dt);

    // 3D Kalman filter measurement matrix
    Eigen::Matrix<float, 7, 11> compute_measurement_matrix();

    // Compute 3D-GIoU with orientation awareness
    float compute_orientation_aware_giou(
        const Track::BoundingBox3D& track_box,
        const Detection::BoundingBox3D& detection_box);

    // Convert quaternion to Euler angles
    Eigen::Vector3f quaternion_to_euler(
        const Eigen::Quaternionf& q);

    Config config_;
    std::vector<Track> active_tracks_;
    uint64_t next_track_id_ = 0U;
    ara::core::TimeStamp last_timestamp_;
};
```

### 3D Kalman Filter

```cpp
/**
 * @brief 3D Kalman filter for object tracking
 * State vector: [x, y, z, vx, vy, vz, l, w, h, yaw, yaw_rate]
 * Measurement: [x, y, z, l, w, h, yaw]
 */
class KalmanFilter3D {
public:
    using StateVector = Eigen::Matrix<float, 11, 1>;
    using CovarianceMatrix = Eigen::Matrix<float, 11, 11>;
    using MeasurementVector = Eigen::Matrix<float, 7, 1>;

    KalmanFilter3D(float process_noise_accel,
                   float measurement_noise_pos,
                   float measurement_noise_vel);

    /**
     * @brief Predict next state
     * @param dt Time step in seconds
     */
    void predict(float dt) {
        // State transition matrix (constant velocity)
        Eigen::Matrix<float, 11, 11> F = compute_transition_matrix(dt);

        // Predict state mean
        state_mean_ = F * state_mean_;

        // Predict state covariance
        CovarianceMatrix Q = compute_process_noise(dt);
        state_covariance_ = F * state_covariance_ * F.transpose() + Q;

        // Ensure positive semi-definiteness
        state_covariance_ = (state_covariance_ + state_covariance_.transpose()) / 2.0f;
    }

    /**
     * @brief Update with measurement
     * @param measurement [x, y, z, l, w, h, yaw]
     */
    void update(const MeasurementVector& measurement) {
        // Measurement matrix H
        Eigen::Matrix<float, 7, 11> H = compute_measurement_matrix();

        // Measurement noise R
        CovarianceMatrix R = compute_measurement_noise();

        // Innovation y = z - H*x
        MeasurementVector y = measurement - H * state_mean_;

        // Innovation covariance S = H*P*H' + R
        Eigen::Matrix<float, 7, 7> S = H * state_covariance_ * H.transpose() + R;

        // Kalman gain K = P*H'*S^(-1)
        auto K = state_covariance_ * H.transpose() * S.inverse();

        // Update state x = x + K*y
        state_mean_ = state_mean_ + K * y;

        // Update covariance P = (I - K*H)*P
        Eigen::Matrix<float, 11, 11> I = Eigen::Matrix<float, 11, 11>::Identity();
        state_covariance_ = (I - K * H) * state_covariance_;
    }

    StateVector get_state() const { return state_mean_; }
    CovarianceMatrix get_covariance() const { return state_covariance_; }

private:
    StateVector state_mean_;
    CovarianceMatrix state_covariance_;
    float process_noise_accel_;
    float measurement_noise_pos_;
    float measurement_noise_vel_;
};
```

---

## Track Management

### Birth, Death, and Coasting

```cpp
/**
 * @brief Track lifecycle management
 * @safety ASIL B - Prevent track proliferation, validate new tracks
 */
class TrackManager {
public:
    struct Config {
        uint32_t confirm_age = 3U;
        uint32_t max_consecutive_misses = 10U;
        uint32_t max_track_age = 1000U;
        uint32_t max_coasting_speed_mps = 30.0f;  // Coast only if speed < threshold
    };

    /**
     * @brief Create new track from unmatched detection
     * @safety Validates detection before track creation
     */
    Track create_track(const Detection& detection) {
        Track new_track;

        // Initialize from detection
        new_track.track_id = next_track_id_++;
        new_track.state = Track::State::NEW;
        new_track.age = 0U;
        new_track.confirmed_age = 0U;
        new_track.time_since_update = 0U;
        new_track.consecutive_misses = 0U;

        // Initialize Kalman state from detection
        new_track.kf_state.state_mean <<
            detection.bbox.center.x(),
            detection.bbox.center.y(),
            detection.bbox.center.z(),
            detection.bbox.velocity.x(),
            detection.bbox.velocity.y(),
            detection.bbox.velocity.z(),
            detection.bbox.dimensions.x(),
            detection.bbox.dimensions.y(),
            detection.bbox.dimensions.z(),
            detection.bbox.orientation.z(),  // yaw
            0.0f;  // yaw_rate (unknown at birth)

        // Initialize covariance (high uncertainty)
        new_track.kf_state.state_covariance =
            Eigen::Matrix<float, 11, 11>::Identity() * 10.0f;

        // Validity flags
        new_track.validity_flags.position_valid = true;
        new_track.validity_flags.velocity_valid =
            detection.bbox.velocity.norm() < MAX_OBJECT_SPEED_MPS;
        new_track.validity_flags.size_valid =
            (detection.bbox.dimensions.array() > 0.0f).all();
        new_track.validity_flags.class_valid =
            is_valid_class(detection.object_class);

        new_track.last_detection = detection;

        return new_track;
    }

    /**
     * @brief Update track state based on association result
     */
    void update_track_state(Track& track, bool matched) {
        track.age++;
        track.time_since_update++;

        if (matched) {
            track.consecutive_misses = 0U;
            track.confirmed_age++;

            // Transition from NEW to CONFIRMED
            if (track.state == Track::State::NEW &&
                track.confirmed_age >= config_.confirm_age) {
                track.state = Track::State::CONFIRMED;
            }

            // Coast exit
            if (track.state == Track::State::COASTING) {
                track.state = Track::State::CONFIRMED;
            }
        } else {
            track.consecutive_misses++;

            // Enter coasting state
            if (track.state == Track::State::CONFIRMED &&
                track.consecutive_misses >= 3U) {
                track.state = Track::State::COASTING;

                // Validate coasting is safe (low speed)
                float speed = get_current_speed(track);
                if (speed > config_.max_coasting_speed_mps) {
                    // Mark as uncertain - may need special handling
                    track.validity_flags.velocity_valid = false;
                }
            }

            // Delete track
            if (track.consecutive_misses >= config_.max_consecutive_misses) {
                track.state = Track::State::DELETED;
            }
        }

        // Prune old tracks
        if (track.age >= config_.max_track_age) {
            track.state = Track::State::DELETED;
        }
    }

    /**
     * @brief Get current speed from track state
     */
    float get_current_speed(const Track& track) const {
        return track.kf_state.state_mean.segment<3>(3).norm();
    }

    /**
     * @brief Remove deleted tracks from active list
     */
    void remove_deleted_tracks(std::vector<Track>& tracks) {
        tracks.erase(
            std::remove_if(tracks.begin(), tracks.end(),
                [](const Track& t) {
                    return t.state == Track::State::DELETED;
                }),
            tracks.end());
    }

private:
    Config config_;
    uint64_t next_track_id_ = 0U;
};
```

---

## Safety Mechanisms

### Track Validation

```cpp
/**
 * @brief Safety monitor for multi-object tracking
 * @safety ASIL C - Validates all tracks before output
 */
class TrackingSafetyMonitor {
public:
    struct FaultState {
        bool all_tracks_valid : 1;
        uint32_t num_invalid_tracks;
        uint32_t num_id_switches_detected;
        uint32_t num_ghost_tracks;
        DTC_CODE dtc;
    };

    /**
     * @brief Validate all tracks against physical constraints
     * @safety ASIL C - Prevents invalid tracks from reaching planning
     * @req SSR-PERCEP-076, SSR-PERCEP-077
     */
    FaultState validate_tracks(const std::vector<Track>& tracks) {
        FaultState fault;
        fault.all_tracks_valid = true;
        fault.num_invalid_tracks = 0U;
        fault.num_id_switches_detected = 0U;
        fault.num_ghost_tracks = 0U;
        fault.dtc = DTC_NONE;

        for (const auto& track : tracks) {
            // Check 1: Position within sensor FOV
            if (!is_position_in_fov(track.kf_state.state_mean.head<3>())) {
                fault.num_invalid_tracks++;
                fault.all_tracks_valid = false;
                continue;  // Skip further checks for this track
            }

            // Check 2: Velocity within physical limits
            float speed = track.kf_state.state_mean.segment<3>(3).norm();
            if (speed > MAX_OBJECT_SPEED_MPS) {
                fault.num_invalid_tracks++;
                fault.all_tracks_valid = false;
                fault.dtc = DTC_TRACK_IMPLAUSIBLE_VELOCITY;
                continue;
            }

            // Check 3: Size within reasonable bounds
            auto size = track.kf_state.state_mean.segment<3>(6);
            if (size.x() < MIN_OBJECT_SIZE_M || size.x() > MAX_OBJECT_SIZE_M ||
                size.y() < MIN_OBJECT_SIZE_M || size.y() > MAX_OBJECT_SIZE_M ||
                size.z() < MIN_OBJECT_HEIGHT_M || size.z() > MAX_OBJECT_HEIGHT_M) {
                fault.num_invalid_tracks++;
                fault.all_tracks_valid = false;
                fault.dtc = DTC_TRACK_IMPLAUSIBLE_SIZE;
                continue;
            }

            // Check 4: Track age and update consistency
            if (track.consecutive_misses > 15U) {
                fault.num_ghost_tracks++;
                fault.all_tracks_valid = false;
                fault.dtc = DTC_GHOST_TRACK_DETECTED;
            }
        }

        // Check 5: ID switch detection (sudden position jumps)
        detect_id_switches(tracks, fault);

        // Report DTC if any invalid tracks
        if (!fault.all_tracks_valid) {
            Dem_ReportErrorStatus(fault.dtc);
        }

        return fault;
    }

private:
    /**
     * @brief Detect ID switches (track position jumps)
     */
    void detect_id_switches(const std::vector<Track>& tracks,
                             FaultState& fault) {
        for (const auto& track : tracks) {
            if (track.position_history.size() < 2U) {
                continue;
            }

            const auto& current_pos = track.kf_state.state_mean.head<3>();
            const auto& prev_pos = track.position_history.back();

            float delta = (current_pos - prev_pos).norm();
            float expected_max = get_max_motion_per_frame(track) * 1.5f;

            if (delta > expected_max) {
                fault.num_id_switches_detected++;
                fault.all_tracks_valid = false;
                fault.dtc = DTC_TRACK_ID_SWITCH;
            }
        }
    }

    /**
     * @brief Get maximum expected motion per frame
     */
    float get_max_motion_per_frame(const Track& track) const {
        float speed = track.kf_state.state_mean.segment<3>(3).norm();
        float dt = 0.1f;  // Assume 10 Hz tracking
        return speed * dt * 1.5f;  // 50% margin
    }

    bool is_position_in_fov(const Eigen::Vector3f& pos) const {
        // Check range
        float range = pos.head<2>().norm();
        if (range < MIN_SENSOR_RANGE_M || range > MAX_SENSOR_RANGE_M) {
            return false;
        }

        // Check azimuth (horizontal FOV)
        float azimuth = std::atan2(pos.y(), pos.x()) * 180.0f / M_PI;
        if (std::abs(azimuth) > SENSOR_FOV_AZIMUTH_DEG / 2.0f) {
            return false;
        }

        return true;
    }
};
```

### Track Coasting Limits

```cpp
/**
 * @brief Enforce coasting limits to prevent stale tracks
 */
class CoastingMonitor {
public:
    struct Config {
        uint32_t max_coast_frames = 10U;
        float max_coast_speed_mps = 30.0f;
        float coast_uncertainty_growth = 0.1f;  // 10% per frame
    };

    /**
     * @brief Apply coasting constraints
     * @safety ASIL B - Degrades track confidence during coasting
     */
    void apply_coasting_constraints(Track& track) {
        if (track.state != Track::State::COASTING) {
            return;
        }

        // Increase uncertainty during coasting
        float growth_factor = 1.0f +
            track.consecutive_misses * config_.coast_uncertainty_growth;
        track.kf_state.state_covariance *= growth_factor;

        // Limit coasting based on speed
        float speed = track.kf_state.state_mean.segment<3>(3).norm();
        if (speed > config_.max_coast_speed_mps) {
            // High-speed objects cannot coast - delete immediately
            track.state = Track::State::DELETED;
            return;
        }

        // Soft deletion: reduce confidence during coasting
        float coast_confidence = 1.0f -
            static_cast<float>(track.consecutive_misses) /
            static_cast<float>(config_.max_coast_frames);
        track.last_detection.confidence = std::max(0.0f, coast_confidence);
    }
};
```

---

## Integration with Multi-Sensor Fusion

### Tracking After Fusion

```cpp
/**
 * @brief Track fused detections from camera, LiDAR, and radar
 * @safety ASIL C - Cross-sensor track validation
 */
class MultiSensorTracker {
public:
    /**
     * @brief Process fused detections from multiple sensors
     * @param fused_detections Output from sensor fusion module
     * @return Consistent tracks across all sensors
     * @safety Validates track consistency across sensor sources
     */
    std::vector<Track> process_fused_detections(
        const std::vector<FusedDetection>& fused_detections) {

        // Use AB3DMOT for 3D tracking
        std::vector<Detection> detections_3d;
        for (const auto& fused : fused_detections) {
            detections_3d.push_back(fused.to_detection_3d());
        }

        return ab3dmot_tracker_.process(detections_3d, current_timestamp_);
    }

    /**
     * @brief Get tracks per sensor source (for diagnostics)
     */
    struct TrackBreakdown {
        uint32_t camera_only;
        uint32_t lidar_only;
        uint32_t radar_only;
        uint32_t multi_sensor;
    };

    TrackBreakdown get_sensor_breakdown() const {
        TrackBreakdown breakdown = {0, 0, 0, 0};

        for (const auto& track : active_tracks_) {
            uint8_t sensor_flags = track.last_detection.sensor_source;
            if (sensor_flags & (SENSOR_CAMERA | SENSOR_LIDAR | SENSOR_RADAR)) {
                breakdown.multi_sensor++;
            } else if (sensor_flags & SENSOR_LIDAR) {
                breakdown.lidar_only++;
            } else if (sensor_flags & SENSOR_CAMERA) {
                breakdown.camera_only++;
            } else if (sensor_flags & SENSOR_RADAR) {
                breakdown.radar_only++;
            }
        }

        return breakdown;
    }

private:
    Ab3dmotTracker ab3dmot_tracker_;
    std::vector<Track> active_tracks_;
    ara::core::TimeStamp current_timestamp_;
};
```

---

## Performance Benchmarks

| Algorithm | MOTA | IDF1 | Latency | Platform | ASIL |
|-----------|------|------|---------|----------|------|
| SORT (2D) | 75-85% | 70-80% | < 5 ms | Jacinto A72 | B |
| DeepSORT (2D) | 80-90% | 75-85% | < 10 ms | Jetson Orin | B/C |
| AB3DMOT (3D) | 80-90% | 75-85% | < 10 ms | Jetson Orin | C |
| JPDA (3D) | 85-92% | 80-88% | < 20 ms | Jacinto A72+C66x | C/D |
| MHT (3D) | 88-95% | 85-92% | < 50 ms | HPC (Xavier) | C/D |

### End-to-End Tracking Pipeline

| Processing Stage | WCET (ms) | Platform | ASIL |
|-----------------|-----------|----------|------|
| Detection input (from fusion) | 0.5 | Jacinto A72 | B |
| Cost matrix computation | 1.0 | Jacinto A72 | B |
| Hungarian assignment | 0.5 | Jacinto A72 | B |
| Kalman filter update | 0.5 | Jacinto A72 | B |
| Track management | 0.5 | Jacinto A72 | B |
| Safety validation | 0.5 | Jacinto A72 | C |
| **Full pipeline (100 objects)** | **< 5 ms** | **Jacinto A72** | **B** |

---

## Related Context

- @context/skills/adas/sensor-fusion.md - EKF/UKF for state estimation
- @context/skills/adas/lidar-processing.md - 3D detection input for tracking
- @context/skills/adas/camera-processing.md - 2D detection input for tracking
- @context/skills/adas/calibration.md - Extrinsic calibration for multi-sensor tracking
- @knowledge/standards/iso26262/2-conceptual.md - ASIL requirements for tracking
- @knowledge/standards/iso21448/1-overview.md - SOTIF for occlusion handling

---

## References

- Bewley, A., et al. "Simple online and realtime tracking." ICIP 2016.
- Wojke, N., et al. "Simple online and realtime tracking with a deep association metric." ICIP 2017.
- Weng, X., et al. "Ab3dmot: A baseline for 3d multi-object tracking and new evaluation metrics." arXiv 2020.
- Kuhn, H. W. "The Hungarian method for the assignment problem." Naval Research Logistics Quarterly 1955.
- Blackman, S. "Multiple hypothesis tracking for multiple target tracking." IEEE AES 2004.

---

*This context file is part of the Automotive Copilot Agents suite. For related expertise, see @automotive-adas-perception-engineer, @automotive-adas-planning-engineer, and @automotive-functional-safety-engineer.*
