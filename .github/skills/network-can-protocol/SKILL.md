---
name: network-can-protocol
description: "Use when: Skill: CAN Protocol Development for Automotive Networks topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: CAN Protocol Development for Automotive Networks

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/network/can-protocol.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate
- User asks about CAN bus communication, message structure, or protocol details
- User needs to implement CAN drivers or configure AUTOSAR CAN stack
- User requests DBC file configuration or signal encoding patterns
- User is developing diagnostic services (UDS over CAN)
- User asks about CAN-FD extensions or migration from classic CAN
- User needs E2E protection patterns for safety-critical messages
- User requests bus load calculation or optimization strategies

## Standards Compliance
- ISO 11898-1:2015 (CAN Data Link Layer)
- ISO 11898-2:2016 (CAN High-Speed Physical Layer)
- ISO 11898-3:2006 (CAN Low-Speed Fault-Tolerant Physical Layer)
- ISO 11898-7:2020 (CAN Transceiver Behavior)
- ISO 11898-1:2024 (CAN-FD extensions)
- SAE J1939 (Commercial vehicle CAN application layer)
- AUTOSAR 4.4 (CAN stack architecture: CanIf, CanTransceiver, PduR)
- ISO 26262:2018 (Functional Safety - ASIL B/C/D for safety messages)
- ASPICE Level 3 (Model-based development process)
- ISO 21434:2021 (Cybersecurity - CAN message authentication)

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| CAN ID (standard) | 0x000 - 0x7FF | 11-bit identifier |
| CAN ID (extended) | 0x00000000 - 0x1FFFFFFF | 29-bit identifier |
| DLC (Data Length Code) | 0 - 8 (classic), 0 - 15 (CAN-FD) | bytes |
| Bit rate (nominal) | 10 kbps - 1 Mbps | kbps |
| CAN-FD data bit rate | Up to 8 Mbps | Mbps |
| Bus load (recommended max) | < 70% | percentage |
| Sample point | 70% - 90% | percentage of bit time |
| Propagation delay | Depends on cable length | microseconds |
| Dominant bit | Logical 0 (differential voltage > 0.9V) | Vdiff |
| Recessive bit | Logical 1 (differential voltage < 0.5V) | Vdiff |

## CAN Architecture Overview

```
+-------------------------------------------------------------------+
|                    AUTOSAR CAN Stack                               |
+-------------------------------------------------------------------+
|  Application Layer (SWC)                                          |
|  +-------------+  +-------------+  +-------------+                |
|  | EngineCtrl  |  | BmsManager  |  | DiagService |                |
|  +------+------+  +------+------+  +------+------+                |
|         |                |                |                       |
+---------|----------------|----------------|-----------------------+
|         v                v                v         AUTOSAR RTE   |
|  +------+-------+ +------+-------+ +------+-------+               |
|  | CanIf (IF)   | | CanIf (IF)   | | CanIf (IF)   |               |
|  +------+-------+ +------+-------+ +------+-------+               |
|         |                |                |                       |
+---------|----------------|----------------|-----------------------+
|         v                v                v         BSW           |
|  +------+------------------------------------------------+       |
|  |              PduR (PDU Router)                         |       |
|  +------+------------------------------------------------+       |
|         |                                                         |
+---------|---------------------------------------------------------+
|         v                       CAN Network Layer                 |
|  +------+-------+ +------------------------+ +----------------+   |
|  | Can Driver   | | CanTransceiver (CanTrcv)| | CanTrcv Triggers|  |
|  +------+-------+ +------------------------+ +----------------+   |
|         |                                                         |
+---------|---------------------------------------------------------+
|         v                       Microcontroller                   |
|  +------+-------+                                                  |
|  | CAN Hardware | (MultiCAN, FlexCAN, bxCAN)                      |
|  +------+-------+                                                  |
|         |                                                         |
+---------|---------------------------------------------------------+
          v                       Physical Layer
  +-------+-------+
  | CAN Bus (2-wire)| (CAN_H, CAN_L, 120Ω termination)             |
  +---------------+
```

## CAN Frame Structure

### Classic CAN 2.0A/B Frame Format

```
+---------------+----------+---------+---------------+-----+----------+
| Start of Frame| Arbitration| Control | Data Field  | CRC | ACK | EOF |
| (1 bit, dom)  | (11/29 bit)| (4 bit) | (0-8 bytes) | (15)| (2)| (7) |
+---------------+----------+---------+---------------+-----+-----+----+
                          |
                          v
             Standard Frame (CAN 2.0A):
             +----+----+---------------+
             | IDE| RTR| ID[10:0]      |  (11-bit ID)
             +----+----+---------------+

             Extended Frame (CAN 2.0B):
             +----+----+---------------+----+----+---------------+
             | IDE| RTR| ID[28:18]     | SRR| IDE| ID[17:0]      |  (29-bit ID)
             +----+----+---------------+----+----+---------------+
```

### CAN-FD Frame Format (ISO 11898-1:2024)

```
Classic CAN:
+---+---+------+---+---+---+---+---+---+---+
|SOF|ARB |CTRL |DLC|DATA   |CRC|ACK|EOF|IFS|
+---+---+------+---+---+---+---+---+---+---+
  |   |       Nominal Bit Rate (500 kbps)   |

CAN-FD:
+---+---+------+---+---+---+---+---+---+---+
|SOF|ARB |CTRL |DLC|DATA   |CRC|ACK|EOF|IFS|
+---+---+------+---+---+---+---+---+---+---+
  |   |       Nominal Phase (500 kbps)      |
  |                   +----+                |
  |                   |                    |
  |                   v                    |
  |             Data Phase (2 Mbps)        |
  |                                        |
  +----------------------------------------+
              Flexible Data Rate
```

### CAN-FD DLC to Data Length Mapping

| DLC Value | Data Bytes | DLC Value | Data Bytes |
|-----------|-----------|-----------|-----------|
| 0 | 0 | 8 | 8 |
| 1 | 1 | 9 | 12 |
| 2 | 2 | 10 | 16 |
| 3 | 3 | 11 | 20 |
| 4 | 4 | 12 | 24 |
| 5 | 5 | 13 | 32 |
| 6 | 6 | 14 | 48 |
| 7 | 7 | 15 | 64 |

## CAN Driver Implementation

### Hardware Abstraction Layer

