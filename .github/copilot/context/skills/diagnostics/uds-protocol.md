# Skill: UDS Protocol Implementation

## When to Activate

- Implementing diagnostic communication for ECUs compliant with ISO 14229-1 (UDS)
- Developing AUTOSAR Dcm (Diagnostic Communication Manager) module configurations
- Building diagnostic gateways for routing UDS messages between network domains
- Implementing flash bootloader with UDS 0x34/0x36/0x37 services
- Creating diagnostic test automation for manufacturing end-of-line programming
- Developing security access mechanisms for protected diagnostic services
- Implementing routine control for actuator testing and component verification
- Building diagnostic data logging and freeze frame capture systems
- Implementing ISO 15765-2 transport layer for UDS over CAN
- Developing DoIP (Diagnostic over IP) gateway per ISO 13400

## Standards Compliance

- **ISO 14229-1**: UDS Application Layer specification
- **ISO 14229-2**: UDS over CAN (ISO 15765-2) transport
- **ISO 14229-3**: UDS over IP (ISO 13400 DoIP) implementation
- **ISO 14229-5**: UDS over CAN FD transport requirements
- **ISO 15765-2**: Transport Protocol and Network Layer for CAN
- **ISO 13400-2**: DoIP transport protocol and connection management
- **AUTOSAR R21-11**: Dcm (Diagnostic Communication Manager) module specification
- **AUTOSAR R21-11**: Dem (Diagnostic Event Manager) module for DTC storage
- **SAE J2534**: Pass-thru programming interface compatibility
- **OEM Diagnostic Specifications**: Manufacturer-specific DID and routine definitions

## Key Parameters

| Parameter | Range/Options | Unit | Description |
|-----------|---------------|------|-------------|
| Service ID | 0x10, 0x11, 0x14, 0x19, 0x22, 0x27, 0x2E, 0x31, 0x34-0x37, 0x85 | hex | UDS service identifier |
| Sub-function | 0x00-0xFF | hex | Service-specific sub-function |
| Data Identifier (DID) | 0x0000-0xFFFF | hex | 16-bit data identifier |
| Routine ID | 0x0000-0xFFFF | hex | 16-bit routine identifier |
| Security Level | 0x01-0x42 (even=unlock, odd=seed request) | hex | Security access level |
| Session Type | 0x01-0x63 | hex | Diagnostic session identifier |
| P2 Server Timer | 0-5000 | ms | Server response time |
| P2* Server Timer | 0-50000 | ms | Server extended response time |
| S3 Server Timer | 0-65535 | ms | Session timeout |
| Max Block Length | 1-0xFFF | frames | Block size for block transfer |
| CAN ID (Request) | 0x000-0x7FF (11-bit), 0x00000000-0x1FFFFFFF (29-bit) | hex | Request CAN identifier |
| CAN ID (Response) | 0x000-0x7FF (11-bit), 0x00000000-0x1FFFFFFF (29-bit) | hex | Response CAN identifier |
| DTC Format | ISO 14229-1, ISO 15031-6, SAE J2012 | enum | DTC format identifier |
| DTC Status Byte | 8 bits (testFailed, testFailedThisOperationCycle, etc.) | bitmask | DTC status information |

## Domain-Specific Content

### UDS Service Architecture

```
+------------------------------------------------------------------+
|                     Diagnostic Tester (Client)                    |
+------------------------------------------------------------------+
                              |
            +-----------------+-----------------+
            | ISO 15765-2 TP  |  ISO 13400 DoIP |
            | (CAN Transport) |  (Ethernet)     |
            +-----------------+-----------------+
                              |
+-----------------------------v------------------------------+
|                   ECU Diagnostic Stack                      |
| +------------------+  +------------------+  +------------+ |
| | Dcm (Diagnostic  |  | Dem (Diagnostic  |  | CanIf/DoIP | |
| | Comm Manager)    |  | Event Manager)   |  | Transport  | |
| |                  |  |                  |  |            | |
| | - Session Mgmt   |  | - DTC Storage    |  | - ISO-TP   | |
| | - Security Access|  | - Freeze Frame   |  | - DoIP     | |
| | - Service Handler|  | - Aging/Healing  |  | - Routing  | |
| +--------+---------+  +--------+---------+  +-----+------+ |
+----------|--------------------|-------------------|--------+
           |                    |                   |
     +-----v----+         +-----v----+        +-----v----+
     | NVM      |         | Security |        | CAN/Eth  |
     | Storage  |         | Algorithms|       | Hardware |
     +----------+         +----------+        +----------+
```

### UDS Session Management

