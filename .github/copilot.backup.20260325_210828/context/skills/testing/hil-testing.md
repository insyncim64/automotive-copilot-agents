# Skill: Hardware-in-the-Loop (HIL) Testing for Automotive ECUs

## When to Activate
- User needs to design HIL test benches for ECU validation
- User is developing real-time simulation models for powertrain, chassis, or ADAS
- User requests dSPACE SCALEXIO, NI VeriStand, or ETAS HIL platform integration
- User needs fault injection strategies for ISO 26262 testing
- User is implementing test automation frameworks for HIL (Python, Robot Framework, VT System)
- User needs ECU I/O testing strategies (analog, digital, PWM, CAN, Ethernet)
- User requests HIL test coverage analysis for ASPICE/ISO 26262 compliance

## Standards Compliance
- **ISO 26262-4:2018** (Product Development at System Level) - HIL validation of safety mechanisms
- **ISO 26262-6:2018** (Software Testing) - HIL integration testing requirements
- **ASPICE Level 3** - SWE.5 (Integration Testing), SWE.6 (Qualification Testing)
- **AUTOSAR 4.4** - ECU integration testing, RTE validation
- **ISO 21434:2021** (Cybersecurity) - HIL security testing, penetration testing
- **SAE J1939** - Commercial vehicle network HIL testing
- **ISO 11898** - CAN/CAN FD physical layer testing

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Real-time step size | 10-1000 | μs |
| I/O latency | < 10 | μs |
| CAN bus load | 0-90 | % |
| CAN FD data rate | 0.5-5 | Mbps |
| Analog input resolution | 12-16 | bit |
| Analog output resolution | 12-16 | bit |
| Digital I/O frequency | DC-10 | MHz |
| PWM frequency | 1-20000 | Hz |
| Ethernet throughput | 100-1000 | Mbps |
| Fault injection channels | 1-256 | count |
| Test execution time | Minutes-hours | duration |
| Test coverage target | 95-100 | % |

## HIL Testing Architecture

```
+-----------------------------------------------------------------------+
|                         HIL Test Bench                                 |
|                                                                       |
|  +---------------------------+        +---------------------------+   |
|  |  Real-Time Simulator      |        |  ECU Under Test           |   |
|  |  (dSPACE/NI/ETAS)         |        |  (Production HW+SW)       |   |
|  |                           |        |                           |   |
|  |  +---------------------+  |  CAN   |  +---------------------+  |   |
|  |  | Plant Model         |<-+------->|  | ECU Application     |  |   |
|  |  | (Engine/Battery/    |  |  FD    |  | (AUTOSAR SWC)       |  |   |
|  |  |  Vehicle Dynamics)  |  |        |  |                     |  |   |
|  |  +---------------------+  |        |  +---------------------+  |   |
|  |            |              |        |            |              |   |
|  |  +---------------------+  |  Analog|  +---------------------+  |   |
|  |  | I/O Interface       |<-+------->|  | I/O Drivers         |  |   |
|  |  | - Analog In/Out     |  | Digital|  | (ADC, GPIO, PWM)    |  |   |
|  |  | - Digital In/Out    |  | PWM    |  |                     |  |   |
|  |  | - PWM Capture/Gen   |  |        |  +---------------------+  |   |
|  |  +---------------------+  |        |                           |   |
|  |            |              |        |                           |   |
|  |  +---------------------+  | Ethernet| +---------------------+  |   |
|  |  | Network Simulation  |<-+------->| | Communication Stack |  |   |
|  |  | - CAN/CAN FD        |  | DoIP   | | - TCP/IP            |  |   |
|  |  | - LIN               |  | SOME/IP| | - SOME/IP           |  |   |
|  |  | - Ethernet (DoIP)   |  |        | | - DoIP              |  |   |
|  |  +---------------------+  |        | +---------------------+  |   |
|  +---------------------------+        +---------------------------+   |
|           |                                        |                   |
|           v                                        v                   |
|  +------------------+                    +------------------+          |
|  | Test Automation  |                    | Measurement      |          |
|  | - Python         |                    | - CAN trace      |          |
|  | - Robot Framework|                    | - Oscilloscope   |          |
|  | - VT System      |                    | - Power analyzer |          |
|  +------------------+                    +------------------+          |
+-----------------------------------------------------------------------+
```

## HIL Platform Selection

### dSPACE SCALEXIO

