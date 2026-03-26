---
name: diagnostics-uds
description: "Use when: Skill: UDS (Unified Diagnostic Services) - ISO 14229-1 topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: UDS (Unified Diagnostic Services) - ISO 14229-1

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/diagnostics/uds.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate
- User asks about UDS service implementation or diagnostic communication
- User needs to implement diagnostic client/server for ECU flashing, calibration, or diagnostics
- User requests triggering UDS services (0x10, 0x11, 0x22, 0x27, 0x2E, 0x31, 0x34/0x36/0x37)
- User is configuring AUTOSAR Dcm module or implementing diagnostic gateway
- User needs guidance on UDS timing management, session handling, or security access

## Standards Compliance
- ISO 14229-1:2020 (UDS) - Unified Diagnostic Services
- ISO 15765-2:2016 (UDS on CAN) - Transport layer for CAN networks
- ISO 13400:2019 (DoIP) - Diagnostic over IP (Ethernet transport)
- AUTOSAR 4.4 - Dcm (Diagnostic Communication Manager) module
- ISO 26262-6 - ASIL classification for diagnostic functions
- ISO 21434 - Cybersecurity for diagnostic access protection
- SAE J1979 - OBD-II scan tool requirements (emissions-related)
- UN ECE R155 - Cybersecurity management for diagnostic interfaces

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Session types | 0x01 (Default), 0x02 (Programming), 0x03 (Extended) | enumeration |
| Security access levels | Level 1/2/3 (0x01/0x03/0x05 request seed) | enumeration |
| P2Server timeout | 50 (typical) | ms |
| P2*Server timeout | 5000 (extended operations) | ms |
| S3Server timeout | 5000 (session keep-alive) | ms |
| DID range | 0x0000-0xFFFF | identifier |
| Max block length (download) | Per ECU capability (from 0x34 response) | bytes |
| TransferData counter | 0x01-0xFF (wraps to 0x00) | sequence |

## UDS Protocol Architecture

```
+----------------------------------------------------------+
|                    Application Layer                      |
|  +------------------+  +------------------+              |
|  |  Diagnostic      |  |  OEM-Specific    |              |
|  |  Client (Tester) |  |  Services          |              |
|  +------------------+  +------------------+              |
|           |                                             |
+-----------|---------------------------------------------+
            |
+-----------v---------------------------------------------+
|                    UDS Layer (ISO 14229-1)              |
|  Services:                                              |
|  - Diagnostic Management: 0x10, 0x11, 0x27, 0x28, 0x3E, 0x85 |
|  - Data Transmission:   0x22, 0x23, 0x24, 0x2E, 0x3D   |
|  - Stored Data:         0x14, 0x19 (DTC handling)      |
|  - I/O Control:         0x2F                            |
|  - Routine Execution:   0x31                            |
|  - Upload/Download:     0x34, 0x35, 0x36, 0x37, 0x38   |
+-----------|---------------------------------------------+
            |
+-----------v---------------------------------------------+
|                    Transport Layer                       |
|  +------------------+  +------------------+            |
|  |  ISO 15765-2     |  |  ISO 13400       |            |
|  |  (UDS over CAN)  |  |  (DoIP/Ethernet) |            |
|  +------------------+  +------------------+            |
+-----------|---------------------------------------------+
            |
+-----------v---------------------------------------------+
|                    Network Layer                         |
|  +------------------+  +------------------+            |
|  |  CAN (11/29 bit) |  |  Ethernet (TCP)  |            |
|  +------------------+  +------------------+            |
+----------------------------------------------------------+
```

## UDS Message Format

### Request/Response Pattern

```
Positive Request:     [SID] [Sub-function] [Data bytes...]
                      Example: [0x22] [0xF1] [0x90] (Read VIN DID 0xF190)

Positive Response:    [SID + 0x40] [Echo sub-function] [Data bytes...]
                      Example: [0x62] [0xF1] [0x90] [VIN data...]

Negative Response:    [0x7F] [SID] [NRC]
                      Example: [0x7F] [0x22] [0x31] (Request out of range)
```

### Common Negative Response Codes (NRC)