```c
/* Diagnostic session state machine */
typedef enum {
    DIAG_SESSION_DEFAULT      = 0x01,  /* Default session */
    DIAG_SESSION_PROGRAMMING  = 0x02,  /* Programming session */
    DIAG_SESSION_EXTENDED     = 0x03,  /* Extended diagnostics */
    DIAG_SESSION_SAFETY       = 0x04,  /* Safety system session */
    DIAG_SESSION_END          = 0x10   /* Return to default */
} DiagnosticSession_t;

/* Session configuration structure */
typedef struct {
    DiagnosticSession_t session_type;
    uint16_t p2_server_max_ms;      /* Max response time */
    uint16_t p2_star_server_max_ms; /* Extended response time */
    uint16_t s3_server_ms;          /* Session timeout */
    bool security_enabled;          /* Security access required */
    uint8_t min_security_level;     /* Minimum unlocked level */
} SessionConfig_t;

/* Session state */
typedef struct {
    DiagnosticSession_t current_session;
    uint32_t session_start_time_ms;
    uint32_t last_activity_time_ms;
    bool session_active;
    uint8_t security_level_unlocked;
} SessionState_t;

static SessionState_t g_session_state = {0};

/* ISO 14229-1: 0x10 DiagnosticSessionControl service handler */
UdsResponse_t handle_diagnostic_session_control(
    const UdsRequest_t* request,
    UdsResponse_t* response) {

    const uint8_t session_type = request->data[0];
    const uint8_t sub_function_param = (request->length > 1) ?
                                        request->data[1] : 0x00;

    /* Validate session type */
    if (session_type == 0x00 || session_type > 0x63) {
        return build_negative_response(response, NRC_SUB_FUNCTION_NOT_SUPPORTED);
    }

    /* Check session transition permissions */
    if (!is_session_transition_allowed(g_session_state.current_session,
                                        session_type)) {
        return build_negative_response(response, NRC_SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION);
    }

    /* Handle session end (0x10) */
    if (session_type == DIAG_SESSION_END) {
        g_session_state.current_session = DIAG_SESSION_DEFAULT;
        g_session_state.security_level_unlocked = 0x00;
        g_session_state.session_start_time_ms = get_time_ms();
    } else {
        /* Get session configuration */
        const SessionConfig_t* config = get_session_config(session_type);
        if (config == NULL) {
            return build_negative_response(response, NRC_SUB_FUNCTION_NOT_SUPPORTED);
        }

        /* Update session state */
        g_session_state.current_session = session_type;
        g_session_state.session_start_time_ms = get_time_ms();
    }

    /* Build positive response */
    response->service_id = 0x50;  /* 0x10 + 0x40 */
    response->data[0] = session_type;

    /* Include timing parameters */
    response->data[1] = (uint8_t)(g_p2_server_max_ms >> 8);
    response->data[2] = (uint8_t)(g_p2_server_max_ms);
    response->data[3] = (uint8_t)(g_s3_server_ms >> 8);
    response->data[4] = (uint8_t)(g_s3_server_ms);

    response->length = 5;

    /* Log session change */
    log_diagnostic_event(DIAG_EVENT_SESSION_CHANGED,
                         g_session_state.current_session);

    return UDS_RESPONSE_POSITIVE;
}

/* Session timeout monitoring (called periodically) */
void monitor_session_timeout(void) {
    if (!g_session_state.session_active) {
        return;
    }

    const uint32_t elapsed_ms = get_time_ms() - g_session_state.last_activity_time_ms;
    const SessionConfig_t* config = get_session_config(
                                        g_session_state.current_session);

    if (config != NULL && elapsed_ms > config->s3_server_ms) {
        /* Session timeout - return to default session */
        g_session_state.current_session = DIAG_SESSION_DEFAULT;
        g_session_state.security_level_unlocked = 0x00;
        g_session_state.session_start_time_ms = get_time_ms();

        log_diagnostic_event(DIAG_EVENT_SESSION_TIMEOUT, 0);
    }
}
```

### UDS Security Access Implementation

