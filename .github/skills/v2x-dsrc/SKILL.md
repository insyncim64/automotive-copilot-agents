---
name: v2x-dsrc
description: "Use when: Skill: DSRC (Dedicated Short-Range Communications) for V2X topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: DSRC (Dedicated Short-Range Communications) for V2X

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/v2x/dsrc.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## When to Activate
- User is developing DSRC-based V2X systems (OBU/RSU)
- User needs IEEE 802.11p physical/MAC layer implementation guidance
- User requests WAVE protocol stack (IEEE 1609.x) integration
- User is implementing BSM (Basic Safety Message) generation per SAE J2735
- User needs WSM (WAVE Short Message) handling and WSMP encoding
- User asks about 5.9 GHz channel allocation and multi-channel operation
- User requests DSRC security credential management (IEEE 1609.2)
- User needs AUTOSAR implementation patterns for DSRC ECUs
- User asks about ISO 26262 safety mechanisms for DSRC-dependent functions

## Standards Compliance
- IEEE 802.11p-2010 (Physical and MAC layer for WAVE)
- IEEE 1609.0-2013 (WAVE Architecture)
- IEEE 1609.2-2016 (Security Services for V2X)
- IEEE 1609.3-2016 (WSMP - WAVE Short Message Protocol)
- IEEE 1609.4-2016 (Multi-Channel Operation)
- IEEE 1609.11-2019 (WAVE Services)
- SAE J2735-2020 (DSRC Message Set Dictionary - BSM)
- ISO 26262:2018 (Functional Safety) - ASIL B/C/D for V2X-dependent functions
- ASPICE Level 3 - Model-based development process
- AUTOSAR 4.4 - V2X communication stack architecture
- ISO 21434:2021 (Cybersecurity) - V2X message authentication
- FCC Part 90 / ETSI TS 102 691 (5.9 GHz spectrum allocation)

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Operating frequency | 5.850 - 5.925 | GHz |
| Channel bandwidth | 10 | MHz |
| Number of channels | 7 (CH172-CH184) | channels |
| Control channel (CCH) | CH178 (5.890 GHz) | GHz |
| Service channels (SCH) | CH172,174,176,180,182,184 | GHz |
| Data rate | 3, 4.5, 6, 9, 12, 18, 27 | Mbps |
| Modulation | BPSK, QPSK, 16-QAM, 64-QAM | - |
| TX power (OBU) | 20 - 33 | dBm |
| TX power (RSU) | 30 - 44 | dBm |
| Receiver sensitivity | -85 to -95 | dBm |
| Communication range | 300 - 1000 | meters |
| BSM transmission rate | 10 | Hz |
| BSM latency | < 100 | ms |
| Message reliability | > 99 | percent |
| Channel switch interval | 50 | ms |
| Guard interval | 1.6 | µs |
| OFDM subcarriers | 52 (48 data + 4 pilot) | subcarriers |

## DSRC/WAVE Architecture

```
+-------------------------------------------------------------------+
|                    DSRC Communication Stack                        |
+-------------------------------------------------------------------+
|  Application Layer                                                 |
|  +-------------------+  +-------------------+  +---------------+  |
|  |   Safety Apps     |  |   N-Safety Apps   |  |  Mgmt Apps    |  |
|  |   (BSM, CAM)      |  |   (SPAT, MAP)     |  |  (WSM Admin)  |  |
|  +-------------------+  +-------------------+  +---------------+  |
+-------------------------------------------------------------------+
|  WAVE Protocol Stack (IEEE 1609.x)                                 |
|  +----------------------------------------------------------------+|
|  | IEEE 1609.2 (Security)  | IEEE 1609.3 (WSMP) | IEEE 1609.11   |||
|  | - Certificate Mgmt      | - WSM Format       | - WAVE Svcs   |||
|  | - ECDSA P-256 Signing   | - WSA Generation   | - Service Adv |||
|  | - CRL Validation        | - Geocast Routing  | - WSM Router  |||
|  +----------------------------------------------------------------+|
+-------------------------------------------------------------------+
|  IEEE 1609.4 Multi-Channel Manager                                 |
|  +----------------------------------------------------------------+|
|  |  CCH Interval (50ms)     |    SCH Interval (50ms)             ||
|  |  - BSM Tx/Rx             |    - WSA Rx                        ||
|  |  - WSA Tx                |    - Service Channel Comm          ||
|  |  - Time Sync             |    - Extended Data Exchange        ||
|  +----------------------------------------------------------------+|
+-------------------------------------------------------------------+
|  IEEE 802.11p MAC Layer                                            |
|  +----------------------------------------------------------------+|
|  | EDCA (Enhanced Distributed Channel Access)                      ||
|  | - 4 Access Categories (AC_BK, AC_BE, AC_VI, AC_VO)             ||
|  | - AIFS, CWmin, CWmax per AC                                    ||
|  | - Collision avoidance                                          ||
|  +----------------------------------------------------------------+|
+-------------------------------------------------------------------+
|  IEEE 802.11p Physical Layer                                       |
|  +----------------------------------------------------------------+|
|  | OFDM (52 subcarriers, 10 MHz BW)                                ||
|  | - Convolutional coding (1/2, 2/3, 3/4)                         ||
|  | - Interleaving, scrambling                                      ||
|  | - Preamble, Signal, Data symbols                                ||
|  +----------------------------------------------------------------+|
+-------------------------------------------------------------------+
|  RF Front-End (5.9 GHz)                                            |
|  +-------------------+  +-------------------+                     |
|  |  OBU (Vehicle)    |  |  RSU (Roadside)   |                     |
|  |  20-33 dBm        |  |  30-44 dBm        |                     |
|  +-------------------+  +-------------------+                     |
+-------------------------------------------------------------------+
```

