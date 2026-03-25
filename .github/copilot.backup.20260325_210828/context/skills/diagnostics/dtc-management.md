# Skill: DTC (Diagnostic Trouble Code) Management

## When to Activate
- User asks about DTC storage, clearing, or reading per UDS services 0x14/0x19
- User needs to implement AUTOSAR Dem (Diagnostic Event Manager) module
- User is configuring DTC formats, status bytes, or aging mechanisms
- User requests freeze frame data handling or extended data record configuration
- User needs OBD-II Mode 03/07/0A integration for emissions-related DTCs
- User asks about DTC severity classifications or DTC severity filtering

## Standards Compliance
- ISO 14229-1:2020 (UDS) - Diagnostic services 0x14, 0x19
- ISO 15765-2 (UDS on CAN) - Transport layer
- ISO 26262:2018 (Functional Safety) - Safety-related DTCs
- AUTOSAR 4.4 - Dem module specification
- ASPICE Level 3 - Diagnostic development process
- SAE J1979 (OBD-II) - Emission-related DTC access
- SAE J2012 - DTC format and definitions
- ISO 27145 - WWH-OBD (World Wide Harmonized OBD)

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| DTC format | 3 bytes DTC + 1 byte status | bytes |
| DTC status byte | 8 bits (testFailed, pending, confirmed, etc.) | bits |
| DTC type | Type A, B1, B2, C, D per OBD-II | enumeration |
| Aging cycles | 1-255 operation cycles | cycles |
| Freeze frame records | 1-10 per DTC | records |
| Extended data records | 0-5 per DTC | records |
| DTC format mask | 0x000000-0xFFFFFF | hex |
| DTC severity | P (Powertrain), B (Body), C (Chassis), U (Network) | enumeration |

## DTC Status Byte Definition

```
+--------+--------+--------+--------+--------+--------+--------+--------+
|  Bit 7 |  Bit 6 |  Bit 5 |  Bit 4 |  Bit 3 |  Bit 2 |  Bit 1 |  Bit 0 |
+--------+--------+--------+--------+--------+--------+--------+--------+
| test   | test   |pending |confirmed| test   | test   | test   | warning|
| Failed | Failed |  DTC   |   DTC  |  Not   | Failed |  Not   |Indicator|
|        | This   |        |        |Completed| Since  |Completed|Requested|
|        |  Op    |        |        | Since  |  Last  |  This  |        |
|        | Cycle  |        |        | Last   | Clear  |   Op   |        |
|        |        |        |        | Clear  |        |  Cycle |        |
+--------+--------+--------+--------+--------+--------+--------+--------+
```

### Status Bit Definitions

| Bit | Name | Description | Set When | Cleared When |
|-----|------|-------------|----------|--------------|
| 0 | testFailed | Current test result | Diagnostic test fails | Test passes |
| 1 | testFailedThisOperationCycle | Failed in current cycle | Test fails this cycle | Cycle ends |
| 2 | pendingDTC | Will become confirmed | Test fails first time | 3 consecutive passes |
| 3 | confirmedDTC | Fault verified | After sufficient failures | 40 warm-up cycles pass |
| 4 | testNotCompletedSinceLastClear | Test incomplete | ECU reset/clear | Test completes |
| 5 | testFailedSinceLastClear | Historical failure | Any failure since clear | UDS 0x14 clear |
| 6 | testNotCompletedThisOperationCycle | Current cycle incomplete | Cycle start | Test completes this cycle |
| 7 | warningIndicatorRequested | MIL/request | Severity requires warning | Fault clears |

## DTC Type Classifications (OBD-II)

```
Type A: Emission-related, safety-critical
  - MIL (Malfunction Indicator Lamp) on after 1 trip with fault
  - Stored as confirmed DTC immediately
  - P0xxx, P1xxx, P2xxx, P3xxx codes
  - Example: P0300 (Random/Multiple Cylinder Misfire)

Type B: Emission-related, less critical
  - MIL on after 2 consecutive trips with fault
  - Pending DTC after first trip
  - Confirmed DTC after second trip
  - Example: P0420 (Catalyst System Efficiency)

Type C: Non-emission, safety-related
  - No MIL requirement
  - Confirmed after manufacturer-defined trips
  - Example: C0035 (Left Front Wheel Speed Circuit)

Type D: Non-emission, non-safety
  - No warning indicator
  - Stored for service technician access
  - Example: B1000 (Electronic Control Unit)
```

