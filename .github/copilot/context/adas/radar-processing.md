# ADAS Radar Processing Skill

> Context file for FMCW radar signal processing, 4D imaging radar, CFAR detection,
> Doppler tracking, and radar-camera fusion in automotive ADAS applications.

**Standards Compliance:**
- ISO 26262 ASIL B/C (depending on ADAS function: ACC, AEB, BSD)
- ISO 21448 SOTIF (radar limitations in adverse weather)
- AUTOSAR Classic/Adaptive platform integration

---

## Domain Expertise

| Technology | Algorithms | Methods |
|------------|-----------|---------|
| **FMCW Radar** | Range-Doppler processing, FFT, CFAR | 2D-FFT, OS-CFAR, CA-CFAR |
| **4D Imaging Radar** | Elevation estimation, Digital beamforming | MUSIC, ESPRIT, Capon |
| **Doppler Tracking** | Micro-Doppler classification, EKF | JTBD, Doppler-velocity filtering |
| **Radar-Camera Fusion** | ROI-based fusion, Early/late fusion | Frustum projection, Bayesian fusion |

---

## FMCW Radar Fundamentals

### Chirp Signal Model

```cpp
/**
 * @brief FMCW chirp signal generation
 * @param t Time vector (seconds)
 * @param f0 Start frequency (77 GHz)
 * @param B Chirp bandwidth (e.g., 4 GHz for 7.5cm range resolution)
 * @param T_chirp Chirp duration (e.g., 50 us)
 * @return Complex baseband chirp signal
 *
 * @safety QM (test signal generation)
 * @note Range resolution: delta_r = c / (2 * B)
 * @note Max unambiguous range: r_max = (c * T_chirp * f_s) / (2 * B)
 */
struct FmcwChirpConfig {
    float f0_hz = 77.0e9f;           // 77 GHz carrier
    float bandwidth_hz = 4.0e9f;      // 4 GHz bandwidth
    float chirp_duration_s = 50.0e-6f; // 50 us
    float sample_rate_hz = 10.0e6f;   // 10 MS/s
    uint16_t num_chirps = 128;        // Chirps per frame
    float chirp_repetition_time = 60.0e-6f; // 60 us PRT
};

class FmcwChirpGenerator {
public:
    std::vector<std::complex<float>> generate_chirp(const FmcwChirpConfig& config) {
        const size_t num_samples = static_cast<size_t>(
            config.chirp_duration_s * config.sample_rate_hz);
        std::vector<std::complex<float>> chirp(num_samples);

        const float chirp_slope = config.bandwidth_hz / config.chirp_duration_s;

        for (size_t n = 0; n < num_samples; ++n) {
            const float t = static_cast<float>(n) / config.sample_rate_hz;
            const float phase = 2.0f * M_PIf32 * (
                config.f0_hz * t +
                0.5f * chirp_slope * t * t
            );
            chirp[n] = std::polar(1.0f, phase);
        }
        return chirp;
    }
};
```

### Beat Frequency Calculation

```cpp
/**
 * @brief Calculate target range from beat frequency
 * @param f_beat Beat frequency (Hz)
 * @param config FMCW configuration
 * @return Range in meters
 *
 * Physics: f_beat = (2 * R * B) / (c * T_chirp)
 * Solving: R = (f_beat * c * T_chirp) / (2 * B)
 */
inline float beat_frequency_to_range(float f_beat, const FmcwChirpConfig& config) {
    constexpr float SPEED_OF_LIGHT = 299792458.0f;
    return (f_beat * SPEED_OF_LIGHT * config.chirp_duration_s) /
           (2.0f * config.bandwidth_hz);
}

/**
 * @brief Calculate target velocity from Doppler shift
 * @param f_doppler Doppler frequency shift (Hz)
 * @param wavelength Radar wavelength (meters)
 * @return Radial velocity in m/s (positive = approaching)
 *
 * Physics: f_doppler = (2 * v) / lambda
 * Solving: v = (f_doppler * lambda) / 2
 */
inline float doppler_to_velocity(float f_doppler, float wavelength) {
    return (f_doppler * wavelength) / 2.0f;
}
```

---

## Range-Doppler Processing

### 2D-FFT Processing Pipeline

