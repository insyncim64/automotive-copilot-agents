# SOTIF Testing (ISO 21448)

> Safety of the Intended Functionality - testing methodologies to identify and
> validate against triggering conditions where the system behaves correctly
> according to specifications but still produces hazardous outcomes due to
> functional limitations, sensor performance boundaries, or environmental factors.

**Standards Compliance:**
- ISO 21448 (SOTIF) - All parts
- ISO 26262 (Functional Safety) - Complementary
- Euro NCAP / C-NCAP - Test protocols
- UL 4600 - Autonomous product safety

---

## Domain Expertise

| Category | Methods/Tools | When to Use |
|----------|--------------|-------------|
| **Triggering Condition Analysis** | HARA linkage, Scenario cataloging, ODD boundary analysis | Early development, hazard identification |
| **Scenario-Based Testing** | Criticality assessment, Parameter variation, Edge case generation | Validation, coverage measurement |
| **Environmental Simulation** | Weather injection, Lighting simulation, Road surface modeling | SIL/HIL, reproducible testing |
| **Sensor Performance Modeling** | Noise injection, Degradation simulation, Blind spot analysis | Algorithm robustness validation |
| **Misuse Analysis** | Driver behavior modeling, ODD violation detection, Over-reliance scenarios | Human factors validation |
| **Coverage Metrics** | Scenario coverage, Triggering condition coverage, ODD coverage | Release gates, safety case |

---

## SOTIF vs ISO 26262

| Aspect | ISO 26262 | ISO 21448 (SOTIF) |
|--------|-----------|-------------------|
| **Addresses** | Systematic/random HW faults | Functional insufficiencies |
| **Root Cause** | Design errors, HW failures | Correct design but limited capability |
| **Example** | Software bug in brake calc | Radar fails to detect pedestrian in rain |
| **Goal** | Freedom from unreasonable risk due to faults | Absence of unreasonable risk due to intended functionality |
| **Key Activity** | FMEA, FTA, code review | Triggering condition analysis, validation |

---

## Triggering Condition Framework

### Triggering Condition Categories

```yaml
triggering_condition_registry:
  environmental:
    - id: TC-ENV-001
      category: precipitation
      name: "Heavy Rain Attenuation"
      description: "Rain intensity > 50mm/hour attenuates LiDAR signal"
      affected_sensors: [LiDAR, Camera]
      severity: high
      detection_method: "Rain sensor + LiDAR return rate monitoring"
      mitigation: "Increase radar fusion weight, reduce confidence"
      validation_status: validated
      test_coverage: 95%

    - id: TC-ENV-002
      category: visibility
      name: "Fog Scattering"
      description: "Fog with visibility < 100m scatters LiDAR/Camera signals"
      affected_sensors: [LiDAR, Camera]
      severity: critical
      detection_method: "Visibility estimation from camera contrast"
      mitigation: "Radar-primary mode, request driver takeover"
      validation_status: validated
      test_coverage: 90%

    - id: TC-ENV-003
      category: road_surface
      name: "Standing Water Reflection"
      description: "Water puddles create ghost objects in LiDAR/Camera"
      affected_sensors: [LiDAR, Camera]
      severity: medium
      detection_method: "Ground plane analysis, reflectivity check"
      mitigation: "Temporal filtering, height-based rejection"
      validation_status: in_progress
      test_coverage: 75%

  sensor_limitations:
    - id: TC-SENSOR-001
      category: camera_saturation
      name: "Low-Angle Sun Glare"
      description: "Direct sunlight at dawn/dusk saturates camera sensor"
      affected_sensors: [Camera]
      severity: critical
      detection_method: "Sun position calculation + pixel saturation monitoring"
      mitigation: "Sun-aware trajectory planning, rely on radar/LiDAR"
      validation_status: validated
      test_coverage: 92%

    - id: TC-SENSOR-002
      category: lidar_blind_spot
      name: "Low-Reflectivity Objects"
      description: "Black/dark objects have reduced LiDAR return signal"
      affected_sensors: [LiDAR]
      severity: high
      detection_method: "Return intensity monitoring, dropout detection"
      mitigation: "Camera-LiDAR fusion, temporal accumulation"
      validation_status: validated
      test_coverage: 88%

    - id: TC-SENSOR-003
      category: radar_multipath
      name: "Tunnel Wall Reflections"
      description: "Radar signals reflect off tunnel walls creating ghost objects"
      affected_sensors: [Radar]
      severity: medium
      detection_method: "Tunnel detection via map + GPS denial"
      mitigation: "Static object filtering, height-based validation"
      validation_status: in_progress
      test_coverage: 70%

  target_properties:
    - id: TC-TARGET-001
      category: pedestrian
      name: "Dark Clothing at Night"
      description: "Pedestrians in dark clothing have low camera contrast at night"
      affected_sensors: [Camera, LiDAR]
      severity: critical
      detection_method: "IR illumination, thermal signature (if available)"
      mitigation: "Radar-primary, reduced speed, increased following distance"
      validation_status: validated
      test_coverage: 85%

    - id: TC-TARGET-002
      category: vehicle
      name: "Cut-in Vehicle with Low Reflectivity"
      description: "Matte black vehicles have reduced radar cross-section"
      affected_sensors: [Radar]
      severity: high
      detection_method: "Camera confirmation, LiDAR point density"
      mitigation: "Multi-sensor fusion, conservative following distance"
      validation_status: validated
      test_coverage: 90%

  operational_scenarios:
    - id: TC-OPS-001
      category: traffic_density
      name: "Dense Urban Cut-in Cascade"
      description: "Multiple vehicles cutting in rapid succession in dense traffic"
      affected_functions: [ACC, LKA, AEB]
      severity: high
      detection_method: "Object count rate, time-to-collision monitoring"
      mitigation: "Increased following distance, driver warning"
      validation_status: validated
      test_coverage: 80%

    - id: TC-OPS-002
      category: infrastructure
      name: "Construction Zone with Temporary Markings"
      description: "Temporary lane markings conflict with permanent markings"
      affected_functions: [LKA, Lane Departure Warning]
      severity: medium
      detection_method: "Map mismatch detection, marking quality assessment"
      mitigation: "Request driver takeover, reduced automation level"
      validation_status: in_progress
      test_coverage: 65%

  misuse_scenarios:
    - id: TC-MISUSE-001
      category: over_reliance
      name: "Driver Distraction During L2 Operation"
      description: "Driver engages in non-driving tasks assuming full automation"
      affected_functions: [L2 Combined ACC+LKA]
      severity: high
      detection_method: "Driver monitoring camera, hands-on-wheel sensor"
      mitigation: "Escalating warnings, safe stop if unresponsive"
      validation_status: validated
      test_coverage: 95%

    - id: TC-MISUSE-002
      category: odd_violation
      name: "Operating Outside ODD Speed Range"
      description: "Attempting to engage L2 at speeds below/above ODD limits"
      affected_functions: [L2 System]
      severity: medium
      detection_method: "Vehicle speed vs ODD bounds check"
      mitigation: "Prevent activation, clear driver notification"
      validation_status: validated
      test_coverage: 100%
```

