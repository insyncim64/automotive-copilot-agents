# Skill: C-V2X (Cellular Vehicle-to-Everything) Communication

## When to Activate
- User is developing C-V2X communication systems for automotive applications
- User needs to implement 3GPP-based V2X protocols (LTE-V2X, 5G V2X)
- User requests PC5 sidelink or Uu interface implementation patterns
- User is developing V2V, V2I, V2P, or V2N applications
- User needs CAM, DENM, or BSM message handling for C-V2X
- User asks about C-V2X security credential management
- User is implementing cooperative awareness or collision avoidance systems
- User needs AUTOSAR implementation patterns for V2X ECUs
- User asks about ISO 26262 safety mechanisms for V2X-dependent functions
- User requests 3GPP Release 14/15/16 V2X feature comparisons

## Standards Compliance
- **3GPP Release 14**: LTE-V2X initial specification (PC5 sidelink)
- **3GPP Release 15**: LTE-V2X enhanced features, 5G V2X introduction
- **3GPP Release 16**: 5G NR V2X (URLLC support, sidelink enhancements)
- **3GPP TS 22.185**: Service requirements for V2X services
- **3GPP TS 23.285**: Architecture enhancements for V2X services
- **3GPP TS 24.386**: PC5 signaling protocol
- **3GPP TS 36.300**: LTE overall description (V2X sidelink)
- **3GPP TS 38.300**: NR overall description (V2X sidelink)
- **ISO 26262:2018**: Functional safety for V2X-dependent functions (ASIL B/C/D)
- **ISO 21434:2021**: Cybersecurity for V2X communication systems
- **IEEE 1609.2**: Security services for V2X (applies to C-V2X messages)
- **SAE J2735**: Dedicated Short Range Communications (DSRC) Message Set Dictionary (BSM definition)
- **SAE J2945/1**: BSM Minimum Performance Requirements
- **ETSI TS 102 637-2**: V2X Applications; Cooperative Awareness Message (CAM)
- **ETSI TS 102 637-3**: V2X Applications; Decentralized Environmental Notification Message (DENM)
- **UN ECE R155**: Cybersecurity management system requirements
- **UN ECE R156**: Software update management system requirements
- **ASPICE Level 3**: Model-based development with comprehensive validation
- **AUTOSAR 4.4**: V2X communication stack architecture

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Operating frequency (LTE-V2X) | 5.850 - 5.925 | GHz |
| Operating frequency (5G V2X) | Sub-6 GHz, mmWave | GHz |
| PC5 communication range | Up to 1000 | meters |
| Uu communication range | Cellular coverage | kilometers |
| Message generation rate (CAM) | 1 - 100 | Hz |
| Message generation rate (DENM) | Event-triggered | Hz |
| Maximum latency (safety) | 3 - 100 | ms |
| Reliability (safety messages) | 90 - 99.999 | percent |
| Vehicle speed support | 0 - 250 | km/h |
| Security credential lifetime | 1 hour - 1 year | time |
| Certificate validation time | < 50 | ms |
| Message size (BSM) | 200 - 500 | bytes |
| Message size (CAM) | 300 - 800 | bytes |
| Message size (DENM) | 500 - 2000 | bytes |
| Position accuracy | < 1.5 | meters |
| Timing accuracy | < 50 | ms |

## C-V2X Architecture

```
+------------------------------------------------------------------+
|                    C-V2X Communication Modes                      |
|                                                                   |
|  +------------------+     +------------------+                   |
|  |    Vehicle 1     |     |    Vehicle 2     |                   |
|  |   (C-V2X ECU)    |<--->|   (C-V2X ECU)    |                   |
|  |                  |PC5  |                  |                   |
|  |  +------------+  |     |  +------------+  |                   |
|  |  | V2X App    |  |     |  | V2X App    |  |                   |
|  |  | (CAM/DENM) |  |     |  | (CAM/DENM) |  |                   |
|  |  +-----+------+  |     |  +-----+------+  |                   |
|  |        |         |     |        |         |                   |
|  |  +-----v------+  |     |  +-----v------+  |                   |
|  |  | PC5 Stack  |  |     |  | PC5 Stack  |  |                   |
|  |  +-----+------+  |     |  +-----+------+  |                   |
|  +--------+---------+     +--------+---------+                   |
|           |                          |                            |
|           |        V2V (Direct)       |                            |
|           +------------+-------------+                             |
|                        |                                          |
|           +------------v-------------+                            |
|           |        RSU (Roadside)    |                            |
|           |     (V2I Communication)  |                            |
|           +------------+-------------+                            |
|                        |                                          |
|           +------------v-------------+                            |
|           |      Cellular Network    |                            |
|           |     (Uu Interface)       |                            |
|           |    +----------------+    |                            |
|           |    | V2X Server     |    |                            |
|           |    | (V2N Apps)     |    |                            |
|           |    +----------------+    |                            |
|           +------------+-------------+                            |
|                        |                                          |
|           +------------v-------------+                            |
|           |   Pedestrian Device     |                             |
|           |   (V2P Communication)   |                             |
|           +-------------------------+                             |
+------------------------------------------------------------------+

Communication Modes:
- V2V (Vehicle-to-Vehicle): Direct PC5 sidelink for safety messages
- V2I (Vehicle-to-Infrastructure): PC5 or Uu for traffic signal info
- V2P (Vehicle-to-Pedestrian): PC5 for vulnerable road user alerts
- V2N (Vehicle-to-Network): Uu for cloud services, traffic info
```

## PC5 Sidelink Communication

### Resource Allocation Modes

