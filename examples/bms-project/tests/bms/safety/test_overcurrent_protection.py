#!/usr/bin/env python3
"""
Over-Current Protection Test for BMS Safety Validation

Tests the BMS over-current protection function per ISO 26262 ASIL-C requirements.
Validates that pack overcurrent is detected within FTTI and contactor opens.

Workflow: battery-bms-validation.yaml -> safety-functions-validation job
CLI: --threshold-a 500 --reaction-time-ms 10 --fault-injection charge-and-discharge --output results/safety-overcurrent.json
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


class OverCurrentTestResult:
    """Container for over-current protection test results."""

    def __init__(self):
        self.test_id = "OC-PROT-001"
        self.test_name = "Over-Current Protection Validation"
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.passed = False
        self.reaction_time_ms = 0.0
        self.ftti_requirement_ms = 10.0
        self.threshold_a = 500.0
        self.fault_injection_method = "charge-and-discharge"
        self.state_transition_correct = False
        self.contactor_opened = False
        self.fault_code_stored = False
        self.details: List[Dict[str, Any]] = []
        self.diagnostic_coverage = 0.0
        self.charge_fault_detected = False
        self.discharge_fault_detected = False


def run_overcurrent_test(
    threshold_a: float,
    ftti_ms: float,
    fault_injection: str
) -> OverCurrentTestResult:
    """
    Execute over-current protection test.

    Args:
        threshold_a: Over-current threshold in Amperes (default 500A)
        ftti_ms: Fault Tolerant Time Interval in milliseconds (default 10ms)
        fault_injection: Injection method - "charge", "discharge", or "charge-and-discharge"

    Returns:
        OverCurrentTestResult with all test metrics
    """
    result = OverCurrentTestResult()
    result.threshold_a = threshold_a
    result.ftti_requirement_ms = ftti_ms
    result.fault_injection_method = fault_injection

    # Initialize safety controller with standard limits
    limits = SafetyLimits(
        cell_ov_l2_v=4.25,
        cell_uv_l2_v=2.50,
        pack_oc_l2_a=threshold_a,
        temp_ot_l2_c=60.0
    )
    timing = TimingRequirements(
        overvoltage_detection_ms=10.0,
        undervoltage_detection_ms=100.0,
        overcurrent_detection_ms=ftti_ms,
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

    # Test overcurrent fault injection
    fault_injected = False
    fault_results = []

    if fault_injection == "charge":
        # Test charge overcurrent (+520A, above +500A threshold)
        fault_result = _inject_overcurrent_fault(
            controller=controller,
            current_a=520.0,
            fault_type="charge",
            ftti_ms=ftti_ms,
            threshold_a=threshold_a
        )
        fault_results.append(fault_result)
        fault_injected = True
        result.charge_fault_detected = fault_result["detected"]
        result.reaction_time_ms = fault_result["reaction_time_ms"]
        result.state_transition_correct = fault_result["state_transition_correct"]
        result.details.append(fault_result)

    elif fault_injection == "discharge":
        # Test discharge overcurrent (-520A, below -500A threshold)
        fault_result = _inject_overcurrent_fault(
            controller=controller,
            current_a=-520.0,
            fault_type="discharge",
            ftti_ms=ftti_ms,
            threshold_a=threshold_a
        )
        fault_results.append(fault_result)
        fault_injected = True
        result.discharge_fault_detected = fault_result["detected"]
        result.reaction_time_ms = fault_result["reaction_time_ms"]
        result.state_transition_correct = fault_result["state_transition_correct"]
        result.details.append(fault_result)

    elif fault_injection == "charge-and-discharge":
        # Test both charge and discharge overcurrent
        # Reset controller state between tests
        controller.update_pack_current(0.0)
        controller.process_cycle()

        # Test charge overcurrent first
        charge_result = _inject_overcurrent_fault(
            controller=controller,
            current_a=520.0,
            fault_type="charge",
            ftti_ms=ftti_ms,
            threshold_a=threshold_a
        )
        fault_results.append(charge_result)
        result.charge_fault_detected = charge_result["detected"]

        # Reset for discharge test
        controller.update_pack_current(0.0)
        controller.process_cycle()
        controller.clear_faults()

        # Test discharge overcurrent
        discharge_result = _inject_overcurrent_fault(
            controller=controller,
            current_a=-520.0,
            fault_type="discharge",
            ftti_ms=ftti_ms,
            threshold_a=threshold_a
        )
        fault_results.append(discharge_result)
        result.discharge_fault_detected = discharge_result["detected"]

        # Combined result
        fault_injected = True
        result.state_transition_correct = (
            charge_result["state_transition_correct"] or
            discharge_result["state_transition_correct"]
        )
        result.reaction_time_ms = max(
            charge_result["reaction_time_ms"],
            discharge_result["reaction_time_ms"]
        )
        result.details.append({
            "phase": "charge_test",
            **charge_result
        })
        result.details.append({
            "phase": "discharge_test",
            **discharge_result
        })
        result.fault_injection_method = "charge-and-discharge"
        result.details.append({
            "phase": "fault_injection",
            "method": "charge-and-discharge",
            "charge_current_a": 520.0,
            "discharge_current_a": -520.0,
            "threshold_a": threshold_a,
            "ftti_ms": ftti_ms
        })
    else:
        result.details.append({
            "phase": "fault_injection",
            "error": f"Unknown fault injection method: {fault_injection}"
        })
        return result

    if not fault_injected:
        return result

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
    oc_fault_found = any(
        f.event_type in [SafetyEventType.OVERCURRENT_L1, SafetyEventType.OVERCURRENT_L2]
        for f in active_faults
    )
    if oc_fault_found:
        result.fault_code_stored = True
        result.details.append({
            "phase": "diagnostic_verification",
            "fault_codes": [f.event_type.name for f in active_faults],
            "oc_fault_detected": True
        })
    else:
        result.details.append({
            "phase": "diagnostic_verification",
            "fault_codes": [f.event_type.name for f in active_faults] if active_faults else [],
            "oc_fault_detected": False,
            "message": "WARNING: Over-current fault code not found"
        })

    # Calculate diagnostic coverage
    checks_performed = 0
    checks_passed = 0

    # Check 1: Fault detection
    checks_performed += 1
    if any(fr.get("detected", False) for fr in fault_results):
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
    if result.reaction_time_ms <= ftti_ms:
        checks_passed += 1

    result.diagnostic_coverage = (checks_passed / checks_performed) * 100.0

    # Determine overall pass/fail
    result.passed = (
        result.reaction_time_ms <= ftti_ms and
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


def _inject_overcurrent_fault(
    controller: SafetyController,
    current_a: float,
    fault_type: str,
    ftti_ms: float,
    threshold_a: float
) -> Dict[str, Any]:
    """
    Inject overcurrent fault and measure reaction time.

    Args:
        controller: SafetyController instance
        current_a: Current to inject (positive=charge, negative=discharge)
        fault_type: "charge" or "discharge"
        ftti_ms: FTTI requirement in milliseconds
        threshold_a: Current threshold in Amperes

    Returns:
        Dictionary with fault detection results
    """
    result = {
        "detected": False,
        "reaction_time_ms": 0.0,
        "state_transition_correct": False,
        "fault_type": fault_type,
        "current_a": current_a,
        "threshold_a": threshold_a
    }

    # Record fault injection time
    fault_time_ms = time.perf_counter() * 1000

    # Inject overcurrent fault
    controller.update_pack_current(current_a)

    # Measure reaction time: poll state machine until fault detected
    detection_time_ms = None
    max_polls = int(ftti_ms * 10)  # Sample at 10x FTTI frequency

    for poll_idx in range(max_polls):
        # Process safety cycle
        controller.process_cycle()

        current_state = controller.get_state()
        elapsed_ms = (time.perf_counter() * 1000) - fault_time_ms

        # Check for state transition to FAULT or SAFE_STOP
        if current_state in [SafetyState.FAULT, SafetyState.SAFE_STOP]:
            detection_time_ms = elapsed_ms
            result["state_transition_correct"] = True
            result["reaction_time_ms"] = round(elapsed_ms, 3)
            result["poll_count"] = poll_idx
            break

    if detection_time_ms is not None:
        result["detected"] = True
        result["reaction_time_ms"] = round(detection_time_ms, 3)
    else:
        # Fault not detected within FTTI
        controller.process_cycle()
        final_state = controller.get_state()
        result["final_state"] = final_state.name
        result["max_wait_ms"] = ftti_ms
        result["message"] = "Fault not detected within FTTI window"
        result["reaction_time_ms"] = ftti_ms * 1.5  # Penalize

    return result


def format_results(result: OverCurrentTestResult) -> Dict[str, Any]:
    """Format test results as JSON-serializable dictionary."""
    return {
        "test_id": result.test_id,
        "test_name": result.test_name,
        "timestamp": result.timestamp,
        "passed": result.passed,
        "threshold_a": result.threshold_a,
        "ftti_requirement_ms": result.ftti_requirement_ms,
        "fault_injection_method": result.fault_injection_method,
        "metrics": {
            "reaction_time_ms": round(result.reaction_time_ms, 3),
            "state_transition_correct": result.state_transition_correct,
            "contactor_opened": result.contactor_opened,
            "fault_code_stored": result.fault_code_stored,
            "diagnostic_coverage_percent": round(result.diagnostic_coverage, 1),
            "charge_fault_detected": result.charge_fault_detected,
            "discharge_fault_detected": result.discharge_fault_detected
        },
        "iso_26262_compliance": {
            "asil_level": "C",
            "ftti_met": result.reaction_time_ms <= result.ftti_requirement_ms,
            "safety_mechanism": "Over-current detection L2",
            "safe_state_achieved": result.contactor_opened
        },
        "details": result.details
    }


def main():
    parser = argparse.ArgumentParser(
        description="BMS Over-Current Protection Test per ISO 26262 ASIL-C"
    )
    parser.add_argument(
        "--threshold-a",
        type=float,
        default=500.0,
        help="Over-current threshold in Amperes (default: 500A)"
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
        default="charge-and-discharge",
        choices=["charge", "discharge", "charge-and-discharge"],
        help="Fault injection method (default: charge-and-discharge)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="results/safety-overcurrent.json",
        help="Output JSON file path (default: results/safety-overcurrent.json)"
    )

    args = parser.parse_args()

    # Run test
    print(f"Running Over-Current Protection Test...")
    print(f"  Threshold: {args.threshold_a}A")
    print(f"  FTTI Requirement: {args.reaction_time_ms}ms")
    print(f"  Fault Injection: {args.fault_injection}")
    print()

    result = run_overcurrent_test(
        threshold_a=args.threshold_a,
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
    print(f"  Charge Fault Detected: {'Yes' if result.charge_fault_detected else 'No'}")
    print(f"  Discharge Fault Detected: {'Yes' if result.discharge_fault_detected else 'No'}")
    print(f"  Diagnostic Coverage: {result.diagnostic_coverage:.1f}%")
    print()
    print(f"Results written to: {output_path}")

    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main())