```cpp
/**
 * @brief Range-Doppler map generation via 2D-FFT
 *
 * Processing chain:
 * 1. Dechirp: Mix received signal with transmitted chirp
 * 2. Range FFT: FFT along fast-time (samples within chirp)
 * 3. Doppler FFT: FFT along slow-time (chirps within frame)
 * 4. Log-magnitude: Convert to dB scale
 *
 * @safety ASIL B (primary object detection for ACC/AEB)
 * @wcet < 5 ms on Jacinto TDA4VM (C66x DSP @ 1.5 GHz)
 */
class RangeDopplerProcessor {
public:
    struct RdMapConfig {
        size_t num_range_bins;
        size_t num_doppler_bins;
        float range_resolution_m;
        float doppler_resolution_hz;
        bool apply_windowing;
    };

    Eigen::MatrixXcf compute_range_doppler_map(
        const std::vector<std::vector<std::complex<float>>>& adc_data,
        const RdMapConfig& config) {

        const size_t num_chirps = adc_data.size();
        const size_t num_samples = adc_data[0].size();

        // Step 1: Range FFT (along each chirp)
        Eigen::MatrixXcf range_fft(num_samples, num_chirps);
        for (size_t chirp_idx = 0; chirp_idx < num_chirps; ++chirp_idx) {
            apply_window(adc_data[chirp_idx], WindowType::HAMMING);
            fft_inplace(adc_data[chirp_idx]);
            for (size_t sample_idx = 0; sample_idx < num_samples; ++sample_idx) {
                range_fft(sample_idx, chirp_idx) = adc_data[chirp_idx][sample_idx];
            }
        }

        // Step 2: Doppler FFT (along chirp dimension for each range bin)
        Eigen::MatrixXcf rd_map(num_samples, num_chirps);
        for (size_t range_idx = 0; range_idx < num_samples; ++range_idx) {
            std::vector<std::complex<float>> slow_time(num_chirps);
            for (size_t chirp_idx = 0; chirp_idx < num_chirps; ++chirp_idx) {
                slow_time[chirp_idx] = range_fft(range_idx, chirp_idx);
            }

            apply_window(slow_time, WindowType::HAMMING);
            fft_inplace(slow_time);

            for (size_t doppler_idx = 0; doppler_idx < num_chirps; ++doppler_idx) {
                rd_map(range_idx, doppler_idx) = slow_time[doppler_idx];
            }
        }

        // Step 3: Shift zero Doppler to center
        rd_map = shift_doppler_center(rd_map);

        return rd_map;
    }

private:
    void apply_window(std::vector<std::complex<float>>& signal, WindowType type) {
        const auto window = generate_window(signal.size(), type);
        for (size_t n = 0; n < signal.size(); ++n) {
            signal[n] *= window[n];
        }
    }

    Eigen::MatrixXcf shift_doppler_center(const Eigen::MatrixXcf& rd_map) {
        const size_t num_doppler = rd_map.cols();
        const size_t half_doppler = num_doppler / 2;
        Eigen::MatrixXcf shifted = rd_map;

        // Circular shift: swap left/right halves in Doppler dimension
        shifted.block(0, 0, rd_map.rows(), half_doppler) =
            rd_map.block(0, half_doppler, rd_map.rows(), num_doppler - half_doppler);
        shifted.block(0, num_doppler - half_doppler, rd_map.rows(), half_doppler) =
            rd_map.block(0, 0, rd_map.rows(), half_doppler);

        return shifted;
    }
};
```

### Range-Azimuth Heatmap (for MIMO Radar)

```cpp
/**
 * @brief Digital beamforming for azimuth angle estimation
 *
 * Uses MIMO virtual array with N_tx transmit and N_rx receive antennas
 * to form N_tx * N_rx virtual channels.
 *
 * @safety ASIL B
 * @note Azimuth resolution: delta_theta = lambda / (N_virtual * d)
 *       where d is antenna spacing (typically lambda/2)
 */
class AzimuthBeamformer {
public:
    struct MimoConfig {
        uint8_t num_tx;
        uint8_t num_rx;
        std::vector<float> tx_antenna_positions_m;
        std::vector<float> rx_antenna_positions_m;
        float operating_frequency_hz = 77.0e9f;
    };

    /**
     * @brief Compute range-azimuth heatmap via FFT beamforming
     * @param range_fft_data Range FFT output per virtual channel
     * @param num_virtual_channels N_tx * N_rx
     * @param num_range_bins Number of range bins
     * @param azimuth_resolution_deg Desired azimuth resolution
     * @return Range-azimuth heatmap (range x azimuth)
     */
    Eigen::MatrixXf compute_range_azimuth_heatmap(
        const std::vector<std::vector<std::complex<float>>>& range_fft_data,
        size_t num_virtual_channels,
        size_t num_range_bins,
        float azimuth_field_of_view_deg = 120.0f,
        float azimuth_resolution_deg = 5.0f) {

        const size_t num_azimuth_bins = static_cast<size_t>(
            azimuth_field_of_view_deg / azimuth_resolution_deg);
        Eigen::MatrixXf ra_heatmap(num_range_bins, num_azimuth_bins);

        const float wavelength = SPEED_OF_LIGHT / s_mimo_config.operating_frequency_hz;
        const float azimuth_step = azimuth_resolution_deg * M_PIf32 / 180.0f;

        // Compute array manifold (steering) vectors
        auto manifold = compute_array_manifold(num_azimuth_bins, azimuth_step, wavelength);

        // Beamforming for each range bin
        for (size_t range_idx = 0; range_idx < num_range_bins; ++range_idx) {
            // Form spatial snapshot vector
            Eigen::VectorXcf snapshot(num_virtual_channels);
            for (size_t ch = 0; ch < num_virtual_channels; ++ch) {
                snapshot(ch) = range_fft_data[ch][range_idx];
            }

            // Conventional (Bartlett) beamforming
            for (size_t az_idx = 0; az_idx < num_azimuth_bins; ++az_idx) {
                const Eigen::VectorXcf a = manifold.col(az_idx);
                const std::complex<float> beamformed = a.adjoint() * snapshot;
                ra_heatmap(range_idx, az_idx) = std::norm(beamformed);
            }
        }

        return ra_heatmap;
    }

private:
    MimoConfig s_mimo_config = {
        .num_tx = 3,
        .num_rx = 4,
        .tx_antenna_positions_m = {0.0f, 0.5f, 1.0f},
        .rx_antenna_positions_m = {0.0f, 0.5f, 1.0f, 1.5f},
        .operating_frequency_hz = 77.0e9f
    };

    Eigen::MatrixXcf compute_array_manifold(
        size_t num_angles, float angle_step, float wavelength) {

        const size_t num_virtual = s_mimo_config.num_tx * s_mimo_config.num_rx;
        Eigen::MatrixXcf manifold(num_virtual, num_angles);

        // Compute virtual antenna positions
        std::vector<float> virtual_positions;
        for (float tx_pos : s_mimo_config.tx_antenna_positions_m) {
            for (float rx_pos : s_mimo_config.rx_antenna_positions_m) {
                virtual_positions.push_back(tx_pos + rx_pos);
            }
        }

        for (size_t az_idx = 0; az_idx < num_angles; ++az_idx) {
            const float theta = -M_PIf32 / 2.0f + az_idx * angle_step;
            const float sin_theta = std::sin(theta);

            for (size_t v = 0; v < num_virtual; ++v) {
                const float phase = 2.0f * M_PIf32 *
                    virtual_positions[v] * sin_theta / wavelength;
                manifold(v, az_idx) = std::polar(1.0f, -phase);
            }
        }

        return manifold;
    }
};
```

