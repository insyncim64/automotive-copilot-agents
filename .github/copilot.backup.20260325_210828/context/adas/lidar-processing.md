# LiDAR Processing for ADAS

> Point cloud processing, 3D object detection, LiDAR-camera fusion, and SLAM
> for automotive ADAS and autonomous driving applications.

**Standards Compliance:**
- ISO 26262 ASIL B/C/D (functional safety)
- ISO 21448 SOTIF (safety of intended functionality)
- AUTOSAR Classic/Adaptive integration patterns

---

## Domain Expertise

| Capability | Architecture/Method | Accuracy | Latency |
|------------|---------------------|----------|---------|
| **Point Cloud Preprocessing** | Voxelization, RANSAC, Statistical Outlier Removal | N/A | < 5 ms |
| **Ground Segmentation** | RANSAC Plane Fitting, Elevation Mapping | > 98% | < 3 ms |
| **3D Object Detection** | PointPillars, PointRCNN, CenterPoint, PV-RCNN | mAP > 85% | < 30 ms |
| **LiDAR-Camera Fusion** | Frustum-based, Projection-based, Deep Fusion | mAP > 90% | < 40 ms |
| **SLAM** | LOAM, LeGO-LOAM, LIO-SAM | Drift < 1% | < 50 ms |

---

## LiDAR Sensor Fundamentals

### LiDAR Types and Specifications

| LiDAR Type | Principle | Range | Points/sec | Use Case |
|------------|-----------|-------|------------|----------|
| **Mechanical Spinning** | Rotating laser/receiver array | 100-250 m | 1-3 M | Robotaxi (L4) |
| **MEMS Mirror** | Micro-electromechanical scanning | 150-200 m | 500K-1M | L2+/L3 ADAS |
| **Flash LiDAR** | Single-pulse area illumination | 50-100 m | 10M+ | Parking (L4) |
| **Solid-State (OPA)** | Optical phased array | 100-150 m | 1-5M | Emerging L3+ |

### Point Cloud Data Structure

```cpp
/**
 * @brief Raw LiDAR point structure with metadata
 * @safety ASIL B - Input validation required
 */
struct LidarPoint {
    float x;          // Cartesian X (forward) [m]
    float y;          // Cartesian Y (left) [m]
    float z;          // Cartesian Z (up) [m]
    float intensity;  // Return intensity [0-1] or [0-65535]
    uint32_t timestamp_us;  // Microsecond timestamp within sweep
    uint16_t ring;    // Laser ring index (for multi-layer LiDAR)
    uint8_t return_type;    // 0=first, 1=last, 2=strongest, 3=multi
};

/**
 * @brief Organized point cloud (range image format)
 * @note More memory-efficient for processing pipelines
 */
struct OrganizedPointCloud {
    std::vector<LidarPoint> points;
    size_t width;   // Horizontal resolution (e.g., 1800 for 0.2° azimuth)
    size_t height;  // Vertical resolution (e.g., 64 for 64-layer LiDAR)

    // Access via (row, col) for neighborhood operations
    LidarPoint& at(size_t row, size_t col) {
        return points[row * width + col];
    }
};

/**
 * @brief Unorganized point cloud (list format)
 * @note Simpler but less efficient for spatial queries
 */
struct UnorganizedPointCloud {
    std::vector<LidarPoint> points;
    Eigen::Vector4f origin;  // LiDAR sensor position
};
```

---

## Point Cloud Preprocessing

### Voxel Grid Downsampling

```cpp
/**
 * @brief Voxel grid filter for uniform point cloud downsampling
 * @safety ASIL B - Reduces computation while preserving geometry
 *
 * Voxelization enables:
 * - Uniform point density for consistent processing
 * - Noise reduction through spatial averaging
 * - Computational complexity reduction (O(n) → O(n/k))
 */
class VoxelGridFilter {
public:
    struct Config {
        float leaf_size_x;   // Voxel size X [m], typical: 0.1-0.2
        float leaf_size_y;   // Voxel size Y [m], typical: 0.1-0.2
        float leaf_size_z;   // Voxel size Z [m], typical: 0.1-0.2
        bool downsample_all_data;  // If false, only downsample XYZ
    };

    UnorganizedPointCloud filter(const UnorganizedPointCloud& input) {
        UnorganizedPointCloud output;
        output.origin = input.origin;

        // Voxel hash map for O(1) lookup
        std::unordered_map<VoxelKey, VoxelData, VoxelKeyHash> voxel_grid;

        // 1. Assign points to voxels
        for (const auto& point : input.points) {
            VoxelKey key = compute_voxel_key(point);
            auto& voxel = voxel_grid[key];
            voxel.points.push_back(point);
            voxel.centroid_x += point.x;
            voxel.centroid_y += point.y;
            voxel.centroid_z += point.z;
            voxel.centroid_intensity += point.intensity;
            voxel.count++;
        }

        // 2. Compute centroid for each occupied voxel
        output.points.reserve(voxel_grid.size());
        for (const auto& [key, voxel] : voxel_grid) {
            if (voxel.count > 0) {
                LidarPoint centroid;
                centroid.x = voxel.centroid_x / voxel.count;
                centroid.y = voxel.centroid_y / voxel.count;
                centroid.z = voxel.centroid_z / voxel.count;
                centroid.intensity = voxel.centroid_intensity / voxel.count;
                centroid.timestamp_us = voxel.points[0].timestamp_us;
                centroid.ring = voxel.points[0].ring;
                centroid.return_type = voxel.points[0].return_type;
                output.points.push_back(centroid);
            }
        }

        return output;
    }

private:
    struct VoxelKey {
        int x, y, z;
        bool operator==(const VoxelKey& other) const {
            return x == other.x && y == other.y && z == other.z;
        }
    };

    struct VoxelKeyHash {
        size_t operator()(const VoxelKey& k) const {
            return std::hash<int>()(k.x) ^
                   (std::hash<int>()(k.y) << 1) ^
                   (std::hash<int>()(k.z) << 2);
        }
    };

    struct VoxelData {
        std::vector<LidarPoint> points;
        double centroid_x = 0, centroid_y = 0, centroid_z = 0;
        double centroid_intensity = 0;
        size_t count = 0;
    };

    VoxelKey compute_voxel_key(const LidarPoint& p) const {
        return VoxelKey{
            static_cast<int>(floor(p.x / config_.leaf_size_x)),
            static_cast<int>(floor(p.y / config_.leaf_size_y)),
            static_cast<int>(floor(p.z / config_.leaf_size_z))
        };
    }

    Config config_;
};
```

