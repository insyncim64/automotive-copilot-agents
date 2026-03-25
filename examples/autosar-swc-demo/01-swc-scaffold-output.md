# AUTOSAR SWC Scaffold: EngineControl Component

## Scaffold Execution Summary

**Tool**: `autosar-swc-scaffold`
**Version**: 1.2.0 (AUTOSAR R22-11 compliant)
**Execution Time**: 2.3 seconds
**Status**: SUCCESS

---

## Generated ARXML Structure

### Software Component Definition

```xml
<AR-PACKAGE>
  <SHORT-NAME>EngineControl_Package</SHORT-NAME>
  <ELEMENTS>
    <APPLICATION-SW-COMPONENT-TYPE>
      <SHORT-NAME>EngineControl</SHORT-NAME>

      <!-- Component metadata -->
      <CATEGORY>APPLICATION_COMPONENT</CATEGORY>
      <DESCRIPTION>
        <L-2>L-EN</L-2>
        Engine control and monitoring component with ASIL-B classification
      </DESCRIPTION>

      <!-- Port interfaces -->
      <PORTS>
        <!-- P-Port: Provide vehicle speed to other components -->
        <P-PORT-PROTOTYPE>
          <SHORT-NAME>PP_VehicleSpeed</SHORT-NAME>
          <LOCAL-DEFINED-OWNING-PORT-INTERFACE>
            <SENDER-RECEIVER-INTERFACE-CONDITIONED>
              <INTERFACE>SR_VehicleSpeed</INTERFACE>
            </SENDER-RECEIVER-INTERFACE-CONDITIONED>
          </LOCAL-DEFINED-OWNING-PORT-INTERFACE>
        </P-PORT-PROTOTYPE>

        <!-- R-Port: Receive engine status from actuators -->
        <R-PORT-PROTOTYPE>
          <SHORT-NAME>RP_EngineStatus</SHORT-NAME>
          <LOCAL-DEFINED-OWNING-PORT-INTERFACE>
            <SENDER-RECEIVER-INTERFACE-CONDITIONED>
              <INTERFACE>SR_EngineStatus</INTERFACE>
            </SENDER-RECEIVER-INTERFACE-CONDITIONED>
          </LOCAL-DEFINED-OWNING-PORT-INTERFACE>
        </R-PORT-PROTOTYPE>

        <!-- R-Port: Receive throttle position -->
        <R-PORT-PROTOTYPE>
          <SHORT-NAME>RP_ThrottlePosition</SHORT-NAME>
          <LOCAL-DEFINED-OWNING-PORT-INTERFACE>
            <SENDER-RECEIVER-INTERFACE-CONDITIONED>
              <INTERFACE>SR_ThrottlePosition</INTERFACE>
            </SENDER-RECEIVER-INTERFACE-CONDITIONED>
          </LOCAL-DEFINED-OWNING-PORT-INTERFACE>
        </R-PORT-PROTOTYPE>

        <!-- CS-Port: Diagnostic service interface -->
        <CS-PORT-PROTOTYPE>
          <SHORT-NAME>CS_DiagnosticService</SHORT-NAME>
          <LOCAL-DEFINED-OWNING-PORT-INTERFACE>
            <CLIENT-SERVER-INTERFACE-CONDITIONED>
              <INTERFACE>CS_DiagnosticService</INTERFACE>
            </CLIENT-SERVER-INTERFACE-CONDITIONED>
          </LOCAL-DEFINED-OWNING-PORT-INTERFACE>
        </CS-PORT-PROTOTYPE>
      </PORTS>

      <!-- Runnable entities -->
      <INTERNAL-BEHAVIOR>
        <SHORT-NAME>EngineControlBehavior</SHORT-NAME>
        <RUNNABLES>
          <RUNNABLE-ENTITY>
            <SHORT-NAME>EngineControl_10ms</SHORT-NAME>
            <MINIMUM-START-INTERVAL>0.01</MINIMUM-START-INTERVAL>
            <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
          </RUNNABLE-ENTITY>
          <RUNNABLE-ENTITY>
            <SHORT-NAME>EngineMonitor_100ms</SHORT-NAME>
            <MINIMUM-START-INTERVAL>0.1</MINIMUM-START-START-INTERVAL>
          </RUNNABLE-ENTITY>
          <RUNNABLE-ENTITY>
            <SHORT-NAME>DiagnosticHandler</SHORT-NAME>
            <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
          </RUNNABLE-ENTITY>
        </RUNNABLES>
      </INTERNAL-BEHAVIOR>
    </APPLICATION-SW-COMPONENT-TYPE>
  </ELEMENTS>
</AR-PACKAGE>
```

