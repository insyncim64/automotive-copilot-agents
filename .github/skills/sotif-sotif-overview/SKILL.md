---
name: sotif-sotif-overview
description: "Use when: Skill: SOTIF (Safety of the Intended Functionality) - ISO 21448 topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: SOTIF (Safety of the Intended Functionality) - ISO 21448

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/sotif/sotif-overview.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate
- User asks about SOTIF methodology or ISO 21448 compliance
- User needs to distinguish SOTIF from ISO 26262 functional safety
- User is developing ADAS/ADS functions and needs to address functional insufficiencies
- User requests triggering condition analysis or ODD definition
- User needs guidance on known unsafe vs unknown unsafe scenarios

## Standards Compliance
- ISO 21448:2022 (SOTIF) - Safety of the Intended Functionality
- ISO 26262:2018 (Functional Safety) - Complementary, not replacement
- ISO 21434:2021 (Cybersecurity) - Coordinates with threat analysis
- ASPICE Level 3 - Validation process integration
- AUTOSAR 4.4 - Architecture patterns for SOTIF mechanisms
- UN ECE R157 (ALKS) - Regulatory compliance for automated lane keeping
- SAE J3016 - Automation level definitions (L0-L5)

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| ODD definition completeness | Known conditions documented | boolean |
| Triggering condition coverage | >= 90% identified | percentage |
| Scenario coverage (Area 1+2) | >= 95% validated | percentage |
| Residual risk acceptance | Documented and justified | boolean |
| Sensor capability degradation | Full/Degraded/Minimal/Unavailable | enumeration |
| Action authority scaling | Full/Assisted/Warning/None | enumeration |
| Driver monitoring engagement | Required/Monitored/Optional | enumeration |

## SOTIF vs ISO 26262

| Aspect | ISO 26262 | ISO 21448 (SOTIF) |
|--------|-----------|-------------------|
| **Addresses** | Systematic/random HW faults | Functional insufficiencies |
| **Root cause** | Design errors, HW failures | Correct design but limited capability |
| **Example** | Software bug in brake calculation | Radar fails to detect pedestrian in rain |
| **Goal** | Freedom from unreasonable risk due to faults | Absence of unreasonable risk due to intended functionality |
| **Key activity** | FMEA, FTA, code review | Triggering condition analysis, validation |

## Four Scenario Areas

```
                    KNOWN                    UNKNOWN
           +-------------------+-------------------+
           |                   |                   |
    SAFE   |  Area 1:          |  Area 4:          |
           |  Known Safe       |  Unknown Safe     |
           |  - Validated      |  - Not yet        |
           |  - No hazard      |    validated      |
           |                   |  - Acceptable     |
           |                   |    with evidence  |
           +-------------------+-------------------+
           |                   |                   |
   UNSAFE  |  Area 2:          |  Area 3:          |
           |  Known Unsafe     |  Unknown Unsafe   |
           |  - Identified     |  - Not yet        |
           |  - Mitigated      |    identified     |
           |  - Residual risk  |  - SOTIF focus:   |
           |    acceptable     |    minimize this  |
           |                   |                   |
           +-------------------+-------------------+
                         ^
                         |
              SOTIF Goal: Reduce Area 3 to
              acceptable level through systematic
              triggering condition analysis
```

### Area 1: Known Safe
- Conditions where the function operates correctly
- Validated through testing and analysis
- No hazardous behavior identified
- Example: AEB triggers correctly for stationary vehicle in clear weather

### Area 2: Known Unsafe
- Conditions identified where function may fail
- Mitigations implemented and documented
- Residual risk accepted through safety case
- Example: AEB degraded in heavy snow - mitigated by driver warning and reduced speed

### Area 3: Unknown Unsafe (SOTIF Focus)
- Conditions not yet identified but could cause hazard
- Minimized through systematic exploration
- Reduced via diverse testing methods (simulation, proving ground, public roads)
- Example: Rare pedestrian clothing/material combination at night

### Area 4: Unknown Safe
- Conditions not yet validated but believed safe
- Requires evidence to move to Area 1
- Example: AEB performance on gravel roads (not yet tested but no known issues)

## Key Concepts

### Functional Insufficiency
Limitations inherent to the designed functionality despite correct implementation:
- Sensor limitations (range, FOV, weather susceptibility)
- Algorithm limitations (training data coverage, edge cases)
- Performance limitations (latency, throughput, resolution)
- Design assumptions that don't hold in all conditions

### Reasonably Foreseeable Misuse
Driver/operator behaviors that are predictable even if incorrect:
- Over-reliance on ADAS (hands-off, eyes-off)
- Ignoring warnings or override requests
- Using system outside intended ODD
- Poor maintenance (dirty sensors, worn tires)