## IEEE 802.11p Physical Layer

### OFDM Signal Generation

```c
/* IEEE 802.11p OFDM parameters for 10 MHz channel */
#define OFDM_NUM_SUBCARRIERS    52U     /* 48 data + 4 pilot */
#define OFDM_DATA_SUBCARRIERS   48U
#define OFDM_PILOT_SUBCARRIERS  4U
#define OFDM_GUARD_INTERVAL_US  1.6f    /* 1.6 µs guard interval */
#define OFDM_SYMBOL_DURATION_US 8.0f    /* 8 µs total symbol */

/* Modulation schemes per data rate */
typedef enum {
    MOD_BPSK_1_2,    /* 3 Mbps */
    MOD_QPSK_1_2,    /* 6 Mbps */
    MOD_QPSK_3_4,    /* 9 Mbps */
    MOD_16QAM_1_2,   /* 12 Mbps */
    MOD_16QAM_3_4,   /* 18 Mbps */
    MOD_64QAM_2_3,   /* 24 Mbps */
    MOD_64QAM_3_4    /* 27 Mbps */
} DsrcModulation_t;

typedef struct {
    DsrcModulation_t modulation;
    float coding_rate;
    uint8_t data_bits_per_symbol;
    uint8_t coded_bits_per_symbol;
} PhyConfig_t;

static const PhyConfig_t g_phy_configs[] = {
    { MOD_BPSK_1_2,   0.5f,  24,  48 },  /* 3 Mbps */
    { MOD_QPSK_1_2,   0.5f,  48,  96 },  /* 6 Mbps */
    { MOD_QPSK_3_4,   0.75f, 72,  96 },  /* 9 Mbps */
    { MOD_16QAM_1_2,  0.5f,  96,  192},  /* 12 Mbps */
    { MOD_16QAM_3_4,  0.75f, 144, 192},  /* 18 Mbps */
    { MOD_64QAM_2_3,  0.67f, 192, 288},  /* 24 Mbps */
    { MOD_64QAM_3_4,  0.75f, 216, 288}   /* 27 Mbps */
};

/* Generate OFDM symbol (simplified baseband model) */
typedef struct {
    complex_t subcarriers[OFDM_NUM_SUBCARRIERS];
    uint8_t pilot_values[4];  /* Known pilot symbols */
} OfdmSymbol_t;

void generate_ofdm_symbol(
    const uint8_t* coded_bits,
    size_t num_bits,
    PhyConfig_t config,
    OfdmSymbol_t* symbol) {

    /* Map coded bits to constellation points */
    for (size_t i = 0U; i < num_bits; i += config.coded_bits_per_symbol) {
        size_t symbol_idx = i / config.coded_bits_per_symbol;
        complex_t constellation;

        switch (config.modulation) {
            case MOD_BPSK_1_2:
                constellation = map_bpsk(coded_bits[i]);
                break;
            case MOD_QPSK_1_2:
            case MOD_QPSK_3_4:
                constellation = map_qpsk(coded_bits[i], coded_bits[i+1]);
                break;
            case MOD_16QAM_1_2:
            case MOD_16QAM_3_4:
                constellation = map_16qam(&coded_bits[i]);
                break;
            case MOD_64QAM_2_3:
            case MOD_64QAM_3_4:
                constellation = map_64qam(&coded_bits[i]);
                break;
        }

        /* Assign to data subcarrier (skip pilots) */
        size_t subcarrier_idx = get_data_subcarrier_index(symbol_idx);
        symbol->subcarriers[subcarrier_idx] = constellation;
    }

    /* Insert pilot symbols at fixed positions */
    insert_pilot_symbols(symbol);
}
```

### Signal Detection and Decoding

```c
/* Preamble detection using autocorrelation */
typedef struct {
    bool signal_detected;
    float frequency_offset_hz;
    float timing_offset_samples;
    float rssi_dbm;
} SignalDetectResult_t;

SignalDetectResult_t detect_80211p_signal(
    const complex_t* samples,
    size_t num_samples,
    float sample_rate_hz) {

    SignalDetectResult_t result = {0};

    /* Short training sequence detection (autocorrelation) */
    const size_t stf_period_samples = (size_t)(0.8e-6f * sample_rate_hz);
    float max_correlation = 0.0f;
    size_t peak_index = 0U;

    for (size_t n = 0U; n < num_samples - stf_period_samples; n++) {
        float correlation = 0.0f;
        for (size_t k = 0U; k < stf_period_samples; k++) {
            correlation += crealf(samples[n + k] * conjf(samples[n + k + stf_period_samples]));
        }
        if (correlation > max_correlation) {
            max_correlation = correlation;
            peak_index = n;
        }
    }

    /* Threshold detection */
    const float noise_power = estimate_noise_power(samples, num_samples);
    const float detection_threshold = noise_power * 6.0f;  /* ~8 dB SNR */

    if (max_correlation > detection_threshold) {
        result.signal_detected = true;
        result.timing_offset_samples = (float)peak_index;
        result.rssi_dbm = 10.0f * log10f(max_correlation / stf_period_samples);

        /* Estimate frequency offset using long training sequence */
        result.frequency_offset_hz = estimate_cfo(samples, peak_index, sample_rate_hz);
    }

    return result;
}
```

