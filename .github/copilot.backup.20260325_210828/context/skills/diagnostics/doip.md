# Skill: Diagnostic over IP (DoIP) - ISO 13400

## When to Activate
- User asks about Diagnostic over IP implementation or ISO 13400 compliance
- User needs to configure Ethernet-based diagnostic sessions
- User requests DoIP vehicle discovery or routing activation procedures
- User is designing diagnostic gateways for central E/E architectures
- User needs TLS security for diagnostic communications
- User requests integration of UDS over DoIP transport

## Standards Compliance
- ISO 13400-1:2021 (DoIP - General information and use case definition)
- ISO 13400-2:2019 (DoIP - Conformance and test cases)
- ISO 14229-1:2020 (UDS - Unified Diagnostic Services)
- ISO 26262:2018 (Functional Safety) - ASIL B for diagnostic access
- ISO 21434:2021 (Cybersecurity) - TLS 1.2/1.3 for secure sessions
- AUTOSAR 4.4 - DoIP module configuration
- SAE J2534-2 - Pass-thru device over DoIP

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| DoIP TCP port | 13400 (plaintext), 3496 (TLS) | port |
| Vehicle discovery interval | 500-5000 | ms |
| Routing activation timeout | 2000 | ms |
| Alive check interval | 500 | ms |
| Max TCP payload size | 1024-8192 | bytes |
| Diagnostic session timeout | 10000 | ms |
| VLAN ID (optional) | 0-4095 | enumeration |

## DoIP Protocol Architecture

```
+------------------+                    +------------------+
|  Diagnostic      |                    |  Vehicle         |
|  Tester          |                    |  Gateway ECU     |
|  (Off-board)     |                    |  (DoIP Entity)   |
+--------+---------+                    +--------+---------+
         |                                       |
         |  1. Vehicle Discovery (UDP)           |
         |<------------------------------------->|
         |     - Broadcast 0x0001 Request        |
         |     - Unicast 0x0004 Announcement     |
         |                                       |
         |  2. TCP Connection Setup              |
         |-------------------------------------->|
         |     - Port 13400 (plaintext)          |
         |     - Port 3496 (TLS-secured)         |
         |                                       |
         |  3. Routing Activation                |
         |-------------------------------------->|
         |     - 0x0005 Request (with VIN/EID)   |
         |     - 0x0006 Response (status code)   |
         |<--------------------------------------|
         |                                       |
         |  4. Diagnostic Messaging (UDS/DoIP)   |
         |<------------------------------------->|
         |     - 0x8001 Diagnostic Message       |
         |     - UDS payload wrapped in DoIP     |
         |                                       |
         |  5. Alive Monitoring                  |
         |<------------------------------------->|
         |     - 0x8007 Alive Check Request      |
         |     - 0x8008 Entity Status Response   |
         |                                       |
         +---------------------------------------+
                          |
                          v
               +----------+----------+
               |   Internal CAN/FlexRay      |
               |   - Forward UDS to ECUs     |
               |   - Gateway routing         |
               +-----------------------------+
```

## DoIP Connection Sequence

```
Diagnostic Tester                    Vehicle Gateway
       |                                  |
       |--- UDP 0x0001 (Broadcast) ------>|  Vehicle ID Request
       |<-- UDP 0x0004 (Announce) --------|  Vehicle Announcement
       |                                  |  (Contains: VIN, Logical Address, EID, GID)
       |                                  |
       |--- TCP SYN --------------------->|  Connect to 13400/3496
       |<-- TCP ACK ----------------------|  Connection established
       |                                  |
       |--- 0x0005 Routing Activation --->|  Request with:
       |                                  |    - Source: 0x0E00 (Tester)
       |                                  |    - Target: 0x0000 (External Node)
       |                                  |    - VIN/EID (optional)
       |<-- 0x0006 Routing Response ------|  Response with:
       |                                  |    - Code: 0x10 (Activated)
       |                                  |    - Logical Address: 0x1000
       |                                  |
       |=== Diagnostic Session Active ===|
       |                                  |
       |--- 0x8001 Diagnostic Message --->|  UDS Service: 0x10 01
       |                                  |  (Start Diagnostic Session)
       |<-- 0x8001 Diagnostic Message ----|  UDS Response: 0x50 01
       |                                  |
       |--- 0x8001 Diagnostic Message --->|  UDS Service: 0x22 F1 90
       |                                  |  (Read VIN by DID)
       |<-- 0x8001 Diagnostic Message ----|  UDS Response: 0x62 F1 90 <VIN>
       |                                  |
       |--- 0x8007 Alive Check ---------->|  Periodic health check
       |<-- 0x8008 Entity Status ---------|  Node type, status info
```