```c
/* Security access state machine */
typedef enum {
    SECURITY_LOCKED,
    SECURITY_SEED_SENT,
    SECURITY_UNLOCKED
} SecurityState_t;

/* Security access configuration */
typedef struct {
    uint8_t security_level;
    uint16_t seed_delay_ms;
    uint8_t max_attempts;
    uint16_t lockout_time_ms;
    uint32_t (*generate_seed)(void);
    bool (*verify_key)(uint8_t level, const uint8_t* key, uint8_t length);
} SecurityConfig_t;

/* Security access context per level */
typedef struct {
    SecurityState_t state;
    uint8_t failed_attempts;
    uint32_t lockout_end_time_ms;
    uint32_t seed_generation_time_ms;
    uint8_t last_seed[4];
    uint8_t seed_length;
} SecurityContext_t;

static SecurityContext_t g_security_context[4] = {0};  /* Support 4 levels */

/* ISO 14229-1: 0x27 SecurityAccess service - Seed request (odd levels) */
UdsResponse_t handle_security_access_seed(
    const UdsRequest_t* request,
    UdsResponse_t* response) {

    const uint8_t security_type = request->data[0];

    /* Validate security level (must be odd for seed request) */
    if ((security_type & 0x01) == 0x00) {
        return build_negative_response(response, NRC_SUB_FUNCTION_NOT_SUPPORTED);
    }

    const uint8_t security_level = security_type;
    const uint8_t context_index = (security_level - 1) / 2;

    if (context_index >= 4) {
        return build_negative_response(response, NRC_SUB_FUNCTION_NOT_SUPPORTED);
    }

    SecurityContext_t* ctx = &g_security_context[context_index];

    /* Check lockout */
    if (ctx->failed_attempts >= get_security_config(security_level)->max_attempts) {
        if (get_time_ms() < ctx->lockout_end_time_ms) {
            return build_negative_response(response, NRC_EXCEEDED_NUM_OF_ATTEMPTS);
        }
        /* Reset after lockout period */
        ctx->failed_attempts = 0;
        ctx->state = SECURITY_LOCKED;
    }

    /* Check if already unlocked at this level or higher */
    if (ctx->state == SECURITY_UNLOCKED) {
        /* Return zero seed to indicate already unlocked */
        response->service_id = 0x67;  /* 0x27 + 0x40 */
        response->data[0] = security_type;
        response->data[1] = 0x00;
        response->data[2] = 0x00;
        response->data[3] = 0x00;
        response->data[4] = 0x00;
        response->length = 5;
        return UDS_RESPONSE_POSITIVE;
    }

    /* Rate limiting: enforce seed delay */
    const uint32_t elapsed_since_seed = get_time_ms() - ctx->seed_generation_time_ms;
    if (elapsed_since_seed < get_security_config(security_level)->seed_delay_ms) {
        return build_negative_response(response, NRC_REQUEST_SEQUENCE_ERROR);
    }

    /* Generate cryptographically secure seed */
    const uint32_t seed = get_security_config(security_level)->generate_seed();

    /* Store seed for verification */
    ctx->last_seed[0] = (uint8_t)(seed >> 24);
    ctx->last_seed[1] = (uint8_t)(seed >> 16);
    ctx->last_seed[2] = (uint8_t)(seed >> 8);
    ctx->last_seed[3] = (uint8_t)(seed);
    ctx->seed_length = 4;
    ctx->seed_generation_time_ms = get_time_ms();
    ctx->state = SECURITY_SEED_SENT;

    /* Build response */
    response->service_id = 0x67;
    response->data[0] = security_type;
    response->data[1] = ctx->last_seed[0];
    response->data[2] = ctx->last_seed[1];
    response->data[3] = ctx->last_seed[2];
    response->data[4] = ctx->last_seed[3];
    response->length = 5;

    return UDS_RESPONSE_POSITIVE;
}

/* ISO 14229-1: 0x27 SecurityAccess service - Key verification (even levels) */
UdsResponse_t handle_security_access_key(
    const UdsRequest_t* request,
    UdsResponse_t* response) {

    const uint8_t security_type = request->data[0];

    /* Validate security level (must be even for key) */
    if ((security_type & 0x01) != 0x00) {
        return build_negative_response(response, NRC_SUB_FUNCTION_NOT_SUPPORTED);
    }

    const uint8_t security_level = security_type;
    const uint8_t context_index = (security_level - 2) / 2;

    if (context_index >= 4) {
        return build_negative_response(response, NRC_SUB_FUNCTION_NOT_SUPPORTED);
    }

    SecurityContext_t* ctx = &g_security_context[context_index];

    /* Check lockout */
    if (ctx->failed_attempts >= get_security_config(security_level)->max_attempts) {
        if (get_time_ms() < ctx->lockout_end_time_ms) {
            return build_negative_response(response, NRC_EXCEEDED_NUM_OF_ATTEMPTS);
        }
        ctx->failed_attempts = 0;
        ctx->state = SECURITY_LOCKED;
    }

    /* Verify seed was sent */
    if (ctx->state != SECURITY_SEED_SENT) {
        return build_negative_response(response, NRC_REQUEST_SEQUENCE_ERROR);
    }

    /* Verify key */
    const uint8_t* received_key = &request->data[1];
    const uint8_t key_length = request->length - 1;

    if (key_length != ctx->seed_length) {
        return build_negative_response(response, NRC_INVALID_KEY);
    }

    /* Constant-time key comparison to prevent timing attacks */
    if (!constant_time_verify_key(security_level, received_key, key_length)) {
        ctx->failed_attempts++;
        ctx->state = SECURITY_LOCKED;

        if (ctx->failed_attempts >= get_security_config(security_level)->max_attempts) {
            ctx->lockout_end_time_ms = get_time_ms() +
                                       get_security_config(security_level)->lockout_time_ms;
            log_security_event(SECURITY_EVENT_MAX_ATTEMPTS_EXCEEDED, security_level);
        } else {
            log_security_event(SECURITY_EVENT_INVALID_KEY, security_level);
        }

        return build_negative_response(response, NRC_INVALID_KEY);
    }

    /* Key valid - unlock */
    ctx->state = SECURITY_UNLOCKED;
    ctx->failed_attempts = 0;
    g_session_state.security_level_unlocked = security_level;
    g_session_state.last_activity_time_ms = get_time_ms();

    /* Clear seed from memory */
    explicit_memzero(ctx->last_seed, sizeof(ctx->last_seed));

    /* Build response */
    response->service_id = 0x67;
    response->data[0] = security_type;
    response->length = 1;

    log_security_event(SECURITY_EVENT_UNLOCKED, security_level);
    return UDS_RESPONSE_POSITIVE;
}

/* Secure seed generation using hardware RNG */
uint32_t generate_secure_seed(void) {
    /* Use hardware TRNG if available */
    #if defined(HAS_HW_TRNG)
        return hw_trng_generate_u32();
    #else
        /* Fallback: PRNG with entropy from ADC noise */
        static uint32_t seed = 0;
        seed ^= read_adc_noise() << 16;
        seed ^= get_cpu_cycle_count() & 0xFFFF;
        seed ^= (seed >> 7);
        return seed;
    #endif
}

/* Key verification algorithm (example: XOR-based transformation) */
bool verify_key_level_1(const uint8_t* key, uint8_t length) {
    if (length != 4) return false;

    /* Example algorithm - replace with secure implementation */
    const uint8_t expected[4] = {
        g_security_context[0].last_seed[0] ^ 0xA5,
        g_security_context[0].last_seed[1] ^ 0x5A,
        g_security_context[0].last_seed[2] ^ 0x3C,
        g_security_context[0].last_seed[3] ^ 0xC3
    };

    return constant_time_compare(key, expected, 4);
}
```

### UDS Read/Write Data by Identifier