```yaml
dspace_scalexio:
  description: "Modular HIL simulator platform for automotive ECU testing"

  hardware_configuration:
    base_unit: "SCALEXIO Vehicle"
    processor: "Intel Xeon or Core i7"
    real_time_os: "dSPACE RTOS (based on Linux PREEMPT_RT)"
    step_size: "10 μs minimum"

    io_modules:
      - module: "DSP2201 - Digital I/O"
        channels: 32
        type: "Bidirectional, 5-24V compatible"
        features: ["Pulse generation", "Pulse measurement", "Fault injection"]

      - module: "DSP2301 - Analog I/O"
        channels: 16
        type: "±10V, 16-bit resolution"
        features: ["Overvoltage protection", "Short-circuit protection"]

      - module: "DSP2401 - PWM/Resolver"
        channels: 8
        type: "Resolver simulation, PWM capture"
        features: ["Crank/cam simulation", "Knock simulation"]

      - module: "DS6301 - CAN/CAN FD"
        channels: 8
        type: "High-speed CAN with FD support"
        features: ["Bus load simulation", "Error frame injection"]

      - module: "DS6401 - Automotive Ethernet"
        channels: 4
        type: "100/1000 BASE-T1"
        features: ["DoIP testing", "SOME/IP simulation"]

  software_stack:
    - "dSPACE ConfigurationDesk - Hardware configuration"
    - "dSPACE ModelDesk - Plant model integration"
    - "dSPACE AutomationDesk - Test automation (Python/.NET)"
    - "dSPACE VEOS - Virtual ECU for SIL testing"
    - "dSPACE SystemDesk - System architecture modeling"
```

### NI VeriStand

```yaml
ni_veristand:
  description: "Real-time testing and simulation software with PXI hardware"

  hardware_configuration:
    chassis: "NI PXIe-1082 (18-slot)"
    controller: "PXIe-8880 (Intel Core i7, 8-core)"
    real_time_os: "NI Linux Real-Time"
    step_size: "50 μs typical"

    io_modules:
      - module: "PXIe-6358 - Multifunction DAQ"
        channels: "32 AI, 4 AO, 24 DIO"
        resolution: "16-bit"
        sample_rate: "1 MS/s per channel"

      - module: "PXIe-7858 - R Series FPGA"
        features: "Custom timing, PWM generation"
        gates: "863,000"

      - module: "PXI-8512/3 - CAN/CAN FD"
        channels: 4
        features: ["Bus load simulation", "Error injection"]

  software_stack:
    - "NI VeriStand - Real-time test executive"
    - "NI LabVIEW - Plant model development"
    - "NI TestStand - Test sequencing"
    - "NI DIAdem - Data analysis and reporting"
    - "NI XNET - Network communication (CAN, LIN, FlexRay)"
```

### ETAS LABCAR

```yaml
etas_labcar:
  description: "ECU testing platform with focus on powertrain and vehicle dynamics"

  hardware_configuration:
    platform: "LABCAR-RTPC (Real-Time PC)"
    processor: "Intel Xeon multi-core"
    real_time_os: "ARTOS (hard real-time)"
    step_size: "50 μs minimum"

    io_modules:
      - module: "ES4301 - Analog I/O"
        channels: 32
        features: ["High-speed sampling", "Signal conditioning"]

      - module: "ES5301 - Digital I/O"
        channels: 48
        features: ["PWM capture", "Frequency measurement"]

  software_stack:
    - "LABCAR-EXPERIMENTER - Test configuration"
    - "LABCAR-MODELER - Plant model integration (Simulink)"
    - "ORION - Test automation and execution"
    - "INCA - ECU calibration integration"
```

## Plant Model Development

### Real-Time Model Requirements

