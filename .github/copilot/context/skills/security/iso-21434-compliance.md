# Skill: ISO 21434 Cybersecurity Compliance

## When to Activate
- User asks about automotive cybersecurity requirements or implementation
- User needs TARA (Threat Analysis and Risk Assessment) guidance
- User requests secure coding patterns for ECU software
- User is implementing SecOC, secure boot, or HSM integration
- User needs UN R155 CSMS or UN R156 SUMS compliance support
- User is designing intrusion detection systems or security monitoring

## Standards Compliance
- ISO/SAE 21434:2021 (Cybersecurity Engineering)
- UN Regulation No. 155 (CSMS - Cybersecurity Management System)
- UN Regulation No. 156 (SUMS - Software Update Management System)
- AUTOSAR SecOC (Secure Onboard Communication)
- ISO 26262 ASIL A/D (functional safety interaction)
- MISRA C:2012 / MISRA C++:2023 (secure coding)

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| TARA risk value | 1-10 | risk score |
| CVSS vulnerability score | 0.0-10.0 | severity |
| Key rotation interval | 1 day - 10 years | lifetime |
| MAC truncation size | 32-128 | bits |
| Certificate validity | 1-25 | years |
| Secure boot verification time | < 500 | ms |
| Intrusion detection latency | < 100 | ms |
| Security event log retention | Life + 10 | years |

## TARA Methodology (ISO 21434 Part 3)

### Asset Identification

```yaml
# Asset classification with security attributes
asset_001:
  name: "Vehicle speed signal"
  type: "Data"
  confidentiality: Low
  integrity: High        # Safety-critical
  availability: High     # Required for safe operation
  damage_scenario: "Manipulation could cause incorrect speedometer, affect cruise control"

asset_002:
  name: "Diagnostic session key"
  type: "Cryptographic key"
  confidentiality: High
  integrity: High
  availability: Medium
  damage_scenario: "Unauthorized access to vehicle reprogramming"

asset_003:
  name: "Firmware update package"
  type: "Software"
  confidentiality: Medium  # Proprietary algorithms
  integrity: Critical      # Malicious firmware could compromise safety
  availability: Low        # Update is not time-critical
  damage_scenario: "Malware installation, vehicle theft, safety function disable"
```

### Threat Scenarios (STRIDE Framework)

```yaml
# Threat identification with risk assessment
threat_001:
  name: "CAN message spoofing"
  asset: asset_001
  stride_category: "Spoofing"
  attack_path: "Attacker injects fake speed messages on CAN bus via OBD-II port"
  attack_feasibility: High  # Physical access to OBD-II port
  impact: High              # Could affect safety functions
  risk_value: 8             # Feasibility x Impact
  mitigation: "Implement CAN message authentication (SecOC)"

threat_002:
  name: "Firmware downgrade attack"
  asset: asset_003
  stride_category: "Tampering"
  attack_path: "Attacker replaces new firmware with old vulnerable version"
  attack_feasibility: Medium  # Requires diagnostic access
  impact: Critical            # Reintroduces known vulnerabilities
  risk_value: 9
  mitigation: "Anti-rollback protection with version monotonic counter"

threat_003:
  name: "Diagnostic session replay attack"
  asset: asset_002
  stride_category: "Replay"
  attack_path: "Attacker captures and replays diagnostic authentication messages"
  attack_feasibility: Medium
  impact: High  # Unauthorized vehicle access
  risk_value: 7
  mitigation: "Use challenge-response authentication with nonce"
```

### Risk Treatment Implementation