### Statistical Outlier Removal (SOR)

```cpp
/**
 * @brief Statistical outlier removal for LiDAR noise filtering
 * @safety ASIL B - Removes spurious points from rain, dust, sensor noise
 *
 * Algorithm:
 * 1. For each point, compute mean distance to k nearest neighbors
 * 2. Compute global mean and standard deviation of all mean distances
 * 3. Remove points with mean distance > global_mean + std_mult * std_dev
 */
class StatisticalOutlierRemoval {
public:
    struct Config {
        size_t mean_k;       // Number of neighbors for distance estimation
        float std_mult;      // Standard deviation multiplier (typical: 1.0-2.0)
        float max_search_radius;  // Limit neighbor search radius [m]
    };

    UnorganizedPointCloud filter(const UnorganizedPointCloud& input) {
        UnorganizedPointCloud output;

        if (input.points.size() < config_.mean_k + 1) {
            return input;  // Too few points for SOR
        }

        // Build K-D tree for efficient neighbor search
        KdTree tree(input.points);

        // 1. Compute mean distance to k nearest neighbors for each point
        std::vector<float> mean_distances;
        mean_distances.reserve(input.points.size());

        for (const auto& point : input.points) {
            auto neighbors = tree.k_nearest(point, config_.mean_k + 1);
            float sum_dist = 0.0f;
            size_t count = 0;

            for (size_t i = 1; i < neighbors.size() && count < config_.mean_k; ++i) {
                float dist = compute_distance(point, neighbors[i]);
                if (dist < config_.max_search_radius) {
                    sum_dist += dist;
                    count++;
                }
            }

            mean_distances.push_back(count > 0 ? sum_dist / count : 0.0f);
        }

        // 2. Compute global statistics
        const auto [global_mean, global_std] = compute_statistics(mean_distances);
        const float threshold = global_mean + config_.std_mult * global_std;

        // 3. Filter outliers
        for (size_t i = 0; i < input.points.size(); ++i) {
            if (mean_distances[i] <= threshold) {
                output.points.push_back(input.points[i]);
            }
        }

        return output;
    }

private:
    std::pair<float, float> compute_statistics(const std::vector<float>& values) {
        float sum = std::accumulate(values.begin(), values.end(), 0.0f);
        float mean = sum / values.size();

        float sq_sum = 0.0f;
        for (float v : values) {
            sq_sum += (v - mean) * (v - mean);
        }
        float std = std::sqrt(sq_sum / values.size());

        return {mean, std};
    }

    float compute_distance(const LidarPoint& a, const LidarPoint& b) const {
        float dx = a.x - b.x;
        float dy = a.y - b.y;
        float dz = a.z - b.z;
        return std::sqrt(dx*dx + dy*dy + dz*dz);
    }

    Config config_;
};
```

---

## Ground Segmentation

### RANSAC Plane Fitting

