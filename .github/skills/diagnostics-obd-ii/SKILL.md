---
name: diagnostics-obd-ii
description: "Use when: Skill: OBD-II Diagnostics Implementation topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: OBD-II Diagnostics Implementation

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/diagnostics/obd-ii.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate

- Implementing emissions-related diagnostic services for vehicles sold in regulated markets (US, EU, China)
- Developing OBD-II compliance for powertrain ECUs (engine, transmission, aftertreatment)
- Building scan tools or diagnostic testers for emissions inspection stations
- Implementing Mode $01-$09 services per SAE J1979 and ISO 15031-5
- Creating MIL (Malfunction Indicator Lamp) control logic for emissions faults
- Developing freeze frame data capture for emissions-related DTCs
- Implementing readiness monitors for catalytic converter, EVAP, EGR, and oxygen sensor systems
- Building OBD-II over CAN (ISO 15765-3) or K-Line (ISO 14230) transport
- Supporting SAE J2534 pass-thru programming interface
- Creating emission inspection and maintenance (I/M) compliance reporting

## Standards Compliance

- **SAE J1979-2**: E/E Diagnostic Test Modes (OBD-II service definitions)
- **SAE J1979-3**: OBD-II Data Link Security (Secure diagnostic access)
- **ISO 15031-5**: Emission-related diagnostic services
- **ISO 15031-6**: Emission-related DTC definitions
- **ISO 14229-1**: UDS (superset of OBD-II, Mode $21-$2E)
- **ISO 15765-3**: OBD-II over CAN (ISO 15765-2 transport)
- **ISO 14230-2**: OBD-II over K-Line (Keyword Protocol 2000)
- **SAE J2534-1**: Pass-thru programming interface
- **SAE J2534-2**: Pass-thru programming (enhanced)
- **40 CFR Part 86**: US EPA emissions regulations
- **CARB Title 13**: California emissions regulations
- **EU Regulation 2017/1151**: European emissions type approval
- **GB 17691-2018**: China emissions regulations for heavy-duty vehicles

## Key Parameters

| Parameter | Range/Options | Unit | Description |
|-----------|---------------|------|-------------|
| OBD-II Mode | $01-$0A, $21-$2E, $3E | hex | Service identifier |
| PID (Parameter ID) | $00-$FF | hex | Data identifier within mode |
| MID (Monitor ID) | $00-$FF | hex | Monitor identifier for Mode $06 |
| TID (Test ID) | $00-$FF | hex | Test identifier for Mode $06 |
| CID (Component ID) | $00-$FF | hex | Component identifier for Mode $06 |
| DTC Type | Type A, B, C, D | enum | DTC classification per CARB |
| MIL Status | On/Off | boolean | Malfunction Indicator Lamp state |
| DTC Count | 0-255 | count | Number of stored emission DTCs |
| Readiness Status | 8 monitors (bitmask) | bitmask | I/M readiness flags |
| Freeze Frame Size | 16-256 | bytes | Frozen data on fault |
| VIN Length | 17 | chars | Vehicle Identification Number |
| Calibration ID | Variable | string | Calibration verification number (CVN) |
| Protocol | ISO 15765-4 CAN, ISO 14230-4 KWP, SAE J1850 PWM/VPW | enum | OBD-II communication protocol |
| Baud Rate | 10.4 kbps (J1850), 104 kbps (KWP), 250/500 kbps (CAN) | kbps | Communication speed |

## Domain-Specific Content

### OBD-II Service Architecture

```
+------------------------------------------------------------------+
|                    OBD-II Scan Tool (Tester)                      |
+------------------------------------------------------------------+
                              |
            +-----------------+-----------------+
            | ISO 15765-3   | ISO 14230-2    | SAE J1850    |
            | (CAN 29-bit)  | (K-Line)       | (PWM/VPW)    |
            +-----------------+-----------------+------------+
                              |
+-----------------------------v------------------------------+
|                 Vehicle OBD-II Interface                     |
| +----------------------------------------------------------+ |
| | OBD Gateway / Diagnostic Concentrator                     | |
| |                                                           | |
| | - Protocol Detection & Switching                          | |
| | - Request Routing to ECUs                                 | |
| | - Response Aggregation                                    | |
| | - Security Access (Mode $27 / $21-$2E)                   | |
| +----------------------------------------------------------+ |
+------------------------------|-------------------------------+
                               |
         +---------------------+---------------------+
         |                     |                     |
   +-----v----+         +-----v----+         +-----v----+
   | Engine   |         | Trans-   |         | After-   |
   | ECU      |         | mission  |         | treatment|
   | (PCM)    |         | ECU (TCM)|         | (ACM)    |
   +----------+         +----------+         +----------+
```

### OBD-II Mode $01: Show Current Data