```c
/* Mitigation for threat_002: Anti-rollback protection */
#define VERSION_COUNTER_ADDRESS  0x0801F800  /* OTP region */

bool is_firmware_version_allowed(uint32_t firmware_version) {
    /* Read monotonic counter from OTP (one-time programmable memory) */
    uint32_t min_version = read_otp_counter(VERSION_COUNTER_ADDRESS);

    if (firmware_version < min_version) {
        log_security_event(SEC_EVENT_ROLLBACK_ATTEMPT, firmware_version);
        return false;
    }

    return true;
}

void update_minimum_firmware_version(uint32_t new_min_version) {
    uint32_t current_min = read_otp_counter(VERSION_COUNTER_ADDRESS);

    if (new_min_version > current_min) {
        /* Write to OTP - this is irreversible */
        write_otp_counter(VERSION_COUNTER_ADDRESS, new_min_version);
    }
}

/* Mitigation for threat_003: Challenge-response authentication */
typedef struct {
    uint8_t challenge[16];   /* Random nonce */
    uint32_t timestamp;
    uint8_t response[32];    /* HMAC-SHA256 of challenge */
} DiagAuthRequest_t;

bool authenticate_diagnostic_session(void) {
    DiagAuthRequest_t auth_req;

    /* 1. Generate random challenge using hardware RNG */
    if (!hw_rng_generate(auth_req.challenge, sizeof(auth_req.challenge))) {
        return false;
    }
    auth_req.timestamp = get_timestamp_ms();

    /* 2. Send challenge to diagnostic tool */
    send_diagnostic_message(DIAG_AUTH_CHALLENGE, &auth_req, sizeof(auth_req));

    /* 3. Wait for response (with timeout) */
    DiagAuthRequest_t auth_resp;
    if (!receive_diagnostic_message(&auth_resp, DIAG_AUTH_TIMEOUT_MS)) {
        return false;
    }

    /* 4. Verify timestamp freshness (prevent replay) */
    if ((get_timestamp_ms() - auth_resp.timestamp) > DIAG_AUTH_WINDOW_MS) {
        log_security_event(SEC_EVENT_STALE_AUTH_RESPONSE, 0);
        return false;
    }

    /* 5. Verify HMAC response using constant-time comparison */
    uint8_t expected_response[32];
    hmac_sha256(diagnostic_secret_key, sizeof(diagnostic_secret_key),
                auth_req.challenge, sizeof(auth_req.challenge),
                expected_response);

    return constant_time_compare(auth_resp.response, expected_response, 32);
}
```

## Secure Coding Patterns

### Input Validation (CAN Message Processing)

```c
/* Every external input must be validated at trust boundaries */
void process_can_message(uint32_t can_id, const uint8_t* data, uint8_t length) {
    /* 1. Validate CAN ID against whitelist */
    if (!is_authorized_can_id(can_id)) {
        log_security_event(SEC_EVENT_UNAUTHORIZED_CAN_ID, can_id);
        return;
    }

    /* 2. Validate message length */
    if (length != EXPECTED_SPEED_MSG_LENGTH) {
        log_security_event(SEC_EVENT_INVALID_LENGTH, length);
        return;
    }

    /* 3. Validate data range (physical plausibility) */
    uint16_t speed = ((uint16_t)data[0] << 8) | data[1];
    if (speed > MAX_PLAUSIBLE_SPEED_KMH) {
        log_security_event(SEC_EVENT_IMPLAUSIBLE_SPEED, speed);
        return;
    }

    /* 4. Verify message authentication code (SecOC) */
    if (!verify_can_mac(can_id, data, length)) {
        log_security_event(SEC_EVENT_MAC_FAILURE, can_id);
        return;
    }

    set_vehicle_speed(speed);
}
```

### Buffer Overflow Prevention

```c
/* COMPLIANT: Bounds-checked string operations */
void set_vin_number(const char* vin) {
    char vin_buffer[18] = {0};  /* 17 chars + null terminator */

    if (vin == NULL) {
        return;
    }

    size_t vin_len = strlen(vin);
    if (vin_len > 17) {
        log_security_event(SEC_EVENT_INVALID_VIN_LENGTH, vin_len);
        return;
    }

    strncpy(vin_buffer, vin, sizeof(vin_buffer) - 1);
    vin_buffer[sizeof(vin_buffer) - 1] = '\0';  /* Ensure null termination */

    /* Additional validation: VIN format check (ISO 3779) */
    if (validate_vin_format(vin_buffer)) {
        store_vin(vin_buffer);
    }
}
```

### Integer Overflow Protection

```c
/* Check for overflow BEFORE performing the operation */
bool safe_multiply_u32(uint32_t a, uint32_t b, uint32_t* result) {
    if (b != 0U && a > (UINT32_MAX / b)) {
        log_security_event(SEC_EVENT_INTEGER_OVERFLOW, a);
        return false;  /* Would overflow */
    }
    *result = a * b;
    return true;
}

bool safe_add_u32(uint32_t a, uint32_t b, uint32_t* result) {
    if (a > (UINT32_MAX - b)) {
        log_security_event(SEC_EVENT_INTEGER_OVERFLOW, b);
        return false;  /* Would overflow */
    }
    *result = a + b;
    return true;
}
```