## IEEE 802.11p MAC Layer (EDCA)

### Access Category Configuration

```c
/* EDCA parameters per Access Category (IEEE 802.11p) */
typedef enum {
    AC_BK,  /* Background - AC0 */
    AC_BE,  /* Best Effort - AC1 */
    AC_VI,  /* Video - AC2 */
    AC_VO   /* Voice - AC3 (Safety messages) */
} AccessCategory_t;

typedef struct {
    uint16_t cwmin;       /* Minimum contention window */
    uint16_t cwmax;       /* Maximum contention window */
    uint8_t aifs;         /* Arbitration Inter-Frame Space */
    uint8_t txop_limit;   /* TXOP limit in slots */
} EdcaParams_t;

/* Default EDCA parameters for 802.11p */
static const EdcaParams_t g_edca_params[4] = {
    { .cwmin = 15, .cwmax = 1023, .aifs = 7, .txop_limit = 0 },  /* AC_BK */
    { .cwmin = 15, .cwmax = 1023, .aifs = 3, .txop_limit = 0 },  /* AC_BE */
    { .cwmin = 7,  .cwmax = 15,   .aifs = 2, .txop_limit = 0 },  /* AC_VI */
    { .cwmin = 3,  .cwmax = 7,    .aifs = 2, .txop_limit = 0 }   /* AC_VO (BSM) */
};

/* BSM messages use Voice AC (highest priority) */
#define BSM_ACCESS_CATEGORY  AC_VO
```

### Backoff Procedure

```c
typedef struct {
    uint16_t contention_window;
    uint16_t backoff_counter;
    uint8_t retry_count;
    bool backoff_frozen;
} MacState_t;

typedef struct {
    uint8_t* msdu;
    size_t msdu_length;
    AccessCategory_t ac;
    uint8_t queue_id;
} MacFrame_t;

/* EDCA backoff for frame transmission */
MacTxResult_t edca_transmit_frame(
    MacState_t* state,
    const MacFrame_t* frame,
    const EdcaParams_t* params) {

    /* Initialize contention window */
    state->contention_window = params->cwmin;

    /* Random backoff selection */
    state->backoff_counter = random_uniform(0U, state->contention_window);
    state->backoff_frozen = false;

    /* Count down backoff while channel is idle */
    while (state->backoff_counter > 0U) {
        if (channel_is_idle()) {
            wait_slot_time();  /* 13 µs for 802.11p */
            state->backoff_counter--;
        } else {
            state->backoff_frozen = true;
            wait_until_channel_idle();
            wait_aifs(params->aifs);
            state->backoff_frozen = false;
        }
    }

    /* Transmit frame */
    MacTxResult_t result = phy_transmit(frame->msdu, frame->msdu_length);

    if (result == TX_SUCCESS) {
        state->retry_count = 0U;
        return TX_SUCCESS;
    } else {
        /* Exponential backoff on failure */
        state->retry_count++;
        if (state->retry_count <= 7U) {
            state->contention_window = min(
                (state->contention_window + 1U) * 2U - 1U,
                params->cwmax);
        }
        return TX_RETRY;
    }
}
```

## IEEE 1609.4 Multi-Channel Operation

### Channel Coordination

```c
/* Channel interval timing (synchronized via GPS/RTC) */
#define CCH_INTERVAL_MS    50U
#define SCH_INTERVAL_MS    50U
#define GUARD_INTERVAL_MS  4U
#define SYNC_INTERVAL_MS   100U  /* 10 Hz sync */

typedef enum {
    CHANNEL_CCH,      /* Control Channel (CH178) */
    CHANNEL_SCH1,     /* Service Channel 1 (CH172) */
    CHANNEL_SCH2,     /* Service Channel 2 (CH174) */
    CHANNEL_SCH3,     /* Service Channel 3 (CH176) */
    CHANNEL_SCH4,     /* Service Channel 4 (CH180) */
    CHANNEL_SCH5,     /* Service Channel 5 (CH182) */
    CHANNEL_SCH6      /* Service Channel 6 (CH184) */
} DsrcChannel_t;

#define CONTROL_CHANNEL  CH178  /* 5.890 GHz */

typedef struct {
    DsrcChannel_t current_channel;
    uint32_t interval_start_time_ms;
    uint8_t remaining_cch_intervals;
    bool in_guard_interval;
} ChannelCoordinator_t;

/* Channel switching state machine */
void channel_coordinator_tick(
    ChannelCoordinator_t* coord,
    uint32_t current_time_ms) {

    uint32_t elapsed = current_time_ms - coord->interval_start_time_ms;

    /* Check if interval boundary reached */
    if (elapsed >= (CCH_INTERVAL_MS - GUARD_INTERVAL_MS)) {
        if (coord->current_channel == CHANNEL_CCH) {
            /* Switch to SCH */
            coord->current_channel = coord->next_sch_channel;
            coord->interval_start_time_ms = current_time_ms;
        } else {
            /* Switch back to CCH */
            coord->current_channel = CHANNEL_CCH;
            coord->interval_start_time_ms = current_time_ms;
            coord->remaining_cch_intervals--;
        }
    }

    /* Guard interval handling */
    if (elapsed >= CCH_INTERVAL_MS) {
        coord->in_guard_interval = true;
        if (elapsed >= (CCH_INTERVAL_MS + GUARD_INTERVAL_MS)) {
            coord->in_guard_interval = false;
        }
    }
}
```

## BSM (Basic Safety Message) Structure