---

## CFAR Detection

### Constant False Alarm Rate (CFAR) Algorithms

```cpp
/**
 * @brief CFAR detection for target extraction from RD map
 *
 * CFAR types:
 * - CA-CFAR (Cell Averaging): Best for homogeneous background
 * - OS-CFAR (Ordered Statistics): Robust to interfering targets
 * - GO-CFAR (Greatest Of): Good at clutter edges
 * - SO-CFAR (Smallest Of): Better for multiple targets
 *
 * @safety ASIL B
 * @target_false_alarm_rate: 1e-6 (typical)
 */
enum class CfarType {
    CA_CFAR,    // Cell Averaging
    OS_CFAR,    // Ordered Statistics
    GO_CFAR,    // Greatest Of
    SO_CFAR     // Smallest Of
};

struct CfarConfig {
    CfarType type = CfarType::OS_CFAR;
    uint16_t guard_cells = 2;
    uint16_t training_cells = 16;
    float false_alarm_probability = 1e-6f;
    uint8_t os_rank = 12;  // For OS-CFAR: rank in sorted training cells
};

class CfarDetector {
public:
    /**
     * @brief 1D CA-CFAR detection
     * @param power_data Input power data (dB scale)
     * @param config CFAR configuration
     * @return Binary detection vector (1 = target, 0 = noise)
     */
    std::vector<bool> detect_1d_ca_cfar(
        const std::vector<float>& power_data,
        const CfarConfig& config) {

        const size_t n = power_data.size();
        std::vector<bool> detections(n, false);

        // Scale factor for CA-CFAR
        // alpha = N * (P_fa^(-1/N) - 1)
        const float N = static_cast<float>(config.training_cells);
        const float alpha = N * (std::pow(config.false_alarm_probability, -1.0f/N) - 1.0f);

        const uint16_t half_train = config.training_cells / 2;
        const uint16_t half_guard = config.guard_cells;

        for (size_t i = half_train + half_guard; i < n - half_train - half_guard; ++i) {
            // Sum training cells (left and right)
            float sum_left = 0.0f;
            for (size_t j = i - half_train - half_guard; j < i - half_guard; ++j) {
                sum_left += power_data[j];
            }

            float sum_right = 0.0f;
            for (size_t j = i + half_guard + 1; j <= i + half_guard + half_train; ++j) {
                sum_right += power_data[j];
            }

            // Average noise power
            const float noise_power = (sum_left + sum_right) / N;

            // Adaptive threshold
            const float threshold = alpha * noise_power;

            // Detection decision
            if (power_data[i] > threshold) {
                detections[i] = true;
            }
        }

        return detections;
    }

    /**
     * @brief 2D OS-CFAR detection (range-Doppler)
     * @param rd_map Range-Doppler power map
     * @param config CFAR configuration
     * @return List of detected peak positions
     */
    std::vector<std::pair<size_t, size_t>> detect_2d_os_cfar(
        const Eigen::MatrixXf& rd_map,
        const CfarConfig& config) {

        std::vector<std::pair<size_t, size_t>> peaks;
        const size_t num_range = rd_map.rows();
        const size_t num_doppler = rd_map.cols();

        const uint16_t window_size = config.training_cells / 2;
        const uint16_t guard_size = config.guard_cells;

        for (size_t r = window_size + guard_size; r < num_range - window_size - guard_size; ++r) {
            for (size_t d = window_size + guard_size; d < num_doppler - window_size - guard_size; ++d) {
                // Collect training cells (excluding guard cells)
                std::vector<float> training_samples;
                training_samples.reserve(config.training_cells * 4);

                for (int dr = -window_size - guard_size; dr <= window_size + guard_size; ++dr) {
                    for (int dc = -window_size - guard_size; dc <= window_size + guard_size; ++dc) {
                        // Skip guard region and cell under test
                        if (std::abs(dr) <= static_cast<int>(guard_size) &&
                            std::abs(dc) <= static_cast<int>(guard_size)) {
                            continue;
                        }
                        training_samples.push_back(rd_map(r + dr, d + dc));
                    }
                }

                // Sort training samples for OS-CFAR
                std::sort(training_samples.begin(), training_samples.end());

                // Select ranked sample (OS-CFAR)
                const size_t rank_idx = std::min(
                    static_cast<size_t>(config.os_rank),
                    training_samples.size() - 1);
                const float ranked_value = training_samples[rank_idx];

                // Scale factor for OS-CFAR (approximation)
                const float k_os = 1.5f;  // Tuned for target P_fa
                const float threshold = k_os * ranked_value;

                // Detection test
                if (rd_map(r, d) > threshold) {
                    peaks.emplace_back(r, d);
                }
            }
        }

        return peaks;
    }
};
```

### CFAR Safety Mechanisms