## Cryptographic Requirements

### Secure Key Storage (HSM)

```c
/* Key never leaves Hardware Security Module */
typedef struct {
    uint32_t hsm_key_slot;  /* Reference to key in HSM */
    uint8_t key_id[16];     /* Logical key identifier */
    KeyType_t type;         /* AES, ECC, HMAC, etc. */
    KeyUsage_t usage;       /* Sign, verify, encrypt, decrypt */
} HsmKeyHandle_t;

/* GOOD: Key material never exposed to application */
bool sign_message_via_hsm(const HsmKeyHandle_t* key,
                           const uint8_t* data, size_t data_len,
                           uint8_t* signature, size_t* sig_len) {
    return hsm_ecdsa_sign(key->hsm_key_slot, data, data_len,
                           signature, sig_len);
}

/* BAD: Private key in application memory (PROHIBITED) */
/* bool sign_message_insecure(const uint8_t* private_key, ...) */
```

### Secure Random Number Generation

```c
/* Cryptographically secure RNG with health checks */
#include "mbedtls/entropy.h"
#include "mbedtls/ctr_drbg.h"

uint32_t generate_session_token(void) {
    mbedtls_entropy_context entropy;
    mbedtls_ctr_drbg_context ctr_drbg;
    uint32_t token;

    mbedtls_entropy_init(&entropy);
    mbedtls_ctr_drbg_init(&ctr_drbg);

    /* Seed with hardware entropy source */
    mbedtls_ctr_drbg_seed(&ctr_drbg, mbedtls_entropy_func, &entropy, NULL, 0);

    /* Generate cryptographically secure random token */
    mbedtls_ctr_drbg_random(&ctr_drbg, (uint8_t*)&token, sizeof(token));

    mbedtls_ctr_drbg_free(&ctr_drbg);
    mbedtls_entropy_free(&entropy);

    return token;
}
```

### Message Authentication Codes (SecOC)

```c
/* AUTOSAR SecOC - CAN message authentication using CMAC */
#include "mbedtls/cmac.h"

#define CMAC_KEY_SIZE 16
#define CMAC_OUTPUT_SIZE 8  /* Truncated to 64 bits for CAN bandwidth */

typedef struct {
    uint32_t can_id;
    uint8_t data[8];
    uint8_t mac[CMAC_OUTPUT_SIZE];
} SecureCANMessage_t;

bool generate_can_mac(SecureCANMessage_t* msg) {
    const mbedtls_cipher_info_t* cipher_info;
    uint8_t mac_full[16];

    cipher_info = mbedtls_cipher_info_from_type(MBEDTLS_CIPHER_AES_128_ECB);

    /* Build authenticated data = CAN ID + payload */
    uint8_t mac_input[12];
    memcpy(mac_input, &msg->can_id, 4);
    memcpy(mac_input + 4, msg->data, 8);

    /* Get MAC key from HSM (key never leaves HSM) */
    uint8_t mac_key[CMAC_KEY_SIZE];
    if (!hsm_get_mac_key(HSM_KEY_SLOT_CAN_MAC, mac_key, CMAC_KEY_SIZE)) {
        return false;
    }

    /* Compute CMAC */
    mbedtls_cipher_cmac(cipher_info, mac_key, CMAC_KEY_SIZE * 8,
                        mac_input, sizeof(mac_input), mac_full);

    /* Truncate to 64 bits for CAN bandwidth efficiency */
    memcpy(msg->mac, mac_full, CMAC_OUTPUT_SIZE);

    /* Zero out key material from RAM */
    mbedtls_platform_zeroize(mac_key, CMAC_KEY_SIZE);

    return true;
}

/* Constant-time MAC verification (prevent timing attacks) */
bool verify_can_mac(const SecureCANMessage_t* msg) {
    SecureCANMessage_t verify_msg;
    memcpy(&verify_msg, msg, sizeof(SecureCANMessage_t));

    if (!generate_can_mac(&verify_msg)) {
        return false;
    }

    return mbedtls_constant_time_memcmp(msg->mac, verify_msg.mac, CMAC_OUTPUT_SIZE) == 0;
}
```

## Secure Boot Chain

### Three-Stage Secure Boot

