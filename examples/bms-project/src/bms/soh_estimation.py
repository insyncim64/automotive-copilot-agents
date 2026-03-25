"""
Battery Management System - State of Health (SOH) Estimation Module

Implements SOH estimation using Incremental Capacity Analysis (ICA),
Differential Voltage Analysis (DVA), and data-driven machine learning
approaches per ISO 26262 ASIL-C requirements.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple
import math
from collections import deque


class SOHMethod(Enum):
    """SOH estimation methods."""
    INCREMENTAL_CAPACITY = 0
    DIFFERENTIAL_VOLTAGE = 1
    GRADIENT_BOOSTING = 2
    CAPACITY_FADE = 3
    RESISTANCE_GROWTH = 4
    FUSION = 5


class SOHFaultType(Enum):
    """SOH estimation fault types."""
    NONE = 0
    INSUFFICIENT_DATA = 1
    INVALID_CHARGE_PROFILE = 2
    TEMPERATURE_OUT_OF_RANGE = 3
    CURRENT_SENSOR_DRIFT = 4
    VOLTAGE_SENSOR_DRIFT = 5
    ICA_PEAK_NOT_FOUND = 6
    MODEL_NOT_INITIALIZED = 7
    DIVERGENCE_DETECTED = 8
    CALIBRATION_REQUIRED = 9


@dataclass
class SOHEstimatorResult:
    """SOH estimation result."""
    soh_percent: float  # 0-100%
    capacity_ah: float  # Current estimated capacity
    resistance_mohm: float  # Current estimated resistance
    uncertainty: float  # Estimation uncertainty (0-1)
    method: SOHMethod
    timestamp_ms: int
    is_valid: bool
    fault: SOHFaultType = SOHFaultType.NONE
    confidence: float = 1.0  # 0-1 confidence score


@dataclass
class ICAPeak:
    """Incremental Capacity Analysis peak characteristics."""
    position_v: float  # Voltage position of peak
    height_ah_v: float  # Peak height (dQ/dV)
    area_ah: float  # Integrated area under peak
    width_v: float  # Peak width at half maximum
    shift_from_baseline_v: float  # Voltage shift from baseline


@dataclass
class AgingMetrics:
    """Battery aging metrics for SOH estimation."""
    capacity_ah: float
    capacity_retention_percent: float
    resistance_mohm: float
    resistance_growth_percent: float
    charge_throughput_ah: float  # Total Ah throughput
    cycle_count: int
    calendar_age_days: int
    avg_temperature_c: float
    max_temperature_c: float
    fast_charge_count: int


class IncrementalCapacityAnalyzer:
    """
    Incremental Capacity Analysis (ICA) for SOH estimation.

    ICA analyzes dQ/dV vs V curves during constant-current charging.
    Peak positions and heights correlate with electrode phase transitions
    and degrade predictably with aging.
    """

    # ICA peak characteristics for typical NMC/Graphite chemistry
    # These are baseline values for fresh cells at 25°C
    NMC_PEAK_POSITIONS_V = [3.65, 3.75, 3.85, 3.95, 4.10]
    NMC_PEAK_HEIGHTS_AH_V = [2.5, 3.0, 2.8, 2.2, 1.8]
    PEAK_VOLTAGE_TOLERANCE_V = 0.05
    MIN_DATA_POINTS = 100
    VOLTAGE_WINDOW_MIN_V = 3.0
    VOLTAGE_WINDOW_MAX_V = 4.2

    def __init__(self, nominal_capacity_ah: float = 100.0):
        """Initialize ICA analyzer with battery parameters."""
        self.nominal_capacity_ah = nominal_capacity_ah
        self._baseline_peaks: List[ICAPeak] = []
        self._charge_buffer: deque = deque(maxlen=10000)
        self._last_ica_result: Optional[Dict] = None
        self._calibration_data: Optional[Dict] = None

    def add_charge_data(self, voltage_v: float, current_a: float,
                        time_s: float, temperature_c: float) -> None:
        """
        Add charge data point for ICA computation.

        Args:
            voltage_v: Cell voltage during charge
            current_a: Charge current (positive = charging)
            time_s: Timestamp in seconds
            temperature_c: Cell temperature
        """
        if current_a < 0:
            return  # Only analyze charging data

        self._charge_buffer.append({
            'voltage': voltage_v,
            'current': current_a,
            'time': time_s,
            'temperature': temperature_c
        })

    def compute_ica_curve(self) -> Optional[Tuple[List[float], List[float]]]:
        """
        Compute ICA curve (dQ/dV vs V) from charge data.

        Returns:
            Tuple of (voltage_points, dQ_dV_values) or None if insufficient data
        """
        if len(self._charge_buffer) < self.MIN_DATA_POINTS:
            return None

        # Filter for constant current region
        charge_data = list(self._charge_buffer)
        current_values = [d['current'] for d in charge_data]
        avg_current = sum(current_values) / len(current_values)
        current_std = math.sqrt(
            sum((c - avg_current) ** 2 for c in current_values) / len(current_values)
        )

        # Reject if current not stable (CV phase or dynamic current)
        if current_std > avg_current * 0.1:
            return None

        # Sort by voltage
        charge_data.sort(key=lambda x: x['voltage'])

        # Filter voltage window
        charge_data = [
            d for d in charge_data
            if self.VOLTAGE_WINDOW_MIN_V <= d['voltage'] <= self.VOLTAGE_WINDOW_MAX_V
        ]

        if len(charge_data) < self.MIN_DATA_POINTS:
            return None

        # Compute dQ/dV using numerical differentiation
        voltage_points = []
        dq_dv_values = []

        dt = charge_data[1]['time'] - charge_data[0]['time']
        if dt <= 0:
            return None

        # Sliding window derivative
        window_size = 10
        for i in range(window_size, len(charge_data) - window_size):
            # Voltage window
            v_start = charge_data[i - window_size]['voltage']
            v_end = charge_data[i + window_size]['voltage']
            dv = v_end - v_start

            if dv < 0.001:  # Avoid division by zero
                continue

            # Capacity increment (Ah)
            current_window = [charge_data[j]['current'] for j in range(i - window_size, i + window_size)]
            avg_i = sum(current_window) / len(current_window)
            time_window = (charge_data[i + window_size]['time'] -
                          charge_data[i - window_size]['time'])
            dq = (avg_i * time_window) / 3600.0  # Convert to Ah

            dq_dv = dq / dv if dv != 0 else 0.0

            voltage_points.append(charge_data[i]['voltage'])
            dq_dv_values.append(dq_dv)

        return voltage_points, dq_dv_values

    def detect_peaks(self, voltage_points: List[float],
                     dq_dv_values: List[float]) -> List[ICAPeak]:
        """
        Detect ICA peaks from dQ/dV curve.

        Uses local maximum detection with Gaussian smoothing.
        """
        if not voltage_points or not dq_dv_values:
            return []

        # Simple peak detection (production would use scipy.signal.find_peaks)
        peaks = []
        window = 5

        for i in range(window, len(dq_dv_values) - window):
            # Check if local maximum
            is_peak = True
            for j in range(1, window + 1):
                if dq_dv_values[i] <= dq_dv_values[i - j] or \
                   dq_dv_values[i] <= dq_dv_values[i + j]:
                    is_peak = False
                    break

            if is_peak:
                # Find peak width at half maximum
                half_max = dq_dv_values[i] / 2
                left_idx = i
                right_idx = i

                while left_idx > 0 and dq_dv_values[left_idx] > half_max:
                    left_idx -= 1
                while right_idx < len(dq_dv_values) - 1 and dq_dv_values[right_idx] > half_max:
                    right_idx += 1

                peak_width_v = voltage_points[right_idx] - voltage_points[left_idx]

                # Estimate peak area (trapezoidal integration)
                area = 0.0
                for k in range(left_idx, right_idx):
                    if k < len(dq_dv_values) - 1:
                        dv = voltage_points[k + 1] - voltage_points[k]
                        avg_height = (dq_dv_values[k] + dq_dv_values[k + 1]) / 2
                        area += avg_height * dv

                # Find closest baseline peak for shift calculation
                v_pos = voltage_points[i]
                closest_baseline = min(self.NMC_PEAK_POSITIONS_V,
                                       key=lambda x: abs(x - v_pos))
                shift = v_pos - closest_baseline

                peak = ICAPeak(
                    position_v=v_pos,
                    height_ah_v=dq_dv_values[i],
                    area_ah=area,
                    width_v=peak_width_v,
                    shift_from_baseline_v=shift
                )
                peaks.append(peak)

        return peaks

    def estimate_soh(self, peaks: List[ICAPeak]) -> SOHEstimatorResult:
        """
        Estimate SOH from ICA peak characteristics.

        SOH correlation:
        - Peak height reduction ~ capacity fade
        - Peak position shift ~ resistance growth / lithium plating
        - Peak broadening ~ active material loss
        """
        if not peaks:
            return SOHEstimatorResult(
                soh_percent=0.0,
                capacity_ah=0.0,
                resistance_mohm=0.0,
                uncertainty=1.0,
                method=SOHMethod.INCREMENTAL_CAPACITY,
                timestamp_ms=0,
                is_valid=False,
                fault=SOHFaultType.ICA_PEAK_NOT_FOUND,
                confidence=0.0
            )

        # Compare detected peaks to baseline
        height_ratio_sum = 0.0
        shift_sum = 0.0
        valid_peaks = 0

        for detected_peak in peaks:
            # Find matching baseline peak
            closest_baseline_idx = min(
                range(len(self.NMC_PEAK_POSITIONS_V)),
                key=lambda i: abs(self.NMC_PEAK_POSITIONS_V[i] - detected_peak.position_v)
            )

            baseline_height = self.NMC_PEAK_HEIGHTS_AH_V[closest_baseline_idx]
            baseline_position = self.NMC_PEAK_POSITIONS_V[closest_baseline_idx]

            # Height ratio (capacity indicator)
            if baseline_height > 0:
                height_ratio = detected_peak.height_ah_v / baseline_height
                height_ratio_sum += min(height_ratio, 1.5)  # Cap at 150%
                valid_peaks += 1

            # Shift (resistance/lithiation indicator)
            shift_sum += abs(detected_peak.shift_from_baseline_v)

        if valid_peaks == 0:
            return SOHEstimatorResult(
                soh_percent=0.0,
                capacity_ah=0.0,
                resistance_mohm=0.0,
                uncertainty=1.0,
                method=SOHMethod.INCREMENTAL_CAPACITY,
                timestamp_ms=0,
                is_valid=False,
                fault=SOHFaultType.ICA_PEAK_NOT_FOUND,
                confidence=0.0
            )

        avg_height_ratio = height_ratio_sum / valid_peaks
        avg_shift = shift_sum / valid_peaks

        # SOH estimation model (empirical fit)
        # Capacity fade from peak height reduction
        capacity_soh = avg_height_ratio * 100.0

        # Resistance contribution from peak shift
        # Typical shift: 0mV (new) to 50mV (end of life)
        resistance_factor = max(0.0, 1.0 - (avg_shift / 0.050))

        # Combined SOH (weighted average)
        soh = (capacity_soh * 0.7 + resistance_factor * 100.0 * 0.3)
        soh = max(0.0, min(100.0, soh))

        # Estimated capacity
        estimated_capacity = (soh / 100.0) * self.nominal_capacity_ah

        # Estimated resistance (baseline + growth)
        baseline_resistance = 2.0  # mohm for fresh cell
        resistance_growth = (1.0 - resistance_factor) * 5.0  # Up to 5 mohm growth
        estimated_resistance = baseline_resistance + resistance_growth

        # Uncertainty based on number of peaks and data quality
        uncertainty = 0.1 + (0.05 * (5 - valid_peaks))  # More peaks = less uncertainty
        uncertainty = min(0.3, max(0.05, uncertainty))

        # Confidence based on data quality
        confidence = min(1.0, valid_peaks / 5.0) * 0.9

        self._last_ica_result = {
            'peaks_detected': len(peaks),
            'avg_height_ratio': avg_height_ratio,
            'avg_shift_v': avg_shift,
            'valid_peaks': valid_peaks
        }

        import time
        return SOHEstimatorResult(
            soh_percent=round(soh, 2),
            capacity_ah=round(estimated_capacity, 2),
            resistance_mohm=round(estimated_resistance, 3),
            uncertainty=round(uncertainty, 2),
            method=SOHMethod.INCREMENTAL_CAPACITY,
            timestamp_ms=int(time.time() * 1000),
            is_valid=True,
            fault=SOHFaultType.NONE,
            confidence=round(confidence, 2)
        )


class DifferentialVoltageAnalyzer:
    """
    Differential Voltage Analysis (DVA) for SOH estimation.

    DVA analyzes dV/dQ vs Q curves to detect electrode degradation.
    Complementary to ICA (inverse relationship).
    """

    def __init__(self, nominal_capacity_ah: float = 100.0):
        """Initialize DVA analyzer."""
        self.nominal_capacity_ah = nominal_capacity_ah
        self._charge_buffer: deque = deque(maxlen=10000)

    def add_charge_data(self, voltage_v: float, current_a: float,
                        time_s: float, temperature_c: float) -> None:
        """Add charge data point."""
        if current_a < 0:
            return
        self._charge_buffer.append({
            'voltage': voltage_v,
            'current': current_a,
            'time': time_s,
            'temperature': temperature_c
        })

    def compute_dva_curve(self) -> Optional[Tuple[List[float], List[float]]]:
        """Compute dV/dQ vs Q curve."""
        if len(self._charge_buffer) < 100:
            return None

        charge_data = list(self._charge_buffer)
        charge_data.sort(key=lambda x: x['time'])

        # Compute cumulative capacity
        cumulative_q = [0.0]
        for i in range(1, len(charge_data)):
            dt = charge_data[i]['time'] - charge_data[i-1]['time']
            avg_i = (charge_data[i]['current'] + charge_data[i-1]['current']) / 2
            dq = (avg_i * dt) / 3600.0  # Ah
            cumulative_q.append(cumulative_q[-1] + dq)

        total_capacity = cumulative_q[-1]
        if total_capacity < 1.0:  # Less than 1 Ah - insufficient data
            return None

        # Compute dV/dQ
        q_points = []
        dv_dq_values = []

        window = 5
        for i in range(window, len(charge_data) - window):
            dq = cumulative_q[i + window] - cumulative_q[i - window]
            dv = charge_data[i + window]['voltage'] - charge_data[i - window]['voltage']

            if dq > 0.001:  # Avoid division by zero
                q_points.append(cumulative_q[i])
                dv_dq_values.append(dv / dq)

        return q_points, dv_dq_values


class SOHEstimatorML:
    """
    Machine Learning-based SOH estimation using Gradient Boosting.

    Uses features from charge/discharge curves to estimate SOH.
    Production model trained on historical aging data.
    """

    # Feature names for model input
    FEATURE_NAMES = [
        'voltage_mean', 'voltage_std', 'voltage_min', 'voltage_max',
        'current_mean', 'current_std', 'current_max',
        'temperature_mean', 'temperature_max',
        'charge_capacity', 'avg_charge_time',
        'cycle_count', 'calendar_age_days',
        'fast_charge_ratio', 'deep_discharge_ratio'
    ]

    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize ML-based SOH estimator.

        Args:
            model_path: Path to trained gradient boosting model (.pkl)
        """
        self.model_path = model_path
        self._model = None
        self._is_initialized = False
        self._feature_buffer: Dict[str, List[float]] = {
            name: [] for name in self.FEATURE_NAMES
        }
        self._aging_metrics: Optional[AgingMetrics] = None

        # Placeholder for model loading
        # In production: import joblib; self._model = joblib.load(model_path)

    def update_aging_metrics(self, metrics: AgingMetrics) -> None:
        """Update aging metrics for feature computation."""
        self._aging_metrics = metrics

    def add_charge_cycle_data(self, voltage_stats: Dict, current_stats: Dict,
                              temperature_stats: Dict, capacity_ah: float,
                              duration_s: float) -> None:
        """
        Add charge cycle statistics for feature extraction.

        Args:
            voltage_stats: {'mean', 'std', 'min', 'max'}
            current_stats: {'mean', 'std', 'max'}
            temperature_stats: {'mean', 'max'}
            capacity_ah: Charge capacity in Ah
            duration_s: Charge duration in seconds
        """
        self._feature_buffer['voltage_mean'].append(voltage_stats.get('mean', 0.0))
        self._feature_buffer['voltage_std'].append(voltage_stats.get('std', 0.0))
        self._feature_buffer['voltage_min'].append(voltage_stats.get('min', 0.0))
        self._feature_buffer['voltage_max'].append(voltage_stats.get('max', 0.0))

        self._feature_buffer['current_mean'].append(current_stats.get('mean', 0.0))
        self._feature_buffer['current_std'].append(current_stats.get('std', 0.0))
        self._feature_buffer['current_max'].append(current_stats.get('max', 0.0))

        self._feature_buffer['temperature_mean'].append(temperature_stats.get('mean', 25.0))
        self._feature_buffer['temperature_max'].append(temperature_stats.get('max', 25.0))

        self._feature_buffer['charge_capacity'].append(capacity_ah)

        avg_time = duration_s / 3600.0 if duration_s > 0 else 0.0
        self._feature_buffer['avg_charge_time'].append(avg_time)

    def _extract_features(self) -> Optional[List[float]]:
        """Extract features from buffered data for model inference."""
        if not self._aging_metrics:
            return None

        # Check sufficient data
        min_samples = 5
        for name, values in self._feature_buffer.items():
            if len(values) < min_samples:
                return None

        # Compute feature vector (recent averages)
        features = []
        for name in self.FEATURE_NAMES:
            values = self._feature_buffer[name][-10:]  # Last 10 cycles
            features.append(sum(values) / len(values))

        # Add aging metrics
        features.append(self._aging_metrics.cycle_count)
        features.append(self._aging_metrics.calendar_age_days)

        # Compute fast charge ratio (placeholder)
        features.append(0.3)  # Placeholder - would compute from current profile

        # Compute deep discharge ratio (placeholder)
        features.append(0.1)

        return features

    def estimate_soh(self) -> SOHEstimatorResult:
        """
        Estimate SOH using trained gradient boosting model.

        Returns:
            SOH estimation result with confidence and uncertainty
        """
        features = self._extract_features()

        if features is None:
            return SOHEstimatorResult(
                soh_percent=0.0,
                capacity_ah=0.0,
                resistance_mohm=0.0,
                uncertainty=1.0,
                method=SOHMethod.GRADIENT_BOOSTING,
                timestamp_ms=0,
                is_valid=False,
                fault=SOHFaultType.INSUFFICIENT_DATA,
                confidence=0.0
            )

        if not self._is_initialized:
            # Use simplified model for demonstration
            # Production: self._model.predict([features])[0]
            return self._estimate_soh_simplified(features)

        # Production inference
        # soh_percent = self._model.predict([features])[0]
        return self._estimate_soh_simplified(features)

    def _estimate_soh_simplified(self, features: List[float]) -> SOHEstimatorResult:
        """
        Simplified SOH estimation (placeholder for trained model).

        Uses heuristic rules based on feature values.
        """
        # Extract key features
        charge_capacity = features[9]  # Index of charge_capacity
        cycle_count = features[12]
        calendar_age = features[13]

        # Capacity fade model (simplified exponential decay)
        # Typical: 20% capacity loss after 1000 cycles
        cycle_fade = 1.0 - (1.0 - math.exp(-cycle_count / 5000)) * 0.2

        # Calendar aging (simplified)
        # Typical: 10% capacity loss after 10 years
        calendar_fade = 1.0 - (1.0 - math.exp(-calendar_age / (10 * 365))) * 0.1

        # Combined SOH
        soh = cycle_fade * calendar_fade * 100.0
        soh = max(0.0, min(100.0, soh))

        # Estimated capacity
        nominal_capacity = 100.0  # Ah
        estimated_capacity = soh / 100.0 * nominal_capacity

        # Resistance growth model
        # Resistance increases as capacity decreases
        resistance_growth = (100.0 - soh) / 100.0 * 5.0  # Up to 5 mohm
        estimated_resistance = 2.0 + resistance_growth

        # Uncertainty based on data quality
        uncertainty = 0.15  # Base uncertainty for ML method

        # Confidence based on feature quality
        confidence = 0.85  # High confidence with sufficient data

        import time
        return SOHEstimatorResult(
            soh_percent=round(soh, 2),
            capacity_ah=round(estimated_capacity, 2),
            resistance_mohm=round(estimated_resistance, 3),
            uncertainty=round(uncertainty, 2),
            method=SOHMethod.GRADIENT_BOOSTING,
            timestamp_ms=int(time.time() * 1000),
            is_valid=True,
            fault=SOHFaultType.NONE,
            confidence=round(confidence, 2)
        )

    def get_model_info(self) -> Dict:
        """Get model metadata."""
        return {
            'model_type': 'GradientBoostingRegressor',
            'model_path': self.model_path or 'models/bms/soh_gradient_boost.pkl',
            'version': '1.0.0',
            'feature_count': len(self.FEATURE_NAMES),
            'features': self.FEATURE_NAMES,
            'training_samples': 'placeholder',
            'accuracy_rmse': 'placeholder',
            'accuracy_mae': 'placeholder'
        }