```c
/* Mode $01 PID definitions (SAE J1979-2) */
typedef enum {
    PID_ENGINE_LOAD                  = 0x00,
    PID_ENGINE_COOLANT_TEMP          = 0x01,
    PID_FUEL_TRIM_SHORT_BANK1        = 0x02,
    PID_FUEL_TRIM_LONG_BANK1         = 0x03,
    PID_FUEL_TRIM_SHORT_BANK2        = 0x04,
    PID_FUEL_TRIM_LONG_BANK2         = 0x05,
    PID_FUEL_PRESSURE                = 0x06,
    PID_INTAKE_MANIFOLD_PRESSURE     = 0x07,
    PID_ENGINE_SPEED                 = 0x0C,
    PID_VEHICLE_SPEED                = 0x0D,
    PID_TIMING_ADVANCE               = 0x0E,
    PID_INTAKE_AIR_TEMP              = 0x0F,
    PID_MAF_AIR_FLOW_RATE            = 0x10,
    PID_THROTTLE_POSITION            = 0x11,
    PID_O2_SENSOR_PRESENT            = 0x13,
    PID_O2_SENSOR1_VOLTAGE           = 0x14,
    PID_O2_SENSOR2_VOLTAGE           = 0x15,
    PID_O2_SENSOR3_VOLTAGE           = 0x16,
    PID_O2_SENSOR4_VOLTAGE           = 0x17,
    PID_O2_SENSOR5_VOLTAGE           = 0x18,
    PID_O2_SENSOR6_VOLTAGE           = 0x19,
    PID_O2_SENSOR7_VOLTAGE           = 0x1A,
    PID_O2_SENSOR8_VOLTAGE           = 0x1B,
    PID_OBD_REQUIREMENTS             = 0x1C,
    PID_O2_SENSOR9_VOLTAGE           = 0x1D,
    PID_O2_SENSOR10_VOLTAGE          = 0x1E,
    PID_O2_SENSOR11_VOLTAGE          = 0x1F,
    PID_O2_SENSOR12_VOLTAGE          = 0x20,
    PID_AUXILIARY_INPUT              = 0x12,
    PID_RUN_TIME_SINCE_START         = 0x1F,
    PID_DISTANCE_WITH_MIL            = 0x21,
    PID_FUEL_RAIL_PRESSURE           = 0x22,
    PID_FUEL_RAIL_GUAGE_PRESSURE     = 0x23,
    PID_O2_SENSOR_WR_COMMAND_AFR     = 0x24,
    PID_O2_SENSOR_WR_VOLTAGE         = 0x25,
    PID_COMMANDED_EGR                = 0x2C,
    PID_EGR_ERROR                    = 0x2D,
    PID_COMMANDED_EVAP_VENT          = 0x2E,
    PID_FUEL_TANK_LEVEL              = 0x2F,
    PID_WARM_UPS_SINCE_DTC_CLEARED   = 0x30,
    PID_DISTANCE_SINCE_DTC_CLEARED   = 0x31,
    PID_EVAP_SYSTEM_VAPOR_PRESSURE   = 0x32,
    PID_ABSOLUTE_BAROMETRIC_PRESSURE = 0x33,
    PID_O2_SENSOR_WR_AFR1            = 0x34,
    PID_O2_SENSOR_WR_AFR2            = 0x35,
    PID_O2_SENSOR_WR_AFR3            = 0x36,
    PID_O2_SENSOR_WR_AFR4            = 0x37,
    PID_ABSOLUTE_LOAD_VALUE          = 0x43,
    PID_COMMANDED_AFR                = 0x44,
    PID_FUEL_TYPE                    = 0x51,
    PID_ETHANOL_FUEL_PERCENT         = 0x52,
    PID_ABSOLUTE_EVAP_PRESSURE       = 0x53,
    PID_EVAP_VAPOR_PRESSURE_ABS      = 0x54,
    PID_SHORT_O2_VOLTAGE_B1S1        = 0x55,
    PID_SHORT_O2_VOLTAGE_B1S2        = 0x56,
    PID_SHORT_O2_VOLTAGE_B1S3        = 0x57,
    PID_SHORT_O2_VOLTAGE_B1S4        = 0x58,
    PID_SHORT_O2_VOLTAGE_B2S1        = 0x59,
    PID_SHORT_O2_VOLTAGE_B2S2        = 0x5A,
    PID_SHORT_O2_VOLTAGE_B2S3        = 0x5B,
    PID_SHORT_O2_VOLTAGE_B2S4        = 0x5C,
    PID_ABSOLUTE_THROTTLE_POS_B      = 0x5D,
    PID_ABSOLUTE_THROTTLE_POS_C      = 0x5E,
    PID_ACCELERATOR_POS_D            = 0x5F,
    PID_ACCELERATOR_POS_E            = 0x60,
    PID_ACCELERATOR_POS_F            = 0x61,
    PID_COMMANDED_THROTTLE_ACTUATOR  = 0x62,
    PID_TIME_RUN_MIL_ON              = 0x63,
    PID_TIME_SINCE_DTC_CLEARED       = 0x64,
    PID_MAX_VALUES_EQUIV             = 0x65,
    PID_MAX_MAF_RATE                 = 0x66,
    PID_FUEL_TYPE_INJECTED           = 0x67,
    PID_SENIOR_HEATER_COUNT          = 0x68,
    PID_TIMING_ADVANCE_BANK2         = 0x69,
    PID_ENGINE_LOAD_ABSOLUTE         = 0x6A,
    PID_EGR_ABSOLUTE                 = 0x6C,
    PID_EVAP_VAPOR_PRESSURE_ALT      = 0x6D,
    PID_RELATIVE_THROTTLE_POS        = 0x6E,
    PID_AMBIENT_AIR_TEMP             = 0x6F,
    PID_ABSOLUTE_THROTTLE_POS_2      = 0x70,
    PID_O2_WR_LAMBDA_VOLT_B1S1       = 0x74,
    PID_O2_WR_LAMBDA_VOLT_B1S2       = 0x75,
    PID_O2_WR_LAMBDA_VOLT_B1S3       = 0x76,
    PID_O2_WR_LAMBDA_VOLT_B2S1       = 0x79,
    PID_O2_WR_LAMBDA_VOLT_B2S2       = 0x7A,
    PID_O2_WR_LAMBDA_VOLT_B2S3       = 0x7B,
    PID_ABSOLUTE_PEDAL_POS           = 0x7C,
    PID_HYBRID_REMAINING_LIFE        = 0x7E,
    PID_ENGINE_OIL_TEMP              = 0x7F,
    PID_FUEL_INJECTION_TIMING        = 0x80,
    PID_ENGINE_FUEL_RATE             = 0x81,
    PID_EMISSION_REQUIREMENTS        = 0x82,
    PID_ABSOLUTE_RESERVED            = 0x83,
    PID_ACC_PEDAL_RELATIVE           = 0x84,
    PID_ACC_PEDAL_ABSOLUTE           = 0x85,
    PID_COMMANDED_DPF_REGEN          = 0x86,
    PID_DPF_PRESSURE_DELTA           = 0x87,
    PID_COMMANDED_FUEL_CONTROL       = 0x88,
    PID_EGR_RATE_ACTUAL              = 0x89,
    PID_AUX_EMISSION_CONTROL         = 0x8A,
    PID_TURBO_INLET_PRESSURE         = 0x8B,
    PID_BOOST_PRESSURE_CONTROL       = 0x8C,
    PID_VGT_CONTROL                  = 0x8D,
    PID_WASTEGATE_CONTROL            = 0x8E,
    PID_EXHAUST_PRESSURE             = 0x8F,
    PID_TURBO_SPEED                  = 0x90,
    PID_ABSOLUTE_FAN_SPEED           = 0x91,
    PID_FAN_STATUS                   = 0x92,
    PID_VEHICLE_SPEED_2              = 0x93,
    PID_REMAINING_DPF_LIFE           = 0x94,
    PID_OIL_LIFE_REMAINING           = 0x95,
    PID_INJECTION_FUEL_RATE          = 0x96,
    PID_HYBRID_BATTERY_LIFE          = 0x97,
    PID_CATALYST_TEMP_B1S1           = 0x98,
    PID_CATALYST_TEMP_B2S1           = 0x99,
    PID_CATALYST_TEMP_B1S2           = 0x9A,
    PID_CATALYST_TEMP_B2S2           = 0x9B,
    PID_HYBRID_PROPULSION_SYSTEM     = 0x9C,
    PID_TRANSMISSION_TEMP            = 0x9D,
    PID_GLOW_PLUG_ENABLE_STATUS      = 0x9E,
    PID_RELATIVE_ACCEL_POS           = 0x9F,
    PID_HYBRID_BATTERY_VOLTAGE       = 0xA0,
    PID_CHARGE_LEVEL                 = 0xA1,
    PID_ABSOLUTE_FAN_SPEED_2         = 0xA2,
    PID_ABSOLUTE_FAN_SPEED_3         = 0xA3,
    PID_ABSOLUTE_FAN_SPEED_4         = 0xA4,
    PID_EXHAUST_GAS_TEMP_B1S1        = 0xA5,
    PID_EXHAUST_GAS_TEMP_B2S1        = 0xA6,
    PID_EXHAUST_GAS_TEMP_B1S2        = 0xA7,
    PID_EXHAUST_GAS_TEMP_B2S2        = 0xA8,
    PID_HYBRID_GENERATOR_SPEED       = 0xA9,
    PID_ABSOLUTE_BARO_PRESSURE_2     = 0xAA,
    PID_ABSOLUTE_BARO_PRESSURE_3     = 0xAB,
    PID_FUEL_LEVEL_ACCURACY          = 0xAC,
    PID_ABSOLUTE_VVT_POS_B1          = 0xAD,
    PID_ABSOLUTE_VVT_POS_B2          = 0xAE,
    PID_ABSOLUTE_VVT_POS_B3          = 0xAF,
    PID_ABSOLUTE_VVT_POS_B4          = 0xB0,
    PID_INLET_TEMP                   = 0xB1,
    PID_CKM_PERFORMANCE              = 0xB2,
    PID_ABSOLUTE_VVT_POS_B5          = 0xB3,
    PID_ABSOLUTE_VVT_POS_B6          = 0xB4,
    PID_OIL_TEMP_LOAD_PRESSURE       = 0xB5,
    PID_FUEL_TEMP_HIGH_PRESSURE     = 0xB6,
    PID_INJ_CONTROL_PRESSURE         = 0xB7,
    PID_ABSOLUTE_VVT_POS_B7          = 0xB8,
    PID_ABSOLUTE_VVT_POS_B8          = 0xB9,
    PID_GLOW_PLUG_DUR                = 0xBA,
    PID_ABSOLUTE_VGT_POS             = 0xBB,
    PID_FUEL_RAIL_ABS_PRESSURE       = 0xBC,
    PID_FUEL_RAIL_REL_PRESSURE       = 0xBD,
    PID_INJ_TIMING_SINGLE_PULSE      = 0xBE,
    PID_ABSOLUTE_VVT_POS_B9          = 0xBF,
    PID_ABSOLUTE_VVT_POS_B10         = 0xC0,
    PID_ABSOLUTE_VVT_POS_B11         = 0xC1,
    PID_ABSOLUTE_VVT_POS_B12         = 0xC2,
    PID_ABSOLUTE_VVT_POS_B13         = 0xC3,
    PID_ABSOLUTE_VVT_POS_B14         = 0xC4,
    PID_ABSOLUTE_VVT_POS_B15         = 0xC5,
    PID_ABSOLUTE_VVT_POS_B16         = 0xC6,
    PID_ABSOLUTE_THROTTLE_POS_D      = 0xC7,
    PID_ABSOLUTE_THROTTLE_POS_E      = 0xC8,
    PID_ABSOLUTE_THROTTLE_POS_F      = 0xC9,
    PID_ABSOLUTE_THROTTLE_POS_G      = 0xCA,
    PID_ABSOLUTE_THROTTLE_POS_H      = 0xCB,
    PID_COMMANDED_THROTTLE_ACTUATOR_2 = 0xCC,
    PID_FUEL_ACTUATOR_2_POS          = 0xCD,
    PID_FUEL_ACTUATOR_3_POS          = 0xCE,
    PID_INTAKE_VALVE_TIMING          = 0xCF,
    PID_ABSOLUTE_BARO_PRESSURE_4     = 0xD0,
    PID_ABSOLUTE_BARO_PRESSURE_5     = 0xD1,
    PID_ABSOLUTE_BARO_PRESSURE_6     = 0xD2,
    PID_FUEL_TANK_ABSOLUTE_PRESSURE  = 0xD3,
    PID_ABSOLUTE_BARO_PRESSURE_7     = 0xD4,
    PID_ABSOLUTE_BARO_PRESSURE_8     = 0xD5,
    PID_FUEL_LEVEL_ACCURACY_2        = 0xD6,
    PID_FUEL_LEVEL_ACCURACY_3        = 0xD7,
    PID_CKM_PERFORMANCE_2            = 0xD8,
    PID_CKM_PERFORMANCE_3            = 0xD9,
    PID_OIL_CHANGE_REMAINING_LIFE    = 0xDA,
    PID_FUEL_INJECTION_TIMING_2      = 0xDB,
    PID_FUEL_INJECTION_TIMING_3      = 0xDC,
    PID_FUEL_INJECTION_TIMING_4      = 0xDD,
    PID_FUEL_INJECTION_TIMING_5      = 0xDE,
    PID_FUEL_INJECTION_TIMING_6      = 0xDF
} ObdPid_t;

/* PID response structure */
typedef struct {
    uint8_t pid;
    uint8_t data_length;
    uint8_t (*read_handler)(uint8_t pid, uint8_t* buffer);
    const char* description;
    const char* unit;
    float scale;
    float offset;
    float min_value;
    float max_value;
} PidConfig_t;

/* Mode $01 supported PIDs bitmask response */
typedef struct {
    uint32_t bitmask[8];  /* Support up to PID 0xC0 */
} PidSupportMask_t;

static PidSupportMask_t g_pid_support = {
    .bitmask = {
        [0] = 0xB8130011,  /* PIDs 0x00-0x1F */
        [1] = 0xBE1FAF01,  /* PIDs 0x20-0x3F */
        [2] = 0x00000000,  /* PIDs 0x40-0x5F */
        [3] = 0x00000000,  /* PIDs 0x60-0x7F */
        [4] = 0x00000000,  /* PIDs 0x80-0x9F */
        [5] = 0x00000000,  /* PIDs 0xA0-0xBF */
        [6] = 0x00000000,  /* PIDs 0xC0-0xDF */
        [7] = 0x00000000   /* PIDs 0xE0-0xFF */
    }
};

/* SAE J1979 Mode $01 handler */
ObdResponse_t handle_mode_01_show_current_data(
    const ObdRequest_t* request,
    ObdResponse_t* response) {

    const uint8_t pid = request->data[0];

    /* Handle PID $00-$C0: Return supported PID mask */
    if (pid <= 0xC0) {
        const uint8_t mask_index = pid / 0x20;
        const uint32_t mask = g_pid_support.bitmask[mask_index];

        /* Clear bits for PIDs < requested PID */
        const uint8_t bit_position = pid % 0x20;
        const uint32_t filtered_mask = mask & ~((1U << bit_position) - 1);

        response->mode = 0x41;  /* Mode $01 + 0x40 = positive response */
        response->data[0] = pid;
        response->data[1] = (uint8_t)(filtered_mask >> 24);
        response->data[2] = (uint8_t)(filtered_mask >> 16);
        response->data[3] = (uint8_t)(filtered_mask >> 8);
        response->data[4] = (uint8_t)(filtered_mask);
        response->length = 5;

        return OBD_RESPONSE_POSITIVE;
    }

    /* Find PID handler */
    const PidConfig_t* config = get_pid_config(pid);
    if (config == NULL || config->read_handler == NULL) {
        return build_obd_negative_response(response, OBD_NRC_INVALID_PID);
    }

    /* Execute PID read handler */
    uint8_t pid_data[4];
    const uint8_t data_length = config->read_handler(pid, pid_data);

    /* Build response */
    response->mode = 0x41;
    response->data[0] = pid;
    memcpy(&response->data[1], pid_data, data_length);
    response->length = 1 + data_length;

    return OBD_RESPONSE_POSITIVE;
}

/* Example PID handlers */
uint8_t read_engine_load(uint8_t pid, uint8_t* buffer) {
    /* PID $00: Engine Load in % (0-100%)
     * Formula: A = (100 / 255) * value
     */
    const float engine_load_percent = get_engine_load_percent();
    buffer[0] = (uint8_t)(engine_load_percent * 2.55f);
    return 1;
}

uint8_t read_engine_coolant_temp(uint8_t pid, uint8_t* buffer) {
    /* PID $01: Engine Coolant Temperature in °C
     * Formula: Temperature = A - 40
     * Range: -40°C to 215°C
     */
    const int16_t coolant_temp_c = get_engine_coolant_temperature();
    buffer[0] = (uint8_t)(coolant_temp_c + 40);
    return 1;
}

uint8_t read_engine_speed(uint8_t pid, uint8_t* buffer) {
    /* PID $0C: Engine Speed in RPM
     * Formula: RPM = (256*A + B) / 4
     * Range: 0 to 16383.75 RPM
     */
    const uint16_t engine_rpm = get_engine_speed_rpm();
    const uint16_t encoded_rpm = (uint16_t)(engine_rpm * 4);
    buffer[0] = (uint8_t)(encoded_rpm >> 8);
    buffer[1] = (uint8_t)(encoded_rpm);
    return 2;
}

uint8_t read_vehicle_speed(uint8_t pid, uint8_t* buffer) {
    /* PID $0D: Vehicle Speed in km/h
     * Formula: Speed = A (0-255 km/h)
     */
    const uint8_t vehicle_speed_kmh = get_vehicle_speed_kmh();
    buffer[0] = vehicle_speed_kmh;
    return 1;
}

uint8_t read_timing_advance(uint8_t pid, uint8_t* buffer) {
    /* PID $0E: Timing Advance in degrees BTDC
     * Formula: Advance = (A / 2) - 64
     * Range: -64 to 63.5 degrees
     */
    const float timing_advance_deg = get_timing_advance_deg();
    buffer[0] = (uint8_t)((timing_advance_deg + 64.0f) * 2.0f);
    return 1;
}

uint8_t read_maf_air_flow(uint8_t pid, uint8_t* buffer) {
    /* PID $10: MAF Air Flow Rate in g/s
     * Formula: Flow = (256*A + B) / 100
     * Range: 0 to 655.35 g/s
     */
    const float maf_flow_gs = get_maf_flow_rate_gs();
    const uint16_t encoded_flow = (uint16_t)(maf_flow_gs * 100.0f);
    buffer[0] = (uint8_t)(encoded_flow >> 8);
    buffer[1] = (uint8_t)(encoded_flow);
    return 2;
}

uint8_t read_throttle_position(uint8_t pid, uint8_t* buffer) {
    /* PID $11: Throttle Position in %
     * Formula: Position = (100 / 255) * A
     * Range: 0-100%
     */
    const float throttle_percent = get_throttle_position_percent();
    buffer[0] = (uint8_t)(throttle_percent * 2.55f);
    return 1;
}
```