| NRC | Name | Description |
|-----|------|-------------|
| 0x10 | generalProgrammingFailure | Generic error |
| 0x11 | serviceNotSupported | SID not implemented |
| 0x12 | subFunctionNotSupported | Sub-function not implemented |
| 0x13 | incorrectMessageLengthOrInvalidFormat | Wrong message size |
| 0x21 | busyRepeatRequest | ECU busy, retry later |
| 0x22 | conditionsNotCorrect | Pre-conditions not met |
| 0x31 | requestOutOfRange | Parameter out of range |
| 0x33 | securityAccessDenied | Security not unlocked |
| 0x35 | invalidKey | Wrong security key |
| 0x36 | exceededNumberOfAttempts | Max attempts exceeded |
| 0x37 | requiredTimeDelayNotExpired | Login timer active |
| 0x78 | responsePending | ECU needs more time (extend P2 to P2*) |
| 0x83 | serviceNotSupportedInActiveSession | Session mismatch |

## Session and Security State Machine

```
+------------------+   0x10(0x01)    +------------------+
|   Default        |◄───────────────│  Extended        |
|   Session        |────────────────│  Session         |
|   (0x01)         |   0x10(0x03)   |  (0x03)          |
+--------+---------+                +--------+---------+
         | 0x10(0x02)                        | 0x10(0x02)
         v                                   v
+------------------+                +------------------+
| Programming      |                | Programming      |
| Session          |                | Session          |
| (0x02)           |                | (0x02)           |
+------------------+                +------------------+

Security Access Levels:
Level 1 (0x01/0x02): Basic diagnostic access
Level 2 (0x03/0x04): Extended access (calibration)
Level 3 (0x05/0x06): Programming access (flash)
```

### Session Types

| Session | ID | Use Case | Timing |
|---------|----|----------|--------|
| Default | 0x01 | Normal driving, basic diagnostics | S3 timeout active |
| Programming | 0x02 | Flash reprogramming, parameter coding | Extended P2* allowed |
| Extended | 0x03 | Advanced diagnostics, I/O control, routines | OEM-specific features |

### Security Access Sequence

```
Step 1: Request Seed (odd sub-function)
  Tester → ECU: [0x27] [0x03]  (Request Level 2 seed)
  ECU → Tester: [0x67] [0x03] [Seed byte 1] [Seed byte 2] ...

Step 2: Send Key (even sub-function)
  Tester → ECU: [0x27] [0x04] [Key byte 1] [Key byte 2] ...
  ECU → Tester: [0x67] [0x04]  (Positive = unlocked)
                  or
              [0x7F] [0x27] [0x35] (Negative = invalid key)

Step 3: Access granted until session ends or 0x27(0x02) logout
```

## Timing Management

### UDS Timing Parameters

| Parameter | Description | Typical Value | Source |
|-----------|-------------|---------------|--------|
| P2Client | Tester inter-request gap | 50 ms | ISO 14229 |
| P2Server | ECU response timeout | 50 ms | ECU config |
| P2*Server | Extended timeout (after 0x78) | 5000 ms | ECU config |
| S3Server | Session timeout (needs 0x3E) | 5000 ms | ISO 14229 |

### Timing Implementation Pattern

```c
/* UDS client timing state machine */
typedef struct {
    uint32_t p2_timeout_ms;
    uint32_t p2star_timeout_ms;
    uint32_t s3_timeout_ms;
    uint32_t last_response_time_ms;
    bool waiting_for_response;
} UdsTiming_t;

typedef enum {
    UDS_SUCCESS,
    UDS_TIMEOUT_P2,
    UDS_RESPONSE_PENDING,
    UDS_NEGATIVE_RESPONSE,
    UDS_INVALID_FORMAT
} UdsResult_t;

UdsResult_t send_uds_request(
    const uint8_t* request,
    size_t request_len,
    uint8_t* response,
    size_t* response_len,
    UdsTiming_t* timing)
{
    /* Send request over transport layer (CAN/DoIP) */
    transport_send(request, request_len);
    timing->waiting_for_response = true;
    timing->last_response_time_ms = get_time_ms();

    while (timing->waiting_for_response) {
        /* Wait for response with P2 timeout */
        uint32_t elapsed = get_time_ms() - timing->last_response_time_ms;
        if (elapsed > timing->p2_timeout_ms) {
            return UDS_TIMEOUT_P2;
        }

        /* Check for response */
        if (transport_receive(response, response_len, 10)) {
            if (response[0] == 0x7F) {
                /* Negative response */
                if (response[2] == 0x78) {
                    /* ResponsePending - extend timeout to P2* */
                    timing->p2_timeout_ms = timing->p2star_timeout_ms;
                    timing->last_response_time_ms = get_time_ms();
                    continue;  /* Keep waiting */
                }
                return UDS_NEGATIVE_RESPONSE;
            }
            if (response[0] == (request[0] | 0x40)) {
                /* Positive response (SID + 0x40) */
                return UDS_SUCCESS;
            }
            return UDS_INVALID_FORMAT;
        }
    }
    return UDS_TIMEOUT_P2;
}
```