### Triggering Conditions
Specific scenarios where functional insufficiency leads to hazardous behavior:
- Environmental: weather, lighting, road surface
- Operational: speed, traffic density, road type
- Object properties: color, material, size, orientation
- System state: degradation mode, calibration status

## ODD (Operational Design Domain) Specification

Every SOTIF-relevant function must define its ODD explicitly:

```yaml
function: lane_keeping_assist
odd:
  speed_range:
    min_kmh: 60
    max_kmh: 180
  road_types: [highway, expressway]
  lane_markings: [solid, dashed, double]
  weather_conditions: [clear, light_rain, overcast]
  lighting_conditions: [daylight, dusk, artificial_lighting]
  excluded_conditions:
    - heavy_rain
    - snow_on_road
    - construction_zones
    - unpainted_roads
    - tunnels_without_lighting
  sensor_requirements:
    camera: FULL
    radar: DEGRADED_OK
    lidar: OPTIONAL
  driver_requirements:
    monitoring: eyes_on_road
    takeover_time_s: 10
```

## Triggering Condition Catalog

### Example: AEB (Automatic Emergency Braking)

| ID | Category | Description | Severity | Mitigation |
|----|----------|-------------|----------|------------|
| TC-AEB-001 | Environmental | Heavy rain reduces radar return | High | Fuse with camera/lidar |
| TC-AEB-002 | Environmental | Camera saturated by low-angle sun | High | Sun position awareness |
| TC-AEB-003 | Target Properties | Dark clothing pedestrian at night | Critical | IR illumination, radar-primary |
| TC-AEB-004 | Misuse | Driver ignores FCW, doesn't brake | Medium | Escalating warnings, auto-brake |
| TC-AEB-005 | Road Surface | Standing water causes reflection | Medium | Rain sensor integration |
| TC-AEB-006 | Occlusion | Child runs from behind parked car | Critical | V2X integration, speed limit |

## SOTIF Process Integration

```
+----------------------------------------------------------+
|  SOTIF Phase 1: Define Function and ODD                  |
|  - Intended functionality specification                  |
|  - ODD boundaries and assumptions                        |
|  - Initial hazard identification                         |
+---------------------------+------------------------------+
                            |
                            v
+----------------------------------------------------------+
|  SOTIF Phase 2: Identify Triggering Conditions            |
|  - Systematic hazard analysis (HARA linkage)             |
|  - Sensor/algorithm limitation analysis                  |
|  - Misuse scenario identification                        |
|  - Output: Triggering Condition Catalog                  |
+---------------------------+------------------------------+
                            |
                            v
+----------------------------------------------------------+
|  SOTIF Phase 3: Evaluate and Mitigate                     |
|  - Classify scenarios (Area 1-4)                         |
|  - Design mitigations (sensor fusion, ODD restriction)   |
|  - Implement degradation awareness                       |
|  - Move Area 3 -> Area 2 through analysis                |
+---------------------------+------------------------------+
                            |
                            v
+----------------------------------------------------------+
|  SOTIF Phase 4: Validate and Monitor                      |
|  - Multi-method validation (SIL/HIL/Proving Ground/Road) |
|  - Residual risk assessment                              |
|  - Field monitoring post-release                         |
|  - Move Area 2 -> Area 1 through evidence                |
+----------------------------------------------------------+
```

## Example: ALKS (Automated Lane Keeping System)

### Function Specification
- L3 automated driving per UN ECE R157
- Lateral and longitudinal control on highways
- Driver monitoring required for takeover

### ODD Definition
- Speed: 0-60 km/h (expandable to 130 km/h with additional validation)
- Road: Motorways with physical separation
- Lane markings: Continuous or dashed lines
- Traffic: Congested conditions (follow lead vehicle)
- Weather: Clear to light rain (no snow/ice)

### Known Unsafe Scenarios (Area 2)
| Scenario | Triggering Condition | Mitigation | Residual Risk |
|----------|---------------------|------------|---------------|
| Emergency vehicle approach | Siren detection | System disengages, driver takeover | Acceptable with 10s warning |
| Lane marking disappearance | Construction zone | Slow down, request takeover | Acceptable |
| Cut-in vehicle < 0.6s TTC | Aggressive driver | Emergency braking | Acceptable with FCW |
| Heavy rain (>50mm/h) | Camera/radar degradation | System unavailable | Acceptable |

### Triggering Conditions Identified
- Tunnel entrance/exit (lighting transition)
- Bridge expansion joints (sensor noise)
- Erratic lead vehicle behavior
- Overhead sign occlusion
- Wet road surface reflections

## Sensor Fusion and Degradation Awareness

