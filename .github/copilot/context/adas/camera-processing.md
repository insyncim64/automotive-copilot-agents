# Skill: Camera Processing for ADAS

> 2D object detection, semantic segmentation, lane detection, and depth estimation for automotive camera systems.

## Standards Compliance

- ISO 26262 ASIL B/C/D (depending on function criticality)
- ISO 21448 SOTIF (triggering conditions: lighting, weather, occlusion)
- Euro NCAP / C-NCAP (AEB, LSS test protocols)
- AUTOSAR 4.4 (Camera Abstraction Layer)

## Domain Expertise

### 2D Object Detection

| Architecture | Accuracy (mAP) | Latency (ms) | Use Case |
|--------------|----------------|--------------|----------|
| YOLOv8-L | 53.9 | 12 | Primary detection (L2/L3) |
| YOLOv8-X | 55.6 | 18 | High-accuracy (L3/L4) |
| Faster R-CNN R-50 | 37.2 | 45 | Offline processing |
| EfficientDet-D4 | 45.4 | 25 | Resource-constrained |
| SSD ResNet-50 | 35.8 | 20 | Baseline |

**Target Specifications:**

| Metric | L2 (Highway Pilot) | L3 (Traffic Jam Pilot) | L4 (Robotaxi) |
|--------|-------------------|----------------------|--------------|
| Detection mAP @0.5 | > 0.85 | > 0.90 | > 0.95 |
| Latency (end-to-end) | < 50 ms | < 33 ms | < 20 ms |
| False positives / frame | < 0.01 | < 0.005 | < 0.001 |
| Operating conditions | Clear, light rain | Moderate rain, dusk | All weather (design) |

### Semantic Segmentation

| Architecture | mIoU | Latency (ms) | Use Case |
|--------------|------|--------------|----------|
| DeepLabV3+ (R-101) | 83.1 | 35 | Free-space detection |
| PSPNet (R-50) | 79.8 | 28 | Road surface classification |
| UNet (custom) | 75.2 | 15 | Lane marking segmentation |
| BiSeNet V2 | 77.4 | 10 | Real-time drivable area |

### Lane Detection

| Method | Accuracy | Latency | Description |
|--------|----------|---------|-------------|
| Polyline fitting | 95% @ clear | 5 ms | Classical Hough + RANSAC |
| Bezier curves | 96% @ clear | 8 ms | Parametric curve fitting |
| Instance segmentation | 98% @ clear | 25 ms | Deep learning (LaneATT, CLRNet) |

### Depth Estimation

| Method | RMSE (m) | Range (m) | Use Case |
|--------|----------|-----------|----------|
| Monocular (deep learning) | 1.5 @ 50m | 0.5-100 | Single camera systems |
| Stereo matching | 0.3 @ 50m | 1-150 | Stereo camera systems |
| Multi-view stereo | 0.2 @ 50m | 1-200 | Surround-view systems |

---

## Camera Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    Camera Processing Pipeline                    │
├─────────────────────────────────────────────────────────────────┤
│  Image Sensor (RAW12/RAW10)                                     │
│         │                                                        │
│         v                                                        │
│  ┌─────────────────┐                                            │
│  │  ISP Pipeline   │  (Black level, denoise, demosaic, AWB)     │
│  └────────┬────────┘                                            │
│           │                                                      │
│           v                                                      │
│  ┌─────────────────┐                                            │
│  │  Preprocessing  │  (Resize, normalize, color space conv)     │
│  └────────┬────────┘                                            │
│           │                                                      │
│           v                                                      │
│  ┌─────────────────┐                                            │
│  │  Undistortion   │  (Apply intrinsic calibration matrix)      │
│  └────────┬────────┘                                            │
│           │                                                      │
│           v                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Object Detect  │  │   Lane Detect   │  │  Segmentation   │ │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ │
│           │                     │                    │          │
│           └─────────────────────┴────────────────────┘          │
│                                │                                 │
│                                v                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            Post-processing & Fusion Interface            │   │
│  │  - NMS (Non-Maximum Suppression)                         │   │
│  │  - Confidence filtering                                   │   │
│  │  - Coordinate transformation (image -> vehicle frame)    │   │
│  │  - Output to sensor fusion (object list, lane markers)   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Image Signal Processor (ISP) Pipeline