```c
/* Real-time plant model constraints for HIL simulation */

/* CRITICAL: Model must execute within fixed step size */
#define HIL_STEP_SIZE_US        100U      /* 100 μs = 10 kHz */
#define MAX_EXECUTION_TIME_US   80U       /* 80% of step budget */
#define SAFETY_MARGIN_US        20U       /* 20% margin for I/O, comm */

/* Model structure for real-time execution */
typedef struct {
    /* Parameters (constant during simulation) */
    const float vehicle_mass_kg;
    const float wheel_radius_m;
    const float gear_ratio;

    /* States (updated each step) */
    float vehicle_speed_ms;
    float engine_speed_rpm;
    float battery_soc;

    /* Inputs (from ECU via HIL I/O) */
    float pedal_position_percent;
    float brake_pressure_bar;
    uint8_t gear_selector;

    /* Outputs (to ECU via HIL I/O) */
    float wheel_speed_sensor_rpm;
    float alternator_voltage;
    uint8_t warning_lamps;
} VehicleModel_t;

/* Real-time model execution - called at fixed interval */
void VehicleModel_Update(VehicleModel_t* model, float dt_s) {
    /* CRITICAL: All operations must complete within MAX_EXECUTION_TIME_US */

    /* 1. Read inputs from HIL hardware (ADC, CAN) */
    model->pedal_position_percent = hil_read_analog(ADC_PEDAL);
    model->brake_pressure_bar = hil_read_can_signal(CAN_BrakePressure);

    /* 2. Compute vehicle dynamics (simplified for real-time) */
    float traction_force_n = PedalToForce(model->pedal_position_percent);
    float braking_force_n = model->brake_pressure_bar * BRAKE_GAIN;
    float road_load_n = ComputeRoadLoad(model->vehicle_speed_ms);

    /* 3. Update states (Euler integration) */
    float net_force_n = traction_force_n - braking_force_n - road_load_n;
    float acceleration_ms2 = net_force_n / model->vehicle_mass_kg;
    model->vehicle_speed_ms += acceleration_ms2 * dt_s;

    /* 4. Write outputs to HIL hardware (DAC, CAN) */
    hil_write_analog(DAC_WheelSpeed, RPMToVoltage(model->vehicle_speed_ms));
    hil_write_can_signal(CAN_VehicleSpeed, model->vehicle_speed_ms * 3.6f);

    /* 5. Verify execution time */
    uint32_t exec_time_us = hil_get_execution_time_us();
    if (exec_time_us > MAX_EXECUTION_TIME_US) {
        hil_log_overrun(exec_time_us);
    }
}
```

### Model Simplification for Real-Time

```matlab
% MATLAB/Simulink model simplification for HIL real-time

% Original high-fidelity model (NOT suitable for HIL)
function y = battery_detailed_model(i_current, t_ambient)
    % 50-state electrochemical model - TOO SLOW for HIL
    % Execution time: ~5 ms (exceeds 100 μs budget)
    [voltage, soc, temps] =电化学_model(i_current, t_ambient);
    y = voltage;
end

% Simplified equivalent circuit model (HIL-ready)
function y = battery_ecm_model(i_current, t_ambient)
    % 3-state RC equivalent circuit - FAST for HIL
    % Execution time: ~15 μs (within 100 μs budget)
    persistent v_oc v_rc1 v_rc2

    % Parameters (function of SOC and temperature)
    [r0, r1, c1, r2, c2] = lookup_ecm_params(soc, t_ambient);

    % State update (Euler integration)
    dv_rc1 = (-v_rc1 + r1 * i_current) / (r1 * c1);
    dv_rc2 = (-v_rc2 + r2 * i_current) / (r2 * c2);
    v_rc1 = v_rc1 + dv_rc1 * dt;
    v_rc2 = v_rc2 + dv_rc2 * dt;

    % Output equation
    v_oc = lookup_ocv(soc, t_ambient);
    y = v_oc - v_rc1 - v_rc2 - r0 * i_current;
end

% Code generation for dSPACE
%#codegen
function hil_main()
    % Configure for dSPACE target
    coder.extrinsic('hil_read_analog');
    coder.extrinsic('hil_write_analog');

    % Fixed-step discrete solver
    configSet = getActiveConfigSet('battery_hil_model');
    set_param(configSet, 'Solver', 'FixedStepDiscrete');
    set_param(configSet, 'FixedStep', '0.0001');  % 100 μs

    % Generate C code for dSPACE
    slbuild('battery_hil_model');
end
```

## Fault Injection Testing

### Fault Injection Categories