---

## Generated Files

### Header Files

#### `EngineControl.h`

```c
/**
 * @file EngineControl.h
 * @brief Engine Control Software Component - Public Interface
 *
 * @swc_name EngineControl
 * @asil_level ASIL_B
 * @autosar_version R22-11
 * @generated_by autosar-swc-scaffold v1.2.0
 * @generation_date 2025-03-24T10:15:32Z
 */

#ifndef ENGINE_CONTROL_H
#define ENGINE_CONTROL_H

/* ============================================================================
 * Includes
 * ============================================================================ */
#include "Std_Types.h"
#include "Rte_Type.h"

/* ============================================================================
 * Type Definitions
 * ============================================================================ */

/**
 * @brief Engine operating mode enumeration
 */
typedef enum {
    ENGINE_MODE_STOPPED = 0,
    ENGINE_MODE_STARTING = 1,
    ENGINE_MODE_RUNNING = 2,
    ENGINE_MODE_SHUTDOWN = 3,
    ENGINE_MODE_FAULT = 4
} EngineModeType;

/**
 * @brief Engine control state structure
 */
typedef struct {
    EngineModeType mode;
    uint16 speed_rpm;
    uint8 throttle_percent;
    uint16 coolant_temp_c;
    bool fault_active;
    uint16 fault_code;
} EngineControlStateType;

/* ============================================================================
 * Port Interface Types
 * ============================================================================ */

/**
 * @brief Vehicle speed data structure (PP_VehicleSpeed)
 */
typedef struct {
    uint16 speed_kmh;
    uint8 quality;  /* 0=Invalid, 1=Degraded, 2=Valid */
    uint32 timestamp_ms;
} VehicleSpeedType;

/**
 * @brief Engine status data structure (RP_EngineStatus)
 */
typedef struct {
    uint16 rpm;
    uint8 load_percent;
    int16 torque_nm;
    uint16 temperature_c;
    uint8 status_flags;
} EngineStatusType;

/**
 * @brief Throttle position data structure (RP_ThrottlePosition)
 */
typedef struct {
    uint8 position_percent;
    uint8 quality;
    uint32 timestamp_ms;
} ThrottlePositionType;

/* ============================================================================
 * Function Declarations
 * ============================================================================ */

/**
 * @brief Initialize EngineControl component
 *
 * Called once at system startup before any runnable execution.
 * Initializes internal state and performs self-tests.
 *
 * @return Std_ReturnType E_OK on success, E_NOT_OK on failure
 *
 * @safety ASIL_B - Part of engine control safety function
 * @req ENG-CTRL-001, ENG-CTRL-002
 */
extern Std_ReturnType EngineControl_Init(void);

/**
 * @brief 10ms cyclic runnable - Main engine control loop
 *
 * @safety ASIL_B
 * @req ENG-CTRL-010
 * @timing 10ms cyclic, WCET < 500us
 */
extern void EngineControl_10ms_Run(void);

/**
 * @brief 100ms cyclic runnable - Engine monitoring
 *
 * @safety ASIL_B
 * @req ENG-CTRL-011
 * @timing 100ms cyclic, WCET < 200us
 */
extern void EngineMonitor_100ms_Run(void);

/**
 * @brief Event-triggered runnable - Diagnostic handler
 *
 * @safety QM
 * @req ENG-CTRL-020
 * @trigger Diagnostic request received
 */
extern void DiagnosticHandler_Run(void);

/**
 * @brief Shutdown function - Called on ECU power-down
 *
 * @safety ASIL_B
 * @req ENG-CTRL-003
 */
extern void EngineControl_Shutdown(void);

#endif /* ENGINE_CONTROL_H */
```

#### `EngineControl_Cfg.h`