### SAE J2735 BSM Part I - Core Data

```c
/* BSM Part I - Mandatory vehicle state (per SAE J2735) */
typedef struct {
    /* Temporary ID (4-byte random, changes periodically) */
    uint8_t tmp_id[4];

    /* Vehicle position */
    int32_t latitude;           /* degrees * 1e-7, range: -90 to 90 */
    int32_t longitude;          /* degrees * 1e-7, range: -180 to 180 */
    int16_t elevation;          /* meters * 5, offset: -4000 */
    uint8_t elevation_quality;  /* 0 = unavailable, 1-7 = quality levels */

    /* Motion state */
    uint16_t speed;             /* cm/s * 2, range: 0-280 km/h */
    int16_t heading;            /* degrees * 128, range: 0-359.9875 */
    int8_t steering_wheel_angle; /* degrees, range: -125 to 125 */

    /* Accelereration */
    int16_t accel_long;         /* m/s^2 * 100, range: -6.47 to 6.47 */
    int16_t accel_lat;          /* m/s^2 * 100, range: -6.47 to 6.47 */
    int16_t accel_vert;         /* m/s^2 * 100, range: -6.47 to 6.47 */

    /* Brake system status */
    uint8_t brake_status;       /* Bitmask: wheel brakes, traction, ABS */
    /* Bit 0: Wheel brakes applied (left side) */
    /* Bit 1: Wheel brakes applied (right side) */
    /* Bit 2: Traction control loss */
    /* Bit 3: ABS activated */
    /* Bit 4: Auxiliary brakes engaged */
    /* Bit 5-7: Reserved */

    /* Vehicle size */
    uint8_t vehicle_length;     /* meters, offset: -5, range: -5 to 251 */
    uint8_t vehicle_width;      /* meters * 0.1, offset: -10, range: -10 to 200.4 */
} BsmPartI_t;

#define BSM_PART1_ENCODED_SIZE  68U  /* bytes */
```

### BSM Part II - Optional Vehicle Events

```c
/* BSM Part II - Optional data elements */
typedef struct {
    uint8_t part2_count;
    uint8_t part2_data[64];  /* Variable, max 64 bytes typical */
} BsmPartII_t;

/* Common Part II data elements */
typedef struct {
    /* Path history (trajectory, up to 23 points) */
    struct {
        int16_t latitude_offset;   /* 1/10 micro-degree */
        int16_t longitude_offset;  /* 1/10 micro-degree */
        int16_t elevation_offset;  /* 2 meters */
        uint16_t time_offset;      /* milliseconds */
    } path_point[23];
    uint8_t path_point_count;

    /* Path prediction (projected path, 2 points) */
    struct {
        int16_t radius;        /* meters * 0.01 */
        int8_t confidence;     /* degrees * 0.25 */
    } path_prediction[2];

    /* Vehicle safety alerts */
    struct {
        bool event_antilock_brake_active;
        bool event_traction_control_lost;
        bool event_stability_control_active;
        bool event_hard_braking;
        bool event_abs_event;
        bool event_sudden_stop;
        bool event_strike_object;
    } vehicle_events;

    /* Extended vehicle data */
    int16_t outside_temp;      /* Celsius * 0.5, range: -40 to 85 */
    uint8_t traction_confidence;  /* 0-100 percent */
    int16_t yaw_rate;          /* degrees/s * 0.05 */
} BsmExtendedData_t;
```

### BSM Generation and Encoding

```c
/* BSM message generation (10 Hz) */
void generate_bsm_part1(
    const VehicleState_t* vehicle,
    BsmPartI_t* bsm) {

    /* Generate rotating temporary ID */
    update_temporary_id(bsm->tmp_id);

    /* Encode position */
    bsm->latitude = (int32_t)(vehicle->latitude_deg * 1e7);
    bsm->longitude = (int32_t)(vehicle->longitude_deg * 1e7);
    bsm->elevation = (int16_t)((vehicle->elevation_m + 4000.0f) / 5.0f);
    bsm->elevation_quality = 7U;  /* Highest quality (RTK GPS) */

    /* Encode motion */
    bsm->speed = (uint16_t)(vehicle->speed_ms * 200.0f);  /* cm/s * 2 */
    bsm->heading = (int16_t)(fmodf(vehicle->heading_deg, 360.0f) * 128.0f);
    bsm->steering_wheel_angle = (int8_t)vehicle->steering_angle_deg;

    /* Encode acceleration */
    bsm->accel_long = (int16_t)(vehicle->accel_longitudinal_ms2 * 100.0f);
    bsm->accel_lat = (int16_t)(vehicle->accel_lateral_ms2 * 100.0f);
    bsm->accel_vert = (int16_t)(vehicle->accel_vertical_ms2 * 100.0f);

    /* Encode brake status */
    bsm->brake_status = 0U;
    if (vehicle->brake_applied_left)  bsm->brake_status |= (1U << 0);
    if (vehicle->brake_applied_right) bsm->brake_status |= (1U << 1);
    if (vehicle->traction_loss)       bsm->brake_status |= (1U << 2);
    if (vehicle->abs_active)          bsm->brake_status |= (1U << 3);
    if (vehicle->aux_brake_engaged)   bsm->brake_status |= (1U << 4);

    /* Encode vehicle size */
    bsm->vehicle_length = (uint8_t)(vehicle->length_m + 5.0f);
    bsm->vehicle_width = (uint8_t)((vehicle->width_m + 10.0f) * 10.0f);
}

/* ASN.1 UPER encoding (simplified) */
size_t encode_bsm_part1_uper(
    const BsmPartI_t* bsm,
    uint8_t* output_buffer,
    size_t buffer_size) {

    if (buffer_size < BSM_PART1_ENCODED_SIZE) {
        return 0U;
    }

    BitStream_t bs;
    bitstream_init(&bs, output_buffer, buffer_size);

    /* Encode temporary ID (32 bits) */
    bitstream_write_bytes(&bs, bsm->tmp_id, 4U);

    /* Encode latitude (37 bits signed) */
    bitstream_write_signed(&bs, bsm->latitude, 37);

    /* Encode longitude (37 bits signed) */
    bitstream_write_signed(&bs, bsm->longitude, 37);

    /* Encode elevation (16 bits unsigned, offset binary) */
    bitstream_write_unsigned(&bs, (uint16_t)bsm->elevation, 16);

    /* ... continue encoding all fields per SAE J2735 ASN.1 spec ... */

    return bitstream_get_length(&bs);
}
```