```cpp
/**
 * @brief CFAR performance monitoring and fault detection
 * @safety ASIL B
 */
class CfarSafetyMonitor {
public:
    struct CfarHealthStatus {
        float noise_floor_dbm;
        float noise_variance;
        uint32_t detection_count;
        bool interference_detected;
        bool saturation_detected;
        bool clutter_edge_detected;
    };

    CfarHealthStatus monitor_cfar_health(
        const Eigen::MatrixXf& rd_map,
        const std::vector<bool>& cfar_mask) {

        CfarHealthStatus status;

        // Estimate noise floor from training cells
        status.noise_floor_dbm = estimate_noise_floor(rd_map, cfar_mask);

        // Check for abnormal noise variance (interference indicator)
        status.noise_variance = compute_noise_variance(rd_map);
        status.interference_detected = (status.noise_variance > INTERFERENCE_THRESHOLD);

        // Check for receiver saturation
        status.saturation_detected = detect_saturation(rd_map);

        // Count detections
        status.detection_count = std::count(cfar_mask.begin(), cfar_mask.end(), true);

        // Detect clutter edges (rapid noise power change)
        status.clutter_edge_detected = detect_clutter_edge(rd_map);

        return status;
    }

private:
    static constexpr float INTERFERENCE_THRESHOLD = 20.0f;  // dB variance
    static constexpr float SATURATION_LEVEL_DB = -3.0f;     // 3 dB below max

    float estimate_noise_floor(const Eigen::MatrixXf& rd_map,
                                const std::vector<bool>& mask) {
        float sum = 0.0f;
        size_t count = 0;
        for (size_t i = 0; i < mask.size(); ++i) {
            if (!mask[i]) {
                sum += rd_map.data()[i];
                count++;
            }
        }
        return count > 0 ? sum / count : 0.0f;
    }

    bool detect_saturation(const Eigen::MatrixXf& rd_map) {
        const float max_power = rd_map.maxCoeff();
        return max_power > SATURATION_LEVEL_DB;
    }
};
```

---

## 4D Imaging Radar

### Elevation Estimation

```cpp
/**
 * @brief 4D radar processing with elevation angle estimation
 *
 * 4D radar adds elevation dimension using multiple receive antennas
 * in vertical dimension, enabling full 3D point cloud generation.
 *
 * @safety ASIL B
 * @note Elevation resolution: delta_phi = lambda / (N_rx_elev * d)
 */
class ElevationEstimator {
public:
    struct ElevationConfig {
        uint8_t num_rx_elevation;
        std::vector<float> rx_elevation_positions_m;
        float operating_frequency_hz = 77.0e9f;
        size_t fft_size = 32;  // Zero-padded FFT for elevation
    };

    /**
     * @brief Estimate elevation angle via FFT beamforming
     * @param range_azimuth_doppler_data Input data cube
     * @param range_idx Range bin of interest
     * @param doppler_idx Doppler bin of interest
     * @return Elevation spectrum (magnitude vs elevation angle)
     */
    Eigen::VectorXf compute_elevation_spectrum(
        const std::vector<std::complex<float>>& elevation_data,
        const ElevationConfig& config) {

        const size_t num_rx = elevation_data.size();
        const size_t num_elevation_bins = config.fft_size;

        // Zero-pad to FFT size
        std::vector<std::complex<float>> padded(config.fft_size, std::complex<float>(0, 0));
        std::copy(elevation_data.begin(), elevation_data.end(), padded.begin());

        // Apply window
        apply_elevation_window(padded);

        // FFT for elevation estimation
        fft_inplace(padded);

        // Convert to power spectrum
        Eigen::VectorXf spectrum(num_elevation_bins);
        for (size_t i = 0; i < num_elevation_bins; ++i) {
            spectrum(i) = std::norm(padded[i]);
        }

        return spectrum;
    }

    /**
     * @brief Convert elevation FFT bin to angle
     * @param bin_idx FFT bin index
     * @param config Elevation configuration
     * @return Elevation angle in radians
     */
    static float elevation_bin_to_angle(size_t bin_idx, const ElevationConfig& config) {
        const float wavelength = SPEED_OF_LIGHT / config.operating_frequency_hz;
        const float antenna_spacing = wavelength / 2.0f;  // lambda/2 spacing

        // FFT bin to spatial frequency
        const size_t half_fft = config.fft_size / 2;
        const float spatial_freq = (static_cast<int>(bin_idx) - static_cast<int>(half_fft)) /
                                   static_cast<float>(config.fft_size);

        // Spatial frequency to angle
        const float sin_phi = spatial_freq * wavelength / antenna_spacing;

        // Clamp to valid range
        const float clamped = std::max(-1.0f, std::min(1.0f, sin_phi));
        return std::asin(clamped);
    }
};
```

### Point Cloud Generation