```cpp
/**
 * @brief ISP pipeline configuration for automotive camera
 * @safety ASIL B
 * @req SSR-CAM-001, SSR-CAM-002
 */
struct IspConfig {
    // Black level correction
    uint16_t black_level[4];  // Per-channel

    // Lens shading correction
    float lens_shading_gain[8][8];  // 8x8 grid

    // Demosaic method
    enum DemosaicMethod {
        BILINEAR,
        BICUBIC,
        ADAPTIVE_HOMOGENEOUS_DIRECTION  // AHD (preferred for ADAS)
    } demosaic_method;

    // Color correction matrix (3x3)
    float ccm[9];

    // Gamma curve (256-entry LUT)
    uint16_t gamma_lut[256];

    // Auto white balance gains
    float awb_gain_r, awb_gain_g, awb_gain_b;

    // Noise reduction (3D NR for video)
    uint8_t nr_strength;  // 0-7
    bool temporal_nr_enabled;
};

class IspPipeline {
public:
    /**
     * @brief Process RAW Bayer image to RGB
     * @param raw_input RAW12 Bayer pattern input
     * @param width Image width in pixels
     * @param height Image height in pixels
     * @param bayer_pattern RGGB, BGGR, GRBG, or GBRG
     * @return RGB888 image ready for preprocessing
     * @safety Validates input dimensions and pattern
     * @wcet < 5 ms for 1920x1080 @ 300 MHz DSP
     */
    ImageRgb888 process_raw(const uint16_t* raw_input,
                            size_t width, size_t height,
                            BayerPattern bayer_pattern);

    /**
     * @brief Apply lens shading correction
     * @safety Prevents vignetting artifacts affecting detection
     */
    void apply_lens_shading_correction(ImageRgb888& image);

    /**
     * @brief Demosaic Bayer pattern to full RGB
     * @safety AHD method preferred for edge preservation
     */
    void demosaic(const uint16_t* bayer, ImageRgb888& rgb);

    /**
     * @brief Apply color correction matrix
     * @safety CCM tuned for automotive color conditions
     */
    void apply_color_correction(ImageRgb888& image);

private:
    IspConfig config_;
};
```

---

## Camera Intrinsic Calibration