```c
/* C-V2X PC5 resource allocation - Mode 3 vs Mode 4 */
typedef enum {
    RESOURCE_ALLOCATION_MODE_3,  /* eNB/gNB scheduled */
    RESOURCE_ALLOCATION_MODE_4   /* Autonomous selection */
} ResourceAllocationMode_t;

typedef enum {
    SENSE_RESULT_AVAILABLE,
    SENSE_RESULT_UNAVAILABLE,
    RESOURCE_RESELECTION_TRIGGERED,
    RESOURCE_CONGESTION_DETECTED
} SensingState_t;

/* Mode 4: Autonomous resource selection with sensing */
typedef struct {
    uint16_t subchannel_index;
    uint32_t resource_reservation_interval_ms;
    int16_t rssi_dbm;
    uint32_t last_used_timestamp;
    bool resource_selected;
} SubChannelInfo_t;

typedef struct {
    SubChannelInfo_t subchannels[MAX_SUBCHANNELS];
    uint32_t selection_counter;
    uint32_t reselection_counter;
    SensingState_t sensing_state;
} ResourcePool_t;

/* Sensing-based resource selection algorithm */
ResourceSelectionResult_t select_transmission_resource(
    ResourcePool_t* pool,
    uint32_t packet_priority,
    uint32_t packet_size_bytes,
    uint32_t transmission_interval_ms) {

    ResourceSelectionResult_t result = {0};

    /* Step 1: Identify candidate resources in selection window */
    uint32_t selection_window_start = get_current_subframe() + 4;
    uint32_t selection_window_end = selection_window_start +
                                    (packet_priority * 10);

    uint16_t candidate_count = 0;
    uint16_t candidate_resources[MAX_CANDIDATES];

    for (uint16_t subch = 0; subch < MAX_SUBCHANNELS; subch++) {
        SubChannelInfo_t* subch_info = &pool->subchannels[subch];

        /* Step 2: Exclude resources with high RSSI (occupied) */
        if (subch_info->rssi_dbm > RSSI_THRESHOLD_DBM) {
            continue;  /* Resource appears occupied */
        }

        /* Step 3: Check resource reservation */
        if (subch_info->resource_selected &&
            subch_info->resource_reservation_interval_ms ==
            transmission_interval_ms) {
            continue;  /* Resource reserved by other vehicle */
        }

        /* Step 4: Add to candidate set */
        candidate_resources[candidate_count++] = subch;

        if (candidate_count >= MIN_CANDIDATES) {
            break;
        }
    }

    /* Step 5: Random selection from candidate set */
    if (candidate_count > 0) {
        uint16_t selected_index = generate_random_index(candidate_count);
        result.subchannel = candidate_resources[selected_index];
        result.success = true;

        /* Update pool state */
        pool->subchannels[result.subchannel].resource_selected = true;
        pool->subchannels[result.subchannel].last_used_timestamp =
            get_current_subframe();
        pool->subchannels[result.subchannel].rssi_dbm =
            measure_rssi(result.subchannel);
    } else {
        /* No suitable resources - increase threshold and retry */
        result.success = false;
        result.congestion_level = CONGESTION_HIGH;
    }

    return result;
}
```

### Sidelink Control and Data Channels

```c
/* PSCCH (Physical Sidelink Control Channel) format */
typedef struct {
    uint16_t source_layer2_id;      /* 16-bit */
    uint16_t destination_layer2_id; /* 16-bit */
    uint8_t  modulation_coding_scheme;
    uint16_t resource_block_assignment;
    uint8_t  timing_advance;
    uint8_t  group_destination_id;
    uint16_t crc;
} ScpInformation_t;

/* PSSCH (Physical Sidelink Shared Channel) data */
typedef struct {
    V2xMessageType_t message_type;
    uint32_t message_length;
    uint8_t  payload[MAX_V2X_MESSAGE_SIZE];
    uint32_t transmission_timestamp;
    uint8_t  transmission_power_dbm;
} SidelinkData_t;

/* SCI (Sidelink Control Information) format 1 */
typedef struct {
    uint8_t  priority;                  /* 3 bits */
    uint8_t  resource_reservation;      /* 4 bits */
    uint16_t frequency_resource;        /* Resource block assignment */
    uint8_t  time_gap;                  /* Time between transmissions */
    uint8_t  modulation_coding_scheme;  /* 5 bits */
    uint8_t  retransmission_index;      /* 1 bit */
    uint8_t  reserved;                  /* Padding */
} SciFormat1_t;

/* Generate SCI for PSCCH transmission */
SciFormat1_t generate_sci_format1(
    uint8_t priority,
    uint16_t frequency_resource,
    uint8_t mcs_index,
    uint32_t reservation_interval_ms) {

    SciFormat1_t sci = {0};

    sci.priority = priority & 0x07;
    sci.frequency_resource = frequency_resource & 0x3FFF;
    sci.modulation_coding_scheme = mcs_index & 0x1F;
    sci.retransmission_index = 0;  /* Initial transmission */

    /* Convert reservation interval to index */
    if (reservation_interval_ms <= 0) {
        sci.resource_reservation = 0;  /* No reservation */
    } else if (reservation_interval_ms <= 20) {
        sci.resource_reservation = 1;
    } else if (reservation_interval_ms <= 50) {
        sci.resource_reservation = 2;
    } else if (reservation_interval_ms <= 100) {
        sci.resource_reservation = 3;
    } else if (reservation_interval_ms <= 200) {
        sci.resource_reservation = 4;
    } else {
        sci.resource_reservation = 5;  /* Maximum */
    }

    return sci;
}
```

## Uu Interface Communication

### V2N Service Architecture

