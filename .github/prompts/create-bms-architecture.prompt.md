---
mode: ask
description: "Create BMS architecture proposal with SoC/SoH, safety, diagnostics, and validation"
---
Design an automotive Battery Management System (BMS) architecture proposal suitable for EV/HEV programs.

Inputs:
- Pack configuration (series/parallel topology)
- Cell chemistry and operating limits
- Sampling/update rates and ECU constraints
- Network interfaces (CAN/CAN FD/Ethernet)
- Safety and regulatory targets

Output requirements:
- Functional decomposition (measurement, estimation, balancing, thermal, safety)
- SoC/SoH estimation strategy and data requirements
- Contactor/precharge and HV interlock control concept
- Diagnostics model (fault classes, DTC strategy, degraded modes)
- Communication signal map and interface contracts
- Validation strategy (bench, HiL, vehicle)
- Risk list with mitigations (thermal runaway, sensor faults, isolation faults)

Engineering constraints:
- Explicitly address determinism, memory limits, and startup behavior
- Include requirement-to-test traceability structure
- Prefer fail-safe behavior and diagnosability
