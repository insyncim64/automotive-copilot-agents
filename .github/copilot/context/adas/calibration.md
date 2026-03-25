# Sensor Calibration for ADAS Systems

> **Standards Compliance:** ISO 26262 ASIL B/C (Calibration Quality), ISO 21448 SOTIF (Calibration Degradation Scenarios)
>
> **Purpose:** Extrinsic and intrinsic calibration methods for multi-sensor ADAS systems including Camera, LiDAR, Radar, and IMU sensors.

---

## Domain Expertise

| Calibration Type | Methods | Accuracy | Latency | ASIL Suitability |
|-----------------|---------|----------|---------|-----------------|
| **Target-Based** | Checkerboard, AprilTag, Spherical | < 2mm / < 0.1° | 1-5 min | ASIL B (Verified) |
| **Target-Less** | Natural Features, Motion-based | < 5mm / < 0.2° | 10-30 min | ASIL B (Validated) |
| **Online** | Continuous refinement, EKF-based | < 10mm / < 0.5° | Real-time | ASIL C (Monitored) |
| **Hand-Eye** | AX=XB solvers, multi-pose | < 3mm / < 0.15° | 5-15 min | ASIL B |
| **Multi-Sensor** | Joint optimization, bundle adj. | < 1mm / < 0.05° | 30-60 min | ASIL C (Redundant) |

---

## Calibration Fundamentals

### Intrinsic vs Extrinsic Parameters

```cpp
/**
 * @brief Sensor calibration parameter types
 * @safety ASIL B - Calibration quality affects perception accuracy
 */
struct CalibrationParameters {
    // Intrinsic parameters (internal to sensor)
    struct Intrinsic {
        // Camera: focal length, principal point, distortion
        float fx, fy;           // Focal length (pixels)
        float cx, cy;           // Principal point (pixels)
        float k1, k2, k3;       // Radial distortion coefficients
        float p1, p2;           // Tangential distortion coefficients

        // LiDAR: beam angles, range correction
        std::vector<float> beam_elevation_angles;  // Per-channel angles
        std::vector<float> beam_azimuth_offsets;   // Per-channel offsets
        std::vector<float> range_correction;       // Intensity correction

        // Radar: antenna pattern, range bias
        float range_bias_m;
        Eigen::Vector2f antenna_boresight;
        std::vector<float> element_phase_offsets;
    } intrinsic;

    // Extrinsic parameters (sensor pose in vehicle frame)
    struct Extrinsic {
        Eigen::Vector3f position;      // x, y, z (meters from vehicle origin)
        Eigen::Vector3f orientation;   // roll, pitch, yaw (radians)
        Eigen::Matrix4f transformation; // 4x4 homogeneous transform matrix

        // Vehicle coordinate system (ISO 8855):
        // +X: Forward, +Y: Left, +Z: Up
        // Origin: Rear axle center, ground plane
        bool is_valid;
        ara::core::TimeStamp last_calibration;
        CalibrationQuality quality;
    } extrinsic;

    // Calibration quality metrics
    struct Quality {
        float reprojection_error_px;   // Camera: pixels
        float point_to_plane_error_m;  // LiDAR: meters
        float range_residual_m;        // Radar: meters
        float consistency_score;       // 0.0 - 1.0 (multi-sensor agreement)
        CalibrationStatus status;      // VALID, DEGRADED, INVALID
    } quality;
};
```

### Coordinate Frames

```
Vehicle Frame (ISO 8855)
         Z (up)
         ^
         |
         |      Y (left)
         |     /
         |    /
         |   /
         |  /
         | /
         O--------> X (forward)
        /
       /
      /

Sensor Frames:
- Camera: Optical center, Z forward, X right, Y down
- LiDAR: Sensor center, Z up, X forward, Y left
- Radar: Antenna center, X forward, Y left, Z up
- IMU: Center of mass, X forward, Y left, Z up

Transformation chain:
Point_vehicle = T_vehicle_sensor × Point_sensor
```

---

## Target-Based Calibration

### Camera Intrinsic Calibration

```cpp
/**
 * @brief Camera intrinsic calibration using checkerboard patterns
 * @reference Zhang's method, OpenCV calibration
 * @safety ASIL B - Requires minimum 20 images, varied orientations
 */
class CameraIntrinsicCalibrator {
public:
    struct Config {
        size_t min_images = 20;
        size_t max_reprojection_error_px = 5;  // Maximum allowed error
        cv::Size checkerboard_size{9, 6};       // Inner corners
        float square_size_mm = 30.0f;           // Square physical size
    };

    struct CalibrationResult {
        cv::Mat camera_matrix;      // 3x3 intrinsic matrix
        cv::Mat dist_coeffs;        // Distortion coefficients (k1,k2,p1,p2,k3)
        float reprojection_error_px;
        std::vector<cv::Mat> rotation_vectors;  // Per-image extrinsics
        std::vector<cv::Mat> translation_vectors;
        bool is_valid;
        std::string validation_message;
    };

    CalibrationResult calibrate(const std::vector<cv::Mat>& images) {
        CalibrationResult result;

        if (images.size() < config_.min_images) {
            result.is_valid = false;
            result.validation_message =
                fmt::format("Insufficient images: {} < {}",
                           images.size(), config_.min_images);
            return result;
        }

        // Step 1: Detect checkerboard corners
        std::vector<std::vector<cv::Point2f>> image_points;
        std::vector<std::vector<cv::Point3f>> object_points;

        // Generate 3D object points (checkerboard in Z=0 plane)
        std::vector<cv::Point3f> obj_point;
        for (int i = 0; i < config_.checkerboard_size.height; ++i) {
            for (int j = 0; j < config_.checkerboard_size.width; ++j) {
                obj_point.emplace_back(
                    j * config_.square_size_mm,
                    i * config_.square_size_mm,
                    0.0f);
            }
        }

        // Detect corners in each image
        for (const auto& image : images) {
            std::vector<cv::Point2f> corners;
            bool found = cv::findChessboardCorners(
                image, config_.checkerboard_size, corners,
                cv::CALIB_CB_ADAPTIVE_THRESH |
                cv::CALIB_CB_NORMALIZE_IMAGE |
                cv::CALIB_CB_FAST_CHECK);

            if (found) {
                // Refine corner locations to sub-pixel accuracy
                cv::cornerSubPix(
                    image, corners, cv::Size(11, 11), cv::Size(-1, -1),
                    cv::TermCriteria(cv::TermCriteria::EPS +
                                    cv::TermCriteria::MAX_ITER, 30, 0.01));
                image_points.push_back(corners);
                object_points.push_back(obj_point);
            }
        }

        if (image_points.size() < config_.min_images) {
            result.is_valid = false;
            result.validation_message =
                fmt::format("Failed to detect corners in enough images: {} < {}",
                           image_points.size(), config_.min_images);
            return result;
        }

        // Step 2: Run calibration
        cv::Mat camera_matrix = cv::Mat::eye(3, 3, CV_64F);
        cv::Mat dist_coeffs = cv::Mat::zeros(8, 1, CV_64F);
        std::vector<cv::Mat> rvecs, tvecs;

        double rms_error = cv::calibrateCamera(
            object_points, image_points, image[0].size(),
            camera_matrix, dist_coeffs, rvecs, tvecs,
            cv::CALIB_USE_INTRINSIC_GUESS |
            cv::CALIB_FIX_K4 | cv::CALIB_FIX_K5);

        // Step 3: Validate results
        result.camera_matrix = camera_matrix;
        result.dist_coeffs = dist_coeffs;
        result.reprojection_error_px = static_cast<float>(rms_error);
        result.rotation_vectors = rvecs;
        result.translation_vectors = tvecs;

        if (rms_error > config_.max_reprojection_error_px) {
            result.is_valid = false;
            result.validation_message =
                fmt::format("Reprojection error too high: {:.2f} > {:.2f} px",
                           rms_error, config_.max_reprojection_error_px);
        } else {
            result.is_valid = true;
            result.validation_message = "Calibration successful";
        }

        return result;
    }

private:
    Config config_;
};
```