```c
/* CAN Driver - AUTOSAR Classic Platform */
/* Module: Can.c */

#include "Can.h"
#include "Can_Cfg.h"
#include "CanIf_Cbk.h"
#include "Det.h"

/* Development error detection */
#if (CAN_DEV_ERROR_DETECT == STD_ON)
#define CAN_VALIDATE_PTR(_ptr_, _sid_) \
    if ((_ptr_) == NULL_PTR) { \
        Det_ReportError(CAN_MODULE_ID, CAN_INSTANCE_ID, \
                        (_sid_), CAN_E_PARAM_POINTER); \
        return E_NOT_OK; \
    }
#else
#define CAN_VALIDATE_PTR(_ptr_, _sid_)
#endif

/* CAN Hardware Object configuration */
typedef struct {
    Can_HwHandleType Hth;           /* Hardware object index */
    Can_IdType Id;                  /* CAN identifier (11 or 29 bit) */
    Can_ObjectType ObjectType;      /* TRANSMIT or RECEIVE */
    PduIdType CanSduId;             /* Linked PDU ID */
    uint8 DataLength;               /* DLC (0-8 for classic, 0-15 for FD) */
} Can_HardwareObjectConfigType;

/* CAN Controller configuration */
typedef struct {
    uint8 ControllerId;                         /* Logical controller index */
    const Can_HardwareObjectConfigType* HwObjs; /* Hardware object array */
    uint8 HwObjCount;                          /* Number of hardware objects */
    Can_ControllerBaudrateConfigType* Baudrate; /* Baudrate configuration */
    Can_ProcessingType ProcessingType;         /* POLLING or INTERRUPT */
} Can_ControllerConfigType;

/* Global CAN driver state */
typedef struct {
    Can_ControllerStateType State;  /* UNINIT, STOPPED, STARTED */
    Can_HwHandleType ErrorStateHth; /* Hardware object in error state */
    uint16 TxErrorCount;            /* Transmit error counter */
    uint16 RxErrorCount;            /* Receive error counter */
} Can_DriverStateType;

static Can_DriverStateType Can_DriverState[CAN_CONTROLLER_COUNT];
static const Can_ConfigType* Can_ConfigPtr = NULL_PTR;

/* CAN Module Initialization */
void Can_Init(const Can_ConfigType* Config) {
    CAN_VALIDATE_PTR(Config, CAN_INIT_SID);

    Can_ConfigPtr = Config;

    /* Initialize all controllers */
    for (uint8 ctrl = 0; ctrl < CAN_CONTROLLER_COUNT; ctrl++) {
        Can_DriverState[ctrl].State = CAN_CS_STOPPED;
        Can_DriverState[ctrl].TxErrorCount = 0;
        Can_DriverState[ctrl].RxErrorCount = 0;

        /* Configure hardware registers */
        Can_InitControllerHardware(ctrl, &Config->Controllers[ctrl]);
    }
}

/* CAN Controller Start */
void Can_StartController(Can_ControllerType Controller) {
    if (Can_DriverState[Controller].State == CAN_CS_STOPPED) {
        Can_EnableInterrupts(Controller);
        Can_DriverState[Controller].State = CAN_CS_STARTED;
    }
}

/* Transmit function - called by CanIf */
Std_ReturnType Can_Write(Can_HwHandleType Hth, const Can_PduType* PduInfo) {
    CAN_VALIDATE_PTR(PduInfo, CAN_WRITE_SID);

    /* Find controller for this hardware object */
    Can_ControllerType ctrl = Can_GetControllerForHth(Hth);

    if (Can_DriverState[ctrl].State != CAN_CS_STARTED) {
        return CAN_NOT_OK;
    }

    /* Check transmit buffer availability */
    if (!Can_IsTxBufferAvailable(Hth)) {
        return CAN_BUSY;
    }

    /* Write to hardware transmit buffer */
    Can_WriteToHardware(Hth, PduInfo->SwPduHandle, PduInfo->Length,
                        PduInfo->SduPtr);

    return CAN_OK;
}

/* RX Indication callback to CanIf */
void Can_RxIndication(Can_HwHandleType Hth, const Can_PduType* PduInfo) {
    CanIf_RxIndication(PduInfo->SwPduHandle, PduInfo);
}

/* TX Confirmation callback to CanIf */
void Can_TxConfirmation(Can_PduType* PduInfo, Can_NotificationStatusType NotificationStatus) {
    CanIf_TxConfirmation(PduInfo, NotificationStatus);
}
```

### CAN Hardware Register Access (Infineon TC3xx MultiCAN)

```c
/* CAN Hardware abstraction for Infineon TC397 MultiCAN+ */

#define MULTICAN_BASE       0xF0004000UL
#define CAN_MODULE_BASE(x)  (MULTICAN_BASE + ((x) * 0x1000UL))

typedef struct {
    volatile uint32 CR;      /* Control Register */
    volatile uint32 NBTP;    /* Nominal Bit Timing Register */
    volatile uint32 DBTP;    /* Data Bit Timing Register (FD) */
    volatile uint32 ECR;     /* Error Counter Register */
    volatile uint32 PSR;     /* Protocol Status Register */
    volatile uint32 ILIT;    /* Interrupt Line Input Test */
    volatile uint32 ILEC;    /* Interrupt Line Control */
    volatile uint32 GFC;     /* Global Filter Configuration */
    volatile uint32 SIDFC;   /* Standard ID Filter Configuration */
    volatile uint32 XIDFC;   /* Extended ID Filter Configuration */
    volatile uint32 XIDAM;   /* Extended ID Acceptance Mask */
    volatile uint32 RXF0C;   /* RX FIFO 0 Configuration */
    volatile uint32 RXF0S;   /* RX FIFO 0 Status */
    volatile uint32 RXF0A;   /* RX FIFO 0 Acknowledge */
    volatile uint32 RXBC;    /* RX Buffer Configuration */
    volatile uint32 TXBC;    /* TX Buffer Configuration */
    volatile uint32 TXBRP;   /* TX Buffer Request Pending */
    volatile uint32 TXBAR;   /* TX Buffer Add Request */
    volatile uint32 TXBCR;   /* TX Buffer Cancellation Request */
    volatile uint32 TXBTO;   /* TX Buffer Transmission Occurred */
    volatile uint32 TXBCF;   /* TX Buffer Cancellation Finished */
    volatile uint32 TXBTIE;  /* TX Buffer Transmission Interrupt Enable */
    volatile uint32 TXBCIE;  /* TX Buffer Cancellation Finished IE */
} Can_HwRegs_t;

static Can_HwRegs_t* const Can_HwRegs[CAN_HW_UNIT_COUNT] = {
    (Can_HwRegs_t*)CAN_MODULE_BASE(0),  /* CAN0 */
    (Can_HwRegs_t*)CAN_MODULE_BASE(1),  /* CAN1 */
    (Can_HwRegs_t*)CAN_MODULE_BASE(2),  /* CAN2 */
};

/* Configure bit timing for 500 kbps (assuming 80 MHz CAN clock) */
void Can_ConfigureBaudrate(Can_HwUnitType hwUnit,
                            uint32 baudrate_kbps,
                            uint16 sample_point_percent) {
    Can_HwRegs_t* hw = Can_HwRegs[hwUnit];

    /* Calculate bit timing parameters */
    const uint32 can_clock_hz = 80000000UL;
    const uint32 target_bitrate = baudrate_kbps * 1000UL;
    const uint32 total_pairs = can_clock_hz / (2UL * target_bitrate);

    /* Nominal bit time = 1 + PROP_SEG + PHASE_SEG1 + PHASE_SEG2 */
    /* Target: sample point at 75% (typical) */
    const uint16 prop_seg = 2;  /* Fixed */
    const uint16 phase_seg1 = (total_pairs * sample_point_percent / 100) - prop_seg - 1;
    const uint16 phase_seg2 = total_pairs - prop_seg - phase_seg1 - 1;
    const uint16 sjw = phase_seg2;  /* SJW = Phase Seg 2 for resync */

    /* Write Nominal Bit Timing Register */
    hw->NBTP = ((sjw - 1) << 25) |
               ((phase_seg1 - 1) << 16) |
               ((phase_seg2 - 1) << 8) |
               ((prop_seg - 1) << 0);
}

/* Configure CAN-FD data phase for 2 Mbps */
void Can_ConfigureFdDataBaudrate(Can_HwUnitType hwUnit,
                                  uint32 data_baudrate_kbps) {
    Can_HwRegs_t* hw = Can_HwRegs[hwUnit];

    const uint32 can_clock_hz = 80000000UL;
    const uint32 target_bitrate = data_baudrate_kbps * 1000UL;
    const uint32 total_pairs = can_clock_hz / (2UL * target_bitrate);

    const uint16 prop_seg = 2;
    const uint16 phase_seg1 = 6;
    const uint16 phase_seg2 = total_pairs - prop_seg - phase_seg1 - 1;
    const uint16 sjw = phase_seg2;

    /* Write Data Bit Timing Register */
    hw->DBTP = ((sjw - 1) << 25) |
               ((phase_seg1 - 1) << 16) |
               ((phase_seg2 - 1) << 8) |
               ((prop_seg - 1) << 0) |
               (1UL << 30);  /* TDC (Transmitter Delay Compensation) enable */
}
```