## WSM (WAVE Short Message) Handling

### WSM Format (IEEE 1609.3)

```c
/* WSM header structure */
typedef struct {
    uint8_t version;         /* WSM version (currently 1) */
    uint8_t security_level;  /* 0 = no security, 1-3 = security levels */
    uint16_t length;         /* Total WSM length */
    uint8_t channel;         /* Channel number */
    uint8_t data_rate;       /* Data rate index */
} WsmHeader_t;

/* Complete WSM packet */
typedef struct {
    WsmHeader_t header;
    uint8_t wsmp_payload[256];  /* BSM or other WSMP data */
    size_t payload_length;
} WsmPacket_t;

#define WSM_OVERHEAD_BYTES  16U  /* Header + overhead */
#define MAX_WSM_PAYLOAD     256U
```

### WSM Transmission

```c
/* Build and transmit WSM on control channel */
typedef struct {
    uint8_t* payload;
    size_t payload_length;
    AccessCategory_t ac;
    uint32_t expiry_time_ms;  /* Message validity timeout */
} WsmTransmitRequest_t;

WsmTxResult_t transmit_wsm(
    const WsmTransmitRequest_t* request) {

    /* Build WSM header */
    WsmPacket_t wsm;
    wsm.header.version = 1U;
    wsm.header.security_level = 3U;  /* Full security (IEEE 1609.2) */
    wsm.header.channel = CONTROL_CHANNEL;
    wsm.header.data_rate = 3U;  /* 12 Mbps for BSM */
    wsm.header.length = (uint16_t)(WSM_OVERHEAD_BYTES + request->payload_length);

    /* Copy payload */
    memcpy(wsm.wsmp_payload, request->payload, request->payload_length);
    wsm.payload_length = request->payload_length;

    /* Check channel state */
    if (g_channel_coordinator.current_channel != CHANNEL_CCH) {
        /* Queue for next CCH interval */
        return WSM_QUEUED;
    }

    /* Encode and transmit */
    uint8_t encoded_packet[300];
    size_t encoded_length = encode_wsm(&wsm, encoded_packet, sizeof(encoded_packet));

    return phy_tx_request(encoded_packet, encoded_length, request->ac);
}
```

## IEEE 1609.2 Security for DSRC

### Certificate-Based Authentication

```c
/* IEEE 1609.2 certificate structure */
typedef struct {
    uint8_t version;
    uint8_t issuer[32];        /* Issuer ID hash */
    uint8_t subject[32];       /* Subject (ECU) ID hash */
    uint8_t public_key[65];    /* ECDSA P-256 public key (uncompressed) */
    uint32_t valid_from;       /* Validity start time */
    uint32_t valid_until;      /* Validity end time */
    uint8_t permissions[16];   /* Certificate permissions (PSID list) */
    uint8_t signature[64];     /* ECDSA P-256 signature */
} Ieee1609Certificate_t;

#define CERT_SIZE_BYTES  256U
```

### BSM Signing

```c
/* Sign BSM with IEEE 1609.2 ECDSA P-256 */
typedef struct {
    uint8_t signer_info_type;  /* 1 = certificate, 2 = certificate digest */
    union {
        Ieee1609Certificate_t cert;
        uint8_t cert_digest[32];  /* SHA-256 hash */
    } signer;
    uint8_t signature[64];     /* ECDSA P-256 (r, s) */
} SignedBsm_t;

bool sign_bsm(
    const BsmPartI_t* bsm_part1,
    const BsmPartII_t* bsm_part2,
    const HsmKeyHandle_t* private_key,
    const Ieee1609Certificate_t* cert,
    SignedBsm_t* signed_bsm) {

    /* Build hash of BSM data */
    uint8_t bsm_hash[32];
    sha256_compute_context_t ctx;
    sha256_init(&ctx);
    sha256_update(&ctx, bsm_part1, BSM_PART1_ENCODED_SIZE);
    if (bsm_part2 != NULL) {
        sha256_update(&ctx, bsm_part2->part2_data, bsm_part2->part2_count);
    }
    sha256_final(&ctx, bsm_hash);

    /* Sign hash using HSM (private key never leaves HSM) */
    uint8_t signature[64];
    if (!hsm_ecdsa_sign(private_key, bsm_hash, 32U, signature)) {
        return false;
    }

    /* Build signed structure */
    signed_bsm->signer_info_type = 2U;  /* Use digest (saves bandwidth) */
    sha256_compute(cert, CERT_SIZE_BYTES, signed_bsm->signer.cert_digest);
    memcpy(signed_bsm->signature, signature, 64U);

    return true;
}
```