### Camera-LiDAR Extrinsic Calibration (Target-Based)

```cpp
/**
 * @brief Camera-LiDAR extrinsic calibration using checkerboard
 * @safety ASIL B - Requires validated calibration target
 * @req SSR-CALIB-001, SSR-CALIB-002
 */
class CameraLidarCalibrator {
public:
    struct CalibrationTarget {
        enum class Type { CHECKERBOARD, APRILTAG, CIRCLES };
        Type type;
        cv::Size grid_size;         // For checkerboard: inner corners
        float square_size_m;        // Physical square size
        Eigen::Matrix4f target_frame; // Target coordinate frame
    };

    struct CalibrationResult {
        Eigen::Matrix4f T_lidar_camera;  // LiDAR to Camera transform
        Eigen::Matrix4f T_camera_lidar;  // Camera to LiDAR transform
        float reprojection_error_px;     // LiDAR points projected to image
        float point_to_plane_error_m;    // LiDAR points to target plane
        bool is_valid;
        std::string validation_message;
    };

    /**
     * @brief Calibrate using multiple target poses
     * @param camera_images Synchronized camera images
     * @param lidar_pointclouds Synchronized LiDAR point clouds
     * @param target Calibration target specification
     * @return Calibration result with validity flag
     */
    CalibrationResult calibrate(
        const std::vector<cv::Mat>& camera_images,
        const std::vector<PointCloud>& lidar_pointclouds,
        const CalibrationTarget& target) {

        CalibrationResult result;

        if (camera_images.size() != lidar_pointclouds.size()) {
            result.is_valid = false;
            result.validation_message = "Image/point cloud count mismatch";
            return result;
        }

        // Collect correspondences from all poses
        std::vector<Eigen::Vector3f> target_points_lidar;
        std::vector<cv::Point3f> target_points_camera;
        std::vector<cv::Point2f> image_corners;

        for (size_t i = 0; i < camera_images.size(); ++i) {
            // Step 1: Detect target in camera image
            std::vector<cv::Point2f> corners;
            if (!detect_target_in_image(camera_images[i], target, corners)) {
                Dem_ReportErrorStatus(DEM_CALIB_TARGET_NOT_FOUND_IMAGE);
                continue;
            }

            // Step 2: Detect target plane in LiDAR point cloud
            PlaneFitResult plane = detect_target_in_lidar(lidar_pointclouds[i]);
            if (!plane.is_valid) {
                Dem_ReportErrorStatus(DEM_CALIB_TARGET_NOT_FOUND_LIDAR);
                continue;
            }

            // Step 3: Extract target corner points in LiDAR frame
            auto lidar_corners = extract_target_corners_lidar(
                lidar_pointclouds[i], plane, target);

            // Step 4: Store correspondences
            for (size_t j = 0; j < corners.size() && j < lidar_corners.size(); ++j) {
                target_points_lidar.push_back(lidar_corners[j]);
                target_points_camera.push_back(cv::Point3f(
                    lidar_corners[j].x(), lidar_corners[j].y(), lidar_corners[j].z()));
            }
            for (const auto& corner : corners) {
                image_corners.push_back(corner);
            }
        }

        if (target_points_lidar.size() < 20) {
            result.is_valid = false;
            result.validation_message =
                fmt::format("Insufficient correspondences: {}",
                           target_points_lidar.size());
            return result;
        }

        // Step 5: Solve for extrinsic transform using PnP
        cv::Mat camera_matrix, dist_coeffs;
        load_camera_intrinsics(camera_matrix, dist_coeffs);

        cv::Mat rvec, tvec;
        bool success = cv::solvePnP(
            target_points_camera, image_corners,
            camera_matrix, dist_coeffs, rvec, tvec);

        if (!success) {
            result.is_valid = false;
            result.validation_message = "PnP optimization failed";
            return result;
        }

        // Convert to Eigen
        Eigen::Matrix3f R;
        cv::Rodrigues(rvec, R);
        Eigen::Matrix4f T_camera_target = Eigen::Matrix4f::Identity();
        T_camera_target.block<3, 3>(0, 0) = R;
        T_camera_target.block<3, 1>(0, 3) = Eigen::Vector3f(
            tvec.at<double>(0), tvec.at<double>(1), tvec.at<double>(2));

        // Compute LiDAR to target transform from plane
        Eigen::Matrix4f T_lidar_target = compute_target_transform_from_lidar(
            target_points_lidar);

        // Final: T_lidar_camera = T_lidar_target × T_camera_target^(-1)
        result.T_lidar_camera = T_lidar_target * T_camera_target.inverse();
        result.T_camera_lidar = result.T_lidar_camera.inverse();

        // Step 6: Validate calibration quality
        result.reprojection_error_px = compute_reprojection_error(
            target_points_lidar, image_corners, result.T_lidar_camera,
            camera_matrix, dist_coeffs);

        result.point_to_plane_error_m = compute_point_to_plane_error(
            target_points_lidar);

        if (result.reprojection_error_px > 5.0f) {
            result.is_valid = false;
            result.validation_message =
                fmt::format("Reprojection error too high: {:.2f} px",
                           result.reprojection_error_px);
        } else if (result.point_to_plane_error_m > 0.02f) {
            result.is_valid = false;
            result.validation_message =
                fmt::format("Point-to-plane error too high: {:.3f} m",
                           result.point_to_plane_error_m);
        } else {
            result.is_valid = true;
            result.validation_message = "Calibration successful";
        }

        return result;
    }

private:
    bool detect_target_in_image(const cv::Mat& image,
                                 const CalibrationTarget& target,
                                 std::vector<cv::Point2f>& corners) {
        switch (target.type) {
            case CalibrationTarget::Type::CHECKERBOARD:
                return cv::findChessboardCorners(
                    image, target.grid_size, corners,
                    cv::CALIB_CB_ADAPTIVE_THRESH | cv::CALIB_CB_NORMALIZE_IMAGE);
            case CalibrationTarget::Type::APRILTAG:
                // Use AprilTag library
                return detect_apriltag_corners(image, target, corners);
            case CalibrationTarget::Type::CIRCLES:
                return cv::findCirclesGrid(
                    image, target.grid_size, corners,
                    cv::CALIB_CB_SYMMETRIC_GRID);
            default:
                return false;
        }
    }

    struct PlaneFitResult {
        Eigen::Vector3f normal;
        Eigen::Vector3f point_on_plane;
        float rms_error_m;
        bool is_valid;
    };

    PlaneFitResult detect_target_in_lidar(const PointCloud& cloud) {
        PlaneFitResult result;

        // RANSAC plane fitting
        pcl::SACSegmentation<pcl::PointXYZ> seg;
        seg.setOptimizeCoefficients(true);
        seg.setModelType(pcl::SACMODEL_PLANE);
        seg.setMethodType(pcl::SAC_RANSAC);
        seg.setDistanceThreshold(0.05f);  // 5 cm threshold

        pcl::PointCloud<pcl::PointXYZ>::Ptr cloud_pcl(
            new pcl::PointCloud<pcl::PointXYZ>);
        to_pcl(cloud, *cloud_pcl);

        pcl::ModelCoefficients::Ptr coefficients(
            new pcl::ModelCoefficients);
        pcl::PointIndices::Ptr inliers(
            new pcl::PointIndices);

        seg.setInputCloud(cloud_pcl);
        seg.segment(*inliers, *coefficients);

        if (inliers->indices.size() < 100) {
            result.is_valid = false;
            return result;
        }

        result.normal = Eigen::Vector3f(
            coefficients->values[0],
            coefficients->values[1],
            coefficients->values[2]);
        result.point_on_plane = Eigen::Vector3f(
            coefficients->values[3] * result.normal.x(),
            coefficients->values[3] * result.normal.y(),
            coefficients->values[3] * result.normal.z());
        result.is_valid = true;

        return result;
    }

    std::vector<Eigen::Vector3f> extract_target_corners_lidar(
        const PointCloud& cloud,
        const PlaneFitResult& plane,
        const CalibrationTarget& target) {

        // Project points to plane, find boundary, extract corners
        std::vector<Eigen::Vector3f> corners;

        // Extract planar cluster
        auto planar_points = extract_planar_cluster(cloud, plane);

        // Find 2D bounding box in plane coordinates
        auto corners_2d = find_bounding_box_corners_2d(planar_points, plane);

        // Scale to physical size based on target specification
        corners = scale_corners_to_target_size(corners_2d, target);

        return corners;
    }

    float compute_reprojection_error(
        const std::vector<Eigen::Vector3f>& points_lidar,
        const std::vector<cv::Point2f>& image_points,
        const Eigen::Matrix4f& T_lidar_camera,
        const cv::Mat& camera_matrix,
        const cv::Mat& dist_coeffs) {

        double total_error = 0.0;
        size_t count = 0;

        for (size_t i = 0; i < points_lidar.size(); ++i) {
            // Transform LiDAR point to camera frame
            Eigen::Vector4f p_lidar(points_lidar[i].x(), points_lidar[i].y(),
                                     points_lidar[i].z(), 1.0f);
            Eigen::Vector4f p_camera = T_lidar_camera * p_lidar;

            // Project to image
            cv::Point3f p_cam(p_camera.x(), p_camera.y(), p_camera.z());
            std::vector<cv::Point2f> projected;
            cv::projectPoints({p_cam}, cv::Mat::zeros(3, 1, CV_64F),
                             cv::Mat::zeros(3, 1, CV_64F),
                             camera_matrix, dist_coeffs, projected);

            // Compute error
            float dx = projected[0].x - image_points[i].x;
            float dy = projected[0].y - image_points[i].y;
            total_error += std::sqrt(dx*dx + dy*dy);
            count++;
        }

        return count > 0 ? static_cast<float>(total_error / count) : 0.0f;
    }

    float compute_point_to_plane_error(
        const std::vector<Eigen::Vector3f>& points_lidar) {

        // Fit plane to all points, compute RMS distance
        Eigen::Vector3f centroid = compute_centroid(points_lidar);
        Eigen::Matrix3f cov = compute_covariance(points_lidar, centroid);

        // Eigen decomposition for normal
        Eigen::SelfAdjointEigenSolver<Eigen::Matrix3f> solver(cov);
        Eigen::Vector3f normal = solver.eigenvectors().col(0);

        // Compute RMS error
        double total_error = 0.0;
        for (const auto& point : points_lidar) {
            float dist = std::abs(normal.dot(point - centroid));
            total_error += dist * dist;
        }

        return std::sqrt(total_error / points_lidar.size());
    }
};
```