```cpp
/**
 * @brief RANSAC-based ground plane segmentation
 * @safety ASIL B - Critical for obstacle detection and free-space estimation
 *
 * @note Assumes LiDAR is mounted with known orientation relative to vehicle
 *       For sloped roads, use iterative refinement or elevation mapping
 */
class GroundSegmentationRANSAC {
public:
    struct Config {
        float max_distance_threshold;  // Max distance to plane [m], typical: 0.2
        size_t min_inliers;            // Minimum inliers to accept plane
        float p_success;               // Desired probability of success (0.99)
        size_t max_iterations;         // Upper bound on iterations
        float normal_z_threshold;      // Acceptable Z component of normal [0.9-1.0]
    };

    struct Result {
        std::vector<LidarPoint> ground_points;
        std::vector<LidarPoint> obstacle_points;
        Eigen::Vector3f plane_normal;
        float plane_distance;  // Distance from origin to plane
        bool success;
    };

    Result segment(const UnorganizedPointCloud& input) {
        Result result;
        result.success = false;

        if (input.points.size() < 3) {
            return result;
        }

        size_t best_inlier_count = 0;
        Eigen::Vector3f best_normal;
        float best_distance = 0.0f;
        std::vector<size_t> best_inliers;

        // Compute number of iterations for desired success probability
        const float inlier_ratio_estimate = 0.6f;  // Assume 60% ground initially
        const size_t num_samples = 3;  // 3 points define a plane
        size_t max_iters = config_.max_iterations;

        if (inlier_ratio_estimate > 0) {
            max_iters = static_cast<size_t>(
                std::log(1.0f - config_.p_success) /
                std::log(1.0f - std::pow(inlier_ratio_estimate, num_samples))
            );
        }

        std::mt19937 rng(42);  // Fixed seed for determinism

        for (size_t iter = 0; iter < max_iters; ++iter) {
            // 1. Randomly select 3 points
            std::uniform_int_distribution<size_t> dist(0, input.points.size() - 1);
            const auto& p1 = input.points[dist(rng)];
            const auto& p2 = input.points[dist(rng)];
            const auto& p3 = input.points[dist(rng)];

            // 2. Compute plane from 3 points
            Eigen::Vector3f v1(p2.x - p1.x, p2.y - p1.y, p2.z - p1.z);
            Eigen::Vector3f v2(p3.x - p1.x, p3.y - p1.y, p3.z - p1.z);
            Eigen::Vector3f normal = v1.cross(v2).normalized();

            // Ensure normal points upward
            if (normal.z() < 0) {
                normal = -normal;
            }

            // Check normal is close to vertical (ground plane assumption)
            if (normal.z() < config_.normal_z_threshold) {
                continue;
            }

            float d = -(normal.x() * p1.x + normal.y() * p1.y + normal.z() * p1.z);

            // 3. Count inliers
            std::vector<size_t> inliers;
            for (size_t i = 0; i < input.points.size(); ++i) {
                const auto& p = input.points[i];
                float dist_to_plane = std::abs(normal.x() * p.x +
                                               normal.y() * p.y +
                                               normal.z() * p.z + d);
                if (dist_to_plane < config_.max_distance_threshold) {
                    inliers.push_back(i);
                }
            }

            // 4. Update best model
            if (inliers.size() > best_inlier_count) {
                best_inlier_count = inliers.size();
                best_normal = normal;
                best_distance = d;
                best_inliers = inliers;

                // Early termination if we have enough inliers
                if (best_inlier_count >= config_.min_inliers) {
                    break;
                }
            }
        }

        // 5. Check if valid plane found
        if (best_inlier_count >= config_.min_inliers) {
            result.plane_normal = best_normal;
            result.plane_distance = best_distance;
            result.success = true;

            // Separate ground and obstacle points
            for (size_t i : best_inliers) {
                result.ground_points.push_back(input.points[i]);
            }
            for (size_t i = 0; i < input.points.size(); ++i) {
                if (std::find(best_inliers.begin(), best_inliers.end(), i) == best_inliers.end()) {
                    result.obstacle_points.push_back(input.points[i]);
                }
            }
        } else {
            // Fallback: all points as obstacles
            result.obstacle_points = input.points;
        }

        return result;
    }

private:
    Config config_;
};
```

### Elevation Map-based Segmentation

```cpp
/**
 * @brief Elevation map for ground segmentation on sloped terrain
 * @safety ASIL B - Handles road gradients better than RANSAC
 *
 * Creates a 2.5D grid where each cell stores:
 * - Minimum height (ground estimate)
 * - Maximum height (obstacle detection)
 * - Height variance (surface roughness)
 */
class ElevationMapSegmentation {
public:
    struct Config {
        float resolution;         // Grid cell size [m], typical: 0.1-0.2
        float max_ground_slope;   // Maximum ground slope [rad], typical: 10°
        float height_threshold;   // Height above ground for obstacle [m], typical: 0.15
        float min_points_per_cell; // Minimum points to consider cell valid
    };

    struct Cell {
        float min_height = std::numeric_limits<float>::max();
        float max_height = std::numeric_limits<float>::lowest();
        float sum_height = 0.0f;
        float sum_height_sq = 0.0f;
        size_t point_count = 0;

        float mean_height() const {
            return point_count > 0 ? sum_height / point_count : 0.0f;
        }

        float variance() const {
            if (point_count < 2) return 0.0f;
            float mean = mean_height();
            return (sum_height_sq / point_count) - (mean * mean);
        }
    };

    struct Result {
        std::vector<LidarPoint> ground_points;
        std::vector<LidarPoint> obstacle_points;
        std::vector<std::vector<Cell>> elevation_map;
    };

    Result segment(const UnorganizedPointCloud& input) {
        Result result;

        // 1. Determine grid bounds
        float min_x = std::numeric_limits<float>::max();
        float max_x = std::numeric_limits<float>::lowest();
        float min_y = std::numeric_limits<float>::max();
        float max_y = std::numeric_limits<float>::lowest();

        for (const auto& p : input.points) {
            min_x = std::min(min_x, p.x);
            max_x = std::max(max_x, p.x);
            min_y = std::min(min_y, p.y);
            max_y = std::max(max_y, p.y);
        }

        // 2. Initialize grid
        size_t grid_width = static_cast<size_t>((max_x - min_x) / config_.resolution) + 1;
        size_t grid_height = static_cast<size_t>((max_y - min_y) / config_.resolution) + 1;
        result.elevation_map.resize(grid_height, std::vector<Cell>(grid_width));

        // 3. Populate elevation map
        for (const auto& p : input.points) {
            size_t cell_x = static_cast<size_t>((p.x - min_x) / config_.resolution);
            size_t cell_y = static_cast<size_t>((p.y - min_y) / config_.resolution);

            if (cell_x < grid_width && cell_y < grid_height) {
                Cell& cell = result.elevation_map[cell_y][cell_x];
                cell.min_height = std::min(cell.min_height, p.z);
                cell.max_height = std::max(cell.max_height, p.z);
                cell.sum_height += p.z;
                cell.sum_height_sq += p.z * p.z;
                cell.point_count++;
            }
        }

        // 4. Estimate ground height per cell using local neighborhood
        auto get_ground_height = [&](size_t cx, size_t cy) -> float {
            const Cell& cell = result.elevation_map[cy][cx];
            if (cell.point_count < config_.min_points_per_cell) {
                return std::numeric_limits<float>::quiet_NaN();
            }

            // Use percentile-based ground estimation (more robust than min)
            // For simplicity, use weighted combination of min and mean
            const float weight_min = 0.7f;
            const float weight_mean = 0.3f;
            return weight_min * cell.min_height + weight_mean * cell.mean_height();
        };

        // 5. Classify points as ground or obstacle
        for (const auto& p : input.points) {
            size_t cell_x = static_cast<size_t>((p.x - min_x) / config_.resolution);
            size_t cell_y = static_cast<size_t>((p.y - min_y) / config_.resolution);

            if (cell_x >= grid_width || cell_y >= grid_height) {
                result.obstacle_points.push_back(p);
                continue;
            }

            float ground_height = get_ground_height(cell_x, cell_y);

            // Check neighboring cells for smoother ground estimation
            if (std::isnan(ground_height)) {
                float sum_neighbors = 0.0f;
                size_t count_neighbors = 0;
                for (int dy = -1; dy <= 1 && count_neighbors < 4; ++dy) {
                    for (int dx = -1; dx <= 1 && count_neighbors < 4; ++dx) {
                        int nx = static_cast<int>(cell_x) + dx;
                        int ny = static_cast<int>(cell_y) + dy;
                        if (nx >= 0 && ny >= 0 && nx < static_cast<int>(grid_width) &&
                            ny < static_cast<int>(grid_height)) {
                            float ngh = get_ground_height(nx, ny);
                            if (!std::isnan(ngh)) {
                                sum_neighbors += ngh;
                                count_neighbors++;
                            }
                        }
                    }
                }
                ground_height = count_neighbors > 0 ? sum_neighbors / count_neighbors : p.z;
            }

            // Classify based on height above ground
            if (p.z < ground_height + config_.height_threshold) {
                result.ground_points.push_back(p);
            } else {
                result.obstacle_points.push_back(p);
            }
        }

        return result;
    }

private:
    Config config_;
};
```