```yaml
fault_injection_strategy:
  purpose: "Validate ECU fault detection and reaction per ISO 26262"

  fault_categories:
    sensor_faults:
      - type: "Stuck-at-value"
        description: "Sensor output frozen at constant value"
        implementation: "HIL analog output holds last value"
        iso_26262_ref: "FMEA sensor failure mode"

      - type: "Stuck-at-range"
        description: "Sensor output stuck at min or max"
        implementation: "HIL drives 0V or 5V (or 4-20mA: 0mA/24mA)"
        detected_by: "Range check in ECU"

      - type: "Signal-drift"
        description: "Gradual offset from true value"
        implementation: "HIL adds ramp offset over time"
        detected_by: "Plausibility check, cross-sensor validation"

      - type: "Excessive-noise"
        description: "High-frequency noise on signal"
        implementation: "HIL superimposes high-frequency sine"
        detected_by: "Low-pass filter, rate check"

      - type: "Open-circuit"
        description: "Sensor wire disconnected"
        implementation: "HIL relay opens signal path"
        detected_by: "Pull-up resistor detection (>4.9V)"

      - type: "Short-circuit"
        description: "Signal shorted to ground or battery"
        implementation: "HIL relay shorts signal to GND/VBATT"
        detected_by: "Range check (0V or >5V)"

    actuator_faults:
      - type: "Stuck-actuator"
        description: "Actuator does not respond to command"
        implementation: "HIL holds output position constant"
        detected_by: "Position feedback mismatch"

      - type: "Runaway-actuator"
        description: "Actuator moves without command"
        implementation: "HIL drives output to extreme"
        detected_by: "Unexpected position change"

      - type: "Slow-response"
        description: "Actuator response delayed"
        implementation: "HIL adds time delay to response"
        detected_by: "Response time monitoring"

    communication_faults:
      - type: "Message-loss"
        description: "CAN message not received"
        implementation: "HIL blocks specific CAN ID"
        detected_by: "Timeout monitoring (e.g., 100ms)"

      - type: "Message-corruption"
        description: "CAN data altered"
        implementation: "HIL modifies payload bytes"
        detected_by: "CRC/checksum failure"

      - type: "Bus-off"
        description: "CAN controller enters bus-off state"
        implementation: "HIL floods bus with dominant bits"
        detected_by: "ECU CAN controller status"

      - type: "Counter-roll"
        description: "Rolling counter resets or jumps"
        implementation: "HIL resets counter to 0"
        detected_by: "Rolling counter check (AUTOSAR E2E)"

    power_faults:
      - type: "Voltage-dropout"
        description: "Supply voltage dips below minimum"
        implementation: "HIL programmable supply drops to 6V"
        duration: "100ms - 1s"
        detected_by: "Undervoltage reset circuit"

      - type: "Voltage-spike"
        description: "Load dump or inductive spike"
        implementation: "HIL injects +40V spike (ISO 16750-2)"
        duration: "400ms"
        detected_by: "Overvoltage protection circuit"

      - type: "Crank-profile"
        description: "Engine cranking voltage profile"
        implementation: "HIL drops to 6V for 100ms, recovery"
        standard: "ISO 16750-2, 4.6.2.3"
```

### Fault Injection Implementation

```c
/* HIL fault injection interface */
typedef enum {
    FAULT_TYPE_NONE,
    FAULT_TYPE_STUCK_AT,
    FAULT_TYPE_OFFSET,
    FAULT_TYPE_NOISE,
    FAULT_TYPE_OPEN,
    FAULT_TYPE_SHORT,
    FAULT_TYPE_MESSAGE_DROP,
    FAULT_TYPE_CAN_BUS_OFF
} HilFaultType_t;

typedef struct {
    uint32_t channel_id;           /* Analog/DIO/CAN channel */
    HilFaultType_t fault_type;
    float fault_value;              /* For stuck-at */
    float fault_offset;             /* For offset */
    float fault_amplitude;          /* For noise */
    float fault_frequency_hz;       /* For noise */
    uint32_t injection_time_ms;     /* When to inject */
    uint32_t duration_ms;           /* How long (0 = permanent) */
    bool active;
} HilFaultInjection_t;

/* Fault injection execution - called in HIL real-time loop */
void hil_execute_fault_injection(HilFaultInjection_t* fault, float* signal) {
    uint32_t current_time_ms = hil_get_time_ms();

    /* Check if fault should be active */
    if (!fault->active || current_time_ms < fault->injection_time_ms) {
        return;  /* Fault not yet active */
    }

    /* Check if fault has expired */
    if (fault->duration_ms > 0 &&
        current_time_ms > fault->injection_time_ms + fault->duration_ms) {
        fault->active = false;
        return;
    }

    /* Apply fault based on type */
    switch (fault->fault_type) {
        case FAULT_TYPE_STUCK_AT:
            *signal = fault->fault_value;
            break;

        case FAULT_TYPE_OFFSET:
            *signal += fault->fault_offset;
            break;

        case FAULT_TYPE_NOISE: {
            float noise = fault->fault_amplitude *
                          sinf(2.0f * M_PI * fault->fault_frequency_hz *
                               (current_time_ms / 1000.0f));
            *signal += noise;
            break;
        }

        case FAULT_TYPE_OPEN:
            *signal = 5.0f;  /* Pull-up to 5V */
            break;

        case FAULT_TYPE_SHORT:
            *signal = 0.0f;  /* Short to ground */
            break;

        default:
            break;
    }
}

/* CAN message fault injection */
void hil_inject_can_fault(CanFrame_t* frame, HilFaultType_t fault_type) {
    switch (fault_type) {
        case FAULT_TYPE_MESSAGE_DROP:
            /* Silently drop message - ECU sees timeout */
            frame = NULL;
            break;

        case FAULT_TYPE_CAN_BUS_OFF:
            /* Send 16+ consecutive dominant bits */
            can_force_dominant_bits(17);
            break;

        default:
            break;
    }
}
```