```c
/* V2X application server communication via Uu */
typedef struct {
    uint32_t server_ip;
    uint16_t server_port;
    uint8_t  apn[32];
    bool     tls_enabled;
    uint32_t keepalive_interval_s;
} V2xServerConfig_t;

typedef enum {
    V2N_SERVICE_TRAFFIC_INFO,
    V2N_SERVICE_FLOATING_CAR_DATA,
    V2N_SERVICE_DYNAMIC_NAMING,
    V2N_SERVICE_SUBSCRIPTION
} V2nServiceType_t;

typedef struct {
    V2nServiceType_t service_type;
    uint32_t transaction_id;
    uint8_t  payload[MAX_V2N_PAYLOAD_SIZE];
    uint32_t payload_length;
    uint32_t timestamp;
} V2nMessage_t;

/* V2N message transmission via Uu */
V2nTransmitResult_t transmit_v2n_message(
    V2xServerConfig_t* server_config,
    V2nMessage_t* message) {

    V2nTransmitResult_t result = {0};

    /* Step 1: Establish PDP context / PDN connection */
    if (!pdn_connection_active(server_config->apn)) {
        if (!activate_pdn_connection(server_config->apn)) {
            result.error_code = V2N_ERROR_PDN_ACTIVATION_FAILED;
            return result;
        }
    }

    /* Step 2: Create socket (TCP or UDP) */
    int socket_fd;
    if (server_config->tls_enabled) {
        socket_fd = tls_socket_create();
    } else {
        socket_fd = tcp_socket_create();
    }

    if (socket_fd < 0) {
        result.error_code = V2N_ERROR_SOCKET_CREATION_FAILED;
        return result;
    }

    /* Step 3: Connect to V2X server */
    struct sockaddr_in server_addr;
    server_addr.sin_addr.s_addr = server_config->server_ip;
    server_addr.sin_port = htons(server_config->server_port);

    if (tcp_connect(socket_fd, &server_addr) != 0) {
        result.error_code = V2N_ERROR_CONNECTION_FAILED;
        socket_close(socket_fd);
        return result;
    }

    /* Step 4: Send V2N message */
    uint8_t tx_buffer[MAX_V2N_TX_BUFFER];
    uint32_t tx_length = encode_v2n_message(message, tx_buffer);

    int bytes_sent = tcp_send(socket_fd, tx_buffer, tx_length);
    if (bytes_sent < 0) {
        result.error_code = V2N_ERROR_TRANSMISSION_FAILED;
        socket_close(socket_fd);
        return result;
    }

    /* Step 5: Receive response (if expected) */
    V2nMessage_t response;
    if (message->expects_response) {
        uint8_t rx_buffer[MAX_V2N_RX_BUFFER];
        int bytes_received = tcp_receive(socket_fd, rx_buffer,
                                          sizeof(rx_buffer),
                                          RESPONSE_TIMEOUT_MS);
        if (bytes_received > 0) {
            decode_v2n_message(rx_buffer, bytes_received, &response);
            result.response = response;
            result.response_received = true;
        }
    }

    socket_close(socket_fd);
    result.success = true;
    return result;
}
```

## V2X Message Types

### CAM (Cooperative Awareness Message)

```c
/* ETSI TS 102 637-2: Cooperative Awareness Message */
typedef struct {
    /* Basic Container */
    uint8_t  station_type;            /* Vehicle, pedestrian, RSU */
    uint16_t reference_position_lat;   /* 10^-7 degrees */
    uint16_t reference_position_lon;   /* 10^-7 degrees */
    uint16_t position_confidence_ellipse;
    uint16_t altitude;                 /* decimeters */
    uint8_t  altitude_confidence;

    /* High Frequency Container */
    int16_t  speed;                    /* cm/s (signed) */
    uint8_t  speed_confidence;
    int16_t  heading;                  /* 0.1 degrees */
    uint8_t  heading_confidence;
    int16_t  acceleration_longitudinal; /* 0.01 m/s^2 */
    int16_t  acceleration_lateral;      /* 0.01 m/s^2 */
    uint8_t  acceleration_confidence;
    int16_t  yaw_rate;                 /* 0.01 degrees/s */
    uint8_t  yaw_rate_confidence;

    /* Low Frequency Container */
    uint16_t vehicle_length;           /* centimeters */
    uint16_t vehicle_width;            /* centimeters */
    uint8_t  vehicle_height;           /* 10 cm steps */
    uint8_t  vehicle_role;
    uint16_t exterior_lights;          /* Bitmask */
    uint16_t left_turn_signal;
    uint16_t right_turn_signal;
} CamMessage_t;

/* CAM generation - triggered by timer or event */
CamMessage_t generate_cam_message(
    const VehicleDynamics_t* dynamics,
    const VehicleConfig_t* config,
    uint32_t generation_interval_ms) {

    CamMessage_t cam = {0};

    /* Basic Container - static/slow-changing data */
    cam.station_type = STATION_TYPE_PASSENGER_CAR;
    cam.reference_position_lat =
        encode_latitude(dynamics->position.latitude_deg);
    cam.reference_position_lon =
        encode_longitude(dynamics->position.longitude_deg);
    cam.position_confidence_ellipse =
        compute_position_confidence(dynamics->gnss_quality);
    cam.altitude = (uint16_t)(dynamics->position.altitude_m * 10.0f);
    cam.altitude_confidence = ALTITUDE_CONFIDENCE_HIGH;

    /* High Frequency Container - fast-changing dynamics */
    cam.speed = (int16_t)(dynamics->speed_ms * 100.0f);
    cam.speed_confidence = SPEED_CONFIDENCE_HIGH;
    cam.heading = (int16_t)(dynamics->heading_deg * 10.0f) % 3600;
    cam.heading_confidence = HEADING_CONFIDENCE_HIGH;
    cam.acceleration_longitudinal =
        (int16_t)(dynamics->acceleration_longitudinal_mps2 * 100.0f);
    cam.acceleration_lateral =
        (int16_t)(dynamics->acceleration_lateral_mps2 * 100.0f);
    cam.acceleration_confidence = ACCELERATION_CONFIDENCE_HIGH;
    cam.yaw_rate = (int16_t)(dynamics->yaw_rate_deg_s * 100.0f);
    cam.yaw_rate_confidence = YAW_RATE_CONFIDENCE_HIGH;

    /* Low Frequency Container - static vehicle data */
    cam.vehicle_length = (uint16_t)(config->length_m * 100.0f);
    cam.vehicle_width = (uint16_t)(config->width_m * 100.0f);
    cam.vehicle_height = (uint8_t)(config->height_m * 10.0f);
    cam.vehicle_role = config->vehicle_role_code;
    cam.exterior_lights = dynamics->exterior_lights_bitmask;
    cam.left_turn_signal = dynamics->left_turn_signal_active;
    cam.right_turn_signal = dynamics->right_turn_signal_active;

    return cam;
}

/* CAM transmission rate control based on dynamics */
uint32_t determine_cam_generation_rate(
    const VehicleDynamics_t* dynamics,
    uint32_t base_rate_ms) {

    uint32_t rate_ms = base_rate_ms;

    /* Increase rate during high dynamics */
    if (dynamics->acceleration_longitudinal_mps2 > 3.0f ||
        dynamics->acceleration_longitudinal_mps2 < -3.0f) {
        rate_ms = 100;  /* 10 Hz during hard accel/brake */
    }
    else if (dynamics->yaw_rate_deg_s > 10.0f ||
             dynamics->yaw_rate_deg_s < -10.0f) {
        rate_ms = 100;  /* 10 Hz during sharp turning */
    }
    else if (dynamics->speed_ms > 30.0f) {  /* > 108 km/h */
        rate_ms = 200;  /* 5 Hz at high speed */
    }
    else if (dynamics->speed_ms > 15.0f) {  /* > 54 km/h */
        rate_ms = 500;  /* 2 Hz at medium speed */
    }
    else {
        rate_ms = 1000;  /* 1 Hz at low speed / stopped */
    }

    return rate_ms;
}
```