## AUTOSAR Dem Module Architecture

```
+------------------------------------------------------------------+
|                    Diagnostic Event Manager (Dem)                 |
+------------------------------------------------------------------+
|  Event Memory                                                    |
|  +------------------+  +------------------+  +----------------+  |
|  | Primary Memory   |  | Secondary Memory |  | Permanent DTC  |  |
|  | (confirmed DTCs) |  | (pending DTCs)   |  | (non-clearable)|  |
|  +------------------+  +------------------+  +----------------+  |
+------------------------------------------------------------------+
|  DTC Storage                                                     |
|  +------------------+  +------------------+  +----------------+  |
|  | DTC Format       |  | Status Byte      |  | Fault Counter  |  |
|  | (3 bytes)        |  | (8 bits)         |  | (aging)        |  |
|  +------------------+  +------------------+  +----------------+  |
+------------------------------------------------------------------+
|  Freeze Frame Data                                               |
|  +------------------+  +------------------+  +----------------+  |
|  | Snapshot Data    |  | Extended Data    |  | Aging Data     |  |
|  | (at fault time)  |  | (manufacturer)   |  | (cycle count)  |  |
|  +------------------+  +------------------+  +----------------+  |
+------------------------------------------------------------------+
|  Event Detection & Reaction                                      |
|  +------------------+  +------------------+  +----------------+  |
|  | Fault Detection  |  | Debouncing       |  | Reaction       |  |
|  | (from SwC/BSW)   |  | (multi-trip)     |  | (DTC storage)  |  |
|  +------------------+  +------------------+  +----------------+  |
+------------------------------------------------------------------+
|  UDS Interface (0x14, 0x19)                                      |
|  +------------------+  +------------------+  +----------------+  |
|  | Clear DTC (0x14) |  | Read DTC (0x19)  |  | DTC Filtering  |  |
|  +------------------+  +------------------+  +----------------+  |
+------------------------------------------------------------------+
```

## Dem Configuration (AUTOSAR C Code)

```c
/* Dem_Cfg.h - Diagnostic Event Manager Configuration */

/* DTC Format Configuration */
#define DEM_DTC_FORMAT                 DEM_DTC_FORMAT_SAEE_J2012
#define DEM_DTC_SIZE                   4U  /* 3 bytes DTC + 1 byte status */

/* Memory Configuration */
#define DEM_PRIMARY_MEMORY_SIZE        256U   /* Confirmed DTCs */
#define DEM_SECONDARY_MEMORY_SIZE      128U   /* Pending DTCs */
#define DEM_PERMANENT_DTC_MEMORY_SIZE  64U    /* Permanent DTCs */

/* Freeze Frame Configuration */
#define DEM_FREEZE_FRAME_RECORDS       3U     /* Max freeze frames per DTC */
#define DEM_EXTENDED_DATA_RECORDS      2U     /* Manufacturer-specific data */

/* Aging Configuration */
#define DEM_AGING_OPERATION_CYCLES     40U    /* Warm-up cycles to clear */
#define DEM_PASSED_CYCLE_THRESHOLD     3U     /* Passes to clear pending */

/* Event Configuration Structure */
typedef struct {
    uint32_t dtc_code;               /* DTC identifier (e.g., 0x001234) */
    uint8_t  dtc_format;             /* P/B/C/U classification */
    uint8_t  dtc_type;               /* Type A/B/C/D */
    uint8_t  severity;               /* Severity level */
    uint16_t aging_cycles;           /* Cycles before auto-clear */
    uint16_t passed_cycle_threshold; /* Passes to clear pending */
    bool     permanent_dtc;          /* Non-clearable DTC */
    bool     mil_required;           /* MIL illumination */
} Dem_EventConfig_t;

/* Example Event Configuration */
static const Dem_EventConfig_t s_dem_event_config[] = {
    /* Event: Cell Overvoltage */
    {
        .dtc_code = 0x001234U,
        .dtc_format = DEM_DTC_FORMAT_P,      /* Powertrain */
        .dtc_type = DEM_DTC_TYPE_A,          /* Safety-critical */
        .severity = DEM_SEVERITY_HIGH,
        .aging_cycles = 40U,
        .passed_cycle_threshold = 3U,
        .permanent_dtc = false,
        .mil_required = true
    },

    /* Event: Pack Overcurrent */
    {
        .dtc_code = 0x001235U,
        .dtc_format = DEM_DTC_FORMAT_P,
        .dtc_type = DEM_DTC_TYPE_B,          /* Requires 2 trips */
        .severity = DEM_SEVERITY_MEDIUM,
        .aging_cycles = 40U,
        .passed_cycle_threshold = 3U,
        .permanent_dtc = false,
        .mil_required = true
    },

    /* Event: Permanent Calibration Fault */
    {
        .dtc_code = 0x001240U,
        .dtc_format = DEM_DTC_FORMAT_P,
        .dtc_type = DEM_DTC_TYPE_A,
        .severity = DEM_SEVERITY_CRITICAL,
        .aging_cycles = 0U,                  /* Never auto-clear */
        .passed_cycle_threshold = 0U,
        .permanent_dtc = true,               /* Non-clearable */
        .mil_required = true
    }
};
```