### Certificate Validation

```c
/* Validate received BSM signature */
typedef enum {
    SIGNATURE_VALID,
    SIGNATURE_INVALID,
    CERTIFICATE_EXPIRED,
    CERTIFICATE_NOT_YET_VALID,
    CERTIFICATE_REVOKED,
    CERTIFICATE_UNKNOWN_ISSUER,
    CERTIFICATE_PERMISSION_DENIED
} SignatureValidation_t;

SignatureValidation_t validate_signed_bsm(
    const SignedBsm_t* signed_bsm,
    const uint8_t* bsm_data,
    size_t bsm_length,
    uint32_t current_time) {

    /* Step 1: Reconstruct certificate from stored CA or retrieve */
    Ieee1609Certificate_t cert;
    if (signed_bsm->signer_info_type == 2U) {
        /* Look up certificate by digest */
        if (!find_certificate_by_digest(
                signed_bsm->signer.cert_digest, &cert)) {
            return CERTIFICATE_UNKNOWN_ISSUER;
        }
    } else {
        cert = signed_bsm->signer.cert;
    }

    /* Step 2: Verify certificate validity period */
    if (current_time < cert.valid_from) {
        return CERTIFICATE_NOT_YET_VALID;
    }
    if (current_time > cert.valid_until) {
        return CERTIFICATE_EXPIRED;
    }

    /* Step 3: Check CRL for revocation */
    if (is_certificate_revoked(&cert)) {
        return CERTIFICATE_REVOKED;
    }

    /* Step 4: Verify certificate chain */
    if (!verify_certificate_chain(&cert, g_root_ca_certs)) {
        return CERTIFICATE_UNKNOWN_ISSUER;
    }

    /* Step 5: Verify BSM permissions */
    if (!check_psid_permission(&cert, PSID_SAFETY)) {
        return CERTIFICATE_PERMISSION_DENIED;
    }

    /* Step 6: Compute BSM hash */
    uint8_t bsm_hash[32];
    sha256_compute(bsm_data, bsm_length, bsm_hash);

    /* Step 7: Verify ECDSA P-256 signature */
    if (!hsm_ecdsa_verify(
            &cert.public_key, bsm_hash, 32U, signed_bsm->signature)) {
        return SIGNATURE_INVALID;
    }

    return SIGNATURE_VALID;
}
```

## AUTOSAR Implementation

### DSRCCommunicationManager SwComponent

```xml
<!-- AUTOSAR SwComponentType for DSRC -->
<APPLICATION-SW-COMPONENT-TYPE>
  <SHORT-NAME>DSRCCommunicationManager</SHORT-NAME>

  <!-- Port Interfaces -->
  <PORTS>
    <!-- Vehicle dynamics input -->
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>VehicleDynamicsPort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/VehicleDynamics_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <!-- GNSS position input -->
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>GnssPositionPort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/GnssPosition_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <!-- WSM transmit output -->
    <P-PORT-PROTOTYPE>
      <SHORT-NAME>WsmTransmitPort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/WsmTransmit_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>

    <!-- WSM receive output -->
    <P-PORT-PROTOTYPE>
      <SHORT-NAME>WsmReceivePort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/WsmReceive_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>

    <!-- Security service interface -->
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>SecurityServicePort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="CLIENT-SERVER-INTERFACE">
        /NS/Interfaces/V2XSecurity_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>
  </PORTS>

  <!-- Internal Behavior -->
  <INTERNAL-BEHAVIOR>
    <RUNNABLE-ENTITIES>
      <!-- BSM generation: 10 Hz -->
      <RUNNABLE-ENTITY>
        <SHORT-NAME>BsmGeneration_100ms</SHORT-NAME>
        <BEGIN-PERIOD>0.100</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>

      <!-- WSM reception handler: event-driven -->
      <RUNNABLE-ENTITY>
        <SHORT-NAME>WsmReceptionHandler</SHORT-NAME>
        <EVENT-ALGORITHM>
          <RECEIVED-DATA-ELEMENT-PROTOTYPE>WsmReceivePort/WsmData</RECEIVED-DATA-ELEMENT-PROTOTYPE>
        </EVENT-ALGORITHM>
      </RUNNABLE-ENTITY>

      <!-- Certificate validation: 1 Hz -->
      <RUNNABLE-ENTITY>
        <SHORT-NAME>CertValidation_1s</SHORT-NAME>
        <BEGIN-PERIOD>1.000</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>
    </RUNNABLE-ENTITIES>
  </INTERNAL-BEHAVIOR>
</APPLICATION-SW-COMPONENT-TYPE>
```

### Runnable Implementation