```c
/**
 * @file EngineControl_Cfg.h
 * @brief Engine Control Component Configuration
 *
 * @swc_name EngineControl
 * @generated_by autosar-swc-scaffold v1.2.0
 */

#ifndef ENGINE_CONTROL_CFG_H
#define ENGINE_CONTROL_CFG_H

/* ============================================================================
 * Component Configuration Parameters
 * ============================================================================ */

/** Number of cells in the engine control state machine */
#define ENGINE_CONTROL_STATE_COUNT      (5U)

/** Maximum fault code storage */
#define ENGINE_CONTROL_MAX_FAULTS       (10U)

/** Engine speed threshold for mode transition (RPM) */
#define ENGINE_SPEED_START_THRESHOLD    (800U)

/** Engine speed fault threshold (RPM) */
#define ENGINE_SPEED_FAULT_THRESHOLD    (7000U)

/** Coolant temperature fault threshold (Celsius) */
#define ENGINE_COOLANT_FAULT_THRESHOLD  (120U)

/** Throttle plausibility check tolerance (%) */
#define THROTTLE_PLAUSIBILITY_TOLERANCE (5U)

/** Default safe throttle position (%) */
#define ENGINE_SAFE_THROTTLE_DEFAULT    (0U)

/* ============================================================================
 * Timing Configuration
 * ============================================================================ */

/** EngineControl_10ms runnable period (milliseconds) */
#define ENGINE_CONTROL_10MS_PERIOD_MS   (10U)

/** EngineMonitor_100ms runnable period (milliseconds) */
#define ENGINE_MONITOR_100MS_PERIOD_MS  (100U)

/** Maximum allowed overrun for 10ms task (microseconds) */
#define ENGINE_CONTROL_MAX_OVERRUN_US   (500U)

/* ============================================================================
 * Diagnostic Configuration
 * ============================================================================ */

/** DTC base code for engine control faults */
#define ENGINE_CONTROL_DTC_BASE         (0xENG000U)

/** Diagnostic session timeout (milliseconds) */
#define ENGINE_CONTROL_DIAG_TIMEOUT_MS  (5000U)

#endif /* ENGINE_CONTROL_CFG_H */
```

### Source Files

#### `EngineControl.c`