## DBC File Configuration

### DBC File Structure

```dbc
VERSION ""


NS_ :
    NS_DESC_
    CM_
    BA_DEF_
    BA_
    VAL_
    CAT_DEF_
    CAT_
    FILTER
    BA_DEF_DEF_
    EV_DATA_
    ENVVAR_DATA_
    SGTYPE_
    SGTYPE_VAL_
    BA_DEF_SGTYPE_
    BA_SGTYPE_
    SIG_TYPE_REF_
    VAL_TABLE_
    SIG_GROUP_
    SIG_VALTYPE_
    SIGTYPE_VALTYPE_
    BO_TX_BU_
    BA_DEF_REL_
    BA_REL_
    BA_DEF_DEF_REL_
    BU_SG_REL_
    BU_EV_REL_
    BU_BO_REL_
    SG_MUL_VAL_

BS_:

BU_: VSAggregator BmsMaster Inverter MotorCtrl DiagnosticTester Gateway


BO_ 256 BMS_Status: 8 BmsMaster
 SG_ CellVoltageMax : 0|12@1+ (0.001,0) [0|4.095] "V" Vector__XXX
 SG_ CellVoltageMin : 12|12@1+ (0.001,0) [0|4.095] "V" Vector__XXX
 SG_ PackCurrent : 24|16@1+ (0.1,-3200) [-3200|3200] "A" Vector__XXX
 SG_ PackSoc : 40|8@1+ (1,0) [0|100] "%" Vector__XXX
 SG_ BmsStatus : 48|4@1+ (1,0) [0|15] "" Vector__XXX
 SG_ ContactorState : 52|2@1+ (1,0) [0|3] "" Vector__XXX


BO_ 512 Motor_TorqueCmd: 8 VSAggregator
 SG_ TorqueRequest : 0|16@1+ (0.5,0) [0|32000] "Nm" Vector__XXX
 SG_ TorqueRateLimit : 16|16@1+ (0.5,0) [0|32000] "Nm/s" Vector__XXX
 SG_ SpeedLimit : 32|16@1+ (1,0) [0|65000] "rpm" Vector__XXX
 SG_ MotorControlMode : 48|4@1+ (1,0) [0|15] "" Vector__XXX


VAL_ 256 ContactorState 0 "OPEN" 1 "CLOSED" 2 "PRECHARGE" 3 "FAULT";
VAL_ 512 MotorControlMode 0 "TORQUE" 1 "SPEED" 2 "POSITION" 3 "FAULT";
```

### DBC Signal Encoding/Decoding

```c
/* Signal encoding/decoding utilities for Intel (little-endian) format */

/* Extract signal from CAN data bytes */
static inline float decode_signal_intel(const uint8_t* data,
                                         uint16_t start_bit,
                                         uint8_t length,
                                         float factor,
                                         float offset) {
    uint64_t raw_value = 0;

    /* Intel format: LSB first, little-endian across bytes */
    for (uint8_t i = 0; i < length; i++) {
        uint16_t bit_pos = start_bit + i;
        uint8_t byte_index = bit_pos / 8;
        uint8_t bit_index = bit_pos % 8;

        if (data[byte_index] & (1U << bit_index)) {
            raw_value |= (1ULL << i);
        }
    }

    /* Handle signed values */
    if (length < 64) {
        const int64_t sign_bit = (1ULL << (length - 1));
        if (raw_value & sign_bit) {
            raw_value |= (~0ULL << length);  /* Sign extend */
        }
    }

    return ((int64_t)raw_value * factor) + offset;
}

/* Encode signal into CAN data bytes */
static inline void encode_signal_intel(uint8_t* data,
                                        uint16_t start_bit,
                                        uint8_t length,
                                        float value,
                                        float factor,
                                        float offset) {
    /* Apply scaling and offset */
    int64_t raw_value = (int64_t)((value - offset) / factor);

    /* Mask to signal length */
    const uint64_t mask = (length >= 64) ? UINT64_MAX : ((1ULL << length) - 1);
    raw_value &= mask;

    /* Intel format: LSB first */
    for (uint8_t i = 0; i < length; i++) {
        uint16_t bit_pos = start_bit + i;
        uint8_t byte_index = bit_pos / 8;
        uint8_t bit_index = bit_pos % 8;

        if (raw_value & (1ULL << i)) {
            data[byte_index] |= (1U << bit_index);
        } else {
            data[byte_index] &= ~(1U << bit_index);
        }
    }
}

/* Motorola format (big-endian) extraction */
static inline float decode_signal_motorola(const uint8_t* data,
                                            uint16_t start_bit,
                                            uint8_t length,
                                            float factor,
                                            float offset) {
    uint64_t raw_value = 0;

    /* Motorola format: MSB first, big-endian across bytes */
    for (uint8_t i = 0; i < length; i++) {
        uint16_t bit_pos = start_bit - i;  /* Count backward for Motorola */
        uint8_t byte_index = bit_pos / 8;
        uint8_t bit_index_in_byte = 7 - (bit_pos % 8);

        if (data[byte_index] & (1U << bit_index_in_byte)) {
            raw_value |= (1ULL << (length - 1 - i));
        }
    }

    return ((int64_t)raw_value * factor) + offset;
}

/* Example: Decode BMS_Status message (BO_ 256) */
typedef struct {
    float cell_voltage_max_v;
    float cell_voltage_min_v;
    float pack_current_a;
    uint8_t pack_soc_percent;
    uint8_t bms_status;
    uint8_t contactor_state;
} BmsStatus_t;

BmsStatus_t decode_bms_status(const uint8_t can_data[8]) {
    BmsStatus_t status;

    status.cell_voltage_max_v = decode_signal_intel(can_data, 0, 12, 0.001f, 0.0f);
    status.cell_voltage_min_v = decode_signal_intel(can_data, 12, 12, 0.001f, 0.0f);
    status.pack_current_a = decode_signal_intel(can_data, 24, 16, 0.1f, -3200.0f);
    status.pack_soc_percent = (uint8_t)decode_signal_intel(can_data, 40, 8, 1.0f, 0.0f);
    status.bms_status = (uint8_t)decode_signal_intel(can_data, 48, 4, 1.0f, 0.0f);
    status.contactor_state = (uint8_t)decode_signal_intel(can_data, 52, 2, 1.0f, 0.0f);

    return status;
}
```