## Test Automation Framework

### Python Test Automation

```python
# HIL test automation framework
import time
import logging
from dataclasses import dataclass
from typing import List, Optional
from hil_interface import HilBench, CanBus, AnalogIO, DigitalIO

@dataclass
class TestCase:
    id: str
    name: str
    description: str
    asil: str  # QM, A, B, C, D
    requirement_refs: List[str]
    preconditions: List[str]
    steps: List[dict]
    expected_results: List[str]
    pass_criteria: List[str]

class HilTestAutomation:
    def __init__(self, bench_config: str):
        self.hil = HilBench(bench_config)
        self.can = CanBus(channel=0)
        self.analog = AnalogIO()
        self.digital = DigitalIO()
        self.results = []
        self.logger = logging.getLogger('HIL')

    def setup(self):
        """Initialize HIL bench before test execution."""
        self.hil.initialize()
        self.hil.reset_all_outputs()
        self.hil.load_plant_model('vehicle_model_rt')
        self.can.set_baudrate(500000)
        self.logger.info("HIL bench initialized")

    def teardown(self):
        """Clean up HIL bench after test execution."""
        self.hil.stop_simulation()
        self.hil.reset_all_outputs()
        self.logger.info("HIL bench reset")

    def execute_test(self, test: TestCase) -> bool:
        """Execute a single HIL test case."""
        self.logger.info(f"Executing {test.id}: {test.name}")

        try:
            # Setup preconditions
            for precondition in test.preconditions:
                self._execute_precondition(precondition)

            # Execute test steps
            step_results = []
            for i, step in enumerate(test.steps):
                self.logger.debug(f"  Step {i+1}: {step['action']}")

                # Record start time for timing verification
                start_time = time.time()

                # Execute action
                result = self._execute_step(step)

                # Verify timing if specified
                if 'max_time_ms' in step:
                    elapsed_ms = (time.time() - start_time) * 1000
                    assert elapsed_ms <= step['max_time_ms'], \
                        f"Step took {elapsed_ms}ms (max: {step['max_time_ms']}ms)"

                step_results.append(result)

            # Verify expected results
            all_passed = all(step_results)

            # Log result
            status = "PASS" if all_passed else "FAIL"
            self.logger.info(f"  Result: {status}")

            self.results.append({
                'test_id': test.id,
                'name': test.name,
                'status': status,
                'steps': step_results
            })

            return all_passed

        except Exception as e:
            self.logger.error(f"Test failed with exception: {e}")
            self.results.append({
                'test_id': test.id,
                'name': test.name,
                'status': 'FAIL',
                'error': str(e)
            })
            return False

    def _execute_step(self, step: dict) -> bool:
        """Execute a single test step."""
        action = step['action']

        if action == 'set_analog_output':
            channel = step['channel']
            value = step['value']
            self.analog.write(channel, value)
            return True

        elif action == 'set_digital_output':
            channel = step['channel']
            value = step['value']
            self.digital.write(channel, value)
            return True

        elif action == 'inject_can_message':
            msg_id = step['msg_id']
            data = bytes(step['data'])
            self.can.send(msg_id, data)
            return True

        elif action == 'inject_fault':
            fault = step['fault']
            self.hil.inject_fault(fault)
            return True

        elif action == 'wait_for_signal':
            signal = step['signal']
            expected = step['expected']
            timeout = step.get('timeout_ms', 1000)
            tolerance = step.get('tolerance', 0.01)

            start = time.time()
            while (time.time() - start) * 1000 < timeout:
                actual = self._read_signal(signal)
                if abs(actual - expected) <= tolerance:
                    return True
                time.sleep(0.001)  # 1ms polling
            return False

        elif action == 'verify_can_signal':
            msg_id = step['msg_id']
            signal_name = step['signal']
            expected = step['expected']

            frame = self.can.receive(timeout_ms=100)
            if frame is None or frame.id != msg_id:
                return False

            actual = self._decode_signal(frame, signal_name)
            return abs(actual - expected) <= step.get('tolerance', 0.01)

        else:
            raise ValueError(f"Unknown action: {action}")
```

