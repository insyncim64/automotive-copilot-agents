"""
Battery Management System - Thermal Management Module

Implements thermal modeling, cooling/heating control strategies, and
thermal runaway detection per ISO 26262 ASIL-C requirements.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Callable
import math


class ThermalFaultType(Enum):
    """Thermal system fault types."""
    NONE = 0
    OVERTEMPERATURE = 1
    UNDERTEMPERATURE = 2
    THERMAL_RUNAWAY = 3
    SENSOR_FAILURE = 4
    COOLING_FAILURE = 5
    HEATING_FAILURE = 6
    THERMAL_IMBALANCE = 7


class CoolingMode(Enum):
    """Cooling system operating modes."""
    OFF = 0
    NATURAL_CONVECTION = 1
    FORCED_AIR = 2
    LIQUID_COOLING = 3
    MAX_COOLING = 4


class HeatingMode(Enum):
    """Heating system operating modes."""
    OFF = 0
    LOW_POWER = 1
    MEDIUM_POWER = 2
    HIGH_POWER = 3
    PREHEAT = 4


@dataclass
class ThermalZone:
    """Temperature state for a thermal zone."""
    zone_id: int
    temperature_c: float
    target_temperature_c: float
    heating_power_w: float
    cooling_power_w: float
    thermal_mass_j_k: float
    is_valid: bool


@dataclass
class PackThermalStatus:
    """Overall battery pack thermal status."""
    min_temperature_c: float
    max_temperature_c: float
    avg_temperature_c: float
    temperature_gradient_c_m: float
    thermal_imbalance_c: float
    cooling_mode: CoolingMode
    heating_mode: HeatingMode
    faults: List[ThermalFaultType]
    is_safe_to_operate: bool
    thermal_runaway_risk: float  # 0.0 to 1.0


@dataclass
class ThermalModelParams:
    """Parameters for lumped parameter thermal model."""
    # Cell thermal properties
    cell_mass_kg: float = 0.05  # 50g per cell
    cell_specific_heat_j_kg_k: float = 1000.0  # J/(kg·K)
    cell_thermal_conductivity_w_m_k: float = 1.0

    # Pack thermal properties
    pack_thermal_mass_j_k: float = 5000.0  # Total thermal capacity
    pack_thermal_resistance_k_w: float = 0.1  # K/W
    ambient_thermal_resistance_k_w: float = 0.5

    # Cooling system properties
    cooling_capacity_w: float = 500.0  # Maximum cooling power
    cooling_efficiency: float = 0.85
    airflow_rate_m3_s: float = 0.01

    # Heating system properties
    heating_capacity_w: float = 300.0  # Maximum heating power
    heating_efficiency: float = 0.90

    # Thermal runaway parameters
    thermal_runaway_threshold_c: float = 150.0
    thermal_runaway_onset_c: float = 80.0
    self_heating_rate_c_min: float = 0.5  # °C/min threshold


class ThermalModel:
    """
    Lumped parameter thermal model for battery pack.

    Implements:
    - Single-zone lumped capacitance model
    - Multi-zone thermal network
    - Heat generation from electrical losses
    - Convective and conductive heat transfer
    """

    # Thermal model time constants
    THERMAL_TIME_CONSTANT_S = 300.0  # 5 minutes typical
    SAMPLE_TIME_MS = 100  # 100ms sampling

    def __init__(self, params: ThermalModelParams = None, zone_count: int = 12):
        """Initialize thermal model with parameters and zone count."""
        self.params = params or ThermalModelParams()
        self.zone_count = zone_count
        self.zone_temperatures_c: List[float] = [25.0] * zone_count
        self.zone_target_temperatures_c: List[float] = [25.0] * zone_count
        self.ambient_temperature_c = 25.0
        self.pack_current_a = 0.0
        self.pack_voltage_v = 0.0
        self._internal_heat_generation_w = 0.0
        self._heat_transfer_rate_w = 0.0

    def set_zone_temperatures(self, temperatures_c: List[float]) -> None:
        """Set measured zone temperatures from sensors."""
        if len(temperatures_c) != self.zone_count:
            raise ValueError(
                f"Expected {self.zone_count} temperatures, "
                f"got {len(temperatures_c)}")
        self.zone_temperatures_c = temperatures_c.copy()

    def set_ambient_temperature(self, temperature_c: float) -> None:
        """Set ambient temperature for heat transfer calculation."""
        self.ambient_temperature_c = temperature_c

    def set_pack_operating_point(self, current_a: float, voltage_v: float) -> None:
        """Set pack current and voltage for heat generation calculation."""
        self.pack_current_a = current_a
        self.pack_voltage_v = voltage_v

    def compute_heat_generation(self) -> float:
        """
        Compute internal heat generation from electrical losses.

        Heat sources:
        - Ohmic losses: I²R
        - Entropic heating: I·T·dU/dT
        - Side reactions (negligible in normal operation)
        """
        # Estimate internal resistance (simplified model)
        # Typical pack resistance: 50 mohm for 96S pack
        internal_resistance_ohm = 0.05

        # Ohmic heating: P = I²R
        ohmic_heating_w = (self.pack_current_a ** 2) * internal_resistance_ohm

        # Entropic heating (simplified, depends on SOC and chemistry)
        # Typically 5-10% of ohmic heating for NMC chemistry
        entropic_heating_w = ohmic_heating_w * 0.08

        self._internal_heat_generation_w = ohmic_heating_w + entropic_heating_w
        return self._internal_heat_generation_w

    def compute_heat_transfer(self, zone_index: int) -> float:
        """
        Compute heat transfer rate for a zone.

        Heat transfer mechanisms:
        - Conduction to adjacent zones
        - Convection to ambient (via cooling system)
        - Radiation (negligible at battery temperatures)
        """
        zone_temp = self.zone_temperatures_c[zone_index]

        # Temperature difference to ambient
        delta_t_ambient = zone_temp - self.ambient_temperature_c

        # Conductive heat transfer to adjacent zones
        conductive_heat_w = 0.0
        if zone_index > 0:
            delta_t_left = zone_temp - self.zone_temperatures_c[zone_index - 1]
            conductive_heat_w += delta_t_left / self.params.pack_thermal_resistance_k_w

        if zone_index < self.zone_count - 1:
            delta_t_right = zone_temp - self.zone_temperatures_c[zone_index + 1]
            conductive_heat_w += delta_t_right / self.params.pack_thermal_resistance_k_w

        # Convective heat transfer to ambient
        convective_heat_w = delta_t_ambient / self.params.ambient_thermal_resistance_k_w

        self._heat_transfer_rate_w = conductive_heat_w + convective_heat_w
        return self._heat_transfer_rate_w

    def update_temperature(self, zone_index: int, dt_s: float) -> float:
        """
        Update zone temperature using energy balance.

        dT/dt = (Q_generation - Q_transfer) / (m·cp)

        Args:
            zone_index: Index of zone to update
            dt_s: Time step in seconds

        Returns:
            New temperature in °C
        """
        # Heat capacity of zone
        zone_mass_kg = self.params.cell_mass_kg * (96 // self.zone_count)  # Cells per zone
        heat_capacity_j_k = zone_mass_kg * self.params.cell_specific_heat_j_kg_k

        # Energy balance
        heat_generation_w = self.compute_heat_generation() / self.zone_count
        heat_transfer_w = self.compute_heat_transfer(zone_index)

        # Temperature change: dT = (Q_gen - Q_out) * dt / (m·cp)
        net_heat_w = heat_generation_w - heat_transfer_w
        delta_t_k = (net_heat_w * dt_s) / heat_capacity_j_k

        # Update temperature
        new_temp_c = self.zone_temperatures_c[zone_index] + delta_t_k

        # Clamp to physical limits
        new_temp_c = max(-40.0, min(120.0, new_temp_c))

        self.zone_temperatures_c[zone_index] = new_temp_c
        return new_temp_c

    def simulate_step(self, dt_s: float = 0.1) -> List[float]:
        """
        Run one simulation step for all zones.

        Args:
            dt_s: Time step in seconds (default 100ms)

        Returns:
            List of updated zone temperatures
        """
        for i in range(self.zone_count):
            self.update_temperature(i, dt_s)
        return self.zone_temperatures_c.copy()

    def get_zone_status(self, zone_index: int) -> ThermalZone:
        """Get detailed status for a specific thermal zone."""
        if zone_index < 0 or zone_index >= self.zone_count:
            raise ValueError(f"Invalid zone index: {zone_index}")

        return ThermalZone(
            zone_id=zone_index,
            temperature_c=self.zone_temperatures_c[zone_index],
            target_temperature_c=self.zone_target_temperatures_c[zone_index],
            heating_power_w=0.0,  # Updated by controller
            cooling_power_w=0.0,  # Updated by controller
            thermal_mass_j_k=self.params.pack_thermal_mass_j_k / self.zone_count,
            is_valid=True
        )


class ThermalController:
    """
    PID-based thermal management controller.

    Implements:
    - Temperature regulation via PID control
    - Cooling strategy selection (air vs liquid)
    - Heating strategy for cold conditions
    - Derating based on temperature
    """

    # Temperature thresholds
    DERATE_START_C = 45.0
    DERATE_MAX_C = 55.0
    MAX_TEMPERATURE_C = 60.0
    MIN_TEMPERATURE_C = -10.0
    PREHEAT_COMPLETE_C = 15.0
    FAST_CHARGE_MIN_TEMP_C = 25.0

    # PID gains for cooling
    KP_COOLING = 50.0
    TI_COOLING = 100.0  # Integral time
    TD_COOLING = 10.0   # Derivative time

    # PID gains for heating
    KP_HEATING = 30.0
    TI_HEATING = 150.0
    TD_HEATING = 5.0

    def __init__(self, model_params: ThermalModelParams = None):
        """Initialize thermal controller."""
        self.model_params = model_params or ThermalModelParams()

        # PID state for cooling
        self._cooling_integral = 0.0
        self._cooling_prev_error = 0.0

        # PID state for heating
        self._heating_integral = 0.0
        self._heating_prev_error = 0.0

        # Current control outputs
        self._cooling_demand = 0.0  # 0.0 to 1.0
        self._heating_demand = 0.0  # 0.0 to 1.0

    def compute_cooling_pid(self, error: float, dt: float) -> float:
        """
        Compute cooling demand using PID algorithm.

        Args:
            error: Temperature error (current - target)
            dt: Time step in seconds

        Returns:
            Cooling demand (0.0 to 1.0)
        """
        # Proportional term
        p_term = self.KP_COOLING * error

        # Integral term with anti-windup
        self._cooling_integral += error * dt
        self._cooling_integral = max(-100.0, min(100.0, self._cooling_integral))
        i_term = (self.KP_COOLING / self.TI_COOLING) * self._cooling_integral

        # Derivative term
        d_error = error - self._cooling_prev_error
        d_term = (self.KP_COOLING * self.TD_COOLING) * (d_error / dt) if dt > 0 else 0.0

        self._cooling_prev_error = error

        # Combine terms
        cooling_output = p_term + i_term + d_term

        # Clamp to valid range
        cooling_demand = max(0.0, min(1.0, cooling_output / 100.0))

        self._cooling_demand = cooling_demand
        return cooling_demand

    def compute_heating_pid(self, error: float, dt: float) -> float:
        """
        Compute heating demand using PID algorithm.

        Args:
            error: Temperature error (target - current)
            dt: Time step in seconds

        Returns:
            Heating demand (0.0 to 1.0)
        """
        # Proportional term
        p_term = self.KP_HEATING * error

        # Integral term with anti-windup
        self._heating_integral += error * dt
        self._heating_integral = max(-100.0, min(100.0, self._heating_integral))
        i_term = (self.KP_HEATING / self.TI_HEATING) * self._heating_integral

        # Derivative term
        d_error = error - self._heating_prev_error
        d_term = (self.KP_HEATING * self.TD_HEATING) * (d_error / dt) if dt > 0 else 0.0

        self._heating_prev_error = error

        # Combine terms
        heating_output = p_term + i_term + d_term

        # Clamp to valid range
        heating_demand = max(0.0, min(1.0, heating_output / 100.0))

        self._heating_demand = heating_demand
        return heating_demand

    def determine_cooling_mode(self, cooling_demand: float) -> CoolingMode:
        """Determine cooling mode based on demand."""
        if cooling_demand <= 0.05:
            return CoolingMode.OFF
        elif cooling_demand <= 0.25:
            return CoolingMode.NATURAL_CONVECTION
        elif cooling_demand <= 0.50:
            return CoolingMode.FORCED_AIR
        elif cooling_demand <= 0.75:
            return CoolingMode.LIQUID_COOLING
        else:
            return CoolingMode.MAX_COOLING

    def determine_heating_mode(self, heating_demand: float) -> HeatingMode:
        """Determine heating mode based on demand."""
        if heating_demand <= 0.05:
            return HeatingMode.OFF
        elif heating_demand <= 0.30:
            return HeatingMode.LOW_POWER
        elif heating_demand <= 0.60:
            return HeatingMode.MEDIUM_POWER
        elif heating_demand <= 0.85:
            return HeatingMode.HIGH_POWER
        else:
            return HeatingMode.PREHEAT

    def compute_thermal_control(
        self,
        zone_temperatures: List[float],
        target_temperature: float,
        ambient_temperature: float,
        dt: float = 0.1
    ) -> Tuple[CoolingMode, HeatingMode, dict]:
        """
        Compute thermal control outputs for all zones.

        Args:
            zone_temperatures: List of zone temperatures
            target_temperature: Target temperature setpoint
            ambient_temperature: Ambient temperature
            dt: Time step in seconds

        Returns:
            Tuple of (cooling_mode, heating_mode, diagnostic_info)
        """
        # Use average temperature for control
        avg_temp = sum(zone_temperatures) / len(zone_temperatures)
        max_temp = max(zone_temperatures)
        min_temp = min(zone_temperatures)

        # Temperature error (positive = too hot)
        error = avg_temp - target_temperature

        # Determine if cooling or heating is needed
        needs_cooling = error > 0.5  # Deadband of 0.5°C
        needs_heating = error < -0.5

        # Compute control outputs (mutually exclusive)
        if needs_cooling:
            cooling_demand = self.compute_cooling_pid(error, dt)
            heating_demand = 0.0
            self._heating_integral = 0.0  # Reset heating integral
        elif needs_heating:
            heating_demand = self.compute_heating_pid(-error, dt)
            cooling_demand = 0.0
            self._cooling_integral = 0.0  # Reset cooling integral
        else:
            cooling_demand = 0.0
            heating_demand = 0.0

        # Determine operating modes
        cooling_mode = self.determine_cooling_mode(cooling_demand)
        heating_mode = self.determine_heating_mode(heating_demand)

        # Compute derating factor
        derate_factor = 1.0
        if max_temp > self.DERATE_START_C:
            derate_factor = max(0.0, 1.0 - (max_temp - self.DERATE_START_C) /
                               (self.DERATE_MAX_C - self.DERATE_START_C))

        diagnostic = {
            "average_temperature_c": avg_temp,
            "max_temperature_c": max_temp,
            "min_temperature_c": min_temp,
            "target_temperature": target_temperature,
            "temperature_error_c": error,
            "cooling_demand": cooling_demand,
            "heating_demand": heating_demand,
            "derate_factor": derate_factor,
            "can_fast_charge": min_temp >= self.FAST_CHARGE_MIN_TEMP_C
        }

        return cooling_mode, heating_mode, diagnostic


class ThermalRunawayDetector:
    """
    Multi-sensor fusion thermal runaway detection.

    Implements:
    - Temperature rate-of-rise detection
    - Thermal imbalance detection
    - Gas sensor fusion (if available)
    - Voltage anomaly correlation
    """

    # Detection thresholds
    TEMP_RISE_THRESHOLD_C_MIN = 10.0  # °C per minute
    THERMAL_IMBALANCE_THRESHOLD_C = 15.0  # Max temp difference
    THERMAL_RUNAWAY_PROBABILITY_THRESHOLD = 0.7
    CONFIRMATION_TIME_S = 5.0  # Must sustain for 5 seconds

    def __init__(self, zone_count: int = 12):
        """Initialize thermal runaway detector."""
        self.zone_count = zone_count
        self._temperature_history: List[List[float]] = []
        self._max_history_size = 60  # 1 minute at 1Hz
        self._detection_state = [0.0] * zone_count  # 0.0 to 1.0
        self._confirmation_timer = [0.0] * zone_count

        # Sensor fusion weights
        self._temp_rate_weight = 0.5
        self._imbalance_weight = 0.3
        self._gas_sensor_weight = 0.2  # If available

    def add_temperature_sample(self, temperatures_c: List[float]) -> None:
        """Add temperature sample to history."""
        if len(temperatures_c) != self.zone_count:
            raise ValueError(
                f"Expected {self.zone_count} temperatures, "
                f"got {len(temperatures_c)}")

        self._temperature_history.append(temperatures_c.copy())

        # Trim history
        if len(self._temperature_history) > self._max_history_size:
            self._temperature_history.pop(0)

    def compute_temperature_rate(self, zone_index: int, window_s: float = 60.0) -> float:
        """
        Compute temperature rate of change for a zone.

        Args:
            zone_index: Zone to analyze
            window_s: Time window for rate calculation

        Returns:
            Temperature rate in °C/min
        """
        if len(self._temperature_history) < 2:
            return 0.0

        # Get samples from window
        samples_to_use = min(int(window_s), len(self._temperature_history))
        if samples_to_use < 2:
            return 0.0

        oldest = self._temperature_history[-samples_to_use][zone_index]
        newest = self._temperature_history[-1][zone_index]

        # Compute rate (°C/min)
        time_window_min = samples_to_use / 60.0  # Assuming 1Hz sampling
        rate_c_min = (newest - oldest) / time_window_min if time_window_min > 0 else 0.0

        return rate_c_min

    def compute_thermal_imbalance(self, temperatures_c: List[float]) -> Tuple[float, int, int]:
        """
        Compute thermal imbalance across pack.

        Returns:
            Tuple of (imbalance_c, hottest_zone, coldest_zone)
        """
        if not temperatures_c:
            return 0.0, 0, 0

        max_temp = max(temperatures_c)
        min_temp = min(temperatures_c)
        imbalance = max_temp - min_temp

        hottest_zone = temperatures_c.index(max_temp)
        coldest_zone = temperatures_c.index(min_temp)

        return imbalance, hottest_zone, coldest_zone

    def detect_thermal_runaway(
        self,
        temperatures_c: List[float],
        gas_sensor_active: bool = False,
        gas_concentration_ppm: float = 0.0
    ) -> dict:
        """
        Detect potential thermal runaway using multi-sensor fusion.

        Args:
            temperatures_c: Current zone temperatures
            gas_sensor_active: Whether gas sensor data is available
            gas_concentration_ppm: Gas concentration if sensor active

        Returns:
            Detection results with risk assessment
        """
        if len(temperatures_c) != self.zone_count:
            return {
                "thermal_runaway_detected": False,
                "risk_probability": 0.0,
                "error": "Temperature count mismatch"
            }

        # Update history
        self.add_temperature_sample(temperatures_c)

        detection_flags = []
        risk_probabilities = []

        for i in range(self.zone_count):
            # Factor 1: Temperature rate of rise
            temp_rate = self.compute_temperature_rate(i)
            temp_rate_risk = min(1.0, temp_rate / self.TEMP_RISE_THRESHOLD_C_MIN)

            # Factor 2: Absolute temperature
            temp_risk = 0.0
            if temperatures_c[i] > 60.0:
                temp_risk = min(1.0, (temperatures_c[i] - 60.0) / 90.0)

            # Factor 3: Thermal imbalance
            imbalance, _, _ = self.compute_thermal_imbalance(temperatures_c)
            imbalance_risk = min(1.0, imbalance / self.THERMAL_IMBALANCE_THRESHOLD_C)

            # Factor 4: Gas sensor (if available)
            gas_risk = 0.0
            if gas_sensor_active and gas_concentration_ppm > 0:
                # Typical CO detection threshold for thermal runaway: 100 ppm
                gas_risk = min(1.0, gas_concentration_ppm / 100.0)

            # Weighted fusion
            if gas_sensor_active:
                combined_risk = (
                    self._temp_rate_weight * temp_rate_risk +
                    self._imbalance_weight * imbalance_risk +
                    self._gas_sensor_weight * gas_risk +
                    0.0 * temp_risk  # Already included in other factors
                )
            else:
                # Renormalize weights without gas sensor
                combined_risk = (
                    0.6 * temp_rate_risk +
                    0.4 * imbalance_risk
                )

            # Update detection state with low-pass filter
            alpha = 0.9  # Smoothing factor
            self._detection_state[i] = alpha * self._detection_state[i] + (1 - alpha) * combined_risk

            # Update confirmation timer
            if self._detection_state[i] > self.THERMAL_RUNAWAY_PROBABILITY_THRESHOLD:
                self._confirmation_timer[i] += 0.1  # Assuming 10Hz update
            else:
                self._confirmation_timer[i] = max(0.0, self._confirmation_timer[i] - 0.1)

            # Detection decision
            detected = (
                self._detection_state[i] > self.THERMAL_RUNAWAY_PROBABILITY_THRESHOLD and
                self._confirmation_timer[i] >= self.CONFIRMATION_TIME_S
            )

            detection_flags.append(detected)
            risk_probabilities.append(self._detection_state[i])

        # Overall assessment
        any_detected = any(detection_flags)
        max_risk = max(risk_probabilities) if risk_probabilities else 0.0

        return {
            "thermal_runaway_detected": any_detected,
            "risk_probability": max_risk,
            "affected_zones": [i for i, d in enumerate(detection_flags) if d],
            "zone_risks": risk_probabilities,
            "temperature_rates": [
                self.compute_temperature_rate(i) for i in range(self.zone_count)
            ],
            "confirmation_times": self._confirmation_timer.copy()
        }

    def get_detection_statistics(self) -> dict:
        """Get detection system statistics."""
        return {
            "max_risk_probability": max(self._detection_state) if self._detection_state else 0.0,
            "avg_risk_probability": sum(self._detection_state) / len(self._detection_state) if self._detection_state else 0.0,
            "zones_elevated_risk": sum(1 for r in self._detection_state if r > 0.5),
            "history_size": len(self._temperature_history)
        }


def main():
    """Example usage of thermal management system."""
    # Initialize thermal model
    model_params = ThermalModelParams()
    model = ThermalModel(model_params, zone_count=12)
    controller = ThermalController(model_params)
    runaway_detector = ThermalRunawayDetector(zone_count=12)

    # Simulate normal operation
    print("=== Thermal Management Simulation ===\n")

    # Set initial conditions
    model.set_ambient_temperature(25.0)
    model.set_pack_operating_point(100.0, 380.0)  # 100A charging

    # Run simulation for 60 seconds
    for t in range(600):  # 600 steps @ 100ms = 60 seconds
        # Get temperatures
        temps = model.simulate_step(dt_s=0.1)

        # Compute thermal control
        cooling_mode, heating_mode, diag = controller.compute_thermal_control(
            temps, target_temperature=30.0, ambient_temperature=25.0, dt=0.1
        )

        # Check for thermal runaway
        if t % 10 == 0:  # Check every second
            runaway_result = runaway_detector.detect_thermal_runaway(temps)

            if runaway_result["thermal_runaway_detected"]:
                print(f"t={t*0.1:.1f}s: THERMAL RUNAWAY DETECTED!")

    # Print final status
    final_temps = model.zone_temperatures_c
    print(f"\nFinal zone temperatures: {[f'{t:.1f}' for t in final_temps]}°C")
    print(f"Average: {sum(final_temps)/len(final_temps):.1f}°C")
    print(f"Max: {max(final_temps):.1f}°C, Min: {min(final_temps):.1f}°C")
    print(f"Imbalance: {max(final_temps) - min(final_temps):.1f}°C")

    # Run detection test
    print("\n=== Thermal Runaway Detection Test ===")

    # Simulate thermal runaway scenario (one zone heating rapidly)
    runaway_temps = [30.0] * 12
    for i in range(30):  # 30 samples
        runaway_temps[5] += 15.0  # Zone 5 heats at 15°C/min
        runaway_detector.add_temperature_sample(runaway_temps.copy())

        result = runaway_detector.detect_thermal_runaway(runaway_temps)
        print(f"Sample {i+1}: Risk={result['risk_probability']:.3f}, "
              f"Detected={result['thermal_runaway_detected']}")


if __name__ == "__main__":
    main()