```
+-------------------+
|  ROM Bootloader   |  (Immutable, mask ROM)
|  - Verify Stage 2 |  Using fused OEM public key hash
+--------+----------+
         |
+--------v----------+
|  Stage 2 Loader   |  (Updatable, signed)
|  - HSM init       |
|  - Verify App     |  ECDSA signature verification
+--------+----------+
         |
+--------v----------+
|   Application     |  (Runtime integrity monitoring)
|  - Boot chain     |  Verify launch from secure bootloader
|    verification   |
+-------------------+
```

### Implementation Pattern

```c
/* Stage 2: Secure bootloader */
void secure_bootloader(void) {
    /* 1. Initialize HSM and verify integrity */
    hsm_init();
    if (!hsm_self_test()) {
        report_security_failure(FAILURE_HSM_INTEGRITY);
        enter_safe_mode();
        return;
    }

    /* 2. Verify application firmware signature */
    if (!verify_firmware_signature(APPLICATION_ADDR)) {
        /* Attempt rollback to previous version */
        if (!rollback_to_backup_firmware()) {
            enter_safe_mode();
            return;
        }
    }

    /* 3. Verify firmware has not been revoked (anti-rollback) */
    uint32_t firmware_version = read_firmware_version(APPLICATION_ADDR);
    if (firmware_version < get_minimum_allowed_version()) {
        log_security_event(SEC_EVENT_REVOKED_FIRMWARE, firmware_version);
        enter_safe_mode();
        return;
    }

    /* 4. Enable runtime security mechanisms */
    configure_watchdog();
    configure_memory_protection();

    /* 5. Jump to application */
    jump_to_application(APPLICATION_ADDR);
}

/* Application: Runtime integrity monitoring */
void application_init(void) {
    /* Verify we were launched from secure bootloader (anti-bypass) */
    if (!verify_boot_chain_integrity()) {
        trigger_security_reset();
    }

    /* Enable runtime protections */
    enable_stack_canary();
    configure_firewall_rules();

    /* Start security monitoring task */
    create_task(security_monitor_task, PRIORITY_HIGH);
}
```

## Incident Response

### Security Event Logging

```c
typedef enum {
    SEC_EVENT_UNAUTHORIZED_CAN_ID = 0x01,
    SEC_EVENT_MAC_FAILURE = 0x02,
    SEC_EVENT_CERT_VERIFICATION_FAILED = 0x03,
    SEC_EVENT_ROLLBACK_ATTEMPT = 0x04,
    SEC_EVENT_INTRUSION_DETECTED = 0x05,
    SEC_EVENT_DEBUG_ACCESS_ATTEMPT = 0x06
} SecurityEventType_t;

typedef struct {
    uint32_t timestamp;
    SecurityEventType_t event_type;
    uint32_t event_data;
    uint8_t severity;  /* 1=Info, 2=Warning, 3=Critical */
} SecurityEvent_t;

#define SECURITY_LOG_SIZE 100
static SecurityEvent_t security_log[SECURITY_LOG_SIZE];
static uint16_t log_index = 0;

void log_security_event(SecurityEventType_t event_type, uint32_t event_data) {
    SecurityEvent_t event = {
        .timestamp = get_timestamp_ms(),
        .event_type = event_type,
        .event_data = event_data,
        .severity = get_event_severity(event_type)
    };

    /* Store in circular buffer */
    security_log[log_index] = event;
    log_index = (log_index + 1) % SECURITY_LOG_SIZE;

    /* For critical events, trigger immediate response */
    if (event.severity == 3) {
        handle_critical_security_event(&event);
    }

    /* Write to non-volatile storage for forensics */
    if (event.severity >= 2) {
        write_security_event_to_flash(&event);
    }
}

void handle_critical_security_event(const SecurityEvent_t* event) {
    switch (event->event_type) {
        case SEC_EVENT_INTRUSION_DETECTED:
            /* Disable external interfaces */
            disable_can_communication();
            disable_ethernet_communication();
            /* Notify vehicle gateway ECU */
            send_intrusion_alert_to_gateway();
            break;

        case SEC_EVENT_ROLLBACK_ATTEMPT:
            /* Prevent boot of compromised firmware */
            enter_safe_mode();
            break;

        default:
            break;
    }
}
```

### Intrusion Detection