```c
/* Data Identifier (DID) configuration */
typedef struct {
    uint16_t did;
    uint16_t data_length;
    uint8_t read_access_session;    /* Minimum session for read */
    uint8_t write_access_session;   /* Minimum session for write */
    uint8_t security_level_read;    /* 0 = no security required */
    uint8_t security_level_write;   /* 0 = no security required */
    bool (*read_handler)(uint16_t did, uint8_t* buffer, uint16_t* length);
    bool (*write_handler)(uint16_t did, const uint8_t* data, uint16_t length);
    const char* description;
} DidConfig_t;

/* Example DID configurations */
static const DidConfig_t g_did_table[] = {
    /* Vehicle Identification */
    {
        .did = 0xF190,
        .description = "Vehicle Identification Number (VIN)",
        .data_length = 17,
        .read_access_session = DIAG_SESSION_DEFAULT,
        .write_access_session = DIAG_SESSION_PROGRAMMING,
        .security_level_read = 0,
        .security_level_write = 0x22,  /* Level 11 required */
        .read_handler = read_vin_did,
        .write_handler = write_vin_did
    },
    /* System Supplier Identifier */
    {
        .did = 0xF191,
        .description = "System Supplier Identifier",
        .data_length = 20,
        .read_access_session = DIAG_SESSION_DEFAULT,
        .write_access_session = DIAG_SESSION_PROGRAMMING,
        .security_level_read = 0,
        .security_level_write = 0x22,
        .read_handler = read_supplier_id,
        .write_handler = write_supplier_id
    },
    /* Application Software Version */
    {
        .did = 0xF195,
        .description = "Application Software Version",
        .data_length = 32,
        .read_access_session = DIAG_SESSION_DEFAULT,
        .write_access_session = DIAG_SESSION_PROGRAMMING,
        .security_level_read = 0,
        .security_level_write = 0x22,
        .read_handler = read_sw_version,
        .write_handler = NULL  /* Read-only */
    },
    /* Calibration Data */
    {
        .did = 0xF400,
        .description = "Calibration Data Block",
        .data_length = 256,
        .read_access_session = DIAG_SESSION_EXTENDED,
        .write_access_session = DIAG_SESSION_EXTENDED,
        .security_level_read = 0x22,
        .security_level_write = 0x22,
        .read_handler = read_calibration_data,
        .write_handler = write_calibration_data
    }
};

/* ISO 14229-1: 0x22 ReadDataByIdentifier service */
UdsResponse_t handle_read_data_by_identifier(
    const UdsRequest_t* request,
    UdsResponse_t* response) {

    /* Parse DID (big-endian) */
    const uint16_t did = ((uint16_t)request->data[0] << 8) | request->data[1];

    /* Find DID configuration */
    const DidConfig_t* config = find_did_config(did);
    if (config == NULL) {
        return build_negative_response(response, NRC_DATA_IDENTIFIER_NOT_FOUND);
    }

    /* Check session access */
    if (g_session_state.current_session < config->read_access_session) {
        return build_negative_response(response, NRC_SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION);
    }

    /* Check security access */
    if (config->security_level_read > 0 &&
        g_session_state.security_level_unlocked < config->security_level_read) {
        return build_negative_response(response, NRC_SECURITY_ACCESS_DENIED);
    }

    /* Execute read handler */
    uint8_t data_buffer[512];  /* Max DID data length */
    uint16_t data_length = 0;

    if (config->read_handler == NULL ||
        !config->read_handler(config->did, data_buffer, &data_length)) {
        return build_negative_response(response, NRC_CONDITIONS_NOT_CORRECT);
    }

    /* Build response */
    response->service_id = 0x62;  /* 0x22 + 0x40 */
    response->data[0] = (uint8_t)(did >> 8);
    response->data[1] = (uint8_t)(did);
    memcpy(&response->data[2], data_buffer, data_length);
    response->length = 2 + data_length;

    return UDS_RESPONSE_POSITIVE;
}

/* ISO 14229-1: 0x2E WriteDataByIdentifier service */
UdsResponse_t handle_write_data_by_identifier(
    const UdsRequest_t* request,
    UdsResponse_t* response) {

    /* Parse DID (big-endian) */
    const uint16_t did = ((uint16_t)request->data[0] << 8) | request->data[1];

    /* Find DID configuration */
    const DidConfig_t* config = find_did_config(did);
    if (config == NULL) {
        return build_negative_response(response, NRC_DATA_IDENTIFIER_NOT_FOUND);
    }

    /* Check write handler exists */
    if (config->write_handler == NULL) {
        return build_negative_response(response, NRC_REQUEST_OUT_OF_RANGE);
    }

    /* Check session access */
    if (g_session_state.current_session < config->write_access_session) {
        return build_negative_response(response, NRC_SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION);
    }

    /* Check security access */
    if (config->security_level_write > 0 &&
        g_session_state.security_level_unlocked < config->security_level_write) {
        return build_negative_response(response, NRC_SECURITY_ACCESS_DENIED);
    }

    /* Validate data length */
    const uint16_t data_length = request->length - 2;  /* Subtract DID */
    if (data_length > config->data_length) {
        return build_negative_response(response, NRC_REQUEST_OUT_OF_RANGE);
    }

    /* Execute write handler */
    const uint8_t* data = &request->data[2];
    if (!config->write_handler(config->did, data, data_length)) {
        return build_negative_response(response, NRC_CONDITIONS_NOT_CORRECT);
    }

    /* Build response */
    response->service_id = 0x6E;  /* 0x2E + 0x40 */
    response->data[0] = (uint8_t)(did >> 8);
    response->data[1] = (uint8_t)(did);
    response->length = 2;

    return UDS_RESPONSE_POSITIVE;
}

/* Example DID handler implementations */
bool read_vin_did(uint16_t did, uint8_t* buffer, uint16_t* length) {
    /* Read VIN from NVM */
    const VinData_t* vin_data = get_vin_from_nvm();

    if (vin_data == NULL || !vin_data->valid) {
        return false;
    }

    memcpy(buffer, vin_data->vin_string, VIN_LENGTH);
    *length = VIN_LENGTH;
    return true;
}

bool write_vin_did(uint16_t did, const uint8_t* data, uint16_t length) {
    /* Validate VIN format (ISO 3779) */
    if (length != VIN_LENGTH || !validate_vin_format((const char*)data)) {
        return false;
    }

    /* Write to NVM */
    VinData_t vin_data;
    memcpy(vin_data.vin_string, data, VIN_LENGTH);
    vin_data.valid = true;
    vin_data.timestamp = get_timestamp();

    return write_vin_to_nvm(&vin_data);
}
```

### UDS Routine Control