### DENM (Decentralized Environmental Notification Message)

```c
/* ETSI TS 102 637-3: Decentralized Environmental Notification Message */
typedef enum {
    DENM_EVENT_NONE,
    DENM_EVENT_VEHICLE_BREAKDOWN,
    DENM_EVENT_ACCIDENT,
    DENM_EVENT_ROAD_WORKS,
    DENM_EVENT_ADVERSE_WEATHER,
    DENM_EVENT_CONGESTION,
    DENM_EVENT_HAZARDOUS_LOCATION,
    DENM_EVENT_TEMPORARY_SLIPPERY_ROAD,
    DENM_EVENT_VEHICLE_IN_RESERVED,
    DENM_EVENT_ACCIDENT_AREA,
    DENM_EVENT_SHORT_TERM_WEATHER,
    DENM_EVENT_RISK_AREA
} DenmEventType_t;

typedef struct {
    uint16_t event_code;             /* DENM event type */
    uint32_t event_id;               /* Unique event identifier */
    uint32_t detection_timestamp;
    int16_t  event_position_lat;
    int16_t  event_position_lon;
    uint16_t event_position_confidence;
    uint8_t  event_type;
    uint8_t  event_sub_type;
    uint8_t  cause_code;
    uint8_t  severity;               /* 0-10 scale */
    uint32_t expiry_timestamp;
    uint16_t relevance_distance;     /* meters */
    uint8_t  transmission_interval;  /* seconds */
} DenmMessage_t;

/* DENM generation - event-triggered */
DenmMessage_t generate_denm_message(
    DenmEventType_t event_type,
    const VehicleDynamics_t* dynamics,
    uint32_t relevance_distance_m) {

    DenmMessage_t denm = {0};

    /* Management Container */
    denm.event_code = (uint16_t)event_type;
    denm.event_id = generate_unique_event_id();
    denm.detection_timestamp = get_current_time_ms();

    /* Situation Container */
    denm.event_position_lat =
        encode_latitude(dynamics->position.latitude_deg);
    denm.event_position_lon =
        encode_longitude(dynamics->position.longitude_deg);
    denm.event_position_confidence =
        compute_position_confidence(dynamics->gnss_quality);
    denm.event_type = map_to_event_type(event_type);
    denm.event_sub_type = 0;  /* Sub-classification if needed */
    denm.cause_code = map_to_cause_code(event_type);

    /* Location Container */
    denm.relevance_distance = (uint16_t)relevance_distance_m;

    /* ALACarte Container (optional, based on event type) */
    switch (event_type) {
        case DENM_EVENT_ACCIDENT:
            denm.severity = 10;  /* Highest severity */
            denm.transmission_interval = 1;  /* 1 second */
            break;
        case DENM_EVENT_VEHICLE_BREAKDOWN:
            denm.severity = 5;
            denm.transmission_interval = 5;  /* 5 seconds */
            break;
        case DENM_EVENT_ADVERSE_WEATHER:
            denm.severity = 3;
            denm.transmission_interval = 10;  /* 10 seconds */
            break;
        default:
            denm.severity = 1;
            denm.transmission_interval = 10;
            break;
    }

    /* Expiry time - based on event type */
    switch (event_type) {
        case DENM_EVENT_ACCIDENT:
            denm.expiry_timestamp = get_current_time_ms() + 3600000;  /* 1 hour */
            break;
        case DENM_EVENT_VEHICLE_BREAKDOWN:
            denm.expiry_timestamp = get_current_time_ms() + 1800000;  /* 30 min */
            break;
        case DENM_EVENT_ADVERSE_WEATHER:
            denm.expiry_timestamp = get_current_time_ms() + 7200000;  /* 2 hours */
            break;
        default:
            denm.expiry_timestamp = get_current_time_ms() + 300000;   /* 5 min */
            break;
    }

    return denm;
}

/* DENM state machine */
typedef enum {
    DENM_STATE_IDLE,
    DENM_STATE_GENERATION_TRIGGERED,
    DENM_STATE_TRANSMITTING,
    DENM_STATE_UPDATE_PHASE,
    DENM_STATE_NEGATIVE_ACK,
    DENM_STATE_TERMINATION
} DenmState_t;

void denm_state_machine(
    DenmState_t* state,
    DenmMessage_t* denm,
    uint32_t current_time_ms) {

    switch (*state) {
        case DENM_STATE_IDLE:
            /* Wait for event trigger */
            if (detect_denm_trigger_event()) {
                *state = DENM_STATE_GENERATION_TRIGGERED;
            }
            break;

        case DENM_STATE_GENERATION_TRIGGERED:
            /* Generate and start transmitting */
            *denm = generate_denm_message(
                get_detected_event_type(),
                get_current_dynamics(),
                get_relevance_distance());
            transmit_denm(denm);
            *state = DENM_STATE_TRANSMITTING;
            break;

        case DENM_STATE_TRANSMITTING:
            /* Continue periodic transmission */
            if (is_transmission_time(denm->transmission_interval)) {
                transmit_denm(denm);
            }
            /* Check for termination conditions */
            if (current_time_ms > denm->expiry_timestamp) {
                *state = DENM_STATE_TERMINATION;
            } else if (event_cleared()) {
                *state = DENM_STATE_NEGATIVE_ACK;
            }
            break;

        case DENM_STATE_NEGATIVE_ACK:
            /* Send final DENM with cancellation */
            denm->event_sub_type = 1;  /* Cancellation indicator */
            transmit_denm(denm);
            *state = DENM_STATE_TERMINATION;
            break;

        case DENM_STATE_TERMINATION:
            /* Clean up and return to idle */
            clear_denm_state();
            *state = DENM_STATE_IDLE;
            break;

        default:
            break;
    }
}
```