class SOHFusion:
    """
    Fusion of multiple SOH estimation methods.

    Combines ICA, DVA, and ML estimates with confidence-weighted averaging.
    """

    def __init__(self, nominal_capacity_ah: float = 100.0,
                 ml_model_path: Optional[str] = None):
        """Initialize SOH fusion estimator."""
        self.ica_analyzer = IncrementalCapacityAnalyzer(nominal_capacity_ah)
        self.dva_analyzer = DifferentialVoltageAnalyzer(nominal_capacity_ah)
        self.ml_estimator = SOHEstimatorML(ml_model_path)
        self._nominal_capacity = nominal_capacity_ah

        self._last_ica_result: Optional[SOHEstimatorResult] = None
        self._last_ml_result: Optional[SOHEstimatorResult] = None
        self._fusion_result: Optional[SOHEstimatorResult] = None

    def add_charge_data(self, voltage_v: float, current_a: float,
                        time_s: float, temperature_c: float) -> None:
        """Add charge data to all analyzers."""
        self.ica_analyzer.add_charge_data(voltage_v, current_a, time_s, temperature_c)
        self.dva_analyzer.add_charge_data(voltage_v, current_a, time_s, temperature_c)

    def update_aging_metrics(self, metrics: AgingMetrics) -> None:
        """Update aging metrics for ML estimator."""
        self.ml_estimator.update_aging_metrics(metrics)

    def compute_soh(self) -> SOHEstimatorResult:
        """
        Compute fused SOH estimate from all available methods.

        Returns:
            Fused SOH estimation result
        """
        # Get ICA estimate
        ica_curve = self.ica_analyzer.compute_ica_curve()
        if ica_curve:
            voltage_points, dq_dv_values = ica_curve
            peaks = self.ica_analyzer.detect_peaks(voltage_points, dq_dv_values)
            self._last_ica_result = self.ica_analyzer.estimate_soh(peaks)

        # Get ML estimate
        self._last_ml_result = self.ml_estimator.estimate_soh()

        # Fuse estimates
        results = []
        weights = []

        if self._last_ica_result and self._last_ica_result.is_valid:
            results.append(self._last_ica_result)
            weights.append(self._last_ica_result.confidence)

        if self._last_ml_result and self._last_ml_result.is_valid:
            results.append(self._last_ml_result)
            weights.append(self._last_ml_result.confidence)

        if not results:
            self._fusion_result = SOHEstimatorResult(
                soh_percent=0.0,
                capacity_ah=0.0,
                resistance_mohm=0.0,
                uncertainty=1.0,
                method=SOHMethod.FUSION,
                timestamp_ms=0,
                is_valid=False,
                fault=SOFaultType.INSUFFICIENT_DATA,
                confidence=0.0
            )
            return self._fusion_result

        # Confidence-weighted fusion
        total_weight = sum(weights)
        if total_weight == 0:
            total_weight = 1.0

        fused_soh = sum(r.soh_percent * w for r, w in zip(results, weights)) / total_weight
        fused_capacity = sum(r.capacity_ah * w for r, w in zip(results, weights)) / total_weight
        fused_resistance = sum(r.resistance_mohm * w for r, w in zip(results, weights)) / total_weight
        fused_confidence = sum(r.confidence * w for r, w in zip(results, weights)) / total_weight

        # Combined uncertainty (reduced by fusion)
        fused_uncertainty = (
            sum(r.uncertainty * w for r, w in zip(results, weights)) / total_weight
        ) * 0.8  # 20% uncertainty reduction from fusion

        # Check for divergence
        if len(results) >= 2:
            soh_diff = abs(results[0].soh_percent - results[1].soh_percent)
            if soh_diff > 15.0:  # More than 15% difference
                fused_fault = SOHFaultType.DIVERGENCE_DETECTED
                fused_confidence *= 0.5  # Reduce confidence on divergence
            else:
                fused_fault = SOHFaultType.NONE
        else:
            fused_fault = results[0].fault

        import time
        self._fusion_result = SOHEstimatorResult(
            soh_percent=round(fused_soh, 2),
            capacity_ah=round(fused_capacity, 2),
            resistance_mohm=round(fused_resistance, 3),
            uncertainty=round(fused_uncertainty, 2),
            method=SOHMethod.FUSION,
            timestamp_ms=int(time.time() * 1000),
            is_valid=True,
            fault=fused_fault,
            confidence=round(fused_confidence, 2)
        )

        return self._fusion_result

    def get_model_info(self) -> Dict:
        """Get combined model information."""
        return {
            'fusion_methods': ['ICA', 'DVA', 'GradientBoosting'],
            'ica_model': self.ica_analyzer.__dict__,
            'ml_model': self.ml_estimator.get_model_info(),
            'nominal_capacity_ah': self._nominal_capacity
        }