```c
/* Routine Control configuration */
typedef struct {
    uint16_t routine_id;
    const char* description;
    uint8_t min_session;
    uint8_t min_security_level;
    bool (*start_routine)(uint16_t id, const uint8_t* opt_data, uint8_t length);
    bool (*stop_routine)(uint16_t id);
    bool (*get_result)(uint16_t id, uint8_t* result_data, uint16_t* length);
    uint16_t max_execution_time_ms;
} RoutineConfig_t;

/* Routine state */
typedef struct {
    bool is_running;
    uint32_t start_time_ms;
    uint8_t status;
    uint8_t result_data[256];
    uint16_t result_length;
} RoutineState_t;

static RoutineState_t g_routine_state[8] = {0};

/* ISO 14229-1: 0x31 RoutineControl service */
UdsResponse_t handle_routine_control(
    const UdsRequest_t* request,
    UdsResponse_t* response) {

    const uint8_t sub_function = request->data[0];
    const uint16_t routine_id = ((uint16_t)request->data[1] << 8) | request->data[2];
    const uint8_t* option_data = &request->data[3];
    const uint8_t option_length = request->length - 3;

    /* Find routine configuration */
    const RoutineConfig_t* config = find_routine_config(routine_id);
    if (config == NULL) {
        return build_negative_response(response, NRC_ROUTINE_ID_NOT_FOUND);
    }

    /* Check session */
    if (g_session_state.current_session < config->min_session) {
        return build_negative_response(response, NRC_SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION);
    }

    /* Check security */
    if (config->min_security_level > 0 &&
        g_session_state.security_level_unlocked < config->min_security_level) {
        return build_negative_response(response, NRC_SECURITY_ACCESS_DENIED);
    }

    switch (sub_function) {
        case 0x01:  /* Start Routine */
            return handle_routine_start(config, routine_id, option_data,
                                        option_length, response);

        case 0x02:  /* Stop Routine */
            return handle_routine_stop(config, routine_id, response);

        case 0x03:  /* Request Routine Result */
            return handle_routine_result(config, routine_id, response);

        default:
            return build_negative_response(response, NRC_SUB_FUNCTION_NOT_SUPPORTED);
    }
}

/* Start Routine handler */
static UdsResponse_t handle_routine_start(
    const RoutineConfig_t* config,
    uint16_t routine_id,
    const uint8_t* option_data,
    uint8_t option_length,
    UdsResponse_t* response) {

    /* Check if routine already running */
    RoutineState_t* state = get_routine_state(routine_id);
    if (state->is_running) {
        return build_negative_response(response, NRC_CONDITIONS_NOT_CORRECT);
    }

    /* Start routine */
    if (!config->start_routine(routine_id, option_data, option_length)) {
        return build_negative_response(response, NRC_CONDITIONS_NOT_CORRECT);
    }

    state->is_running = true;
    state->start_time_ms = get_time_ms();
    state->status = 0x00;  /* Running */

    /* Build response */
    response->service_id = 0x71;  /* 0x31 + 0x40 */
    response->data[0] = 0x01;  /* Start routine sub-function */
    response->data[1] = (uint8_t)(routine_id >> 8);
    response->data[2] = (uint8_t)(routine_id);
    response->length = 3;

    return UDS_RESPONSE_POSITIVE;
}

/* Stop Routine handler */
static UdsResponse_t handle_routine_stop(
    const RoutineConfig_t* config,
    uint16_t routine_id,
    UdsResponse_t* response) {

    RoutineState_t* state = get_routine_state(routine_id);

    if (!state->is_running) {
        return build_negative_response(response, NRC_CONDITIONS_NOT_CORRECT);
    }

    /* Stop routine */
    if (!config->stop_routine(routine_id)) {
        return build_negative_response(response, NRC_CONDITIONS_NOT_CORRECT);
    }

    state->is_running = false;
    state->status = 0x01;  /* Stopped */

    /* Build response */
    response->service_id = 0x71;
    response->data[0] = 0x02;  /* Stop routine sub-function */
    response->data[1] = (uint8_t)(routine_id >> 8);
    response->data[2] = (uint8_t)(routine_id);
    response->length = 3;

    return UDS_RESPONSE_POSITIVE;
}

/* Request Routine Result handler */
static UdsResponse_t handle_routine_result(
    const RoutineConfig_t* config,
    uint16_t routine_id,
    UdsResponse_t* response) {

    RoutineState_t* state = get_routine_state(routine_id);

    /* Check if routine completed */
    if (state->is_running) {
        /* Check for timeout */
        const uint32_t elapsed = get_time_ms() - state->start_time_ms;
        if (elapsed < config->max_execution_time_ms) {
            return build_negative_response(response, NRC_REQUEST_SEQUENCE_ERROR);
        }
        /* Force stop on timeout */
        config->stop_routine(routine_id);
        state->is_running = false;
        state->status = 0x02;  /* Timeout */
    }

    /* Get result */
    uint8_t result_data[256];
    uint16_t result_length = 0;

    if (!config->get_result(routine_id, result_data, &result_length)) {
        return build_negative_response(response, NRC_CONDITIONS_NOT_CORRECT);
    }

    /* Build response */
    response->service_id = 0x71;
    response->data[0] = 0x03;  /* Request result sub-function */
    response->data[1] = (uint8_t)(routine_id >> 8);
    response->data[2] = (uint8_t)(routine_id);
    response->data[3] = state->status;
    memcpy(&response->data[4], result_data, result_length);
    response->length = 4 + result_length;

    return UDS_RESPONSE_POSITIVE;
}

/* Example routine implementations */
bool start_routine_actuator_test(uint16_t routine_id,
                                  const uint8_t* opt_data, uint8_t length) {
    /* Actuator test routine */
    const uint8_t actuator_id = (length > 0) ? opt_data[0] : 0;

    /* Validate actuator ID */
    if (!is_valid_actuator(actuator_id)) {
        return false;
    }

    /* Command actuator sweep */
    return actuator_perform_sweep(actuator_id);
}

bool get_routine_actuator_result(uint16_t routine_id,
                                  uint8_t* result_data, uint16_t* length) {
    /* Return test results */
    ActuatorTestResult_t result;
    if (!actuator_get_test_result(&result)) {
        return false;
    }

    result_data[0] = result.pass_fail;
    result_data[1] = (uint8_t)(result.measured_value >> 8);
    result_data[2] = (uint8_t)(result.measured_value);
    *length = 3;
    return true;
}
```

### UDS Flash Programming Sequence