### OBD-II Mode $02: Show Freeze Frame Data

```c
/* Freeze Frame data structure per ISO 15031-5 */
typedef struct {
    /* Mandatory Frame Data (required for Type A/B DTCs) */
    uint8_t dtc_status;           /* DTC status byte */
    uint16_t dtc;                 /* DTC code */
    uint8_t fuel_system_status;   /* Fuel system status */
    uint8_t engine_load;          /* Calculated engine load % */
    int8_t coolant_temp;          /* Engine coolant temp °C */
    int16_t fuel_trim_short;      /* Short term fuel trim % */
    int16_t fuel_trim_long;       /* Long term fuel trim % */
    uint16_t fuel_pressure;       /* Fuel pressure kPa */
    uint8_t intake_pressure;      /* Intake manifold pressure kPa */
    uint16_t engine_speed;        /* Engine RPM */
    uint8_t vehicle_speed;        /* Vehicle speed km/h */
    uint8_t timing_advance;       /* Timing advance deg BTDC */
    int8_t intake_air_temp;       /* Intake air temp °C */
    uint8_t maf_flow;             /* MAF flow rate g/s */
    uint8_t throttle_position;    /* Throttle position % */

    /* Optional Frame Data (OEM-specific) */
    uint8_t oxygen_sensor_voltage[4];  /* O2S voltages mV */
    uint8_t fuel_level;                /* Fuel level % */
    uint8_t barometric_pressure;       /* Barometric pressure kPa */
    uint8_t catalyst_temp[2];          /* Catalyst temp °C */
    uint8_t evap_vapor_pressure;       /* EVAP pressure */
    uint8_t ambient_air_temp;          /* Ambient temp °C */

    /* Frame Metadata */
    uint32_t freeze_frame_timestamp;   /* Time of fault */
    uint16_t distance_when_stored_km;  /* Odometer at fault */
    uint8_t warmup_counter;            /* Warmup cycles at fault */
    uint8_t fault_cycle_counter;       /* Fault cycle counter */
} FreezeFrame_t;

/* Freeze Frame storage */
typedef struct {
    FreezeFrame_t frames[4];  /* Minimum 4 frames per CARB */
    uint8_t frame_count;
    uint8_t next_frame_index;
} FreezeFrameStorage_t;

static FreezeFrameStorage_t g_freeze_frame_storage = {0};

/* Capture freeze frame on DTC set */
void capture_freeze_frame(uint16_t dtc, DtcType_t dtc_type) {
    /* Only capture for Type A, B, C emission DTCs */
    if (dtc_type != DTC_TYPE_A && dtc_type != DTC_TYPE_B &&
        dtc_type != DTC_TYPE_C) {
        return;
    }

    /* Allocate frame slot */
    const uint8_t frame_index = g_freeze_frame_storage.next_frame_index;
    FreezeFrame_t* frame = &g_freeze_frame_storage.frames[frame_index];

    /* Clear frame */
    explicit_memzero(frame, sizeof(FreezeFrame_t));

    /* Populate mandatory data */
    frame->dtc_status = DTC_STATUS_PENDING | DTC_STATUS_TEST_FAILED;
    frame->dtc = dtc;
    frame->fuel_system_status = get_fuel_system_status();
    frame->engine_load = (uint8_t)(get_engine_load_percent() * 2.55f);
    frame->coolant_temp = get_engine_coolant_temperature();
    frame->fuel_trim_short = (int16_t)(get_fuel_trim_short() * 128.0f);
    frame->fuel_trim_long = (int16_t)(get_fuel_trim_long() * 128.0f);
    frame->fuel_pressure = get_fuel_pressure_kpa();
    frame->intake_pressure = get_intake_manifold_pressure_kpa();
    frame->engine_speed = get_engine_speed_rpm();
    frame->vehicle_speed = get_vehicle_speed_kmh();
    frame->timing_advance = (uint8_t)((get_timing_advance_deg() + 64.0f) * 2.0f);
    frame->intake_air_temp = get_intake_air_temperature();
    frame->maf_flow = (uint8_t)(get_maf_flow_rate_gs() * 100.0f);
    frame->throttle_position = (uint8_t)(get_throttle_position_percent() * 2.55f);

    /* Populate optional data */
    for (uint8_t i = 0; i < 4; i++) {
        frame->oxygen_sensor_voltage[i] = get_o2_sensor_voltage_mV(i) / 10;
    }
    frame->fuel_level = get_fuel_level_percent();
    frame->barometric_pressure = get_barometric_pressure_kpa();
    frame->ambient_air_temp = get_ambient_air_temperature();

    /* Metadata */
    frame->freeze_frame_timestamp = get_etime_seconds();
    frame->distance_when_stored_km = get_odometer_km();
    frame->warmup_counter = get_warmup_cycle_counter();
    frame->fault_cycle_counter = get_fault_cycle_counter();

    /* Store frame */
    g_freeze_frame_storage.frame_count++;
    g_freeze_frame_storage.next_frame_index =
        (g_freeze_frame_storage.next_frame_index + 1) % 4;

    /* Log freeze frame capture */
    log_diagnostic_event(DIAG_EVENT_FREEZE_FRAME_CAPTURED, dtc);
}

/* SAE J1979 Mode $02 handler: Show Freeze Frame Data */
ObdResponse_t handle_mode_02_freeze_frame(
    const ObdRequest_t* request,
    ObdResponse_t* response) {

    const uint8_t pid = request->data[0];

    /* Mode $02 uses same PIDs as Mode $01 */
    if (pid <= 0xC0) {
        /* Return supported PID mask (same as Mode $01) */
        const uint8_t mask_index = pid / 0x20;
        const uint32_t mask = g_pid_support.bitmask[mask_index];
        const uint8_t bit_position = pid % 0x20;
        const uint32_t filtered_mask = mask & ~((1U << bit_position) - 1);

        response->mode = 0x62;  /* Mode $02 + 0x40 */
        response->data[0] = pid;
        response->data[1] = (uint8_t)(filtered_mask >> 24);
        response->data[2] = (uint8_t)(filtered_mask >> 16);
        response->data[3] = (uint8_t)(filtered_mask >> 8);
        response->data[4] = (uint8_t)(filtered_mask);
        response->length = 5;

        return OBD_RESPONSE_POSITIVE;
    }

    /* Get most recent freeze frame (or by DTC if specified) */
    const FreezeFrame_t* frame = get_freeze_frame_by_dtc(pid);
    if (frame == NULL) {
        /* No freeze frame available */
        response->mode = 0x62;
        response->data[0] = pid;
        response->length = 1;
        return OBD_RESPONSE_POSITIVE;
    }

    /* Return freeze frame PID value */
    const PidConfig_t* config = get_pid_config(pid);
    if (config == NULL) {
        return build_obd_negative_response(response, OBD_NRC_INVALID_PID);
    }

    /* Extract value from freeze frame */
    uint8_t frame_data = extract_pid_from_freeze_frame(frame, pid);

    response->mode = 0x62;
    response->data[0] = pid;
    response->data[1] = frame_data;
    response->length = 2;

    return OBD_RESPONSE_POSITIVE;
}

/* Get freeze frame by DTC */
const FreezeFrame_t* get_freeze_frame_by_dtc(uint16_t dtc) {
    for (uint8_t i = 0; i < g_freeze_frame_storage.frame_count; i++) {
        if (g_freeze_frame_storage.frames[i].dtc == dtc) {
            return &g_freeze_frame_storage.frames[i];
        }
    }
    /* Return most recent if DTC not found */
    if (g_freeze_frame_storage.frame_count > 0) {
        return &g_freeze_frame_storage.frames[
            (g_freeze_frame_storage.next_frame_index + 3) % 4];
    }
    return NULL;
}
```