## DoIP Message Format

```
DoIP Header (8 bytes fixed)
+----------------+----------------+----------------+----------------+
| Byte 0         | Byte 1         | Byte 2-3       | Byte 4-7       |
| Protocol       | Inverse        | Payload Type   | Payload Length |
| Version        | Protocol       |                |                |
| (0x02)         | (0xFD)         |                |                |
+----------------+----------------+----------------+----------------+

DoIP Payload (variable)
+----------------+----------------+----------------+----------------+
| Byte 0-1       | Byte 2-N       |
| Header Field   | Payload Data   |
| (optional)     | (variable)     |
+----------------+----------------+

Example: Diagnostic Message (0x8001)
+----------------+----------------+----------------+----------------+
| Source         | Target         | UDS Service    | UDS Data       |
| Address        | Address        | ID + Subfunc   | (variable)     |
| (2 bytes)      | (2 bytes)      | (variable)     | (variable)     |
+----------------+----------------+----------------+----------------+
```

## Complete Message Types Reference

| Payload Type | Message Name | Direction | Transport | Description |
|--------------|-------------|-----------|-----------|-------------|
| 0x0000 | Generic DoIP Header NACK | RX/TX | UDP/TCP | Protocol error response |
| 0x0001 | Vehicle Identification Request | RX | UDP | Broadcast/multicast vehicle search |
| 0x0002 | Vehicle Identification Request with EID | RX | UDP | Specific ECU search by EID |
| 0x0003 | Vehicle Identification Request with VIN | RX | UDP | Specific vehicle search by VIN |
| 0x0004 | Vehicle Announcement Message | TX | UDP | Periodic vehicle announcement |
| 0x0005 | Routing Activation Request | RX | TCP | Request diagnostic session access |
| 0x0006 | Routing Activation Response | TX | TCP | Grant/deny activation request |
| 0x0007 | Alive Check Request | RX | TCP | Health check request |
| 0x0008 | Entity Status Response | TX | TCP | Node status response |
| 0x0009 | Diagnostic Power Mode Info Request | RX | TCP | Request power mode status |
| 0x000A | Diagnostic Power Mode Info Response | TX | TCP | Power mode (off/accessory/run) |
| 0x4001 | TCP Data Ack | RX/TX | TCP | Optional TCP acknowledgement |
| 0x8001 | Diagnostic Message | RX/TX | TCP | UDS payload wrapper |
| 0x8002 | Diagnostic Message Positive Ack | RX/TX | TCP | Message successfully processed |
| 0x8003 | Diagnostic Message Negative Ack | RX/TX | TCP | Message processing failed |

## TLS Security (Port 3496)

```yaml
# Secure DoIP configuration for production vehicles
doip_tls:
  enabled: true
  port: 3496  # IANA assigned port for DoIP over TLS

  tls_version:
    minimum: "TLS 1.2"
    preferred: "TLS 1.3"

  cipher_suites:
    - TLS_AES_256_GCM_SHA384
    - TLS_AES_128_GCM_SHA256
    - TLS_CHACHA20_POLY1305_SHA256
    - TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
    - TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256

  certificate_requirements:
    key_type: "ECDSA P-256"
    signature_algorithm: "ECDSA-SHA256"
    certificate_chain_validation: true
    ocsp_stapling: recommended
    certificate_pinning: required

  mutual_authentication:
    enabled: true
    client_certificate_required: true
    client_certificate_validation: "strict"

  session_management:
    session_ticket_lifetime_s: 3600
    session_cache_size: 1000
    renegotiation: disabled
```

## VLAN Configuration

```yaml
# VLAN isolation for diagnostic traffic
doip_vlan:
  enabled: true
  vlan_id: 100  # Dedicated diagnostic VLAN
  priority: 6   # High priority for diagnostic frames

  configuration:
    - interface: "ETH0"
      vlan_mode: "tagged"
      vlan_id: 100

    - interface: "ETH1"
      vlan_mode: "untagged"
      vlan_id: 100

  firewall_rules:
    - rule: "Allow DoIP traffic on VLAN 100 only"
      source: "any"
      destination: "vehicle_gateway"
      port: [13400, 3496]
      vlan: 100
      action: "accept"

    - rule: "Block DoIP from non-diagnostic VLANs"
      source: "any"
      destination: "vehicle_gateway"
      port: [13400, 3496]
      vlan: "!100"
      action: "drop"
```

## Error Handling Codes

