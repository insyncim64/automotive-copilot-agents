---
mode: ask
description: "Generate ACC controller design artifacts with safety constraints and test plan"
---
Create a production-oriented Adaptive Cruise Control (ACC) controller package for embedded C/C++ integration.

Inputs:
- Vehicle class and mass range
- Target speed range and operating conditions
- Available sensors/signals (radar, camera, wheel speed, braking, torque requests)
- ECU/platform constraints (cycle time, memory, AUTOSAR Classic/Adaptive)
- Safety target (ASIL level)

Output requirements:
- Longitudinal control architecture and state machine
- Controller strategy (PID/LQR/MPC) with tuning rationale
- Signal I/O list with units and scaling
- Failure handling and fallback behavior
- ISO 26262-aligned safety mechanisms and assumptions
- Verification plan covering MiL, SiL, HiL, and edge cases
- C/C++ implementation skeleton and test pseudocode

Constraints:
- Keep deterministic timing and embedded memory constraints explicit
- Prioritize robustness over aggressive performance tuning
- Include traceability links between requirements, design, and tests