---

## Scenario-Based Testing Methodology

### Scenario Classification (Pegasus Method)

```yaml
scenario_layers:
  layer_1_functional:
    description: "Abstract functional description"
    example: "Lane change maneuver"
    test_count: ~10

  layer_2_logical:
    description: "Parameterized scenario with ranges"
    parameters:
      - ego_speed: [30, 130] km/h
      - relative_speed: [-50, +50] km/h
      - distance_to_lead_vehicle: [5, 200] m
      - weather: [clear, rain, fog]
      - time_of_day: [day, dawn, dusk, night]
    test_count: ~1,000 (via DOE)

  layer_3_concrete:
    description: "Fully instantiated test case"
    example: "Lane change at 80 km/h, lead vehicle at 70 km/h, 50m gap, light rain, dusk"
    test_count: ~10,000+ (via variation)
```

### Criticality Assessment

```cpp
struct ScenarioCriticality {
    // Time-to-Collision (TTC) based criticality
    float ttc_seconds;

    // Time-to-Brake (TTB) - latest possible braking point
    float ttb_seconds;

    // Time-to-Steer (TTS) - latest possible evasion point
    float tts_seconds;

    // Kinematic Time-to-Collision (TTCk)
    float ttck_seconds;

    // Required acceleration to avoid collision
    float required_deceleration_mps2;

    // Criticality score (0-1, higher = more critical)
    float criticality_score;
};

class CriticalityCalculator {
public:
    ScenarioCriticality calculate(
        const EgoVehicleState& ego,
        const std::vector<DynamicObject>& objects,
        const RoadGeometry& road) {

        ScenarioCriticality result;

        // Find most critical object
        const DynamicObject* critical_object = find_closest_in_path(ego, objects);
        if (!critical_object) {
            result.criticality_score = 0.0f;
            return result;
        }

        // Calculate TTC
        const float relative_distance = calculate_distance(ego, *critical_object);
        const float relative_speed = ego.speed - critical_object->speed;

        if (relative_speed > 0.1f) {
            result.ttc_seconds = relative_distance / relative_speed;
        } else {
            result.ttc_seconds = std::numeric_limits<float>::max();
        }

        // Calculate required deceleration
        result.required_deceleration_mps2 =
            calculate_required_deceleration(relative_distance, relative_speed);

        // Criticality scoring
        if (result.ttc_seconds < 2.0f) {
            result.criticality_score = 1.0f;  // Critical
        } else if (result.ttc_seconds < 4.0f) {
            result.criticality_score = 0.7f;  // High
        } else if (result.ttc_seconds < 6.0f) {
            result.criticality_score = 0.4f;  // Medium
        } else {
            result.criticality_score = 0.0f;  // Safe
        }

        return result;
    }

private:
    float calculate_required_deceleration(float distance, float relative_speed) {
        // v^2 = u^2 + 2as => a = -u^2 / (2s)
        return -(relative_speed * relative_speed) / (2.0f * distance);
    }
};
```

---

## Test Scenario Generation

### Combinatorial Testing (Design of Experiments)

```cpp
struct ScenarioParameter {
    std::string name;
    std::vector<float> values;  // Discrete values to test
    bool critical;              // Is this a safety-critical parameter?
};

class ScenarioGenerator {
public:
    // Full factorial - all combinations (expensive)
    std::vector<TestScenario> generate_full_factorial(
        const std::vector<ScenarioParameter>& parameters) {

        std::vector<TestScenario> scenarios;

        // Calculate total combinations
        size_t total = 1;
        for (const auto& param : parameters) {
            total *= param.values.size();
        }

        // Generate all combinations
        for (size_t i = 0; i < total; i++) {
            TestScenario scenario;
            size_t remaining = i;

            for (const auto& param : parameters) {
                const size_t idx = remaining % param.values.size();
                scenario.parameters[param.name] = param.values[idx];
                remaining /= param.values.size();
            }

            scenarios.push_back(scenario);
        }

        return scenarios;
    }

    // Pairwise testing - all pairs of parameter values (efficient)
    std::vector<TestScenario> generate_pairwise(
        const std::vector<ScenarioParameter>& parameters) {

        // Uses orthogonal arrays or IPOG algorithm
        // Significantly reduces test count while maintaining coverage
        return generate_orthogonal_array(parameters);
    }

    // Boundary value analysis
    std::vector<TestScenario> generate_boundary_values(
        const ScenarioParameter& param) {

        std::vector<TestScenario> scenarios;

        // Test min, min+epsilon, nominal, max-epsilon, max
        const float epsilon = (param.values.back() - param.values.front()) * 0.01f;

        scenarios.push_back(create_scenario(param.name, param.values.front()));
        scenarios.push_back(create_scenario(param.name, param.values.front() + epsilon));
        scenarios.push_back(create_scenario(param.name,
            (param.values.front() + param.values.back()) / 2.0f));
        scenarios.push_back(create_scenario(param.name, param.values.back() - epsilon));
        scenarios.push_back(create_scenario(param.name, param.values.back()));

        return scenarios;
    }
};
```