| Error Code | Name | Description | Action |
|------------|------|-------------|--------|
| 0x00 | Correct | Routing activation successful | Proceed with diagnostic session |
| 0x01 | Already Active | Routing already active from this source | Use existing session |
| 0x02 | Unknown Source | Source logical address not recognized | Check tester configuration |
| 0x03 | Unknown Target | Target logical address not reachable | Verify target ECU availability |
| 0x04 | Invalid Message | Malformed DoIP message | Check message format |
| 0x05 | Out of Memory | Gateway resource exhausted | Wait and retry |
| 0x06 | Target Unreachable | Target ECU not responding | Check ECU power/bus status |
| 0x07 | Authentication Required | TLS certificate validation failed | Present valid certificate |

## Timing Parameters

| Parameter | Symbol | Value | Unit |
|-----------|--------|-------|------|
| TCP connection timeout | T_TCP_Initial | 2000 | ms |
| General TCP timeout | T_TCP_General | 5000 | ms |
| Alive check timeout | T_TCP_Alive | 500 | ms |
| DoIP entity control timeout | A_DoIP_Ctrl | 2000 | ms |
| Vehicle announcement interval | T_Vehicle_Announcement | 500-5000 | ms |
| Routing activation response | T_Routing_Activation | 2000 | ms |
| Diagnostic message timeout | T_Diagnostic_Msg | 5000 | ms |

## DoIP State Machine

```
+-----------+
|  CLOSED   |
+-----+-----+
      |
      | TCP Connection Request
      v
+-----------+
| CONNECTED |<------------------+
+-----+-----+                   |
      |                         |
      | Routing Activation Req  | Routing Activation Failed
      v                         |
+-----------+                   |
| ACTIVATED |-------------------+
+-----+-----+
      |
      | Diagnostic Session
      v
+-----------+
| DIAGNOSTIC|<--------+
| SESSION   |---------+ (multiple messages)
+-----+-----+
      |
      | TCP Close / Timeout
      v
+-----------+
|  CLOSED   |
+-----------+
```

## C Code Patterns

### DoIP Client Implementation

