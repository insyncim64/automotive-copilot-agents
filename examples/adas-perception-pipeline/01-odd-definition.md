# ODD Definition: Highway Pilot ADAS System

## ODD Specification Summary

**Tool**: `adas-odd-define`
**Version**: 2.1.0 (ISO 21448 SOTIF compliant)
**Execution Time**: 1.2 seconds
**Status**: SUCCESS

---

## Operational Design Domain

### Basic Information

| Attribute | Value |
|-----------|-------|
| ODD Name | Highway_Pilot_ODD |
| Version | 1.0 |
| ASIL Level | B |
| Standards | ISO 26262-3, ISO 21448 (SOTIF), ISO 34501 |
| Date | 2025-03-24 |

---

## Road Types

### Supported Road Classifications

```yaml
road_types:
  highway:
    min_lanes: 2
    max_lanes: 4
    median: required
    access: controlled
    shoulders: required
    examples:
      - "Interstate highways (US)"
      - "Autobahn (Germany)"
      - "Expressways (China)"

  expressway:
    min_lanes: 2
    access: controlled
    grade_separation: required
    examples:
      - "Federal highways (B-Straße, Germany)"
      - "Provincial expressways (China)"
      - "State highways (US)"
```

### Road Geometry Constraints

| Parameter | Minimum | Maximum | Unit |
|-----------|---------|---------|------|
| Lane width | 3.0 | 3.75 | m |
| Shoulder width | 1.5 | 3.0 | m |
| Curve radius | 500 | ∞ | m |
| Maximum curvature | 0 | 15 | deg/100m |
| Maximum gradient | -8 | +8 | % |
| Superelevation | -6 | +8 | % |

### Lane Marking Types

```yaml
lane_markings:
  supported:
    - type: solid
      color: [white, yellow]
      visibility: "visible or partially faded"

    - type: dashed
      color: [white, yellow]
      pattern: "3m line, 9m gap"
      visibility: "visible or partially faded"

    - type: double_solid
      color: [white, yellow]
      usage: "no-passing zone"

    - type: dashed_next_to_solid
      color: [white, yellow]
      usage: "passing allowed from dashed side"

  unsupported:
    - "Temporary construction markings"
    - "Unmarked roads"
    - "Snow-covered markings"
```

---

## Speed Range

### Operating Speed Envelope

```yaml
speed_range:
  min_kmh: 0
  max_kmh: 130
  unit: km/h

  operational_zones:
    - zone: stopped
      range: [0, 5]
      mode: STANDBY

    - zone: low_speed
      range: [5, 60]
      mode: ASSIST
      constraints:
        - "Following distance: 2s minimum"

    - zone: medium_speed
      range: [60, 100]
      mode: ASSIST
      constraints:
        - "Following distance: 2.5s minimum"

    - zone: high_speed
      range: [100, 130]
      mode: ASSIST
      constraints:
        - "Following distance: 3s minimum"
```

### Speed Limits by Road Type

| Road Type | Min Speed | Max Speed | Unit |
|-----------|-----------|-----------|------|
| Highway | 60 | 130 | km/h |
| Expressway | 40 | 100 | km/h |

---

## Weather Conditions

### Supported Weather

```yaml
weather_conditions:
  clear:
    visibility_km: ">10"
    precipitation: "none"
    road_surface: "dry"
    wind_speed_kmh: "<50"

  rain_light:
    visibility_km: "5-10"
    precipitation_mm_h: "<5"
    road_surface: "wet"
    wind_speed_kmh: "<40"

  rain_moderate:
    visibility_km: "3-5"
    precipitation_mm_h: "5-15"
    road_surface: "wet with standing water"
    wind_speed_kmh: "<30"

  fog_light:
    visibility_km: "1-5"
    precipitation: "none or mist"
    road_surface: "damp"
    wind_speed_kmh: "<20"
```

### Excluded Weather Conditions

| Condition | Reason |
|-----------|--------|
| Heavy rain (>15 mm/h) | Sensor degradation, reduced visibility |
| Snow | Lane marking occlusion, altered dynamics |
| Ice | Altered vehicle dynamics, safety risk |
| Dense fog (<1 km visibility) | Camera/LiDAR performance degradation |
| Sandstorm/dust storm | Sensor contamination, zero visibility |
| Hail | Sensor damage risk, unpredictable obstacles |