---

## 3D Object Detection

### PointPillars Architecture

```cpp
/**
 * @brief PointPillars 3D object detection network
 * @safety ASIL C - Primary perception for L3+ autonomous driving
 *
 * Architecture:
 * 1. Point Pillar Feature Net: Convert irregular point cloud to pseudo-image
 * 2. 2D CNN Backbone: Process pillar feature map efficiently
 * 3. Detection Head: Output 3D bounding boxes with class scores
 *
 * Performance:
 * - Latency: 10-15 ms on embedded GPU (Jetson Orin)
 * - Accuracy: 75-85% mAP on KITTI, Waymo benchmarks
 * - Memory: ~200 MB model + intermediate buffers
 */
class PointPillarsDetector {
public:
    struct Config {
        // Pillar parameters
        float pillar_size_x;      // Typical: 0.16 m
        float pillar_size_y;      // Typical: 0.16 m
        float pillar_size_z;      // Typical: 4.0 m (covers full height range)
        float max_x_range;        // Typical: 70.0 m (forward)
        float min_x_range;        // Typical: 0.0 m
        float max_y_range;        // Typical: 70.0 m (left/right)
        float min_y_range;        // Typical: -70.0 m
        size_t max_points_per_pillar;  // Typical: 100
        size_t max_pillars;       // Typical: 12000

        // Network parameters (pre-defined for deployment)
        std::string model_path;
        float score_threshold;    // Typical: 0.45
        float nms_iou_threshold;  // Typical: 0.3
    };

    struct Detection {
        Eigen::Vector3f center;    // (x, y, z) center
        Eigen::Vector3f size;      // (l, w, h) dimensions
        Eigen::Vector3f rpy;       // (roll, pitch, yaw) orientation
        float confidence;          // Detection confidence [0-1]
        uint8_t class_id;          // Object class
    };

    std::vector<Detection> detect(const UnorganizedPointCloud& input) {
        std::vector<Detection> detections;

        // 1. Voxelization: Assign points to pillars
        std::unordered_map<PillarKey, std::vector<LidarPoint>, PillarKeyHash> pillars;
        for (const auto& point : input.points) {
            // Filter points outside ROI
            if (point.x < config_.min_x_range || point.x > config_.max_x_range ||
                point.y < config_.min_y_range || point.y > config_.max_y_range) {
                continue;
            }

            PillarKey key = compute_pillar_key(point);
            if (pillars[key].size() < config_.max_points_per_pillar) {
                pillars[key].push_back(point);
            }

            if (pillars.size() >= config_.max_pillars) {
                break;
            }
        }

        // 2. Feature encoding per pillar
        PillarFeatureMap feature_map;
        for (const auto& [key, points] : pillars) {
            auto features = encode_pillar_features(points, key, config_);
            feature_map.add_pillar(key, features);
        }

        // 3. Scatter to pseudo-image
        auto pseudo_image = feature_map.to_pseudo_image();

        // 4. Run 2D CNN backbone (TensorRT inference)
        auto backbone_features = run_cnn_backbone(pseudo_image);

        // 5. Detection head (class + bbox regression)
        auto raw_detections = run_detection_head(backbone_features);

        // 6. Post-processing: Score thresholding + NMS
        detections = postprocess_detections(raw_detections);

        return detections;
    }

private:
    struct PillarKey {
        int x, y;
        bool operator==(const PillarKey& other) const {
            return x == other.x && y == other.y;
        }
    };

    struct PillarKeyHash {
        size_t operator()(const PillarKey& k) const {
            return std::hash<int>()(k.x) ^ (std::hash<int>()(k.y) << 1);
        }
    };

    Config config_;
    std::unique_ptr<TensorRTEngine> engine_;
};

/**
 * @brief Pillar Feature Net implementation
 * @note Learns rich features from sparse point cloud
 *
 * Input per point: (x, y, z, intensity, x_offset, y_offset, z_offset, x_center, y_center, z_center)
 * Output per pillar: 64-dimensional feature vector
 */
class PillarFeatureNet {
public:
    static constexpr size_t kNumFeatures = 10;  // Per-point features
    static constexpr size_t kOutputFeatures = 64;  // Per-pillar output

    std::vector<float> encode(const std::vector<LidarPoint>& points,
                               const Eigen::Vector3f& pillar_center) {
        std::vector<std::array<float, kNumFeatures>> point_features;
        point_features.reserve(points.size());

        for (const auto& p : points) {
            std::array<float, kNumFeatures> features;
            features[0] = p.x;                    // Absolute coordinates
            features[1] = p.y;
            features[2] = p.z;
            features[3] = p.intensity;            // Return intensity
            features[4] = p.x - pillar_center.x(); // Offset from pillar center
            features[5] = p.y - pillar_center.y();
            features[6] = p.z - pillar_center.z();
            features[7] = pillar_center.x();       // Pillar center (for location awareness)
            features[8] = pillar_center.y();
            features[9] = pillar_center.z();
            point_features.push_back(features);
        }

        // Linear layer -> BatchNorm -> ReLU
        auto linear_output = linear_layer(point_features);
        auto normalized = batch_norm(linear_output);
        auto activated = relu(normalized);

        // Reduce to single pillar feature (max or average pooling)
        return max_pool(activated);
    }

private:
    std::vector<std::array<float, kOutputFeatures>> linear_layer(
        const std::vector<std::array<float, kNumFeatures>>& input) {
        // Pre-trained weights loaded from model file
        // W: [kNumFeatures, kOutputFeatures], b: [kOutputFeatures]
        // output = input @ W + b
        // ... implementation ...
        return {};
    }

    std::vector<std::array<float, kOutputFeatures>> batch_norm(
        const std::vector<std::array<float, kOutputFeatures>>& input) {
        // Batch normalization with learned gamma, beta
        // ... implementation ...
        return {};
    }

    std::vector<std::array<float, kOutputFeatures>> relu(
        const std::vector<std::array<float, kOutputFeatures>>& input) {
        std::vector<std::array<float, kOutputFeatures>> output(input.size());
        for (size_t i = 0; i < input.size(); ++i) {
            for (size_t j = 0; j < kOutputFeatures; ++j) {
                output[i][j] = std::max(0.0f, input[i][j]);
            }
        }
        return output;
    }

    std::vector<float> max_pool(
        const std::vector<std::array<float, kOutputFeatures>>& features) {
        std::vector<float> pooled(kOutputFeatures, std::numeric_limits<float>::lowest());
        for (const auto& f : features) {
            for (size_t j = 0; j < kOutputFeatures; ++j) {
                pooled[j] = std::max(pooled[j], f[j]);
            }
        }
        return pooled;
    }
};
```