## DTC Status Byte Operations

```c
/* DTC Status Byte Bit Masks */
#define DEM_STATUS_TEST_FAILED              0x01U  /* Bit 0 */
#define DEM_STATUS_TEST_FAILED_THIS_CYCLE   0x02U  /* Bit 1 */
#define DEM_STATUS_PENDING_DTC              0x04U  /* Bit 2 */
#define DEM_STATUS_CONFIRMED_DTC            0x08U  /* Bit 3 */
#define DEM_STATUS_TEST_NOT_COMPLETED       0x10U  /* Bit 4 */
#define DEM_STATUS_TEST_FAILED_SINCE_CLEAR  0x20U  /* Bit 5 */
#define DEM_STATUS_TEST_NOT_COMPLETED_CYCLE 0x40U  /* Bit 6 */
#define DEM_STATUS_WARNING_INDICATOR        0x80U  /* Bit 7 */

/* DTC Status Structure */
typedef struct {
    uint8_t status_byte;
    uint8_t fault_counter;
    uint8_t passed_cycle_count;
    uint16_t first_operation_cycle;
    uint16_t last_operation_cycle;
} Dem_DtcStatus_t;

/* Set status bit */
static inline void Dem_SetStatusBit(Dem_DtcStatus_t* status, uint8_t mask) {
    status->status_byte |= mask;
}

/* Clear status bit */
static inline void Dem_ClearStatusBit(Dem_DtcStatus_t* status, uint8_t mask) {
    status->status_byte &= ~mask;
}

/* Test status bit */
static inline bool Dem_TestStatusBit(const Dem_DtcStatus_t* status, uint8_t mask) {
    return (status->status_byte & mask) != 0U;
}

/* Update DTC status based on test result */
void Dem_UpdateDtcStatus(uint32_t dtc, bool test_passed) {
    Dem_DtcStatus_t* status = Dem_GetDtcStatus(dtc);
    if (status == NULL) {
        return;
    }

    if (!test_passed) {
        /* Test failed */
        Dem_SetStatusBit(status, DEM_STATUS_TEST_FAILED);
        Dem_SetStatusBit(status, DEM_STATUS_TEST_FAILED_THIS_CYCLE);
        Dem_SetStatusBit(status, DEM_STATUS_TEST_FAILED_SINCE_CLEAR);
        Dem_ClearStatusBit(status, DEM_STATUS_TEST_NOT_COMPLETED);
        Dem_ClearStatusBit(status, DEM_STATUS_TEST_NOT_COMPLETED_CYCLE);

        /* Increment fault counter */
        if (status->fault_counter < 127U) {
            status->fault_counter++;
        }

        /* Set pending after first failure */
        if (status->fault_counter == 1U) {
            Dem_SetStatusBit(status, DEM_STATUS_PENDING_DTC);
        }

        /* Set confirmed after sufficient failures (Type B: 2 trips) */
        const Dem_EventConfig_t* config = Dem_GetEventConfig(dtc);
        if (status->fault_counter >= config->passed_cycle_threshold) {
            Dem_SetStatusBit(status, DEM_STATUS_CONFIRMED_DTC);
            if (config->mil_required) {
                Dem_SetStatusBit(status, DEM_STATUS_WARNING_INDICATOR);
                /* Trigger MIL illumination via BCM */
                Bcm_IlluminateMil(true);
            }
        }
    } else {
        /* Test passed */
        Dem_ClearStatusBit(status, DEM_STATUS_TEST_FAILED);
        Dem_ClearStatusBit(status, DEM_STATUS_TEST_FAILED_THIS_CYCLE);

        /* Increment passed cycle count */
        if (status->passed_cycle_count < 255U) {
            status->passed_cycle_count++;
        }

        /* Clear pending after 3 consecutive passes */
        if (status->passed_cycle_count >= DEM_PASSED_CYCLE_THRESHOLD) {
            Dem_ClearStatusBit(status, DEM_STATUS_PENDING_DTC);
            status->fault_counter = 0U;
        }
    }
}
```