```c
/* Flash programming state machine */
typedef enum {
    FLASH_IDLE,
    FLASH_DOWNLOAD_REQUESTED,
    FLASH_DOWNLOAD_IN_PROGRESS,
    FLASH_DOWNLOAD_COMPLETE,
    FLASH_READY_TO_ACTIVATE
} FlashState_t;

typedef struct {
    FlashState_t state;
    uint32_t memory_address;
    uint32_t memory_size;
    uint32_t bytes_downloaded;
    uint8_t data_format;
    uint8_t address_and_length_format;
    uint16_t max_block_length;
    uint32_t download_start_time_ms;
} FlashContext_t;

static FlashContext_t g_flash_context = {0};

/* ISO 14229-1: 0x34 RequestDownload service */
UdsResponse_t handle_request_download(
    const UdsRequest_t* request,
    UdsResponse_t* response) {

    const uint8_t data_format = request->data[0];
    const uint8_t addr_len_format = request->data[1];
    const uint8_t addr_length = (addr_len_format >> 4) & 0x0F;
    const uint8_t size_length = addr_len_format & 0x0F;

    /* Validate address and length format */
    if (addr_length < 1 || addr_length > 4 ||
        size_length < 1 || size_length > 4) {
        return build_negative_response(response, NRC_FORMAT_NOT_CORRECT);
    }

    /* Parse memory address */
    uint32_t memory_address = 0;
    for (uint8_t i = 0; i < addr_length; i++) {
        memory_address = (memory_address << 8) | request->data[2 + i];
    }

    /* Parse memory size */
    uint32_t memory_size = 0;
    for (uint8_t i = 0; i < size_length; i++) {
        memory_size = (memory_size << 8) | request->data[2 + addr_length + i];
    }

    /* Validate memory region */
    if (!is_valid_flash_region(memory_address, memory_size)) {
        return build_negative_response(response, NRC_REQUEST_OUT_OF_RANGE);
    }

    /* Check session and security */
    if (g_session_state.current_session != DIAG_SESSION_PROGRAMMING) {
        return build_negative_response(response, NRC_SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION);
    }
    if (g_session_state.security_level_unlocked < 0x22) {
        return build_negative_response(response, NRC_SECURITY_ACCESS_DENIED);
    }

    /* Check flash is not already in use */
    if (g_flash_context.state != FLASH_IDLE) {
        return build_negative_response(response, NRC_CONDITIONS_NOT_CORRECT);
    }

    /* Initialize flash context */
    g_flash_context.state = FLASH_DOWNLOAD_REQUESTED;
    g_flash_context.memory_address = memory_address;
    g_flash_context.memory_size = memory_size;
    g_flash_context.bytes_downloaded = 0;
    g_flash_context.data_format = data_format;
    g_flash_context.address_and_length_format = addr_len_format;
    g_flash_context.max_block_length = get_max_block_length(memory_address);
    g_flash_context.download_start_time_ms = get_time_ms();

    /* Erase flash region */
    if (!flash_erase(memory_address, memory_size)) {
        g_flash_context.state = FLASH_IDLE;
        return build_negative_response(response, NRC_GENERAL_PROGRAMMING_FAILURE);
    }

    /* Build response */
    response->service_id = 0x74;  /* 0x34 + 0x40 */
    response->data[0] = addr_len_format;
    /* Maximum block length for transfer */
    response->data[1] = (uint8_t)(g_flash_context.max_block_length >> 8);
    response->data[2] = (uint8_t)(g_flash_context.max_block_length);
    response->length = 3;

    return UDS_RESPONSE_POSITIVE;
}

/* ISO 14229-1: 0x36 TransferData service */
UdsResponse_t handle_transfer_data(
    const UdsRequest_t* request,
    UdsResponse_t* response) {

    /* Check state */
    if (g_flash_context.state != FLASH_DOWNLOAD_IN_PROGRESS &&
        g_flash_context.state != FLASH_DOWNLOAD_REQUESTED) {
        return build_negative_response(response, NRC_REQUEST_SEQUENCE_ERROR);
    }

    const uint8_t block_counter = request->data[0];
    const uint8_t* data = &request->data[1];
    const uint16_t data_length = request->length - 1;

    /* Validate block counter */
    const uint8_t expected_counter = (g_flash_context.bytes_downloaded /
                                       g_flash_context.max_block_length) & 0xFF;
    if (block_counter != expected_counter) {
        return build_negative_response(response, NRC_WRONG_BLOCK_SEQUENCE_COUNTER);
    }

    /* Validate data length */
    if (data_length > g_flash_context.max_block_length) {
        return build_negative_response(response, NRC_REQUEST_OUT_OF_RANGE);
    }

    /* Check download complete */
    if (g_flash_context.bytes_downloaded + data_length > g_flash_context.memory_size) {
        return build_negative_response(response, NRC_TRANSFER_DATA_SUSPEND);
    }

    /* Write to flash */
    const uint32_t write_address = g_flash_context.memory_address +
                                   g_flash_context.bytes_downloaded;

    if (!flash_write(write_address, data, data_length)) {
        return build_negative_response(response, NRC_GENERAL_PROGRAMMING_FAILURE);
    }

    g_flash_context.bytes_downloaded += data_length;

    /* Update state */
    if (g_flash_context.state == FLASH_DOWNLOAD_REQUESTED) {
        g_flash_context.state = FLASH_DOWNLOAD_IN_PROGRESS;
    }

    /* Build response */
    response->service_id = 0x76;  /* 0x36 + 0x40 */
    response->data[0] = block_counter;
    response->length = 1;

    /* Check if download complete */
    if (g_flash_context.bytes_downloaded >= g_flash_context.memory_size) {
        g_flash_context.state = FLASH_DOWNLOAD_COMPLETE;
    }

    return UdsResponse_t(UDS_RESPONSE_POSITIVE);
}

/* ISO 14229-1: 0x37 ExitRoutine service (finalize download) */
UdsResponse_t handle_exit_routine(
    const UdsRequest_t* request,
    UdsResponse_t* response) {

    /* Check state */
    if (g_flash_context.state != FLASH_DOWNLOAD_COMPLETE) {
        return build_negative_response(response, NRC_REQUEST_SEQUENCE_ERROR);
    }

    /* Verify downloaded data (CRC/checksum) */
    if (!verify_flash_integrity(g_flash_context.memory_address,
                                 g_flash_context.memory_size)) {
        g_flash_context.state = FLASH_IDLE;
        return build_negative_response(response, NRC_GENERAL_PROGRAMMING_FAILURE);
    }

    /* Mark download as complete and ready for activation */
    g_flash_context.state = FLASH_READY_TO_ACTIVATE;

    /* Store download completion flag */
    set_download_completion_flag(g_flash_context.memory_address,
                                  g_flash_context.memory_size);

    /* Build response */
    response->service_id = 0x77;  /* 0x37 + 0x40 */
    response->length = 0;

    return UDS_RESPONSE_POSITIVE;
}

/* ISO 14229-1: 0x11 ECUReset service - Application reset triggers flash commit */
UdsResponse_t handle_ecu_reset(
    const UdsRequest_t* request,
    UdsResponse_t* response) {

    const uint8_t reset_type = request->data[0];

    switch (reset_type) {
        case 0x01:  /* Hard Reset */
        case 0x02:  /* Key Off/On Reset */
        case 0x03:  /* Soft Reset */
        case 0x04:  /* Enable Rapid Power Shut-Down */
        case 0x05:  /* Disable Rapid Power Shut-Down */

            /* Check if pending flash commit */
            if (g_flash_context.state == FLASH_READY_TO_ACTIVATE) {
                /* Commit flash update */
                if (!commit_flash_update()) {
                    return build_negative_response(response,
                                                   NRC_GENERAL_PROGRAMMING_FAILURE);
                }
                g_flash_context.state = FLASH_IDLE;
            }

            /* Perform reset after response sent */
            schedule_ecu_reset(reset_type);

            /* Build response (sent before reset) */
            response->service_id = 0x51;
            response->length = 0;
            return UDS_RESPONSE_POSITIVE;

        default:
            return build_negative_response(response, NRC_SUB_FUNCTION_NOT_SUPPORTED);
    }
}
```