### CenterPoint Architecture

```cpp
/**
 * @brief CenterPoint 3D object detector (anchor-free approach)
 * @safety ASIL C - State-of-the-art for multi-class 3D detection
 *
 * Key innovations:
 * - Anchor-free: Predict object centers directly (no predefined boxes)
 * - Multi-task head: Simultaneously predict center, size, rotation, velocity
 * - Motion modeling: Track objects across frames via velocity prediction
 *
 * Comparison with PointPillars:
 * - +10-15% mAP improvement on challenging datasets
 * - Better handling of occluded and truncated objects
 * - ~20% higher latency due to more complex architecture
 */
class CenterPointDetector {
public:
    struct Detection {
        Eigen::Vector3f center;
        Eigen::Vector3f dimensions;  // (length, width, height)
        float yaw;                    // Heading angle [-π, π]
        Eigen::Vector2f velocity;     // (vx, vy) in m/s
        float confidence;
        uint8_t class_id;
        uint32_t track_id;           // Optional: for tracking
    };

    struct Config {
        float voxel_size;           // Voxel size [m], typical: 0.075-0.1
        float score_threshold;      // Confidence threshold, typical: 0.35
        float nms_iou_threshold;    // Non-max suppression IoU, typical: 0.3
        size_t max_detections;      // Maximum detections per class, typical: 500
        std::vector<std::string> class_names;  // ["car", "pedestrian", "cyclist", ...]
    };

    std::vector<Detection> detect(const UnorganizedPointCloud& input) {
        std::vector<Detection> detections;

        // 1. Voxel Feature Encoding (VFE)
        auto voxels = voxelize(input);
        auto voxel_features = encode_voxel_features(voxels);

        // 2. Sparse 3D Convolution Backbone
        auto sparse_features = run_sparse_3d_conv(voxel_features);

        // 3. Convert to Bird's Eye View (BEV) representation
        auto bev_features = voxels_to_bev(sparse_features);

        // 4. 2D CNN for BEV feature refinement
        auto refined_bev = run_bev_refinement(bev_features);

        // 5. Multi-task detection head
        //    - Heatmap: Object center presence probability
        //    - Regression: Center offset, dimensions, rotation
        //    - Velocity: Motion vector
        auto heatmap = predict_heatmap(refined_bev);
        auto regression = predict_regression(refined_bev);
        auto velocity = predict_velocity(refined_bev);

        // 6. Decode detections from heatmap peaks
        auto raw_detections = decode_heatmap_peaks(heatmap, regression, velocity);

        // 7. Post-processing: Score filtering, NMS
        detections = postprocess(raw_detections);

        return detections;
    }

private:
    Config config_;
    std::unique_ptr<TensorRTEngine> engine_;
};
```

