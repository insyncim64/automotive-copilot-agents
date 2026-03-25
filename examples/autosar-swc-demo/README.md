# AUTOSAR Software Component Demo

This example project demonstrates the AUTOSAR Classic Platform software component development workflow for creating safety-critical ECU software components.

## Overview

This demo showcases:
- Software Component (SWC) definition with ports and interfaces
- Runnable entity implementation with timing constraints
- ARXML system description generation
- RTE (Runtime Environment) configuration
- ASIL-B safety classification
- End-to-end RTE generation workflow

## Project Structure

```
autosar-swc-demo/
├── README.md
├── arxml/
│   ├── system.arxml              # System description
│   ├── software-components/
│   │   ├── engine-control.arxml  # Engine control SWC
│   │   └── diagnostics.arxml     # Diagnostic SWC
│   ├── interfaces/
│   │   ├── sender-receiver.arxml # SR port interfaces
│   │   └── client-server.arxml   # CS port interfaces
│   └── ecu-extract/
│       └── engine-ecu.arxml      # ECU configuration
├── config/
│   ├── autosar/
│   │   └── AUTOSAR_R22-11.xsd    # AUTOSAR schema
│   ├── os/
│   │   └── tasks.yaml            # OS task configuration
│   ├── rte/
│   │   ├── rte-generation-config.yaml
│   │   └── expected-artifacts.yaml
│   └── hw/
│       ├── ecu-spec.yaml         # Target hardware specs
│       └── memory-budget.yaml    # Memory constraints
├── src/
│   ├── swc/
│   │   ├── engine-control/
│   │   │   ├── EngineControl.c   # SWC implementation
│   │   │   └── EngineControl.h
│   │   └── diagnostics/
│   │       ├── Diagnostics.c
│   │       └── Diagnostics.h
│   └── bsw/
│       └── placeholder.txt       # BSW stub implementations
├── tests/
│   ├── rte/
│   │   ├── unit/
│   │   │   ├── test_sr_transfer.cpp
│   │   │   └── test_cs_routing.cpp
│   │   └── test_runnables.cpp
│   └── mil/
│       └── test_state-machine.slx
├── scripts/
│   ├── generate-rte.sh           # RTE generation script
│   └── validate-arxml.py         # ARXML validation
└── results/
    └── placeholder.txt           # RTE generation results
```

## Prerequisites

1. **Hardware Requirements**:
   - x86_64 Linux workstation (for RTE generation)
   - 16 GB RAM minimum
   - 100 GB free disk space

2. **Software Requirements**:
   - Python 3.10+
   - CMake 3.25+
   - ARM GCC cross-compiler (for target build)
   - Vector DaVinci Configurator (optional, for ARXML editing)

3. **AUTOSAR Tools**:
   - AUTOSAR Classic Platform R22-11 schema files
   - RTE generator tool (e.g., DaVinci RTE Generator)
   - ARXML validator

4. **GitHub Actions Setup**:
   - Standard `ubuntu-latest` runner for validation and configuration
   - Self-hosted runner with ARM cross-compiler for integration build

## Configuration

### ARXML System Description