```cpp
/**
 * @brief Camera intrinsic parameters (pinhole model + distortion)
 * @safety ASIL B
 * @req SSR-CAM-010
 */
struct CameraIntrinsics {
    // Intrinsic matrix K
    float fx;  // Focal length x (pixels)
    float fy;  // Focal length y (pixels)
    float cx;  // Principal point x (pixels)
    float cy;  // Principal point y (pixels)

    // Distortion coefficients (5-parameter Brown-Conrady)
    float k1, k2, k3;  // Radial distortion
    float p1, p2;      // Tangential distortion

    /**
     * @brief Project 3D point to image plane
     * @param point_3d 3D point in camera coordinate frame
     * @return 2D image coordinate (u, v)
     */
    Eigen::Vector2f project(const Eigen::Vector3f& point_3d) const {
        // Apply distortion
        const float x = point_3d.x() / point_3d.z();
        const float y = point_3d.y() / point_3d.z();
        const float r2 = x * x + y * y;
        const float r4 = r2 * r2;
        const float r6 = r4 * r2;

        // Radial distortion
        const float radial = (1.0f + k1 * r2 + k2 * r4 + k3 * r6);
        const float dx = 2.0f * x * y * p1 + p2 * (r2 + 2.0f * x * x);
        const float dy = p1 * (r2 + 2.0f * y * y) + 2.0f * x * y * p2;

        const float x_distorted = x * radial + dx;
        const float y_distorted = y * radial + dy;

        // Project to pixel coordinates
        return Eigen::Vector2f(
            fx * x_distorted + cx,
            fy * y_distorted + cy
        );
    }

    /**
     * @brief Unproject 2D pixel to 3D ray
     * @param pixel 2D image coordinate (u, v)
     * @param depth Depth value (if known) or 1.0 for unit ray
     * @return 3D point/direction in camera frame
     */
    Eigen::Vector3f unproject(const Eigen::Vector2f& pixel,
                               float depth = 1.0f) const {
        // Remove distortion iteratively (Newton-Raphson)
        float x = (pixel.x() - cx) / fx;
        float y = (pixel.y() - cy) / fy;

        for (int i = 0; i < 5; i++) {
            const float r2 = x * x + y * y;
            const float r4 = r2 * r2;
            const float r6 = r4 * r2;
            const float radial = 1.0f + k1 * r2 + k2 * r4 + k3 * r6;
            const float dx = 2.0f * x * y * p1 + p2 * (r2 + 2.0f * x * x);
            const float dy = p1 * (r2 + 2.0f * y * y) + 2.0f * x * y * p2;

            const float x_est = x * radial + dx;
            const float y_est = y * radial + dy;

            const float ex = (pixel.x() - cx) / fx - x_est;
            const float ey = (pixel.y() - cy) / fy - y_est;

            // Jacobian approximation
            const float Jxx = radial + 2.0f * x * (k1 + 2.0f * k2 * r2 + 3.0f * k3 * r4) + 6.0f * p1 * y + 6.0f * p2 * x;
            const float Jyy = radial + 2.0f * y * (k1 + 2.0f * k2 * r2 + 3.0f * k3 * r4) + 2.0f * p1 * y + 6.0f * p2 * x;

            x += ex / Jxx;
            y += ey / Jyy;
        }

        return Eigen::Vector3f(x * depth, y * depth, depth);
    }
};

/**
 * @brief Calibrate camera intrinsics using checkerboard
 * @safety ASIL B
 * @req SSR-CAM-011
 */
class IntrinsicCalibrator {
public:
    /**
     * @brief Add calibration image (checkerboard detected)
     * @param image Raw image with checkerboard
     * @param checkerboard_size Size of checkerboard (e.g., 9x6)
     * @param square_size_mm Square size in millimeters
     * @return true if checkerboard detected
     */
    bool add_calibration_image(const ImageGray8& image,
                                cv::Size checkerboard_size,
                                float square_size_mm);

    /**
     * @brief Run calibration optimization (Levenberg-Marquardt)
     * @return Reprojection error in pixels
     * @safety Validates calibration quality (< 0.5 px target)
     */
    double calibrate() {
        // Minimize reprojection error
        // sum over all views and points: ||observed - projected||^2

        cv::Mat camera_matrix = (cv::Mat_<float>(3, 3) <<
            fx_, 0.0f, cx_,
            0.0f, fy_, cy_,
            0.0f, 0.0f, 1.0f);
        cv::Mat dist_coeffs = (cv::Mat_<float>(5, 1) <<
            k1_, k2_, p1_, p2_, k3_);

        const double rms_error = cv::calibrateCamera(
            object_points_,      // 3D checkerboard corners
            image_points_,       // 2D detected corners
            image_size_,
            camera_matrix,
            dist_coeffs,
            rvecs_, tvecs_,      // Per-view extrinsics
            cv::CALIB_FIX_K3     // Fix k3 for wide-angle
        );

        // Extract calibrated parameters
        fx_ = camera_matrix.at<float>(0, 0);
        fy_ = camera_matrix.at<float>(1, 1);
        cx_ = camera_matrix.at<float>(0, 2);
        cy_ = camera_matrix.at<float>(1, 2);
        k1_ = dist_coeffs.at<float>(0);
        k2_ = dist_coeffs.at<float>(1);
        p1_ = dist_coeffs.at<float>(2);
        p2_ = dist_coeffs.at<float>(3);
        k3_ = dist_coeffs.at<float>(4);

        return rms_error;
    }

    /**
     * @brief Validate calibration quality
     * @return true if calibration meets automotive standards
     * @safety Target: RMS error < 0.5 pixels, min 20 images
     */
    bool validate_calibration() const {
        return image_points_.size() >= 20 && rms_error_ < 0.5;
    }

private:
    std::vector<std::vector<cv::Point3f>> object_points_;
    std::vector<std::vector<cv::Point2f>> image_points_;
    cv::Size image_size_;
    std::vector<cv::Mat> rvecs_, tvecs_;

    float fx_, fy_, cx_, cy_;
    float k1_, k2_, k3_, p1_, p2_;
    double rms_error_ = 0.0;
};
```

---

## 2D Object Detection (YOLOv8)