```cpp
/**
 * @brief Radar point cloud generation from RD map detections
 */
struct RadarPoint {
    Eigen::Vector3f position_m;     // (x, y, z) in sensor frame
    float range_m;
    float azimuth_rad;
    float elevation_rad;
    float radial_velocity_mps;
    float rcs_db;                   // Radar cross-section estimate
    uint32_t detection_id;
    bool is_valid;
};

class RadarPointCloudGenerator {
public:
    std::vector<RadarPoint> generate_point_cloud(
        const std::vector<std::pair<size_t, size_t>>& rd_peaks,
        const Eigen::MatrixXf& rd_map,
        const Eigen::MatrixXf& ra_map,
        const CfarConfig& cfar_config,
        const FmcwChirpConfig& chirp_config) {

        std::vector<RadarPoint> points;
        points.reserve(rd_peaks.size());

        const float wavelength = SPEED_OF_LIGHT / (chirp_config.f0_hz);
        const float range_resolution = SPEED_OF_LIGHT / (2.0f * chirp_config.bandwidth_hz);
        const float doppler_resolution = 1.0f / (chirp_config.num_chirps * chirp_config.chirp_repetition_time);

        uint32_t point_id = 0;
        for (const auto& peak : rd_peaks) {
            const size_t range_idx = peak.first;
            const size_t doppler_idx = peak.second;

            RadarPoint point;
            point.detection_id = point_id++;

            // Range from FFT bin
            point.range_m = range_idx * range_resolution;

            // Azimuth from RA map peak search
            point.azimuth_rad = find_azimuth_peak(ra_map, range_idx);

            // Elevation (assume 0 for 3D radar, estimated for 4D)
            point.elevation_rad = 0.0f;

            // Velocity from Doppler
            const float doppler_freq = (static_cast<float>(doppler_idx) -
                                        rd_map.cols() / 2.0f) * doppler_resolution;
            point.radial_velocity_mps = doppler_to_velocity(doppler_freq, wavelength);

            // RCS estimate (calibrated)
            point.rcs_db = rd_map(range_idx, doppler_idx) + RCS_CALIBRATION_OFFSET;

            // Convert to Cartesian
            point.position_m.x() = point.range_m * std::cos(point.azimuth_rad);
            point.position_m.y() = point.range_m * std::sin(point.azimuth_rad);
            point.position_m.z() = point.range_m * std::sin(point.elevation_rad);

            point.is_valid = (point.range_m > MIN_RANGE_M) &&
                             (point.range_m < MAX_RANGE_M) &&
                             (std::abs(point.radial_velocity_mps) < MAX_VELOCITY_MPS);

            points.push_back(point);
        }

        return points;
    }

private:
    static constexpr float MIN_RANGE_M = 0.5f;
    static constexpr float MAX_RANGE_M = 250.0f;
    static constexpr float MAX_VELOCITY_MPS = 100.0f;
    static constexpr float RCS_CALIBRATION_OFFSET = -20.0f;  // dB

    float find_azimuth_peak(const Eigen::MatrixXf& ra_map, size_t range_idx) {
        const size_t azimuth_idx = static_cast<size_t>(
            (ra_map.row(range_idx).maxCoeff(&azimuth_idx)));
        // Convert bin to angle (calibrated per antenna geometry)
        return (static_cast<float>(azimuth_idx) - ra_map.cols() / 2.0f) * AZIMUTH_RESOLUTION_RAD;
    }

    static constexpr float AZIMUTH_RESOLUTION_RAD = 5.0f * M_PIf32 / 180.0f;
};
```

---

## Doppler Tracking

### Micro-Doppler Classification

```cpp
/**
 * @brief Micro-Doppler signature analysis for target classification
 *
 * Micro-Doppler arises from moving parts (pedestrian limbs, vehicle wheels)
 * and provides additional classification information beyond RCS.
 *
 * @safety ASIL B (pedestrian/cyclist classification)
 */
struct MicroDopplerFeatures {
    float main_body_doppler_hz;
    float micro_doppler_bandwidth_hz;
    float micro_doppler_period_s;
    float energy_ratio;  // Micro-Doppler energy / total energy
    uint8_t limb_count_estimate;  // For pedestrian detection
};

class MicroDopplerClassifier {
public:
    enum class TargetType {
        UNKNOWN,
        PEDESTRIAN,
        CYCLIST,
        VEHICLE_2WHEEL,
        VEHICLE_4WHEEL,
        ANIMAL
    };

    /**
     * @brief Extract micro-Doppler features from time-frequency representation
     * @param spectrogram Time-frequency spectrogram of target
     * @param target_range Range bin of target
     * @param integration_time_s Integration time for spectrogram
     * @return Extracted micro-Doppler features
     */
    MicroDopplerFeatures extract_features(
        const Eigen::MatrixXf& spectrogram,
        float integration_time_s = 1.0f) {

        MicroDopplerFeatures features;

        // Find main body Doppler (highest energy bin)
        Eigen::Index main_doppler_idx;
        spectrogram.colwise().sum().maxCoeff(&main_doppler_idx);
        features.main_body_doppler_hz = doppler_bin_to_hz(main_doppler_idx);

        // Compute micro-Doppler bandwidth (spread around main Doppler)
        const float threshold_db = spectrogram.maxCoeff() - 10.0f;
        features.micro_doppler_bandwidth_hz = compute_bandwidth(spectrogram, threshold_db);

        // Estimate micro-Doppler period (for periodic motion like walking)
        features.micro_doppler_period_s = estimate_period(spectrogram, integration_time_s);

        // Energy ratio
        features.energy_ratio = compute_micro_doppler_energy_ratio(
            spectrogram, main_doppler_idx);

        return features;
    }

    /**
     * @brief Classify target based on micro-Doppler features
     * @param features Extracted micro-Doppler features
     * @return Target classification
     */
    TargetType classify(const MicroDopplerFeatures& features) {
        // Rule-based classifier (ML-based classifier recommended for production)
        if (features.micro_doppler_period_s > 0.5f &&
            features.micro_doppler_period_s < 1.5f &&
            features.energy_ratio > 0.2f) {
            return TargetType::PEDESTRIAN;  // Walking gait
        }

        if (features.micro_doppler_period_s > 0.1f &&
            features.micro_doppler_period_s < 0.3f &&
            features.micro_doppler_bandwidth_hz > 50.0f) {
            return TargetType::CYCLIST;  // Pedaling motion
        }

        if (features.micro_doppler_bandwidth_hz < 10.0f) {
            return TargetType::VEHICLE_4WHEEL;  // Smooth motion
        }

        return TargetType::UNKNOWN;
    }
};
```

### Joint Tracking and Classification