---

## Target-Less Calibration

### Motion-Based Calibration (Hand-Eye)

```cpp
/**
 * @brief Hand-eye calibration using sensor motion
 * @description Solves AX=XB for sensor mounted on moving platform
 * @safety ASIL B - Requires diverse motion patterns
 * @req SSR-CALIB-010
 */
class HandEyeCalibrator {
public:
    /**
     * @brief AX=XB calibration problem
     *
     * A: Motion of first sensor (e.g., camera) between poses
     * B: Motion of second sensor (e.g., LiDAR) between poses
     * X: Unknown transformation between sensors (what we solve for)
     *
     * Equation: A × X = X × B
     */
    struct MotionPair {
        Eigen::Matrix4f A;  // Motion of sensor 1 (from pose i to i+1)
        Eigen::Matrix4f B;  // Motion of sensor 2 (from pose i to i+1)
        float rotation_angle_rad;  // Rotation magnitude for quality check
    };

    struct CalibrationResult {
        Eigen::Matrix4f X;  // Transformation: sensor2 -> sensor1
        float rotation_error_rad;
        float translation_error_m;
        size_t motion_pairs_used;
        bool is_valid;
        std::string validation_message;
    };

    /**
     * @brief Solve AX=XB using Daniilidis method (dual quaternions)
     * @param motion_pairs Corresponding motions from both sensors
     * @return Calibration result
     */
    CalibrationResult calibrate_daniilidis(
        const std::vector<MotionPair>& motion_pairs) {

        CalibrationResult result;

        if (motion_pairs.size() < 3) {
            result.is_valid = false;
            result.validation_message = "Need at least 3 motion pairs";
            return result;
        }

        // Step 1: Filter motion pairs with sufficient rotation
        std::vector<MotionPair> valid_pairs;
        for (const auto& pair : motion_pairs) {
            if (pair.rotation_angle_rad > 0.1f) {  // > 5 degrees
                valid_pairs.push_back(pair);
            }
        }

        if (valid_pairs.size() < 3) {
            result.is_valid = false;
            result.validation_message =
                "Insufficient rotational motion in data";
            return result;
        }

        // Step 2: Build linear system from dual quaternions
        // Using Daniilidis formulation: Ax = b
        // where x encodes rotation and translation of X

        Eigen::MatrixXf A(valid_pairs.size() * 6, 8);
        Eigen::VectorXf b(valid_pairs.size() * 6);

        for (size_t i = 0; i < valid_pairs.size(); ++i) {
            const auto& pair = valid_pairs[i];

            // Extract rotation matrices
            Eigen::Matrix3f RA = pair.A.block<3, 3>(0, 0);
            Eigen::Matrix3f RB = pair.B.block<3, 3>(0, 0);

            // Convert to angle-axis
            Eigen::AngleAxisf axisA(RA);
            Eigen::AngleAxisf axisB(RB);

            // Build dual quaternion constraints
            // See: Daniilidis, "Hand-Eye Calibration Using Dual Quaternions"
            build_dual_quaternion_constraints(
                axisA, axisB, A.block(i * 6, 0, 6, 8));
        }

        // Step 3: Solve using SVD
        Eigen::JacobiSVD<Eigen::MatrixXf> svd(
            A, Eigen::ComputeFullU | Eigen::ComputeFullV);
        Eigen::VectorXf x = svd.matrixV().col(7);  // Last column (min singular value)

        // Step 4: Extract rotation and translation from solution
        Eigen::Matrix3f R_X;
        Eigen::Vector3f t_X;
        extract_rotation_translation_from_dq(x, R_X, t_X);

        result.X = Eigen::Matrix4f::Identity();
        result.X.block<3, 3>(0, 0) = R_X;
        result.X.block<3, 1>(0, 3) = t_X;

        // Step 5: Validate result
        auto errors = compute_calibration_errors(valid_pairs, result.X);
        result.rotation_error_rad = errors.rotation_error;
        result.translation_error_m = errors.translation_error;
        result.motion_pairs_used = valid_pairs.size();

        if (errors.rotation_error_rad > 0.05f) {  // > 3 degrees
            result.is_valid = false;
            result.validation_message =
                fmt::format("Rotation error too high: {:.2f} deg",
                           errors.rotation_error_rad * 180.0f / M_PI);
        } else if (errors.translation_error_m > 0.05f) {  // > 5 cm
            result.is_valid = false;
            result.validation_message =
                fmt::format("Translation error too high: {:.3f} m",
                           errors.translation_error_m);
        } else {
            result.is_valid = true;
            result.validation_message = "Hand-eye calibration successful";
        }

        return result;
    }

    /**
     * @brief Solve AX=XB using Tsai-Lenz method (Kronecker product)
     * @note More robust to noise than Daniilidis but slightly less accurate
     */
    CalibrationResult calibrate_tsai_lenz(
        const std::vector<MotionPair>& motion_pairs) {

        // Two-step approach:
        // 1. Solve for rotation using Kronecker product formulation
        // 2. Solve for translation using least squares

        CalibrationResult result;

        // Step 1: Rotation estimation
        Eigen::Matrix3f sum_A = Eigen::Matrix3f::Zero();
        Eigen::Matrix3f sum_B = Eigen::Matrix3f::Zero();

        for (const auto& pair : motion_pairs) {
            Eigen::Matrix3f RA = pair.A.block<3, 3>(0, 0);
            Eigen::Matrix3f RB = pair.B.block<3, 3>(0, 0);

            // Tsai-Lenz: sum of (RA - I) and (RB - I)
            sum_A += (RA - Eigen::Matrix3f::Identity());
            sum_B += (RB - Eigen::Matrix3f::Identity());
        }

        // Build Kronecker system: (I - RA) ⊗ (I - RB^T) vec(RX) = 0
        Eigen::MatrixXf K = build_kronecker_system(motion_pairs);

        // Solve using SVD
        Eigen::JacobiSVD<Eigen::MatrixXf> svd(
            K, Eigen::ComputeFullU | Eigen::ComputeFullV);
        Eigen::VectorXf r_vec = svd.matrixV().col(8);

        Eigen::Matrix3f R_X = Eigen::Map<Eigen::Matrix3f>(r_vec.data());

        // Enforce orthonormality via SVD projection
        Eigen::JacobiSVD<Eigen::Matrix3f> svd_R(
            R_X, Eigen::ComputeFullU | Eigen::ComputeFullV);
        R_X = svd_R.matrixU() * svd_R.matrixV().transpose();

        // Step 2: Translation estimation
        Eigen::MatrixXf A_t(motion_pairs.size() * 3, 3);
        Eigen::VectorXf b_t(motion_pairs.size() * 3);

        for (size_t i = 0; i < motion_pairs.size(); ++i) {
            Eigen::Matrix3f RA = motion_pairs[i].A.block<3, 3>(0, 0);
            Eigen::Vector3f tA = motion_pairs[i].A.block<3, 1>(0, 3);
            Eigen::Vector3f tB = motion_pairs[i].B.block<3, 1>(0, 3);

            A_t.block(i * 3, 0, 3, 3) = (RA - Eigen::Matrix3f::Identity());
            b_t.segment(i * 3, 3) = RA * t_X - tA + R_X * tB;
        }

        Eigen::Vector3f t_X = A_t.colPivHouseholderQr().solve(b_t);

        result.X = Eigen::Matrix4f::Identity();
        result.X.block<3, 3>(0, 0) = R_X;
        result.X.block<3, 1>(0, 3) = t_X;

        // Validate
        result.is_valid = true;
        result.validation_message = "Tsai-Lenz calibration complete";

        return result;
    }

private:
    void build_dual_quaternion_constraints(
        const Eigen::AngleAxisf& axisA,
        const Eigen::AngleAxisf& axisB,
        Eigen::Map<Eigen::MatrixXf> A_block) {

        // Dual quaternion representation of rotation
        // q = [cos(theta/2), sin(theta/2) * axis]

        float thetaA = axisA.angle();
        float thetaB = axisB.angle();

        Eigen::Vector3f rA = std::sin(thetaA / 2.0f) * axisA.axis();
        Eigen::Vector3f rB = std::sin(thetaB / 2.0f) * axisB.axis();

        float sA = std::cos(thetaA / 2.0f);
        float sB = std::cos(thetaB / 2.0f);

        // Build constraint matrix for rotation
        // See Daniilidis paper for derivation
        A_block.block<3, 4>(0, 0) = build_rotation_constraint(rA, rB, sA, sB);
        A_block.block<3, 4>(3, 0) = build_translation_constraint(rA, rB, sA, sB);
    }

    struct CalibrationErrors {
        float rotation_error_rad;
        float translation_error_m;
    };

    CalibrationErrors compute_calibration_errors(
        const std::vector<MotionPair>& pairs,
        const Eigen::Matrix4f& X) {

        CalibrationErrors errors;
        double rot_error_sum = 0.0;
        double trans_error_sum = 0.0;

        for (const auto& pair : pairs) {
            // Check: A * X ≈ X * B
            Eigen::Matrix4f AX = pair.A * X;
            Eigen::Matrix4f XB = X * pair.B;

            // Rotation error
            Eigen::Matrix3f R_error = AX.block<3, 3>(0, 0).transpose() *
                                      XB.block<3, 3>(0, 0);
            Eigen::AngleAxisf aa(R_error);
            rot_error_sum += std::abs(aa.angle());

            // Translation error
            Eigen::Vector3f t_error = AX.block<3, 1>(0, 3) -
                                      XB.block<3, 1>(0, 3);
            trans_error_sum += t_error.norm();
        }

        errors.rotation_error_rad =
            static_cast<float>(rot_error_sum / pairs.size());
        errors.translation_error_m =
            static_cast<float>(trans_error_sum / pairs.size());

        return errors;
    }
};
```