### BSM (Basic Safety Message) - SAE J2735

```c
/* SAE J2735: Basic Safety Message Part I */
typedef struct {
    /* Part I - Core data (transmitted at 10 Hz) */
    int32_t  latitude;           /* 10^-7 degrees */
    int32_t  longitude;          /* 10^-7 degrees */
    uint16_t elevation;          /* decimeters */
    uint8_t  accuracy_semi_major;
    uint8_t  accuracy_semi_minor;
    uint8_t  accuracy_orientation;
    uint16_t speed;              /* 0.02 m/s steps */
    uint16_t heading;            /* 0.125 degrees */
    uint16_t angle;              /* Vehicle angle */
    uint8_t  accel_set[4];       /* Long, lat, vert, yaw */
    uint8_t  brakes;             /* Brake status bitmask */
    uint8_t  vehicle_size[3];    /* Length, width, height */
} BsmPart1_t;

/* SAE J2735: Basic Safety Message Part II (optional elements) */
typedef struct {
    uint8_t  vehicle_role;       /* Not used, reserved */
    uint16_t exterior_lights;
    uint8_t  path_history_count;
    uint8_t  path_history[23][4]; /* Position offsets */
    uint8_t  path_prediction_count;
    uint8_t  path_prediction[2][4];
    uint16_t rtcm_count;
    uint8_t  rtcm_message[rtcm_count];
} BsmPart2_t;

/* BSM generation */
BsmPart1_t generate_bsm_part1(
    const VehicleDynamics_t* dynamics) {

    BsmPart1_t bsm = {0};

    /* Position */
    bsm.latitude = (int32_t)(dynamics->position.latitude_deg * 10000000.0);
    bsm.longitude = (int32_t)(dynamics->position.longitude_deg * 10000000.0);
    bsm.elevation = (uint16_t)(dynamics->position.altitude_m * 10.0f);

    /* Position accuracy */
    bsm.accuracy_semi_major =
        compute_accuracy_code(dynamics->gnss_position_error_m);
    bsm.accuracy_semi_minor = bsm.accuracy_semi_major;
    bsm.accuracy_orientation = 0;  /* Not used */

    /* Speed (0.02 m/s steps) */
    uint16_t speed_raw = (uint16_t)(dynamics->speed_ms / 0.02f);
    bsm.speed = (speed_raw > 8191) ? 8191 : speed_raw;  /* Max value */

    /* Heading (0.125 degrees) */
    uint16_t heading_raw = (uint16_t)(dynamics->heading_deg / 0.125f);
    bsm.heading = heading_raw % 2880;  /* 0-359.875 degrees */

    /* Vehicle angle */
    bsm.angle = 127;  /* Unavailable */

    /* Acceleration set */
    bsm.accel_set[0] = encode_acceleration(
        dynamics->acceleration_longitudinal_mps2);
    bsm.accel_set[1] = encode_acceleration(
        dynamics->acceleration_lateral_mps2);
    bsm.accel_set[2] = 127;  /* Vertical unavailable */
    bsm.accel_set[3] = encode_yaw_rate(dynamics->yaw_rate_deg_s);

    /* Brake status */
    bsm.brakes = encode_brake_status(dynamics->brake_status);

    /* Vehicle size */
    encode_vehicle_size(dynamics->vehicle_config, bsm.vehicle_size);

    return bsm;
}
```

## Security Credential Management

### Certificate Enrollment and Validation

```c
/* IEEE 1609.2 / ETSI TS 103 097: Certificate format for V2X */
typedef struct {
    uint8_t  issuer[32];          /* Issuer identifier (hash) */
    uint32_t subject_id;          /* Subject identifier */
    uint8_t  subject_public_key[64]; /* ECDSA P-256 public key */
    uint32_t valid_from;          /* Validity start timestamp */
    uint32_t valid_until;         /* Validity end timestamp */
    uint8_t  region_code[8];      /* Geometric region */
    uint8_t  assurance_level;    /* Certificate assurance level */
    uint8_t  app_permissions[16]; /* Authorized V2X applications */
    uint8_t  signature[64];      /* Issuer signature */
} V2xCertificate_t;

typedef struct {
    V2xCertificate_t certificates[MAX_CERT_POOL_SIZE];
    uint8_t  certificate_count;
    uint32_t last_crl_update;
    uint8_t  crl_bitmap[CRL_BITMAP_SIZE];  /* Revoked certificate bitmap */
} CredentialStore_t;

/* Certificate validation */
CertValidationResult_t validate_certificate(
    const V2xCertificate_t* cert,
    const CredentialStore_t* store,
    uint32_t current_timestamp) {

    CertValidationResult_t result = {0};

    /* Step 1: Check certificate format */
    if (cert->issuer[0] == 0x00) {
        result.valid = false;
        result.reason = CERT_FORMAT_INVALID;
        return result;
    }

    /* Step 2: Check validity period */
    if (current_timestamp < cert->valid_from) {
        result.valid = false;
        result.reason = CERT_NOT_YET_VALID;
        return result;
    }
    if (current_timestamp > cert->valid_until) {
        result.valid = false;
        result.reason = CERT_EXPIRED;
        return result;
    }

    /* Step 3: Check revocation (CRL) */
    uint32_t cert_index = compute_crl_index(cert->subject_id);
    if (cert_index < CRL_BITMAP_SIZE * 8) {
        uint8_t byte_index = cert_index / 8;
        uint8_t bit_index = cert_index % 8;
        if (store->crl_bitmap[byte_index] & (1 << bit_index)) {
            result.valid = false;
            result.reason = CERT_REVOKED;
            return result;
        }
    }

    /* Step 4: Verify signature (ECDSA P-256) */
    const uint8_t* issuer_public_key = get_issuer_public_key(cert->issuer);
    if (issuer_public_key == NULL) {
        result.valid = false;
        result.reason = CERT_ISSUER_UNKNOWN;
        return result;
    }

    if (!ecdsa_p256_verify(
            issuer_public_key,
            cert,
            offsetof(V2xCertificate_t, signature),
            cert->signature)) {
        result.valid = false;
        result.reason = CERT_SIGNATURE_INVALID;
        return result;
    }

    /* Step 5: Verify app permissions */
    if (!verify_app_permissions(
            cert->app_permissions,
            get_current_application_id())) {
        result.valid = false;
        result.reason = CERT_PERMISSION_DENIED;
        return result;
    }

    result.valid = true;
    return result;
}

/* Sign V2X message with private key from HSM */
V2xSignature_t sign_v2x_message(
    const uint8_t* message,
    size_t message_length,
    uint32_t private_key_slot) {

    V2xSignature_t signature = {0};

    /* Step 1: Compute hash of message */
    uint8_t message_hash[32];
    sha256_compute(message, message_length, message_hash);

    /* Step 2: Sign hash with ECDSA P-256 (HSM-protected key) */
    uint8_t r[32], s[32];
    if (!hsm_ecdsa_sign(private_key_slot, message_hash, 32, r, s)) {
        signature.valid = false;
        signature.error_code = SIGN_ERROR_HSM_FAILURE;
        return signature;
    }

    /* Step 3: Format signature */
    memcpy(signature.r, r, 32);
    memcpy(signature.s, s, 32);
    signature.valid = true;
    signature.timestamp = get_current_time_ms();

    return signature;
}
```