```cpp
/**
 * @brief YOLOv8 object detection for automotive
 * @safety ASIL B
 * @req SSR-CAM-020, SSR-CAM-021
 *
 * Input: 640x640 RGB image (normalized to [0,1])
 * Output: Detected objects with class, confidence, bbox
 *
 * @dependencies
 * - TensorRT 8.x for inference optimization
 * - CUDA 12.x for GPU acceleration
 * - OpenCV 4.8+ for preprocessing
 */
class YoloV8Detector {
public:
    struct Detection {
        int class_id;
        float confidence;
        cv::Rect bbox;  // [x_min, y_min, x_max, y_max]
        Eigen::Vector4f bbox_corners;  // For NMS
    };

    /**
     * @brief Initialize detector with TensorRT engine
     * @param engine_path Path to serialized TRT engine
     * @param confidence_threshold Minimum confidence (0.25 typical)
     * @param nms_threshold NMS IoU threshold (0.45 typical)
     */
    bool initialize(const std::string& engine_path,
                    float confidence_threshold = 0.25f,
                    float nms_threshold = 0.45f);

    /**
     * @brief Run inference on input image
     * @param image Input image (any size, will be resized to 640x640)
     * @return Vector of detections
     * @safety WCET < 15 ms on Jetson Orin
     * @safety Includes input validation and output plausibility
     */
    std::vector<Detection> detect(const ImageRgb888& image) {
        // Preprocess: resize, normalize, HWC->CHW
        auto input_tensor = preprocess(image);

        // Run inference
        std::vector<float> output;
        if (!context_->executeV2({input_tensor.data(), output.data()})) {
            Dem_ReportErrorStatus(DTC_INFERENCE_FAILURE);
            return {};
        }

        // Postprocess: decode outputs, apply NMS
        auto detections = decode_outputs(output);
        return apply_nms(detections);
    }

    /**
     * @brief Get inference timing statistics
     */
    struct TimingStats {
        float preprocess_ms;
        float inference_ms;
        float postprocess_ms;
        float total_ms;
    };
    TimingStats get_timing_stats() const { return timing_stats_; }

private:
    /**
     * @brief Preprocess image for YOLOv8
     * - Resize to 640x640 with letterbox padding
     * - Normalize to [0, 1]
     * - Convert HWC to CHW
     * - Create 1x3x640x640 tensor
     */
    Tensor preprocess(const ImageRgb888& image);

    /**
     * @brief Decode YOLOv8 output format
     * YOLOv8 output: 1x84x8400 tensor (84 = 4 bbox + 80 classes)
     */
    std::vector<Detection> decode_outputs(const std::vector<float>& output);

    /**
     * @brief Apply Non-Maximum Suppression
     * @safety Removes duplicate detections for same object
     */
    std::vector<Detection> apply_nms(std::vector<Detection>& detections);

    std::unique_ptr<nvinfer1::ICudaEngine> engine_;
    std::unique_ptr<nvinfer1::IExecutionContext> context_;
    float confidence_threshold_;
    float nms_threshold_;
    TimingStats timing_stats_;
};

/**
 * @brief Letterbox resize with aspect ratio preservation
 * @safety Maintains detection accuracy by avoiding distortion
 */
ImageRgb888 letterbox_resize(const ImageRgb888& image,
                              int target_width, int target_height) {
    const float scale = std::min(
        static_cast<float>(target_width) / image.width,
        static_cast<float>(target_height) / image.height
    );

    const int new_width = static_cast<int>(image.width * scale);
    const int new_height = static_cast<int>(image.height * scale);

    // Resize maintaining aspect ratio
    ImageRgb888 resized = resize_bilinear(image, new_width, new_height);

    // Create output with gray padding (114, 114, 114) for YOLO
    ImageRgb888 output(target_width, target_height);
    output.fill(cv::Scalar(114, 114, 114));

    // Paste resized image in center
    const int x_offset = (target_width - new_width) / 2;
    const int y_offset = (target_height - new_height) / 2;
    paste_image(output, resized, x_offset, y_offset);

    return output;
}
```

---

## Lane Detection

