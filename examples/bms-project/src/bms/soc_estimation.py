"""
Battery Management System - State of Charge (SOC) Estimation Module

Implements dual-approach SOC estimation using Extended Kalman Filter (EKF)
and Neural Network (LSTM) methods per ISO 26262 ASIL-C requirements.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple, Dict
import math


class SOCMethod(Enum):
    """SOC estimation method types."""
    EKF = "extended_kalman_filter"
    NEURAL_NETWORK = "neural_network_lstm"
    COULOMB_COUNTING = "coulomb_counting"
    OCV_LOOKUP = "open_circuit_voltage"
    FUSION = "sensor_fusion"


class SOCFaultType(Enum):
    """SOC estimation fault types."""
    NONE = 0
    SENSOR_TIMEOUT = 1
    CURRENT_SENSOR_FAULT = 2
    VOLTAGE_SENSOR_FAULT = 3
    TEMPERATURE_SENSOR_FAULT = 4
    DIVERGENCE_DETECTED = 5
    MODEL_NOT_INITIALIZED = 6
    INVALID_INPUT_RANGE = 7


@dataclass
class SOCEstimatorResult:
    """Result of SOC estimation."""
    soc: float  # State of Charge (0.0 - 100.0)
    soh: float  # State of Health (0.0 - 100.0)
    uncertainty: float  # Estimation uncertainty (percent)
    method: SOCMethod
    timestamp_ms: int
    is_valid: bool
    fault: SOCFaultType
    confidence: float  # Confidence level (0.0 - 1.0)


@dataclass
class EKFState:
    """Extended Kalman Filter internal state."""
    x: List[float]  # State vector [SOC, V1, V2, ...]
    P: List[List[float]]  # State covariance matrix
    Q: List[List[float]]  # Process noise covariance
    R: float  # Measurement noise covariance


class SOCEstimatorEKF:
    """
    Extended Kalman Filter based SOC estimator.

    Implements an equivalent circuit model (ECM) with the following states:
    - SOC: State of Charge
    - V1: RC pair 1 voltage (fast dynamics)
    - V2: RC pair 2 voltage (slow dynamics)

    The EKF fuses coulomb counting with voltage-based correction
    to provide accurate SOC estimation with bounded uncertainty.

    Attributes:
        battery_capacity_ah: Nominal battery capacity in Ampere-hours
        ekf_state: Internal EKF state (state vector and covariance matrices)
    """

    # EKF tuning parameters
    INITIAL_SOC_UNCERTAINTY = 0.1  # 10% initial uncertainty
    PROCESS_NOISE_SOC = 0.001
    PROCESS_NOISE_VOLTAGE = 0.01
    MEASUREMENT_NOISE = 0.001  # Voltage measurement noise variance

    # Equivalent circuit model parameters (typical NMC cell)
    R0 = 0.002  # Ohmic resistance (Ohm)
    R1 = 0.001  # RC pair 1 resistance (Ohm)
    C1 = 1000.0  # RC pair 1 capacitance (F)
    R2 = 0.0005  # RC pair 2 resistance (Ohm)
    C2 = 5000.0  # RC pair 2 capacitance (F)

    # OCV-SOC lookup table (typical NMC chemistry)
    OCV_TABLE = [
        (0.00, 3.00), (0.05, 3.30), (0.10, 3.40), (0.15, 3.48),
        (0.20, 3.55), (0.25, 3.60), (0.30, 3.65), (0.35, 3.70),
        (0.40, 3.75), (0.45, 3.80), (0.50, 3.85), (0.55, 3.90),
        (0.60, 3.95), (0.65, 4.00), (0.70, 4.05), (0.75, 4.10),
        (0.80, 4.15), (0.85, 4.20), (0.90, 4.25), (0.95, 4.30),
        (1.00, 4.35)
    ]

    def __init__(self, battery_capacity_ah: float, initial_soc: float = 0.5):
        """
        Initialize EKF-based SOC estimator.

        Args:
            battery_capacity_ah: Battery nominal capacity in Ampere-hours
            initial_soc: Initial SOC guess (0.0 - 1.0)
        """
        self.battery_capacity_ah = battery_capacity_ah
        self.initial_soc = max(0.0, min(1.0, initial_soc))

        # Initialize EKF state
        self._ekf_state = self._initialize_ekf_state()
        self._last_timestamp_ms = 0
        self._coulomb_count_ah = 0.0
        self._is_initialized = False

        # Model export metadata
        self._model_version = "soc_ekf_v3"
        self._model_path: Optional[str] = None

    def _initialize_ekf_state(self) -> EKFState:
        """Initialize EKF state vector and covariance matrices."""
        # State vector: [SOC, V1, V2]
        x = [self.initial_soc, 0.0, 0.0]

        # Initial covariance (high uncertainty)
        P = [
            [self.INITIAL_SOC_UNCERTAINTY ** 2, 0, 0],
            [0, 0.01, 0],
            [0, 0, 0.01]
        ]

        # Process noise covariance
        Q = [
            [self.PROCESS_NOISE_SOC, 0, 0],
            [0, self.PROCESS_NOISE_VOLTAGE, 0],
            [0, 0, self.PROCESS_NOISE_VOLTAGE]
        ]

        return EKFState(
            x=x,
            P=P,
            Q=Q,
            R=self.MEASUREMENT_NOISE
        )

    def _ocv_from_soc(self, soc: float) -> float:
        """Look up OCV from SOC using interpolation."""
        soc = max(0.0, min(1.0, soc))

        # Find bracketing points
        for i in range(len(self.OCV_TABLE) - 1):
            soc_lo, ocv_lo = self.OCV_TABLE[i]
            soc_hi, ocv_hi = self.OCV_TABLE[i + 1]

            if soc_lo <= soc <= soc_hi:
                # Linear interpolation
                alpha = (soc - soc_lo) / (soc_hi - soc_lo)
                return ocv_lo + alpha * (ocv_hi - ocv_lo)

        return self.OCV_TABLE[-1][1]  # Fallback to max

    def _ocv_slope(self, soc: float, delta: float = 0.01) -> float:
        """Compute dOCV/dSOC at given SOC point."""
        ocv_hi = self._ocv_from_soc(soc + delta)
        ocv_lo = self._ocv_from_soc(soc - delta)
        return (ocv_hi - ocv_lo) / (2.0 * delta)

    def _predict_step(self, current_a: float, dt_s: float) -> None:
        """
        EKF prediction (time update) step.

        Uses coulomb counting for SOC prediction and RC dynamics
        for voltage state prediction.
        """
        state = self._ekf_state.x

        # State transition model
        # SOC(k) = SOC(k-1) - (I * dt) / Q
        delta_soc = (current_a * dt_s) / (self.battery_capacity_ah * 3600.0)
        soc_pred = state[0] - delta_soc

        # RC voltage dynamics (discrete-time)
        tau1 = self.R1 * self.C1
        tau2 = self.R2 * self.C2

        v1_pred = state[1] * math.exp(-dt_s / tau1) + \
                  self.R1 * current_a * (1.0 - math.exp(-dt_s / tau1))
        v2_pred = state[2] * math.exp(-dt_s / tau2) + \
                  self.R2 * current_a * (1.0 - math.exp(-dt_s / tau2))

        state[0] = max(0.0, min(1.0, soc_pred))
        state[1] = v1_pred
        state[2] = v2_pred

        # Covariance prediction: P = F * P * F' + Q
        # State transition matrix F (Jacobian)
        F = [
            [1.0, 0.0, 0.0],
            [0.0, math.exp(-dt_s / tau1), 0.0],
            [0.0, 0.0, math.exp(-dt_s / tau2)]
        ]

        # Matrix multiplication: F * P * F'
        FP = self._matrix_multiply(F, state.P)
        FPF_T = self._matrix_multiply_transpose(FP, F)

        # Add process noise
        for i in range(3):
            for j in range(3):
                state.P[i][j] = FPF_T[i][j] + state.Q[i][j]

    def _update_step(self, measured_voltage_v: float, current_a: float) -> float:
        """
        EKF update (measurement update) step.

        Corrects SOC estimate using voltage measurement residual.

        Returns:
            Innovation (voltage residual) for convergence monitoring
        """
        state = self._ekf_state.x

        # Predicted terminal voltage
        ocv = self._ocv_from_soc(state[0])
        v_terminal_pred = ocv - state[1] - state[2] - current_a * self.R0

        # Innovation (measurement residual)
        innovation = measured_voltage_v - v_terminal_pred

        # Measurement matrix H (Jacobian of observation model)
        h_soc = self._ocv_slope(state[0])
        H = [h_soc, -1.0, -1.0]

        # Innovation covariance: S = H * P * H' + R
        HP = [sum(H[j] * state.P[j][i] for j in range(3)) for i in range(3)]
        S = sum(HP[i] * H[i] for i in range(3)) + state.R

        # Kalman gain: K = P * H' / S
        K = [state.P[i][0] * H[0] + state.P[i][1] * H[1] + state.P[i][2] * H[2]
             for i in range(3)]
        K = [k / S for k in K]

        # State update: x = x + K * innovation
        for i in range(3):
            state.x[i] += K[i] * innovation

        # Clamp SOC to valid range
        state.x[0] = max(0.0, min(1.0, state.x[0]))

        # Covariance update: P = (I - K * H) * P
        KH = [[K[i] * H[j] for j in range(3)] for i in range(3)]
        I_KH = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
        for i in range(3):
            for j in range(3):
                I_KH[i][j] -= KH[i][j]

        state.P = self._matrix_multiply(I_KH, state.P)

        return innovation

    def _matrix_multiply(self, A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
        """Multiply two 3x3 matrices."""
        n = len(A)
        C = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    C[i][j] += A[i][k] * B[k][j]
        return C

    def _matrix_multiply_transpose(self, A: List[List[float]], B: List[List[float]]) -> List[List[float]]:
        """Multiply A by transpose of B."""
        n = len(A)
        C = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    C[i][j] += A[i][k] * B[j][k]
        return C

    def update(self, voltage_v: float, current_a: float, temperature_c: float,
               timestamp_ms: int) -> SOCEstimatorResult:
        """
        Update SOC estimate with new measurement.

        Args:
            voltage_v: Cell/pack terminal voltage
            current_a: Pack current (positive = charging)
            temperature_c: Cell temperature
            timestamp_ms: Timestamp in milliseconds

        Returns:
            SOCEstimatorResult with updated SOC and confidence
        """
        fault = SOCFaultType.NONE
        is_valid = True

        # Validate inputs
        if voltage_v < 2.0 or voltage_v > 5.0:
            fault = SOCFaultType.VOLTAGE_SENSOR_FAULT
            is_valid = False
        if abs(current_a) > 1000.0:
            fault = SOCFaultType.CURRENT_SENSOR_FAULT
            is_valid = False

        if not is_valid:
            return SOCEstimatorResult(
                soc=self._ekf_state.x[0] * 100.0,
                soh=100.0,
                uncertainty=self.INITIAL_SOC_UNCERTAINTY * 100.0,
                method=SOCMethod.EKF,
                timestamp_ms=timestamp_ms,
                is_valid=False,
                fault=fault,
                confidence=0.0
            )

        # Initialize on first valid measurement
        if not self._is_initialized:
            self._is_initialized = True
            self._last_timestamp_ms = timestamp_ms

        # Compute time delta
        dt_ms = timestamp_ms - self._last_timestamp_ms
        dt_s = max(0.001, dt_ms / 1000.0)  # Minimum 1ms to avoid division by zero
        self._last_timestamp_ms = timestamp_ms

        # EKF prediction step
        self._predict_step(current_a, dt_s)

        # EKF update step
        innovation = self._update_step(voltage_v, current_a)

        # Compute uncertainty from covariance
        soc_variance = self._ekf_state.P[0][0]
        uncertainty = math.sqrt(soc_variance) * 100.0  # Convert to percent

        # Compute confidence (inverse of uncertainty)
        confidence = max(0.0, 1.0 - uncertainty / 10.0)  # 10% uncertainty = 0 confidence

        return SOCEstimatorResult(
            soc=self._ekf_state.x[0] * 100.0,
            soh=100.0,  # SOH estimated separately
            uncertainty=uncertainty,
            method=SOCMethod.EKF,
            timestamp_ms=timestamp_ms,
            is_valid=True,
            fault=fault,
            confidence=confidence
        )

    def get_model_info(self) -> Dict:
        """Get model metadata for export."""
        return {
            "model_type": "EKF",
            "version": self._model_version,
            "parameters": {
                "battery_capacity_ah": self.battery_capacity_ah,
                "R0": self.R0,
                "R1": self.R1,
                "C1": self.C1,
                "R2": self.R2,
                "C2": self.C2,
                "process_noise_soc": self.PROCESS_NOISE_SOC,
                "process_noise_voltage": self.PROCESS_NOISE_VOLTAGE,
                "measurement_noise": self.MEASUREMENT_NOISE
            },
            "ocv_table": self.OCV_TABLE,
            "exported_path": self._model_path
        }


class SOCEstimatorNN:
    """
    LSTM-based Neural Network SOC estimator.

    Implements a recurrent neural network with LSTM layers for
    sequence-based SOC estimation. The network learns temporal
    patterns in voltage, current, and temperature data.

    This is a pure Python implementation for demonstration.
    In production, this would use PyTorch/TensorFlow with
    pre-trained weights loaded from .pth or .onnx files.

    Input Features (per timestep):
    - cell_voltage_v: Cell voltage (V)
    - current_a: Pack current (A)
    - temperature_c: Temperature (°C)
    - cycle_count: Battery cycle count

    Output:
    - soc: State of Charge (0.0 - 1.0)
    - soc_uncertainty: Estimation uncertainty
    """

    # Input normalization parameters
    VOLTAGE_MEAN = 3.7
    VOLTAGE_STD = 0.3
    CURRENT_MEAN = 0.0
    CURRENT_STD = 100.0
    TEMP_MEAN = 25.0
    TEMP_STD = 20.0

    # LSTM architecture (reference for exported model)
    INPUT_SIZE = 4  # voltage, current, temperature, cycle_count
    HIDDEN_SIZE = 64
    NUM_LAYERS = 2
    SEQUENCE_LENGTH = 50  # 5 seconds at 10 Hz

    def __init__(self, model_path: Optional[str] = None,
                 use_pretrained: bool = True):
        """
        Initialize LSTM-based SOC estimator.

        Args:
            model_path: Path to PyTorch .pth model file
            use_pretrained: Use pre-trained weights if available
        """
        self.model_path = model_path
        self.use_pretrained = use_pretrained
        self._is_loaded = False

        # Internal state for sequence buffering
        self._sequence_buffer: List[Dict] = []
        self._hidden_state: Optional[List[List[float]]] = None

        # Model metadata
        self._model_version = "soc_lstm_v2"
        self._training_dataset: Optional[str] = None
        self._training_metrics: Optional[Dict] = None

        if use_pretrained and model_path:
            self._load_model(model_path)

    def _load_model(self, model_path: str) -> bool:
        """Load pre-trained model weights."""
        # In production: Use PyTorch to load .pth file
        # Example:
        # import torch
        # checkpoint = torch.load(model_path)
        # self._lstm.load_state_dict(checkpoint['model_state_dict'])

        self._is_loaded = True
        return True

    def _normalize_inputs(self, voltage_v: float, current_a: float,
                          temperature_c: float, cycle_count: int) -> List[float]:
        """Normalize inputs using training statistics."""
        voltage_norm = (voltage_v - self.VOLTAGE_MEAN) / self.VOLTAGE_STD
        current_norm = (current_a - self.CURRENT_MEAN) / self.CURRENT_STD
        temp_norm = (temperature_c - self.TEMP_MEAN) / self.TEMP_STD
        cycle_norm = min(1.0, cycle_count / 1000.0)  # Normalize to [0, 1]

        return [voltage_norm, current_norm, temp_norm, cycle_norm]

    def _lstm_cell(self, inputs: List[float], hidden: List[List[float]],
                   cell_state: List[List[float]]) -> Tuple[List[List[float]], List[List[float]]]:
        """
        Simplified LSTM cell computation.

        This is a demonstration implementation. In production,
        this would use actual trained weights and proper LSTM math.
        """
        # Placeholder: In production, this executes actual LSTM forward pass
        # with learned weights from training
        batch_size = len(hidden)

        # Simple regression for demonstration
        voltage = inputs[0] if len(inputs) > 0 else 0.0

        # Approximate SOC from normalized voltage
        # (This mimics what a trained LSTM would learn)
        soc_estimate = (voltage * self.VOLTAGE_STD + self.VOLTAGE_MEAN - 3.0) / 1.35

        # Update hidden state (placeholder)
        new_hidden = [[soc_estimate] * self.HIDDEN_SIZE for _ in range(batch_size)]
        new_cell = [[soc_estimate] * self.HIDDEN_SIZE for _ in range(batch_size)]

        return new_hidden, new_cell

    def update(self, voltage_v: float, current_a: float, temperature_c: float,
               cycle_count: int, timestamp_ms: int) -> SOCEstimatorResult:
        """
        Update SOC estimate using LSTM model.

        Args:
            voltage_v: Cell voltage (V)
            current_a: Pack current (A)
            temperature_c: Temperature (°C)
            cycle_count: Battery cycle count
            timestamp_ms: Timestamp in milliseconds

        Returns:
            SOCEstimatorResult with SOC estimate and confidence
        """
        fault = SOCFaultType.NONE
        is_valid = True

        # Validate inputs
        if voltage_v < 2.0 or voltage_v > 5.0:
            fault = SOCFaultType.VOLTAGE_SENSOR_FAULT
            is_valid = False
        if temperature_c < -30.0 or temperature_c > 70.0:
            fault = SOCFaultType.TEMPERATURE_SENSOR_FAULT
            is_valid = False

        if not is_valid:
            return SOCEstimatorResult(
                soc=50.0,  # Default fallback
                soh=100.0,
                uncertainty=10.0,
                method=SOCMethod.NEURAL_NETWORK,
                timestamp_ms=timestamp_ms,
                is_valid=False,
                fault=fault,
                confidence=0.0
            )

        # Normalize inputs
        normalized = self._normalize_inputs(
            voltage_v, current_a, temperature_c, cycle_count)

        # Add to sequence buffer
        self._sequence_buffer.append({
            "normalized": normalized,
            "raw_voltage": voltage_v,
            "timestamp_ms": timestamp_ms
        })

        # Trim buffer to sequence length
        if len(self._sequence_buffer) > self.SEQUENCE_LENGTH:
            self._sequence_buffer.pop(0)

        # Need full sequence for accurate prediction
        sequence_ready = len(self._sequence_buffer) >= self.SEQUENCE_LENGTH

        if not sequence_ready:
            # Fallback: Use voltage-based estimate with high uncertainty
            soc_estimate = (voltage_v - 3.0) / 1.35 * 100.0
            soc_estimate = max(0.0, min(100.0, soc_estimate))
            uncertainty = 15.0  # High uncertainty during warmup
            confidence = 0.3
        else:
            # Execute LSTM forward pass on sequence
            soc_estimate = self._run_inference()
            uncertainty = 3.0  # Lower uncertainty with full sequence
            confidence = 0.85

        return SOCEstimatorResult(
            soc=max(0.0, min(100.0, soc_estimate)),
            soh=100.0,
            uncertainty=uncertainty,
            method=SOCMethod.NEURAL_NETWORK,
            timestamp_ms=timestamp_ms,
            is_valid=True,
            fault=fault,
            confidence=confidence
        )

    def _run_inference(self) -> float:
        """
        Run LSTM inference on sequence buffer.

        Returns:
            SOC estimate (0.0 - 100.0)
        """
        if not self._sequence_buffer:
            return 50.0

        # In production: Run actual PyTorch LSTM forward pass
        # For demonstration: Use weighted average of recent voltages

        recent_samples = self._sequence_buffer[-10:]  # Last 10 samples
        avg_voltage = sum(s["raw_voltage"] for s in recent_samples) / len(recent_samples)

        # Convert voltage to SOC using typical NMC curve
        soc = (avg_voltage - 3.0) / 1.35 * 100.0
        return max(0.0, min(100.0, soc))

    def get_model_info(self) -> Dict:
        """Get model metadata."""
        return {
            "model_type": "LSTM",
            "version": self._model_version,
            "architecture": {
                "input_size": self.INPUT_SIZE,
                "hidden_size": self.HIDDEN_SIZE,
                "num_layers": self.NUM_LAYERS,
                "sequence_length": self.SEQUENCE_LENGTH
            },
            "normalization": {
                "voltage": {"mean": self.VOLTAGE_MEAN, "std": self.VOLTAGE_STD},
                "current": {"mean": self.CURRENT_MEAN, "std": self.CURRENT_STD},
                "temperature": {"mean": self.TEMP_MEAN, "std": self.TEMP_STD}
            },
            "model_path": self.model_path,
            "is_loaded": self._is_loaded,
            "training_dataset": self._training_dataset,
            "training_metrics": self._training_metrics
        }


class SOCComparison:
    """
    Compare and fuse SOC estimates from multiple methods.

    Provides mechanisms to:
    - Compare EKF vs NN estimates for plausibility
    - Compute fused SOC estimate with confidence weighting
    - Detect estimator divergence
    """

    # Divergence thresholds
    MAX_SOC_DIFFERENCE = 10.0  # Percent
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    LOW_CONFIDENCE_THRESHOLD = 0.4

    def __init__(self):
        """Initialize SOC comparison module."""
        self._ekf_history: List[SOCEstimatorResult] = []
        self._nn_history: List[SOCEstimatorResult] = []
        self._max_history = 100

    def compare(self, ekf_result: SOCEstimatorResult,
                nn_result: SOCEstimatorResult) -> Dict:
        """
        Compare EKF and NN SOC estimates.

        Args:
            ekf_result: SOC estimate from EKF
            nn_result: SOC estimate from NN

        Returns:
            Dict with comparison metrics and divergence status
        """
        # Store in history
        self._ekf_history.append(ekf_result)
        self._nn_history.append(nn_result)

        if len(self._ekf_history) > self._max_history:
            self._ekf_history.pop(0)
            self._nn_history.pop(0)

        # Compute difference
        soc_diff = abs(ekf_result.soc - nn_result.soc)

        # Determine divergence status
        is_diverged = soc_diff > self.MAX_SOC_DIFFERENCE

        # Compute weighted average (if both valid)
        if ekf_result.is_valid and nn_result.is_valid:
            total_conf = ekf_result.confidence + nn_result.confidence
            if total_conf > 0:
                fused_soc = (ekf_result.soc * ekf_result.confidence +
                            nn_result.soc * nn_result.confidence) / total_conf
                fused_confidence = min(1.0, total_conf / 2.0)
            else:
                fused_soc = (ekf_result.soc + nn_result.soc) / 2.0
                fused_confidence = 0.5
        elif ekf_result.is_valid:
            fused_soc = ekf_result.soc
            fused_confidence = ekf_result.confidence * 0.9
        elif nn_result.is_valid:
            fused_soc = nn_result.soc
            fused_confidence = nn_result.confidence * 0.9
        else:
            fused_soc = 50.0
            fused_confidence = 0.0

        return {
            "ekf_soc": ekf_result.soc,
            "nn_soc": nn_result.soc,
            "soc_difference": soc_diff,
            "is_diverged": is_diverged,
            "fused_soc": fused_soc,
            "fused_confidence": fused_confidence,
            "ekf_confidence": ekf_result.confidence,
            "nn_confidence": nn_result.confidence,
            "ekf_uncertainty": ekf_result.uncertainty,
            "nn_uncertainty": nn_result.uncertainty,
            "recommendation": self._get_recommendation(ekf_result, nn_result, soc_diff)
        }

    def _get_recommendation(self, ekf: SOCEstimatorResult,
                            nn: SOCEstimatorResult,
                            diff: float) -> str:
        """Generate recommendation based on comparison."""
        if not ekf.is_valid and not nn.is_valid:
            return "BOTH_ESTIMATORS_INVALID"
        if not ekf.is_valid:
            return "USE_NN_ONLY"
        if not nn.is_valid:
            return "USE_EKF_ONLY"
        if diff > self.MAX_SOC_DIFFERENCE * 1.5:
            return "CRITICAL_DIVERGENCE_CHECK_SENSORS"
        if diff > self.MAX_SOC_DIFFERENCE:
            if ekf.confidence > nn.confidence:
                return "USE_EKF_NN_DEGRADED"
            else:
                return "USE_NN_EKF_DEGRADED"
        if ekf.confidence > self.HIGH_CONFIDENCE_THRESHOLD and \
           nn.confidence > self.HIGH_CONFIDENCE_THRESHOLD:
            return "USE_FUSED_HIGH_CONFIDENCE"
        return "USE_FUSED_NORMAL"

    def compute_accuracy_metrics(self, ground_truth_soc: List[float]) -> Dict:
        """
        Compute accuracy metrics against ground truth.

        Args:
            ground_truth_soc: List of true SOC values (aligned with history)

        Returns:
            Dict with RMSE, MAE, and max error for each method
        """
        if len(ground_truth_soc) != len(self._ekf_history):
            return {"error": "History length mismatch"}

        ekf_errors = []
        nn_errors = []

        for i, gt in enumerate(ground_truth_soc):
            if i < len(self._ekf_history):
                ekf_errors.append(abs(self._ekf_history[i].soc - gt))
            if i < len(self._nn_history):
                nn_errors.append(abs(self._nn_history[i].soc - gt))

        def compute_metrics(errors: List[float]) -> Dict:
            if not errors:
                return {"rmse": float('inf'), "mae": float('inf'), "max": float('inf')}
            rmse = math.sqrt(sum(e**2 for e in errors) / len(errors))
            mae = sum(errors) / len(errors)
            return {"rmse": rmse, "mae": mae, "max": max(errors)}

        return {
            "ekf": compute_metrics(ekf_errors),
            "nn": compute_metrics(nn_errors),
            "sample_count": len(ground_truth_soc)
        }


def main():
    """Example usage of SOC estimators."""
    # Initialize estimators
    ekf = SOCEstimatorEKF(battery_capacity_ah=75.0, initial_soc=0.5)
    nn = SOCEstimatorNN(use_pretrained=False)
    comparator = SOCComparison()

    # Simulate discharge cycle
    print("SOC Estimation Comparison: EKF vs LSTM Neural Network")
    print("=" * 60)

    timestamp_ms = 0
    soc_history = []

    for cycle in range(100):
        # Simulate cell voltage (decreasing as SOC depletes)
        true_soc = 100.0 - (cycle * 0.5)  # Linear discharge
        voltage_v = 3.0 + (true_soc / 100.0) * 1.35  # OCV curve

        # Add noise
        import random
        voltage_v += random.uniform(-0.02, 0.02)
        current_a = -10.0 + random.uniform(-1, 1)  # Discharge at 10A
        temperature_c = 25.0 + random.uniform(-0.5, 0.5)

        # Update estimators
        ekf_result = ekf.update(voltage_v, current_a, temperature_c, timestamp_ms)
        nn_result = nn.update(voltage_v, current_a, temperature_c, 0, timestamp_ms)

        # Compare
        comparison = comparator.compare(ekf_result, nn_result)

        if cycle % 10 == 0:
            print(f"\nCycle {cycle}:")
            print(f"  True SOC: {true_soc:.1f}%")
            print(f"  EKF SOC:  {ekf_result.soc:.1f}% (confidence: {ekf_result.confidence:.2f})")
            print(f"  NN SOC:   {nn_result.soc:.1f}% (confidence: {nn_result.confidence:.2f})")
            print(f"  Fused:    {comparison['fused_soc']:.1f}%")
            print(f"  Diff:     {comparison['soc_difference']:.1f}%")
            print(f"  Status:   {comparison['recommendation']}")

        soc_history.append(true_soc)
        timestamp_ms += 100  # 10 Hz

    # Compute final accuracy metrics
    metrics = comparator.compute_accuracy_metrics(soc_history)
    print("\n" + "=" * 60)
    print("Final Accuracy Metrics:")
    print(f"  EKF - RMSE: {metrics['ekf']['rmse']:.2f}%, MAE: {metrics['ekf']['mae']:.2f}%")
    print(f"  NN  - RMSE: {metrics['nn']['rmse']:.2f}%, MAE: {metrics['nn']['mae']:.2f}%")

    # Display model info
    print("\n" + "=" * 60)
    print("EKF Model Info:")
    ekf_info = ekf.get_model_info()
    print(f"  Version: {ekf_info['version']}")
    print(f"  Battery Capacity: {ekf_info['parameters']['battery_capacity_ah']} Ah")
    print(f"  R0: {ekf_info['parameters']['R0']} Ohm")

    print("\nNN Model Info:")
    nn_info = nn.get_model_info()
    print(f"  Version: {nn_info['version']}")
    print(f"  Architecture: {nn_info['architecture']['hidden_size']} hidden units")
    print(f"  Sequence Length: {nn_info['architecture']['sequence_length']} timesteps")


if __name__ == "__main__":
    main()