```xml
<?xml version="1.0" encoding="UTF-8"?>
<AUTOSAR xmlns="http://autosar.org/schema/r4.2.4">
  <AR-PACKAGE>
    <SHORT-NAME>OEM_Adamas_EngineControl</SHORT-NAME>
    <ELEMENTS>
      <!-- Application Software Component -->
      <APPLICATION-SW-COMPONENT-TYPE>
        <SHORT-NAME>EngCtrlSwComponentType</SHORT-NAME>
        <PORTS>
          <!-- Required Port: Vehicle Speed -->
          <R-PORT-PROTOTYPE>
            <SHORT-NAME>RP_VehicleSpeed</SHORT-NAME>
            <REQUIRED-COM-SPECIFICATION>
              <REQUIRED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
                /Interfaces/SR_VehicleSpeed
              </REQUIRED-INTERFACE-TREF>
            </REQUIRED-COM-SPECIFICATION>
          </R-PORT-PROTOTYPE>

          <!-- Provided Port: Engine Status -->
          <P-PORT-PROTOTYPE>
            <SHORT-NAME>PP_EngineStatus</SHORT-NAME>
            <PROVIDED-COM-SPECIFICATION>
              <PROVIDED-INTERFACE-TREF DEST="SENDER-RECEIVER-INTERFACE">
                /Interfaces/SR_EngineStatus
              </PROVIDED-INTERFACE-TREF>
            </PROVIDED-COM-SPECIFICATION>
          </P-PORT-PROTOTYPE>

          <!-- Client Port: Diagnostic Service -->
          <R-PORT-PROTOTYPE>
            <SHORT-NAME>RP_DiagnosticService</SHORT-NAME>
            <REQUIRED-COM-SPECIFICATION>
              <REQUIRED-INTERFACE-TREF DEST="CLIENT-SERVER-INTERFACE">
                /Interfaces/CS_DiagnosticService
              </REQUIRED-INTERFACE-TREF>
            </REQUIRED-COM-SPECIFICATION>
          </R-PORT-PROTOTYPE>
        </PORTS>
        <INTERNAL-BEHAVIOR>
          <SHORT-NAME>EngCtrlInternalBehavior</SHORT-NAME>
          <RUNNABLE-ENTITIES>
            <!-- 10ms cyclic runnable -->
            <MODE-SWITCH-RECEIVER-ENTITY>
              <SHORT-NAME>EngineControl_10ms</SHORT-NAME>
              <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
              <MINIMUM-START-INTERVAL>0.01</MINIMUM-START-INTERVAL>
            </MODE-SWITCH-RECEIVER-ENTITY>

            <!-- Event-triggered runnable -->
            <EVENT-RECEIVER-ENTITY>
              <SHORT-NAME>OnDTCRequested</SHORT-SHORT-NAME>
              <CAN-BE-INVOKED-CONCURRENTLY>false</CAN-BE-INVOKED-CONCURRENTLY>
            </EVENT-RECEIVER-ENTITY>
          </RUNNABLE-ENTITIES>
        </INTERNAL-BEHAVIOR>
      </APPLICATION-SW-COMPONENT-TYPE>
    </ELEMENTS>
  </AR-PACKAGE>
</AUTOSAR>
```

### Sender-Receiver Interface

```xml
<SENDER-RECEIVER-INTERFACE>
  <SHORT-NAME>SR_VehicleSpeed</SHORT-NAME>
  <DATA-ELEMENTS>
    <VARIABLE-DATA-PROTOTYPE>
      <SHORT-NAME>Value</SHORT-NAME>
      <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">
        /DataTypes/uint16
      </TYPE-TREF>
      <INIT-VALUE>
        <NUMERICAL-VALUE-SPECIFICATION>
          <VALUE>0</VALUE>
        </NUMERICAL-VALUE-SPECIFICATION>
      </INIT-VALUE>
    </VARIABLE-DATA-PROTOTYPE>
  </DATA-ELEMENTS>
  <MAINTAIN-ALIVE>true</MAINTAIN-ALIVE>
  <TRANSMISSION-MODE-DECLARATION-GROUP>
    <SHORT-NAME>DefaultMode</SHORT-NAME>
    <TRANSMISSION-MODE-TRUE-TIMING>
      <PERIOD>0.01</PERIOD>  <!-- 10ms cycle -->
    </TRANSMISSION-MODE-TRUE-TIMING>
  </TRANSMISSION-MODE-DECLARATION-GROUP>
</SENDER-RECEIVER-INTERFACE>
```

### Client-Server Interface

```xml
<CLIENT-SERVER-INTERFACE>
  <SHORT-NAME>CS_DiagnosticService</SHORT-NAME>
  <OPERATIONS>
    <CLIENT-SERVER-OPERATION>
      <SHORT-NAME>ReadDataByIdentifier</SHORT-NAME>
      <ARGUMENTS>
        <!-- Input: Data ID -->
        <ARGUMENT-DATA-PROTOTYPE>
          <SHORT-NAME>DataId</SHORT-NAME>
          <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">
            /DataTypes/uint16
          </TYPE-TREF>
          <DIRECTION>IN</DIRECTION>
        </ARGUMENT-DATA-PROTOTYPE>

        <!-- Output: Data buffer -->
        <ARGUMENT-DATA-PROTOTYPE>
          <SHORT-NAME>Data</SHORT-NAME>
          <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">
            /DataTypes/uint8_array
          </TYPE-TREF>
          <DIRECTION>OUT</DIRECTION>
        </ARGUMENT-DATA-PROTOTYPE>

        <!-- Output: Data length -->
        <ARGUMENT-DATA-PROTOTYPE>
          <SHORT-NAME>Length</SHORT-NAME>
          <TYPE-TREF DEST="IMPLEMENTATION-DATA-TYPE">
            /DataTypes/uint8
          </TYPE-TREF>
          <DIRECTION>OUT</DIRECTION>
        </ARGUMENT-DATA-PROTOTYPE>
      </ARGUMENTS>
    </CLIENT-SERVER-OPERATION>
  </OPERATIONS>
</CLIENT-SERVER-INTERFACE>
```