## AUTOSAR Implementation

### V2X Communication Stack

```
+----------------------------------------------------------+
|              V2X Application Layer                        |
|  +------------+  +------------+  +------------+          |
|  |   CAV      |  |   IC       |  |   V2P      |          |
|  |  (Coop     |  | (Intersect.|  | (Vulnerable |          |
|  |   Awareness)|  |   Control) |  |  Pedest.)  |          |
|  +------------+  +------------+  +------------+          |
+--------------------------|-------------------------------+
                           |
+--------------------------v-------------------------------+
|              V2X Message Handler                          |
|  +------------+  +------------+  +------------+          |
|  |   CAM      |  |   DENM     |  |   BSM      |          |
|  |  Handler   |  |  Handler   |  |  Handler   |          |
|  +------------+  +------------+  +------------+          |
+--------------------------|-------------------------------+
                           |
+--------------------------v-------------------------------+
|              Security Layer (IEEE 1609.2)                 |
|  +------------+  +------------+  +------------+          |
|  |   Sign     |  |   Verify   |  |   Cert     |          |
|  |   Messages |  |   Messages |  |   Store    |          |
|  +------------+  +------------+  +------------+          |
+--------------------------|-------------------------------+
                           |
+--------------------------v-------------------------------+
|              Networking & Transport (WAVE/IPv6)           |
|  +------------+  +------------+  +------------+          |
|  |   WSM      |  |   BTP      |  |   GeoNet   |          |
|  |  Encap/Decap| |  Ports     |  |  Routing   |          |
|  +------------+  +------------+  +------------+          |
+--------------------------|-------------------------------+
                           |
+--------------------------v-------------------------------+
|              Access Layer (PC5 / Uu)                      |
|  +------------+  +------------+                          |
|  |   PC5      |  |   Uu       |                          |
|  |  Sidelink  |  |  Cellular  |                          |
|  +------------+  +------------+                          |
+----------------------------------------------------------+
```

### V2X SwComponent Definition

```xml
<!-- V2X Communication SwComponentType (ARXML) -->
<APPLICATION-SW-COMPONENT-TYPE>
  <SHORT-NAME>V2XCommunicationManager</SHORT-NAME>

  <!-- Port Interfaces -->
  <PORTS>
    <!-- Vehicle Dynamics Input -->
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>VehicleDynamicsPort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/VehicleDynamics_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <!-- GNSS Position Input -->
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>GnssPositionPort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/GnssPosition_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <!-- PC5 Sidelink Output -->
    <P-PORT-PROTOTYPE>
      <SHORT-NAME>Pc5TransmitPort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/Pc5Sidelink_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>

    <!-- Uu Interface Output -->
    <P-PORT-PROTOTYPE>
      <SHORT-NAME>UuTransmitPort</SHORT-NAME>
      <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/UuCellular_IF
      </PROVIDED-INTERFACE-TREF>
    </P-PORT-PROTOTYPE>

    <!-- Received V2X Messages Input -->
    <R-PORT-PROTOTYPE>
      <SHORT-NAME>ReceivedMessagesPort</SHORT-NAME>
      <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
        /NS/Interfaces/ReceivedV2xMessages_IF
      </REQUIRED-INTERFACE-TREF>
    </R-PORT-PROTOTYPE>

    <!-- Security Service (Signing) -->
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
      <!-- CAM Generation Runnable (100ms base rate) -->
      <RUNNABLE-ENTITY>
        <SHORT-NAME>CamGeneration_100ms</SHORT-NAME>
        <BEGIN-PERIOD>0.1</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>

      <!-- DENM Event Handler (Event-triggered) -->
      <RUNNABLE-ENTITY>
        <SHORT-NAME>DenmEventHandler</SHORT-NAME>
        <EVENT-REF DEST="ASYNC-SENDER-RECEIVER-EVENT">
          /NS/Events/DenmTriggerEvent
        </EVENT-REF>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>

      <!-- PC5 Reception Handler (Interrupt-driven) -->
      <RUNNABLE-ENTITY>
        <SHORT-NAME>Pc5ReceptionHandler</SHORT-NAME>
        <EVENT-REF DEST="ASYNC-SENDER-RECEIVER-EVENT">
          /NS/Events/Pc5RxEvent
        </EVENT-REF>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>

      <!-- Certificate Validation Runnable (1s) -->
      <RUNNABLE-ENTITY>
        <SHORT-NAME>CertValidation_1s</SHORT-NAME>
        <BEGIN-PERIOD>1.0</BEGIN-PERIOD>
        <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
      </RUNNABLE-ENTITY>
    </RUNNABLE-ENTITIES>
  </INTERNAL-BEHAVIOR>
</APPLICATION-SW-COMPONENT-TYPE>
```

## ISO 26262 Safety Mechanisms

### V2X Message Plausibility Check