### Edge Case Mining from Real Data

```python
# Edge case extraction from fleet data
class EdgeCaseMiner:
    def __init__(self, data_lake_connection: str):
        self.connection = data_lake_connection
        self.edge_case_thresholds = {
            'ttc_min': 2.5,  # seconds
            'thw_min': 1.0,  # seconds
            'lateral_accel_max': 3.0,  # m/s^2
            'longitudinal_jerk_max': 5.0,  # m/s^3
            'visibility_range_min': 50.0,  # meters
        }

    def extract_edge_cases(self, time_range: Tuple[str, str]) -> List[Scenario]:
        """Extract edge cases from fleet telemetry data."""

        query = """
        SELECT
            scenario_id, timestamp, location, weather,
            ttc_min, thw_min, lateral_accel,
            perception_confidence_min, object_count_max
        FROM fleet_telemetry
        WHERE timestamp BETWEEN %s AND %s
          AND (
            ttc_min < %s
            OR thw_min < %s
            OR ABS(lateral_accel) > %s
            OR perception_confidence_min < 0.5
          )
        """

        cursor = self.connection.cursor()
        cursor.execute(query, (
            time_range[0], time_range[1],
            self.edge_case_thresholds['ttc_min'],
            self.edge_case_thresholds['thw_min'],
            self.edge_case_thresholds['lateral_accel_max']
        ))

        edge_cases = []
        for row in cursor.fetchall():
            edge_cases.append(self._row_to_scenario(row))

        return edge_cases

    def cluster_edge_cases(self, scenarios: List[Scenario]) -> List[ScenarioCluster]:
        """Cluster similar edge cases to identify patterns."""

        # Feature extraction
        features = np.array([
            [s.ttc_min, s.thw_min, s.lateral_accel,
             s.perception_confidence_min, s.object_count_max]
            for s in scenarios
        ])

        # DBSCAN clustering
        clustering = DBSCAN(eps=0.5, min_samples=10)
        labels = clustering.fit_predict(features)

        # Group by cluster
        clusters = defaultdict(list)
        for scenario, label in zip(scenarios, labels):
            if label != -1:  # Not noise
                clusters[label].append(scenario)

        return [
            ScenarioCluster(
                cluster_id=cluster_id,
                scenarios=scenarios,
                representative=self._find_representative(scenarios)
            )
            for cluster_id, scenarios in clusters.items()
        ]
```

---

## Environmental Simulation

### Weather Injection (CARLA)

```python
# CARLA weather simulation for SOTIF testing
import carla

class WeatherSimulator:
    def __init__(self, carla_client: carla.Client):
        self.client = carla_client
        self.world = self.client.get_world()

    def set_weather_condition(self, condition: str, intensity: float = 1.0):
        """Apply weather condition with specified intensity (0.0-1.0)."""

        if condition == 'clear':
            weather = carla.WeatherParameters.ClearNoon
        elif condition == 'rain':
            weather = carla.WeatherParameters(
                cloudiness=80.0 * intensity,
                precipitation=100.0 * intensity,
                precipitation_deposits=80.0 * intensity,
                wetness=100.0 * intensity,
                fog_density=20.0 * intensity,
                sun_altitude_angle=45.0
            )
        elif condition == 'fog':
            weather = carla.WeatherParameters(
                cloudiness=70.0,
                fog_density=90.0 * intensity,
                fog_distance=50.0 * (1.0 - intensity),
                fog_falloff=2.0
            )
        elif condition == 'snow':
            weather = carla.WeatherParameters(
                cloudiness=90.0,
                precipitation=50.0 * intensity,
                precipitation_type=carla.WeatherPrecision.Millimeters,
                wetness=30.0,
                sun_altitude_angle=30.0
            )
        elif condition == 'dust':
            weather = carla.WeatherParameters(
                cloudiness=60.0,
                dust_storm=100.0 * intensity
            )
        else:
            raise ValueError(f"Unknown weather condition: {condition}")

        self.world.set_weather(weather)

    def simulate_sun_glare(self, azimuth: float, elevation: float):
        """Simulate low-angle sun causing camera glare."""

        weather = self.world.get_weather()
        weather.sun_azimuth_angle = azimuth
        weather.sun_altitude_angle = elevation  # Low angle: 5-15 degrees
        weather.cloudiness = 0.0  # Clear sky for maximum glare
        self.world.set_weather(weather)

        # Log sun position relative to vehicle
        vehicle_transform = self._get_ego_vehicle_transform()
        relative_sun_angle = self._calculate_relative_sun_angle(
            vehicle_transform, azimuth, elevation
        )
        self._log_glare_condition(relative_sun_angle)
```

### Sensor Noise Modeling

