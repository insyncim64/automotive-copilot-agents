#!/usr/bin/env python3
"""
Over-Voltage Protection Test for BMS Safety Validation

Tests the BMS over-voltage protection function per ISO 26262 ASIL-C requirements.
Validates that cell over-voltage is detected within FTTI and contactor opens.

Workflow: battery-bms-validation.yaml -> safety-functions-validation job
CLI: --threshold-v 4.25 --reaction-time-ms 10 --fault-injection all-cells --output results/safety-overvoltage.json
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


class OverVoltageTestResult:
    """Container for over-voltage protection test results."""

    def __init__(self):
        self.test_id = "OV-PROT-001"
        self.test_name = "Over-Voltage Protection Validation"
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.passed = False
        self.reaction_time_ms = 0.0
        self.ftti_requirement_ms = 10.0
        self.threshold_v = 4.25
        self.fault_injection_method = "all-cells"
        self.state_transition_correct = False
        self.contactor_opened = False
        self.fault_code_stored = False
        self.details: List[Dict[str, Any]] = []
        self.diagnostic_coverage = 0.0


def run_overvoltage_test(
    threshold_v: float,
    ftti_ms: float,
    fault_injection: str
) -> OverVoltageTestResult:
    """
    Execute over-voltage protection test.

    Args:
        threshold_v: Over-voltage threshold in volts (default 4.25V)
        ftti_ms: Fault Tolerant Time Interval in milliseconds (default 10ms)
        fault_injection: Injection method - "all-cells" or "single-cell"

    Returns:
        OverVoltageTestResult with all test metrics
    """
    result = OverVoltageTestResult()
    result.threshold_v = threshold_v
    result.ftti_requirement_ms = ftti_ms
    result.fault_injection_method = fault_injection

    # Initialize safety controller with standard limits
    limits = SafetyLimits(
        cell_ov_l2_v=threshold_v,
        cell_uv_l2_v=2.50,
        pack_oc_l2_a=500.0,
        temp_ot_l2_c=60.0
    )
    timing = TimingRequirements(
        overvoltage_detection_ms=ftti_ms,
        undervoltage_detection_ms=100.0,
        overcurrent_detection_ms=10.0,
        short_circuit_detection_us=100.0,
        contactor_open_time_ms=5.0
    )

    controller = SafetyController(limits=limits, timing=timing)

    # Simulate 96S battery pack with normal voltages (3.7V nominal)
    cell_count = 96
    normal_voltages = [3700.0] * cell_count  # mV
    normal_temps = [25.0] * 12  # Celsius
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
        "timestamp_ms": 0.0
    })

    # Verify initial state is NORMAL
    if initial_state != SafetyState.NORMAL:
        result.details.append({
            "phase": "validation_error",
            "message": f"Expected NORMAL state after init, got {initial_state.name}"
        })
        return result

    # Inject over-voltage fault on all cells
    fault_time_ms = time.perf_counter() * 1000
    fault_injected = False

    if fault_injection == "all-cells":
        # Set all cells to 4.3V (above 4.25V threshold)
        fault_voltages = [4300.0] * cell_count
        controller.update_cell_voltages(fault_voltages)
        fault_injected = True
        result.details.append({
            "phase": "fault_injection",
            "method": "all-cells",
            "fault_voltage_mv": 4300.0,
            "threshold_mv": threshold_v * 1000,
            "cells_affected": cell_count
        })
    elif fault_injection == "single-cell":
        # Set cell 0 to 4.3V (tests single-cell detection)
        fault_voltages = normal_voltages.copy()
        fault_voltages[0] = 4300.0
        controller.update_cell_voltages(fault_voltages)
        fault_injected = True
        result.details.append({
            "phase": "fault_injection",
            "method": "single-cell",
            "fault_voltage_mv": 4300.0,
            "threshold_mv": threshold_v * 1000,
            "cell_index": 0
        })
    else:
        result.details.append({
            "phase": "fault_injection",
            "error": f"Unknown fault injection method: {fault_injection}"
        })
        return result

    if not fault_injected:
        return result

    # Measure reaction time: poll state machine until fault detected
    detection_time_ms = None
    state_before_fault = initial_state
    max_polls = int(ftti_ms * 10)  # Sample at 10x FTTI frequency
    poll_interval_ms = 0.1  # 100 Hz polling

    for poll_idx in range(max_polls):
        # Process safety cycle
        controller.process_cycle()

        current_state = controller.get_state()
        elapsed_ms = (time.perf_counter() * 1000) - fault_time_ms

        # Check for state transition to FAULT or SAFE_STOP
        if current_state in [SafetyState.FAULT, SafetyState.SAFE_STOP]:
            detection_time_ms = elapsed_ms
            result.state_transition_correct = True
            result.details.append({
                "phase": "fault_detected",
                "state": current_state.name,
                "reaction_time_ms": round(elapsed_ms, 3),
                "poll_count": poll_idx
            })
            break

        state_before_fault = current_state

    if detection_time_ms is None:
        # Fault not detected within FTTI - check if at least WARNING state
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

    # Verify contactor opened
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
            "message": "ERROR: Contactor should be open after fault"
        })

    # Verify fault code stored
    active_faults = controller.get_active_faults()
    ov_fault_found = any(
        f.event_type in [SafetyEventType.OVERVOLTAGE_L1, SafetyEventType.OVERVOLTAGE_L2]
        for f in active_faults
    )
    if ov_fault_found:
        result.fault_code_stored = True
        result.details.append({
            "phase": "diagnostic_verification",
            "fault_codes": [f.event_type.name for f in active_faults],
            "ov_fault_detected": True
        })
    else:
        result.details.append({
            "phase": "diagnostic_verification",
            "fault_codes": [f.event_type.name for f in active_faults] if active_faults else [],
            "ov_fault_detected": False,
            "message": "WARNING: Over-voltage fault code not found"
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

    result.diagnostic_coverage = (checks_passed / checks_performed) * 100.0

    # Determine overall pass/fail
    result.passed = (
        detection_time_ms is not None and
        detection_time_ms <= ftti_ms and
        result.state_transition_correct and
        result.contactor_opened
    )

    result.details.append({
        "phase": "summary",
        "reaction_time_ms": round(result.reaction_time_ms, 3),
        "ftti_requirement_ms": ftti_ms,
        "within_ftti": result.reaction_time_ms <= ftti_ms,
        "diagnostic_coverage_percent": round(result.diagnostic_coverage, 1),
        "passed": result.passed
    })

    return result


def format_results(result: OverVoltageTestResult) -> Dict[str, Any]:
    """Format test results as JSON-serializable dictionary."""
    return {
        "test_id": result.test_id,
        "test_name": result.test_name,
        "timestamp": result.timestamp,
        "passed": result.passed,
        "threshold_v": result.threshold_v,
        "ftti_requirement_ms": result.ftti_requirement_ms,
        "fault_injection_method": result.fault_injection_method,
        "metrics": {
            "reaction_time_ms": round(result.reaction_time_ms, 3),
            "state_transition_correct": result.state_transition_correct,
            "contactor_opened": result.contactor_opened,
            "fault_code_stored": result.fault_code_stored,
            "diagnostic_coverage_percent": round(result.diagnostic_coverage, 1)
        },
        "iso_26262_compliance": {
            "asil_level": "C",
            "ftti_met": result.reaction_time_ms <= result.ftti_requirement_ms,
            "safety_mechanism": "Over-voltage detection L2",
            "safe_state_achieved": result.contactor_opened
        },
        "details": result.details
    }


def main():
    parser = argparse.ArgumentParser(
        description="BMS Over-Voltage Protection Test per ISO 26262 ASIL-C"
    )
    parser.add_argument(
        "--threshold-v",
        type=float,
        default=4.25,
        help="Over-voltage threshold in volts (default: 4.25V)"
    )
    parser.add_argument(
        "--reaction-time-ms",
        type=float,
        default=10.0,
        help="Fault Tolerant Time Interval in ms (default: 10ms)"
    )
    parser.add_argument(
        "--fault-injection",
        type=str,
        default="all-cells",
        choices=["all-cells", "single-cell"],
        help="Fault injection method (default: all-cells)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/safety-overvoltage.json",
        help="Output JSON file path (default: results/safety-overvoltage.json)"
    )

    args = parser.parse_args()

    # Run test
    print(f"Running Over-Voltage Protection Test...")
    print(f"  Threshold: {args.threshold_v}V")
    print(f"  FTTI Requirement: {args.reaction_time_ms}ms")
    print(f"  Fault Injection: {args.fault_injection}")
    print()

    result = run_overvoltage_test(
        threshold_v=args.threshold_v,
        ftti_ms=args.reaction_time_ms,
        fault_injection=args.fault_injection
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
    print(f"  Diagnostic Coverage: {result.diagnostic_coverage:.1f}%")
    print()
    print(f"Results written to: {output_path}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