```c
/* ASIL B: V2X message plausibility validation */
typedef struct {
    int32_t  position_lat;
    int32_t  position_lon;
    uint16_t speed;
    uint16_t heading;
    uint32_t timestamp;
    uint8_t  confidence_level;
} ReceivedV2xData_t;

typedef struct {
    int32_t  own_position_lat;
    int32_t  own_position_lon;
    uint16_t own_speed;
    uint32_t own_timestamp;
} LocalData_t;

typedef enum {
    PLAUSIBLE,
    IMPLAUSIBLE_POSITION,
    IMPLAUSIBLE_SPEED,
    IMPLAUSIBLE_HEADING,
    STALE_MESSAGE,
    LOW_CONFIDENCE
} PlausibilityResult_t;

PlausibilityResult_t check_v2x_message_plausibility(
    const ReceivedV2xData_t* received,
    const LocalData_t* local) {

    /* Check 1: Position plausibility (distance check) */
    int32_t delta_lat = received->position_lat - local->own_position_lat;
    int32_t delta_lon = received->position_lon - local->own_position_lon;

    /* Approximate distance calculation (simplified for embedded) */
    int32_t distance_approx = abs(delta_lat) + abs(delta_lon);
    if (distance_approx > MAX_PLAUSIBLE_DISTANCE_DEGREES) {
        /* Message claims to be from impossibly far away */
        return IMPLAUSIBLE_POSITION;
    }

    /* Check 2: Speed plausibility */
    if (received->speed > MAX_VEHICLE_SPEED_RAW) {
        return IMPLAUSIBLE_SPEED;
    }

    /* Check 3: Heading plausibility */
    if (received->heading > MAX_HEADING_RAW) {
        return IMPLAUSIBLE_HEADING;
    }

    /* Check 4: Message freshness */
    uint32_t age_ms = local->own_timestamp - received->timestamp;
    if (age_ms > MAX_MESSAGE_AGE_MS) {
        return STALE_MESSAGE;
    }

    /* Check 5: Confidence level */
    if (received->confidence_level < MIN_CONFIDENCE_LEVEL) {
        return LOW_CONFIDENCE;
    }

    return PLAUSIBLE;
}

/* Dual-channel validation for ASIL C/D functions */
typedef struct {
    PlausibilityResult_t primary_result;
    PlausibilityResult_t monitor_result;
    bool agreement;
} DualChannelValidation_t;

DualChannelValidation_t dual_channel_v2x_validation(
    const ReceivedV2xData_t* received,
    const LocalData_t* local) {

    DualChannelValidation_t result = {0};

    /* Primary channel: Full plausibility check */
    result.primary_result = check_v2x_message_plausibility(received, local);

    /* Monitor channel: Simplified independent check */
    uint32_t age_ms = local->own_timestamp - received->timestamp;
    if (age_ms <= MAX_MESSAGE_AGE_MS &&
        received->speed <= MAX_VEHICLE_SPEED_RAW &&
        received->confidence_level >= MIN_CONFIDENCE_LEVEL) {
        result.monitor_result = PLAUSIBLE;
    } else {
        result.monitor_result = IMPLAUSIBLE_SPEED;  /* Generic failure */
    }

    /* Compare results */
    result.agreement = (result.primary_result == PLAUSIBLE &&
                        result.monitor_result == PLAUSIBLE) ||
                       (result.primary_result != PLAUSIBLE &&
                        result.monitor_result != PLAUSIBLE);

    return result;
}
```

### Message Integrity and Authentication

```c
/* Security check for received V2X messages */
typedef struct {
    bool signature_valid;
    bool certificate_valid;
    bool certificate_not_revoked;
    bool timestamp_fresh;
    bool position_plausible;
    bool overall_trust;
    uint8_t trust_level;  /* 0-100 scale */
} SecurityCheckResult_t;

SecurityCheckResult_t perform_v2x_security_check(
    const V2xMessage_t* message,
    const CredentialStore_t* cred_store,
    const LocalData_t* local) {

    SecurityCheckResult_t result = {0};
    uint8_t trust_score = 100;

    /* Step 1: Verify certificate */
    CertValidationResult_t cert_result =
        validate_certificate(&message->certificate, cred_store,
                             local->own_timestamp);
    result.certificate_valid = cert_result.valid;
    result.certificate_not_revoked =
        (cert_result.reason != CERT_REVOKED);

    if (!result.certificate_valid) {
        trust_score -= 50;
    }

    /* Step 2: Verify signature */
    result.signature_valid = verify_v2x_signature(
        message, &message->certificate);
    if (!result.signature_valid) {
        trust_score -= 30;
    }

    /* Step 3: Check timestamp freshness */
    uint32_t message_age = local->own_timestamp - message->generation_timestamp;
    result.timestamp_fresh = (message_age < MAX_MESSAGE_AGE_MS);
    if (!result.timestamp_fresh) {
        trust_score -= 10;
    }

    /* Step 4: Check position plausibility */
    ReceivedV2xData_t received_data = extract_v2x_data(message);
    LocalData_t local_data = *local;
    PlausibilityResult_t plaus_result =
        check_v2x_message_plausibility(&received_data, &local_data);
    result.position_plausible = (plaus_result == PLAUSIBLE);
    if (!result.position_plausible) {
        trust_score -= 20;
    }

    /* Step 5: Compute overall trust */
    result.overall_trust = (result.signature_valid &&
                            result.certificate_valid &&
                            result.certificate_not_revoked &&
                            result.timestamp_fresh);
    result.trust_level = trust_score;

    return result;
}
```

## Test Scenarios

### MIL Test (MATLAB/Simulink)