### OBD-II Mode $03: Show Stored DTCs

```c
/* SAE J1979 Mode $03: Show Stored DTCs */
ObdResponse_t handle_mode_03_stored_dtc(
    const ObdRequest_t* request,
    ObdResponse_t* response) {

    /* Get emission-related DTCs */
    uint16_t dtc_list[256];
    uint8_t dtc_count = 0;

    /* Query Dem module for emission DTCs */
    dtc_count = dem_get_emission_dtc_list(dtc_list, 256);

    if (dtc_count == 0) {
        /* No DTCs stored */
        response->mode = 0x43;  /* Mode $03 + 0x40 */
        response->length = 0;
        return OBD_RESPONSE_POSITIVE;
    }

    /* Build DTC list response */
    /* Each DTC is 3 bytes: status byte + 2-byte DTC */
    response->mode = 0x43;
    uint8_t response_index = 0;

    for (uint8_t i = 0; i < dtc_count && response_index < 510; i++) {
        const uint16_t dtc = dtc_list[i];
        const uint8_t status = dem_get_dtc_status(dtc);

        /* Encode DTC per ISO 15031-6 */
        const uint8_t dtc_high = (uint8_t)(dtc >> 8);
        const uint8_t dtc_low = (uint8_t)(dtc);

        response->data[response_index++] = status;
        response->data[response_index++] = dtc_high;
        response->data[response_index++] = dtc_low;
    }

    response->length = response_index;
    return OBD_RESPONSE_POSITIVE;
}

/* DTC encoding per ISO 15031-6 */
typedef enum {
    DTC_TYPE_P = 0x00,  /* Powertrain (SAE J2012) */
    DTC_TYPE_C = 0x01,  /* Chassis */
    DTC_TYPE_B = 0x02,  /* Body */
    DTC_TYPE_U = 0x03   /* Network */
} DtcPrefix_t;

/* Convert internal DTC to OBD-II format */
uint16_t encode_dtc_obd_format(uint16_t internal_dtc) {
    /* Example: Internal DTC 0x0123 -> P0123 */
    const DtcPrefix_t prefix = DTC_TYPE_P;  /* Powertrain */
    const uint8_t digit1 = (internal_dtc >> 12) & 0x0F;
    const uint8_t digit2 = (internal_dtc >> 8) & 0x0F;
    const uint8_t digit3 = (internal_dtc >> 4) & 0x0F;
    const uint8_t digit4 = internal_dtc & 0x0F;

    /* OBD-II DTC format:
     * Bit 15-14: DTC type (00=P, 01=C, 10=B, 11=U)
     * Bit 13-12: First digit (0-3)
     * Bit 11-8: Second digit
     * Bit 7-4: Third digit
     * Bit 3-0: Fourth digit
     */
    uint16_t obd_dtc = 0;
    obd_dtc |= ((prefix & 0x03) << 14);
    obd_dtc |= ((digit1 & 0x03) << 12);
    obd_dtc |= ((digit2 & 0x0F) << 8);
    obd_dtc |= ((digit3 & 0x0F) << 4);
    obd_dtc |= (digit4 & 0x0F);

    return obd_dtc;
}

/* Decode OBD-II DTC to internal format */
uint16_t decode_dtc_from_obd_format(uint16_t obd_dtc) {
    const DtcPrefix_t prefix = (DtcPrefix_t)((obd_dtc >> 14) & 0x03);
    const uint8_t digit1 = (obd_dtc >> 12) & 0x03;
    const uint8_t digit2 = (obd_dtc >> 8) & 0x0F;
    const uint8_t digit3 = (obd_dtc >> 4) & 0x0F;
    const uint8_t digit4 = obd_dtc & 0x0F;

    /* Convert to internal format */
    uint16_t internal_dtc = 0;
    internal_dtc |= ((digit1 & 0x03) << 12);
    internal_dtc |= ((digit2 & 0x0F) << 8);
    internal_dtc |= ((digit3 & 0x0F) << 4);
    internal_dtc |= (digit4 & 0x0F);

    return internal_dtc;
}
```