## Data Identifier (DID) Ranges

| DID Range | Assigned To | Examples |
|-----------|-------------|----------|
| 0x0000-0x00FF | ISO 14229 reserved | - |
| 0x0100-0xA5FF | OEM-specific | Vehicle parameters, calibration |
| 0xA600-0xA7FF | Reserved | - |
| 0xA800-0xACFF | Reserved | - |
| 0xF000-0xF0FF | Network configuration | Gateway config, subnet params |
| 0xF100-0xF1FF | Identification | VIN (0xF190), Serial (0xF18C), SW version (0xF1A2) |
| 0xF200-0xF2FF | Periodic DIDs | High-speed sensor data streaming |
| 0xF300-0xF3FF | Dynamically defined DIDs | Custom composite data |
| 0xF400-0xF4FF | OEM safety-related | ASIL-relevant parameters |
| 0xF500-0xF5FF | OEM powertrain | Engine, transmission params |
| 0xF600-0xF6FF | OEM chassis | Brake, steering params |
| 0xF700-0xF7FF | OEM body | Comfort, HVAC params |

### Example DID Definitions

```yaml
# OEM DID catalog (YAML configuration)
dids:
  - id: 0xF190
    name: VehicleIdentificationNumber
    data_type: string_ascii
    length: 17
    access: read_only
    session: [default, extended, programming]
    security: none
    description: "17-character VIN per ISO 3779"

  - id: 0xF18C
    name: EcuSerialNumber
    data_type: string_ascii
    length: 20
    access: read_only
    session: [default, extended, programming]
    security: none

  - id: 0xF1A2
    name: SoftwareVersion
    data_type: string_ascii
    length: 50
    access: read_only
    session: [default, extended, programming]
    security: none

  - id: 0xF1B8
    name: CalibrationData
    data_type: binary
    length: variable
    access: read_write
    session: [programming]
    security: level_2
    description: "Calibration parameters for engine tuning"
```

## Flash Programming Sequence (0x34/0x36/0x37)

### Download Flow

```
+-----------+     +-----------+     +-----------+     +-----------+
| 0x10(0x02)| --> | 0x27(0x05)| --> | 0x34      | --> | 0x36 (Nx) |
| Programming|     | Seed/Key  |     | Request   |     | Transfer  |
| Session   |     | Unlock    |     | Download  |     | Data      |
+-----------+     +-----------+     +-----------+     +-----------+
                                                              |
                                                              v
+-----------+     +-----------+     +-----------+     +-----------+
| 0x11(0x01)| <-- | 0x10(0x01)| <-- | 0x37      | <-- | 0x36 (N)  |
| ECU Reset |     | Default   |     | Transfer  |     | Last Block|
| (Reboot)  |     | Session   |     | Exit      |     |           |
+-----------+     +-----------+     +-----------+     +-----------+
```

### Flash Programming Implementation