```cpp
// Sensor noise injection for robustness testing
class SensorNoiseModel {
public:
    struct CameraNoiseParams {
        float gaussian_noise_std;      // Photon shot noise
        float salt_pepper_rate;        // Hot/dead pixels
        float motion_blur_strength;    // Motion blur kernel size
        float bloom_strength;          // Lens bloom for bright lights
        float chromatic_aberration;    // Color fringing
    };

    struct LidarNoiseParams {
        float range_noise_std;         // Range measurement noise (meters)
        float angle_noise_std;         // Angular noise (degrees)
        float dropout_rate;            // Random point dropout
        float multipath_rate;          // Ghost returns
        float reflectivity_bias;       // Intensity bias
        float rain_attenuation;        // Rain-induced attenuation
    };

    struct RadarNoiseParams {
        float range_noise_std;
        float velocity_noise_std;
        float azimuth_noise_std;
        float clutter_rate;            // Ground clutter
        float multipath_rate;
    };

    // Apply noise to camera image
    static cv::Mat apply_camera_noise(
        const cv::Mat& clean_image,
        const CameraNoiseParams& params,
        std::mt19937& rng) {

        cv::Mat noisy_image = clean_image.clone();

        // Gaussian noise
        if (params.gaussian_noise_std > 0.0f) {
            cv::Mat noise(noisy_image.size(), noisy_image.type());
            cv::randn(rng, noise, cv::Scalar(0, 0, 0),
                      cv::Scalar(params.gaussian_noise_std,
                                params.gaussian_noise_std,
                                params.gaussian_noise_std));
            cv::add(noisy_image, noise, noisy_image);
        }

        // Salt-and-pepper noise
        if (params.salt_pepper_rate > 0.0f) {
            apply_salt_pepper_noise(noisy_image, params.salt_pepper_rate, rng);
        }

        // Motion blur (directional)
        if (params.motion_blur_strength > 0.0f) {
            cv::Mat kernel = create_motion_blur_kernel(
                params.motion_blur_strength, 0.0f, rng);  // Random direction
            cv::filter2D(noisy_image, noisy_image, -1, kernel);
        }

        // Bloom effect (for bright regions)
        if (params.bloom_strength > 0.0f) {
            apply_bloom_effect(noisy_image, params.bloom_strength);
        }

        return noisy_image;
    }

    // Apply noise to LiDAR point cloud
    static PointCloud apply_lidar_noise(
        const PointCloud& clean_cloud,
        const LidarNoiseParams& params,
        std::mt19937& rng) {

        PointCloud noisy_cloud;
        noisy_cloud.reserve(clean_cloud.size());

        std::normal_distribution<float> range_noise(0.0f, params.range_noise_std);
        std::normal_distribution<float> angle_noise(0.0f,
            params.angle_noise_std * M_PI / 180.0f);
        std::uniform_real_distribution<float> dropout(0.0f, 1.0f);
        std::uniform_real_distribution<float> multipath(0.0f, 1.0f);

        for (const auto& point : clean_cloud) {
            // Random dropout
            if (dropout(rng) < params.dropout_rate) {
                continue;
            }

            // Range noise
            PointCloud::PointType noisy_point = point;
            const float range = std::sqrt(
                point.x * point.x + point.y * point.y + point.z * point.z);
            const float noisy_range = range + range_noise(rng);

            // Angle noise (simplified - azimuth only)
            const float azimuth = std::atan2(point.y, point.x);
            const float noisy_azimuth = azimuth + angle_noise(rng);

            // Reproject
            const float elevation = std::atan2(point.z,
                std::sqrt(point.x * point.x + point.y * point.y));
            noisy_point.x = noisy_range * std::cos(noisy_azimuth) * std::cos(elevation);
            noisy_point.y = noisy_range * std::sin(noisy_azimuth) * std::cos(elevation);
            noisy_point.z = noisy_range * std::sin(elevation);

            // Multipath (ghost returns)
            if (multipath(rng) < params.multipath_rate) {
                PointCloud::PointType ghost = noisy_point;
                ghost.x *= 1.2f;  // Ghost appears further away
                ghost.intensity *= 0.3f;  // Ghost has lower intensity
                noisy_cloud.push_back(ghost);
            }

            noisy_point.intensity = point.intensity * (1.0f - params.rain_attenuation);
            noisy_cloud.push_back(noisy_point);
        }

        return noisy_cloud;
    }
};
```

---

## SOTIF Hazard Analysis

### Hazard Identification Process

```cpp
struct SotifHazard {
    std::string hazard_id;
    std::string triggering_condition;
    std::string affected_function;
    std::string potential_harm;
    unsigned int severity;      // 1-4 (S0-S3 per ISO 26262)
    unsigned int exposure;      // 1-5 (E0-E4)
    std::string mitigation_strategy;
    bool mitigation_validated;
};

class SotifHazardAnalyzer {
public:
    // Systematic hazard identification using guidewords
    std::vector<SotifHazard> identify_hazards(
        const SystemArchitecture& architecture,
        const OddDefinition& odd) {

        std::vector<SotifHazard> hazards;

        // Guideword-based analysis
        const std::vector<std::string> guidewords = {
            "too_early", "too_late", "too_short", "too_long",
            "too_much", "too_little", "wrong_value", "missing",
            "unexpected", "ambiguous", "incomplete"
        };

        for (const auto& sensor : architecture.sensors) {
            for (const auto& guideword : guidewords) {
                auto sensor_hazards = analyze_sensor_with_guideword(
                    sensor, guideword, odd);
                hazards.insert(hazards.end(),
                    sensor_hazards.begin(), sensor_hazards.end());
            }
        }

        for (const auto& function : architecture.functions) {
            for (const auto& guideword : guidewords) {
                auto function_hazards = analyze_function_with_guideword(
                    function, guideword, odd);
                hazards.insert(hazards.end(),
                    function_hazards.begin(), function_hazards.end());
            }
        }

        return hazards;
    }

private:
    std::vector<SotifHazard> analyze_sensor_with_guideword(
        const Sensor& sensor,
        const std::string& guideword,
        const OddDefinition& odd) {

        std::vector<SotifHazard> hazards;

        // Example: Camera + "too_little" + "night" = insufficient light
        if (sensor.type == "camera" && guideword == "too_little") {
            hazards.push_back({
                .hazard_id = generate_id("CAM", "TL", "NIGHT"),
                .triggering_condition = "Low light conditions (night, tunnel)",
                .affected_function = "Object detection, lane detection",
                .potential_harm = "Undetected obstacles, lane departure",
                .severity = 3,  // S3 - Life-threatening
                .exposure = 4,  // E4 - Daily occurrence (night driving)
                .mitigation_strategy = "IR illumination, radar fusion, reduced speed",
                .mitigation_validated = false
            });
        }

        // Example: LiDAR + "too_little" + "rain" = signal attenuation
        if (sensor.type == "lidar" && guideword == "too_little") {
            hazards.push_back({
                .hazard_id = generate_id("LIDAR", "TL", "RAIN"),
                .triggering_condition = "Heavy rain (>50mm/hr)",
                .affected_function = "3D object detection, free space detection",
                .potential_harm = "Undetected obstacles, false free space",
                .severity = 3,  // S3
                .exposure = 3,  // E3 - Medium probability
                .mitigation_strategy = "Radar-primary mode, confidence reduction",
                .mitigation_validated = false
            });
        }

        return hazards;
    }
};
```