```cpp
/**
 * @brief Extended Kalman Filter for radar target tracking
 *
 * State vector: [x, y, vx, vy, ax, ay]
 * Measurement: [range, azimuth, range_rate]
 *
 * @safety ASIL B
 */
class RadarTargetTracker {
public:
    struct TrackState {
        uint32_t track_id;
        Eigen::Vector6f state;          // [x, y, vx, vy, ax, ay]
        Eigen::Matrix6f covariance;
        uint32_t age;
        uint32_t missed_detections;
        MicroDopplerClassifier::TargetType classification;
        float classification_confidence;
    };

    /**
     * @brief EKF prediction step
     * @param dt Time step (seconds)
     * @param process_noise_std Process noise standard deviation
     */
    void predict(float dt, float process_noise_std = 1.0f) {
        // State transition matrix (constant acceleration model)
        Eigen::Matrix6f F;
        F << 1, 0, dt, 0, 0.5f*dt*dt, 0,
             0, 1, 0, dt, 0, 0.5f*dt*dt,
             0, 0, 1, 0, dt, 0,
             0, 0, 0, 1, 0, dt,
             0, 0, 0, 0, 1, 0,
             0, 0, 0, 0, 0, 1;

        state_ = F * state_;

        // Process noise covariance
        const float q = process_noise_std * process_noise_std;
        Eigen::Matrix6f Q;
        Q << dt*dt*dt*dt/4, 0, dt*dt*dt/2, 0, dt*dt/2, 0,
             0, dt*dt*dt*dt/4, 0, dt*dt*dt/2, 0, dt*dt/2,
             dt*dt*dt/2, 0, dt*dt, 0, dt, 0,
             0, dt*dt*dt/2, 0, dt*dt, 0, dt,
             dt*dt/2, 0, dt, 0, 1, 0,
             0, dt*dt/2, 0, dt, 0, 1;
        Q *= q;

        covariance_ = F * covariance_ * F.transpose() + Q;
    }

    /**
     * @brief EKF update with radar measurement
     * @param range Measured range (m)
     * @param azimuth Measured azimuth (rad)
     * @param range_rate Measured range rate (m/s)
     * @param measurement_noise Measurement noise covariance
     * @return Innovation (for data association)
     */
    float update(float range, float azimuth, float range_rate,
                 const Eigen::Matrix3f& measurement_noise) {

        // Predicted measurement (non-linear)
        const float x = state_(0);
        const float y = state_(1);
        const float vx = state_(2);
        const float vy = state_(3);

        const float predicted_range = std::sqrt(x*x + y*y);
        const float predicted_azimuth = std::atan2(y, x);
        const float predicted_range_rate = (x*vx + y*vy) / predicted_range;

        // Measurement residual
        Eigen::Vector3f innovation;
        innovation << range - predicted_range,
                      normalize_angle(azimuth - predicted_azimuth),
                      range_rate - predicted_range_rate;

        // Jacobian (measurement matrix)
        Eigen::Matrix3x6f H;
        const float r2 = x*x + y*y;
        const float r = std::sqrt(r2);
        H << x/r, y/r, 0, 0, 0, 0,
             -y/r2, x/r2, 0, 0, 0, 0,
             vx/r - x*(x*vx+y*vy)/pow(r,3), vy/r - y*(x*vx+y*vy)/pow(r,3),
             x/r, y/r, 0, 0;

        // Kalman gain
        const Eigen::Matrix3f S = H * covariance_ * H.transpose() + measurement_noise;
        const Eigen::Matrix6f K = covariance_ * H.transpose() * S.inverse();

        // State update
        state_ += K * innovation;

        // Covariance update (Joseph form for numerical stability)
        const Eigen::Matrix6f I = Eigen::Matrix6f::Identity();
        const Eigen::Matrix6f IKH = I - K * H;
        covariance_ = IKH * covariance_ * IKH.transpose() +
                      K * measurement_noise * K.transpose();

        // Return innovation norm (for JPDA/MHT association)
        return innovation.norm();
    }

private:
    Eigen::Vector6f state_;
    Eigen::Matrix6f covariance_;

    static float normalize_angle(float angle) {
        while (angle > M_PI) angle -= 2.0f * M_PIf32;
        while (angle < -M_PI) angle += 2.0f * M_PIf32;
        return angle;
    }
};
```

---

## Radar-Camera Fusion

### Frustum-Based Association