---

## LiDAR-Camera Fusion

### Frustum-based Fusion (Early Fusion)

```cpp
/**
 * @brief Frustum-based LiDAR-camera fusion
 * @safety ASIL C - Combines LiDAR depth accuracy with camera texture
 *
 * Pipeline:
 * 1. Generate 2D proposals from camera (YOLO/SSD)
 * 2. Extrude 2D boxes into 3D frustums
 * 3. Group LiDAR points within each frustum
 * 4. Estimate 3D box from frustum point cloud
 *
 * Advantages:
 * - Leverages mature 2D detection models
 * - Efficient (processes only relevant points)
 * - Robust to LiDAR sparsity at long range
 *
 * Limitations:
 * - Dependent on camera detection quality
 * - May miss objects visible only to LiDAR
 */
class FrustumBasedFusion {
public:
    struct Config {
        float min_frustum_points;   // Minimum LiDAR points in frustum, typical: 10
        float max_frustum_range;    // Maximum frustum range [m], typical: 100
        float iou_threshold;        // 2D-3D IoU for association, typical: 0.5
        Eigen::Matrix4f lidar_to_camera;  // Extrinsic calibration
        Eigen::Matrix3f camera_intrinsics; // Camera intrinsics
    };

    struct FusedDetection {
        Detection2D camera_detection;    // 2D box from camera
        Detection3D lidar_detection;     // 3D box from LiDAR
        float fusion_confidence;
        uint8_t class_id;
    };

    std::vector<FusedDetection> fuse(
        const std::vector<Detection2D>& camera_detections,
        const UnorganizedPointCloud& lidar_points,
        const cv::Mat& camera_image) {

        std::vector<FusedDetection> fused_detections;

        for (const auto& det_2d : camera_detections) {
            // 1. Construct 3D frustum from 2D box
            std::vector<Eigen::Vector3f> frustum_corners =
                create_frustum(det_2d.bbox, config_.max_frustum_range,
                              config_.camera_intrinsics, config_.lidar_to_camera);

            // 2. Find LiDAR points inside frustum
            std::vector<LidarPoint> frustum_points;
            for (const auto& point : lidar_points.points) {
                if (is_point_in_frustum(point, frustum_corners)) {
                    frustum_points.push_back(point);
                }
            }

            // 3. Skip if insufficient points
            if (frustum_points.size() < config_.min_frustum_points) {
                continue;
            }

            // 4. Estimate 3D bounding box from frustum points
            Detection3D det_3d = estimate_3d_box(frustum_points, det_2d.class_id);

            // 5. Create fused detection
            FusedDetection fused;
            fused.camera_detection = det_2d;
            fused.lidar_detection = det_3d;
            fused.fusion_confidence = 0.8f * det_2d.confidence +
                                      0.2f * det_3d.confidence;  // Weighted fusion
            fused.class_id = det_2d.class_id;
            fused_detections.push_back(fused);
        }

        return fused_detections;
    }

private:
    std::vector<Eigen::Vector3f> create_frustum(
        const BoundingBox2D& bbox_2d,
        float max_range,
        const Eigen::Matrix3f& K,
        const Eigen::Matrix4f& extrinsic) {

        std::vector<Eigen::Vector3f> corners;

        // 8 corners of frustum: 4 near plane + 4 far plane
        float near_z = 2.0f;  // Near clipping plane

        // Near plane corners (in camera frame)
        std::vector<Eigen::Vector2d> near_pixels = {
            {bbox_2d.x, bbox_2d.y},
            {bbox_2d.x + bbox_2d.width, bbox_2d.y},
            {bbox_2d.x + bbox_2d.width, bbox_2d.y + bbox_2d.height},
            {bbox_2d.x, bbox_2d.y + bbox_2d.height}
        };

        for (const auto& pixel : near_pixels) {
            Eigen::Vector3d cam_ray = K.inverse() * pixel.homogeneous();
            corners.push_back(extrinsic * (near_z * cam_ray).homogeneous());
        }

        // Far plane corners (same process, different depth)
        std::vector<Eigen::Vector2d> far_pixels = near_pixels;  // Same corners, larger scale
        for (const auto& pixel : far_pixels) {
            Eigen::Vector3d cam_ray = K.inverse() * pixel.homogeneous();
            corners.push_back(extrinsic * (max_range * cam_ray).homogeneous());
        }

        return corners;
    }

    bool is_point_in_frustum(const LidarPoint& point,
                              const std::vector<Eigen::Vector3f>& frustum) {
        // Point-in-polyhedron test using ray casting or half-space method
        // ... implementation ...
        return true;
    }

    Detection3D estimate_3d_box(const std::vector<LidarPoint>& points,
                                 uint8_t class_id) {
        // Fit oriented bounding box using PCA or minimum volume box
        // ... implementation ...
        Detection3D box;
        return box;
    }

    Config config_;
};
```