---

## Test Coverage Metrics

### SOTIF Coverage Framework

```yaml
sotif_coverage_metrics:
  triggering_condition_coverage:
    description: "Percentage of identified triggering conditions with validation tests"
    formula: "validated_TCs / total_identified_TCs * 100"
    target: ">= 95%"
    gate: release_blocking

  scenario_coverage:
    description: "Percentage of logical scenario space covered"
    formula: "tested_scenarios / total_logical_scenarios * 100"
    target: ">= 90%"
    sub_metrics:
      - parameter_coverage: "Each parameter value tested at least once"
      - pair_coverage: "Each pair of parameter values tested together"
      - critical_scenario_coverage: "All critical scenarios (TTC < 4s) tested"

  odd_coverage:
    description: "Percentage of ODD envelope validated"
    breakdown:
      road_types:
        - highway: "Tested with X scenarios"
        - urban_expressway: "Tested with Y scenarios"
        - urban_arterial: "Tested with Z scenarios"
      speed_range:
        - min_speed: "0 km/h - stationary tests"
        - typical_speed: "30-80 km/h - normal operation"
        - max_speed: "120-130 km/h - high speed tests"
      weather_conditions:
        - clear: "Baseline validation"
        - light_rain: "Light precipitation tests"
        - heavy_rain: "SOTIF boundary tests"
        - fog: "Visibility limitation tests"
      lighting_conditions:
        - daylight: "Standard validation"
        - dawn_dusk: "Low-angle sun glare tests"
        - night: "Low-light performance tests"
        - tunnel_transition: "Light adaptation tests"

  sensor_performance_coverage:
    description: "Sensor operating envelope validated"
    metrics:
      - range_coverage: "Tested from min to max range in steps"
      - fov_coverage: "Tested across full FOV (center, edges, corners)"
      - reflectivity_coverage: "Tested with high/medium/low reflectivity targets"
      - contrast_coverage: "Tested with varying target-background contrast"

  misuse_coverage:
    description: "Foreseeable misuse scenarios validated"
    target: ">= 90%"
    categories:
      - over_reliance: "Driver assumes higher automation than available"
      - odd_violation: "Operating outside defined ODD"
      - hmi_confusion: "Misunderstanding system state or capabilities"
```

### Coverage Measurement Tool

```python
# SOTIF coverage measurement and reporting
class SotifCoverageAnalyzer:
    def __init__(self, triggering_conditions: List[TriggeringCondition],
                 scenario_catalog: List[Scenario],
                 odd_definition: OddDefinition):
        self.triggering_conditions = triggering_conditions
        self.scenario_catalog = scenario_catalog
        self.odd_definition = odd_definition
        self.test_results = []

    def add_test_result(self, test_result: TestResult):
        """Record test execution result."""
        self.test_results.append(test_result)

    def calculate_triggering_condition_coverage(self) -> CoverageReport:
        """Calculate coverage of triggering conditions."""

        tc_test_status = {}
        for tc in self.triggering_conditions:
            tc_test_status[tc.id] = {
                'validated': False,
                'test_count': 0,
                'pass_count': 0,
                'fail_count': 0
            }

        for result in self.test_results:
            for tc_id in result.triggering_conditions_covered:
                if tc_id in tc_test_status:
                    tc_test_status[tc_id]['validated'] = True
                    tc_test_status[tc_id]['test_count'] += 1
                    if result.passed:
                        tc_test_status[tc_id]['pass_count'] += 1
                    else:
                        tc_test_status[tc_id]['fail_count'] += 1

        total_tc = len(self.triggering_conditions)
        validated_tc = sum(1 for status in tc_test_status.values()
                          if status['validated'])

        return CoverageReport(
            metric="Triggering Condition Coverage",
            covered=validated_tc,
            total=total_tc,
            percentage=validated_tc / total_tc * 100 if total_tc > 0 else 0,
            details=tc_test_status
        )

    def calculate_scenario_parameter_coverage(self) -> CoverageReport:
        """Calculate coverage of scenario parameter space."""

        # Extract all parameters and their values from scenario catalog
        parameter_values = defaultdict(set)
        for scenario in self.scenario_catalog:
            for param_name, param_value in scenario.parameters.items():
                parameter_values[param_name].add(param_value)

        # Check which values have been tested
        tested_values = defaultdict(set)
        for result in self.test_results:
            for param_name, param_value in result.executed_parameters.items():
                tested_values[param_name].add(param_value)

        # Calculate coverage per parameter
        coverage_per_param = {}
        for param_name, all_values in parameter_values.items():
            tested = tested_values.get(param_name, set())
            coverage_per_param[param_name] = {
                'total': len(all_values),
                'tested': len(tested),
                'coverage': len(tested) / len(all_values) * 100
                          if all_values else 0,
                'missing': list(all_values - tested)
            }

        # Overall coverage (average across parameters)
        overall_coverage = sum(
            p['coverage'] for p in coverage_per_param.values()
        ) / len(coverage_per_param) if coverage_per_param else 0

        return CoverageReport(
            metric="Scenario Parameter Coverage",
            covered=len(tested_values),
            total=len(parameter_values),
            percentage=overall_coverage,
            details=coverage_per_param
        )

    def generate_sotif_report(self) -> SotifValidationReport:
        """Generate comprehensive SOTIF validation report."""

        tc_coverage = self.calculate_triggering_condition_coverage()
        param_coverage = self.calculate_scenario_parameter_coverage()
        odd_coverage = self.calculate_odd_coverage()

        # Identify gaps
        gaps = []
        if tc_coverage.percentage < 95.0:
            gaps.append({
                'area': 'Triggering Conditions',
                'gap': f"{100 - tc_coverage.percentage:.1f}% not validated",
                'risk': 'Unvalidated triggering conditions may cause hazards'
            })

        if param_coverage.percentage < 90.0:
            gaps.append({
                'area': 'Scenario Parameters',
                'gap': f"{100 - param_coverage.percentage:.1f}% parameter space untested",
                'risk': 'Parameter combinations may have undiscovered issues'
            })

        return SotifValidationReport(
            report_date=datetime.now(),
            triggering_condition_coverage=tc_coverage,
            scenario_parameter_coverage=param_coverage,
            odd_coverage=odd_coverage,
            total_tests_executed=len(self.test_results),
            pass_rate=self._calculate_pass_rate(),
            identified_gaps=gaps,
            recommendation=self._generate_recommendation(gaps)
        )
```