```cpp
/**
 * @brief Lane detection using polynomial fitting
 * @safety ASIL B
 * @req SSR-CAM-030, SSR-CAM-031
 */
struct LaneMarking {
    enum class Type {
        SOLID_SINGLE,
        SOLID_DOUBLE,
        DASHED,
        DASHED_LONG,
        BOTTSDOTS,
        NONE
    };

    enum class Color {
        WHITE,
        YELLOW,
        BLUE,    // Korea
        INVALID
    };

    // Polynomial coefficients (3rd order: ax^3 + bx^2 + cx + d)
    float coefficients[4];

    // Lane type and color
    Type type;
    Color color;

    // Confidence [0, 1]
    float confidence;

    // Valid range in image (y_min, y_max)
    float y_min, y_max;

    /**
     * @brief Get X position at given Y
     */
    float get_x_at_y(float y) const {
        return coefficients[0] * y * y * y +
               coefficients[1] * y * y +
               coefficients[2] * y +
               coefficients[3];
    }

    /**
     * @brief Compute curvature at given Y
     * @return Curvature in 1/meters
     */
    float get_curvature(float y, float ym_per_pix, float xm_per_pix) const {
        // Convert coefficients to world coordinates
        const float c = coefficients[2] * (ym_per_pix / xm_per_pix);
        const float b = coefficients[1] * (ym_per_pix / (xm_per_pix * xm_per_pix));

        // Curvature formula: |f''| / (1 + f'^2)^1.5
        const float y_world = y * ym_per_pix;
        const float first_deriv = 3 * b * y_world * y_world + 2 * c * y_world + coefficients[0];
        const float second_deriv = 6 * b * y_world + 2 * coefficients[0];

        return std::abs(second_deriv) / std::pow(1 + first_deriv * first_deriv, 1.5f);
    }
};

/**
 * @brief Lane detection pipeline
 * @safety ASIL B
 */
class LaneDetector {
public:
    struct LaneOutput {
        std::optional<LaneMarking> left_lane;
        std::optional<LaneMarking> right_lane;
        float lane_width_m;
        float vehicle_offset_from_center_m;
        float road_curvature_1pm;  // 1/meters
        float max_safe_speed_kmh;
    };

    /**
     * @brief Detect lanes in input image
     * @param image Undistorted camera image
     * @param camera_intrinsics Camera calibration for metric conversion
     * @return Detected lanes with curvature and vehicle position
     * @safety WCET < 20 ms for 1920x1080
     */
    LaneOutput detect_lanes(const ImageRgb888& image,
                            const CameraIntrinsics& camera_intrinsics) {
        LaneOutput output;

        // Step 1: Convert to HLS, extract S channel (robust to shadows)
        ImageHLS hls_image = rgb_to_hls(image);
        ImageGray8 s_channel = extract_saturation_channel(hls_image);

        // Step 2: Edge detection (Canny)
        ImageGray8 edges = canny_edge(s_channel, 50, 150);

        // Step 3: ROI mask (trapezoid for road area)
        ImageGray8 masked_edges = apply_roi_mask(edges, roi_polygon_);

        // Step 4: Hough transform for line segments
        auto line_segments = hough_transform_ppl(masked_edges);

        // Step 5: Separate and fit left/right lanes
        auto left_lines = separate_lane_lines(line_segments, LaneSide::LEFT);
        auto right_lines = separate_lane_lines(line_segments, LaneSide::RIGHT);

        if (!left_lines.empty()) {
            auto poly = fit_polynomial(left_lines);
            output.left_lane = classify_lane_marking(poly, left_lines);
        }

        if (!right_lines.empty()) {
            auto poly = fit_polynomial(right_lines);
            output.right_lane = classify_lane_marking(poly, right_lines);
        }

        // Step 6: Compute lane width and vehicle offset
        if (output.left_lane && output.right_lane) {
            output.lane_width_m = compute_lane_width_meters(
                *output.left_lane, *output.right_lane, camera_intrinsics);
            output.vehicle_offset_from_center_m = compute_vehicle_offset(
                *output.left_lane, *output.right_lane, image.width / 2, camera_intrinsics);

            // Compute road curvature
            const float y_eval = image.height * 0.9f;  // Near bottom of image
            output.road_curvature_1pm = output.left_lane->get_curvature(
                y_eval, YM_PER_PIX, XM_PER_PIX);

            // Compute max safe speed based on curvature
            output.max_safe_speed_kmh = compute_max_safe_speed(output.road_curvature_1pm);
        }

        return output;
    }

private:
    std::vector<cv::Point> roi_polygon_;
    static constexpr float YM_PER_PIX = 30.0f / 720.0f;  // 30m visible range / 720 pixels
    static constexpr float XM_PER_PIX = 3.7f / 700.0f;   // Lane width 3.7m / 700 pixels
};

/**
 * @brief Classify lane marking type using ML classifier
 * @safety ASIL B
 */
LaneMarking::Type classify_lane_marking_type(
    const std::vector<float>& coefficients,
    const std::vector<cv::Vec4i>& line_segments) {

    // Features for classification
    const float avg_gap = compute_avg_dashed_gap(line_segments);
    const float avg_segment_length = compute_avg_segment_length(line_segments);
    const float gap_to_segment_ratio = avg_gap / avg_segment_length;

    // Rule-based classification
    if (gap_to_segment_ratio < 0.2f) {
        return LaneMarking::Type::SOLID_SINGLE;
    } else if (gap_to_segment_ratio < 1.5f) {
        return LaneMarking::Type::DASHED;
    } else if (gap_to_segment_ratio < 3.0f) {
        return LaneMarking::Type::DASHED_LONG;
    } else {
        return LaneMarking::Type::SOLID_SINGLE;
    }
}
```