```c
/* Sensor capability reporting - required for SOTIF */
typedef enum {
    SENSOR_CAPABILITY_FULL,        /* Normal operation */
    SENSOR_CAPABILITY_DEGRADED,    /* Reduced range or accuracy */
    SENSOR_CAPABILITY_MINIMAL,     /* Severely limited */
    SENSOR_CAPABILITY_UNAVAILABLE  /* No usable data */
} SensorCapability_t;

/* Function must adapt behavior based on available capability */
typedef struct {
    SensorCapability_t radar;
    SensorCapability_t camera;
    SensorCapability_t lidar;
    float combined_capability_percent;  /* 0-100 */
} PerceptionCapability_t;

/* Scale action authority based on confidence */
typedef struct {
    float brake_authority;    /* 0.0 to 1.0 */
    float steer_authority;    /* 0.0 to 1.0 */
    bool driver_takeover_required;
} ActionAuthority_t;

ActionAuthority_t determine_action_authority(
    const PerceptionCapability_t* capability) {

    if (capability->combined_capability_percent < 30.0f) {
        return (ActionAuthority_t){
            .brake_authority = 0.0f,
            .steer_authority = 0.0f,
            .driver_takeover_required = true
        };
    } else if (capability->combined_capability_percent < 60.0f) {
        return (ActionAuthority_t){
            .brake_authority = 0.5f,
            .steer_authority = 0.3f,
            .driver_takeover_required = false
        };
    } else {
        return (ActionAuthority_t){
            .brake_authority = 1.0f,
            .steer_authority = 1.0f,
            .driver_takeover_required = false
        };
    }
}
```

## Approach

1. **Define function and ODD**
   - Specify intended functionality clearly
   - Define ODD boundaries (speed, road, weather, traffic)
   - Document assumptions about driver behavior

2. **Identify triggering conditions**
   - Systematic hazard analysis linked to HARA
   - Sensor limitation analysis (range, FOV, weather)
   - Algorithm limitation analysis (training data gaps)
   - Reasonably foreseeable misuse scenarios

3. **Classify scenarios into four areas**
   - Area 1: Known safe (validated, no hazard)
   - Area 2: Known unsafe (identified, mitigated)
   - Area 3: Unknown unsafe (not yet identified - minimize)
   - Area 4: Unknown safe (not validated - gather evidence)

4. **Design and implement mitigations**
   - Multi-sensor fusion (independent confirmation)
   - Degradation awareness and graceful degradation
   - ODD enforcement (prevent activation outside boundaries)
   - Driver monitoring and takeover strategies

5. **Validate across methods**
   - Simulation (SIL): Broad scenario exploration
   - HIL testing: Specific scenario validation
   - Proving ground: Critical scenarios with replicas
   - Public road testing: Real-world exposure

6. **Assess residual risk**
   - Document all Area 2 scenarios with mitigations
   - Argue Area 3 minimized through systematic process
   - Obtain safety case approval

7. **Monitor post-release**
   - Field data collection
   - Incident analysis
   - Quarterly triggering condition review
   - OTA updates for newly identified conditions

## Deliverables

- **SOTIF Plan**: Process definition, scope, responsibilities
- **ODD Specification**: Detailed operational domain boundaries
- **Triggering Condition Catalog**: All identified conditions with mitigations
- **Scenario Classification**: Four-area mapping with evidence
- **Validation Strategy**: Multi-method approach with coverage targets
- **Residual Risk Assessment**: Safety case argument for acceptance
- **Field Monitoring Plan**: Post-release data collection and analysis

## Related Context
- @context/skills/safety/iso-26262-overview.md
- @context/skills/safety/safety-mechanisms-patterns.md
- @context/skills/adas/object-detection.md
- @context/skills/adas/sensor-fusion.md
- @context/skills/adas/adaptive-cruise-control.md
- @context/skills/china-standards/sotif/
- @context/skills/china-standards/odd/

## Tools and Methods

| Tool | Purpose | Coverage |
|------|---------|----------|
| CARLA | Open-source simulation | Scenario exploration |
| VTD | Commercial simulation | High-fidelity sensor models |
| IPG CarMaker | Vehicle dynamics + traffic | Closed-loop testing |
| dSPACE ASM | HIL simulation | Real-time ECU testing |
| OpenSCENARIO | Scenario description | Standardized scenario exchange |
| Vector CANoe | Network + HIL | ECU integration testing |

## Regulatory Landscape

| Region | Regulation | SOTIF Relevance |
|--------|------------|-----------------|
| EU/UNECE | UN ECE R157 (ALKS) | Mandatory SOTIF evidence |
| EU | Type Approval (EU) 2022/1426 | SOTIF in ADS approval |
| China | GB/T standards | SOTIF methodology aligned |
| US | NHTSA ADS 2.0/3.0 | Safety principles (voluntary) |
| Japan | MLIT Guidelines | SOTIF integration required |