```c
/* Flash download state machine */
typedef struct {
    uint32_t memory_address;
    uint32_t data_size;
    uint16_t max_block_length;
    uint8_t block_sequence;
    uint32_t bytes_transferred;
    bool download_active;
} FlashDownloadState_t;

UdsResult_t request_download(
    FlashDownloadState_t* state,
    uint8_t* response,
    size_t* response_len)
{
    /* 0x34 RequestDownload message */
    uint8_t request[11];
    request[0] = 0x34;  /* SID */
    request[1] = 0x00;  /* Data format: no compression, no encryption */
    /* Address and length format: 3 bytes address, 3 bytes length */
    request[2] = 0x44;  /* addr_len=3, mem_len=3 */
    /* Memory address (big-endian) */
    request[3] = (state->memory_address >> 16) & 0xFF;
    request[4] = (state->memory_address >> 8) & 0xFF;
    request[5] = state->memory_address & 0xFF;
    /* Uncompressed data size (big-endian) */
    request[6] = (state->data_size >> 16) & 0xFF;
    request[7] = (state->data_size >> 8) & 0xFF;
    request[8] = state->data_size & 0xFF;

    UdsResult_t result = send_uds_request(request, 9, response, response_len,
                                           &g_timing);
    if (result != UDS_SUCCESS) {
        return result;
    }

    /* Parse max block length from response */
    /* Response: [0x74] [addr_len_format] [max_block_length] */
    if (*response_len >= 3) {
        state->max_block_length = (response[1] << 8) | response[2];
    }
    state->download_active = true;
    state->block_sequence = 1;
    state->bytes_transferred = 0;

    return UDS_SUCCESS;
}

UdsResult_t transfer_data_block(
    FlashDownloadState_t* state,
    const uint8_t* data,
    size_t data_len,
    uint8_t* response,
    size_t* response_len)
{
    if (!state->download_active) {
        return UDS_NEGATIVE_RESPONSE;  /* Download not initiated */
    }

    /* 0x36 TransferData message */
    uint8_t request[1 + 1 + 255];  /* SID + counter + data */
    size_t req_len = 2 + data_len;
    request[0] = 0x36;  /* SID */
    request[1] = state->block_sequence;  /* Counter (1-255, wraps to 0) */
    memcpy(&request[2], data, data_len);

    UdsResult_t result = send_uds_request(request, req_len, response,
                                           response_len, &g_timing);
    if (result != UDS_SUCCESS) {
        return result;
    }

    /* Verify response counter matches */
    if (response[1] != state->block_sequence) {
        return UDS_INVALID_FORMAT;
    }

    /* Update state */
    state->bytes_transferred += data_len;
    state->block_sequence++;
    if (state->block_sequence == 0) {
        state->block_sequence = 1;  /* Wrap after 0xFF */
    }

    return UDS_SUCCESS;
}

UdsResult_t request_transfer_exit(
    FlashDownloadState_t* state,
    uint8_t* response,
    size_t* response_len)
{
    if (!state->download_active) {
        return UDS_NEGATIVE_RESPONSE;
    }

    /* 0x37 RequestTransferExit message */
    uint8_t request[1];
    request[0] = 0x37;  /* SID */

    UdsResult_t result = send_uds_request(request, 1, response, response_len,
                                           &g_timing);

    if (result == UDS_SUCCESS) {
        state->download_active = false;
    }
    return result;
}
```

## Key UDS Services Reference

### Diagnostic Management Services

| SID | Service | Sub-functions | Description |
|-----|---------|---------------|-------------|
| 0x10 | DiagnosticSessionControl | 0x01 Default, 0x02 Programming, 0x03 Extended | Switch diagnostic session |
| 0x11 | ECUReset | 0x01 Hard, 0x02 Key-Off-On, 0x03 Soft, 0x04 Enable Rapid Power | Reset ECU |
| 0x27 | SecurityAccess | 0x01/0x02 L1, 0x03/0x04 L2, 0x05/0x06 L3 | Unlock protected services |
| 0x28 | CommunicationControl | 0x00 Enable, 0x01 Disable TX | Control ECU communication |
| 0x3E | TesterPresent | 0x00 Keep session alive | Prevent S3 timeout |
| 0x85 | ControlDTCSetting | 0x01 On, 0x02 Off | Enable/disable DTC storage |

### Data Transmission Services