### Deep Fusion Architectures

```cpp
/**
 * @brief Deep fusion network for LiDAR-camera 3D detection
 * @safety ASIL C - End-to-end learned fusion for maximum accuracy
 *
 * Architecture options:
 * - PointPainting: Camera segmentation scores painted onto LiDAR points
 * - 3D-CVF: View transformation and feature fusion in BEV space
 * - TransFusion: Transformer-based cross-modal attention
 *
 * Performance:
 * - mAP improvement: +10-20% over LiDAR-only baselines
 * - Robustness: Better performance in adverse weather
 * - Latency: +5-10 ms overhead vs. LiDAR-only
 */
class DeepFusionDetector {
public:
    struct Config {
        std::string fusion_type;  // "point_painting", "3dcvf", "transfusion"
        std::string lidar_backbone;  // "pointpillars", "voxelnet", "centerpoint"
        std::string camera_backbone;  // "resnet34", "efficientnet"
        float score_threshold;
    };

    std::vector<Detection3D> detect(
        const UnorganizedPointCloud& lidar_points,
        const cv::Mat& camera_image) {

        std::vector<Detection3D> detections;

        // 1. Camera branch: Extract dense features
        auto camera_features = camera_backbone_.extract_features(camera_image);

        // 2. LiDAR branch: Extract sparse features
        auto lidar_features = lidar_backbone_.extract_features(lidar_points);

        // 3. Fusion module
        auto fused_features = fusion_module_.fuse(
            lidar_features,
            camera_features,
            calibration_);

        // 4. Detection head
        detections = detection_head_.predict(fused_features);

        return detections;
    }

private:
    Config config_;
    std::unique_ptr<CameraBackbone> camera_backbone_;
    std::unique_ptr<LidarBackbone> lidar_backbone_;
    std::unique_ptr<FusionModule> fusion_module_;
    std::unique_ptr<DetectionHead> detection_head_;
    Calibration calibration_;
};
```

---

## LiDAR SLAM

### LOAM (LiDAR Odometry and Mapping)

```cpp
/**
 * @brief LOAM: LiDAR Odometry and Mapping
 * @safety ASIL B - Real-time localization for autonomous driving
 *
 * Core algorithm:
 * 1. Feature extraction: Identify edge and planar points
 * 2. Odometry: Match features to local map (10 Hz)
 * 3. Mapping: Register odometry result to global map (1 Hz)
 *
 * Performance:
 * - Odometry drift: < 1% over typical urban routes
 * - Latency: < 50 ms for odometry, < 200 ms for mapping
 * - Robustness: Works in feature-rich environments, struggles in tunnels
 */
class LoamSlam {
public:
    struct Config {
        float edge_threshold;       // Curvature threshold for edge points
        float planar_threshold;     // Variance threshold for planar points
        size_t max_edge_features;   // Max edge features per scan, typical: 2000
        size_t max_planar_features; // Max planar features, typical: 4000
        float max_correspondence_dist;  // Max matching distance [m], typical: 2.0
    };

    struct OdometryResult {
        Eigen::Matrix4f transform;  // Pose change from last frame
        double timestamp;
        bool valid;
    };

    struct MapResult {
        std::vector<LidarPoint> edge_map;
        std::vector<LidarPoint> planar_map;
        Eigen::Matrix4f global_pose;
    };

    OdometryResult process_odometry(const UnorganizedPointCloud& input) {
        OdometryResult result;
        result.valid = false;

        // 1. Extract edge and planar features
        auto [edge_points, planar_points] = extract_features(input);

        // 2. Match features to local map
        auto edge_correspondences = match_edge_features(edge_points, local_edge_map_);
        auto planar_correspondences = match_planar_features(planar_points, local_planar_map_);

        // 3. Compute pose via ICP-like optimization
        Eigen::Matrix4f delta_transform;
        if (optimize_pose(edge_correspondences, planar_correspondences,
                          delta_transform)) {
            result.transform = delta_transform;
            result.timestamp = get_timestamp();
            result.valid = true;

            // Update current pose
            current_pose_ = current_pose_ * delta_transform;
        }

        return result;
    }

    MapResult process_mapping(const UnorganizedPointCloud& input,
                               const Eigen::Matrix4f& current_pose) {
        MapResult result;
        result.global_pose = current_pose;

        // Transform current scan to global frame
        auto global_points = transform_points(input, current_pose);

        // Add to global maps (with downsampling for memory efficiency)
        auto [edge_points, planar_points] = extract_features(global_points);
        result.edge_map = add_to_map(edge_points, global_edge_map_, 0.2f);
        result.planar_map = add_to_map(planar_points, global_planar_map_, 0.4f);

        // Update local map for next odometry iteration
        update_local_map(current_pose);

        return result;
    }

private:
    std::pair<std::vector<LidarPoint>, std::vector<LidarPoint>> extract_features(
        const UnorganizedPointCloud& input) {

        std::vector<LidarPoint> edge_points;
        std::vector<LidarPoint> planar_points;

        // Organize into range image for neighborhood computation
        auto range_image = organize_to_range_image(input);

        for (size_t row = 0; row < range_image.height; ++row) {
            for (size_t col = 0; col < range_image.width; ++col) {
                const auto& point = range_image.at(row, col);
                if (!is_valid(point)) continue;

                // Compute curvature using neighborhood
                float curvature = compute_curvature(range_image, row, col);

                // Classify based on curvature
                if (curvature > config_.edge_threshold) {
                    edge_points.push_back(point);
                } else if (curvature < config_.planar_threshold) {
                    planar_points.push_back(point);
                }
            }
        }

        // Downsample to most salient features
        downsample_features(edge_points, config_.max_edge_features);
        downsample_features(planar_points, config_.max_planar_features);

        return {edge_points, planar_points};
    }

    Config config_;
    Eigen::Matrix4f current_pose_ = Eigen::Matrix4f::Identity();
    std::vector<LidarPoint> global_edge_map_;
    std::vector<LidarPoint> global_planar_map_;
    std::vector<LidarPoint> local_edge_map_;
    std::vector<LidarPoint> local_planar_map_;
};
```