```cpp
/**
 * @brief Radar-camera fusion via frustum projection
 *
 * Projects radar 3D points onto camera image plane and associates
 * with camera detections based on geometric overlap.
 *
 * @safety ASIL B/C (sensor fusion for AEB/ACC)
 */
class RadarCameraFuser {
public:
    struct FusedObject {
        Eigen::Vector3f position_m;
        Eigen::Vector3f velocity_mps;
        float range_m;
        float azimuth_rad;
        uint8_t class_id;  // From camera
        float camera_confidence;
        float radar_rcs_db;
        bool is_radar_only;
        bool is_camera_only;
    };

    /**
     * @brief Associate radar points with camera detections
     * @param radar_points Radar point cloud
     * @param camera_detections Camera 2D bounding boxes
     * @param camera_intrinsics Camera intrinsic matrix
     * @param extrinsics Radar-to-camera transformation
     * @return Fused object list
     */
    std::vector<FusedObject> associate_radar_camera(
        const std::vector<RadarPoint>& radar_points,
        const std::vector<CameraDetection>& camera_detections,
        const CameraIntrinsics& camera_intrinsics,
        const Eigen::Matrix4f& extrinsics) {

        std::vector<FusedObject> fused_objects;

        for (const auto& radar_pt : radar_points) {
            // Transform radar point to camera frame
            Eigen::Vector4f pt_cam_homogeneous;
            pt_cam_homogeneous << radar_pt.position_m, 1.0f;
            pt_cam_homogeneous = extrinsics * pt_cam_homogeneous;

            Eigen::Vector3f pt_cam = pt_cam_homogeneous.head<3>();

            // Project to image plane
            const Eigen::Vector2f pixel = camera_intrinsics.project(pt_cam);

            // Find overlapping camera detection
            int best_detection_idx = -1;
            float min_distance_px = std::numeric_limits<float>::max();

            for (size_t i = 0; i < camera_detections.size(); ++i) {
                const auto& det = camera_detections[i];
                const float dist_to_center = point_to_box_distance(
                    pixel, det.bbox);

                if (dist_to_center < min_distance_px &&
                    dist_to_center < ASSOCIATION_THRESHOLD_PX) {
                    min_distance_px = dist_to_center;
                    best_detection_idx = static_cast<int>(i);
                }
            }

            // Create fused object
            FusedObject fused;
            fused.position_m = radar_pt.position_m;
            fused.velocity_mps << radar_pt.radial_velocity_mps, 0.0f, 0.0f;
            fused.range_m = radar_pt.range_m;
            fused.azimuth_rad = radar_pt.azimuth_rad;
            fused.radar_rcs_db = radar_pt.rcs_db;

            if (best_detection_idx >= 0) {
                fused.class_id = camera_detections[best_detection_idx].class_id;
                fused.camera_confidence = camera_detections[best_detection_idx].confidence;
                fused.is_radar_only = false;
                fused.is_camera_only = false;
            } else {
                fused.class_id = CLASS_UNKNOWN;  // Radar-only
                fused.camera_confidence = 0.0f;
                fused.is_radar_only = true;
                fused.is_camera_only = false;
            }

            fused_objects.push_back(fused);
        }

        // Add camera-only detections (no radar return)
        for (const auto& cam_det : camera_detections) {
            bool associated = false;
            for (const auto& fused : fused_objects) {
                if (!fused.is_radar_only) {
                    associated = true;
                    break;
                }
            }
            if (!associated) {
                FusedObject cam_only;
                cam_only.class_id = cam_det.class_id;
                cam_only.camera_confidence = cam_det.confidence;
                cam_only.is_camera_only = true;
                cam_only.is_radar_only = false;
                fused_objects.push_back(cam_only);
            }
        }

        return fused_objects;
    }

private:
    static constexpr float ASSOCIATION_THRESHOLD_PX = 50.0f;
    static constexpr uint8_t CLASS_UNKNOWN = 255;

    float point_to_box_distance(const Eigen::Vector2f& point,
                                 const cv::Rect& box) {
        // Find closest point on box boundary
        const float cx = box.x + box.width / 2.0f;
        const float cy = box.y + box.height / 2.0f;
        return std::sqrt(std::pow(point.x() - cx, 2) + std::pow(point.y() - cy, 2));
    }
};
```

### Ghost Target Mitigation

```cpp
/**
 * @brief Ghost target detection and mitigation
 *
 * Ghost targets arise from multipath reflections (e.g., guardrails,
 * tunnel walls) and must be filtered to prevent false braking.
 *
 * @safety ASIL B (false positive reduction for AEB)
 */
class GhostTargetFilter {
public:
    struct GhostProbability {
        float probability;  // 0.0 (real) to 1.0 (ghost)
        std::string reason;
    };

    GhostProbability assess_ghost_probability(
        const RadarPoint& point,
        const std::vector<RadarPoint>& all_points,
        const MapData& map_data) {

        GhostProbability prob;
        prob.probability = 0.0f;
        prob.reason = "";

        // Test 1: Check for plausible reflector (metal surface nearby)
        const bool has_reflector = map_data.has_guardrail_nearby(
            point.position_m, REFLECTOR_SEARCH_RADIUS_M);
        if (has_reflector) {
            prob.probability += 0.3f;
            prob.reason += "Guardrail nearby; ";
        }

        // Test 2: Check for kinematic implausibility
        const bool implausible_motion = is_kinematically_implausible(point, all_points);
        if (implausible_motion) {
            prob.probability += 0.3f;
            prob.reason += "Implausible motion; ";
        }

        // Test 3: Check for RCS inconsistency
        const bool rcs_anomaly = is_rcs_inconsistent(point);
        if (rcs_anomaly) {
            prob.probability += 0.2f;
            prob.reason += "RCS anomaly; ";
        }

        // Test 4: Check for geometric inconsistency (behind wall)
        const bool behind_surface = map_data.is_point_behind_surface(
            point.position_m);
        if (behind_surface) {
            prob.probability += 0.4f;
            prob.reason += "Behind surface; ";
        }

        // Test 5: Check for Doppler inconsistency
        const bool doppler_anomaly = is_doppler_inconsistent(point);
        if (doppler_anomaly) {
            prob.probability += 0.2f;
            prob.reason += "Doppler anomaly; ";
        }

        // Clamp probability
        prob.probability = std::min(1.0f, prob.probability);

        return prob;
    }

    bool filter_ghost(const RadarPoint& point,
                       const std::vector<RadarPoint>& all_points,
                       const MapData& map_data,
                       float threshold = 0.5f) {
        const GhostProbability ghost_prob = assess_ghost_probability(
            point, all_points, map_data);
        return ghost_prob.probability > threshold;
    }

private:
    static constexpr float REFLECTOR_SEARCH_RADIUS_M = 5.0f;

    bool is_kinematically_implausible(const RadarPoint& point,
                                       const std::vector<RadarPoint>& all_points) {
        // Check if point velocity is inconsistent with traffic flow
        // Ghost targets often show stationary or erratic velocities
        return std::abs(point.radial_velocity_mps) < 0.1f &&
               point.range_m > MIN_DYNAMIC_OBJECT_RANGE_M;
    }

    bool is_rcs_inconsistent(const RadarPoint& point) {
        // Check if RCS is inconsistent with object size
        // Ghost targets often have anomalously low RCS
        return point.rcs_db < EXPECTED_MIN_RCS_DB;
    }

    bool is_doppler_inconsistent(const RadarPoint& point) {
        // Check if Doppler velocity matches geometric range rate
        // Ghost targets show Doppler-range rate mismatch
        return false;  // Requires additional computation
    }

    static constexpr float MIN_DYNAMIC_OBJECT_RANGE_M = 10.0f;
    static constexpr float EXPECTED_MIN_RCS_DB = -10.0f;
};
```

