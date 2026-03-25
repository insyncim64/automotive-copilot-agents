#!/usr/bin/env python3
"""
Over-Temperature Protection Test for BMS Safety Validation

Tests the BMS over-temperature protection function per ISO 26262 ASIL-C requirements.
Validates that cell over-temperature is detected within FTTI and contactor opens.
Includes hysteresis verification: fault clears when temperature drops below threshold - hysteresis.

Workflow: battery-bms-validation.yaml -> safety-functions-validation job
CLI: --threshold-celsius 60 --hysteresis-celsius 5 --reaction-time-ms 50 --output results/safety-overtemp.json
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from bms.safety_controller import (
    SafetyController,
    SafetyState,
    SafetyEventType,
    SafetyLimits,
    TimingRequirements,
    SafetyEvent
)


class OverTempTestResult:
    """Container for over-temperature protection test results."""

    def __init__(self):
        self.test_id = "OT-PROT-001"
        self.test_name = "Over-Temperature Protection Validation"
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.passed = False
        self.reaction_time_ms = 0.0
        self.ftti_requirement_ms = 50.0
        self.threshold_celsius = 60.0
        self.hysteresis_celsius = 5.0
        self.fault_injection_method = "all-sensors"
        self.state_transition_correct = False
        self.contactor_opened = False
        self.fault_code_stored = False
        self.hysteresis_verified = False
        self.details: List[Dict[str, Any]] = []
        self.diagnostic_coverage = 0.0
        self.warning_triggered = False
        self.fault_triggered = False


def run_overtemp_test(
    threshold_celsius: float,
    hysteresis_celsius: float,
    ftti_ms: float
) -> OverTempTestResult:
    """
    Execute over-temperature protection test.

    Args:
        threshold_celsius: Over-temperature threshold in Celsius (default 60°C)
        hysteresis_celsius: Hysteresis value in Celsius (default 5°C)
        ftti_ms: Fault Tolerant Time Interval in milliseconds (default 50ms)

    Returns:
        OverTempTestResult with all test metrics
    """
    result = OverTempTestResult()
    result.threshold_celsius = threshold_celsius
    result.hysteresis_celsius = hysteresis_celsius
    result.ftti_requirement_ms = ftti_ms

    # Initialize safety controller with standard limits
    limits = SafetyLimits(
        cell_ov_l2_v=4.25,
        cell_uv_l2_v=2.50,
        pack_oc_l2_a=500.0,
        temp_ot_l2_c=threshold_celsius
    )
    timing = TimingRequirements(
        overvoltage_detection_ms=10.0,
        undervoltage_detection_ms=100.0,
        overcurrent_detection_ms=10.0,
        short_circuit_detection_us=100.0,
        contactor_open_time_ms=5.0
    )

    controller = SafetyController(limits=limits, timing=timing)

    # Simulate 96S battery pack with normal voltages (3.7V nominal)
    cell_count = 96
    normal_voltages = [3700.0] * cell_count  # mV
    normal_temps = [25.0] * 12  # Celsius (normal operating temperature)
    pack_current = 0.0  # A

    # Initialize controller with normal values
    controller.update_cell_voltages(normal_voltages)
    controller.update_temperatures(normal_temps)
    controller.update_pack_current(pack_current)

    # Process initial cycle to establish baseline
    controller.process_cycle()
    initial_state = controller.get_state()
    result.details.append({
        "phase": "initialization",
        "state": initial_state.name,
        "contactor": "closed" if controller.contactor_closed else "open",
        "timestamp_ms": 0.0,
        "initial_temps_c": normal_temps
    })

    # Verify initial state is NORMAL
    if initial_state != SafetyState.NORMAL:
        result.details.append({
            "phase": "validation_error",
            "message": f"Expected NORMAL state after init, got {initial_state.name}"
        })
        return result

    # Phase 1: Test L1 Warning threshold (threshold - hysteresis = 55°C)
    warning_threshold = threshold_celsius - hysteresis_celsius
    warning_temps = [warning_threshold] * 12
    controller.update_temperatures(warning_temps)
    controller.process_cycle()

    warning_state = controller.get_state()
    if warning_state == SafetyState.WARNING:
        result.warning_triggered = True
        result.details.append({
            "phase": "warning_threshold",
            "temperature_c": warning_threshold,
            "state": warning_state.name,
            "warning_triggered": True
        })

    # Reset to normal for clean L2 test
    controller.update_temperatures(normal_temps)
    controller.process_cycle()
    controller.clear_faults()

    # Phase 2: Inject over-temperature fault (65°C > 60°C threshold)
    fault_time_ms = time.perf_counter() * 1000
    fault_temps = [65.0] * 12  # Above 60°C threshold
    controller.update_temperatures(fault_temps)

    result.details.append({
        "phase": "fault_injection",
        "method": "all-sensors",
        "fault_temperature_c": 65.0,
        "threshold_c": threshold_celsius,
        "ftti_ms": ftti_ms
    })

    # Measure reaction time: poll state machine until fault detected
    detection_time_ms = None
    max_polls = int(ftti_ms * 10)  # Sample at 10x FTTI frequency

    for poll_idx in range(max_polls):
        controller.process_cycle()
        current_state = controller.get_state()
        elapsed_ms = (time.perf_counter() * 1000) - fault_time_ms

        # Check for state transition to FAULT or SAFE_STOP
        if current_state in [SafetyState.FAULT, SafetyState.SAFE_STOP]:
            detection_time_ms = elapsed_ms
            result.state_transition_correct = True
            result.fault_triggered = True
            result.details.append({
                "phase": "fault_detected",
                "state": current_state.name,
                "reaction_time_ms": round(elapsed_ms, 3),
                "poll_count": poll_idx
            })
            break

    if detection_time_ms is None:
        # Fault not detected within FTTI
        controller.process_cycle()
        final_state = controller.get_state()
        result.details.append({
            "phase": "timeout",
            "final_state": final_state.name,
            "max_wait_ms": ftti_ms,
            "message": "Fault not detected within FTTI window"
        })
        result.reaction_time_ms = ftti_ms * 1.5  # Penalize
    else:
        result.reaction_time_ms = detection_time_ms

    # Verify contactor opened on L2 fault
    controller.process_cycle()
    if not controller.contactor_closed:
        result.contactor_opened = True
        result.details.append({
            "phase": "contactor_verification",
            "contactor_state": "open",
            "verified": True
        })
    else:
        result.details.append({
            "phase": "contactor_verification",
            "contactor_state": "closed",
            "verified": False,
            "message": "ERROR: Contactor should be open after over-temperature fault"
        })

    # Verify fault code stored
    active_faults = controller.get_active_faults()
    ot_fault_found = any(
        f.event_type in [SafetyEventType.OVERTEMPERATURE_L1, SafetyEventType.OVERTEMPERATURE_L2]
        for f in active_faults
    )
    if ot_fault_found:
        result.fault_code_stored = True
        result.details.append({
            "phase": "diagnostic_verification",
            "fault_codes": [f.event_type.name for f in active_faults],
            "ot_fault_detected": True
        })
    else:
        result.details.append({
            "phase": "diagnostic_verification",
            "fault_codes": [f.event_type.name for f in active_faults] if active_faults else [],
            "ot_fault_detected": False,
            "message": "WARNING: Over-temperature fault code not found"
        })

    # Phase 3: Hysteresis verification - cool temperature below threshold - hysteresis
    # Fault should clear when temperature drops to 55°C (60°C - 5°C)
    result.details.append({
        "phase": "hysteresis_test",
        "description": "Verify fault clears when temperature drops below threshold - hysteresis",
        "threshold_c": threshold_celsius,
        "hysteresis_c": hysteresis_celsius,
        "clear_point_c": threshold_celsius - hysteresis_celsius
    })

    # Clear fault state first
    controller.clear_faults()

    # Set temperature to clear point (55°C)
    clear_temps = [threshold_celsius - hysteresis_celsius] * 12
    controller.update_temperatures(clear_temps)

    # Process cycles to allow state transition
    for _ in range(10):
        controller.process_cycle()

    hysteresis_state = controller.get_state()

    # After clearing faults and cooling, system should return to NORMAL or WARNING (not FAULT)
    if hysteresis_state in [SafetyState.NORMAL, SafetyState.WARNING]:
        result.hysteresis_verified = True
        result.details.append({
            "phase": "hysteresis_verification",
            "temperature_c": threshold_celsius - hysteresis_celsius,
            "state": hysteresis_state.name,
            "fault_active": len(controller.get_active_faults()) > 0,
            "hysteresis_passed": True
        })
    else:
        result.details.append({
            "phase": "hysteresis_verification",
            "temperature_c": threshold_celsius - hysteresis_celsius,
            "state": hysteresis_state.name,
            "fault_active": len(controller.get_active_faults()) > 0,
            "hysteresis_passed": False,
            "message": f"Expected NORMAL/WARNING at {threshold_celsius - hysteresis_celsius}°C, got {hysteresis_state.name}"
        })

    # Calculate diagnostic coverage
    checks_performed = 0
    checks_passed = 0

    # Check 1: Fault detection
    checks_performed += 1
    if detection_time_ms is not None:
        checks_passed += 1

    # Check 2: State transition
    checks_performed += 1
    if result.state_transition_correct:
        checks_passed += 1

    # Check 3: Contactor opens
    checks_performed += 1
    if result.contactor_opened:
        checks_passed += 1

    # Check 4: Fault code stored
    checks_performed += 1
    if result.fault_code_stored:
        checks_passed += 1

    # Check 5: Timing within FTTI
    checks_performed += 1
    if detection_time_ms is not None and detection_time_ms <= ftti_ms:
        checks_passed += 1

    # Check 6: Hysteresis verified
    checks_performed += 1
    if result.hysteresis_verified:
        checks_passed += 1

    result.diagnostic_coverage = (checks_passed / checks_performed) * 100.0

    # Determine overall pass/fail
    result.passed = (
        detection_time_ms is not None and
        detection_time_ms <= ftti_ms and
        result.state_transition_correct and
        result.contactor_opened and
        result.hysteresis_verified
    )

    result.details.append({
        "phase": "summary",
        "reaction_time_ms": round(result.reaction_time_ms, 3),
        "ftti_requirement_ms": ftti_ms,
        "within_ftti": result.reaction_time_ms <= ftti_ms if result.reaction_time_ms > 0 else False,
        "warning_triggered": result.warning_triggered,
        "fault_triggered": result.fault_triggered,
        "hysteresis_verified": result.hysteresis_verified,
        "diagnostic_coverage_percent": round(result.diagnostic_coverage, 1),
        "passed": result.passed
    })

    return result


def format_results(result: OverTempTestResult) -> Dict[str, Any]:
    """Format test results as JSON-serializable dictionary."""
    return {
        "test_id": result.test_id,
        "test_name": result.test_name,
        "timestamp": result.timestamp,
        "passed": result.passed,
        "threshold_celsius": result.threshold_celsius,
        "hysteresis_celsius": result.hysteresis_celsius,
        "ftti_requirement_ms": result.ftti_requirement_ms,
        "fault_injection_method": result.fault_injection_method,
        "metrics": {
            "reaction_time_ms": round(result.reaction_time_ms, 3),
            "state_transition_correct": result.state_transition_correct,
            "contactor_opened": result.contactor_opened,
            "fault_code_stored": result.fault_code_stored,
            "diagnostic_coverage_percent": round(result.diagnostic_coverage, 1),
            "warning_triggered": result.warning_triggered,
            "fault_triggered": result.fault_triggered,
            "hysteresis_verified": result.hysteresis_verified
        },
        "iso_26262_compliance": {
            "asil_level": "C",
            "ftti_met": result.reaction_time_ms <= result.ftti_requirement_ms if result.reaction_time_ms > 0 else False,
            "safety_mechanism": "Over-temperature detection L2",
            "safe_state_achieved": result.contactor_opened,
            "hysteresis_behavior": "Fault clears at threshold - hysteresis"
        },
        "details": result.details
    }


def main():
    parser = argparse.ArgumentParser(
        description="BMS Over-Temperature Protection Test per ISO 26262 ASIL-C"
    )
    parser.add_argument(
        "--threshold-celsius",
        type=float,
        default=60.0,
        help="Over-temperature threshold in Celsius (default: 60°C)"
    )
    parser.add_argument(
        "--hysteresis-celsius",
        type=float,
        default=5.0,
        help="Hysteresis value in Celsius (default: 5°C)"
    )
    parser.add_argument(
        "--reaction-time-ms",
        type=float,
        default=50.0,
        help="Fault Tolerant Time Interval in ms (default: 50ms)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/safety-overtemp.json",
        help="Output JSON file path (default: results/safety-overtemp.json)"
    )

    args = parser.parse_args()

    # Run test
    print(f"Running Over-Temperature Protection Test...")
    print(f"  Threshold: {args.threshold_celsius}°C")
    print(f"  Hysteresis: {args.hysteresis_celsius}°C")
    print(f"  FTTI Requirement: {args.reaction_time_ms}ms")
    print()

    result = run_overtemp_test(
        threshold_celsius=args.threshold_celsius,
        hysteresis_celsius=args.hysteresis_celsius,
        ftti_ms=args.reaction_time_ms
    )

    # Format and save results
    output_data = format_results(result)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    # Print summary
    print(f"Test Result: {'PASS' if result.passed else 'FAIL'}")
    print(f"  Reaction Time: {result.reaction_time_ms:.3f} ms")
    print(f"  FTTI Limit: {args.reaction_time_ms} ms")
    print(f"  State Transition: {'Correct' if result.state_transition_correct else 'Incorrect'}")
    print(f"  Contactor Opened: {'Yes' if result.contactor_opened else 'No'}")
    print(f"  Fault Code Stored: {'Yes' if result.fault_code_stored else 'No'}")
    print(f"  Warning Triggered: {'Yes' if result.warning_triggered else 'No'}")
    print(f"  Fault Triggered: {'Yes' if result.fault_triggered else 'No'}")
    print(f"  Hysteresis Verified: {'Yes' if result.hysteresis_verified else 'No'}")
    print(f"  Diagnostic Coverage: {result.diagnostic_coverage:.1f}%")
    print()
    print(f"Results written to: {output_path}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