---

## Safety Mechanisms

### Plausibility Checks for LiDAR Detections

```cpp
/**
 * @brief Runtime plausibility monitoring for LiDAR perception
 * @safety ASIL C/D - Detects sensor faults and algorithm failures
 *
 * Checks:
 * - Point cloud density (detects occlusion, dirt, sensor degradation)
 * - Detection physical limits (velocity, acceleration, size)
 * - Temporal consistency (object persistence, motion smoothness)
 * - Cross-sensor agreement (LiDAR-camera correlation)
 */
class LidarSafetyMonitor {
public:
    struct FaultState {
        bool point_cloud_valid;
        bool density_valid;
        bool detections_plausible;
        bool temporal_consistent;
        uint32_t fault_codes;
    };

    FaultState validate(const UnorganizedPointCloud& points,
                         const std::vector<Detection3D>& detections) {
        FaultState state;
        state.fault_codes = 0;

        // 1. Point cloud density check
        float density = compute_point_density(points);
        state.point_cloud_valid = (density >= MIN_DENSITY_POINTS_PER_M3);
        if (!state.point_cloud_valid) {
            state.fault_codes |= FAULT_LOW_POINT_DENSITY;
        }

        // 2. Detection physical limits
        for (const auto& det : detections) {
            // Velocity plausibility (max 150 km/h for vehicles)
            float speed = det.velocity.norm();
            if (speed > MAX_OBJECT_SPEED_MPS) {
                state.detections_plausible = false;
                state.fault_codes |= FAULT_IMPLAUSIBLE_VELOCITY;
            }

            // Size plausibility
            if (det.dimensions.minCoeff() < MIN_OBJECT_SIZE_M ||
                det.dimensions.maxCoeff() > MAX_OBJECT_SIZE_M) {
                state.detections_plausible = false;
                state.fault_codes |= FAULT_IMPLAUSIBLE_SIZE;
            }
        }

        // 3. Temporal consistency (compare with previous frame)
        if (!detections.empty() && !previous_detections_.empty()) {
            float motion_smoothness = compute_motion_smoothness(detections, previous_detections_);
            state.temporal_consistent = (motion_smoothness < MAX_MOTION_JERK);
            if (!state.temporal_consistent) {
                state.fault_codes |= FAULT_TEMPORAL_INCONSISTENCY;
            }
        }
        previous_detections_ = detections;

        return state;
    }

private:
    static constexpr float MIN_DENSITY_POINTS_PER_M3 = 5.0f;
    static constexpr float MAX_OBJECT_SPEED_MPS = 42.0f;  // ~150 km/h
    static constexpr float MIN_OBJECT_SIZE_M = 0.3f;
    static constexpr float MAX_OBJECT_SIZE_M = 25.0f;
    static constexpr float MAX_MOTION_JERK = 50.0f;  // m/s^3
    static constexpr uint32_t FAULT_LOW_POINT_DENSITY = (1 << 0);
    static constexpr uint32_t FAULT_IMPLAUSIBLE_VELOCITY = (1 << 1);
    static constexpr uint32_t FAULT_IMPLAUSIBLE_SIZE = (1 << 2);
    static constexpr uint32_t FAULT_TEMPORAL_INCONSISTENCY = (1 << 3);

    std::vector<Detection3D> previous_detections_;
};
```

---

## Performance Benchmarks

| Processing Stage | WCET (ms) | Platform | ASIL |
|-----------------|-----------|----------|------|
| Voxel downsampling | 2.0 | Jacinto TDA4VM C66x | B |
| Ground segmentation (RANSAC) | 3.0 | Jacinto TDA4VM C66x | B |
| PointPillars inference | 12.0 | Jetson Orin GPU | C |
| CenterPoint inference | 18.0 | Jetson Orin GPU | C |
| LiDAR-Camera fusion | 5.0 | Jacinto TDA4VM A72 | C |
| LOAM odometry | 8.0 | Jetson Orin CPU | B |
| Full pipeline (end-to-end) | < 30 ms | Jetson Orin | C |

---

## @-Mentions

- @context/skills/adas/sensor-fusion.md – EKF/UKF for LiDAR tracking
- @context/skills/adas/camera-processing.md – Camera branch for deep fusion
- @context/skills/adas/calibration.md – LiDAR-camera extrinsic calibration
- @knowledge/standards/iso26262/2-conceptual.md – ASIL decomposition for perception
- @knowledge/standards/iso21448/1-overview.md – SOTIF triggering conditions (adverse weather)

---

## References and Dependencies

```cpp
// Required dependencies:
// - Eigen 3.4+ for linear algebra
// - PCL 1.12+ for point cloud processing
// - OpenCV 4.8+ for camera image processing
// - CUDA 12.x + cuDNN 8.x for GPU acceleration
// - TensorRT 8.x for inference optimization
// - libpointmatcher or libnabo for ICP/nearest-neighbor
```