## E2E Protection (End-to-End)

### E2E Profile for ASIL-Rated Messages

```c
/* AUTOSAR E2E Profile 01 - Data Freshness + CRC8 + Data ID */

#define E2E_CRC8_POLYNOMIAL     0x1DU   /* SAE J1850 */
#define E2E_CRC8_INIT           0xFFU
#define E2E_CRC8_XOR_OUT        0xFFU
#define E2E_DATA_ID             0x42U   /* Unique per message */
#define E2E_MAX_COUNTER_JUMP    2U      /* Allow one missed message */

typedef struct {
    uint8_t Data[7];        /* Application data (7 bytes) */
    uint8_t Counter: 4;     /* Rolling counter (0-15) */
    uint8_t DataId: 4;      /* Data identifier (fixed) */
    uint8_t Crc;            /* CRC-8 over Data + Counter + DataId */
} E2E_ProtectedMessage_t;

/* Compute E2E CRC-8 */
static uint8_t e2e_compute_crc8(const uint8_t* data, uint8_t length) {
    uint8_t crc = E2E_CRC8_INIT;

    for (uint8_t i = 0; i < length; i++) {
        crc ^= data[i];
        for (uint8_t bit = 0; bit < 8; bit++) {
            if (crc & 0x01) {
                crc = (crc >> 1) ^ E2E_CRC8_POLYNOMIAL;
            } else {
                crc >>= 1;
            }
        }
    }

    return crc ^ E2E_CRC8_XOR_OUT;
}

/* Protect outgoing message */
E2E_ProtectedMessage_t e2e_protect_message(
    const uint8_t app_data[7],
    uint8_t* counter_ptr) {

    E2E_ProtectedMessage_t protected_msg;

    /* Copy application data */
    memcpy(protected_msg.Data, app_data, 7);

    /* Update counter */
    protected_msg.Counter = (*counter_ptr) & 0x0FU;
    protected_msg.DataId = E2E_DATA_ID;

    /* Compute CRC over Data + Counter + DataId */
    uint8_t crc_input[8];
    memcpy(crc_input, app_data, 7);
    crc_input[7] = (protected_msg.Counter << 4) | protected_msg.DataId;

    protected_msg.Crc = e2e_compute_crc8(crc_input, 8);

    /* Increment counter for next message */
    *counter_ptr = (*counter_ptr + 1U) & 0x0FU;

    return protected_msg;
}

/* Verify incoming protected message */
typedef enum {
    E2E_OK,
    E2E_CRC_ERROR,
    E2E_COUNTER_ERROR,
    E2E_DATA_ID_ERROR
} E2E_CheckResult_t;

E2E_CheckResult_t e2e_verify_message(
    const E2E_ProtectedMessage_t* msg,
    uint8_t* expected_counter_ptr) {

    /* Check Data ID */
    if (msg->DataId != E2E_DATA_ID) {
        return E2E_DATA_ID_ERROR;
    }

    /* Verify CRC */
    uint8_t crc_input[8];
    memcpy(crc_input, msg->Data, 7);
    crc_input[7] = (msg->Counter << 4) | msg->DataId;

    const uint8_t computed_crc = e2e_compute_crc8(crc_input, 8);
    if (computed_crc != msg->Crc) {
        return E2E_CRC_ERROR;
    }

    /* Check counter (allow jump of 1 for missed message) */
    const uint8_t expected_counter = *expected_counter_ptr & 0x0FU;
    const uint8_t counter_diff = (msg->Counter - expected_counter) & 0x0FU;

    if ((counter_diff > E2E_MAX_COUNTER_JUMP) && (counter_diff != 0)) {
        return E2E_COUNTER_ERROR;
    }

    /* Update expected counter */
    *expected_counter_ptr = msg->Counter;

    return E2E_OK;
}
```

## UDS Diagnostic Services over CAN

### UDS Request/Response Pattern