### ISO 15765-2 Transport Integration

```c
/* ISO 15765-2: Transport Protocol state machine */
typedef enum {
    ISO_TP_IDLE,
    ISO_TP_RECEIVING_SINGLE_FRAME,
    ISO_TP_RECEIVING_FIRST_FRAME,
    ISO_TP_RECEIVING_CONSECUTIVE_FRAME,
    ISO_TP_SENDING_SINGLE_FRAME,
    ISO_TP_SENDING_FIRST_FRAME,
    ISO_TP_SENDING_CONSECUTIVE_FRAME,
    ISO_TP_WAITING_FLOW_CONTROL
} IsoTpState_t;

/* ISO 15765-2 frame types */
typedef enum {
    ISO_TP_SINGLE_FRAME      = 0x00,
    ISO_TP_FIRST_FRAME       = 0x10,
    ISO_TP_CONSECUTIVE_FRAME = 0x20,
    ISO_TP_FLOW_CONTROL      = 0x30
} IsoTpFrameType_t;

/* ISO 15765-2 context */
typedef struct {
    IsoTpState_t state;
    uint32_t can_id_rx;
    uint32_t can_id_tx;
    uint8_t buffer[4096];  /* Max ISO-TP payload */
    uint16_t buffer_size;
    uint16_t bytes_received;
    uint16_t total_length;
    uint8_t block_size;
    uint8_t st_min;
    uint8_t consecutive_fc;
    uint32_t last_frame_time_ms;
    uint8_t next_sn;  /* Sequence number */
} IsoTpContext_t;

static IsoTpContext_t g_iso_tp_context = {0};

/* ISO 15765-2: Receive CAN frame */
void iso_tp_receive_frame(const CanFrame_t* frame) {
    const uint8_t* data = frame->data;
    const uint8_t first_byte = data[0];
    const IsoTpFrameType_t frame_type = (IsoTpFrameType_t)(first_byte >> 4);

    switch (frame_type) {
        case ISO_TP_SINGLE_FRAME: {
            /* Single frame: 0xxx (length <= 7) or 0000 (extended) */
            uint8_t length = first_byte & 0x0F;
            const uint8_t* payload = &data[1];

            if (length == 0) {
                /* Extended single frame */
                length = data[1];
                payload = &data[2];
            }

            if (length <= sizeof(g_iso_tp_context.buffer)) {
                memcpy(g_iso_tp_context.buffer, payload, length);
                g_iso_tp_context.bytes_received = length;
                iso_tp_notify上层_complete();
            }
            break;
        }

        case ISO_TP_FIRST_FRAME: {
            /* First frame: 1xxx (total length high nibble) */
            const uint16_t total_length = ((first_byte & 0x0F) << 8) | data[1];

            if (total_length <= sizeof(g_iso_tp_context.buffer)) {
                g_iso_tp_context.state = ISO_TP_RECEIVING_FIRST_FRAME;
                g_iso_tp_context.total_length = total_length;
                g_iso_tp_context.bytes_received = 6;  /* 6 bytes in first frame */
                g_iso_tp_context.next_sn = 1;
                memcpy(g_iso_tp_context.buffer, &data[2], 6);

                /* Send Flow Control */
                iso_tp_send_flow_control(ISO_TP_CTS,
                                         g_iso_tp_context.block_size,
                                         g_iso_tp_context.st_min);
            }
            break;
        }

        case ISO_TP_CONSECUTIVE_FRAME: {
            /* Consecutive frame: 0010xxxx (sequence number) */
            const uint8_t sn = first_byte & 0x0F;

            if (sn == g_iso_tp_context.next_sn &&
                g_iso_tp_context.state == ISO_TP_RECEIVING_FIRST_FRAME) {

                const uint16_t offset = g_iso_tp_context.bytes_received;
                const uint16_t copy_length = 7;  /* 7 bytes in consecutive frame */

                if (offset + copy_length <= g_iso_tp_context.total_length) {
                    memcpy(&g_iso_tp_context.buffer[offset], &data[1], copy_length);
                    g_iso_tp_context.bytes_received += copy_length;
                    g_iso_tp_context.next_sn = (sn + 1) & 0x0F;

                    /* Check if complete */
                    if (g_iso_tp_context.bytes_received >= g_iso_tp_context.total_length) {
                        iso_tp_notify上层_complete();
                    }
                }
            }
            break;
        }

        case ISO_TP_FLOW_CONTROL:
            /* Flow control frame (from receiver to sender) */
            iso_tp_handle_flow_control(data[0] & 0x0F,  /* Flow status */
                                        data[1],          /* Block size */
                                        data[2]);         /* STmin */
            break;
    }
}

/* ISO 15765-2: Send Flow Control frame */
void iso_tp_send_flow_control(uint8_t flow_status,
                               uint8_t block_size,
                               uint8_t st_min) {
    CanFrame_t fc_frame;
    fc_frame.id = g_iso_tp_context.can_id_tx;
    fc_frame.dlc = 8;
    fc_frame.data[0] = 0x30 | (flow_status & 0x0F);
    fc_frame.data[1] = block_size;
    fc_frame.data[2] = st_min;
    /* Padding */
    for (uint8_t i = 3; i < 8; i++) {
        fc_frame.data[i] = 0x00;
    }

    can_transmit(&fc_frame);
}

/* ISO 15765-2: Send UDS message (multi-frame support) */
void iso_tp_send_uds_message(const uint8_t* data, uint16_t length) {
    if (length <= 7) {
        /* Single frame */
        CanFrame_t sf_frame;
        sf_frame.id = g_iso_tp_context.can_id_tx;
        sf_frame.dlc = 8;
        sf_frame.data[0] = length;
        memcpy(&sf_frame.data[1], data, length);
        /* Padding */
        for (uint8_t i = length + 1; i < 8; i++) {
            sf_frame.data[i] = 0x00;
        }
        can_transmit(&sf_frame);
    } else {
        /* First frame */
        CanFrame_t ff_frame;
        ff_frame.id = g_iso_tp_context.can_id_tx;
        ff_frame.dlc = 8;
        ff_frame.data[0] = 0x10 | ((length >> 8) & 0x0F);
        ff_frame.data[1] = length & 0xFF;
        memcpy(&ff_frame.data[2], data, 6);
        can_transmit(&ff_frame);

        /* Wait for Flow Control, then send consecutive frames */
        g_iso_tp_context.state = ISO_TP_WAITING_FLOW_CONTROL;
    }
}
```