### Natural Feature Calibration (Target-Less)

```cpp
/**
 * @brief Target-less calibration using natural features
 * @description Uses environmental features (building edges, poles, etc.)
 * @safety ASIL B - Requires feature-rich environment
 * @req SSR-CALIB-015
 */
class NaturalFeatureCalibrator {
public:
    struct Config {
        float min_feature_distance_m = 5.0f;
        float max_feature_distance_m = 50.0f;
        size_t min_features = 100;
        float ransac_inlier_ratio = 0.6f;
        float ransac_threshold_m = 0.1f;
    };

    struct FeatureCorrespondence {
        Eigen::Vector3f point_camera;  // From camera (triangulated)
        Eigen::Vector3f point_lidar;   // From LiDAR
        float descriptor_distance;     // Feature similarity
    };

    struct CalibrationResult {
        Eigen::Matrix4f T_lidar_camera;
        size_t correspondences_used;
        float inlier_ratio;
        float reprojection_error_px;
        bool is_valid;
        std::string validation_message;
    };

    CalibrationResult calibrate(
        const std::vector<cv::Mat>& camera_images,
        const std::vector<PointCloud>& lidar_clouds,
        const std::vector<Eigen::Matrix4f>& vehicle_poses) {

        CalibrationResult result;

        // Step 1: Extract features from each sensor
        std::vector<FeatureSet> camera_features;
        std::vector<FeatureSet> lidar_features;

        for (size_t i = 0; i < camera_images.size(); ++i) {
            auto cam_feat = extract_camera_features(camera_images[i]);
            auto lidar_feat = extract_lidar_features(lidar_clouds[i]);
            camera_features.push_back(cam_feat);
            lidar_features.push_back(lidar_feat);
        }

        // Step 2: Match features across sensors using appearance + geometry
        std::vector<FeatureCorrespondence> correspondences;

        for (size_t i = 0; i < camera_features.size(); ++i) {
            auto matches = match_features(
                camera_features[i], lidar_features[i], vehicle_poses[i]);
            correspondences.insert(correspondences.end(),
                                   matches.begin(), matches.end());
        }

        if (correspondences.size() < config_.min_features) {
            result.is_valid = false;
            result.validation_message =
                fmt::format("Insufficient features: {} < {}",
                           correspondences.size(), config_.min_features);
            return result;
        }

        // Step 3: RANSAC optimization
        std::vector<size_t> inliers;
        Eigen::Matrix4f best_transform;

        ransac_optimize(correspondences, config_.ransac_threshold_m,
                       config_.ransac_inlier_ratio, 1000,
                       inliers, best_transform);

        if (inliers.size() < config_.min_features) {
            result.is_valid = false;
            result.validation_message =
                fmt::format("Insufficient RANSAC inliers: {}", inliers.size());
            return result;
        }

        result.T_lidar_camera = best_transform;
        result.correspondences_used = inliers.size();
        result.inlier_ratio = static_cast<float>(inliers.size()) /
                              correspondences.size();

        // Step 4: Refine using non-linear optimization
        result.T_lidar_camera = refine_calibration(
            correspondences, inliers, result.T_lidar_camera);

        // Step 5: Validate
        result.reprojection_error_px = compute_reprojection_error(
            correspondences, inliers, result.T_lidar_camera);

        if (result.inlier_ratio < 0.4f) {
            result.is_valid = false;
            result.validation_message =
                fmt::format("Inlier ratio too low: {:.1f}%",
                           result.inlier_ratio * 100.0f);
        } else if (result.reprojection_error_px > 5.0f) {
            result.is_valid = false;
            result.validation_message =
                fmt::format("Reprojection error too high: {:.2f} px",
                           result.reprojection_error_px);
        } else {
            result.is_valid = true;
            result.validation_message = "Natural feature calibration successful";
        }

        return result;
    }

private:
    struct FeatureSet {
        std::vector<Eigen::Vector3f> points;     // 3D positions
        std::vector<Eigen::VectorXf> descriptors; // Feature descriptors
        std::vector<size_t> descriptors;          // Feature IDs
    };

    FeatureSet extract_camera_features(const cv::Mat& image) {
        FeatureSet features;

        // Use ORB features (fast, robust)
        cv::Ptr<cv::ORB> orb = cv::ORB::create(1000);
        std::vector<cv::KeyPoint> keypoints;
        cv::Mat descriptors;
        orb->detectAndCompute(image, cv::noArray(), keypoints, descriptors);

        // Note: For 3D points, need stereo or temporal triangulation
        // This is a simplified example
        for (const auto& kp : keypoints) {
            features.points.emplace_back(kp.pt.x, kp.pt.y, 1.0f);  // Simplified
            Eigen::VectorXf desc(32);
            for (int i = 0; i < 32; ++i) {
                desc(i) = static_cast<float>(descriptors.row(0)(i));
            }
            features.descriptors.push_back(desc);
        }

        return features;
    }

    FeatureSet extract_lidar_features(const PointCloud& cloud) {
        FeatureSet features;

        // Extract geometric features (edges, corners)
        // Using point cloud curvature
        for (const auto& point : cloud.points) {
            float curvature = compute_point_curvature(cloud, point);
            if (curvature > 0.1f) {  // Edge/corner feature
                features.points.push_back(point);
                Eigen::VectorXf desc = compute_lidar_descriptor(cloud, point);
                features.descriptors.push_back(desc);
            }
        }

        return features;
    }

    std::vector<FeatureCorrespondence> match_features(
        const FeatureSet& camera,
        const FeatureSet& lidar,
        const Eigen::Matrix4f& initial_guess) {

        std::vector<FeatureCorrespondence> matches;

        // Match using descriptor similarity + geometric consistency
        for (size_t i = 0; i < camera.points.size(); ++i) {
            size_t best_match = 0;
            float best_distance = std::numeric_limits<float>::max();

            for (size_t j = 0; j < lidar.points.size(); ++j) {
                float dist = (camera.descriptors[i] - lidar.descriptors[j]).norm();
                if (dist < best_distance) {
                    best_distance = dist;
                    best_match = j;
                }
            }

            if (best_distance < 0.5f) {  // Descriptor threshold
                FeatureCorrespondence corr;
                corr.point_camera = camera.points[i];
                corr.point_lidar = lidar.points[best_match];
                corr.descriptor_distance = best_distance;
                matches.push_back(corr);
            }
        }

        return matches;
    }

    void ransac_optimize(
        const std::vector<FeatureCorrespondence>& correspondences,
        float threshold_m, float target_inlier_ratio, size_t max_iterations,
        std::vector<size_t>& inliers, Eigen::Matrix4f& transform) {

        // Standard RANSAC loop
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dist(0, correspondences.size() - 1);

        size_t best_inlier_count = 0;

        for (size_t iter = 0; iter < max_iterations; ++iter) {
            // Sample minimal set (3 correspondences for 6-DOF)
            std::vector<FeatureCorrespondence> sample;
            for (int i = 0; i < 3; ++i) {
                sample.push_back(correspondences[dist(gen)]);
            }

            // Estimate transform from sample
            Eigen::Matrix4f candidate = estimate_from_correspondences(sample);

            // Count inliers
            std::vector<size_t> current_inliers;
            for (size_t i = 0; i < correspondences.size(); ++i) {
                auto corr = correspondences[i];
                Eigen::Vector3f projected =
                    (candidate * Eigen::Vector4f(
                        corr.point_lidar.x(), corr.point_lidar.y(),
                        corr.point_lidar.z(), 1.0f)).head<3>();

                float error = (projected - corr.point_camera).norm();
                if (error < threshold_m) {
                    current_inliers.push_back(i);
                }
            }

            if (current_inliers.size() > best_inlier_count) {
                best_inlier_count = current_inliers.size();
                inliers = current_inliers;
                transform = candidate;

                if (static_cast<float>(best_inlier_count) /
                    correspondences.size() >= target_inlier_ratio) {
                    break;  // Early exit
                }
            }
        }
    }

    Eigen::Matrix4f refine_calibration(
        const std::vector<FeatureCorrespondence>& correspondences,
        const std::vector<size_t>& inliers,
        const Eigen::Matrix4f& initial_transform) {

        // Non-linear optimization using Ceres or g2o
        // Minimize reprojection error over all inliers

        Eigen::Matrix4f refined = initial_transform;

        // Simplified: Iterative closest point (ICP) refinement
        for (int iter = 0; iter < 10; ++iter) {
            Eigen::MatrixXf A(inliers.size() * 3, 6);
            Eigen::VectorXf b(inliers.size() * 3);

            for (size_t i = 0; i < inliers.size(); ++i) {
                auto corr = correspondences[inliers[i]];

                // Build Jacobian for SE(3) update
                Eigen::Vector3f p = refined.block<3, 3>(0, 0) *
                                    corr.point_lidar + refined.block<3, 1>(0, 3);
                Eigen::Vector3f residual = p - corr.point_camera;

                // Jacobian w.r.t. rotation and translation
                A.block(i * 3, 0, 3, 3) = -skew_symmetric(p);
                A.block(i * 3, 3, 3, 3) = -Eigen::Matrix3f::Identity();
                b.segment(i * 3, 3) = residual;
            }

            // Solve for update
            Eigen::Vector6f delta = A.colPivHouseholderQr().solve(b);

            // Apply update
            Eigen::Matrix3f R_delta;
            rodrigues_formula(delta.head<3>(), R_delta);
            refined.block<3, 3>(0, 0) *= R_delta;
            refined.block<3, 1>(0, 3) += delta.tail<3>();
        }

        return refined;
    }
};
```