### OBD-II Mode $04: Clear/Reset DTCs

```c
/* SAE J1979 Mode $04: Clear DTCs and Reset Readiness */
ObdResponse_t handle_mode_04_clear_dtc(
    const ObdRequest_t* request,
    ObdResponse_t* response) {

    /* Mode $04 has no parameters */
    if (request->length != 1) {
        return build_obd_negative_response(response, OBD_NRC_INVALID_LENGTH);
    }

    /* Check security access (optional but recommended) */
    if (g_session_state.security_level_unlocked < 0x22) {
        /* Some OEMs require security access for Mode $04 */
        /* return build_obd_negative_response(response, OBD_NRC_SECURITY_ACCESS_DENIED); */
    }

    /* Clear all emission-related DTCs */
    dem_clear_all_emission_dtc();

    /* Reset readiness monitors */
    reset_readiness_monitors();

    /* Turn off MIL */
    set_mil_state(MIL_OFF);

    /* Clear freeze frames */
    g_freeze_frame_storage.frame_count = 0;
    g_freeze_frame_storage.next_frame_index = 0;

    /* Log DTC clear event */
    log_diagnostic_event(DIAG_EVENT_DTC_CLEARED_MODE_04, 0);

    /* Build response */
    response->mode = 0x44;  /* Mode $04 + 0x40 */
    response->length = 0;

    return OBD_RESPONSE_POSITIVE;
}
```