### Negative Response Codes (NRC) Reference

```c
/* ISO 14229-1 Negative Response Codes */
typedef enum {
    NRC_POSITIVE_RESPONSE              = 0x00,
    NRC_GENERAL_REJECT                 = 0x10,
    NRC_SERVICE_NOT_SUPPORTED          = 0x11,
    NRC_SUB_FUNCTION_NOT_SUPPORTED     = 0x12,
    NRC_INCORRECT_MESSAGE_LENGTH       = 0x13,
    NRC_CONDITIONS_NOT_CORRECT         = 0x22,
    NRC_REQUEST_SEQUENCE_ERROR         = 0x24,
    NRC_REQUEST_OUT_OF_RANGE           = 0x31,
    NRC_SECURITY_ACCESS_DENIED         = 0x33,
    NRC_AUTHENTICATION_REQUIRED        = 0x34,
    NRC_INVALID_KEY                    = 0x35,
    NRC_EXCEEDED_NUM_OF_ATTEMPTS       = 0x36,
    NRC_REQUIRED_TIME_DELAY_NOT_EXPIRED = 0x37,
    NRC_UPLOAD_DOWNLOAD_NOT_ACCEPTED   = 0x70,
    NRC_TRANSFER_DATA_SUSPEND          = 0x71,
    NRC_GENERAL_PROGRAMMING_FAILURE    = 0x72,
    NRC_WRONG_BLOCK_SEQUENCE_COUNTER   = 0x73,
    NRC_REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING = 0x78,
    NRC_SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7E,
    NRC_SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION = 0x7F,
    NRC_RPM_TOO_HIGH                   = 0x81,
    NRC_RPM_TOO_LOW                    = 0x82,
    NRC_ENGINE_IS_RUNNING              = 0x83,
    NRC_DATA_IDENTIFIER_NOT_FOUND      = 0xA2,
    NRC_VEHICLE_MANUFACTURER_RESERVED  = 0xE0
} NrcCode_t;

/* Build negative response */
UdsResponse_t build_negative_response(UdsResponse_t* response, NrcCode_t nrc) {
    response->service_id = 0x7F;
    response->data[0] = response->request_service_id;  /* Echo rejected SID */
    response->data[1] = nrc;
    response->length = 2;

    log_diagnostic_event(DIAG_EVENT_NEGATIVE_RESPONSE, nrc);
    return UDS_RESPONSE_NEGATIVE;
}
```

## Related Context

- `diagnostics/dtc-management.md` — DTC storage, aging, and UDS 0x14/0x19 services
- `diagnostics/doip.md` — Diagnostic over IP (ISO 13400) transport layer
- `network/can-protocol.md` — CAN bus fundamentals and ISO 15765-2 transport
- `diagnostics/obd-ii.md` — OBD-II emissions diagnostics compatibility
- `safety/iso-26262-compliance.md` — Functional safety requirements for diagnostic access
- `security/cybersecurity-rules.md` — Security hardening for diagnostic interfaces

## Approach

1. Implement UDS state machine with all major services (0x10, 0x11, 0x14, 0x19, 0x22, 0x27, 0x2E, 0x31, 0x34-0x37, 0x85)
2. Configure session management with P2/P2*/S3 timing parameters per OEM requirements
3. Implement security access with cryptographically secure seed generation and constant-time key verification
4. Create DID configuration table with access control (session, security level) and read/write handlers
5. Build routine control framework for actuator testing and component verification
6. Implement flash programming sequence with download, transfer, and commit phases
7. Integrate ISO 15765-2 transport layer for CAN-based UDS communication
8. Connect UDS services to Dem module for DTC clearing and diagnostic event logging
9. Add comprehensive negative response handling with proper NRC codes
10. Implement session timeout monitoring and security lockout mechanisms

## Deliverables

- UDS service handler implementation for all major services
- Session management state machine with timing supervision
- Security access module with seed-key algorithm
- DID configuration table and handler framework
- Routine control implementation for actuator testing
- Flash programming bootloader integration
- ISO 15765-2 transport layer integration
- Negative response code handling and logging
- DTC interface functions (Dem module integration)
- Unit test suite for UDS service handlers
- HIL test procedures for diagnostic validation
- Integration guide for AUTOSAR Dcm module

## Tools Required

- Vector CANoe / CANalyzer — Diagnostic protocol analysis and simulation
- Intrepid Control Systems Vehicle Spy — CAN/UDS monitoring and scripting
- PEAK-System PCAN-View — CAN bus monitoring
- dSPACE DiagnosticDesk — HIL diagnostic testing
- ETAS INCA — Calibration and diagnostic access
- Vector vFlash — ECU flashing and programming validation
- AUTOSAR Dcm Configurator (EB Tresos, DaVinci) — Diagnostic module configuration
- Cppcheck / Polyspace — Static analysis for security-critical code
- Google Test / UnitTest++ — Unit testing framework
- Robot Framework — Test automation
- Wireshark — DoIP and Ethernet diagnostic analysis
- Oscilloscope / Logic Analyzer — Physical layer debugging