```c
/* BSM Generation Runnable (100ms cycle) */
#include "Rte_DSRCCommunicationManager.h"

void DSRCCommunicationManager_BsmGeneration_100ms_Runnable(void) {
    /* Read vehicle dynamics */
    VehicleDynamics_t vehicle_dyn;
    Rte_Read_DSRCCommunicationManager_VehicleDynamicsPort_Value(&vehicle_dyn);

    /* Read GNSS position */
    GnssPosition_t gnss_pos;
    Rte_Read_DSRCCommunicationManager_GnssPositionPort_Value(&gnss_pos);

    /* Generate BSM Part I */
    BsmPartI_t bsm_part1;
    generate_bsm_part1_from_vehicle(&vehicle_dyn, &gnss_pos, &bsm_part1);

    /* Generate BSM Part II (if events active) */
    BsmPartII_t bsm_part2;
    bsm_part2.part2_count = 0U;
    if (vehicle_dyn.hard_braking || vehicle_dyn.abs_active) {
        encode_vehicle_events(&bsm_part2, &vehicle_dyn);
    }

    /* Sign BSM (IEEE 1609.2) */
    SignedBsm_t signed_bsm;
    if (!sign_bsm(&bsm_part1, &bsm_part2,
                  &g_private_key, &g_certificate, &signed_bsm)) {
        Dem_ReportErrorStatus(DSM_SIGN_FAILURE, DEM_EVENT_STATUS_FAILED);
        return;
    }

    /* Build WSM */
    WsmTransmitRequest_t wsm_req;
    wsm_req.payload = (uint8_t*)&signed_bsm;
    wsm_req.payload_length = sizeof(SignedBsm_t);
    wsm_req.ac = AC_VO;
    wsm_req.expiry_time_ms = get_time_ms() + 100U;

    /* Transmit WSM */
    WsmPacket_t wsm_tx;
    build_wsm_packet(&wsm_req, &wsm_tx);
    Rte_Write_DSRCCommunicationManager_WsmTransmitPort_Data(&wsm_tx);
}
```

## ISO 26262 Safety Mechanisms

### Dual-Channel Validation for ASIL C/D

```c
/* Dual-channel plausibility check for V2X-dependent functions */
typedef struct {
    BsmPartI_t local_bsm;       /* Locally generated BSM */
    BsmPartI_t remote_bsm;      /* Received BSM from vehicle */
    uint32_t timestamp_ms;
    bool local_valid;
    bool remote_valid;
    float plausibility_distance_m;
} DualChannelValidation_t;

/* Plausibility check between local perception and received BSM */
bool validate_bsm_plausibility(
    const DualChannelValidation_t* validation,
    float max_plausibility_distance_m,
    float max_speed_delta_ms,
    float max_heading_delta_deg) {

    if (!validation->local_valid || !validation->remote_valid) {
        return false;
    }

    /* Compute distance between positions */
    float distance_m = geodesic_distance(
        validation->local_bsm.latitude, validation->local_bsm.longitude,
        validation->remote_bsm.latitude, validation->remote_bsm.longitude);

    if (distance_m > max_plausibility_distance_m) {
        /* Vehicles too far apart - likely different vehicle */
        return false;
    }

    /* Compare speed */
    float local_speed_ms = (float)validation->local_bsm.speed / 200.0f;
    float remote_speed_ms = (float)validation->remote_bsm.speed / 200.0f;
    float speed_delta_ms = fabsf(local_speed_ms - remote_speed_ms);

    if (speed_delta_ms > max_speed_delta_ms) {
        /* Speed mismatch - implausible */
        return false;
    }

    /* Compare heading */
    float local_heading_deg = (float)validation->local_bsm.heading / 128.0f;
    float remote_heading_deg = (float)validation->remote_bsm.heading / 128.0f;
    float heading_delta_deg = fabsf(angle_difference(
        local_heading_deg, remote_heading_deg));

    if (heading_delta_deg > max_heading_delta_deg) {
        /* Heading mismatch - implausible */
        return false;
    }

    /* Passed all plausibility checks */
    return true;
}

/* Safe state reaction on validation failure */
void handle_bsm_validation_failure(
    const DualChannelValidation_t* validation,
    FailureType_t failure_type) {

    switch (failure_type) {
        case SIGNATURE_INVALID:
            /* Security failure - discard message */
            discard_unauthenticated_bsm();
            break;

        case PLAUSIBILITY_FAILURE:
            /* Implausible data - use degraded mode */
            enter_degraded_v2x_mode();
            break;

        case CERTIFICATE_REVOKED:
            /* Revoked certificate - report to backend */
            report_revoked_certificate(validation->remote_bsm.tmp_id);
            break;

        default:
            /* Generic failure */
            Dem_ReportErrorStatus(DSM_V2X_VALIDATION_FAILURE,
                                  DEM_EVENT_STATUS_FAILED);
            break;
    }
}
```

## Testing

### MIL Test: BSM Rate Validation

```matlab
% MATLAB/Simulink test: Verify BSM transmission at 10 Hz
function results = test_bsm_generation_rate()
    % Load model
    model = 'dsrc_bsm_generator';
    load_system(model);

    % Configure simulation
    set_param(model, 'StopTime', '10.0');  % 10 seconds
    set_param(model, 'FixedStep', '0.001'); % 1 ms step

    % Simulate constant vehicle state
    simIn = Simulink.SimulationInput(model);
    simIn = simIn.setVariable('vehicle_speed_ms', 30.0);
    simIn = simIn.setVariable('latitude_deg', 37.7749);
    simIn = simIn.setVariable('longitude_deg', -122.4194);

    simOut = sim(simIn);

    % Count BSM messages generated
    bsm_events = simOut.BsmTransmitEvent.Time;
    num_bsm = length(bsm_events);

    % Expected: 100 messages in 10 seconds (10 Hz)
    expected_bsm = 100;
    tolerance = 2;  % Allow small timing variation

    assert(num_bsm >= (expected_bsm - tolerance), ...
        sprintf('BSM count %d below expected %d', num_bsm, expected_bsm));
    assert(num_bsm <= (expected_bsm + tolerance), ...
        sprintf('BSM count %d above expected %d', num_bsm, expected_bsm));

    % Verify inter-message interval
    intervals = diff(bsm_events);
    mean_interval = mean(intervals);
    assert(abs(mean_interval - 0.1) < 0.01, ...
        sprintf('Mean BSM interval %.3f s, expected 0.1 s', mean_interval));

    results.bsm_count = num_bsm;
    results.mean_interval_s = mean_interval;
    results.test_passed = true;
end
```