### Robot Framework for HIL

```robot
*** Settings ***
Library    HilLibrary    bench_config=bench01.yaml
Library    CanBusLibrary    interface=vector    channel=1
Library    Process
Suite Setup    Initialize HIL Bench
Suite Teardown    Shutdown HIL Bench
Test Template    Execute HIL Test Step

*** Variables ***
${HIL_BENCH}          bench01
${ECU_ID}             BMS-001
${CAN_BAUDRATE}       500000
${STEP_SIZE_US}       100
${TIMEOUT_MS}         1000

*** Test Cases ***
BMS Overcurrent Protection Triggers Within FTTI
    [Documentation]    SSR-BMS-012: BMS shall detect overcurrent > 500A within 10ms
    [Tags]    safety    asil_d    regression    hil
    [Setup]    Reset HIL Outputs
    # Precondition: ECU powered, contactor closed
    Set Power Supply    13.5V    2A
    Wait Until Keyword Succeeds    5s    100ms
    ...    Verify CAN Signal    BMS_Status    Contactor_State    CLOSED
    # Inject overcurrent via plant model
    Set Sensor Model Value    pack_current_a    520.0
    # Verify contactor opens within FTTI
    Wait Until Keyword Succeeds    ${TIMEOUT_MS}    1ms
    ...    Verify CAN Signal    BMS_Status    Contactor_State    OPEN
    [Teardown]    Log Test Result

BMS Recovers After Fault Clears
    [Documentation]    SSR-BMS-015: System recovers when fault clears
    [Tags]    safety    asil_d
    [Setup]    Reset HIL Outputs
    # Start from overcurrent fault state
    Set Sensor Model Value    pack_current_a    520.0
    Sleep    200ms
    Verify CAN Signal    BMS_Status    Contactor_State    OPEN
    # Clear overcurrent condition
    Set Sensor Model Value    pack_current_a    100.0
    Sleep    500ms
    # Attempt recovery via diagnostic command
    Send UDS Command    0x31 0x01 0xFF 0x00    # Routine Control: Clear Faults
    Sleep    100ms
    # Verify recovery
    Verify CAN Signal    BMS_Status    Fault_Active    FALSE
    [Teardown]    Log Test Result

BMS Cell Voltage Monitoring Accuracy
    [Documentation]    SSR-BMS-001: Cell voltage accuracy ±10mV
    [Tags]    accuracy    asil_c
    [Setup]    Reset HIL Outputs
    # Sweep cell voltage from 2.5V to 4.5V
    ${test_voltages}=    Create List    2.5    3.0    3.5    4.0    4.2    4.5
    FOR    ${voltage}    IN    @{test_voltages}
        Set Analog Output    AI_CELL_1    ${voltage}
        Sleep    50ms
        ${reported}=    Read CAN Signal    BMS_CellVoltage1    value
        Should Be Close    ${reported}    ${voltage}    0.01
    END
    [Teardown]    Log Test Result

*** Keywords ***
Initialize HIL Bench
    Load Plant Model    vehicle_model_rt
    Configure CAN       ${CAN_BAUDRATE}
    Reset All Outputs
    Start Real-Time Simulation

Verify CAN Signal
    [Arguments]    ${message_name}    ${signal_name}    ${expected_value}
    ${frame}=    Receive CAN Message    timeout=100ms
    ${actual}=    Decode Signal    ${frame}    ${signal_name}
    Should Be Equal As Numbers    ${actual}    ${expected_value}

Inject Fault
    [Arguments]    ${fault_type}    ${channel}    ${value}
    ${fault}=    Create Fault    type=${fault_type}    channel=${channel}    value=${value}
    HIL Inject Fault    ${fault}
```