---

## Safety Case Evidence

### SOTIF Safety Argument Structure

```yaml
safety_case_goal_1:
  claim: "The system is free from unreasonable risk due to SOTIF hazards"
  argument_structure:
    sub_claim_1_1:
      claim: "All triggering conditions have been systematically identified"
      evidence:
        - "HARA linkage document showing traceability from hazards to TCs"
        - "Triggering condition registry with completeness analysis"
        - "Guideword-based analysis records"
        - "Fleet data mining results for edge cases"

    sub_claim_1_2:
      claim: "All identified triggering conditions have appropriate mitigations"
      evidence:
        - "Mitigation design documents for each TC"
        - "Risk assessment showing residual risk is acceptable"
        - "Safety mechanism verification tests"

    sub_claim_1_3:
      claim: "All mitigations have been validated through testing"
      evidence:
        - "Test coverage report (>= 95% TC coverage)"
        - "Test results showing mitigation effectiveness"
        - "Criticality reduction analysis (before/after mitigation)"
        - "HIL and vehicle test reports"

    sub_claim_1_4:
      claim: "The residual risk is acceptable"
      evidence:
        - "Residual risk analysis per triggering condition"
        - "Comparison to reference systems (state of the art)"
        - "Risk acceptance criteria from safety policy"
        - "Customer and regulatory requirement compliance"
```

### Test Evidence Documentation

```python
# SOTIF test evidence generator
class SotifEvidenceGenerator:
    def generate_test_evidence(self, test_scenario: Scenario,
                                test_results: List[TestResult]) -> EvidenceDocument:

        # Extract key metrics
        passing_tests = [r for r in test_results if r.passed]
        failing_tests = [r for r in test_results if not r.passed]

        # Calculate effectiveness metrics
        mitigation_effectiveness = self._calculate_mitigation_effectiveness(
            test_results)

        criticality_reduction = self._calculate_criticality_reduction(
            test_results)

        evidence = EvidenceDocument(
            scenario_id=test_scenario.id,
            scenario_description=test_scenario.description,
            triggering_conditions=test_scenario.triggering_conditions,
            test_summary={
                'total_executions': len(test_results),
                'passed': len(passing_tests),
                'failed': len(failing_tests),
                'pass_rate': len(passing_tests) / len(test_results) * 100
            },
            effectiveness_metrics={
                'mitigation_effectiveness': mitigation_effectiveness,
                'criticality_reduction': criticality_reduction,
                'residual_criticality': self._calculate_residual_criticality(test_results)
            },
            test_artifacts=[r.artifact_path for r in test_results],
            conclusion=self._generate_conclusion(test_results,
                                                  mitigation_effectiveness)
        )

        return evidence

    def _calculate_mitigation_effectiveness(self,
                                             test_results: List[TestResult]) -> float:
        """Calculate how effectively the mitigation addresses the triggering condition."""

        if not test_results:
            return 0.0

        # Measure: percentage of tests where mitigation successfully prevented hazard
        successful_mitigations = sum(
            1 for r in test_results
            if r.passed and r.mitigation_activated
        )

        return successful_mitigations / len(test_results) * 100

    def _calculate_criticality_reduction(self,
                                          test_results: List[TestResult]) -> float:
        """Calculate reduction in scenario criticality due to mitigation."""

        if not test_results:
            return 0.0

        criticality_before = np.mean([r.criticality_without_mitigation
                                       for r in test_results])
        criticality_after = np.mean([r.criticality_with_mitigation
                                      for r in test_results])

        if criticality_before == 0:
            return 100.0  # No risk to reduce

        reduction = (criticality_before - criticality_after) / criticality_before * 100
        return max(0.0, reduction)  # Clamp to non-negative
```

---

## Test Automation Integration

### SOTIF Test Pipeline