---

## Online Calibration

### Real-Time Extrinsic Refinement

```cpp
/**
 * @brief Online calibration for continuous extrinsic refinement
 * @description Monitors and corrects extrinsic parameters during operation
 * @safety ASIL C - Continuous monitoring with degradation detection
 * @req SSR-CALIB-020, SSR-CALIB-021
 */
class OnlineCalibrationMonitor {
public:
    struct Config {
        float update_rate_hz = 1.0f;          // Calibration update frequency
        float convergence_threshold_m = 0.01f; // Convergence criterion
        float max_correction_per_step_m = 0.005f; // Max change per update
        size_t sliding_window_size = 100;     // Frames for optimization
        float outlier_threshold_m = 0.2f;     // Outlier rejection
        float quality_degradation_threshold = 0.3f; // When to flag invalid
    };

    struct CalibrationState {
        Eigen::Matrix4f T_lidar_camera;      // Current estimate
        Eigen::Matrix12f covariance;         // Uncertainty estimate
        ara::core::TimeStamp last_update;
        size_t frames_processed;
        CalibrationQuality quality;
        bool is_converged;
    };

    class OnlineCalibrator {
    public:
        OnlineCalibrator(const Config& config) : config_(config) {
            state_.T_lidar_camera = Eigen::Matrix4f::Identity();
            state_.covariance = Eigen::Matrix12f::Identity() * 0.01;
            state_.quality = CalibrationQuality::UNKNOWN;
            state_.is_converged = false;
        }

        /**
         * @brief Process new sensor data and update calibration
         * @param camera_image Synchronized camera image
         * @param lidar_cloud Synchronized LiDAR point cloud
         * @return Updated calibration state
         */
        CalibrationState update(const cv::Mat& camera_image,
                                 const PointCloud& lidar_cloud) {

            // Step 1: Extract features from current frame
            auto features = extract_calibration_features(
                camera_image, lidar_cloud);

            if (features.correspondences.size() < 20) {
                // Insufficient features - maintain current estimate
                state_.quality = CalibrationQuality::DEGRADED;
                return state_;
            }

            // Step 2: Add to sliding window
            feature_buffer_.push_back(features);
            if (feature_buffer_.size() > config_.sliding_window_size) {
                feature_buffer_.pop_front();
            }

            // Step 3: Optimize calibration using all frames in window
            if (feature_buffer_.size() >= 20) {
                auto [new_transform, new_covariance] =
                    optimize_calibration(feature_buffer_);

                // Step 4: Apply bounded correction
                Eigen::Vector3f delta_t = compute_translation_delta(
                    state_.T_lidar_camera, new_transform);
                Eigen::Vector3f delta_r = compute_rotation_delta(
                    state_.T_lidar_camera, new_transform);

                // Limit correction magnitude
                delta_t = clamp_vector(delta_t, config_.max_correction_per_step_m);
                delta_r = clamp_vector(delta_r, 0.01f);  // 0.01 rad limit

                // Apply correction
                Eigen::Matrix4f correction =
                    create_transform_from_delta(delta_r, delta_t);
                state_.T_lidar_camera = new_transform * correction;
                state_.covariance = new_covariance;
                state_.last_update = ara::core::TimeStamp::now();
                state_.frames_processed++;

                // Check convergence
                if (delta_t.norm() < config_.convergence_threshold_m &&
                    delta_r.norm() < 0.001f) {
                    state_.is_converged = true;
                    state_.quality = CalibrationQuality::VALID;
                }
            }

            // Step 5: Quality monitoring
            monitor_calibration_quality();

            return state_;
        }

        /**
         * @brief Get current calibration state
         */
        CalibrationState get_state() const {
            return state_;
        }

        /**
         * @brief Check if calibration is valid for use
         */
        bool is_valid() const {
            return state_.quality == CalibrationQuality::VALID ||
                   state_.quality == CalibrationQuality::DEGRADED;
        }

    private:
        Config config_;
        CalibrationState state_;
        std::deque<FeatureSet> feature_buffer_;

        struct FeatureSet {
            std::vector<Eigen::Vector3f> lidar_points;
            std::vector<cv::Point2f> image_points;
            std::vector<Eigen::Vector3f> descriptors;
            ara::core::TimeStamp timestamp;
        };

        FeatureSet extract_calibration_features(
            const cv::Mat& image, const PointCloud& cloud) {

            FeatureSet features;

            // Extract edges and corners from LiDAR
            auto lidar_features = extract_lidar_edges_corners(cloud);
            features.lidar_points = lidar_features.points;
            features.descriptors = lidar_features.descriptors;

            // Project LiDAR points to image using current calibration
            for (const auto& lidar_point : lidar_features.points) {
                Eigen::Vector4f p_cam =
                    state_.T_lidar_camera *
                    Eigen::Vector4f(lidar_point.x(), lidar_point.y(),
                                     lidar_point.z(), 1.0f);

                // Check if in front of camera
                if (p_cam.z() > 0.5f) {
                    // Project using camera intrinsics
                    cv::Point2f img_point(
                        p_cam.x() / p_cam.z(),
                        p_cam.y() / p_cam.z());

                    if (image.cols > img_point.x && img_point.x > 0 &&
                        image.rows > img_point.y && img_point.y > 0) {
                        features.image_points.push_back(img_point);
                    }
                }
            }

            features.timestamp = ara::core::TimeStamp::now();
            return features;
        }

        std::pair<Eigen::Matrix4f, Eigen::Matrix12f> optimize_calibration(
            const std::deque<FeatureSet>& buffer) {

            // Extended Kalman Filter for online calibration
            // State: [tx, ty, tz, rx, ry, rz] (6-DOF extrinsic)

            Eigen::Matrix<float, 6, 1> state;
            state.setZero();  // Start from current estimate

            Eigen::Matrix<float, 6, 6> P = state_.covariance.topLeftCorner<6, 6>();

            for (const auto& features : buffer) {
                // Prediction step (random walk model)
                Eigen::Matrix<float, 6, 6> F =
                    Eigen::Matrix<float, 6, 6>::Identity();
                Eigen::Matrix<float, 6, 6> Q =
                    Eigen::Matrix<float, 6, 6>::Identity() * 1e-6;

                P = F * P * F.transpose() + Q;

                // Update step
                if (features.lidar_points.size() >= 10) {
                    // Compute measurement Jacobian
                    Eigen::MatrixXf H;
                    Eigen::VectorXf z;
                    compute_measurement_jacobian(features, state, H, z);

                    // Kalman update
                    Eigen::Matrix6f R =
                        Eigen::Matrix6f::Identity() * 0.001;  // Measurement noise
                    Eigen::Matrix6f S = H * P * H.transpose() + R;
                    Eigen::Matrix6f K = P * H.transpose() * S.inverse();

                    state = state + K * z;
                    P = (Eigen::Matrix6f::Identity() - K * H) * P;
                }
            }

            // Convert state to transform
            Eigen::Matrix4f T = create_transform_from_state(state);

            return {T, P};
        }

        void monitor_calibration_quality() {
            // Monitor for calibration degradation
            float reprojection_error = compute_current_reprojection_error();

            if (reprojection_error > 10.0f) {
                state_.quality = CalibrationQuality::INVALID;
                Dem_ReportErrorStatus(DEM_CALIBRATION_INVALID);
            } else if (reprojection_error > 5.0f) {
                state_.quality = CalibrationQuality::DEGRADED;
            } else {
                state_.quality = CalibrationQuality::VALID;
            }
        }

        float compute_current_reprojection_error() {
            // Compute reprojection error for latest features
            if (feature_buffer_.empty()) return 0.0f;

            const auto& features = feature_buffer_.back();
            double total_error = 0.0;
            size_t count = 0;

            for (size_t i = 0; i < features.lidar_points.size(); ++i) {
                Eigen::Vector4f p_cam =
                    state_.T_lidar_camera *
                    Eigen::Vector4f(features.lidar_points[i].x(),
                                     features.lidar_points[i].y(),
                                     features.lidar_points[i].z(), 1.0f);

                cv::Point2f projected(p_cam.x() / p_cam.z(),
                                      p_cam.y() / p_cam.z());

                if (i < features.image_points.size()) {
                    float dx = projected.x - features.image_points[i].x;
                    float dy = projected.y - features.image_points[i].y;
                    total_error += std::sqrt(dx*dx + dy*dy);
                    count++;
                }
            }

            return count > 0 ? static_cast<float>(total_error / count) : 0.0f;
        }
    };
};
```