### Weather-Based Operational Limits

```
Weather Condition       | Max Speed | Following Distance | Status
------------------------|-----------|-------------------|--------
Clear, dry road         | 130 km/h  | 3.0s              | NORMAL
Light rain              | 100 km/h  | 3.5s              | DERATED
Moderate rain           | 80 km/h   | 4.0s              | DERATED
Light fog               | 60 km/h   | 4.0s              | DERATED
Heavy rain/fog          | 0 km/h    | N/A               | DISABLED
```

---

## Lighting Conditions

### Supported Lighting

```yaml
lighting_conditions:
  daylight:
    illuminance_lux: ">10000"
    sun_position: "any"
    shadows: "acceptable"

  dusk:
    illuminance_lux: "100-10000"
    sun_position: "below horizon, twilight"
    artificial_lights: "may be present"

  dawn:
    illuminance_lux: "100-10000"
    sun_position: "below horizon, twilight"
    artificial_lights: "may be present"

  artificial_lighting:
    illuminance_lux: "50-1000"
    light_sources:
      - "Street lights (highway)"
      - "Vehicle headlights"
      - "Tunnel lighting"
    glare_tolerance: "moderate"
```

### Excluded Lighting Conditions

| Condition | Reason |
|-----------|--------|
| Direct sun glare (low-angle sun) | Camera saturation, reduced detection |
| Unlit roads at night | Insufficient illumination for camera |
| Stroboscopic tunnel lighting | Sensor flicker, perception errors |
| Oncoming high-beam glare | Temporary camera blindness |

---

## Traffic Participant Types

### Supported Participants

```yaml
traffic_participants:
  vehicles:
    passenger_car:
      dimensions: { L: [3.5, 5.5], W: [1.5, 2.2], H: [1.2, 2.0] }
      max_speed_kmh: 250

    truck:
      dimensions: { L: [6, 20], W: [2.5, 2.6], H: [2.5, 4.0] }
      max_speed_kmh: 100

    bus:
      dimensions: { L: [8, 15], W: [2.5, 2.6], H: [2.8, 3.5] }
      max_speed_kmh: 100

    motorcycle:
      dimensions: { L: [1.8, 2.5], W: [0.8, 1.2], H: [1.0, 1.5] }
      max_speed_kmh: 200

    van:
      dimensions: { L: [4, 7], W: [1.8, 2.2], H: [1.8, 2.5] }
      max_speed_kmh: 130

  vulnerable_road_users:
    pedestrian:
      dimensions: { W: [0.5, 1.0], H: [1.0, 2.0] }
      max_speed_kmh: 25
      detection_range_m: 100

    cyclist:
      dimensions: { L: [1.5, 2.0], W: [0.5, 0.8], H: [1.5, 2.0] }
      max_speed_kmh: 50
      detection_range_m: 80

    e_scooter:
      dimensions: { W: [0.4, 0.6], H: [1.0, 1.5] }
      max_speed_kmh: 25
      detection_range_m: 60
```

### Traffic Behavior Assumptions

| Participant | Expected Behavior | Uncertainty Model |
|-------------|-------------------|-------------------|
| Passenger car | Lane-keeping, predictable | Low |
| Truck | Lane-keeping, slower acceleration | Low |
| Motorcycle | Lane changes, filtering | Medium |
| Cyclist (shoulder) | May enter lane | High |
| Pedestrian (median) | Unpredictable near exits | High |

---

## Geographic Constraints

### Lane Marking Quality

```yaml
lane_marking_visibility:
  minimum_contrast_ratio: 0.3
  minimum_visible_length_m: 5
  maximum_occlusion_percent: 30
  camera_detection_confidence: ">0.7"
```

### Curvature Limits

```yaml
curvature:
  maximum_deg_per_100m: 15
  minimum_radius_m: 500
  clothoid_transition: supported
  bank_angle_range_deg: [-6, 8]
```

### Gradient Limits

```yaml
gradient:
  maximum_uphill_percent: 8
  maximum_downhill_percent: 8
  crest_detection: required
  sag_detection: required
```

---

## Exclusions

### Explicitly Excluded Scenarios