### HIL Test: DSRC ECU Communication

```robot
*** Settings ***
Library    DsrcHilLibrary    bench_config=dsrc_bench01.yaml
Library    CanBusLibrary    interface=vector    channel=1
Suite Setup    Initialize DSRC HIL Bench
Suite Teardown    Shutdown DSRC HIL Bench

*** Test Cases ***
DSRC BSM Transmission At 10 Hz
    [Documentation]    Verify BSM generated every 100 ms
    [Tags]    regression    v2x    dsrc

    # Precondition: ECU powered, GPS simulated
    Set Gnss Simulator Position    37.7749    -122.4194    50.0
    Set Vehicle Speed    30.0    # m/s
    Sleep    500ms    # Allow system to stabilize

    # Monitor WSM transmit port for 2 seconds
    ${start_time}=    Get Timestamp Ms
    @{bsm_messages}=    Create List
    FOR    ${i}    IN RANGE    20
        ${wsm}=    Receive Wsm From Port    timeout=150ms
        Run Keyword Unless    ${wsm} == ${None}    Append To List    ${bsm_messages}    ${wsm}
    END
    ${end_time}=    Get Timestamp Ms

    # Verify message count
    ${num_messages}=    Get Length    ${bsm_messages}
    Should Be True    ${num_messages} >= 18
    ...    BSM count ${num_messages} below expected 20 in 2s

    # Verify BSM content
    ${first_bsm}=    Get From List    ${bsm_messages}    0
    ${bsm}=    Decode Bsm Part1    ${first_bsm}
    ${speed}=    Get Bsm Speed    ${bsm}
    Should Be True    ${speed} >= 106.0 and ${speed} <= 110.0
    ...    BSM speed ${speed} km/h not matching expected 108 km/h

DSRC WSM Reception And Validation
    [Documentation]    Verify received WSM validation
    [Tags]    regression    v2x    security

    # Inject signed BSM from simulated vehicle
    ${test_bsm}=    Generate Test Bsm
    ...    latitude=37.7750
    ...    longitude=-122.4195
    ...    speed_ms=25.0
    ${signed_bsm}=    Sign Bsm With Cert    ${test_bsm}    test_vehicle_cert.pem
    ${wsm}=    Build Wsm Packet    ${signed_bsm}

    # Inject via RF interface
    Inject Wsm Packet    ${wsm}    channel=CCH    rssi_dbm=-65

    # Verify ECU processes message
    Wait Until Keyword Succeeds    100ms    10ms
    ...    Verify Bsm In Received List    ${test_bsm.tmp_id}

    # Verify signature validation
    ${validation_result}=    Get Signature Validation Status    ${test_bsm.tmp_id}
    Should Be Equal    ${validation_result}    SIGNATURE_VALID

DSRC Channel Load Under High Density
    [Documentation]    Test DSRC under high vehicle density scenario
    [Tags]    performance    scalability

    # Simulate 50 vehicles transmitting BSM (worst-case scenario)
    FOR    ${i}    IN RANGE    50
        ${vehicle_bsm}=    Generate Test Bsm
        ...    latitude=${37.7749 + ${i}*0.0001}
        ...    longitude=${-122.4194 + ${i}*0.0001}
        ...    speed_ms=${20 + ${i}*0.5}
        Schedule Wsm Injection    ${vehicle_bsm}    offset_ms=${i*2}
    END

    # Execute injection burst
    Execute Scheduled Injections

    # Measure channel load
    Sleep    1s
    ${channel_load}=    Measure Channel Utilization
    Should Be True    ${channel_load} < 0.7
    ...    Channel load ${channel_load} exceeds 70% threshold

    # Verify ECU still processes own BSM
    ${own_bsm_count}=    Count Own Bsm Transmissions
    Should Be True    ${own_bsm_count} >= 9
    ...    ECU BSM rate degraded under load
```

## Related Context
- @context/skills/v2x/cv2x.md (C-V2X/PC5 sidelink - alternative to DSRC)
- @context/skills/security/iso-21434-compliance.md (TARA, threat analysis)
- @context/skills/safety/iso-26262-overview.md (ASIL classification, HARA)
- @context/skills/autosar/classic-platform.md (AUTOSAR SwComponent patterns)
- @context/skills/network/can-protocol.md (In-vehicle network contrast)

## Tools Required
| Tool | Purpose | Coverage |
|------|---------|----------|
| MATLAB/Simulink | BSM algorithm development, MIL testing | Model validation |
| Vector CANoe/CANalyzer | DSRC ECU testing, WSM analysis | HIL, bus analysis |
| dSPACE SCALEXIO | HIL simulation with DSRC channel emulation | Real-time HIL |
| Keysight/Anritsu Signal Generators | RF testing, 802.11p PHY validation | PHY layer testing |
| Polyspace/Klocwork | Static analysis (MISRA, security) | Code quality |
| AUTOSAR toolchain (DaVinci/ETAS) | SwComponent configuration, RTE generation | Integration |
| Wireshark with 802.11p dissector | WSM packet analysis | Protocol debugging |
| IEEE 1609.2 Test Tools | Certificate validation, security testing | Security compliance |