## Test Coverage Analysis

### HIL Coverage Metrics

```yaml
coverage_metrics:
  requirements_coverage:
    metric: "Percentage of system requirements verified by HIL tests"
    target: "100% of safety requirements (ASIL A-D)"
    calculation: "verified_requirements / total_requirements * 100"
    tool: "DOORS/Test management tool integration"

  functional_coverage:
    metric: "Percentage of functional scenarios covered"
    target: "95% of operational scenarios"
    calculation: "covered_scenarios / total_scenarios * 100"
    method: "Scenario-based testing with ODD coverage"

  fault_injection_coverage:
    metric: "Percentage of FMEA failure modes tested"
    target: "100% of detected failure modes"
    calculation: "tested_failure_modes / total_failure_modes * 100"
    source: "FMEA/FTA linkage to HIL tests"

  timing_coverage:
    metric: "Verification of all timing requirements"
    target: "100% of timing-critical requirements"
    method: "Oscilloscope/CANalyzer timing measurement"

  boundary_coverage:
    metric: "Testing at all operating boundaries"
    target: "All min/max limits verified"
    method: "Boundary value analysis on all signals"
```

### Coverage Traceability

```yaml
# Requirements to HIL test traceability
traceability_matrix:
  - requirement:
      id: SSR-BMS-012
      text: "BMS shall detect overcurrent > 500A within 10ms"
      asil: D
    hil_tests:
      - TC-HIL-BMS-042  # Normal overcurrent detection
      - TC-HIL-BMS-043  # Boundary: exactly 500A
      - TC-HIL-BMS-044  # Boundary: 500.1A
      - FI-HIL-BMS-001  # Fault injection: sensor stuck-at
    coverage_status: FULLY_COVERED
    last_execution: "2025-03-15"
    result: PASS

  - requirement:
      id: SSR-BMS-013
      text: "BMS shall open contactor within 100ms of overcurrent detection"
      asil: D
    hil_tests:
      - TC-HIL-BMS-047  # End-to-end timing measurement
      - FI-HIL-BMS-002  # Fault injection: primary path failure
    coverage_status: FULLY_COVERED
    last_execution: "2025-03-15"
    result: PASS
```

## Test Report Generation

### Automated Test Report

```python
# Generate HIL test report
from datetime import datetime
import json

def generate_hil_test_report(results: list, output_path: str):
    """Generate HTML test report from HIL execution results."""

    report = {
        'report_id': f"HIL-RPT-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        'generated_at': datetime.now().isoformat(),
        'bench_id': 'HIL-BENCH-01',
        'ecu_id': 'BMS-ECU-001',
        'sw_version': 'v2.4.0',
        'hw_version': 'Rev C',
        'total_tests': len(results),
        'passed': sum(1 for r in results if r['status'] == 'PASS'),
        'failed': sum(1 for r in results if r['status'] == 'FAIL'),
        'blocked': sum(1 for r in results if r['status'] == 'BLOCKED'),
        'pass_rate': sum(1 for r in results if r['status'] == 'PASS') / len(results) * 100,
        'execution_time_seconds': sum(r.get('duration_s', 0) for r in results),
        'test_details': results
    }

    # Generate summary statistics
    report['coverage'] = {
        'requirements_covered': len(set(
            ref for r in results for ref in r.get('requirement_refs', [])
        )),
        'asil_d_tests': sum(1 for r in results if r.get('asil') == 'D'),
        'asil_c_tests': sum(1 for r in results if r.get('asil') == 'C'),
        'fault_injection_tests': sum(1 for r in results if r.get('fault_injected'))
    }

    # Write JSON report
    with open(output_path + '.json', 'w') as f:
        json.dump(report, f, indent=2)

    # Generate HTML report
    html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <title>HIL Test Report - {report['report_id']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 20px; margin: 20px 0; }}
        .pass {{ color: green; }}
        .fail {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>HIL Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Report ID:</strong> {report['report_id']}</p>
        <p><strong>Generated:</strong> {report['generated_at']}</p>
        <p><strong>ECU:</strong> {report['ecu_id']} (SW: {report['sw_version']})</p>
        <p><strong>Total Tests:</strong> {report['total_tests']}</p>
        <p><strong>Passed:</strong> <span class="pass">{report['passed']}</span></p>
        <p><strong>Failed:</strong> <span class="fail">{report['failed']}</span></p>
        <p><strong>Pass Rate:</strong> {report['pass_rate']:.1f}%</p>
    </div>
    <h2>Test Details</h2>
    <table>
        <tr>
            <th>Test ID</th>
            <th>Name</th>
            <th>ASIL</th>
            <th>Status</th>
            <th>Duration (s)</th>
        </tr>
"""

    for result in results:
        status_class = 'pass' if result['status'] == 'PASS' else 'fail'
        html_report += f"""
        <tr>
            <td>{result['test_id']}</td>
            <td>{result['name']}</td>
            <td>{result.get('asil', 'N/A')}</td>
            <td class="{status_class}">{result['status']}</td>
            <td>{result.get('duration_s', 'N/A')}</td>
        </tr>
"""

    html_report += """
    </table>
</body>
</html>
"""

    with open(output_path + '.html', 'w') as f:
        f.write(html_report)

    return report
```