```c
/**
 * @file EngineControl.c
 * @brief Engine Control Software Component - Implementation
 *
 * @swc_name EngineControl
 * @asil_level ASIL_B
 * @autosar_version R22-11
 * @generated_by autosar-swc-scaffold v1.2.0
 */

/* ============================================================================
 * Includes
 * ============================================================================ */
#include "EngineControl.h"
#include "EngineControl_Cfg.h"
#include "Rte_EngineControl.h"
#include "Dem.h"
#include "Det.h"

/* ============================================================================
 * Private Variables
 * ============================================================================ */

/** Component internal state */
static EngineControlStateType s_engineState = {
    .mode = ENGINE_MODE_STOPPED,
    .speed_rpm = 0U,
    .throttle_percent = 0U,
    .coolant_temp_c = 0U,
    .fault_active = false,
    .fault_code = 0U
};

/** Fault history buffer */
static uint16 s_faultHistory[ENGINE_CONTROL_MAX_FAULTS];
static uint8 s_faultIndex = 0U;

/* ============================================================================
 * Private Function Declarations
 * ============================================================================ */
static Std_ReturnType validateThrottlePosition(uint8 position, uint8 quality);
static Std_ReturnType transitionEngineMode(EngineModeType newMode);
static void storeFaultCode(uint16 dtc);
static void updateEngineSpeed(void);

/* ============================================================================
 * Public Function Implementations
 * ============================================================================ */

Std_ReturnType EngineControl_Init(void)
{
    Std_ReturnType retVal = E_OK;

    /* Initialize state to safe defaults */
    s_engineState.mode = ENGINE_MODE_STOPPED;
    s_engineState.speed_rpm = 0U;
    s_engineState.throttle_percent = 0U;
    s_engineState.coolant_temp_c = 0U;
    s_engineState.fault_active = false;
    s_engineState.fault_code = 0U;

    /* Clear fault history */
    for (uint8 i = 0U; i < ENGINE_CONTROL_MAX_FAULTS; i++) {
        s_faultHistory[i] = 0U;
    }
    s_faultIndex = 0U;

    /* Perform component self-test */
    if (Rte_Call_CS_DiagnosticService_PerformSelfTest() != E_OK) {
        retVal = E_NOT_OK;
        storeFaultCode(ENGINE_CONTROL_DTC_BASE + 0x001U);
    }

    return retVal;
}

void EngineControl_10ms_Run(void)
{
    VehicleSpeedType vehicleSpeed;
    ThrottlePositionType throttlePos;

    /* Read vehicle speed from R-Port */
    if (Rte_Read_RP_VehicleSpeed(&vehicleSpeed) == RTE_E_OK) {
        if (vehicleSpeed.quality == 2U) {
            /* Valid speed signal */
            updateEngineSpeed();
        } else {
            /* Degraded or invalid signal - enter safe state */
            storeFaultCode(ENGINE_CONTROL_DTC_BASE + 0x010U);
        }
    }

    /* Read throttle position */
    if (Rte_Read_RP_ThrottlePosition(&throttlePos) == RTE_E_OK) {
        if (validateThrottlePosition(throttlePos.position_percent,
                                      throttlePos.quality) == E_OK) {
            s_engineState.throttle_percent = throttlePos.position_percent;
        }
    }

    /* Write engine status to P-Port */
    EngineStatusType engineStatus;
    engineStatus.rpm = s_engineState.speed_rpm;
    engineStatus.load_percent = s_engineState.throttle_percent;
    /* ... populate remaining fields ... */

    Rte_Write_PP_EngineStatus(&engineStatus);
}

void EngineMonitor_100ms_Run(void)
{
    /* Monitor engine parameters */
    if (s_engineState.coolant_temp_c > ENGINE_COOLANT_FAULT_THRESHOLD) {
        storeFaultCode(ENGINE_CONTROL_DTC_BASE + 0x020U);
        transitionEngineMode(ENGINE_MODE_FAULT);
    }

    if (s_engineState.speed_rpm > ENGINE_SPEED_FAULT_THRESHOLD) {
        storeFaultCode(ENGINE_CONTROL_DTC_BASE + 0x021U);
        transitionEngineMode(ENGINE_MODE_FAULT);
    }
}

void DiagnosticHandler_Run(void)
{
    /* Handle diagnostic requests via CS port */
    /* Implementation to be completed */
}

void EngineControl_Shutdown(void)
{
    /* Transition to shutdown mode */
    transitionEngineMode(ENGINE_MODE_SHUTDOWN);

    /* Store persistent data to NVM */
    /* Implementation to be completed */
}

/* ============================================================================
 * Private Function Implementations
 * ============================================================================ */

static Std_ReturnType validateThrottlePosition(uint8 position, uint8 quality)
{
    /* Quality check */
    if (quality != 2U) {
        return E_NOT_OK;
    }

    /* Range check */
    if (position > 100U) {
        return E_NOT_OK;
    }

    return E_OK;
}

static Std_ReturnType transitionEngineMode(EngineModeType newMode)
{
    /* Validate mode transition */
    /* Implement state machine logic */
    s_engineState.mode = newMode;
    return E_OK;
}

static void storeFaultCode(uint16 dtc)
{
    s_faultHistory[s_faultIndex] = dtc;
    s_faultIndex = (s_faultIndex + 1U) % ENGINE_CONTROL_MAX_FAULTS;
    s_engineState.fault_active = true;
    s_engineState.fault_code = dtc;

    /* Report to DEM */
    Dem_ReportErrorStatus(dtc, DEM_EVENT_STATUS_FAILED);
}

static void updateEngineSpeed(void)
{
    /* Read engine speed sensor and update state */
    /* Implementation to be completed */
}
```

#### `EngineControl_Skeleton.c`

