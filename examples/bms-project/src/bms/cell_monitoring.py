"""
Battery Management System - Cell Monitoring Module

Implements cell voltage and temperature monitoring with isolation detection
and open-wire fault diagnosis per ISO 26262 ASIL-C requirements.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple
import math


class CellFaultType(Enum):
    """Cell monitoring fault types."""
    NONE = 0
    OVERVOLTAGE = 1
    UNDERVOLTAGE = 2
    OVERTEMPERATURE = 3
    UNDERTEMPERATURE = 4
    OPEN_WIRE = 5
    ISOLATION_FAULT = 6
    SENSOR_MISMATCH = 7


@dataclass
class CellStatus:
    """Status of a single cell."""
    index: int
    voltage_mv: float
    temperature_c: float
    fault: CellFaultType
    is_valid: bool


@dataclass
class PackStatus:
    """Overall battery pack status."""
    total_voltage_v: float
    pack_current_a: float
    min_cell_voltage_mv: float
    max_cell_voltage_mv: float
    avg_cell_voltage_mv: float
    cell_voltage_delta_mv: float
    min_temperature_c: float
    max_temperature_c: float
    avg_temperature_c: float
    isolation_resistance_mohm: float
    faults: List[CellFaultType]
    is_safe_to_operate: bool


class CellMonitor:
    """
    Cell voltage and temperature monitoring with safety diagnostics.

    Implements:
    - Cell voltage measurement with range validation (2.5V - 4.5V)
    - Temperature measurement with range validation (-20C to 80C)
    - Isolation resistance monitoring (>500 mohm required)
    - Open-wire detection for cell sense lines
    - Plausibility checks between adjacent cells
    """

    # Cell voltage limits (typical NMC chemistry)
    MIN_CELL_VOLTAGE_MV = 2500.0
    MAX_CELL_VOLTAGE_MV = 4500.0
    NOMINAL_CELL_VOLTAGE_MV = 3700.0

    # Cell voltage accuracy thresholds
    VOLTAGE_TOLERANCE_MV = 5.0  # ±5mV accuracy requirement
    CELL_DELTA_WARNING_MV = 50.0  # Warning if cells differ by >50mV
    CELL_DELTA_CRITICAL_MV = 100.0  # Critical if cells differ by >100mV

    # Temperature limits
    MIN_TEMPERATURE_C = -20.0
    MAX_TEMPERATURE_C = 80.0
    TEMP_TOLERANCE_C = 2.0  # ±2°C accuracy requirement
    TEMP_DERATE_C = 55.0  # Start derating at 55°C
    TEMP_CRITICAL_C = 65.0  # Critical temperature

    # Isolation monitoring
    MIN_ISOLATION_MOHM = 500.0  # Minimum isolation resistance
    ISOLATION_WARNING_MOHM = 1000.0  # Warning threshold
    FAULT_ISOLATION_MOHM = 100.0  # Fault threshold

    def __init__(self, cell_count: int = 96, temperature_sensor_count: int = 12):
        """Initialize cell monitor with configured cell and sensor count."""
        self.cell_count = cell_count
        self.temperature_sensor_count = temperature_sensor_count
        self.cell_voltages_mv: List[float] = [0.0] * cell_count
        self.cell_temperatures_c: List[float] = [25.0] * temperature_sensor_count
        self.pack_current_a = 0.0
        self.isolation_resistance_mohm = 10000.0  # Start with good isolation
        self._previous_cell_voltages: List[float] = [0.0] * cell_count
        self._open_wire_threshold_mv = 100.0  # Detect >100mV sudden change

    def update_cell_voltages(self, voltages_mv: List[float]) -> None:
        """Update cell voltage measurements."""
        if len(voltages_mv) != self.cell_count:
            raise ValueError(
                f"Expected {self.cell_count} cell voltages, got {len(voltages_mv)}")
        self._previous_cell_voltages = self.cell_voltages_mv.copy()
        self.cell_voltages_mv = voltages_mv.copy()

    def update_temperatures(self, temperatures_c: List[float]) -> None:
        """Update temperature sensor measurements."""
        if len(temperatures_c) != self.temperature_sensor_count:
            raise ValueError(
                f"Expected {self.temperature_sensor_count} temperatures, "
                f"got {len(temperatures_c)}")
        self.cell_temperatures_c = temperatures_c.copy()

    def update_pack_current(self, current_a: float) -> None:
        """Update pack current measurement (positive = charging)."""
        self.pack_current_a = current_a

    def update_isolation(self, resistance_mohm: float) -> None:
        """Update isolation resistance measurement."""
        self.isolation_resistance_mohm = resistance_mohm

    def check_cell_voltage_accuracy(self, reference_voltages_mv: List[float]) -> dict:
        """
        Validate cell voltage measurement accuracy against reference.

        Args:
            reference_voltages_mv: Reference voltages from calibrated equipment

        Returns:
            dict with accuracy metrics and pass/fail status
        """
        if len(reference_voltages_mv) != self.cell_count:
            return {
                "pass": False,
                "error": "Reference voltage count mismatch",
                "max_error_mv": float('inf'),
                "avg_error_mv": float('inf'),
                "rmse_mv": float('inf')
            }

        errors_mv = []
        for i in range(self.cell_count):
            error = abs(self.cell_voltages_mv[i] - reference_voltages_mv[i])
            errors_mv.append(error)

        max_error = max(errors_mv)
        avg_error = sum(errors_mv) / len(errors_mv)
        rmse = math.sqrt(sum(e**2 for e in errors_mv) / len(errors_mv))

        return {
            "pass": max_error <= self.VOLTAGE_TOLERANCE_MV,
            "max_error_mv": max_error,
            "avg_error_mv": avg_error,
            "rmse_mv": rmse,
            "tolerance_mv": self.VOLTAGE_TOLERANCE_MV,
            "cell_count": self.cell_count,
            "cells_within_tolerance": sum(
                1 for e in errors_mv if e <= self.VOLTAGE_TOLERANCE_MV)
        }

    def check_temperature_accuracy(self, reference_temperatures_c: List[float]) -> dict:
        """
        Validate temperature measurement accuracy against reference.

        Args:
            reference_temperatures_c: Reference temperatures from calibrated equipment

        Returns:
            dict with accuracy metrics and pass/fail status
        """
        if len(reference_temperatures_c) != self.temperature_sensor_count:
            return {
                "pass": False,
                "error": "Reference temperature count mismatch",
                "max_error_c": float('inf'),
                "avg_error_c": float('inf'),
                "rmse_c": float('inf')
            }

        errors_c = []
        for i in range(self.temperature_sensor_count):
            error = abs(self.cell_temperatures_c[i] - reference_temperatures_c[i])
            errors_c.append(error)

        max_error = max(errors_c)
        avg_error = sum(errors_c) / len(errors_c)
        rmse = math.sqrt(sum(e**2 for e in errors_c) / len(errors_c))

        return {
            "pass": max_error <= self.TEMP_TOLERANCE_C,
            "max_error_c": max_error,
            "avg_error_c": avg_error,
            "rmse_c": rmse,
            "tolerance_c": self.TEMP_TOLERANCE_C,
            "sensor_count": self.temperature_sensor_count,
            "sensors_within_tolerance": sum(
                1 for e in errors_c if e <= self.TEMP_TOLERANCE_C)
        }

    def check_isolation_monitoring(self, min_isolation_mohm: float = None,
                                    fault_threshold_mohm: float = None) -> dict:
        """
        Validate isolation monitoring functionality.

        Args:
            min_isolation_mohm: Minimum acceptable isolation resistance
            fault_threshold_mohm: Threshold for isolation fault

        Returns:
            dict with isolation status and pass/fail metrics
        """
        min_iso = min_isolation_mohm or self.MIN_ISOLATION_MOHM
        fault_iso = fault_threshold_mohm or self.FAULT_ISOLATION_MOHM

        is_above_minimum = self.isolation_resistance_mohm >= min_iso
        is_fault = self.isolation_resistance_mohm < fault_iso

        return {
            "pass": is_above_minimum,
            "isolation_resistance_mohm": self.isolation_resistance_mohm,
            "minimum_required_mohm": min_iso,
            "fault_threshold_mohm": fault_iso,
            "is_fault": is_fault,
            "is_warning": self.isolation_resistance_mohm < self.ISOLATION_WARNING_MOHM,
            "margin_mohm": self.isolation_resistance_mohm - min_iso
        }

    def check_open_wire_detection(self) -> dict:
        """
        Detect open-wire faults in cell sense lines.

        An open wire is detected when:
        - Cell voltage suddenly drops to 0 or spikes abnormally
        - Cell voltage differs from previous reading by >threshold
        - Cell voltage is implausible compared to adjacent cells

        Returns:
            dict with open-wire detection results
        """
        open_wire_cells = []
        implausible_cells = []

        for i in range(self.cell_count):
            current_v = self.cell_voltages_mv[i]
            previous_v = self._previous_cell_voltages[i] if i < len(self._previous_cell_voltages) else 0

            # Check for sudden voltage loss (open wire)
            if previous_v > 0:
                delta = abs(current_v - previous_v)
                if delta > self._open_wire_threshold_mv and current_v < 500:
                    open_wire_cells.append({
                        "cell_index": i,
                        "previous_voltage_mv": previous_v,
                        "current_voltage_mv": current_v,
                        "delta_mv": delta
                    })

            # Check for implausible voltage vs adjacent cells
            if i > 0 and i < self.cell_count - 1:
                prev_cell_v = self.cell_voltages_mv[i - 1]
                next_cell_v = self.cell_voltages_mv[i + 1]
                avg_adjacent = (prev_cell_v + next_cell_v) / 2.0

                if abs(current_v - avg_adjacent) > self.CELL_DELTA_CRITICAL_MV:
                    if self.MIN_CELL_VOLTAGE_MV <= current_v <= self.MAX_CELL_VOLTAGE_MV:
                        implausible_cells.append({
                            "cell_index": i,
                            "voltage_mv": current_v,
                            "adjacent_average_mv": avg_adjacent,
                            "delta_mv": abs(current_v - avg_adjacent)
                        })

        return {
            "pass": len(open_wire_cells) == 0,
            "open_wire_faults": open_wire_cells,
            "implausible_cells": implausible_cells,
            "total_faults": len(open_wire_cells) + len(implausible_cells),
            "detection_threshold_mv": self._open_wire_threshold_mv
        }

    def get_cell_status(self, cell_index: int) -> CellStatus:
        """Get detailed status for a specific cell."""
        if cell_index < 0 or cell_index >= self.cell_count:
            raise ValueError(f"Invalid cell index: {cell_index}")

        voltage = self.cell_voltages_mv[cell_index]
        temp = self.cell_temperatures_c[
            cell_index % self.temperature_sensor_count]

        fault = CellFaultType.NONE
        is_valid = True

        if voltage < self.MIN_CELL_VOLTAGE_MV:
            fault = CellFaultType.UNDERVOLTAGE
            is_valid = False
        elif voltage > self.MAX_CELL_VOLTAGE_MV:
            fault = CellFaultType.OVERVOLTAGE
            is_valid = False
        elif temp < self.MIN_TEMPERATURE_C:
            fault = CellFaultType.UNDERTEMPERATURE
            is_valid = False
        elif temp > self.MAX_TEMPERATURE_C:
            fault = CellFaultType.OVERTEMPERATURE
            is_valid = False

        return CellStatus(
            index=cell_index,
            voltage_mv=voltage,
            temperature_c=temp,
            fault=fault,
            is_valid=is_valid
        )

    def get_pack_status(self) -> PackStatus:
        """Get overall battery pack status."""
        if not self.cell_voltages_mv or all(v == 0 for v in self.cell_voltages_mv):
            # No valid data
            return PackStatus(
                total_voltage_v=0.0,
                pack_current_a=0.0,
                min_cell_voltage_mv=0.0,
                max_cell_voltage_mv=0.0,
                avg_cell_voltage_mv=0.0,
                cell_voltage_delta_mv=0.0,
                min_temperature_c=0.0,
                max_temperature_c=0.0,
                avg_temperature_c=0.0,
                isolation_resistance_mohm=0.0,
                faults=[CellFaultType.SENSOR_MISMATCH],
                is_safe_to_operate=False
            )

        valid_voltages = [v for v in self.cell_voltages_mv if v > 0]
        valid_temps = [t for t in self.cell_temperatures_c if t > -50]

        min_v = min(valid_voltages) if valid_voltages else 0.0
        max_v = max(valid_voltages) if valid_voltages else 0.0
        avg_v = sum(valid_voltages) / len(valid_voltages) if valid_voltages else 0.0

        min_t = min(valid_temps) if valid_temps else 0.0
        max_t = max(valid_temps) if valid_temps else 0.0
        avg_t = sum(valid_temps) / len(valid_temps) if valid_temps else 0.0

        faults = []
        is_safe = True

        # Check voltage limits
        if min_v < self.MIN_CELL_VOLTAGE_MV:
            faults.append(CellFaultType.UNDERVOLTAGE)
            is_safe = False
        if max_v > self.MAX_CELL_VOLTAGE_MV:
            faults.append(CellFaultType.OVERVOLTAGE)
            is_safe = False

        # Check temperature limits
        if max_t > self.TEMP_CRITICAL_C:
            faults.append(CellFaultType.OVERTEMPERATURE)
            is_safe = False
        if min_t < self.MIN_TEMPERATURE_C:
            faults.append(CellFaultType.UNDERTEMPERATURE)
            is_safe = False

        # Check isolation
        if self.isolation_resistance_mohm < self.FAULT_ISOLATION_MOHM:
            faults.append(CellFaultType.ISOLATION_FAULT)
            is_safe = False

        # Check cell balance
        cell_delta = max_v - min_v
        if cell_delta > self.CELL_DELTA_CRITICAL_MV:
            faults.append(CellFaultType.SENSOR_MISMATCH)
            is_safe = False

        return PackStatus(
            total_voltage_v=sum(valid_voltages) / 1000.0,
            pack_current_a=self.pack_current_a,
            min_cell_voltage_mv=min_v,
            max_cell_voltage_mv=max_v,
            avg_cell_voltage_mv=avg_v,
            cell_voltage_delta_mv=cell_delta,
            min_temperature_c=min_t,
            max_temperature_c=max_t,
            avg_temperature_c=avg_t,
            isolation_resistance_mohm=self.isolation_resistance_mohm,
            faults=faults,
            is_safe_to_operate=is_safe
        )


def main():
    """Example usage of CellMonitor."""
    # Initialize monitor for 96S battery pack
    monitor = CellMonitor(cell_count=96, temperature_sensor_count=12)

    # Simulate cell voltages (nominal 3.7V per cell)
    simulated_voltages = [3700.0 + (i % 5) * 2 for i in range(96)]
    monitor.update_cell_voltages(simulated_voltages)

    # Simulate temperatures
    simulated_temps = [25.0 + (i % 3) for i in range(12)]
    monitor.update_temperatures(simulated_temps)

    # Simulate pack current (charging at 50A)
    monitor.update_pack_current(50.0)

    # Get pack status
    status = monitor.get_pack_status()
    print(f"Pack Voltage: {status.total_voltage_v:.1f} V")
    print(f"Cell Voltage Range: {status.min_cell_voltage_mv:.1f} - "
          f"{status.max_cell_voltage_mv:.1f} mV")
    print(f"Temperature Range: {status.min_temperature_c:.1f} - "
          f"{status.max_temperature_c:.1f} °C")
    print(f"Safe to Operate: {status.is_safe_to_operate}")

    # Check accuracy against reference
    reference_voltages = simulated_voltages.copy()
    accuracy_result = monitor.check_cell_voltage_accuracy(reference_voltages)
    print(f"\nVoltage Accuracy:")
    print(f"  Max Error: {accuracy_result['max_error_mv']:.2f} mV")
    print(f"  Pass: {accuracy_result['pass']}")


if __name__ == "__main__":
    main()