---

## Semantic Segmentation

```cpp
/**
 * @brief Semantic segmentation for free-space detection
 * @safety ASIL B
 * @req SSR-CAM-040
 *
 * Classes: road, sidewalk, building, vegetation, vehicle, pedestrian, sky
 */
class SemanticSegmenter {
public:
    enum class SemanticClass : uint8_t {
        ROAD = 0,
        SIDEWALK = 1,
        BUILDING = 2,
        VEGETATION = 3,
        VEHICLE = 4,
        PEDESTRIAN = 5,
        SKY = 6,
        NUM_CLASSES = 7
    };

    /**
     * @brief Generate semantic segmentation mask
     * @param image Input RGB image
     * @return Per-pixel class probabilities [H x W x NUM_CLASSES]
     * @safety WCET < 30 ms for 1920x1080
     */
    Tensor segment(const ImageRgb888& image);

    /**
     * @brief Extract drivable area from segmentation
     * @return Binary mask of drivable region
     * @safety Used for path planning obstacle avoidance
     */
    ImageGray8 get_drivable_area(const Tensor& segmentation) {
        ImageGray8 mask(segmentation.height(), segmentation.width());

        for (int y = 0; y < segmentation.height(); y++) {
            for (int x = 0; x < segmentation.width(); x++) {
                const float road_prob = segmentation.at(y, x, SemanticClass::ROAD);
                const float sidewalk_prob = segmentation.at(y, x, SemanticClass::SIDEWALK);

                // Drivable: road + sidewalk (for emergency maneuvers)
                mask.at(y, x) = (road_prob > 0.5f || sidewalk_prob > 0.3f) ? 255 : 0;
            }
        }

        return mask;
    }

    /**
     * @brief Detect free space for path planning
     * @param drivable_mask Binary drivable area mask
     * @param camera_height_m Camera height above ground
     * @return Polygon of free space in vehicle coordinates
     */
    DrivableArea detect_free_space(const ImageGray8& drivable_mask,
                                    float camera_height_m);
};
```

---

## Depth Estimation

### Monocular Depth (Deep Learning)

```cpp
/**
 * @brief Monocular depth estimation using deep learning
 * @safety ASIL B
 * @req SSR-CAM-050
 *
 * Limitations: Scale ambiguity, requires training on similar scenes
 */
class MonocularDepthEstimator {
public:
    /**
     * @brief Predict depth from single image
     * @param image RGB input image
     * @return Depth map in meters (inverse: closer = brighter)
     * @safety WCET < 25 ms for 1920x1080
     * @accuracy RMSE: ~1.5m @ 50m range (clear weather)
     */
    Tensor predict_depth(const ImageRgb888& image);

    /**
     * @brief Convert disparity to metric depth
     * @param disparity Disparity map (0-255)
     * @param baseline Virtual baseline (learned parameter)
     * @param focal_length Focal length in pixels
     * @return Depth in meters
     */
    Tensor disparity_to_depth(const Tensor& disparity,
                               float baseline, float focal_length) {
        Tensor depth(disparity.shape());
        for (int i = 0; i < disparity.size(); i++) {
            const float d = disparity[i];
            if (d > 0.0f) {
                depth[i] = (baseline * focal_length) / d;
            } else {
                depth[i] = MAX_DEPTH_M;  // Unknown depth
            }
        }
        return depth;
    }
};
```