```c
/* UDS (ISO 14229) services over CAN (ISO 15765-2 transport layer) */

/* UDS Service IDs */
#define UDS_SID_DIAGNOSTIC_SESSION_CONTROL  0x10
#define UDS_SID_ECU_RESET                   0x11
#define UDS_SID_READ_DATA_BY_IDENTIFIER     0x22
#define UDS_SID_READ_DATA_BY_PERIODIC_ID    0x2A
#define UDS_SID_SECURITY_ACCESS             0x27
#define UDS_SID_COMMUNICATION_CONTROL       0x28
#define UDS_SID_READ_DTC_INFORMATION        0x19
#define UDS_SID_WRITE_DATA_BY_IDENTIFIER    0x2E
#define UDS_SID_ROUTINE_CONTROL             0x31
#define UDS_SID_REQUEST_DOWNLOAD            0x34
#define UDS_SID_REQUEST_UPLOAD              0x35
#define UDS_SID_TRANSFER_DATA               0x36
#define UDS_SID_REQUEST_TRANSFER_EXIT       0x37
#define UDS_SID_CONTROL_DTC_SETTING         0x85

/* Positive response = SID + 0x40 */
#define UDS_POSITIVE_RESPONSE(sid)          ((sid) + 0x40)

/* Negative Response Code (NRC) values */
#define UDS_NRC_POSITIVE_RESPONSE           0x00
#define UDS_NRC_GENERAL_REJECT              0x10
#define UDS_NRC_SERVICE_NOT_SUPPORTED       0x11
#define UDS_NRC_SUB_FUNCTION_NOT_SUPPORTED  0x12
#define UDS_NRC_INCORRECT_MESSAGE_LENGTH    0x13
#define UDS_NRC_REQUEST_SEQUENCE_ERROR      0x1E
#define UDS_NRC_REQUEST_OUT_OF_RANGE        0x31
#define UDS_NRC_SECURITY_ACCESS_DENIED      0x33
#define UDS_NRC_INVALID_KEY                 0x35
#define UDS_NRC_EXCEEDED_NUMBER_OF_ATTEMPTS 0x36
#define UDS_NRC_REQUEST_PENDING             0x78
#define UDS_NRC_SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION 0x7E
#define UDS_NRC_SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION 0x7F

/* UDS Request handler */
typedef struct {
    uint8_t Sid;
    uint8_t SubFunction;
    const uint8_t* DataPtr;
    uint16_t Length;
} UdsRequest_t;

typedef struct {
    uint8_t Sid;
    uint8_t Data[7];  /* Max 7 bytes for single-frame response */
    uint8_t Length;
} UdsResponse_t;

/* Session control handler */
UdsResponse_t handle_diagnostic_session_control(const UdsRequest_t* req) {
    UdsResponse_t resp;
    resp.Sid = UDS_POSITIVE_RESPONSE(UDS_SID_DIAGNOSTIC_SESSION_CONTROL);
    resp.Length = 4;

    switch (req->SubFunction) {
        case 0x01:  /* Default Session */
            resp.Data[0] = 0x01;
            resp.Data[1] = 0xF4;  /* P2 timing: 50ms */
            resp.Data[2] = 0x00;  /* P2* timing: 0ms */
            resp.Data[3] = 0x00;
            break;

        case 0x02:  /* Programming Session */
            resp.Data[0] = 0x02;
            resp.Data[1] = 0x50;  /* P2 timing: 50ms */
            resp.Data[2] = 0x01;  /* P2* timing: 5000ms */
            resp.Data[3] = 0xF4;
            break;

        case 0x03:  /* Extended Diagnostic Session */
            resp.Data[0] = 0x03;
            resp.Data[1] = 0x10;  /* P2 timing: 10ms */
            resp.Data[2] = 0x00;
            resp.Data[3] = 0x00;
            break;

        default:
            resp.Sid = 0x7F;  /* Negative Response */
            resp.Data[0] = UDS_SID_DIAGNOSTIC_SESSION_CONTROL;
            resp.Data[1] = UDS_NRC_SUB_FUNCTION_NOT_SUPPORTED;
            resp.Length = 2;
            break;
    }

    return resp;
}

/* Read Data By Identifier handler */
UdsResponse_t handle_read_data_by_identifier(const UdsRequest_t* req) {
    UdsResponse_t resp;
    resp.Sid = UDS_POSITIVE_RESPONSE(UDS_SID_READ_DATA_BY_IDENTIFIER);

    /* DID (Data Identifier) from request data */
    uint16_t did = (req->DataPtr[0] << 8) | req->DataPtr[1];

    switch (did) {
        case 0xF190:  /* Vehicle Identification Number */
            resp.Data[0] = 0xF1;
            resp.Data[1] = 0x90;
            memcpy(&resp.Data[2], get_vin_number(), 17);
            resp.Length = 19;
            break;

        case 0xF1A0:  /* Vehicle Supplier Identifier */
            resp.Data[0] = 0xF1;
            resp.Data[1] = 0xA0;
            memcpy(&resp.Data[2], get_supplier_id(), 10);
            resp.Length = 12;
            break;

        case 0xF18C:  /* ECU Software Version Number */
          resp.Data[0] = 0xF1;
          resp.Data[1] = 0x8C;
          memcpy(&resp.Data[2], get_sw_version(), 14);
          resp.Length = 16;
          break;

      case 0xF191:  /* Vehicle Information */
          resp.Data[0] = 0xF1;
          resp.Data[1] = 0x91;
          memcpy(&resp.Data[2], get_vehicle_info(), 14);
          resp.Length = 16;
          break;

      case 0xF18D:  /* ECU Hardware Version Number */
          resp.Data[0] = 0xF1;
          resp.Data[1] = 0x8D;
          memcpy(&resp.Data[2], get_hw_version(), 14);
          resp.Length = 16;
          break;

      case 0xF1A1:  /* ECU Serial Number */
          resp.Data[0] = 0xF1;
          resp.Data[1] = 0xA1;
          memcpy(&resp.Data[2], get_ecu_serial(), 14);
          resp.Length = 16;
          break;

      case 0xF197:  /* System Supplier Identifier */
          resp.Data[0] = 0xF1;
          resp.Data[1] = 0x97;
          memcpy(&resp.Data[2], get_system_supplier(), 14);
          resp.Length = 16;
          break;

      case 0xF19D:  /* ASAM/ODX File Identification */
          resp.Data[0] = 0xF1;
          resp.Data[1] = 0x9D;
          memcpy(&resp.Data[2], get_odx_file_id(), 14);
          resp.Length = 16;
          break;

      case 0x0003:  /* Engine Oil Level */
          resp.Data[0] = 0x00;
          resp.Data[1] = 0x03;
          resp.Data[2] = get_oil_level_percent();  /* 0-100% */
          resp.Length = 3;
          break;

      case 0x000C:  /* Vehicle Speed */
          resp.Data[0] = 0x00;
          resp.Data[1] = 0x0C;
          uint16_t speed = get_vehicle_speed_kmh();
          resp.Data[2] = (speed >> 8) & 0xFF;
          resp.Data[3] = speed & 0xFF;
          resp.Length = 4;
          break;

      default:
          /* DID not found - return negative response 0x12 (SubFunction Not Supported) */
          resp.Data[0] = 0x7F;
          resp.Data[1] = 0x22;  /* ReadDataByIdentifier response */
          resp.Data[2] = 0x12;  /* SubFunction Not Supported */
          resp.Length = 3;
          break;
    }

    /* Transmit response */
    CanIf_Transmit(TX_PDU_DIAGNOSTIC, &resp);
}

/*
 * UDS Service 0x27: Security Access
 * Implements seed-key authentication with lockout protection
 */
typedef struct {
    uint8_t failed_attempts;
    uint32_t lockout_end_time_ms;
    uint8_t seed[4];
    bool seed_sent;
} SecurityAccess_t;

static SecurityAccess_t g_security_access = {0};

#define MAX_FAILED_ATTEMPTS     3U
#define LOCKOUT_DURATION_MS     60000U  /* 60 second lockout */

void handle_security_access(const uint8_t* request, uint8_t length) {
    CanTpResponse_t resp;

    if (length < 2) {
        send_negative_response(0x12);  /* SubFunction Not Supported */
        return;
    }

    uint8_t sub_function = request[0] & 0x7F;
    bool is_key = (request[0] & 0x80) != 0;

    /* Check lockout status */
    if (g_security_access.failed_attempts >= MAX_FAILED_ATTEMPTS) {
        uint32_t current_time = get_system_time_ms();
        if (current_time < g_security_access.lockout_end_time_ms) {
            /* Still in lockout - return 0x35 (Invalid Key) */
            send_negative_response(0x35);
            return;
        }
        /* Lockout expired - reset */
        g_security_access.failed_attempts = 0;
        g_security_access.lockout_end_time_ms = 0;
        g_security_access.seed_sent = false;
    }

    if (!is_key) {
        /* Send Seed (0x27 0x01, 0x03, 0x05, etc.) */
        if (g_security_access.seed_sent) {
            /* Already sent seed - resend same seed */
            resp.Data[0] = 0x67;
            resp.Data[1] = request[0];
            memcpy(&resp.Data[2], g_security_access.seed, 4);
            resp.Length = 6;
        } else {
            /* Generate new seed */
            generate_random_seed(g_security_access.seed, 4);
            g_security_access.seed_sent = true;

            resp.Data[0] = 0x67;
            resp.Data[1] = request[0];
            memcpy(&resp.Data[2], g_security_access.seed, 4);
            resp.Length = 6;
        }
    } else {
        /* Verify Key */
        if (!g_security_access.seed_sent) {
            /* No seed requested - send negative response 0x24 (Request Sequence Error) */
            send_negative_response(0x24);
            return;
        }

        if (length < 5) {
            /* Key too short */
            send_negative_response(0x12);
            return;
        }

        const uint8_t* received_key = &request[1];
        uint8_t expected_key[4];

        /* Compute expected key (seed XOR with secret, then CRC) */
        compute_expected_key(g_security_access.seed, expected_key);

        /* Constant-time comparison (prevent timing attacks) */
        bool key_valid = true;
        for (uint8_t i = 0; i < 4; i++) {
            if (received_key[i] != expected_key[i]) {
                key_valid = false;
            }
        }

        if (key_valid) {
            /* Key valid - grant security access */
            g_security_access.failed_attempts = 0;
            g_security_access.seed_sent = false;
            set_diagnostic_session(SESSION_PROGRAMMING);

            resp.Data[0] = 0x67;
            resp.Data[1] = request[0];
            resp.Length = 2;
        } else {
            /* Invalid key */
            g_security_access.failed_attempts++;

            if (g_security_access.failed_attempts >= MAX_FAILED_ATTEMPTS) {
                /* Lockout - set lockout timer */
                g_security_access.lockout_end_time_ms = get_system_time_ms() + LOCKOUT_DURATION_MS;
                send_negative_response(0x36);  /* Exceeded Number of Attempts */
                return;
            }

            send_negative_response(0x35);  /* Invalid Key */
            return;
        }
    }

    /* Transmit response */
    CanIf_Transmit(TX_PDU_DIAGNOSTIC, &resp);
}

/*
 * UDS Service 0x31: Routine Control
 * Implements ECU reset, I/O control, and memory checksum routines
 */
typedef enum {
    ROUTINE_ERASE_MEMORY      = 0xFF00,
    ROUTINE_CHECKSUM_MEMORY   = 0xFF01,
    ROUTINE_RESET_ECU         = 0xFF02,
    ROUTINE_IO_CONTROL        = 0xFF03,
    ROUTINE_ACTIVATE_TESTMODE = 0xFF04
} RoutineIdentifier_t;

void handle_routine_control(const uint8_t* request, uint8_t length) {
    CanTpResponse_t resp;

    if (length < 3) {
        send_negative_response(0x12);  /* SubFunction Not Supported */
        return;
    }

    uint8_t sub_function = request[0];
    uint16_t routine_id = (request[1] << 8) | request[2];

    switch (routine_id) {
        case ROUTINE_ERASE_MEMORY:
            if (sub_function != 0x01) {  /* Must be startRoutine */
                send_negative_response(0x12);
                return;
            }
            if (!is_in_programming_session()) {
                send_negative_response(0x7F);  /* Service Not Allowed In Active Session */
                return;
            }
            /* Erase flash memory */
            erase_flash_sector(FLASH_SECTOR_APP);
            resp.Data[0] = 0x71;
            resp.Data[1] = 0x01;
            resp.Data[2] = 0xFF;
            resp.Data[3] = 0x00;
            resp.Length = 4;
            break;

        case ROUTINE_CHECKSUM_MEMORY:
            if (sub_function != 0x01) {
                send_negative_response(0x12);
                return;
            }
            /* Calculate checksum of application memory */
            uint32_t checksum = calculate_crc32(
                (uint8_t*)FLASH_APP_START,
                FLASH_APP_SIZE);
            resp.Data[0] = 0x71;
            resp.Data[1] = 0x01;
            resp.Data[2] = 0xFF;
            resp.Data[3] = 0x01;
            resp.Data[4] = (checksum >> 24) & 0xFF;
            resp.Data[5] = (checksum >> 16) & 0xFF;
            resp.Data[6] = (checksum >> 8) & 0xFF;
            resp.Data[7] = checksum & 0xFF;
            resp.Length = 8;
            break;

        case ROUTINE_RESET_ECU:
            if (sub_function != 0x01) {
                send_negative_response(0x12);
                return;
            }
            /* Schedule ECU reset after response */
            schedule_ecu_reset(RESET_TYPE_HARD);
            resp.Data[0] = 0x71;
            resp.Data[1] = 0x01;
            resp.Data[2] = 0xFF;
            resp.Data[3] = 0x02;
            resp.Length = 4;
            break;

        case ROUTINE_IO_CONTROL:
            if (sub_function != 0x03) {  /* activateIOControl */
                send_negative_response(0x12);
                return;
            }
            /* Activate I/O control for testing */
            activate_io_control_mode(true);
            resp.Data[0] = 0x71;
            resp.Data[1] = 0x03;
            resp.Data[2] = 0xFF;
            resp.Data[3] = 0x03;
            resp.Length = 4;
            break;

        case ROUTINE_ACTIVATE_TESTMODE:
            if (sub_function != 0x01) {
                send_negative_response(0x12);
                return;
            }
            if (!is_security_access_granted()) {
                send_negative_response(0x33);  /* Security Access Denied */
                return;
            }
            activate_test_mode(true);
            resp.Data[0] = 0x71;
            resp.Data[1] = 0x01;
            resp.Data[2] = 0xFF;
            resp.Data[3] = 0x04;
            resp.Length = 4;
            break;

        default:
            send_negative_response(0x31);  /* Request Out Of Range */
            return;
    }

    /* Transmit response */
    CanIf_Transmit(TX_PDU_DIAGNOSTIC, &resp);
}

/*
 * ISO 15765-2: CAN Transport Layer
 * Handles segmentation and reassembly of multi-frame CAN messages
 */
typedef enum {
    PCI_SINGLE_FRAME     = 0x00,
    PCI_FIRST_FRAME      = 0x10,
    PCI_CONSECUTIVE_FRAME = 0x20,
    PCI_FLOW_CONTROL     = 0x30
} CanTpPCIType_t;

typedef enum {
    TP_IDLE,
    TP_RECEIVING_FIRST_FRAME,
    TP_RECEIVING_CONSECUTIVE_FRAMES,
    TP_TRANSMITTING
} CanTpState_t;

typedef struct {
    CanTpState_t state;
    uint16_t total_length;
    uint16_t received_length;
    uint8_t data[4096];  /* Maximum ISO-TP payload */
    uint8_t next_sn;      /* Expected sequence number */
    uint32_t last_frame_time_ms;
    uint32_t timeout_ms;
} CanTpContext_t;

static CanTpContext_t g_tp_rx = {0};
static CanTpContext_t g_tp_tx = {0};

#define TP_TIMEOUT_MS       2000U
#define TP_BS_MAX           8U      /* Block size */
#define TP_ST_MIN_US        0U      /* Separation time minimum */

void handle_can_tp_rx(const CanFrame_t* frame) {
    uint8_t pci = frame->Data[0] & 0xF0;
    uint8_t pci_type = pci >> 4;

    switch (pci_type) {
        case 0:  /* Single Frame */
        {
            uint8_t length = frame->Data[0] & 0x0F;
            if (length > 7) {
                return;  /* Invalid SF length */
            }
            memcpy(g_tp_rx.data, &frame->Data[1], length);
            g_tp_rx.received_length = length;
            g_tp_rx.state = TP_IDLE;

            /* Pass to upper layer */
            can_tp_receive_indication(g_tp_rx.data, g_tp_rx.received_length);
            break;
        }

        case 1:  /* First Frame */
        {
            if (g_tp_rx.state != TP_IDLE) {
                /* Reception already in progress - abort */
                return;
            }

            uint16_t total_length = ((frame->Data[0] & 0x0F) << 8) | frame->Data[1];
            if (total_length > sizeof(g_tp_rx.data)) {
                /* Buffer too small */
                send_flow_control(FC_CLEARED);
                return;
            }

            g_tp_rx.total_length = total_length;
            g_tp_rx.received_length = 6;  /* 6 bytes in FF after PCI */
            g_tp_rx.next_sn = 1;
            memcpy(g_tp_rx.data, &frame->Data[2], 6);
            g_tp_rx.state = TP_RECEIVING_CONSECUTIVE_FRAMES;
            g_tp_rx.last_frame_time_ms = get_system_time_ms();

            /* Send Flow Control */
            send_flow_control(FC_CONTINUE);
            break;
        }

        case 2:  /* Consecutive Frame */
        {
            if (g_tp_rx.state != TP_RECEIVING_CONSECUTIVE_FRAMES) {
                return;  /* Not expecting CF */
            }

            uint8_t sn = frame->Data[0] & 0x0F;
            if (sn != g_tp_rx.next_sn) {
                /* Wrong sequence number - abort */
                g_tp_rx.state = TP_IDLE;
                return;
            }

            /* Copy data */
            uint16_t remaining = g_tp_rx.total_length - g_tp_rx.received_length;
            uint8_t copy_length = (remaining < 7) ? remaining : 7;
            memcpy(&g_tp_rx.data[g_tp_rx.received_length], &frame->Data[1], copy_length);
            g_tp_rx.received_length += copy_length;
            g_tp_rx.next_sn = (g_tp_rx.next_sn + 1) & 0x0F;
            g_tp_rx.last_frame_time_ms = get_system_time_ms();

            /* Check if complete */
            if (g_tp_rx.received_length >= g_tp_rx.total_length) {
                g_tp_rx.state = TP_IDLE;

                /* Pass to upper layer */
                can_tp_receive_indication(g_tp_rx.data, g_tp_rx.received_length);
            }
            break;
        }

        case 3:  /* Flow Control */
        {
            /* Handle FC if we're transmitting */
            if (g_tp_tx.state != TP_TRANSMITTING) {
                return;
            }

            uint8_t fc_status = frame->Data[0] & 0x0F;
            if (fc_status == FC_CONTINUE) {
                /* Continue transmission */
                uint8_t bs = frame->Data[1];
                uint8_t st_min = frame->Data[2];

                transmit_consecutive_frames((bs > 0) ? bs : TP_BS_MAX, st_min);
            } else if (fc_status == FC_WAIT) {
                /* Wait for next FC */
                g_tp_tx.state = TP_RECEIVING_FIRST_FRAME;  /* Pause state */
            } else {
                /* FC_CLEARED - abort */
                g_tp_tx.state = TP_IDLE;
            }
            break;
        }

        default:
            break;
    }
}

void send_flow_control(uint8_t status) {
    CanFrame_t fc_frame;
    fc_frame.Id = 0x7E8;  /* Response ID */
    fc_frame.DLC = 8;
    fc_frame.Data[0] = 0x30 | status;
    fc_frame.Data[1] = TP_BS_MAX;  /* Block Size */
    fc_frame.Data[2] = TP_ST_MIN_US;  /* Separation Time */
    fc_frame.Data[3] = 0x00;
    fc_frame.Data[4] = 0x00;
    fc_frame.Data[5] = 0x00;
    fc_frame.Data[6] = 0x00;
    fc_frame.Data[7] = 0x00;

    CanIf_Transmit(TX_PDU_DIAGNOSTIC_FC, &fc_frame);
}

/*
 * CAN Bus Load Monitoring
 * Monitors bus utilization and alerts when thresholds exceeded
 */
typedef struct {
    uint32_t total_bits;
    uint32_t data_bits;
    uint32_t overhead_bits;
    uint32_t error_bits;
    uint32_t measurement_window_ms;
    uint32_t window_start_ms;
    float load_percent;
    bool warning_70;
    bool alert_80;
} BusLoadMonitor_t;

static BusLoadMonitor_t g_bus_load = {0};

#define BUS_LOAD_WARNING_THRESHOLD    70.0f
#define BUS_LOAD_ALERT_THRESHOLD      80.0f

void can_frame_transmitted(uint16_t frame_bits) {
    uint32_t current_time = get_system_time_ms();

    /* Reset window if expired */
    if ((current_time - g_bus_load.window_start_ms) > g_bus_load.measurement_window_ms) {
        g_bus_load.total_bits = 0;
        g_bus_load.data_bits = 0;
        g_bus_load.overhead_bits = 0;
        g_bus_load.error_bits = 0;
        g_bus_load.window_start_ms = current_time;
        g_bus_load.warning_70 = false;
        g_bus_load.alert_80 = false;
    }

    /* Count bits: 1 start + 11/13 ID + 6 control + data + 15 CRC + 2 ACK + 3 EOF + IFS */
    /* Simplified: 13 (overhead) + data_bits + stuff_bits (approx 20%) */
    uint16_t data_bits = (uint16_t)frame_bits - 13U;
    uint16_t stuff_bits = data_bits / 5;  /* Approximate bit stuffing */

    g_bus_load.total_bits += frame_bits + stuff_bits;
    g_bus_load.data_bits += data_bits;
    g_bus_load.overhead_bits += 13U + stuff_bits;
}

void can_error_frame_detected(uint16_t error_bits) {
    g_bus_load.error_bits += error_bits;
}

float calculate_bus_load_percent(void) {
    uint32_t elapsed_ms = get_system_time_ms() - g_bus_load.window_start_ms;
    if (elapsed_ms == 0) {
        return 0.0f;
    }

    /* Bus speed: 500 kbps = 500 bits/ms */
    float max_bits = (float)elapsed_ms * 500.0f;
    g_bus_load.load_percent = ((float)g_bus_load.total_bits / max_bits) * 100.0f;

    return g_bus_load.load_percent;
}

void check_bus_load_thresholds(void) {
    float load = calculate_bus_load_percent();

    if (load >= BUS_LOAD_ALERT_THRESHOLD) {
        if (!g_bus_load.alert_80) {
            g_bus_load.alert_80 = true;
            g_bus_load.warning_70 = true;
            can_tp_send_error_indication(CAN_TP_ERROR_BUS_OVERLOADED);
            /* Log event */
            log_event(EVENT_BUS_LOAD_ALERT, (uint8_t*)&load, sizeof(float));
        }
    } else if (load >= BUS_LOAD_WARNING_THRESHOLD) {
        if (!g_bus_load.warning_70) {
            g_bus_load.warning_70 = true;
            /* Log warning */
            log_event(EVENT_BUS_LOAD_WARNING, (uint8_t*)&load, sizeof(float));
        }
    } else {
        g_bus_load.warning_70 = false;
        g_bus_load.alert_80 = false;
    }
}

/*
 * Bus Load Calculation Utilities
 */
uint16_t calculate_can_frame_bits_standard(uint8_t dlc) {
    /* Standard CAN 2.0A (11-bit ID):
     * - Start of Frame: 1 bit
     * - Arbitration Field: 11 (ID) + 1 (RTR) + 2 (IDE+r0) = 14 bits
     * - Control Field: 4 bits
     * - Data Field: dlc * 8 bits
     * - CRC Field: 15 (CRC) + 1 (delimiter) = 16 bits
     * - ACK Field: 2 bits
     * - End of Frame: 7 bits
     * - Inter Frame Space: 3 bits
     * Total: 1 + 14 + 4 + (dlc*8) + 16 + 2 + 7 + 3 = 47 + (dlc*8)
     */
    return 47U + (dlc * 8U);
}

uint16_t calculate_can_frame_bits_extended(uint8_t dlc) {
    /* Extended CAN 2.0B (29-bit ID):
     * Same as standard but with 18 additional ID bits + 2 substitute bits
     * Total: 67 + (dlc*8)
     */
    return 67U + (dlc * 8U);
}

uint16_t calculate_can_fd_frame_bits(uint8_t dlc) {
    /* CAN FD frame with 11-bit ID, 500 kbps arb, 2 Mbps data:
     * Approximate calculation (data portion is 4x faster)
     */
    uint16_t arb_bits = 50U;  /* Arbitration phase at 500 kbps */
    uint16_t data_bits = dlc * 2U;  /* Equivalent 500kbps bits (4x speed) */
    return arb_bits + data_bits;
}

/*
 * Related Context
 * - @context/skills/autosar/classic-platform.md — AUTOSAR Classic CAN stack configuration
 * - @context/skills/security/iso-21434-compliance.md — SecOC message authentication
 * - @context/skills/safety/iso-26262-overview.md — ASIL classification for CAN signals
 * - @context/skills/network/ethernet-communication.md — CAN-to-Ethernet gateway patterns
 * - @context/skills/adas/adaptive-cruise-control.md — CAN signal usage in ADAS
 * - @context/skills/diagnostics/uds-diagnostic-services.md — UDS over CAN (ISO 15765-2)
 *
 * Approach
 *
 * 1. Define network topology and signal matrix
 *    - Identify ECUs and their CAN connections
 *    - Define message IDs, signals, and timing
 *    - Create DBC file with complete signal definitions
 *
 * 2. Configure AUTOSAR CAN stack
 *    - Configure Can Controller (baud rate, sample point)
 *    - Configure Can Hardware Object (TX/RX, ID masks)
 *    - Configure CanIf (PDU routing, notification)
 *    - Configure PduR (gateway routing if needed)
 *
 * 3. Implement application layer
 *    - Create signal packing/unpacking functions
 *    - Implement periodic message transmission
 *    - Handle received signals with appropriate actions
 *
 * 4. Integrate diagnostics
 *    - Configure ISO 15765-2 transport layer
 *    - Implement UDS service handlers
 *    - Configure security access and programming sessions
 *
 * 5. Validate and verify
 *    - Monitor bus with CAN analyzer (vector canoe)
 *    - Verify timing and bus load
 *    - Test diagnostics with client tool
 *
 * Deliverables
 *
 * - DBC file (message and signal definitions)
 * - ARXML configuration (AUTOSAR stack)
 * - CAN driver implementation (if custom)
 * - Application signal handlers
 * - Diagnostic service implementations
 * - ISO 15765-2 transport layer
 * - Bus load monitoring utilities
 * - Test validation report
 * - Integration guide
 *
 * Tools Required
 *
 * - Vector CANoe / CANalyzer (bus monitoring)
 * - Vector CANdb++ (DBC editing)
 * - Vector DaVinci Configurator (AUTOSAR config)
 * - PEAK PCAN-View / CANalyzer (open source alternative)
 * - Intrepid Vehicle Spy 3 (diagnostics)
 * - Oscilloscope (physical layer validation)
 * - dSPACE / ETAS HIL systems (ECU testing)
 * - CAN stress / error injection tester
 * - EMC chamber (EMI/EMC testing)
 * - Logic analyzer (SPI debugging)
 */