```c
/* DoIP client state machine */
typedef enum {
    DOIP_STATE_CLOSED,
    DOIP_STATE_CONNECTING,
    DOIP_STATE_CONNECTED,
    DOIP_STATE_ACTIVATING,
    DOIP_STATE_ACTIVE,
    DOIP_STATE_DIAGNOSTIC
} DoipState_t;

/* DoIP message structure */
typedef struct {
    uint8_t protocol_version;
    uint8_t inverse_version;
    uint16_t payload_type;
    uint32_t payload_length;
    uint8_t payload[8192];  /* Max DoIP payload */
} DoipMessage_t;

/* DoIP client context */
typedef struct {
    DoipState_t state;
    int tcp_socket;
    uint16_t source_address;
    uint16_t target_address;
    uint32_t last_activity_ms;
    uint32_t timeout_ms;
} DoipContext_t;

/* Initialize DoIP client */
void doip_init(DoipContext_t* ctx) {
    ctx->state = DOIP_STATE_CLOSED;
    ctx->tcp_socket = -1;
    ctx->source_address = 0x0E00;  /* External test equipment */
    ctx->target_address = 0x0000;  /* Default: all nodes */
    ctx->last_activity_ms = 0U;
    ctx->timeout_ms = 2000U;
}

/* Send DoIP message with header */
int doip_send(DoipContext_t* ctx, uint16_t payload_type,
              const uint8_t* payload, uint32_t length) {
    DoipMessage_t msg;
    msg.protocol_version = 0x02U;
    msg.inverse_version = 0xFDU;
    msg.payload_type = payload_type;
    msg.payload_length = htonl(length);
    memcpy(msg.payload, payload, length);

    size_t total_size = 8U + length;
    return send(ctx->tcp_socket, (const char*)&msg, total_size, 0);
}

/* Receive DoIP message with validation */
int doip_receive(DoipContext_t* ctx, DoipMessage_t* msg) {
    /* Read header first (8 bytes) */
    int ret = recv(ctx->tcp_socket, (char*)msg, 8U, MSG_WAITALL);
    if (ret != 8U) {
        return -1;
    }

    /* Validate protocol version */
    if (msg->protocol_version != 0x02U) {
        return -1;
    }
    if (msg->inverse_version != 0xFDU) {
        return -1;
    }

    /* Read payload */
    uint32_t payload_len = ntohl(msg->payload_length);
    if (payload_len > sizeof(msg->payload)) {
        return -1;
    }

    ret = recv(ctx->tcp_socket, (char*)msg->payload, payload_len, MSG_WAITALL);
    if (ret != (int)payload_len) {
        return -1;
    }

    ctx->last_activity_ms = get_time_ms();
    return (int)(8U + payload_len);
}

/* Routing activation request */
int doip_request_routing_activation(DoipContext_t* ctx) {
    uint8_t request[7U];
    request[0U] = (ctx->source_address >> 8) & 0xFFU;
    request[1U] = ctx->source_address & 0xFFU;
    request[2U] = 0x00U;  /* Activation type: Default */
    request[3U] = 0x00U;
    request[4U] = 0x00U;  /* Reserved */
    request[5U] = 0x00U;
    request[6U] = 0x00U;

    return doip_send(ctx, 0x0005U, request, sizeof(request));
}

/* Diagnostic message wrapper */
int doip_send_diagnostic(DoipContext_t* ctx,
                          const uint8_t* uds_payload, uint32_t uds_length) {
    uint8_t diag_header[4U];
    diag_header[0U] = (ctx->source_address >> 8) & 0xFFU;
    diag_header[1U] = ctx->source_address & 0xFFU;
    diag_header[2U] = (ctx->target_address >> 8) & 0xFFU;
    diag_header[3U] = ctx->target_address & 0xFFU;

    /* Build complete DoIP payload */
    uint8_t full_payload[4U + 8192U];
    memcpy(full_payload, diag_header, 4U);
    memcpy(&full_payload[4U], uds_payload, uds_length);

    return doip_send(ctx, 0x8001U, full_payload, 4U + uds_length);
}

/* Main DoIP state machine - call periodically */
void doip_state_machine(DoipContext_t* ctx) {
    uint32_t now = get_time_ms();

    switch (ctx->state) {
        case DOIP_STATE_CLOSED:
            /* Initiate TCP connection */
            ctx->tcp_socket = tcp_connect(DOIP_HOST, DOIP_PORT, DOIP_PORT_TLS);
            if (ctx->tcp_socket >= 0) {
                ctx->state = DOIP_STATE_CONNECTING;
            }
            break;

        case DOIP_STATE_CONNECTING:
            if (tcp_is_connected(ctx->tcp_socket)) {
                ctx->state = DOIP_STATE_ACTIVATING;
                doip_request_routing_activation(ctx);
            } else if ((now - ctx->last_activity_ms) > ctx->timeout_ms) {
                ctx->state = DOIP_STATE_CLOSED;
            }
            break;

        case DOIP_STATE_ACTIVATING:
            /* Wait for routing activation response (0x0006) */
            break;

        case DOIP_STATE_ACTIVE:
        case DOIP_STATE_DIAGNOSTIC:
            /* Check alive timeout */
            if ((now - ctx->last_activity_ms) > 50000U) {
                /* Send alive check */
                doip_send(ctx, 0x0007U, NULL, 0U);
                ctx->last_activity_ms = now;
            }
            break;

        default:
            break;
    }
}
```

### AUTOSAR Dcm Configuration for DoIP

```c
/* Dcm_Dsp_Protocol configuration for DoIP */
#define DCMDSP_PROTOCOL_ID_DOIP           0x02U
#define DCMDSP_PROT_DOIP_USED             STD_ON

/* DoIP entity logical addresses */
#define DOIP_LOGICAL_ADDRESS_GATEWAY      0x1000U
#define DOIP_LOGICAL_ADDRESS_TESTER       0x0E00U
#define DOIP_LOGICAL_ADDRESS_ALL          0x0000U

/* DoIP routing activation configuration */
typedef struct {
    uint16_t source_address;
    uint16_t target_address;
    uint8_t activation_type;
    bool require_vin;
    bool require_eid;
    bool require_gid;
} DoipActivationConfig_t;

static const DoipActivationConfig_t DoipActivationConfig = {
    .source_address = DOIP_LOGICAL_ADDRESS_TESTER,
    .target_address = DOIP_LOGICAL_ADDRESS_GATEWAY,
    .activation_type = 0x00U,  /* Default activation */
    .require_vin = false,
    .require_eid = false,
    .require_gid = false
};

/* DoIP message buffer configuration */
#define DOIP_RX_BUFFER_SIZE         8192U
#define DOIP_TX_BUFFER_SIZE         8192U
#define DOIP_MAX_CONCURRENT_SESSIONS 4U

/* PduR routing configuration for DoIP */
#define PDUR_DOIP_RX_PDU_ID         0x0100U
#define PDUR_DOIP_TX_PDU_ID         0x0101U
#define PDUR_DCM_DOIP_RX_PDU_ID     0x0102U
#define PDUR_DCM_DOIP_TX_PDU_ID     0x0103U

/* Dcm configuration for DoIP transport */
#define DCM_DOIP_SUPPORT            STD_ON
#define DCM_DOIP_PORT_PLAINTEXT     13400U
#define DCM_DOIP_PORT_TLS           3496U
#define DCM_DOIP_SECURITY_ENABLED   STD_ON

/* DoIP session management */
typedef struct {
    uint8_t session_id;
    uint16_t source_address;
    uint16_t target_address;
    uint32_t last_activity_ms;
    bool active;
    bool tls_enabled;
} DoipSession_t;

static DoipSession_t DoipSessions[DCM_DOIP_MAX_SESSIONS];
```