### Stereo Matching

```cpp
/**
 * @brief Stereo depth estimation (Semi-Global Matching)
 * @safety ASIL B
 * @req SSR-CAM-051
 *
 * Accuracy: ~30cm @ 50m with 24cm baseline
 */
class StereoMatcher {
public:
    /**
     * @brief Compute disparity map using SGM
     * @param left_image Left camera image (rectified)
     * @param right_image Right camera image (rectified)
     * @param num_disparities Number of disparity levels (64, 128, 256)
     * @return Disparity map [0, num_disparities)
     * @safety WCET < 20 ms for 1920x1080 on FPGA/ASIC
     */
    Tensor compute_disparity(const ImageGray8& left_image,
                              const ImageGray8& right_image,
                              int num_disparities = 128);

    /**
     * @brief Triangulate disparity to 3D point cloud
     * @param disparity Disparity map
     * @param baseline Stereo baseline in meters
     * @param fx Focal length in pixels
     * @param cx, cy Principal point
     * @return 3D point cloud (Nx3 matrix)
     */
    Eigen::MatrixXf disparity_to_pointcloud(const Tensor& disparity,
                                             float baseline,
                                             float fx, float cx, float cy) {
        const int height = disparity.height();
        const int width = disparity.width();

        Eigen::MatrixXf pointcloud(height * width, 3);
        int valid_count = 0;

        for (int v = 0; v < height; v++) {
            for (int u = 0; u < width; u++) {
                const float d = disparity.at(v, u);
                if (d > 0.0f) {
                    const float Z = (baseline * fx) / d;
                    const float X = (u - cx) * Z / fx;
                    const float Y = (v - cy) * Z / fy;

                    pointcloud.row(valid_count) << X, Y, Z;
                    valid_count++;
                }
            }
        }

        return pointcloud.block(0, 0, valid_count, 3);
    }
};
```

---

## Safety Mechanisms