### RTE Configuration

```yaml
# config/rte/rte-generation-config.yaml
rte_generation:
  mode: full
  autosar_version: R22-11
  platform: Classic

  swc_list:
    - name: EngCtrlSwComponentType
      arxml: arxml/software-components/engine-control.arxml
    - name: DiagSwComponentType
      arxml: arxml/software-components/diagnostics.arxml

  port_configuration:
    queued_ports:
      - port: RP_VehicleSpeed
        queue_size: 2
        overwrite_oldest: true
      - port: PP_EngineStatus
        queue_size: 1
        overwrite_oldest: true

  consistency_mechanisms:
    atomic_read_write: true
    lock_free_buffers: true
    safety_level: ASIL-B

  code_generation_options:
    generate_sender_code: true
    generate_receiver_code: true
    generate_client_code: true
    generate_server_code: true
    generate_mode_switch_code: true
    optimize_for_speed: true
    generate_trace_hooks: false
```

### OS Task Configuration

```yaml
# config/os/tasks.yaml
os_tasks:
  - name: EngineControlTask_10ms
    type: cyclic
    priority: 5
    period_ms: 10
    deadline_ms: 10
    stack_size_bytes: 2048
    runnables:
      - EngCtrlSwComponentType/EngineControl_10ms
      - DiagSwComponentType/Heartbeat_10ms

  - name: DiagnosticTask_100ms
    type: event
    priority: 3
    period_ms: 100
    deadline_ms: 100
    stack_size_bytes: 4096
    runnables:
      - DiagSwComponentType/DTCManager_100ms

  - name: BackgroundTask
    type: background
    priority: 1
    stack_size_bytes: 1024
    runnables:
      - DiagSwComponentType/LogFlush
```

### Hardware Specification

```yaml
# config/hw/ecu-spec.yaml
target_hardware:
  mcu:
    manufacturer: Infineon
    part_number: TC397XP
    architecture: TriCore
    frequency_mhz: 300
    cores: 6
    lockstep_cores: 2
    fpu: single_precision

  memory:
    flash_kb: 4096
    sram_kb: 512
    dflash_kb: 128
    eeprom_kb: 64

  peripherals:
    can_controllers: 4
    can_fd_capable: true
    spi_controllers: 6
    adc_groups: 8
    pwm_channels: 24

  safety_features:
    ecc_memory: true
    lockstep_execution: true
    watchdog: external_and_internal
    emc_testing: CISPR_25_Class_5

# config/hw/memory-budget.yaml
memory_budget:
  rom:
    total_kb: 3584
    allocation:
      bootloader_kb: 64
      application_code_kb: 2048
      bsw_code_kb: 1024
      rte_code_kb: 256
      calibration_kb: 128
      reserved_kb: 64
    limit_percent: 90

  ram:
    total_kb: 480
    allocation:
      stack_total_kb: 128
      data_kb: 256
      rte_buffers_kb: 64
      reserved_kb: 32
    limit_percent: 85

  stack_per_task:
    EngineControlTask_10ms: 2048
    DiagnosticTask_100ms: 4096
    BackgroundTask: 1024
    margin_percent: 25
```

## Running the Demo

### ARXML Validation

```bash
# Validate ARXML schema compliance
python scripts/validate-arxml.py \
  --input arxml/ \
  --schema config/autosar/AUTOSAR_R22-11.xsd \
  --output validation-report.json
```

### RTE Generation

```bash
# Execute RTE generator
./scripts/generate-rte.sh \
  --input arxml/ \
  --config config/rte/rte-generation-config.yaml \
  --output generated/rte/ \
  --log generation.log
```

### Integration Build

```bash
# Cross-compile for target ECU
cmake -B build \
  -DCMAKE_TOOLCHAIN_FILE=toolchain-tc397.cmake \
  -DCMAKE_BUILD_TYPE=Release

cmake --build build --target ecu_binary

# Check memory usage
python tools/analyze_memory_map.py \
  --map build/bin/ecu_binary.map \
  --budget config/hw/memory-budget.yaml \
  --output memory-map-report.md
```

### RTE Verification

```bash
# Run unit tests for RTE APIs
python -m pytest tests/rte/unit/ \
  --junitxml=results/unit-results.xml

# Test sender-receiver data transfer
python tests/rte/test_sr_transfer.py \
  --binary build/bin/ecu_binary.elf \
  --output results/sr-transfer-results.md

# Measure RTE overhead
python tests/rte/measure_overhead.py \
  --binary build/bin/ecu_binary.elf \
  --output results/rte-overhead.md
```