```yaml
exclusions:
  infrastructure:
    - construction_zones
    - toll_stations
    - parking_garages
    - roundabouts
    - intersections_with_traffic_lights
    - unpaved_roads
    - private_roads

  environmental:
    - tunnels_without_lighting
    - bridges_with_severe_crosswind
    - roads_with_heavy_snow_cover
    - flooded_roads

  traffic:
    - emergency_vehicle_convoys
    - military_escort
    - funeral_processions
    - oversized_load_escorts

  vehicle_state:
    - sensor_occlusion_detected
    - calibration_expired
    - system_fault_active
```

### Transition Scenarios

When exiting the ODD, the system shall:

1. **Issue visual warning** 10 seconds before ODD exit
2. **Issue auditory warning** 5 seconds before ODD exit
3. **Issue haptic warning** 3 seconds before ODD exit
4. **Request driver takeover** with 3-second grace period
5. **Execute minimal risk maneuver** if driver does not respond

---

## SOTIF Considerations

### Known Limitations

| Limitation | Category | Mitigation |
|------------|----------|------------|
| Phantom braking on bridge shadows | Sensor limitation | Sensor fusion weighting |
| Reduced detection in heavy rain | Environmental | Speed derating, driver alert |
| Stationary object false negatives | Algorithm limitation | Map-based validation |
| Cut-in detection latency | Performance | Predictive tracking |

### Triggering Conditions

```yaml
triggering_conditions:
  - id: TC-001
    description: "Low sun angle causing camera glare"
    category: environmental
    mitigation: "Increase LiDAR weighting, issue driver alert"

  - id: TC-002
    description: "White truck against bright sky (low contrast)"
    category: target_characteristics
    mitigation: "Radar primary detection, camera confirmation"

  - id: TC-003
    description: "Tire debris on road (small obstacle)"
    category: road_debris
    mitigation: "LiDAR-based detection, camera classification"
```

---

## ODD Validation

### Validation Coverage

| Validation Method | Scenarios Tested | Coverage |
|-------------------|------------------|----------|
| Simulation (SIL) | 10,000+ | Broad exploration |
| HIL testing | 500+ | Critical scenarios |
| Proving ground | 100+ | Edge cases |
| Public road testing | 100,000+ km | Real-world exposure |

### ODD Compliance Matrix

| ODD Element | Verified By | Status |
|-------------|-------------|--------|
| Road types | HIL + Public road | PASS |
| Speed range | All methods | PASS |
| Weather conditions | Proving ground + HIL | PASS |
| Lighting conditions | All methods | PASS |
| Traffic participants | Simulation + Public road | PASS |
| Geographic constraints | HIL + Proving ground | PASS |

---

## Traceability

### Upward Traceability

| ODD Element | Safety Goal | HARA Reference |
|-------------|-------------|----------------|
| Speed range (0-130 km/h) | SG-HP-001 | HARA-HP-003 |
| Weather limitations | SG-HP-002 | HARA-HP-007 |
| Lane marking requirements | SG-HP-003 | HARA-HP-012 |
| Exclusion zones | SG-HP-004 | HARA-HP-015 |

### Downward Traceability

| ODD Element | Downstream Artifact | Reference |
|-------------|---------------------|-----------|
| Weather conditions | Sensor calibration | CAL-WEATHER-001 |
| Speed range | Fusion parameters | FUSION-SPEED-001 |
| Lane markings | Perception algorithm | PERC-LANE-001 |
| Traffic participants | Detection classes | DET-CLASS-001 |

---

## ODD Tool Execution Metadata

- **Tool**: adas-odd-define
- **Version**: 2.1.0
- **Standard**: ISO 21448 (SOTIF), ISO 34501
- **Execution Duration**: 1.2 seconds
- **Input Files**: highway_pilot_requirements.yaml, vehicle_specs.json
- **Exit Code**: 0 (Success)

---

## References

- ISO 26262-3:2018 - Concept phase
- ISO 21448:2022 - Safety of the Intended Functionality (SOTIF)
- ISO 34501:2021 - Scenario-based safety evaluation framework
- UL 4600 - Standard for Safety for Autonomous Products
- NHTSA ADS 2.0 - Automated Driving Systems Guidance

---

**Generated by automotive-copilot-agents v2.1.0**
**Document ID**: ODD-HP-001
**Revision**: 1.0
**Date**: 2025-03-24