### Calibration Validity Monitoring

```cpp
/**
 * @brief Monitor calibration health and detect degradation
 * @safety ASIL C - Triggers recalibration when quality degrades
 */
class CalibrationHealthMonitor {
public:
    struct HealthStatus {
        CalibrationQuality overall_quality;
        float reprojection_error_px;
        float temporal_consistency_score;  // 0.0 - 1.0
        float multi_sensor_agreement;      // 0.0 - 1.0
        std::chrono::milliseconds time_since_last_calib;
        bool requires_recalibration;
        std::string diagnostic_message;
    };

    HealthStatus check_health(const CalibrationState& state,
                               const SensorData& latest_data) {

        HealthStatus status;
        status.time_since_last_calib =
            std::chrono::duration_cast<std::chrono::milliseconds>(
                ara::core::TimeStamp::now() - state.last_update);

        // Check 1: Reprojection error
        status.reprojection_error_px = compute_reprojection_error(
            latest_data.camera_image, latest_data.lidar_cloud,
            state.T_lidar_camera);

        // Check 2: Temporal consistency
        status.temporal_consistency_score = check_temporal_consistency(
            latest_data, state);

        // Check 3: Multi-sensor agreement
        status.multi_sensor_agreement = check_sensor_agreement(latest_data);

        // Determine overall quality
        float quality_score = compute_quality_score(status);

        if (quality_score > 0.8f && status.reprojection_error_px < 3.0f) {
            status.overall_quality = CalibrationQuality::VALID;
            status.requires_recalibration = false;
        } else if (quality_score > 0.5f && status.reprojection_error_px < 7.0f) {
            status.overall_quality = CalibrationQuality::DEGRADED;
            status.requires_recalibration = false;
            status.diagnostic_message = "Calibration degraded - monitor closely";
        } else {
            status.overall_quality = CalibrationQuality::INVALID;
            status.requires_recalibration = true;
            status.diagnostic_message = "Calibration invalid - recalibration required";
            Dem_ReportErrorStatus(DEM_CALIBRATION_RECALIBRATION_REQUIRED);
        }

        // Check 4: Time-based degradation
        if (status.time_since_last_calib > std::chrono::hours(24)) {
            status.overall_quality = CalibrationQuality::DEGRADED;
            status.requires_recalibration = true;
            status.diagnostic_message +=
                " - Calibration older than 24 hours";
        }

        return status;
    }

private:
    float compute_quality_score(const HealthStatus& status) {
        float score = 0.0f;

        // Reprojection error contribution (0-0.4)
        if (status.reprojection_error_px < 3.0f) {
            score += 0.4f;
        } else if (status.reprojection_error_px < 7.0f) {
            score += 0.4f * (1.0f - (status.reprojection_error_px - 3.0f) / 4.0f);
        }

        // Temporal consistency contribution (0-0.3)
        score += 0.3f * status.temporal_consistency_score;

        // Multi-sensor agreement contribution (0-0.3)
        score += 0.3f * status.multi_sensor_agreement;

        return score;
    }

    float check_temporal_consistency(const SensorData& data,
                                      const CalibrationState& state) {
        // Compare current extrinsic with historical estimates
        // Consistent calibration should have stable extrinsics

        if (extrinsic_history_.size() < 10) {
            return 1.0f;  // Insufficient history
        }

        Eigen::Vector3f current_t = state.T_lidar_camera.block<3, 1>(0, 3);
        Eigen::Vector3f mean_t = compute_mean_position(extrinsic_history_);
        float std_dev = compute_std_dev_position(extrinsic_history_, mean_t);

        // Check if current estimate is within 2 sigma of history
        float deviation = (current_t - mean_t).norm();
        if (deviation > 2.0f * std_dev) {
            return 0.3f;  // Anomalous
        } else if (deviation > 1.0f * std_dev) {
            return 0.7f;  // Slightly off
        }
        return 1.0f;  // Consistent
    }

    float check_sensor_agreement(const SensorData& data) {
        // Cross-check calibration using redundant measurements
        // E.g., compare object positions from camera-only vs LiDAR-only

        auto camera_objects = detect_objects_camera(data.camera_image);
        auto lidar_objects = detect_objects_lidar(data.lidar_cloud);

        // Associate objects and compute position differences
        float total_agreement = 0.0f;
        size_t associations = 0;

        for (const auto& cam_obj : camera_objects) {
            auto lidar_match = find_associated_lidar_object(
                cam_obj, lidar_objects, data.calibration);

            if (lidar_match.has_value()) {
                float position_diff = (cam_obj.position -
                                       lidar_match->position).norm();
                if (position_diff < 1.0f) {
                    total_agreement += 1.0f;
                } else if (position_diff < 3.0f) {
                    total_agreement += 0.5f;
                }
                associations++;
            }
        }

        return associations > 0 ? total_agreement / associations : 1.0f;
    }

    std::deque<Eigen::Matrix4f> extrinsic_history_;
};
```