| SID | Service | Description |
|-----|---------|-------------|
| 0x22 | ReadDataByIdentifier | Read calibration, configuration, sensor data |
| 0x23 | ReadMemoryByAddress | Read arbitrary memory (requires security) |
| 0x24 | ReadScalingDataByIdentifier | Read scaling factors for DID values |
| 0x2E | WriteDataByIdentifier | Write calibration, configuration |
| 0x3D | WriteMemoryByAddress | Write arbitrary memory (requires security) |

### Stored Data Services (DTC)

| SID | Service | Sub-function | Description |
|-----|---------|--------------|-------------|
| 0x14 | ClearDiagnosticInformation | DTC group (0xFFFFFF = all) | Clear fault codes |
| 0x19 | ReadDTCInformation | 0x02 ByStatusMask, 0x0A Supported, 0x1C Readiness | Query fault codes |

### I/O Control and Routines

| SID | Service | Description |
|-----|---------|-------------|
| 0x2F | InputOutputControlByIdentifier | Override sensor inputs, actuator outputs |
| 0x31 | RoutineControl | 0x01 Start, 0x02 Stop, 0x03 Request Results |

## C Code Patterns for UDS Client

### UDS Client State Machine

```c
/* UDS client main structure */
typedef struct {
    UdsTiming_t timing;
    FlashDownloadState_t flash_state;
    uint8_t current_session;
    bool security_unlocked[4];  /* Levels 1-3 */
    uint32_t last_tester_present_ms;
} UdsClient_t;

/* High-level API for common operations */
typedef struct {
    uint16_t did;
    uint8_t* data;
    size_t data_len;
} DidReadRequest_t;

UdsResult_t uds_read_did(UdsClient_t* client,
                          uint16_t did,
                          uint8_t* out_data,
                          size_t* out_len)
{
    uint8_t request[4];
    request[0] = 0x22;  /* SID */
    request[1] = (did >> 8) & 0xFF;
    request[2] = did & 0xFF;

    uint8_t response[260];
    size_t response_len = sizeof(response);

    UdsResult_t result = send_uds_request(request, 3, response,
                                           &response_len, &client->timing);
    if (result != UDS_SUCCESS) {
        return result;
    }

    /* Parse response: [0x62] [DID high] [DID low] [data...] */
    if (response_len < 4) {
        return UDS_INVALID_FORMAT;
    }
    if (response[1] != (did >> 8) & 0xFF ||
        response[2] != (did & 0xFF)) {
        return UDS_INVALID_FORMAT;
    }

    *out_len = response_len - 3;
    memcpy(out_data, &response[3], *out_len);
    return UDS_SUCCESS;
}

UdsResult_t uds_write_did(UdsClient_t* client,
                           uint16_t did,
                           const uint8_t* data,
                           size_t data_len)
{
    uint8_t request[4 + 255];
    request[0] = 0x2E;  /* SID */
    request[1] = (did >> 8) & 0xFF;
    request[2] = did & 0xFF;
    memcpy(&request[3], data, data_len);

    uint8_t response[3];
    size_t response_len = sizeof(response);

    return send_uds_request(request, 3 + data_len, response,
                             &response_len, &client->timing);
}

/* Background task: keep session alive */
void uds_background_task(UdsClient_t* client)
{
    uint32_t now = get_time_ms();
    if ((now - client->last_tester_present_ms) >
        (client->timing.s3_timeout_ms - 1000U)) {
        /* Send TesterPresent to keep session alive */
        uint8_t request[2] = {0x3E, 0x00};
        uint8_t response[2];
        size_t response_len = sizeof(response);
        send_uds_request(request, 2, response, &response_len,
                         &client->timing);
        client->last_tester_present_ms = now;
    }
}
```

### Session and Security Helper Functions

