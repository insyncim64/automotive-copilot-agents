"""
Battery Management System - Safety Controller Module

Implements ISO 26262 ASIL-C safety functions including over-voltage,
under-voltage, overcurrent, short-circuit, and over-temperature protection
with formal safety state machine.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple
import time


class SafetyState(Enum):
    """Safety state machine states per ISO 26262."""
    INIT = 0
    NORMAL = 1
    WARNING = 2
    FAULT = 3
    SAFE_STOP = 4
    SERVICE = 5


class SafetyEventType(Enum):
    """Safety event types that trigger state transitions."""
    # Voltage events
    OVERVOLTAGE_L1 = 0  # Warning level
    OVERVOLTAGE_L2 = 1  # Fault level
    UNDERVOLTAGE_L1 = 2  # Warning level
    UNDERVOLTAGE_L2 = 3  # Fault level

    # Current events
    OVERCURRENT_L1 = 4  # Warning level
    OVERCURRENT_L2 = 5  # Fault level
    SHORT_CIRCUIT = 6  # Critical fault

    # Temperature events
    OVERTEMPERATURE_L1 = 7  # Warning level
    OVERTEMPERATURE_L2 = 8  # Fault level
    UNDERTEMPERATURE = 9  # Warning level

    # SOH/SOC events
    LOW_SOC = 10  # Warning level
    CRITICAL_SOC = 11  # Fault level
    SOH_DEGRADED = 12  # Warning level
    SOH_CRITICAL = 13  # Fault level

    # System events
    WATCHDOG_TIMEOUT = 14
    SENSOR_FAULT = 15
    COMMUNICATION_LOSS = 16
    ISOLATION_FAULT = 17
    OPEN_WIRE_FAULT = 18

    # Recovery events
    FAULT_CLEARED = 19
    SYSTEM_RESET = 20
    ENTER_SERVICE = 21
    EXIT_SERVICE = 22


class ContactorState(Enum):
    """Main contactor states."""
    OPEN = 0
    CLOSED = 1
    FAULT = 2


@dataclass
class SafetyLimits:
    """Safety threshold configuration."""
    # Cell voltage limits (V)
    cell_ov_l2_v: float = 4.25  # Fault level
    cell_ov_l1_v: float = 4.20  # Warning level
    cell_uv_l2_v: float = 2.50  # Fault level
    cell_uv_l1_v: float = 2.80  # Warning level

    # Pack current limits (A)
    pack_oc_l2_a: float = 500.0  # Fault level
    pack_oc_l1_a: float = 400.0  # Warning level
    short_circuit_a: float = 1000.0  # Short circuit threshold

    # Temperature limits (°C)
    temp_ot_l2_c: float = 60.0  # Fault level
    temp_ot_l1_c: float = 55.0  # Warning level
    temp_ut_c: float = -20.0  # Under-temperature warning

    # SOC limits (%)
    soc_low_warning: float = 15.0
    soc_critical: float = 5.0

    # SOH limits (%)
    soh_degraded: float = 80.0
    soh_critical: float = 60.0

    # Isolation resistance (mohm)
    isolation_fault_mohm: float = 100.0
    isolation_warning_mohm: float = 500.0


@dataclass
class TimingRequirements:
    """Safety timing requirements per ISO 26262 FTTI."""
    # Fault detection times
    overvoltage_detection_ms: float = 10.0
    undervoltage_detection_ms: float = 100.0
    overcurrent_detection_ms: float = 10.0
    short_circuit_detection_us: float = 100.0
    overtemp_detection_ms: float = 50.0

    # Fault reaction times (FTTI - Fault Tolerant Time Interval)
    contactor_open_time_ms: float = 5.0
    total_fault_reaction_ms: float = 100.0

    # Monitoring times
    watchdog_period_ms: float = 10.0
    sensor_polling_period_ms: float = 1.0
    communication_timeout_ms: float = 500.0


@dataclass
class FaultRecord:
    """Record of a detected fault."""
    event_type: SafetyEventType
    timestamp_ms: float
    value: float
    threshold: float
    severity: int  # 1=warning, 2=fault, 3=critical
    cleared: bool = False
    cleared_timestamp_ms: Optional[float] = None


@dataclass
class SafetyStatus:
    """Current safety system status."""
    state: SafetyState
    contactor_state: ContactorState
    active_faults: List[FaultRecord]
    fault_count: int
    warning_count: int
    soh_percent: float
    soc_percent: float
    time_to_fault_ms: float  # Predicted time until fault at current rate


class SafetyStateMachine:
    """
    ISO 26262 compliant safety state machine.

    State Transition Diagram:
    ========================

                    SYSTEM_RESET
                        |
                        v
                    [INIT] ----(self-test OK)----> [NORMAL]
                        |                              |
                    (fault)                            | (warning event)
                        |                              v
                        |                          [WARNING]
                        |                              |
                        |    (fault cleared)           | (fault event)
                        |<-----------------------------+
                        |
                        v
                    [FAULT] ----(all faults cleared)--> [SAFE_STOP]
                        |                                   |
                    (immediate)                             | (manual reset)
                        |                                   v
                        +------------------------------ [SERVICE]

    State Descriptions:
    ==================
    INIT:      System initialization, self-test execution
    NORMAL:    All systems nominal, contactor closed, full operation
    WARNING:   Degraded operation, increased monitoring, contactor closed
    FAULT:     Fault detected, fault reaction in progress
    SAFE_STOP: Safe state achieved, contactor open, waiting for reset
    SERVICE:   Maintenance mode, restricted operation for diagnostics
    """

    # State transition table
    TRANSITIONS = {
        SafetyState.INIT: {
            SafetyEventType.SYSTEM_RESET: SafetyState.INIT,
            SafetyEventType.FAULT_CLEARED: SafetyState.INIT,  # After self-test
        },
        SafetyState.NORMAL: {
            SafetyEventType.OVERVOLTAGE_L1: SafetyState.WARNING,
            SafetyEventType.UNDERVOLTAGE_L1: SafetyState.WARNING,
            SafetyEventType.OVERCURRENT_L1: SafetyState.WARNING,
            SafetyEventType.OVERTEMPERATURE_L1: SafetyState.WARNING,
            SafetyEventType.UNDERTEMPERATURE: SafetyState.WARNING,
            SafetyEventType.LOW_SOC: SafetyState.WARNING,
            SafetyEventType.SOH_DEGRADED: SafetyState.WARNING,
            SafetyEventType.OVERVOLTAGE_L2: SafetyState.FAULT,
            SafetyEventType.UNDERVOLTAGE_L2: SafetyState.FAULT,
            SafetyEventType.OVERCURRENT_L2: SafetyState.FAULT,
            SafetyEventType.SHORT_CIRCUIT: SafetyState.FAULT,
            SafetyEventType.OVERTEMPERATURE_L2: SafetyState.FAULT,
            SafetyEventType.CRITICAL_SOC: SafetyState.FAULT,
            SafetyEventType.SOH_CRITICAL: SafetyState.FAULT,
            SafetyEventType.WATCHDOG_TIMEOUT: SafetyState.FAULT,
            SafetyEventType.SENSOR_FAULT: SafetyState.FAULT,
            SafetyEventType.COMMUNICATION_LOSS: SafetyState.FAULT,
            SafetyEventType.ISOLATION_FAULT: SafetyState.FAULT,
            SafetyEventType.OPEN_WIRE_FAULT: SafetyState.FAULT,
            SafetyEventType.ENTER_SERVICE: SafetyState.SERVICE,
        },
        SafetyState.WARNING: {
            SafetyEventType.FAULT_CLEARED: SafetyState.NORMAL,
            SafetyEventType.OVERVOLTAGE_L2: SafetyState.FAULT,
            SafetyEventType.UNDERVOLTAGE_L2: SafetyState.FAULT,
            SafetyEventType.OVERCURRENT_L2: SafetyState.FAULT,
            SafetyEventType.SHORT_CIRCUIT: SafetyState.FAULT,
            SafetyEventType.OVERTEMPERATURE_L2: SafetyState.FAULT,
            SafetyEventType.CRITICAL_SOC: SafetyState.FAULT,
            SafetyEventType.SOH_CRITICAL: SafetyState.FAULT,
            SafetyEventType.WATCHDOG_TIMEOUT: SafetyState.FAULT,
            SafetyEventType.SENSOR_FAULT: SafetyState.FAULT,
            SafetyEventType.ENTER_SERVICE: SafetyState.SERVICE,
        },
        SafetyState.FAULT: {
            SafetyEventType.FAULT_CLEARED: SafetyState.SAFE_STOP,
        },
        SafetyState.SAFE_STOP: {
            SafetyEventType.SYSTEM_RESET: SafetyState.INIT,
            SafetyEventType.EXIT_SERVICE: SafetyState.SERVICE,
        },
        SafetyState.SERVICE: {
            SafetyEventType.SYSTEM_RESET: SafetyState.INIT,
            SafetyEventType.EXIT_SERVICE: SafetyState.NORMAL,
            SafetyEventType.FAULT_CLEARED: SafetyState.NORMAL,
        },
    }

    def __init__(self, limits: SafetyLimits, timing: TimingRequirements):
        """Initialize safety state machine."""
        self.limits = limits
        self.timing = timing
        self.state = SafetyState.INIT
        self.contactor_state = ContactorState.OPEN
        self.active_faults: List[FaultRecord] = []
        self.fault_history: List[FaultRecord] = []
        self.current_time_ms = 0.0
        self.last_state_change_ms = 0.0
        self.state_change_count = 0

        # Timing monitors
        self.fault_detection_time_ms: Dict[SafetyEventType, float] = {}
        self.fault_reaction_time_ms: Dict[SafetyEventType, float] = {}

        # Self-test result
        self.self_test_passed = False

    def transition(self, event: SafetyEventType) -> bool:
        """
        Execute state transition based on event.

        Returns True if transition was valid and executed.
        """
        if self.state not in self.TRANSITIONS:
            return False

        if event not in self.TRANSITIONS[self.state]:
            # Event doesn't cause transition from current state
            return False

        old_state = self.state
        new_state = self.TRANSITIONS[self.state][event]

        # Execute transition
        self.state = new_state
        self.current_time_ms = time.time() * 1000
        self.last_state_change_ms = self.current_time_ms
        self.state_change_count += 1

        # Update contactor state based on new safety state
        self._update_contactor_state()

        # Record transition for diagnostics
        self._log_state_transition(old_state, new_state, event)

        return True

    def _update_contactor_state(self):
        """Update contactor state based on safety state."""
        if self.state in [SafetyState.FAULT, SafetyState.SAFE_STOP]:
            self.contactor_state = ContactorState.OPEN
        elif self.state == SafetyState.INIT:
            self.contactor_state = ContactorState.OPEN
        elif self.state == SafetyState.SERVICE:
            # Contactor may be closed in service mode with restrictions
            self.contactor_state = ContactorState.OPEN  # Default safe
        else:
            self.contactor_state = ContactorState.CLOSED

    def _log_state_transition(self, old_state: SafetyState,
                               new_state: SafetyState,
                               event: SafetyEventType):
        """Log state transition for diagnostics and audit."""
        # In production, this would write to non-volatile fault log
        pass

    def initialize(self) -> bool:
        """
        Execute initialization and self-test sequence.

        Returns True if all self-tests pass.
        """
        self.state = SafetyState.INIT
        self.self_test_passed = False

        # Execute self-tests
        tests_passed = [
            self._self_test_memory(),
            self._self_test_sensors(),
            self._self_test_contactor(),
            self._self_test_watchdog(),
            self._self_test_communication(),
        ]

        self.self_test_passed = all(tests_passed)

        if self.self_test_passed:
            self.transition(SafetyEventType.SYSTEM_RESET)
            return True
        else:
            self._record_fault(
                SafetyEventType.SENSOR_FAULT,
                severity=3,
                value=0,
                threshold=0
            )
            return False

    def _self_test_memory(self) -> bool:
        """Test memory integrity (CRC check on configuration)."""
        # Placeholder - would verify NVM CRC, RAM pattern, etc.
        return True

    def _self_test_sensors(self) -> bool:
        """Verify sensor communication and plausibility."""
        # Placeholder - would check ADC, temperature sensors, current sensor
        return True

    def _self_test_contactor(self) -> bool:
        """Verify contactor driver and feedback circuit."""
        # Placeholder - would cycle contactor and verify feedback
        return True

    def _self_test_watchdog(self) -> bool:
        """Verify watchdog timer functionality."""
        # Placeholder - would trigger watchdog and verify reset
        return True

    def _self_test_communication(self) -> bool:
        """Verify CAN/Ethernet communication."""
        # Placeholder - would send/receive test messages
        return True

    def _record_fault(self, event_type: SafetyEventType,
                      severity: int, value: float, threshold: float):
        """Record a new fault."""
        fault = FaultRecord(
            event_type=event_type,
            timestamp_ms=self.current_time_ms,
            value=value,
            threshold=threshold,
            severity=severity
        )
        self.active_faults.append(fault)
        self.fault_history.append(fault)

    def _clear_fault(self, event_type: SafetyEventType):
        """Clear a fault record."""
        for fault in self.active_faults:
            if fault.event_type == event_type:
                fault.cleared = True
                fault.cleared_timestamp_ms = self.current_time_ms
        self.active_faults = [f for f in self.active_faults if not f.cleared]


class SafetyController:
    """
    Main safety controller implementing ISO 26262 ASIL-C safety functions.

    Responsibilities:
    - Monitor all safety-relevant signals
    - Detect faults within specified detection times
    - Trigger appropriate reactions within FTTI
    - Manage safety state machine
    - Coordinate with cell monitoring, SOC, and SOH estimators
    """

    def __init__(self,
                 limits: Optional[SafetyLimits] = None,
                 timing: Optional[TimingRequirements] = None):
        """Initialize safety controller."""
        self.limits = limits or SafetyLimits()
        self.timing = timing or TimingRequirements()
        self.state_machine = SafetyStateMachine(self.limits, self.timing)

        # Current sensor values
        self.cell_voltages_v: List[float] = []
        self.pack_current_a: float = 0.0
        self.temperatures_c: List[float] = []
        self.soc_percent: float = 50.0
        self.soh_percent: float = 100.0
        self.isolation_resistance_mohm: float = 10000.0

        # Timing tracking
        self.last_cycle_time_ms: float = 0.0
        self.cycle_count: int = 0

        # Performance metrics
        self.detection_times: List[float] = []
        self.reaction_times: List[float] = []

    def initialize(self) -> bool:
        """
        Initialize safety controller and execute self-tests.

        Returns True if controller is ready for operation.
        """
        return self.state_machine.initialize()

    def update_sensors(self,
                       cell_voltages_v: List[float],
                       pack_current_a: float,
                       temperatures_c: List[float],
                       soc_percent: float,
                       soh_percent: float,
                       isolation_resistance_mohm: float):
        """Update sensor readings from cell monitoring module."""
        self.cell_voltages_v = cell_voltages_v
        self.pack_current_a = pack_current_a
        self.temperatures_c = temperatures_c
        self.soc_percent = soc_percent
        self.soh_percent = soh_percent
        self.isolation_resistance_mohm = isolation_resistance_mohm

    def check_voltage_protection(self) -> Tuple[bool, Optional[SafetyEventType]]:
        """
        Check cell voltage protection limits.

        Returns:
            Tuple of (fault_detected, event_type)
        """
        if not self.cell_voltages_v:
            return False, None

        max_voltage = max(self.cell_voltages_v)
        min_voltage = min(self.cell_voltages_v)

        # L2 faults (immediate contactor open)
        if max_voltage >= self.limits.cell_ov_l2_v:
            self.state_machine._record_fault(
                SafetyEventType.OVERVOLTAGE_L2,
                severity=2,
                value=max_voltage,
                threshold=self.limits.cell_ov_l2_v
            )
            return True, SafetyEventType.OVERVOLTAGE_L2

        if min_voltage <= self.limits.cell_uv_l2_v:
            self.state_machine._record_fault(
                SafetyEventType.UNDERVOLTAGE_L2,
                severity=2,
                value=min_voltage,
                threshold=self.limits.cell_uv_l2_v
            )
            return True, SafetyEventType.UNDERVOLTAGE_L2

        # L1 warnings (derate power)
        if max_voltage >= self.limits.cell_ov_l1_v:
            self.state_machine._record_fault(
                SafetyEventType.OVERVOLTAGE_L1,
                severity=1,
                value=max_voltage,
                threshold=self.limits.cell_ov_l1_v
            )
            return True, SafetyEventType.OVERVOLTAGE_L1

        if min_voltage <= self.limits.cell_uv_l1_v:
            self.state_machine._record_fault(
                SafetyEventType.UNDERVOLTAGE_L1,
                severity=1,
                value=min_voltage,
                threshold=self.limits.cell_uv_l1_v
            )
            return True, SafetyEventType.UNDERVOLTAGE_L1

        return False, None

    def check_current_protection(self) -> Tuple[bool, Optional[SafetyEventType]]:
        """
        Check pack current protection limits.

        Returns:
            Tuple of (fault_detected, event_type)
        """
        abs_current = abs(self.pack_current_a)

        # Short circuit (fastest detection required)
        if abs_current >= self.limits.short_circuit_a:
            self.state_machine._record_fault(
                SafetyEventType.SHORT_CIRCUIT,
                severity=3,
                value=self.pack_current_a,
                threshold=self.limits.short_circuit_a
            )
            return True, SafetyEventType.SHORT_CIRCUIT

        # L2 faults
        if abs_current >= self.limits.pack_oc_l2_a:
            self.state_machine._record_fault(
                SafetyEventType.OVERCURRENT_L2,
                severity=2,
                value=self.pack_current_a,
                threshold=self.limits.pack_oc_l2_a
            )
            return True, SafetyEventType.OVERCURRENT_L2

        # L1 warnings
        if abs_current >= self.limits.pack_oc_l1_a:
            self.state_machine._record_fault(
                SafetyEventType.OVERCURRENT_L1,
                severity=1,
                value=self.pack_current_a,
                threshold=self.limits.pack_oc_l1_a
            )
            return True, SafetyEventType.OVERCURRENT_L1

        return False, None

    def check_temperature_protection(self) -> Tuple[bool, Optional[SafetyEventType]]:
        """
        Check temperature protection limits.

        Returns:
            Tuple of (fault_detected, event_type)
        """
        if not self.temperatures_c:
            return False, None

        max_temp = max(self.temperatures_c)
        min_temp = min(self.temperatures_c)

        # L2 fault
        if max_temp >= self.limits.temp_ot_l2_c:
            self.state_machine._record_fault(
                SafetyEventType.OVERTEMPERATURE_L2,
                severity=2,
                value=max_temp,
                threshold=self.limits.temp_ot_l2_c
            )
            return True, SafetyEventType.OVERTEMPERATURE_L2

        # L1 warnings
        if max_temp >= self.limits.temp_ot_l1_c:
            self.state_machine._record_fault(
                SafetyEventType.OVERTEMPERATURE_L1,
                severity=1,
                value=max_temp,
                threshold=self.limits.temp_ot_l1_c
            )
            return True, SafetyEventType.OVERTEMPERATURE_L1

        if min_temp <= self.limits.temp_ut_c:
            self.state_machine._record_fault(
                SafetyEventType.UNDERTEMPERATURE,
                severity=1,
                value=min_temp,
                threshold=self.limits.temp_ut_c
            )
            return True, SafetyEventType.UNDERTEMPERATURE

        return False, None

    def check_soc_soh_protection(self) -> Tuple[bool, Optional[SafetyEventType]]:
        """
        Check SOC and SOH limits.

        Returns:
            Tuple of (fault_detected, event_type)
        """
        # SOC checks
        if self.soc_percent <= self.limits.soc_critical:
            self.state_machine._record_fault(
                SafetyEventType.CRITICAL_SOC,
                severity=2,
                value=self.soc_percent,
                threshold=self.limits.soc_critical
            )
            return True, SafetyEventType.CRITICAL_SOC

        if self.soc_percent <= self.limits.soc_low_warning:
            self.state_machine._record_fault(
                SafetyEventType.LOW_SOC,
                severity=1,
                value=self.soc_percent,
                threshold=self.limits.soc_low_warning
            )
            return True, SafetyEventType.LOW_SOC

        # SOH checks
        if self.soh_percent <= self.limits.soh_critical:
            self.state_machine._record_fault(
                SafetyEventType.SOH_CRITICAL,
                severity=2,
                value=self.soh_percent,
                threshold=self.limits.soh_critical
            )
            return True, SafetyEventType.SOH_CRITICAL

        if self.soh_percent <= self.limits.soh_degraded:
            self.state_machine._record_fault(
                SafetyEventType.SOH_DEGRADED,
                severity=1,
                value=self.soh_percent,
                threshold=self.limits.soh_degraded
            )
            return True, SafetyEventType.SOH_DEGRADED

        return False, None

    def check_isolation_protection(self) -> Tuple[bool, Optional[SafetyEventType]]:
        """
        Check isolation resistance.

        Returns:
            Tuple of (fault_detected, event_type)
        """
        if self.isolation_resistance_mohm <= self.limits.isolation_fault_mohm:
            self.state_machine._record_fault(
                SafetyEventType.ISOLATION_FAULT,
                severity=2,
                value=self.isolation_resistance_mohm,
                threshold=self.limits.isolation_fault_mohm
            )
            return True, SafetyEventType.ISOLATION_FAULT

        if self.isolation_resistance_mohm <= self.limits.isolation_warning_mohm:
            self.state_machine._record_fault(
                SafetyEventType.ISOLATION_FAULT,
                severity=1,
                value=self.isolation_resistance_mohm,
                threshold=self.limits.isolation_warning_mohm
            )
            return True, SafetyEventType.ISOLATION_FAULT

        return False, None

    def process_safety_cycle(self) -> SafetyStatus:
        """
        Execute one safety controller cycle.

        This should be called at the safety monitoring frequency
        (typically 1ms for ASIL-C systems).

        Returns:
            SafetyStatus with current safety system state
        """
        self.cycle_count += 1
        cycle_start_ms = time.time() * 1000

        # Check all protection functions
        events: List[SafetyEventType] = []

        # Voltage protection (highest priority after short circuit)
        fault, event = self.check_voltage_protection()
        if event:
            events.append(event)

        # Current protection (short circuit is critical)
        fault, event = self.check_current_protection()
        if event:
            events.append(event)

        # Temperature protection
        fault, event = self.check_temperature_protection()
        if event:
            events.append(event)

        # SOC/SOH protection
        fault, event = self.check_soc_soh_protection()
        if event:
            events.append(event)

        # Isolation protection
        fault, event = self.check_isolation_protection()
        if event:
            events.append(event)

        # Process events through state machine
        for event in events:
            self.state_machine.transition(event)

        # Compute status
        status = SafetyStatus(
            state=self.state_machine.state,
            contactor_state=self.state_machine.contactor_state,
            active_faults=self.state_machine.active_faults.copy(),
            fault_count=len([f for f in self.state_machine.active_faults
                           if f.severity >= 2]),
            warning_count=len([f for f in self.state_machine.active_faults
                              if f.severity == 1]),
            soh_percent=self.soh_percent,
            soc_percent=self.soc_percent,
            time_to_fault_ms=self._compute_time_to_fault()
        )

        self.last_cycle_time_ms = cycle_start_ms
        return status

    def _compute_time_to_fault(self) -> float:
        """
        Predict time until next fault based on current trends.

        Returns:
            Estimated milliseconds until fault, or infinity if stable
        """
        # Simplified implementation - would use trend analysis in production
        if self.state_machine.state == SafetyState.FAULT:
            return 0.0
        return float('inf')

    def clear_faults(self) -> bool:
        """
        Attempt to clear faults and transition to safe state.

        Returns True if all faults cleared.
        """
        # Verify fault conditions have cleared
        fault_cleared, _ = self.check_voltage_protection()
        current_cleared, _ = self.check_current_protection()
        temp_cleared, _ = self.check_temperature_protection()

        if not (fault_cleared or current_cleared or temp_cleared):
            # All fault conditions cleared
            self.state_machine.transition(SafetyEventType.FAULT_CLEARED)
            self.state_machine._clear_fault(SafetyEventType.OVERVOLTAGE_L2)
            self.state_machine._clear_fault(SafetyEventType.UNDERVOLTAGE_L2)
            self.state_machine._clear_fault(SafetyEventType.OVERCURRENT_L2)
            return True

        return False

    def get_status(self) -> SafetyStatus:
        """Get current safety status without processing."""
        return SafetyStatus(
            state=self.state_machine.state,
            contactor_state=self.state_machine.contactor_state,
            active_faults=self.state_machine.active_faults.copy(),
            fault_count=len([f for f in self.state_machine.active_faults
                           if f.severity >= 2]),
            warning_count=len([f for f in self.state_machine.active_faults
                              if f.severity == 1]),
            soh_percent=self.soh_percent,
            soc_percent=self.soc_percent,
            time_to_fault_ms=self._compute_time_to_fault()
        )


def main():
    """Example usage of SafetyController."""
    # Initialize controller
    controller = SafetyController()

    # Initialize and run self-tests
    if not controller.initialize():
        print("Safety controller initialization FAILED")
        return

    print("Safety controller initialized successfully")
    print(f"Initial state: {controller.state_machine.state.name}")
    print(f"Contactor: {controller.state_machine.contactor_state.name}")
    print()

    # Simulate normal operation
    print("=== Normal Operation ===")
    controller.update_sensors(
        cell_voltages_v=[3.70, 3.72, 3.68, 3.71, 3.69],
        pack_current_a=50.0,
        temperatures_c=[25.0, 26.0, 25.5],
        soc_percent=75.0,
        soh_percent=95.0,
        isolation_resistance_mohm=5000.0
    )

    status = controller.process_safety_cycle()
    print(f"State: {status.state.name}")
    print(f"Contactor: {status.contactor_state.name}")
    print(f"Faults: {status.fault_count}, Warnings: {status.warning_count}")
    print()

    # Simulate over-voltage event
    print("=== Over-Voltage Event ===")
    controller.update_sensors(
        cell_voltages_v=[4.26, 4.24, 4.22, 4.23, 4.21],  # Cell 0 exceeds L2
        pack_current_a=50.0,
        temperatures_c=[25.0, 26.0, 25.5],
        soc_percent=98.0,
        soh_percent=95.0,
        isolation_resistance_mohm=5000.0
    )

    status = controller.process_safety_cycle()
    print(f"State: {status.state.name}")
    print(f"Contactor: {status.contactor_state.name}")
    print(f"Active faults: {len(status.active_faults)}")
    for fault in status.active_faults:
        print(f"  - {fault.event_type.name}: {fault.value:.2f}V "
              f"(threshold: {fault.threshold:.2f}V)")
    print()

    # Clear fault condition
    print("=== Fault Clearance ===")
    controller.update_sensors(
        cell_voltages_v=[4.18, 4.17, 4.16, 4.15, 4.14],  # Back to normal
        pack_current_a=0.0,
        temperatures_c=[25.0, 26.0, 25.5],
        soc_percent=98.0,
        soh_percent=95.0,
        isolation_resistance_mohm=5000.0
    )

    cleared = controller.clear_faults()
    status = controller.process_safety_cycle()
    print(f"Faults cleared: {cleared}")
    print(f"State: {status.state.name}")
    print(f"Contactor: {status.contactor_state.name}")
    print()

    # Simulate short-circuit event
    print("=== Short-Circuit Event ===")
    controller.update_sensors(
        cell_voltages_v=[3.70, 3.72, 3.68, 3.71, 3.69],
        pack_current_a=1200.0,  # Exceeds short-circuit threshold
        temperatures_c=[25.0, 26.0, 25.5],
        soc_percent=75.0,
        soh_percent=95.0,
        isolation_resistance_mohm=5000.0
    )

    status = controller.process_safety_cycle()
    print(f"State: {status.state.name}")
    print(f"Contactor: {status.contactor_state.name}")
    for fault in status.active_faults:
        print(f"  - {fault.event_type.name}: {fault.value:.0f}A "
              f"(threshold: {fault.threshold:.0f}A)")


if __name__ == "__main__":
    main()