## Freeze Frame Data Handling

```c
/* Freeze Frame Data Structure */
#define DEM_FREEZE_FRAME_DATA_SIZE  64U

typedef struct {
    uint32_t dtc_code;                    /* DTC that triggered freeze frame */
    uint16_t operation_cycle;             /* Cycle number when fault occurred */
    uint32_t timestamp_ms;                /* Time since ECU start */
    uint32_t odometer_km;                 /* Vehicle odometer reading */
    float    vehicle_speed_kmh;           /* Vehicle speed at fault */
    float    battery_voltage_v;           /* Supply voltage at fault */
    float    coolant_temp_c;              /* Engine coolant temperature */
    float    intake_air_temp_c;           /* Intake air temperature */
    float    engine_speed_rpm;            /* Engine speed (if applicable) */
    float    throttle_position_percent;   /* Throttle position */
    uint8_t  gear_position;               /* Current gear */
    uint8_t  brake_pedal_status;          /* Brake pedal applied */
    uint8_t  accelerator_pedal_percent;   /* Accelerator position */
    uint8_t  reserved[40];                /* Manufacturer-specific data */
} Dem_FreezeFrame_t;

/* Capture freeze frame on first fault occurrence */
void Dem_CaptureFreezeFrame(uint32_t dtc) {
    const Dem_DtcStatus_t* status = Dem_GetDtcStatus(dtc);
    if (status == NULL) {
        return;
    }

    /* Only capture on first occurrence in this cycle */
    if (!Dem_TestStatusBit(status, DEM_STATUS_TEST_NOT_COMPLETED_THIS_CYCLE)) {
        return;
    }

    /* Get available freeze frame slot */
    Dem_FreezeFrame_t* frame = Dem_GetFreezeFrameSlot(dtc);
    if (frame == NULL) {
        return;  /* No available slots */
    }

    /* Capture current vehicle state */
    frame->dtc_code = dtc;
    frame->operation_cycle = Dem_GetCurrentOperationCycle();
    frame->timestamp_ms = Dem_GetTimestampMs();
    frame->odometer_km = Dem_GetOdometerReading();
    frame->vehicle_speed_kmh = Veh_GetSpeedKmh();
    frame->battery_voltage_v = Adc_GetSupplyVoltage();
    frame->coolant_temp_c = Sensor_GetCoolantTemp();
    frame->intake_air_temp_c = Sensor_GetIntakeAirTemp();
    frame->engine_speed_rpm = Sensor_GetEngineSpeed();
    frame->throttle_position_percent = Sensor_GetThrottlePosition();
    frame->gear_position = Tcu_GetCurrentGear();
    frame->brake_pedal_status = Brk_GetPedalStatus();
    frame->accelerator_pedal_percent = App_GetPedalPosition();

    /* Log freeze frame capture */
    Dem_LogEvent(DEM_EVENT_FREEZE_FRAME_CAPTURED, dtc);
}

/* Read freeze frame via UDS 0x19 service */
Dem_FreezeFrame_t* Dem_ReadFreezeFrameByDtc(uint32_t dtc, uint8_t record_number) {
    /* Verify DTC exists and has freeze frame */
    if (!Dem_DtcExists(dtc)) {
        return NULL;
    }

    /* Get freeze frame record */
    Dem_FreezeFrame_t* frame = Dem_GetFreezeFrameRecord(dtc, record_number);
    if (frame == NULL) {
        return NULL;
    }

    return frame;
}
```

## UDS Service Integration

### Service 0x14: ClearDiagnosticInformation