```c
UdsResult_t uds_change_session(UdsClient_t* client, uint8_t session_type)
{
    uint8_t request[2] = {0x10, session_type};
    uint8_t response[8];
    size_t response_len = sizeof(response);

    UdsResult_t result = send_uds_request(request, 2, response,
                                           &response_len, &client->timing);
    if (result == UDS_SUCCESS) {
        client->current_session = session_type;
    }
    return result;
}

UdsResult_t uds_security_access(UdsClient_t* client,
                                 uint8_t level,  /* 1, 2, or 3 */
                                 const uint8_t (*key_algorithm)(const uint8_t*, size_t))
{
    if (level < 1 || level > 3) {
        return UDS_NEGATIVE_RESPONSE;
    }
    if (client->security_unlocked[level]) {
        return UDS_SUCCESS;  /* Already unlocked */
    }

    /* Step 1: Request seed */
    uint8_t seed_request[2] = {0x27, (uint8_t)(level * 2 - 1)};
    uint8_t response[10];
    size_t response_len = sizeof(response);

    UdsResult_t result = send_uds_request(seed_request, 2, response,
                                           &response_len, &client->timing);
    if (result != UDS_SUCCESS) {
        return result;
    }

    /* Extract seed from response [0x67] [sub-function] [seed...] */
    if (response_len < 3) {
        return UDS_INVALID_FORMAT;
    }
    const uint8_t* seed = &response[2];
    size_t seed_len = response_len - 2;

    /* Step 2: Compute key using algorithm */
    uint8_t key[32];
    size_t key_len = key_algorithm(seed, seed_len);

    /* Step 3: Send key */
    uint8_t key_request[2 + 32] = {0x27, (uint8_t)(level * 2)};
    memcpy(&key_request[2], key, key_len);

    uint8_t key_response[2];
    size_t key_response_len = sizeof(key_response);

    result = send_uds_request(key_request, 2 + key_len, key_response,
                               &key_response_len, &client->timing);
    if (result == UDS_SUCCESS) {
        client->security_unlocked[level] = true;
    }
    return result;
}
```

## AUTOSAR Dcm Configuration

### Dcm Module Setup (ARXML)