```c
/* Runtime integrity monitoring */
#define CODE_SECTION_START  0x08000000
#define CODE_SECTION_SIZE   0x00080000

uint32_t calculate_code_checksum(void) {
    const uint32_t* code = (const uint32_t*)CODE_SECTION_START;
    uint32_t checksum = 0;

    for (size_t i = 0; i < (CODE_SECTION_SIZE / sizeof(uint32_t)); i++) {
        checksum ^= code[i];
    }

    return checksum;
}

void integrity_monitor_task(void) {
    static uint32_t expected_checksum = 0;

    /* Calculate expected checksum at boot */
    if (expected_checksum == 0) {
        expected_checksum = calculate_code_checksum();
    }

    while (1) {
        /* Periodically verify code integrity */
        uint32_t current_checksum = calculate_code_checksum();

        if (current_checksum != expected_checksum) {
            log_security_event(SEC_EVENT_INTRUSION_DETECTED, current_checksum);
            trigger_security_reset();
        }

        task_delay(INTEGRITY_CHECK_INTERVAL_MS);
    }
}
```

## Secure Development Lifecycle (SDL)

### SDL Phases and Security Activities

```yaml
# Security activities integrated throughout development lifecycle
requirements_phase:
  activities:
    - "Define security requirements based on TARA"
    - "Identify cryptographic requirements"
    - "Define access control policies"

design_phase:
  activities:
    - "Security architecture review"
    - "Threat modeling (STRIDE framework)"
    - "Define secure communication protocols"

implementation_phase:
  activities:
    - "Secure coding training for developers"
    - "Static analysis (SAST) on every commit"
    - "Code review with security checklist"

testing_phase:
  activities:
    - "Penetration testing (authorized ethical hacking)"
    - "Fuzzing of external interfaces (CAN, Ethernet, USB)"
    - "Vulnerability scanning"

deployment_phase:
  activities:
    - "Secure key injection in manufacturing"
    - "Firmware signing and verification"
    - "Secure storage of audit logs"

maintenance_phase:
  activities:
    - "Security patch management"
    - "Vulnerability disclosure handling"
    - "Incident response procedures"
```

## Code Review Security Checklist

### Input Validation
- [ ] All external inputs validated (range, format, type)
- [ ] CAN message IDs checked against whitelist
- [ ] Buffer sizes verified before copy operations
- [ ] Integer overflow checked for arithmetic operations
- [ ] String inputs null-terminated and length-checked

### Cryptography
- [ ] No hardcoded keys or passwords
- [ ] Cryptographically secure RNG used (not rand())
- [ ] Keys stored in HSM or secure element
- [ ] Certificates validated (chain, expiration, revocation)
- [ ] Constant-time comparison for security-critical checks

### Authentication & Authorization
- [ ] Challenge-response authentication for diagnostic access
- [ ] Session tokens generated with sufficient entropy
- [ ] Privilege separation enforced (least privilege principle)
- [ ] Debug interfaces disabled in production builds
- [ ] Anti-replay mechanisms for security-critical messages

### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] Secure erase for deleted cryptographic material
- [ ] Memory not leaked through error messages
- [ ] Secrets not logged or transmitted in clear text

### Secure Boot
- [ ] Boot chain integrity verified at each stage
- [ ] Anti-rollback protection enforced
- [ ] Firmware signature validated before execution
- [ ] Recovery mode secured against bypass

### Error Handling
- [ ] Error messages do not leak sensitive information
- [ ] Security failures logged with sufficient detail
- [ ] System enters safe state on security failure
- [ ] Critical events trigger alerts to security monitoring

### Dependencies
- [ ] Third-party libraries scanned for known vulnerabilities (CVE)
- [ ] Library versions pinned (no floating dependencies)
- [ ] SBOM (Software Bill of Materials) updated
- [ ] License compliance verified

## Related Context
- @context/skills/safety/iso-26262-overview.md
- @context/skills/security/ota-update-security.md
- @context/skills/autosar/classic-platform.md
- @context/skills/autosar/adaptive-platform.md
- @context/skills/network/can-protocol.md
- @context/skills/safety/safety-mechanisms-patterns.md

## Tools Required
- Hardware Security Module (HSM) - Infineon OPTIGA, NXP EdgeLock
- Cryptographic library - mbedTLS, wolfSSL, AUTOSAR CryptoStack
- Static analysis - Polyspace, QAC, SonarQube
- Penetration testing - CANalyzer, Vehicle Spy, custom fuzzers
- HIL security testing - dSPACE, ETAS with fault injection
- Vulnerability scanning - Snyk, Black Duck, Dependabot