```c
/* UDS 0x14: Clear Diagnostic Information */
/* Request:  [0x14] [DTC Group MSB] [DTC Group LSB] [DTC Group LSB] */
/* Response: [0x54] */

typedef enum {
    DEM_CLEAR_ALL_DTCS          = 0xFFFFFFU,  /* Clear all DTCs */
    DEM_CLEAR_PENDING_DTCS      = 0xFFFF01U,  /* Clear pending only */
    DEM_CLEAR_PERMANENT_DTCS    = 0xFFFF02U,  /* Clear permanent (if allowed) */
    DEM_CLEAR_BY_GROUP          = 0xFF0000U   /* Clear by DTC group (P/B/C/U) */
} Dem_ClearGroup_t;

Uds_Response_t Dem_HandleClearDtc(const uint8_t* request, uint8_t length) {
    Uds_Response_t response;

    /* Verify session and security access */
    if (!Uds_IsSessionActive(UDS_SESSION_EXTENDED)) {
        return Uds_NegativeResponse(0x14, DEM_NRC_SERVICE_NOT_ACTIVE);
    }

    if (!Uds_IsSecurityAccessGranted(UDS_SECURITY_LEVEL_DIAG)) {
        return Uds_NegativeResponse(0x14, DEM_NRC_SECURITY_ACCESS_DENIED);
    }

    /* Parse DTC group mask */
    uint32_t dtc_group_mask = ((uint32_t)request[1] << 16) |
                              ((uint32_t)request[2] << 8) |
                              (uint32_t)request[3];

    /* Clear DTCs matching mask */
    uint16_t cleared_count = 0U;
    for (uint32_t dtc = 0U; dtc <= 0xFFFFFFU; dtc++) {
        if ((dtc & dtc_group_mask) == dtc) {
            if (Dem_ClearDtc(dtc)) {
                cleared_count++;
            }
        }
    }

    /* Log clearing operation */
    Dem_LogEvent(DEM_EVENT_DTC_CLEARED, dtc_group_mask);

    /* Positive response */
    response.data[0] = 0x54U;  /* 0x14 + 0x40 */
    response.length = 1U;
    return response;
}

/* Clear individual DTC */
bool Dem_ClearDtc(uint32_t dtc) {
    Dem_DtcStatus_t* status = Dem_GetDtcStatus(dtc);
    if (status == NULL) {
        return false;
    }

    /* Permanent DTCs cannot be cleared via 0x14 */
    const Dem_EventConfig_t* config = Dem_GetEventConfig(dtc);
    if (config->permanent_dtc) {
        return false;
    }

    /* Clear all status bits except testNotCompleted */
    status->status_byte &= DEM_STATUS_TEST_NOT_COMPLETED;
    status->fault_counter = 0U;
    status->passed_cycle_count = 0U;

    /* Clear freeze frame data */
    Dem_ClearFreezeFrame(dtc);

    /* Clear extended data records */
    Dem_ClearExtendedData(dtc);

    /* Turn off MIL if no more confirmed DTCs */
    if (!Dem_HasConfirmedDtcsWithMil()) {
        Bcm_IlluminateMil(false);
    }

    return true;
}
```

### Service 0x19: ReadDTCInformation

```c
/* UDS 0x19 Sub-functions */
typedef enum {
    DEM_SUBFUNC_REPORT_NUM_DTC_BY_STATUS_MASK        = 0x01U,
    DEM_SUBFUNC_REPORT_DTC_BY_STATUS_MASK            = 0x02U,
    DEM_SUBFUNC_REPORT_DTC_SNAPSHOT_RECORD_BY_DTC    = 0x04U,
    DEM_SUBFUNC_REPORT_DTC_EXT_DATA_BY_DTC           = 0x06U,
    DEM_SUBFUNC_REPORT_DTC_BY_AGE                    = 0x08U,
    DEM_SUBFUNC_REPORT_SUPPORTED_DTC                 = 0x0AU,
    DEM_SUBFUNC_REPORT_FIRST_TEST_FAILED_DTC         = 0x0BU,
    DEM_SUBFUNC_REPORT_FIRST_CONFIRMED_DTC           = 0x0CU,
    DEM_SUBFUNC_REPORT_MOST_RECENT_TEST_FAILED_DTC   = 0x0DU,
    DEM_SUBFUNC_REPORT_MOST_RECENT_CONFIRMED_DTC     = 0x0EU,
    DEM_SUBFUNC_REPORT_MIRROR_MEMORY_DTC             = 0x0FU,
    DEM_SUBFUNC_REPORT_PERMANENT_DTC                 = 0x10U
} Dem_SubFunction_t;

/* 0x19.02: Read DTCs by status mask */
Uds_Response_t Dem_HandleReadDtcByStatusMask(
    const uint8_t* request, uint8_t length) {

    Uds_Response_t response;
    uint8_t status_mask = request[2];  /* Filter by status bits */

    /* Collect matching DTCs */
    uint32_t matching_dtcs[DEM_MAX_DTC_COUNT];
    uint8_t dtc_count = 0U;

    for (uint32_t dtc = 0U; dtc <= 0xFFFFFFU; dtc++) {
        const Dem_DtcStatus_t* status = Dem_GetDtcStatus(dtc);
        if (status != NULL &&
            (status->status_byte & status_mask) != 0U) {
            matching_dtcs[dtc_count++] = dtc;
            if (dtc_count >= DEM_MAX_DTC_RESPONSE) {
                break;  /* Limit response size */
            }
        }
    }

    /* Build response: [0x59][0x02][DTCStatusAvailabilityMask][DTC+Status]... */
    response.data[0] = 0x59U;  /* 0x19 + 0x40 */
    response.data[1] = 0x02U;  /* Sub-function echo */
    response.data[2] = DEM_DTC_STATUS_AVAILABILITY_MASK;

    size_t offset = 3U;
    for (uint8_t i = 0U; i < dtc_count; i++) {
        /* DTC: 3 bytes */
        response.data[offset++] = (matching_dtcs[i] >> 16) & 0xFFU;
        response.data[offset++] = (matching_dtcs[i] >> 8) & 0xFFU;
        response.data[offset++] = matching_dtcs[i] & 0xFFU;

        /* Status: 1 byte */
        response.data[offset++] = Dem_GetDtcStatus(matching_dtcs[i])->status_byte;

        /* Check response size limit */
        if (offset >= (sizeof(response.data) - 4U)) {
            break;
        }
    }

    response.length = offset;
    return response;
}
```