### OBD-II Mode $05: Oxygen Sensor Monitoring (Legacy)

```c
/* SAE J1979 Mode $05: Oxygen Sensor Monitoring (Legacy)
 * Note: Mode $05 is deprecated for CAN-based OBD-II.
 * Use Mode $06 for comprehensive component monitoring.
 */
typedef struct {
    uint8_t sensor_id;      /* O2S ID (01-XX) */
    uint8_t richness_ratio; /* Rich/Lean ratio */
    uint8_t voltage;        /* O2S voltage */
    uint8_t response_time;  /* Response time ms */
    uint8_t voltage_threshold;   /* Voltage threshold mV */
    uint8_t response_time_threshold; /* Response time threshold ms */
} O2SensorTest_t;

ObdResponse_t handle_mode_05_oxygen_sensor(
    const ObdRequest_t* request,
    ObdResponse_t* response) {

    const uint8_t o2s_id = request->data[0];

    /* Validate sensor ID */
    if (!is_valid_oxygen_sensor(o2s_id)) {
        return build_obd_negative_response(response, OBD_NRC_INVALID_PID);
    }

    /* Get O2S test results */
    O2SensorTest_t test_result;
    if (!get_oxygen_sensor_test_result(o2s_id, &test_result)) {
        return build_obd_negative_response(response, OBD_NRC_DATA_NOT_AVAILABLE);
    }

    /* Build response */
    response->mode = 0x45;  /* Mode $05 + 0x40 */
    response->data[0] = o2s_id;
    response->data[1] = test_result.richness_ratio;
    response->data[2] = test_result.voltage;
    response->data[3] = test_result.response_time;
    response->data[4] = test_result.voltage_threshold;
    response->data[5] = test_result.response_time_threshold;
    response->length = 6;

    return OBD_RESPONSE_POSITIVE;
}
```

### OBD-II Mode $06: On-Board Component Monitoring

```c
/* Mode $06 MID (Monitor ID) definitions */
typedef enum {
    /* Catalyst Monitoring */
    MID_CATALYST_B1S1          = 0x00,
    MID_CATALYST_B2S1          = 0x01,
    MID_CATALYST_B1S2          = 0x02,
    MID_CATALYST_B2S2          = 0x03,

    /* Oxygen Sensor Monitoring */
    MID_O2_SENSOR_B1S1         = 0x10,
    MID_O2_SENSOR_B1S2         = 0x11,
    MID_O2_SENSOR_B1S3         = 0x12,
    MID_O2_SENSOR_B1S4         = 0x13,
    MID_O2_SENSOR_B2S1         = 0x20,
    MID_O2_SENSOR_B2S2         = 0x21,
    MID_O2_SENSOR_B2S3         = 0x22,
    MID_O2_SENSOR_B2S4         = 0x23,

    /* EGR System Monitoring */
    MID_EGR_SYSTEM             = 0x30,
    MID_EGR_SENSOR             = 0x31,

    /* VVT System Monitoring */
    MID_VVT_SYSTEM             = 0x40,

    /* Evaporative System Monitoring */
    MID_EVAP_SYSTEM            = 0x50,
    MID_EVAP_PURGE             = 0x51,
    MID_EVAP_VENT              = 0x52,

    /* Secondary Air System */
    MID_SECONDARY_AIR          = 0x60,

    /* Fuel System Monitoring */
    MID_FUEL_SYSTEM            = 0x70,
    MID_FUEL_INJECTOR          = 0x71,

    /* Transmission Monitoring */
    MID_TRANSMISSION           = 0x80,

    /* A/C Refrigerant Monitoring */
    MID_AC_REFRIGERANT         = 0x90,

    /* MISFIRE Monitoring */
    MID_MISFIRE_CYCLE_AVERAGE  = 0xA0,
    MID_MISFIRE_COUNT          = 0xA1
} ObdMid_t;

/* Monitor test result structure */
typedef struct {
    uint8_t mid;
    uint8_t tid;
    uint16_t test_value;
    uint16_t test_limit;
    uint8_t test_status;  /* Pass/Fail/Incomplete */
    uint8_t test_type;
    const char* description;
    const char* unit;
    float scale;
    float offset;
} MonitorResult_t;

/* SAE J1979 Mode $06 handler */
ObdResponse_t handle_mode_06_component_monitoring(
    const ObdRequest_t* request,
    ObdResponse_t* response) {

    const uint8_t sub_mode = request->data[0];
    const uint8_t mid = (request->length > 1) ? request->data[1] : 0x00;

    switch (sub_mode) {
        case 0x00:
            /* Request MID support */
            return handle_mode_06_mid_support(mid, response);

        case 0x01:
            /* Request TID support for specific MID */
            return handle_mode_06_tid_support(mid, response);

        case 0x02:
            /* Request test results for specific MID/TID */
            return handle_mode_06_test_results(request, response);

        default:
            return build_obd_negative_response(response, OBD_NRC_INVALID_SUBMODE);
    }
}

/* Mode $06 $00: Request MID support */
static ObdResponse_t handle_mode_06_mid_support(
    uint8_t mid,
    ObdResponse_t* response) {

    /* Build MID support mask */
    uint32_t mid_mask = get_supported_mid_mask();

    response->mode = 0x46;  /* Mode $06 + 0x40 */
    response->data[0] = 0x00;  /* Sub-mode */
    response->data[1] = (uint8_t)(mid_mask >> 24);
    response->data[2] = (uint8_t)(mid_mask >> 16);
    response->data[3] = (uint8_t)(mid_mask >> 8);
    response->data[4] = (uint8_t)(mid_mask);
    response->length = 5;

    return OBD_RESPONSE_POSITIVE;
}

/* Mode $06 $02: Request test results */
static ObdResponse_t handle_mode_06_test_results(
    const ObdRequest_t* request,
    ObdResponse_t* response) {

    const uint8_t mid = request->data[1];
    const uint8_t tid = (request->length > 2) ? request->data[2] : 0x00;

    /* Get monitor results */
    MonitorResult_t results[16];
    uint8_t result_count = get_monitor_results(mid, tid, results, 16);

    if (result_count == 0) {
        /* No data available */
        return build_obd_negative_response(response, OBD_NRC_DATA_NOT_AVAILABLE);
    }

    /* Build response */
    response->mode = 0x46;
    response->data[0] = 0x02;  /* Sub-mode */
    response->data[1] = mid;
    response->data[2] = tid;

    uint8_t response_index = 3;
    for (uint8_t i = 0; i < result_count && response_index < 250; i++) {
        const MonitorResult_t* result = &results[i];

        /* Encode test result */
        response->data[response_index++] = result->tid;
        response->data[response_index++] = result->test_status;
        response->data[response_index++] = (uint8_t)(result->test_value >> 8);
        response->data[response_index++] = (uint8_t)(result->test_value);
        response->data[response_index++] = (uint8_t)(result->test_limit >> 8);
        response->data[response_index++] = (uint8_t)(result->test_limit);
    }

    response->length = response_index;
    return OBD_RESPONSE_POSITIVE;
}
```

### OBD-II Mode $07: Show Pending DTCs