## Approach

1. **Define HIL test objectives**
   - Identify requirements to verify (safety, functional, performance)
   - Determine fault injection scenarios from FMEA
   - Establish coverage targets (requirements, fault modes, timing)

2. **Configure HIL hardware**
   - Select appropriate I/O modules (analog, digital, network)
   - Configure real-time step size (typically 100 μs)
   - Set up power supplies and measurement equipment

3. **Develop plant models**
   - Create real-time vehicle/powertrain/battery models
   - Simplify high-fidelity models for real-time execution
   - Validate models against test data or high-fidelity simulation

4. **Implement test automation**
   - Write test cases in Python or Robot Framework
   - Configure test sequences in AutomationDesk/ORION
   - Integrate with test management system (DOORS, Polarion)

5. **Execute tests**
   - Run automated test suite
   - Monitor execution in real-time
   - Capture failures and anomalies

6. **Generate reports**
   - Produce test summary with pass/fail statistics
   - Document coverage metrics
   - Archive results for traceability

## Deliverables

- **HIL Test Specification** - Test cases, procedures, acceptance criteria
- **Plant Model Documentation** - Model description, assumptions, validation
- **Test Automation Scripts** - Python/Robot Framework test suites
- **Test Execution Report** - Pass/fail results, coverage analysis
- **Fault Injection Report** - FMEA coverage, failure mode verification
- **Calibration Data** - INCA/APIS calibration files
- **Traceability Matrix** - Requirements to tests linkage

## Related Context

- [@context/skills/testing/sil-testing.md](../testing/sil-testing.md) - Software-in-the-Loop testing
- [@context/skills/testing/mil-testing.md](../testing/mil-testing.md) - Model-in-the-Loop testing
- [@context/skills/testing/pil-testing.md](../testing/pil-testing.md) - Processor-in-the-Loop testing
- [@context/skills/testing/test-automation.md](../testing/test-automation.md) - Test automation frameworks
- [@context/skills/safety/iso-26262-overview.md](../safety/iso-26262-overview.md) - ISO 26262 testing requirements
- [@context/skills/autosar/classic-platform.md](../autosar/classic-platform.md) - AUTOSAR ECU testing

## Tools Required

| Tool | Purpose | Vendor |
|------|---------|--------|
| dSPACE SCALEXIO | HIL simulator | dSPACE |
| NI VeriStand | Real-time testing | National Instruments |
| ETAS LABCAR | ECU testing | ETAS |
| Vector CANoe | Network simulation | Vector |
| ETAS INCA | Calibration | ETAS |
| dSPACE AutomationDesk | Test automation | dSPACE |
| Robot Framework | Open-source test automation | Open-source |
| pytest | Python test framework | Open-source |
| NI TestStand | Test executive | National Instruments |
| National Instruments DIAdem | Data analysis | National Instruments |

## Regulatory Context

| Region | Regulation | HIL Testing Relevance |
|--------|------------|----------------------|
| EU/UNECE | UN ECE R157 (ALKS) | HIL validation of automated driving functions |
| EU | Type Approval (EU) 2022/1426 | HIL evidence for ADS approval |
| US | FMVSS | HIL testing for compliance verification |
| China | GB/T standards | HIL methodology aligned with international standards |