```xml
<!-- AUTOSAR Dcm Configuration for UDS -->
<ECUC-MODULE-CONFIGURATION-VALUES>
  <SHORT-NAME>Dcm_Config</SHORT-NAME>
  <DEFINITION-REF DEST="ECUC-MODULE-DEFINITION">/Dcm</DEFINITION-REF>

  <!-- UDS Services Enabled -->
  <PARAMETER-VALUES>
    <ECUC-TEXTUAL-PARAMETER-VALUE>
      <DEFINITION-REF DEST="PARAMETER-DEFINITION">
        /Dcm/DcmConfiguration/DcmSupportUdsServices
      </DEFINITION-REF>
      <VALUE>true</VALUE>
    </ECUC-TEXTUAL-PARAMETER-VALUE>
    <ECUC-TEXTUAL-PARAMETER-VALUE>
      <DEFINITION-REF DEST="PARAMETER-DEFINITION">
        /Dcm/DcmConfiguration/DcmSupportP2Star
      </DEFINITION-REF>
      <VALUE>true</VALUE>
    </ECUC-TEXTUAL-PARAMETER-VALUE>
  </PARAMETER-VALUES>

  <!-- Session Configuration -->
  <SUB-CONFIGURATIONS>
    <ECUC-SUB-CONFIGURATION-VALUE>
      <SHORT-NAME>DcmSession_Default</SHORT-NAME>
      <DEFINITION-REF DEST="ECUC-PARAM-CONFIG-CONTAINER-DEF">
        /Dcm/DcmSession
      </DEFINITION-REF>
      <PARAMETER-VALUES>
        <ECUC-NUMERICAL-PARAMETER-VALUE>
          <DEFINITION-REF DEST="PARAMETER-DEFINITION">
            /Dcm/DcmSession/DcmSessionId
          </DEFINITION-REF>
          <VALUE>1</VALUE>  <!-- 0x01 Default -->
        </ECUC-NUMERICAL-PARAMETER-VALUE>
        <ECUC-NUMERICAL-PARAMETER-VALUE>
          <DEFINITION-REF DEST="PARAMETER-DEFINITION">
            /Dcm/DcmSession/DcmS3ClientTime
          </DEFINITION-REF>
          <VALUE>5000</VALUE>  <!-- 5 seconds -->
        </ECUC-NUMERICAL-PARAMETER-VALUE>
      </PARAMETER-VALUES>
    </ECUC-SUB-CONFIGURATION-VALUE>

    <!-- Security Access Configuration -->
    <ECUC-SUB-CONFIGURATION-VALUE>
      <SHORT-NAME>DcmSecurity_Level1</SHORT-NAME>
      <DEFINITION-REF DEST="ECUC-PARAM-CONFIG-CONTAINER-DEF">
        /Dcm/DcmSecurityLevel
      </DEFINITION-REF>
      <PARAMETER-VALUES>
        <ECUC-NUMERICAL-PARAMETER-VALUE>
          <DEFINITION-REF DEST="PARAMETER-DEFINITION">
            /Dcm/DcmSecurityLevel/DcmSecurityLevelId
          </DEFINITION-REF>
          <VALUE>1</VALUE>
        </ECUC-NUMERICAL-PARAMETER-VALUE>
        <ECUC-NUMERICAL-PARAMETER-VALUE>
          <DEFINITION-REF DEST="PARAMETER-DEFINITION">
            /Dcm/DcmSecurityLevel/DcmSecurityLevelDelayTimerOnBoot
          </DEFINITION-REF>
          <VALUE>10000</VALUE>  <!-- 10 second delay after boot -->
        </ECUC-NUMERICAL-PARAMETER-VALUE>
      </PARAMETER-VALUES>
    </ECUC-SUB-CONFIGURATION-VALUE>

    <!-- DID Configuration -->
    <ECUC-SUB-CONFIGURATION-VALUE>
      <SHORT-NAME>DcmDspData_DID_F190</SHORT-NAME>
      <DEFINITION-REF DEST="ECUC-PARAM-CONFIG-CONTAINER-DEF">
        /Dcm/DcmDspData
      </DEFINITION-REF>
      <PARAMETER-VALUES>
        <ECUC-NUMERICAL-PARAMETER-VALUE>
          <DEFINITION-REF DEST="PARAMETER-DEFINITION">
            /Dcm/DcmDspData/DcmDspDataDidNumber
          </DEFINITION-REF>
          <VALUE>0xF190</VALUE>
        </ECUC-NUMERICAL-PARAMETER-VALUE>
        <ECUC-NUMERICAL-PARAMETER-VALUE>
          <DEFINITION-REF DEST="PARAMETER-DEFINITION">
            /Dcm/DcmDspData/DcmDspDataSize
          </DEFINITION-REF>
          <VALUE>17</VALUE>
        </ECUC-NUMERICAL-PARAMETER-VALUE>
        <ECUC-TEXTUAL-PARAMETER-VALUE>
          <DEFINITION-REF DEST="PARAMETER-DEFINITION">
            /Dcm/DcmDspData/DcmDspDataReadData
          </DEFINITION-REF>
          <VALUE>Rte_Read_VIN_Data</VALUE>  <!-- RTE callout -->
        </ECUC-TEXTUAL-PARAMETER-VALUE>
      </PARAMETER-VALUES>
    </ECUC-SUB-CONFIGURATION-VALUE>
  </SUB-CONFIGURATIONS>
</ECUC-MODULE-CONFIGURATION-VALUES>
```

## Related Context
- @context/skills/diagnostics/doip.md - DoIP transport layer for UDS over Ethernet
- @context/skills/diagnostics/dtc-management.md - DTC handling with Dem module
- @context/skills/autosar/classic-platform.md - AUTOSAR Classic Dcm configuration
- @context/skills/security/iso-21434-compliance.md - Diagnostic cybersecurity
- @context/skills/network/can-protocol.md - UDS over CAN transport

## Tools Required
- Vector CANoe/CANalyzer (UDS testing)
- Peak-System PCAN-View (CAN bus monitoring)
- Wireshark (DoIP traffic analysis)
- UDS client libraries (python-udsoncan, C# UDS toolkit)
- AUTOSAR configurators (DaVinci Configurator, EB Tresos)

## Testing and Validation
- Verify all UDS services with positive and negative test cases
- Test timing: P2 timeout, P2* extension, S3 session timeout
- Validate security access with correct and incorrect keys
- Test flash programming sequence end-to-end with power loss recovery
- Verify DTC setting control (0x85) prevents DTC storage when disabled