```yaml
# CI/CD integration for SOTIF testing
sotif_test_pipeline:
  stage_sil_testing:
    environment: "Docker with CARLA simulation"
    parallel_jobs: 50
    test_duration: "2 hours"
    coverage_target: "80% TC coverage"

    jobs:
      - weather_robustness:
          scenarios: [rain, fog, snow, dust, sun_glare]
          intensity_sweep: [0.3, 0.5, 0.7, 0.9, 1.0]
          pass_criteria: "No collisions, safe degradation"

      - sensor_degradation:
          fault_injection: [camera_blind, lidar_dropout, radar_noise]
          combinations: [single, dual, triple]
          pass_criteria: "Graceful degradation, driver warning"

      - edge_case_replay:
          data_source: "Fleet edge case database"
          replay_count: 1000
          pass_criteria: "System handles all historical edge cases"

  stage_hil_testing:
    environment: "dSPACE/ETAS HIL bench"
    parallel_jobs: 4
    test_duration: "8 hours"
    coverage_target: "Validated TCs with high severity"

    jobs:
      - safety_mechanism_validation:
          focus: "High-severity triggering conditions"
          fault_injection: true
          timing_verification: true
          pass_criteria: "FTTI compliance, safe state entry"

      - driver_in_loop:
          focus: "Misuse scenarios, ODD violations"
          driver_monitoring: true
          hmi_effectiveness: true
          pass_criteria: "Clear communication, appropriate warnings"

  stage_vehicle_testing:
    environment: "Proving ground + public roads"
    duration: "4 weeks"
    mileage_target: "10,000 km mixed conditions"
    coverage_target: "Real-world validation of critical TCs"

    test_types:
      - controlled_proving_ground:
          scenarios: [emergency_braking, cut_in, pedestrian_crossing]
          variations: [dry, wet, low_friction]
          repetitions: 50

      - naturalistic_driving:
          routes: [highway, urban, rural]
          conditions: [day, night, rain, fog]
          data_collection: "Full sensor logs + annotations"
```

---

## @-Mentions

**Related Context Files:**

| Context File | When to Reference |
|-------------|-------------------|
| @context/skills/adas/sensor-fusion.md | Multi-sensor SOTIF mitigation, fusion degradation |
| @context/skills/adas/camera-processing.md | Camera-specific SOTIF scenarios (glare, low-light) |
| @context/skills/adas/radar-processing.md | Radar performance limitations, multipath scenarios |
| @context/skills/adas/lidar-processing.md | LiDAR attenuation, reflectivity issues |
| @context/skills/adas/calibration.md | Calibration degradation as SOTIF trigger |
| @knowledge/standards/iso21448/1-overview.md | SOTIF framework, Part 1 vocabulary |
| @knowledge/standards/iso21448/3-detailed.md | SOTIF validation, Part 3 conceptual phase |

**Related Knowledge Files:**

| Knowledge File | When to Reference |
|---------------|-------------------|
| @knowledge/standards/iso26262/2-conceptual.md | HARA linkage, safety goal derivation |
| @knowledge/standards/iso21448/1-overview.md | SOTIF process overview |
| @knowledge/standards/iso21448/3-detailed.md | SOTIF validation requirements |
| @knowledge/technologies/sensor-fusion/2-conceptual.md | Fusion architecture for SOTIF mitigation |
| @knowledge/tools/vector-toolchain/1-overview.md | CARLA simulation, scenario-based testing |

---

## Performance Benchmarks

| Test Type | Target Coverage | Execution Time | Environment |
|-----------|----------------|----------------|-------------|
| SIL Weather Sweep | 100% TC coverage | 2 hours | CARLA simulation |
| SIL Edge Case Replay | 1000+ scenarios | 4 hours | Host PC cluster |
| HIL Safety Mechanism | High-severity TCs | 8 hours | dSPACE/ETAS |
| Vehicle Proving Ground | Critical scenarios | 1 week | Controlled track |
| Vehicle Public Road | Real-world exposure | 4 weeks | Mixed routes |
| Fleet Data Mining | Continuous | Real-time | Cloud pipeline |

---

## Example Code

### SOTIF Test Scenario Execution

```cpp
// Execute SOTIF test scenario in simulation
class SotifTestExecutor {
public:
    struct TestResult {
        bool passed;
        float criticality_score;
        float time_to_collision_s;
        bool mitigation_activated;
        std::vector<std::string> artifacts;
        std::string conclusion;
    };

    TestResult execute_scenario(
        const TestScenario& scenario,
        const PerceptionSystem& perception,
        const PlanningSystem& planning,
        const ControlSystem& control,
        SimulationEnvironment& sim) {

        TestResult result;
        result.criticality_score = 0.0f;
        result.time_to_collision_s = std::numeric_limits<float>::max();

        // Initialize scenario
        sim.load_scenario(scenario);

        // Execute simulation loop
        const float simulation_duration_s = 60.0f;
        const float dt = 0.01f;  // 100 Hz
        const size_t num_steps = static_cast<size_t>(simulation_duration_s / dt);

        std::vector<float> criticality_history;
        std::vector<float> ttc_history;

        for (size_t step = 0; step < num_steps; step++) {
            // Get sensor data (with noise injection per TC)
            const SensorData sensor_data = sim.get_sensor_data(
                scenario.triggering_conditions);

            // Run perception
            const PerceptionOutput perception_out = perception.process(sensor_data);

            // Run planning
            const PlanningOutput planning_out = planning.compute(perception_out);

            // Run control
            const ControlOutput control_out = control.execute(planning_out);

            // Step simulation
            sim.step(control_out, dt);

            // Calculate criticality
            const float ttc = calculate_ttc(sim.get_ego_state(),
                                             sim.get_objects());
            const float criticality = calculate_criticality(ttc);

            criticality_history.push_back(criticality);
            ttc_history.push_back(ttc);

            result.time_to_collision_s = std::min(result.time_to_collision_s, ttc);

            // Check for collision
            if (sim.has_collision()) {
                result.passed = false;
                result.conclusion = "COLLISION - Test failed";
                result.artifacts.push_back(sim.save_recording());
                return result;
            }

            // Check for ODD exit
            if (!sim.is_within_odd()) {
                result.passed = false;
                result.conclusion = "ODD VIOLATION - System operated outside ODD";
                result.artifacts.push_back(sim.save_recording());
                return result;
            }
        }

        // Calculate final metrics
        result.criticality_score = *std::max_element(
            criticality_history.begin(), criticality_history.end());
        result.mitigation_activated = sim.mitigation_was_activated();
        result.passed = (result.criticality_score < 0.5f);  // Threshold
        result.conclusion = result.passed ?
            "PASSED - System handled scenario safely" :
            "FAILED - Criticality exceeded threshold";
        result.artifacts.push_back(sim.save_recording());

        return result;
    }
};
```