```c
/* SAE J1979 Mode $07: Show Pending DTCs */
ObdResponse_t handle_mode_07_pending_dtc(
    const ObdRequest_t* request,
    ObdResponse_t* response) {

    /* Get pending DTCs (detected but not confirmed) */
    uint16_t pending_dtc_list[256];
    uint8_t pending_count = 0;

    pending_count = dem_get_pending_dtc_list(pending_dtc_list, 256);

    if (pending_count == 0) {
        /* No pending DTCs */
        response->mode = 0x47;  /* Mode $07 + 0x40 */
        response->length = 0;
        return OBD_RESPONSE_POSITIVE;
    }

    /* Build DTC list response */
    response->mode = 0x47;
    uint8_t response_index = 0;

    for (uint8_t i = 0; i < pending_count && response_index < 510; i++) {
        const uint16_t dtc = pending_dtc_list[i];
        const uint8_t status = dem_get_dtc_status(dtc) | DTC_STATUS_PENDING;

        response->data[response_index++] = status;
        response->data[response_index++] = (uint8_t)(dtc >> 8);
        response->data[response_index++] = (uint8_t)(dtc);
    }

    response->length = response_index;
    return OBD_RESPONSE_POSITIVE;
}
```

### OBD-II Mode $09: Vehicle Information

```c
/* SAE J1979 Mode $09: Request Vehicle Information */
ObdResponse_t handle_mode_09_vehicle_info(
    const ObdRequest_t* request,
    ObdResponse_t* response) {

    const uint8_t pid = request->data[0];

    switch (pid) {
        case 0x01:
            /* VIN (Vehicle Identification Number) */
            return handle_mode_09_pid_01_vin(response);

        case 0x02:
            /* Calibration ID */
            return handle_mode_09_pid_02_calibration_id(response);

        case 0x03:
            /* PID support for Mode $09 */
            return handle_mode_09_pid_03_support(response);

        case 0x04:
            /* CVN (Calibration Verification Number) */
            return handle_mode_09_pid_04_cvn(response);

        case 0x05:
            /* ECU name */
            return handle_mode_09_pid_05_ecu_name(response);

        default:
            return build_obd_negative_response(response, OBD_NRC_INVALID_PID);
    }
}

/* Mode $09 PID $01: VIN */
static ObdResponse_t handle_mode_09_pid_01_vin(ObdResponse_t* response) {
    const char* vin = get_vin_string();
    const uint8_t vin_length = strlen(vin);

    response->mode = 0x49;  /* Mode $09 + 0x40 */
    response->data[0] = 0x01;  /* PID */
    response->data[1] = 0x01;  /* Count (number of VIN messages) */
    memcpy(&response->data[2], vin, vin_length);
    response->length = 2 + vin_length;

    return OBD_RESPONSE_POSITIVE;
}

/* Mode $09 PID $02: Calibration ID */
static ObdResponse_t handle_mode_09_pid_02_calibration_id(ObdResponse_t* response) {
    const char* calibration_id = get_calibration_id();
    const uint8_t cal_id_length = strlen(calibration_id);

    response->mode = 0x49;
    response->data[0] = 0x02;  /* PID */
    response->data[1] = 0x01;  /* Count */
    memcpy(&response->data[2], calibration_id, cal_id_length);
    response->length = 2 + cal_id_length;

    return OBD_RESPONSE_POSITIVE;
}

/* Mode $09 PID $04: CVN (Calibration Verification Number) */
static ObdResponse_t handle_mode_09_pid_04_cvn(ObdResponse_t* response) {
    const uint32_t cvn = calculate_cvn();

    response->mode = 0x49;
    response->data[0] = 0x04;  /* PID */
    response->data[1] = 0x01;  /* Count */
    response->data[2] = (uint8_t)(cvn >> 24);
    response->data[3] = (uint8_t)(cvn >> 16);
    response->data[4] = (uint8_t)(cvn >> 8);
    response->data[5] = (uint8_t)(cvn);
    response->length = 6;

    return OBD_RESPONSE_POSITIVE;
}
```

### OBD-II Readiness Monitors

```c
/* OBD-II Readiness Monitor status (8 monitors per CARB/EPA) */
typedef enum {
    MONITOR_MISFIRE           = (1 << 0),
    MONITOR_FUEL_SYSTEM       = (1 << 1),
    MONITOR_COMPONENTS        = (1 << 2),
    MONITOR_CATALYST          = (1 << 3),
    MONITOR_EVAPORATIVE       = (1 << 4),
    MONITOR_SECONDARY_AIR     = (1 << 5),
    MONITOR_A_C_REFRIGERANT   = (1 << 6),
    MONITOR_OXYGEN_SENSOR     = (1 << 7)
} ReadinessMonitor_t;

/* Readiness status structure */
typedef struct {
    uint8_t supported_monitors;    /* Bitmask of supported monitors */
    uint8_t complete_monitors;     /* Bitmask of completed monitors */
    uint8_t mil_state;             /* MIL on/off */
    uint8_t dtc_count;             /* Number of stored DTCs */
} ReadinessStatus_t;

/* Mode $01 PID $01: Readiness Monitor Status */
uint8_t read_readiness_status(uint8_t pid, uint8_t* buffer) {
    ReadinessStatus_t status;
    get_readiness_status(&status);

    /* Byte 1: MIL status and DTC count */
    buffer[0] = (status.mil_state ? 0x80 : 0x00) | (status.dtc_count & 0x7F);

    /* Byte 2: Supported monitors */
    buffer[1] = status.supported_monitors;

    /* Byte 3: Complete monitors */
    buffer[2] = status.complete_monitors;

    /* Byte 4-7: Reserved (0x00) */
    buffer[3] = 0x00;
    buffer[4] = 0x00;
    buffer[5] = 0x00;
    buffer[6] = 0x00;
    buffer[7] = 0x00;

    return 8;
}

/* Update readiness monitor status */
void update_readiness_monitor(ReadinessMonitor_t monitor, bool complete) {
    if (complete) {
        g_readiness_status.complete_monitors |= monitor;
    } else {
        g_readiness_status.complete_monitors &= ~monitor;
    }
}

/* Reset readiness monitors (on Mode $04) */
void reset_readiness_monitors(void) {
    g_readiness_status.complete_monitors = 0x00;
    g_readiness_status.mil_state = MIL_OFF;
    g_readiness_status.dtc_count = 0;
}

/* Check if all required monitors are complete (I/M check) */
bool is_im_readiness_complete(void) {
    /* Required monitors for I/M: Catalyst, EVAP, O2S, EGR (if equipped) */
    const uint8_t required_monitors = MONITOR_CATALYST | MONITOR_EVAPORATIVE |
                                       MONITOR_OXYGEN_SENSOR;

    return (g_readiness_status.complete_monitors & required_monitors) ==
           required_monitors;
}
```

### MIL (Malfunction Indicator Lamp) Control