## DTC Aging Mechanism

```c
/* DTC Aging: Automatic removal after fault-free operation cycles */

typedef struct {
    uint16_t operation_cycle_count;      /* Total cycles since fault */
    uint16_t passed_cycle_count;         /* Consecutive cycles without fault */
    uint16_t failed_cycle_count;         /* Recent cycles with fault */
    uint16_t warm_up_cycle_count;        /* Warm-up cycles for aging */
} Dem_AgingInfo_t;

/* Operation cycle counter (incremented per ignition cycle) */
static uint16_t s_operation_cycle_counter = 0U;

/* Increment operation cycle counter at ignition on */
void Dem_OnIgnitionOn(void) {
    s_operation_cycle_counter++;
    if (s_operation_cycle_counter == 0U) {
        s_operation_cycle_counter = 1U;  /* Wrap around protection */
    }

    /* Clear testFailedThisOperationCycle for all DTCs */
    Dem_ClearAllStatusBits(DEM_STATUS_TEST_FAILED_THIS_CYCLE);
    Dem_ClearAllStatusBits(DEM_STATUS_TEST_NOT_COMPLETED_CYCLE);
}

/* Aging check at ignition off */
void Dem_OnIgnitionOff(void) {
    /* Check all DTCs for aging */
    for (uint32_t dtc = 0U; dtc <= 0xFFFFFFU; dtc++) {
        Dem_DtcStatus_t* status = Dem_GetDtcStatus(dtc);
        if (status == NULL) {
            continue;
        }

        const Dem_EventConfig_t* config = Dem_GetEventConfig(dtc);

        /* Skip permanent DTCs */
        if (config->permanent_dtc) {
            continue;
        }

        /* Check for aging: 40 warm-up cycles without fault */
        if (status->passed_cycle_count >= config->aging_cycles) {
            /* Auto-clear DTC */
            Dem_ClearDtc(dtc);
            Dem_LogEvent(DEM_EVENT_DTC_AGED_OUT, dtc);
        }
    }
}

/* Update aging counters based on test results */
void Dem_UpdateAgingCounters(uint32_t dtc, bool test_passed) {
    Dem_DtcStatus_t* status = Dem_GetDtcStatus(dtc);
    if (status == NULL) {
        return;
    }

    if (test_passed) {
        status->passed_cycle_count++;
        status->failed_cycle_count = 0U;
    } else {
        status->passed_cycle_count = 0U;
        if (status->failed_cycle_count < 255U) {
            status->failed_cycle_count++;
        }
    }
}
```

## OBD-II Integration (Emissions-Related DTCs)