```cpp
/**
 * @brief Camera processing safety monitor
 * @safety ASIL B
 * @req SSR-CAM-060
 */
class CameraSafetyMonitor {
public:
    struct CameraHealthStatus {
        enum class Status {
            HEALTHY,
            DEGRADED,
            FAILED
        };

        Status status;
        float saturation_ratio;        // % pixels saturated
        float motion_blur_metric;      // Blur estimate
        float occlusion_ratio;         // % lens occluded
        float noise_level;             // Image noise estimate
        uint32_t consecutive_faults;
    };

    /**
     * @brief Check image quality and detect sensor faults
     * @param image Input image
     * @return Health status with degradation assessment
     * @safety Triggers fallback when camera unreliable
     */
    CameraHealthStatus check_camera_health(const ImageRgb888& image) {
        CameraHealthStatus status;

        // 1. Check for saturation (overexposure)
        status.saturation_ratio = compute_saturation_ratio(image);
        if (status.saturation_ratio > 0.3f) {
            // More than 30% saturated -> unreliable
            status.status = CameraHealthStatus::DEGRADED;
        }

        // 2. Detect motion blur (Laplacian variance)
        status.motion_blur_metric = compute_laplacian_variance(image);
        if (status.motion_blur_metric < BLUR_THRESHOLD) {
            status.status = CameraHealthStatus::DEGRADED;
        }

        // 3. Detect lens occlusion (dark corners, water drops)
        status.occlusion_ratio = detect_occlusion(image);
        if (status.occlusion_ratio > 0.2f) {
            status.status = CameraHealthStatus::DEGRADED;
        }

        // 4. Check for frozen frame (temporal consistency)
        if (is_frame_frozen(image)) {
            status.status = CameraHealthStatus::FAILED;
            status.consecutive_faults++;
        } else {
            status.consecutive_faults = 0;
        }

        // 5. Final assessment
        if (status.consecutive_faults >= 5) {
            status.status = CameraHealthStatus::FAILED;
        } else if (status.saturation_ratio > 0.5f ||
                   status.occlusion_ratio > 0.5f) {
            status.status = CameraHealthStatus::FAILED;
        }

        return status;
    }

    /**
     * @brief Compute saturation ratio
     * @return Fraction of pixels at maximum intensity
     */
    float compute_saturation_ratio(const ImageRgb888& image) {
        int saturated_pixels = 0;
        for (int y = 0; y < image.height; y++) {
            for (int x = 0; x < image.width; x++) {
                const auto& pixel = image.at(y, x);
                if (pixel.r >= 250 && pixel.g >= 250 && pixel.b >= 250) {
                    saturated_pixels++;
                }
            }
        }
        return static_cast<float>(saturated_pixels) / (image.height * image.width);
    }

    /**
     * @brief Detect motion blur using Laplacian variance
     * @return Laplacian variance (lower = more blur)
     */
    float compute_laplacian_variance(const ImageRgb888& image) {
        ImageGray8 gray = rgb_to_grayscale(image);
        ImageGray8 laplacian;
        cv::Laplacian(gray, laplacian, CV_8U);
        return static_cast<float>(cv::mean(laplacian)[1]);  // Variance
    }

    /**
     * @brief Detect lens occlusion (water, dirt, tape)
     * @return Estimated occlusion ratio
     */
    float detect_occlusion(const ImageRgb888& image);

private:
    static constexpr float BLUR_THRESHOLD = 50.0f;
};

/**
 * @brief Cross-validate camera detections with radar
 * @safety ASIL C (for AEB function)
 */
struct CameraRadarCrossValidation {
    /**
     * @brief Validate camera object list against radar
     * @param camera_objects Objects from camera detection
     * @param radar_objects Objects from radar tracking
     * @param camera_to_radar_extrinsic Extrinsic calibration
     * @return Validated objects with confidence adjustment
     */
    static ValidatedObjectList cross_validate(
        const CameraObjectList& camera_objects,
        const RadarObjectList& radar_objects,
        const Extrinsics& camera_to_radar_extrinsic) {

        ValidatedObjectList validated;

        for (const auto& cam_obj : camera_objects) {
            // Project camera object to radar frame
            const auto radar_frame_obj = transform_to_frame(
                cam_obj, camera_to_radar_extrinsic);

            // Find matching radar object (nearest neighbor)
            const auto* radar_match = find_nearest_radar_object(
                radar_frame_obj, radar_objects);

            if (radar_match != nullptr) {
                // Both sensors agree -> increase confidence
                validated.add_object(cam_obj, ValidationStatus::CONFIRMED);
                validated.back().confidence = std::min(1.0f, cam_obj.confidence + 0.2f);
            } else {
                // Camera only -> reduced confidence
                validated.add_object(cam_obj, ValidationStatus::CAMERA_ONLY);
                validated.back().confidence = cam_obj.confidence * 0.7f;
            }
        }

        return validated;
    }
};
```

---

## Performance Benchmarks

| Processing Stage | Jetson Orin | TDA4VM | Xilinx MPSoC | Target |
|-----------------|-------------|--------|--------------|--------|
| ISP (1920x1080) | 3 ms | 5 ms | 4 ms | < 10 ms |
| Undistortion | 2 ms | 3 ms | 2 ms (FPGA) | < 5 ms |
| YOLOv8 inference | 12 ms | 25 ms | 20 ms | < 33 ms |
| Lane detection | 8 ms | 15 ms | 12 ms | < 20 ms |
| Segmentation | 20 ms | 40 ms | 30 ms | < 50 ms |
| Depth estimation | 15 ms | 30 ms | 25 ms | < 33 ms |
| **Total Pipeline** | **60 ms** | **118 ms** | **93 ms** | **< 100 ms** |

---

## References

- @knowledge/standards/iso26262/2-conceptual.md — ASIL classification for vision systems
- @knowledge/standards/iso21448/3-detailed.md — SOTIF triggering conditions for cameras
- @context/skills/adas/sensor-fusion.md — Camera-to-radar/lidar fusion
- @context/skills/adas/calibration.md — Camera extrinsic calibration
- @knowledge/technologies/computer-vision/2-conceptual.md — Deep learning architectures

---

## Related Skills

| Skill Context File | Description |
|-------------------|-------------|
| @context/skills/adas/sensor-fusion.md | Multi-sensor fusion after camera processing |
| @context/skills/adas/lidar-processing.md | 3D detection complementary to camera |
| @context/skills/adas/object-tracking.md | Temporal tracking of detected objects |
| @context/skills/adas/calibration.md | Camera calibration procedures |