## Workflow Execution

The AUTOSAR RTE generation workflow executes 5 stages:

1. **Input Validation** (5-10 min)
   - ARXML schema validation (R22-11 compliance)
   - Port interface compatibility checks
   - Runnable-to-task mapping validation
   - Timing consistency analysis

2. **RTE Configuration** (10-15 min)
   - Generation mode selection
   - Data consistency mechanisms (ASIL-B)
   - Buffer allocation calculation
   - Resource estimation

3. **Code Generation** (15-25 min)
   - Execute RTE generator
   - Generate RTE source files
   - Generate SWC stub files
   - Generate BSW stub files
   - Analyze generation logs

4. **Integration Build** (20-30 min)
   - Cross-compile for target ECU
   - Link RTE + SWCs + BSW
   - Verify no unresolved symbols
   - Analyze memory map

5. **RTE Verification** (15-25 min)
   - Unit tests for RTE APIs
   - Sender-receiver transfer tests
   - Client-server routing tests
   - Mode switch notification tests
   - RTE overhead measurement

## Expected Results

After successful execution, you'll find:

```
generated/rte/
├── Rte.c                      # RTE implementation
├── Rte.h                      # RTE public API
├── Rte_Type.h                 # RTE type definitions
├── Rte_Internal.h             # RTE internal API
├── Rte_EngCtrl.h              # Engine Control SWC header
├── Rte_Diag.h                 # Diagnostics SWC header
└── Rte_Callout_Stubs.c        # BSW callout stubs

results/
├── validation/
│   ├── arxml-validation.json  # Schema validation results
│   ├── port-compatibility.md  # Port compatibility report
│   └── runnable-mapping.md    # Runnable-to-task mapping
├── generation/
│   ├── generation.log         # RTE generator log
│   ├── generation-analysis.md # Log analysis report
│   └── artifact-verification.md
├── build/
│   ├── ecu_binary.elf         # Final ECU binary
│   ├── ecu_binary.map         # Memory map
│   └── memory-map-report.md   # Budget analysis
└── verification/
    ├── unit-results.xml       # Unit test results (JUnit)
    ├── sr-transfer-results.md # SR port tests
    ├── cs-routing-results.md  # CS port tests
    ├── mode-switch-results.md # Mode switch tests
    └── rte-overhead.md        # Performance analysis
```

### RTE Overhead Targets

| Metric | Target | Typical |
|--------|--------|---------|
| SR transfer latency | < 2 µs | 0.8 µs |
| CS call latency | < 10 µs | 4.5 µs |
| Mode switch latency | < 5 µs | 2.1 µs |
| RTE ROM footprint | < 256 KB | 198 KB |
| RTE RAM footprint | < 64 KB | 42 KB |

## Using MCP Tools

This demo leverages the following MCP tools:

```bash
# Validate ARXML schema
autosar:arxml-validate --input arxml/ --schema AUTOSAR_R22-11.xsd

# Generate SWC stubs
autosar:swc-generate --component EngCtrlSwComponentType --output src/swc/

# Check RTE configuration
autosar:rte-check --config config/rte/rte-generation-config.yaml

# Configure BSW modules
autosar:bsw-config --module Can --output config/bsw/Can_Cfg.arxml
```

## SWC Implementation Example

### Engine Control SWC