```c
/* OBD-II Mode 03: Read confirmed DTCs (emission-related) */
/* OBD-II Mode 07: Read pending DTCs (emission-related) */
/* OBD-II Mode 0A: Read permanent DTCs (emission-related) */

typedef struct {
    uint8_t mil_status;           /* MIL on/off */
    uint16_t dtc_count;           /* Number of emission DTCs */
    uint8_t readiness_status;     /* Monitor readiness bitmap */
} Obd_Status_t;

/* Read OBD-II status */
Obd_Status_t Obd_GetStatus(void) {
    Obd_Status_t status = {0};

    /* Count emission-related DTCs (P0xxx, P2xxx, P3xxx) */
    uint16_t confirmed_count = 0U;
    uint16_t pending_count = 0U;

    for (uint32_t dtc = 0U; dtc <= 0xFFFFFFU; dtc++) {
        /* Check if powertrain DTC (P0xxx, P2xxx, P3xxx) */
        if ((dtc & 0xF00000U) != 0x000000U) {
            continue;
        }

        const Dem_DtcStatus_t* dStatus = Dem_GetDtcStatus(dtc);
        if (dStatus == NULL) {
            continue;
        }

        /* Count confirmed DTCs for Mode 03 */
        if (Dem_TestStatusBit(dStatus, DEM_STATUS_CONFIRMED_DTC)) {
            confirmed_count++;
        }

        /* Count pending DTCs for Mode 07 */
        if (Dem_TestStatusBit(dStatus, DEM_STATUS_PENDING_DTC)) {
            pending_count++;
        }
    }

    status.mil_status = (confirmed_count > 0U) ? 1U : 0U;
    status.dtc_count = confirmed_count;

    /* Readiness status: 8 bits for different monitors */
    status.readiness_status = Dem_GetReadinessStatus();

    return status;
}

/* Format DTC for OBD-II response */
uint32_t Obd_FormatDtcForMode03(uint32_t dtc) {
    /* Convert internal DTC format to SAE J2012 OBD-II format */
    /* Example: Internal 0x001234 -> OBD-II P0123 */

    /* Extract DTC type (P/B/C/U) */
    uint8_t dtc_type = (dtc >> 22) & 0x03U;

    /* Convert to OBD-II format:
     * P0xxx: 0x00xxxx
     * P1xxx: 0x10xxxx
     * P2xxx: 0x20xxxx
     * P3xxx: 0x30xxxx
     */
    uint32_t obd_dtc = (dtc_type * 0x100000U) | (dtc & 0xFFFFFU);

    return obd_dtc;
}
```

## DTC Severity Classification

```c
/* DTC Severity Levels per AUTOSAR */
typedef enum {
    DEM_SEVERITY_NONE = 0U,      /* No action required */
    DEM_SEVERITY_LOW = 1U,       /* Log only */
    DEM_SEVERITY_MEDIUM = 2U,    /* Warning to driver */
    DEM_SEVERITY_HIGH = 3U,      /* Immediate action required */
    DEM_SEVERITY_CRITICAL = 4U   /* Safe state required */
} Dem_Severity_t;

/* Severity-based reaction table */
typedef struct {
    Dem_Severity_t severity;
    bool log_to_nvm;
    bool illuminate_mil;
    bool limit_vehicle_performance;
    bool request_safe_state;
    bool notify_gateway;
} Dem_SeverityReaction_t;

static const Dem_SeverityReaction_t s_severity_reactions[] = {
    /* NONE */
    {
        .log_to_nvm = false,
        .illuminate_mil = false,
        .limit_vehicle_performance = false,
        .request_safe_state = false,
        .notify_gateway = false
    },
    /* LOW */
    {
        .log_to_nvm = true,
        .illuminate_mil = false,
        .limit_vehicle_performance = false,
        .request_safe_state = false,
        .notify_gateway = false
    },
    /* MEDIUM */
    {
        .log_to_nvm = true,
        .illuminate_mil = true,
        .limit_vehicle_performance = false,
        .request_safe_state = false,
        .notify_gateway = true
    },
    /* HIGH */
    {
        .log_to_nvm = true,
        .illuminate_mil = true,
        .limit_vehicle_performance = true,
        .request_safe_state = false,
        .notify_gateway = true
    },
    /* CRITICAL */
    {
        .log_to_nvm = true,
        .illuminate_mil = true,
        .limit_vehicle_performance = true,
        .request_safe_state = true,
        .notify_gateway = true
    }
};

/* Apply severity-based reaction */
void Dem_ApplySeverityReaction(uint32_t dtc) {
    const Dem_EventConfig_t* config = Dem_GetEventConfig(dtc);
    const Dem_SeverityReaction_t* reaction =
        &s_severity_reactions[config->severity];

    if (reaction->log_to_nvm) {
        Dem_LogToNvm(dtc);
    }

    if (reaction->illuminate_mil) {
        Bcm_IlluminateMil(true);
    }

    if (reaction->limit_vehicle_performance) {
        /* Request performance limitation via gateway */
        Gateway_RequestDerate(GW_DERATE_REASON_DTC, config->severity);
    }

    if (reaction->request_safe_state) {
        /* Enter safe state immediately */
        Safety_EnterSafeState(SAFETY_STATE_DTC_CRITICAL, dtc);
    }

    if (reaction->notify_gateway) {
        /* Notify gateway ECU for fleet monitoring */
        Gateway_NotifyDtc(dtc, config->severity);
    }
}
```