---

## Performance Benchmarks

### Radar Processing Latency Budget

| Processing Stage | WCET (ms) | Platform | ASIL |
|-----------------|-----------|----------|------|
| Range FFT (128 chirps x 256 samples) | 0.8 | Jacinto TDA4VM C66x | B |
| Doppler FFT | 0.6 | Jacinto TDA4VM C66x | B |
| CFAR detection (2D OS-CFAR) | 1.2 | Jacinto TDA4VM C66x | B |
| Clustering (DBSCAN) | 0.5 | Jacinto TDA4VM C66x | B |
| Tracking (EKF, 50 tracks) | 0.4 | Jacinto TDA4VM C66x | B |
| **Total Processing** | **< 4.0 ms** | Jacinto TDA4VM | B |

### Detection Performance Targets

| Metric | Highway ACC | Urban AEB | Blind Spot |
|--------|-------------|-----------|------------|
| Max Range | 200 m | 80 m | 50 m |
| Min Range | 1 m | 0.5 m | 1 m |
| Range Accuracy | < 0.5 m | < 0.3 m | < 0.5 m |
| Velocity Accuracy | < 0.5 m/s | < 0.3 m/s | < 1.0 m/s |
| Azimuth Accuracy | < 1 deg | < 2 deg | < 3 deg |
| False Positive Rate | < 0.01 / km | < 0.001 / km | < 0.1 / km |

---

## Safety Mechanisms

### Radar Health Monitoring

```cpp
/**
 * @brief Radar system health monitoring
 * @safety ASIL B
 */
class RadarHealthMonitor {
public:
    struct RadarHealthStatus {
        bool is_operational;
        float noise_floor_dbm;
        float tx_power_dbm;
        float receiver_gain_db;
        bool interference_detected;
        bool water_ingress_detected;
        float temperature_celsius;
        uint32_t fault_codes;
    };

    RadarHealthStatus check_health(const RawAdcData& adc_data) {
        RadarHealthStatus status;

        // Noise floor check
        status.noise_floor_dbm = estimate_noise_floor(adc_data);
        status.is_operational = (status.noise_floor_dbm > NOISE_FLOOR_MIN_DBM) &&
                                (status.noise_floor_dbm < NOISE_FLOOR_MAX_DBM);

        // TX power monitoring
        status.tx_power_dbm = measure_tx_power();
        status.is_operational &= (status.tx_power_dbm > TX_POWER_MIN_DBM);

        // Receiver gain check
        status.receiver_gain_db = measure_receiver_gain();
        status.is_operational &= (status.receiver_gain_db > GAIN_MIN_DB);

        // Interference detection (high variance in noise floor)
        status.interference_detected = detect_interference(adc_data);
        if (status.interference_detected) {
            status.fault_codes |= FAULT_INTERFERENCE;
        }

        // Water ingress detection (dielectric loading)
        status.water_ingress_detected = detect_water_ingress(adc_data);
        if (status.water_ingress_detected) {
            status.fault_codes |= FAULT_WATER_INGRESS;
        }

        // Temperature monitoring
        status.temperature_celsius = read_temperature_sensor();
        status.is_operational &= (status.temperature_celsius > TEMP_MIN_C) &&
                                 (status.temperature_celsius < TEMP_MAX_C);

        return status;
    }

private:
    static constexpr float NOISE_FLOOR_MIN_DBM = -100.0f;
    static constexpr float NOISE_FLOOR_MAX_DBM = -70.0f;
    static constexpr float TX_POWER_MIN_DBM = 10.0f;
    static constexpr float GAIN_MIN_DB = 20.0f;
    static constexpr float TEMP_MIN_C = -40.0f;
    static constexpr float TEMP_MAX_C = 85.0f;

    static constexpr uint32_t FAULT_INTERFERENCE = 0x0001;
    static constexpr uint32_t FAULT_WATER_INGRESS = 0x0002;
};
```

---

## Required Dependencies

```cpp
// Required dependencies for radar processing:
// - Eigen 3.4+ for linear algebra (EKF, beamforming)
// - FFTW 3.3+ or ARM CMSIS-DSP for FFT operations
// - OpenCV 4.8+ for camera fusion (image projection)
// - AUTOSAR MCAL drivers for radar sensor interface
// - CUDA 12.x for GPU-accelerated processing (optional, 4D radar)
```

---

## Related Context Files

- @context/skills/adas/sensor-fusion.md — EKF/UKF for multi-sensor fusion
- @context/skills/adas/camera-processing.md — Camera detection for fusion
- @knowledge/standards/iso26262/2-conceptual.md — ASIL classification
- @knowledge/standards/iso21448/1-overview.md — SOTIF triggering conditions

---

## Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|-----------|
| Stationary object detection | Radar struggles with stopped vehicles | Fuse with camera, use HD map |
| Low azimuth resolution (5 deg typical) | Poor lateral positioning | 4D imaging radar (1 deg), sensor fusion |
| Multipath in urban canyons | Ghost targets, false positives | Ghost target filter, map validation |
| Rain attenuation (77 GHz) | Reduced range in heavy rain | Degrade confidence, rely on camera |
| Metal surface reflections | False barriers, ghost objects | Multi-frame validation, clustering |

---

*This context file supports @context/skills/adas/radar-processing.md @-mentions in the ADAS perception engineer custom instruction.*