---

## Multi-Sensor Calibration Pipeline

```cpp
/**
 * @brief Unified calibration pipeline for multi-sensor systems
 * @safety ASIL C - Handles Camera, LiDAR, Radar, IMU calibration
 */
class MultiSensorCalibrationPipeline {
public:
    struct PipelineConfig {
        bool enable_camera_lidar = true;
        bool enable_camera_radar = true;
        bool enable_lidar_radar = false;  // Radar calibration challenging
        bool enable_imu_calibration = true;
        CalibrationMethod primary_method = CalibrationMethod::TARGET_BASED;
        bool enable_online_refinement = true;
    };

    struct CalibrationResults {
        Eigen::Matrix4f T_vehicle_camera;
        Eigen::Matrix4f T_vehicle_lidar;
        Eigen::Matrix4f T_vehicle_radar;
        Eigen::Matrix4f T_vehicle_imu;

        // Derived transforms
        Eigen::Matrix4f T_lidar_camera;
        Eigen::Matrix4f T_radar_camera;
        Eigen::Matrix4f T_radar_lidar;

        CalibrationQuality quality;
        ara::core::TimeStamp calibration_time;
        std::string validation_report;
    };

    CalibrationResults run_calibration(
        const SensorData& data,
        const PipelineConfig& config) {

        CalibrationResults results;
        results.quality = CalibrationQuality::UNKNOWN;

        std::stringstream report;
        report << "=== Multi-Sensor Calibration Report ===\n";

        // Step 1: Camera intrinsic (if needed)
        if (config.enable_camera_lidar || config.enable_camera_radar) {
            report << "\n[1] Camera Intrinsic Calibration:\n";
            auto camera_intrinsic = calibrate_camera_intrinsic(data.camera_images);
            report << "  Reprojection error: "
                   << camera_intrinsic.reprojection_error_px << " px\n";
            report << "  Status: "
                   << (camera_intrinsic.is_valid ? "VALID" : "INVALID") << "\n";

            if (!camera_intrinsic.is_valid) {
                results.quality = CalibrationQuality::INVALID;
                results.validation_report = report.str();
                return results;
            }
        }

        // Step 2: Camera-LiDAR extrinsic
        if (config.enable_camera_lidar) {
            report << "\n[2] Camera-LiDAR Extrinsic Calibration:\n";

            Eigen::Matrix4f T_lidar_camera;
            float reprojection_error;

            if (config.primary_method == CalibrationMethod::TARGET_BASED) {
                auto result = calibrate_camera_lidar_target(
                    data.camera_images, data.lidar_clouds);
                T_lidar_camera = result.T_lidar_camera;
                reprojection_error = result.reprojection_error_px;
            } else {
                auto result = calibrate_camera_lidar_natural(data);
                T_lidar_camera = result.T_lidar_camera;
                reprojection_error = result.reprojection_error_px;
            }

            results.T_lidar_camera = T_lidar_camera;
            report << "  Reprojection error: " << reprojection_error << " px\n";
        }

        // Step 3: Camera-Radar extrinsic
        if (config.enable_camera_radar) {
            report << "\n[3] Camera-Radar Extrinsic Calibration:\n";
            auto result = calibrate_camera_radar(
                data.camera_images, data.radar_targets);
            results.T_radar_camera = result.T_radar_camera;
            report << "  Range residual: " << result.range_residual_m << " m\n";
            report << "  Azimuth error: " << result.azimuth_error_deg << " deg\n";
        }

        // Step 4: IMU calibration
        if (config.enable_imu_calibration) {
            report << "\n[4] IMU Calibration:\n";
            auto result = calibrate_imu(data.imu_data);
            results.T_vehicle_imu = result.transform;
            report << "  Gyro bias: " << result.gyro_bias.transpose() << "\n";
            report << "  Accel bias: " << result.accel_bias.transpose() << "\n";
        }

        // Step 5: Compute derived transforms
        if (config.enable_camera_lidar && config.enable_camera_radar) {
            results.T_radar_lidar =
                results.T_radar_camera * results.T_lidar_camera.inverse();
        }

        // Step 6: Online refinement
        if (config.enable_online_refinement) {
            report << "\n[5] Online Refinement:\n";
            auto refined = refine_calibration_online(data, results);
            results = refined;
            report << "  Refinement applied\n";
        }

        // Step 7: Overall quality assessment
        results.quality = assess_overall_quality(results);
        results.calibration_time = ara::core::TimeStamp::now();
        results.validation_report = report.str();

        return results;
    }

private:
    // Implementation of individual calibration methods...
};
```