### SOTIF Report Generator

```python
# Generate SOTIF validation report for safety case
class SotifReportGenerator:
    def __init__(self, project_name: str, sw_version: str):
        self.project_name = project_name
        self.sw_version = sw_version
        self.sections = []

    def add_triggering_condition_summary(self,
                                          tcs: List[TriggeringCondition],
                                          test_results: Dict[str, List[TestResult]]):
        """Add triggering condition coverage summary."""

        validated = sum(1 for tc in tcs if tc.id in test_results
                       and any(r.passed for r in test_results[tc.id]))
        total = len(tcs)

        section = ReportSection(
            title="Triggering Condition Coverage",
            content=f"""
## Summary

| Metric | Value |
|--------|-------|
| Total Identified TCs | {total} |
| Validated TCs | {validated} |
| Coverage | {validated/total*100:.1f}% |
| Target | 95% |
| Status | {'PASS' if validated/total >= 0.95 else 'FAIL'} |

## Coverage by Category

| Category | Total | Validated | Coverage |
|----------|-------|-----------|----------|
| Environmental | {self._count(tcs, 'environmental')} | ... | ... |
| Sensor Limitations | {self._count(tcs, 'sensor_limitations')} | ... | ... |
| Target Properties | {self._count(tcs, 'target_properties')} | ... | ... |
| Operational | {self._count(tcs, 'operational')} | ... | ... |
| Misuse | {self._count(tcs, 'misuse')} | ... | ... |
"""
        )
        self.sections.append(section)

    def add_residual_risk_analysis(self,
                                    tcs: List[TriggeringCondition],
                                    test_results: Dict[str, List[TestResult]]):
        """Add residual risk analysis for unvalidated or partially mitigated TCs."""

        high_risk_tcs = []
        for tc in tcs:
            if tc.id not in test_results:
                high_risk_tcs.append({
                    'tc_id': tc.id,
                    'severity': tc.severity,
                    'status': 'NOT_VALIDATED',
                    'risk': 'Unvalidated - testing required'
                })
            elif not any(r.passed for r in test_results[tc.id]):
                high_risk_tcs.append({
                    'tc_id': tc.id,
                    'severity': tc.severity,
                    'status': 'VALIDATION_FAILED',
                    'risk': 'Mitigation ineffective - redesign required'
                })

        section = ReportSection(
            title="Residual Risk Analysis",
            content=f"""
## High-Risk Triggering Conditions

{'No high-risk conditions identified.' if not high_risk_tcs else '''
| TC ID | Severity | Status | Risk |
|-------|----------|--------|------|
''' + chr(10).join(
    f"| {tc['tc_id']} | {tc['severity']} | {tc['status']} | {tc['risk']} |"
    for tc in high_risk_tcs
)}

## Risk Acceptance

{'All identified triggering conditions have been validated with effective mitigations. '
 'Residual risk is assessed as ACCEPTABLE.' if not high_risk_tcs else
 f'{len(high_risk_tcs)} triggering conditions require attention before release.'}
"""
        )
        self.sections.append(section)

    def generate_full_report(self, output_path: str):
        """Generate complete SOTIF validation report."""

        report = f"""# SOTIF Validation Report

**Project:** {self.project_name}
**Software Version:** {self.sw_version}
**Report Date:** {datetime.now().strftime('%Y-%m-%d')}
**Report Status:** DRAFT

---

## Executive Summary

This report summarizes the SOTIF (Safety of the Intended Functionality) validation
activities for {self.project_name}. The validation demonstrates that the system is
free from unreasonable risk due to SOTIF hazards within the defined Operational
Design Domain (ODD).

"""
        for section in self.sections:
            report += f"\n{section.content}\n"

        report += f"""
---

## Conclusion

Based on the validation evidence presented in this report:

- [ ] Triggering condition coverage meets target (>= 95%)
- [ ] All high-severity TCs have validated mitigations
- [ ] Residual risk is acceptable
- [ ] System is ready for release

**Recommendation:** {'APPROVE FOR RELEASE' if self._all_gates_passed() else 'DO NOT RELEASE - Address gaps'}

---

## Appendices

- Appendix A: Complete Triggering Condition Registry
- Appendix B: Test Scenario Catalog
- Appendix C: Test Results Summary
- Appendix D: Edge Case Mining Report
- Appendix E: Fleet Data Analysis
"""

        with open(output_path, 'w') as f:
            f.write(report)

        return output_path
```

---

## Review Checklist

- [ ] Triggering condition registry complete and current
- [ ] All TCs linked to hazards via HARA
- [ ] Mitigation strategies defined for each TC
- [ ] Test scenarios cover all TCs (>= 95% coverage)
- [ ] Environmental simulation validated against real data
- [ ] Sensor noise models calibrated to physical sensors
- [ ] Criticality metrics defined and implemented
- [ ] Edge case mining from fleet data operational
- [ ] Coverage metrics measured and reported
- [ ] Residual risk analysis complete
- [ ] SOTIF report generated for safety case
- [ ] Safety argument structured with evidence traceability

---

*Part of the ADAS perception context files. For related expertise, see @context/skills/adas/sensor-fusion.md, @context/skills/adas/camera-processing.md, @context/skills/adas/lidar-processing.md, and @knowledge/standards/iso21448/1-overview.md.*