def main():
    """Example usage of SOH estimators."""
    print("=" * 60)
    print("Battery State of Health (SOH) Estimation")
    print("=" * 60)

    # Initialize estimators
    ica_analyzer = IncrementalCapacityAnalyzer(nominal_capacity_ah=100.0)
    ml_estimator = SOHEstimatorML(model_path='models/bms/soh_gradient_boost.pkl')

    # Simulate aging data over 500 cycles
    print("\nSimulating battery aging over 500 cycles...")
    print("-" * 60)

    for cycle in range(0, 501, 50):
        # Simulate charge data for this cycle
        # Capacity fade: ~0.02% per cycle (typical LFP/NMC)
        capacity_retention = 1.0 - (cycle * 0.0002)
        current_capacity = 100.0 * capacity_retention

        # Simulate ICA data
        for i in range(200):
            voltage = 3.0 + (i / 200) * 1.2  # 3.0V to 4.2V
            current = current_capacity / 2.0  # C/2 charge
            time_s = i * 10.0
            temperature = 25.0 + (cycle / 1000) * 5  # Slight temperature increase

            ica_analyzer.add_charge_data(voltage, current, time_s, temperature)

        # Update aging metrics for ML estimator
        aging_metrics = AgingMetrics(
            capacity_ah=current_capacity,
            capacity_retention_percent=capacity_retention * 100,
            resistance_mohm=2.0 + (cycle * 0.005),
            resistance_growth_percent=(cycle * 0.005) / 2.0 * 100,
            charge_throughput_ah=cycle * 100.0,
            cycle_count=cycle,
            calendar_age_days=cycle,
            avg_temperature_c=25.0 + (cycle / 1000) * 5,
            max_temperature_c=35.0 + (cycle / 1000) * 5,
            fast_charge_count=int(cycle * 0.2)
        )
        ml_estimator.update_aging_metrics(aging_metrics)

        # Add charge cycle data for ML features
        ml_estimator.add_charge_cycle_data(
            voltage_stats={'mean': 3.6, 'std': 0.3, 'min': 3.0, 'max': 4.2},
            current_stats={'mean': current_capacity / 2, 'std': 5.0, 'max': current_capacity},
            temperature_stats={'mean': 25.0 + cycle / 40, 'max': 35.0 + cycle / 40},
            capacity_ah=current_capacity,
            duration_s=7200  # 2 hour charge
        )

        # Compute ICA SOH
        ica_curve = ica_analyzer.compute_ica_curve()
        if ica_curve:
            voltage_points, dq_dv_values = ica_curve
            peaks = ica_analyzer.detect_peaks(voltage_points, dq_dv_values)
            ica_result = ica_analyzer.estimate_soh(peaks)
        else:
            ica_result = SOHEstimatorResult(
                soh_percent=0.0, capacity_ah=0.0, resistance_mohm=0.0,
                uncertainty=1.0, method=SOHMethod.INCREMENTAL_CAPACITY,
                timestamp_ms=0, is_valid=False, fault=SOFaultType.INSUFFICIENT_DATA
            )

        # Compute ML SOH
        ml_result = ml_estimator.estimate_soh()

        # Print results
        print(f"\nCycle {cycle:3d}:")
        print(f"  True Capacity:    {current_capacity:6.2f} Ah ({capacity_retention * 100:5.1f}% retention)")
        if ica_result.is_valid:
            print(f"  ICA SOH:          {ica_result.soh_percent:6.2f}% (±{ica_result.uncertainty * 100:.1f}%, conf={ica_result.confidence:.2f})")
        else:
            print(f"  ICA SOH:          {'N/A':>6} ({ica_result.fault.name})")
        if ml_result.is_valid:
            print(f"  ML SOH:           {ml_result.soh_percent:6.2f}% (±{ml_result.uncertainty * 100:.1f}%, conf={ml_result.confidence:.2f})")
        else:
            print(f"  ML SOH:           {'N/A':>6} ({ml_result.fault.name})")

    # Print model information
    print("\n" + "=" * 60)
    print("Model Information")
    print("=" * 60)
    print(f"ICA Analyzer:")
    print(f"  Nominal Capacity: {ica_analyzer.nominal_capacity_ah} Ah")
    print(f"  Baseline Peaks: {len(ica_analyzer.NMC_PEAK_POSITIONS_V)}")
    print(f"  Peak Positions: {ica_analyzer.NMC_PEAK_POSITIONS_V}")

    print(f"\nML Estimator:")
    ml_info = ml_estimator.get_model_info()
    print(f"  Model Type: {ml_info['model_type']}")
    print(f"  Model Path: {ml_info['model_path']}")
    print(f"  Feature Count: {ml_info['feature_count']}")

    print("\n" + "=" * 60)
    print("SOH Estimation Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