```matlab
% C-V2X CAM Generation Test - MIL
function results = test_cam_generation_mil()
    % Load model
    model = 'cv2x_cam_generator';
    load_system(model);

    % Configure simulation
    set_param(model, 'StopTime', '100');  % 100 seconds
    set_param(model, 'FixedStep', '0.001'); % 1 ms step

    % Test Case 1: Normal highway driving
    simIn = Simulink.SimulationInput(model);
    simIn = simIn.setVariable('vehicle_speed_mps', 30);  % 108 km/h
    simIn = simIn.setVariable('acceleration_mps2', 0);
    simIn = simIn.setVariable('yaw_rate_deg_s', 0);
    simIn = simIn.setVariable('gnss_quality', 1);  % High quality

    simOut = sim(simIn);

    % Verify CAM generation rate (should be 5 Hz at this speed)
    cam_messages = simOut.cam_messages.Data;
    cam_intervals = diff(cam_messages(:,1));  % Time between messages
    avg_interval = mean(cam_intervals);

    assert(abs(avg_interval - 0.2) < 0.05, ...
        'CAM interval should be ~200ms at highway speed');

    % Verify message content
    assert(all(cam_messages(:,2) <= 8191), ...
        'Speed field should not exceed maximum');
    assert(all(cam_messages(:,3) >= 0 & cam_messages(:,3) <= 2880), ...
        'Heading field should be in valid range');

    results.test1_highway_passed = true;

    % Test Case 2: Hard braking event
    simIn = Simulink.SimulationInput(model);
    simIn = simIn.setVariable('vehicle_speed_mps', 20);
    simIn = simIn.setVariable('acceleration_mps2', -5);  % Hard brake
    simIn = simIn.setVariable('yaw_rate_deg_s', 0);

    simOut = sim(simIn);

    % Verify increased CAM rate during hard braking
    cam_messages = simOut.cam_messages.Data;
    cam_intervals = diff(cam_messages(:,1));
    avg_interval = mean(cam_intervals);

    assert(abs(avg_interval - 0.1) < 0.05, ...
        'CAM interval should be ~100ms during hard braking');

    results.test2_braking_passed = true;
end
```

### HIL Test (Robot Framework)

```robot
*** Settings ***
Library    V2xTestLibrary    bench_config=v2x_bench01.yaml
Library    CanBusLibrary    interface=vector    channel=1
Suite Setup    Initialize V2X HIL Bench
Suite Teardown    Shutdown V2X HIL Bench

*** Test Cases ***
C-V2X CAM Transmission Rate Control
    [Documentation]    Verify CAM rate adapts to vehicle dynamics
    [Tags]    v2x    cam    regression

    # Precondition: ECU powered, PC5 interface active
    Wait Until Keyword Succeeds    5s    100ms
    ...    Verify V2X State    PC5_ACTIVE

    # Set vehicle dynamics: highway speed (108 km/h)
    Set Vehicle Speed    30.0    # m/s
    Set Acceleration    0.0
    Wait    2s

    # Measure CAM transmission rate
    ${cam_count}=    Count PC5 Messages    CAM    timeout=5s
    Should Be True    ${cam_count} >= 20 and ${cam_count} <= 30
    ...    CAM rate should be ~5 Hz at highway speed

    # Set vehicle dynamics: hard braking
    Set Acceleration    -5.0    # m/s^2
    Wait    2s

    # Verify increased CAM rate
    ${cam_count_braking}=    Count PC5 Messages    CAM    timeout=5s
    Should Be True    ${cam_count_braking} >= 40
    ...    CAM rate should increase to ~10 Hz during braking

C-V2X DENM Event Triggering
    [Documentation]    Verify DENM generated on accident detection
    [Tags]    v2x    denm    safety

    # Precondition: Normal driving
    Set Vehicle Speed    15.0
    Set Acceleration    0.0

    # Inject accident event (high deceleration + airbag trigger)
    Set Acceleration    -30.0    # Emergency braking
    Trigger Airbag Signal    TRUE

    # Verify DENM transmission within 100ms
    ${denm_messages}=    Get PC5 Messages    DENM    timeout=500ms
    Should Not Be Empty    ${denm_messages}
    ...    DENM should be transmitted on accident

    # Verify DENM content
    ${event_type}=    Get DENM Event Type    ${denm_messages}[0]
    Should Be Equal    ${event_type}    ACCIDENT

    ${severity}=    Get DENM Severity    ${denm_messages}[0]
    Should Be True    ${severity} >= 8
    ...    Accident should have high severity
```

## Approach

1. **Define V2X communication requirements**
   - Select C-V2X technology (LTE-V2X, 5G NR V2X)
   - Identify message types (CAM, DENM, BSM, SPaT, MAP)
   - Define communication modes (V2V, V2I, V2P, V2N)
   - Specify latency and reliability targets per use case

2. **Design V2X architecture**
   - PC5 sidelink resource allocation (Mode 3 or Mode 4)
   - Uu interface for V2N services
   - Security credential management architecture
   - AUTOSAR SWC decomposition

3. **Implement message generation and handling**
   - CAM generation with adaptive rate control
   - DENM state machine for event-triggered warnings
   - BSM Part I and Part II encoding
   - Message validation and plausibility checks

4. **Implement security layer**
   - Certificate enrollment and storage
   - Message signing (ECDSA P-256 via HSM)
   - Certificate validation and CRL checking
   - Trust level computation

5. **Integrate with AUTOSAR platform**
   - Configure V2X communication ports
   - Define runnables and timing
   - Generate RTE and integrate
   - Configure NVM for certificate storage

6. **Validate through testing**
   - MIL: Algorithm validation in Simulink
   - SIL: Code verification with plant models
   - HIL: Real-time ECU testing with V2X simulation
   - Field testing: Public road V2X trials

## Deliverables

- V2X communication architecture specification
- PC5/Uu interface implementation (C/C++)
- CAM/DENM/BSM message handlers
- Security credential management module
- AUTOSAR SWC integration code
- ISO 26262 safety mechanism implementation
- Test results (MIL/SIL/HIL/Field)
- Security certification evidence

## Related Context
- @context/skills/v2x/dsrc.md
- @context/skills/security/iso-21434-compliance.md
- @context/skills/safety/iso-26262-overview.md
- @context/skills/autosar/adaptive-platform.md

## Tools Required
- MATLAB/Simulink (algorithm development, MIL)
- Vector CANoe/CANalyzer (V2X message analysis)
- Keysight V2X test solutions (conformance testing)
- Cambridge Consultants C-Box (V2X simulation)
- AUTOSAR toolchain (DaVinci Configurator, EB Tresos)
- HSM tools (NXP HSM, Infineon OPTIGA)
- Static analyzer (Polyspace, Klocwork)
- dSPACE/ETAS HIL systems (V2X HIL testing)