```c
/* MIL state machine */
typedef enum {
    MIL_OFF,
    MIL_ON_PENDING,
    MIL_ON_CONFIRMED,
    MIL_FLASHING  /* Severe misfire - catalyst damage */
} MilState_t;

typedef struct {
    MilState_t state;
    uint16_t dtc_triggering;
    uint32_t mil_on_time_seconds;
    uint8_t trip_counter;
    uint8_t warmup_counter;
} MilControl_t;

static MilControl_t g_mil_control = {0};

/* Update MIL state based on DTC status */
void update_mil_control(uint16_t dtc, DtcStatus_t status) {
    /* Type A DTC: MIL on immediately (1 trip) */
    if (get_dtc_type(dtc) == DTC_TYPE_A) {
        if (status & DTC_STATUS_TEST_FAILED) {
            g_mil_control.state = MIL_ON_CONFIRMED;
            g_mil_control.dtc_triggering = dtc;
        }
    }

    /* Type B/C DTC: MIL on after 2 consecutive failed trips */
    if (get_dtc_type(dtc) == DTC_TYPE_B || get_dtc_type(dtc) == DTC_TYPE_C) {
        if (status & DTC_STATUS_TEST_FAILED_THIS_CYCLE) {
            g_mil_control.trip_counter++;
            if (g_mil_control.trip_counter >= 2) {
                g_mil_control.state = MIL_ON_CONFIRMED;
                g_mil_control.dtc_triggering = dtc;
            }
        } else if (!(status & DTC_STATUS_PENDING)) {
            g_mil_control.trip_counter = 0;
        }
    }

    /* Check for MIL turn-off conditions (3 consecutive good trips) */
    if (g_mil_control.state == MIL_ON_CONFIRMED) {
        if (!(status & DTC_STATUS_PENDING) &&
            !(status & DTC_STATUS_TEST_FAILED_THIS_CYCLE)) {
            g_mil_control.warmup_counter++;
            if (g_mil_control.warmup_counter >= 3) {
                g_mil_control.state = MIL_OFF;
                g_mil_control.dtc_triggering = 0;
            }
        }
    }
}

/* Flash MIL for severe misfire (catalyst damage) */
void flash_mil_for_misfire(void) {
    g_mil_control.state = MIL_FLASHING;

    /* Flash pattern: 1 Hz on/off */
    static uint32_t last_flash_time = 0;
    const uint32_t current_time = get_time_ms();

    if (current_time - last_flash_time > 500) {
        toggle_mil_output();
        last_flash_time = current_time;
    }
}
```

### OBD-II Protocol Detection

```c
/* OBD-II Protocol detection per SAE J1979 */
typedef enum {
    OBD_PROTOCOL_AUTO = 0,
    OBD_PROTOCOL_J1850_PWM = 1,   /* 10.4 kbps, Ford */
    OBD_PROTOCOL_J1850_VPW = 2,   /* 10.4 kbps, GM */
    OBD_PROTOCOL_ISO9141_2 = 3,   /* 10.4 kbps, K-Line */
    OBD_PROTOCOL_ISO14230_KWP = 4, /* 10.4 kbps, KWP2000 */
    OBD_PROTOCOL_ISO15765_CAN = 5, /* 250/500 kbps, CAN */
    OBD_PROTOCOL_ISO15765_CAN_FD = 6 /* 500 kbps, CAN FD */
} ObdProtocol_t;

static ObdProtocol_t g_obd_protocol = OBD_PROTOCOL_AUTO;

/* Auto-detect OBD-II protocol */
ObdProtocol_t detect_obd_protocol(void) {
    /* Step 1: Try CAN (ISO 15765) */
    if (can_detect_obd_protocol()) {
        g_obd_protocol = OBD_PROTOCOL_ISO15765_CAN;
        return g_obd_protocol;
    }

    /* Step 2: Try K-Line (ISO 14230 KWP2000) */
    if (kwp_detect_obd_protocol()) {
        g_obd_protocol = OBD_PROTOCOL_ISO14230_KWP;
        return g_obd_protocol;
    }

    /* Step 3: Try K-Line (ISO 9141-2) */
    if (iso9141_detect_obd_protocol()) {
        g_obd_protocol = OBD_PROTOCOL_ISO9141_2;
        return g_obd_protocol;
    }

    /* Step 4: Try J1850 VPW (GM) */
    if (j1850_vpw_detect()) {
        g_obd_protocol = OBD_PROTOCOL_J1850_VPW;
        return g_obd_protocol;
    }

    /* Step 5: Try J1850 PWM (Ford) */
    if (j1850_pwm_detect()) {
        g_obd_protocol = OBD_PROTOCOL_J1850_PWM;
        return g_obd_protocol;
    }

    /* Protocol detection failed */
    return OBD_PROTOCOL_AUTO;
}

/* CAN protocol detection */
bool can_detect_obd_protocol(void) {
    /* Listen for OBD-II request on standard CAN IDs */
    const uint32_t obd_can_ids[] = {
        0x7DF,  /* Functional OBD request (broadcast) */
        0x7E0,  /* ECU #1 */
        0x7E1,  /* ECU #2 */
        0x7E2,  /* ECU #3 */
        0x7E3,  /* ECU #4 */
        0x7E4,  /* ECU #5 */
        0x7E5,  /* ECU #6 */
        0x7E6,  /* ECU #7 */
        0x7E7   /* ECU #8 */
    };

    /* Wait for OBD request */
    for (uint8_t i = 0; i < 9; i++) {
        if (can_receive(obd_can_ids[i], 500)) {
            /* Received valid OBD request on CAN */
            return true;
        }
    }

    return false;
}
```

## Related Context

- `diagnostics/uds-protocol.md` — UDS (ISO 14229) services (Mode $21-$2E)
- `diagnostics/dtc-management.md` — DTC storage, aging, and status management
- `diagnostics/doip.md` — Diagnostic over IP transport for OBD-II
- `network/can-protocol.md` — CAN bus and ISO 15765-2/3 transport
- `safety/iso-26262-compliance.md` — Functional safety for emission-critical systems
- `regulations/emissions-compliance.md` — EPA, CARB, EU emission regulations

## Approach

1. Implement OBD-II Mode $01-$0A services per SAE J1979-2 and ISO 15031-5
2. Configure CAN protocol detection for ISO 15765-3 (OBD-II over CAN)
3. Implement PID handlers for all mandatory emission-related parameters
4. Build freeze frame data capture for Type A/B/C DTCs
5. Implement readiness monitor tracking for I/M compliance
6. Create MIL control logic per CARB and EPA requirements
7. Implement Mode $03/$07 DTC reporting with proper status bytes
8. Build Mode $06 component monitoring with MID/TID structure
9. Add Mode $09 vehicle information (VIN, CVN, calibration ID)
10. Ensure compliance with 40 CFR Part 86, CARB Title 13, and EU 2017/1151
11. Test with standardized OBD-II scan tools and emissions analyzers

## Deliverables

- OBD-II Mode $01-$0A service handler implementation
- PID read handlers for all mandatory emission parameters
- Freeze frame capture and retrieval system
- Readiness monitor state machine for I/M compliance
- MIL control logic with flashing for severe misfire
- DTC list reporting (Mode $03/$07) with status encoding
- Mode $06 component monitoring framework
- Mode $09 vehicle information handlers
- OBD-II protocol auto-detection (CAN, K-Line, J1850)
- Compliance test report for EPA/CARB/EU regulations
- Unit test suite for OBD-II service handlers
- Integration guide for Dem module and NVM storage

## Tools Required

- Vector CANoe / CANalyzer — OBD-II protocol analysis
- Intrepid Control Systems Vehicle Spy — OBD-II monitoring and simulation
- Bosch KTS / Snap-on Modis — Professional OBD-II scan tools
- Horiba MEXA — Emissions analyzer for validation
- MAHA MET 6.1 — Emissions inspection station simulator
- ETAS INCA — Calibration and OBD monitoring
- dSPACE SCALEXIO — HIL testing with OBD simulation
- SAE J2534-compatible pass-thru device (Drew Tech, Tactrix)
- Peak-System PCAN — CAN interface for testing
- Wireshark — DoIP and network diagnostics
- Oscilloscope — Physical layer debugging (K-Line, J1850)
- Emission regulations compliance checker (EPA/CARB tools)