```c
/**
 * @file EngineControl.c
 * @brief Engine Control Software Component implementation
 *
 * @safety ASIL-B
 * @autosar_version R22-11
 * @component EngCtrlSwComponentType
 */

#include "Rte_EngCtrl.h"
#include "EngineControl.h"

/* Local state */
static EngCtrl_StateType s_engine_state = ENG_CTRL_STATE_INIT;
static uint16_t s_vehicle_speed_kmh = 0U;
static uint32_t s_last_heartbeat_ms = 0U;

/**
 * @brief 10ms cyclic runnable for engine control
 *
 * Implements: SSR-ENG-001, SSR-ENG-002
 * Timing: 10ms period, WCET < 500 µs
 */
void EngCtrl_EngineControl_10ms(void) {
    /* Read vehicle speed from required port */
    uint16_t vehicle_speed;
    if (Rte_Read_EngCtrl_RP_VehicleSpeed_Value(&vehicle_speed) == RTE_E_OK) {
        s_vehicle_speed_kmh = vehicle_speed;
    }

    /* Engine state machine */
    switch (s_engine_state) {
        case ENG_CTRL_STATE_INIT:
            if (vehicle_speed == 0U) {
                s_engine_state = ENG_CTRL_STATE_IDLE;
            }
            break;

        case ENG_CTRL_STATE_IDLE:
            if (vehicle_speed > 0U) {
                s_engine_state = ENG_CTRL_STATE_RUNNING;
            }
            /* Update engine status output */
            EngCtrl_EngineStatus_t status;
            status.state = ENG_STATUS_IDLE;
            status.speed_filter = 0U;
            Rte_Write_EngCtrl_PP_EngineStatus_Value(&status);
            break;

        case ENG_CTRL_STATE_RUNNING:
            if (vehicle_speed == 0U) {
                s_engine_state = ENG_CTRL_STATE_IDLE;
            } else {
                /* Running state - compute output */
                EngCtrl_EngineStatus_t status;
                status.state = ENG_STATUS_RUNNING;
                status.speed_filter = s_vehicle_speed_kmh;
                Rte_Write_EngCtrl_PP_EngineStatus_Value(&status);
            }
            break;

        default:
            /* Defensive: unexpected state */
            s_engine_state = ENG_CTRL_STATE_INIT;
            break;
    }

    s_last_heartbeat_ms = Rte_GetTimestampMs();
}

/**
 * @brief Server runnable: Read diagnostic data
 *
 * Implements: UDS Service 0x22
 * @param DataId: Diagnostic data identifier
 * @param Data: Output data buffer
 * @param Length: Output data length
 * @return RTE_E_OK on success
 */
Std_ReturnType EngCtrl_DiagnosticPort_ReadDataByIdentifier(
    uint16_t DataId,
    uint8_t* Data,
    uint8_t* Length
) {
    Std_ReturnType ret = E_NOT_OK;

    switch (DataId) {
        case DID_ENGINE_SPEED:
            /* Read from internal state */
            uint16_t engine_speed = EngCtrl_GetEngineSpeed();
            Data[0] = (uint8_t)(engine_speed >> 8U);
            Data[1] = (uint8_t)(engine_speed & 0xFFU);
            *Length = 2U;
            ret = E_OK;
            break;

        case DID_VEHICLE_SPEED:
            Data[0] = (uint8_t)(s_vehicle_speed_kmh >> 8U);
            Data[1] = (uint8_t)(s_vehicle_speed_kmh & 0xFFU);
            *Length = 2U;
            ret = E_OK;
            break;

        default:
            /* Unknown DID */
            ret = E_NOT_OK;
            break;
    }

    return ret;
}

/**
 * @brief Mode switch notification
 *
 * Called when EcuMode transitions
 */
void EngCtrl_OnEcuModeSwitch(
    Rte_ModeType_EcuMode previousMode,
    Rte_ModeType_EcuMode currentMode
) {
    if (currentMode == RTE_MODE_EcuMode_OFF) {
        /* Save state to NVM before shutdown */
        EngCtrl_SaveState();
    } else if (previousMode == RTE_MODE_EcuMode_OFF) {
        /* Restore state after startup */
        EngCtrl_RestoreState();
    }
}
```

## Troubleshooting

### Common Issues

1. **ARXML validation fails**
   - Ensure ARXML files conform to AUTOSAR R22-11 schema
   - Check for missing required elements
   - Verify all TYPE-TREF destinations are valid

2. **RTE generation errors**
   - Review generation.log for specific error messages
   - Ensure all port interfaces are properly defined
   - Check runnable-to-task mapping consistency

3. **Unresolved symbols at link time**
   - Verify BSW callout stubs are implemented
   - Check that all required ports have connected providers
   - Ensure SWC runnables are registered in OS tasks

4. **Memory budget exceeded**
   - Reduce RTE buffer sizes in configuration
   - Disable unused RTE features (trace hooks, etc.)
   - Optimize SWC code for smaller footprint

### Getting Help

- Review AUTOSAR Classic Platform R22-11 specification
- Check RTE generator tool documentation
- Consult ISO 26262 compliance documentation for safety requirements
- Review generation logs in `generated/rte/generation.log`

## Next Steps

After successful demo execution:

1. Review `memory-map-report.md` for resource utilization
2. Address any unresolved symbols or missing BSW implementations
3. Proceed to full ECU integration workflow
4. Document SWC safety analysis in safety case

## References

- [AUTOSAR RTE Generation Workflow](../../.github/workflows/autosar-rte-generation.yaml)
- [AUTOSAR Classic Platform R22-11 Specification](../../knowledge-base/standards/autosar/)
- [ISO 26262 Software Development Guidelines](../../knowledge-base/standards/iso-26262/)
- [RTE API Documentation](generated/rte/Rte.h)