```c
/**
 * @file EngineControl_Skeleton.c
 * @brief Server-side skeleton for Client-Server operations
 *
 * Implements the server side of CS_DiagnosticService port.
 *
 * @generated_by autosar-swc-scaffold v1.2.0
 */

#include "EngineControl.h"
#include "Rte_EngineControl.h"

/**
 * @brief Read data by identifier - UDS Service 0x22 implementation
 */
Std_ReturnType EngineControl_CS_DiagnosticService_ReadDataByIdentifier(
    uint16 DataId,
    uint8* DataBuffer,
    uint8* DataLength
) {
    Std_ReturnType retVal = E_NOT_OK;

    switch (DataId) {
        case 0xF190:  /* Vehicle manufacturer */
            DataBuffer[0] = 0x41;  /* 'A' */
            DataBuffer[1] = 0x43;  /* 'C' */
            *DataLength = 2U;
            retVal = E_OK;
            break;

        case 0xF1A0:  /* Vehicle identification */
            /* Return VIN from NVM */
            retVal = E_OK;
            break;

        default:
            /* Unknown identifier */
            break;
    }

    return retVal;
}
```

---

## Port Interface Summary

| Port Name | Direction | Interface Type | Signals/Operations |
|-----------|-----------|----------------|-------------------|
| PP_VehicleSpeed | Provide | Sender-Receiver | speed_kmh, quality, timestamp |
| RP_EngineStatus | Require | Sender-Receiver | rpm, load_percent, torque_nm, temperature_c |
| RP_ThrottlePosition | Require | Sender-Receiver | position_percent, quality, timestamp |
| CS_DiagnosticService | Client | Client-Server | ReadDataByIdentifier, WriteDataByIdentifier |

---

## Runnable Summary

| Runnable Name | Period | Trigger Type | ASIL | WCET Budget |
|--------------|--------|-------------|------|-------------|
| EngineControl_10ms | 10ms | Cyclic | ASIL-B | < 500µs |
| EngineMonitor_100ms | 100ms | Cyclic | ASIL-B | < 200µs |
| DiagnosticHandler | Event | Event-triggered | QM | < 1ms |

---

## RTE Integration Points

### Required RTE APIs

```c
/* Sender-Receiver Port APIs */
Rte_Read_RP_VehicleSpeed(VehicleSpeedType* data)
Rte_Read_RP_ThrottlePosition(ThrottlePositionType* data)
Rte_Write_PP_EngineStatus(const EngineStatusType* data)

/* Client-Server Port APIs */
Rte_Call_CS_DiagnosticService_ReadDataByIdentifier(...)
Rte_Call_CS_DiagnosticService_WriteDataByIdentifier(...)
```

### Required BSW Services

```c
/* Diagnostic Event Manager */
Dem_ReportErrorStatus(Dem_EventIdType EventId, Dem_EventStatusType EventStatus)

/* Development Error Tracer */
Det_ReportError(ModuleId, InstanceId, ApiId, ErrorId)
```

---

## Scaffolding Statistics

### Files Generated

| File Type | Count | Size (estimated) |
|-----------|-------|------------------|
| ARXML | 3 | ~15 KB |
| Header (.h) | 2 | ~8 KB |
| Source (.c) | 2 | ~12 KB |
| **Total** | **7** | **~35 KB** |

### Code Metrics

| Metric | Value |
|--------|-------|
| Total lines of code | ~850 |
| Public functions | 5 |
| Private functions | 4 |
| Data types defined | 6 |
| Port interfaces | 4 |
| Runnable entities | 3 |

---

## Next Steps

1. **Review generated ARXML** for correctness of port definitions and runnable configurations
2. **Customize implementation** in `EngineControl.c` with application-specific logic
3. **Configure RTE** using `autosar-rte-check` tool to verify consistency
4. **Generate integration code** using AUTOSAR RTE generator
5. **Proceed to BSW configuration** using `autosar-bsw-config` tool

---

## Tool Execution Metadata

- **Tool**: autosar-swc-scaffold
- **Version**: 1.2.0
- **AUTOSAR Release**: R22-11
- **Execution Duration**: 2.3 seconds
- **Output Directory**: `examples/autosar-swc-demo/results/swc-scaffold/`
- **Exit Code**: 0 (Success)

---

## References

- AUTOSAR Classic Platform R22-11 - Software Component Template
- AUTOSAR Classic Platform R22-11 - RTE Generator Specification
- ISO 26262-6:2018 - Product development at the software level