---

## Performance Benchmarks

| Method | Accuracy | Time Required | Computational Cost | ASIL Suitability |
|--------|----------|---------------|-------------------|-----------------|
| Checkerboard (Camera) | < 0.5 px | 2-5 min | Low | ASIL B |
| AprilTag (Camera-LiDAR) | < 2mm, < 0.1° | 5-10 min | Medium | ASIL B |
| Hand-Eye (AX=XB) | < 3mm, < 0.15° | 10-20 min | Medium | ASIL B |
| Natural Features | < 5mm, < 0.2° | 10-30 min | High | ASIL B |
| Online (EKF) | < 10mm, < 0.5° | Real-time | Medium | ASIL C |
| Multi-Sensor Bundle | < 1mm, < 0.05° | 30-60 min | Very High | ASIL C |

### Computational Complexity

| Algorithm | Time Complexity | Space Complexity | Typical Runtime |
|-----------|----------------|-----------------|-----------------|
| Camera Intrinsic (Zhang) | O(n*m) | O(n+m) | 0.5-2s (20 images) |
| PnP (Camera-LiDAR) | O(n) | O(n) | 10-50ms |
| Hand-Eye (Daniilidis) | O(n) | O(n) | 5-20ms |
| Hand-Eye (Tsai-Lenz) | O(n) | O(n) | 5-15ms |
| RANSAC Natural Features | O(n*iterations) | O(n) | 100-500ms |
| EKF Online | O(1) per step | O(window) | 10-50ms/frame |
| Bundle Adjustment | O(n^3) | O(n^2) | 10-60s |

---

## Safety Mechanisms

```cpp
/**
 * @brief Safety wrapper for calibration operations
 * @safety ASIL C - Monitors calibration quality and triggers safe state
 */
class CalibrationSafetyMonitor {
public:
    struct SafetyStatus {
        bool calibration_valid;
        bool degradation_detected;
        bool safe_to_operate;
        std::string diagnostic_message;
        ara::core::Result<void> validation_result;
    };

    SafetyStatus validate_calibration(const CalibrationResults& results) {
        SafetyStatus status;

        // Check 1: Calibration recency
        auto age = std::chrono::duration_cast<std::chrono::hours>(
            ara::core::TimeStamp::now() - results.calibration_time);

        if (age.count() > 24) {
            status.calibration_valid = false;
            status.safe_to_operate = false;
            status.diagnostic_message = "Calibration expired (>24h old)";
            return status;
        }

        // Check 2: Quality metrics
        if (results.quality != CalibrationQuality::VALID) {
            status.calibration_valid = false;
            status.degradation_detected = true;
            status.safe_to_operate = (results.quality ==
                                       CalibrationQuality::DEGRADED);
            status.diagnostic_message = "Calibration quality degraded";
            return status;
        }

        // Check 3: Plausibility of extrinsics
        if (!plausibility_check_extrinsics(results)) {
            status.calibration_valid = false;
            status.safe_to_operate = false;
            status.diagnostic_message = "Extrinsic parameters implausible";
            return status;
        }

        // Check 4: Cross-sensor consistency
        float consistency = compute_cross_sensor_consistency(results);
        if (consistency < 0.7f) {
            status.calibration_valid = false;
            status.degradation_detected = true;
            status.safe_to_operate = false;
            status.diagnostic_message = "Cross-sensor inconsistency detected";
            return status;
        }

        // All checks passed
        status.calibration_valid = true;
        status.safe_to_operate = true;
        status.validation_result = ara::core::Result<void>::FromValue();

        return status;
    }

private:
    bool plausibility_check_extrinsics(const CalibrationResults& results) {
        // Check that extrinsics are within expected ranges

        // Camera should be forward-facing
        Eigen::Vector3f cam_forward =
            results.T_vehicle_camera.block<3, 1>(0, 2);
        if (cam_forward.x() < 0.5f) {  // Should point mostly forward
            return false;
        }

        // LiDAR should be within vehicle bounds
        Eigen::Vector3f lidar_pos = results.T_vehicle_lidar.block<3, 1>(0, 3);
        if (std::abs(lidar_pos.x()) > 3.0f ||  // > 3m from origin
            std::abs(lidar_pos.y()) > 1.5f ||  // > 1.5m lateral
            lidar_pos.z() < 0.5f || lidar_pos.z() > 3.0f) {  // Height
            return false;
        }

        // Rotation angles should be small (sensors mostly aligned with vehicle)
        Eigen::Vector3f euler = rotation_matrix_to_euler(
            results.T_vehicle_lidar.block<3, 3>(0, 0));
        if (euler.array().abs().maxCoeff() > 0.5f) {  // > 30 degrees
            return false;
        }

        return true;
    }

    float compute_cross_sensor_consistency(const CalibrationResults& results) {
        // Compare derived transforms for consistency
        // T_radar_lidar should equal T_radar_camera * T_camera_lidar

        Eigen::Matrix4f T_radar_lidar_direct = results.T_radar_lidar;
        Eigen::Matrix4f T_radar_lidar Derived =
            results.T_radar_camera * results.T_lidar_camera.inverse();

        float position_diff = (T_radar_lidar_Derived.block<3, 1>(0, 3) -
                               T_radar_lidar_Direct.block<3, 1>(0, 3)).norm();

        if (position_diff > 0.1f) {  // > 10cm inconsistency
            return 0.0f;
        }

        return 1.0f - (position_diff / 0.1f);
    }
};
```

---

## AUTOSAR Adaptive Service Interface

```cpp
/**
 * @brief AUTOSAR Adaptive Calibration Service
 * @safety ASIL B - Service interface for calibration operations
 */
namespace ara::com::example {

class CalibrationServiceProxy {
public:
    // Event: Calibration completed
    ara::com::Event<CalibrationResults> CalibrationCompletedEvent;

    // Event: Calibration quality update
    ara::com::Event<CalibrationQuality> CalibrationQualityEvent;

    // Event: Calibration degradation alert
    ara::com::Event<CalibrationAlert> CalibrationAlertEvent;

    // Method: Start calibration procedure
    ara::core::Result<CalibrationResults> StartCalibration(
        CalibrationMethod method,
        CalibrationTarget target_spec);

    // Method: Get current calibration state
    ara::core::Result<CalibrationState> GetCalibrationState();

    // Method: Validate calibration quality
    ara::core::Result<CalibrationValidation> ValidateCalibration();

    // Method: Trigger recalibration
    ara::core::Result<void> TriggerRecalibration();

    // Field: Current calibration parameters
    ara::com::Field<CalibrationParameters> CalibrationParametersField;
};

} // namespace ara::com::example
```

---

## @-Mentions

**Related Context Files:**
- @context/skills/adas/sensor-fusion.md - Fusion requires accurate calibration
- @context/skills/adas/camera-processing.md - Camera intrinsic calibration
- @context/skills/adas/lidar-processing.md - LiDAR point cloud calibration
- @context/skills/adas/sotif-testing.md - Calibration degradation scenarios

**Related Knowledge:**
- @knowledge/standards/iso26262/2-conceptual.md - ASIL requirements for calibration
- @knowledge/standards/iso21448/3-detailed.md - SOTIF analysis for calibration errors
- @knowledge/technologies/sensor-fusion/2-conceptual.md - Calibration impact on fusion

---

## References

1. Zhang, Z. (2000). "A Flexible New Technique for Camera Calibration"
2. Daniilidis, K. (1999). "Hand-Eye Calibration Using Dual Quaternions"
3. Tsai, R.Y., Lenz, R.K. (1989). "A New Technique for Fully Autonomous Calibration"
4. Brookshire, J., Teller, S. (2012). "Extrinsic Calibration from Per-frame Epipolar Geometry"
5. Levinson, J., Thrun, S. (2014). "Automatic Online Calibration of Lasers and Cameras"
6. AUTOSAR Classic Platform R21-11 - Calibration Service Specifications

---

*Context file version: 1.0 | Last updated: 2026-03-22*