## Approach

1. **Configure Dem module** (AUTOSAR tool: DaVinci Configurator/EB Tresos)
   - Define DTC format and memory layout
   - Configure event storage parameters
   - Set aging and debouncing parameters

2. **Define DTC events** (System design)
   - Create DTC catalog with unique identifiers
   - Assign severity levels and reactions
   - Define freeze frame data requirements

3. **Implement event detection** (Application SWC)
   - Create diagnostic runnable entities
   - Implement fault detection logic
   - Report events to Dem via `Dem_SetEventStatus()`

4. **Configure freeze frame data** (Calibration)
   - Select signals to capture at fault occurrence
   - Define extended data record format
   - Configure freeze frame storage limits

5. **Integrate UDS services** (BSW integration)
   - Implement 0x14 (ClearDiagnosticInformation)
   - Implement 0x19 sub-functions (ReadDTCInformation)
   - Configure DTC filtering by status mask

6. **Validate DTC handling** (HIL testing)
   - Inject faults and verify DTC storage
   - Test aging mechanism with cycle simulation
   - Verify UDS service responses
   - Test freeze frame capture accuracy

## Deliverables

- Dem module configuration (ARXML/C code)
- DTC catalog spreadsheet (DTC code, description, severity, reaction)
- Freeze frame data specification
- Extended data record definitions
- UDS service test report (0x14/0x19 validation)
- Aging mechanism validation report
- OBD-II compliance report (for emissions-related DTCs)

## Related Context

- @context/skills/diagnostics/uds.md (Services 0x14, 0x19 implementation)
- @context/skills/diagnostics/doip.md (Transport layer for diagnostics)
- @context/skills/autosar/classic-platform.md (Dem module integration)
- @context/skills/safety/iso-26262-overview.md (Safety-related DTCs)
- @context/skills/network/can-protocol.md (DTC communication)

## Tools Required

- Vector DaVinci Configurator/Developer (Dem configuration)
- EB Tresos (Dem module setup)
- Vector CANoe/CANalyzer (DTC verification)
- PCAN-View (DTC monitoring)
- OBD-II scanner (Emissions DTC validation)
- HIL simulator (Fault injection testing)

## DTC Troubleshooting Guide

| Symptom | Possible Cause | Diagnostic Step |
|---------|----------------|-----------------|
| DTC not stored | Event not reported to Dem | Check `Dem_SetEventStatus()` calls |
| DTC not clearing | Permanent DTC or security lockout | Verify security access level |
| Freeze frame empty | No slot available | Check `DEM_FREEZE_FRAME_RECORDS` config |
| MIL not illuminating | Severity too low or config error | Check DTC severity classification |
| DTC clears too quickly | Aging parameter too low | Verify `DEM_AGING_OPERATION_CYCLES` |
| Too many pending DTCs | Debouncing too sensitive | Adjust `passed_cycle_threshold` |

## Common Implementation Pitfalls

1. **Not setting all required status bits**
   - Ensure `testFailed` AND `pendingDTC` are set on first failure
   - Set `confirmedDTC` only after debouncing threshold

2. **Incorrect freeze frame capture timing**
   - Capture on first failure in operation cycle, not every cycle
   - Prioritize high-severity DTCs for freeze frame slots

3. **Aging counter not incrementing**
   - Verify operation cycle counter increments at ignition on
   - Ensure passed cycle count resets on fault recurrence

4. **UDS 0x19 response too large**
   - Implement pagination for large DTC lists
   - Use DTC status mask filtering to limit response size

5. **Permanent DTCs accidentally clearable**
   - Set `permanent_dtc = true` in event config
   - Block 0x14 clearing for permanent DTCs