## Implementation Skills

### Skill: doip_vehicle_discovery
**Task**: Implement UDP-based vehicle discovery for locating DoIP entities on the network.
- Broadcast 0x0001 Vehicle ID Request to 255.255.255.255:13400
- Parse 0x0004 Vehicle Announcement responses (VIN, Logical Address, EID, GID)
- Implement timeout and retry logic for discovery (T_Vehicle_Announcement = 500-5000 ms)
- Cache discovered vehicles for rapid reconnection

**Validation Criteria**:
- [ ] Discovery completes within 2 seconds on local network
- [ ] Correctly parses all fields in Vehicle Announcement Message
- [ ] Handles multiple simultaneous vehicle responses
- [ ] Implements exponential backoff for retries

### Skill: doip_routing_activation
**Task**: Implement routing activation handshake to establish diagnostic session.
- Send 0x0005 Routing Activation Request with source/target addresses
- Handle all 0x0006 response codes (0x00-0x07)
- Implement session timeout monitoring (A_DoIP_Ctrl = 2000 ms)
- Support multiple activation types (Default, OEM, Central Security)

**Validation Criteria**:
- [ ] Successfully activates session with code 0x00 (Activated)
- [ ] Handles 0x02 (Unknown Source) with fallback procedure
- [ ] Handles 0x06 (Target Unreachable) gracefully
- [ ] Session timeout triggers reactivation

### Skill: doip_diagnostic_message
**Task**: Implement UDS message transport over DoIP (0x8001 payload type).
- Wrap UDS requests in DoIP diagnostic message format
- Parse positive (0x8002) and negative (0x8003) acknowledgements
- Handle DoIP header fields (Source/Target Address)
- Implement flow control for large UDS payloads (> 4096 bytes)

**Validation Criteria**:
- [ ] Round-trip UDS latency < 50 ms on local network
- [ ] Correctly segments payloads > MTU
- [ ] Handles 0x8003 Negative Ack with error info
- [ ] Maintains ISO 14229 P2/P2* timing

### Skill: doip_tls_security
**Task**: Implement TLS-secured DoIP connections on port 3496.
- Integrate mbedTLS/wolfSSL for TLS 1.2/1.3 handshake
- Implement mutual certificate authentication
- Validate certificate chain with OEM root CA
- Support certificate pinning for production vehicles

**Validation Criteria**:
- [ ] TLS handshake completes within 500 ms
- [ ] Rejects connections without valid client certificate
- [ ] Supports TLS 1.3 cipher suites
- [ ] Certificate validation fails for expired/revoked certs

### Skill: doip_error_handling
**Task**: Implement comprehensive DoIP error detection and recovery.
- Detect and log all DoIP error codes (0x00-0x07)
- Implement automatic reconnection on TCP failure
- Handle TCP socket errors (ECONNRESET, ETIMEDOUT)
- Log security events for TARA compliance

**Validation Criteria**:
- [ ] Recovers from TCP disconnect within 5 seconds
- [ ] Logs all error events with timestamps
- [ ] Implements exponential backoff for retries
- [ ] Alerts operator after 3 consecutive failures

## Related Context
- @context/skills/diagnostics/uds.md
- @context/skills/diagnostics/dtc-management.md
- @context/skills/security/iso-21434-compliance.md
- @context/skills/security/ota-update-security.md
- @context/skills/network/can-protocol.md

## Tools Required
- Wireshark (DoIP dissector for packet analysis)
- CANoe.DiVa (DoIP conformance testing)
- Vector Diagnostic Gateway (DoIP ↔ CAN bridge)
- mbedTLS/wolfSSL (TLS integration for embedded)
- Python-can/doip (DoIP scripting and testing)

## Regulatory Compliance

| Region | Regulation | DoIP Relevance |
|--------|------------|----------------|
| EU/UNECE | UN R155 (Cybersecurity) | TLS mandatory for secure access |
| EU/UNECE | UN R156 (Software Update) | DoIP transport for OTA updates |
| US | SAE J2534-2 | DoIP support for pass-thru devices |
| China | GB/T 32960 | DoIP for remote diagnostics |
| Global | ISO 13400-2 | Conformance test requirements |
