# Automotive Copilot Agents - Agent Catalog

> Comprehensive catalog of automotive domain experts for GitHub Copilot Chat.

**Document Version**: 1.0
**Last Updated**: 2026-03-22
**Phase**: 1 (Foundation)

---

## Quick Reference

| Domain | Agent | Priority | Activation Keyword |
|--------|-------|----------|-------------------|
| ADAS | @automotive-adas-perception-engineer | P0 | "sensor fusion", "camera", "radar", "LiDAR" |
| Safety | @automotive-functional-safety-engineer | P0 | "ASIL", "ISO 26262", "HARA", "FMEA" |
| Security | @automotive-cybersecurity-engineer | P0 | "TARA", "ISO 21434", "SecOC", "HSM" |
| AUTOSAR | @automotive-autosar-architect | P0 | "AUTOSAR", "arxml", "RTE", "BSW" |
| Battery | @automotive-battery-bms-engineer | P0 | "BMS", "cell voltage", "SOC", "SOH" |
| ADAS Planning | @automotive-adas-planning-engineer | P1 | "path planning", "trajectory", "motion planning" |
| ADAS Control | @automotive-adas-control-engineer | P1 | "longitudinal control", "lateral control", "MPC" |
| Powertrain | @automotive-powertrain-control-engineer | P1 | "engine", "transmission", "torque" |
| Chassis | @automotive-chassis-systems-engineer | P1 | "suspension", "brake", "steering", "ESC" |
| Diagnostics | @automotive-diagnostics-engineer | P1 | "UDS", "DTC", "OBD", "diagnostics" |

---

## Phase 1 Agents (Foundation)

### 1. automotive-adas-perception-engineer

**Instruction File**: `.github/copilot/instructions/automotive-adas-perception-engineer.md`

**Domain**: ADAS perception systems for L2-L4 autonomous driving

**Expertise**:
- Multi-sensor fusion (EKF, UKF, particle filters, JPDA, MHT)
- Camera processing (2D/3D object detection, semantic segmentation, lane detection)
- Radar processing (FMCW, 4D imaging, CFAR, Doppler tracking)
- LiDAR processing (point cloud, 3D detection, SLAM)
- Multi-object tracking (SORT, DeepSORT, AB3DMOT)
- ISO 26262 ASIL-D and ISO 21448 SOTIF compliance
- AUTOSAR Adaptive integration (ara::com services)

**Example Activations**:
- "How do I implement EKF for camera-radar fusion?"
- "What's the best approach for 3D object detection from LiDAR?"
- "Help me design a SOTIF test scenario for tunnel transitions"
- "Show me an AUTOSAR Adaptive service definition for perception output"
- "How do I achieve ASIL-D compliance for my perception pipeline?"

**Collaboration Interfaces**:
- Outputs: `ObjectList`, `DrivableArea`, `LaneGraph` to planning agent
- Inputs: Vehicle dynamics from control agent
- Safety mechanisms: Cross-sensor plausibility, temporal consistency checks

**Performance Benchmarks**:
| Metric | L2 (Highway Pilot) | L3 (Traffic Jam Pilot) | L4 (Robotaxi) |
|--------|-------------------|----------------------|--------------|
| End-to-end Latency | < 100 ms | < 50 ms | < 30 ms |
| Position Accuracy (RMS) | < 0.5 m | < 0.3 m | < 0.15 m |
| False Positive Rate | < 0.1 / km | < 0.01 / km | < 0.001 / km |

---

### 2. automotive-functional-safety-engineer

**Instruction File**: `.github/copilot/instructions/automotive-functional-safety-engineer.md`

**Domain**: ISO 26262 functional safety lifecycle from concept to production

**Expertise**:
- HARA (Hazard Analysis and Risk Assessment)
- FMEA (Failure Mode and Effects Analysis)
- FTA (Fault Tree Analysis)
- ASIL decomposition and dependent failure analysis
- Safety mechanism design (diagnostic coverage, E2E protection)
- Safety case development and work product reviews
- ISO 26262-6 software safety requirements

**Example Activations**:
- "Help me perform HARA for an electric brake booster system"
- "What diagnostic coverage is required for ASIL D?"
- "Show me an example ASIL decomposition for redundant braking"
- "How do I structure a safety case for ISO 26262 certification?"
- "Review my FMEA for completeness"

**Collaboration Interfaces**:
- Inputs: System architecture from AUTOSAR architect
- Outputs: Safety goals, safety requirements to all domain agents
- Reviews: All safety-critical code and designs

**Safety Analysis Templates**:
- HARA entry format with S/E/C classification
- FMEA workbook with RPN calculation
- FTA construction with quantitative analysis
- ASIL decomposition record with independence argument

---

### 3. automotive-cybersecurity-engineer

**Instruction File**: `.github/copilot/instructions/automotive-cybersecurity-engineer.md`

**Domain**: ISO/SAE 21434 cybersecurity engineering and UNECE R155 compliance

**Expertise**:
- TARA (Threat Analysis and Risk Assessment)
- Secure software architecture (defense-in-depth)
- Cryptographic key management and HSM integration
- SecOC (Secure Onboard Communication)
- Secure boot and code signing
- Intrusion detection systems (IDS)
- Penetration testing and vulnerability management

**Example Activations**:
- "Perform TARA for a vehicle gateway ECU"
- "How do I implement SecOC for CAN message authentication?"
- "Show me a secure boot chain for AUTOSAR Adaptive"
- "What cryptographic algorithms are approved for automotive?"
- "Help me design an intrusion detection rule set"

**Collaboration Interfaces**:
- Inputs: Network architecture from system architect
- Outputs: Security requirements, cyber security goals
- Reviews: All external interface designs and code

**Crypto Configuration**:
| Purpose | Algorithm | Key Size | Storage |
|---------|-----------|----------|---------|
| Code Signing | ECDSA | P-384 | HSM (offline) |
| Secure Boot | ECDSA | P-256 | HSM |
| SecOC MAC | AES-CMAC | 128-bit | HSM |
| TLS Session | AES-GCM | 256-bit | HSM |
| V2X Signing | ECDSA | P-256 | HSM |

---

### 4. automotive-autosar-architect

**Instruction File**: `.github/copilot/instructions/automotive-autosar-architect.md`

**Domain**: AUTOSAR Classic and Adaptive platform architecture

**Expertise**:
- AUTOSAR Classic platform (BSW configuration, RTE generation)
- AUTOSAR Adaptive platform (service-oriented architecture)
- ARXML system description and configuration
- Software component design and port interfaces
- BSW module configuration (Can, CanIf, Com, PduR, Dem, Dcm)
- Adaptive service definition (ara::com, ara::exec, ara::log)
- Migration strategies from Classic to Adaptive

**Example Activations**:
- "Show me an AUTOSAR Classic software component template"
- "How do I configure the Dem module for DTC storage?"
- "Design a service-oriented architecture for ADAS perception"
- "What's the difference between Sender-Receiver and Client-Server ports?"
- "Help me define an ara::com service for battery data"

**Collaboration Interfaces**:
- Inputs: System requirements from OEM
- Outputs: ECU configuration, software components to developers
- Integration: RTE generation, BSW integration support

**Key Patterns**:
- Sender-Receiver interface for data exchange
- Client-Server interface for RPC operations
- Mode Switch interface for state coordination
- Field notification for event signaling

---

### 5. automotive-battery-bms-engineer

**Instruction File**: `.github/copilot/instructions/automotive-battery-bms-engineer.md`

**Domain**: Battery Management Systems for electric vehicles

**Expertise**:
- Cell voltage monitoring and protection
- State of Charge (SOC) estimation (EKF, adaptive filtering)
- State of Health (SOH) estimation
- Cell balancing algorithms (passive/active)
- Thermal management and fault detection
- ISO 26262 ASIL-C/D compliance for battery safety
- HV contactor control and precharge management

**Example Activations**:
- "How do I implement coulomb counting with voltage correction?"
- "Show me an EKF-based SOC estimation algorithm"
- "What safety mechanisms are needed for ASIL C cell monitoring?"
- "Design a cell balancing strategy for a 96s battery pack"
- "Help me define DTCs for battery faults"

**Collaboration Interfaces**:
- Outputs: SOC, SOH, power limits to vehicle control
- Inputs: Charger commands, thermal management requests
- Safety: Contactor control coordination with diagnostics agent

**Key Parameters**:
| Parameter | Typical Value | Unit |
|-----------|--------------|------|
| Cell voltage range | 2.5 - 4.2 | V |
| Max cell imbalance | 10 | mV |
| SOC estimation accuracy | < 5 | % |
| SOH estimation accuracy | < 3 | % |
| Contactor open time | < 100 | ms |

---

### 6. automotive-adas-planning-engineer

**Instruction File**: `.github/copilot/instructions/automotive-adas-planning-engineer.md`

**Domain**: Motion planning and trajectory generation for ADAS/AD

**Expertise**:
- Path planning algorithms (A*, RRT*, lattice planners)
- Trajectory generation (polynomials, splines, optimization)
- Behavioral planning (state machines, decision making)
- Trajectory optimization (MPC, convex optimization)
- Collision avoidance and emergency maneuvers
- ODD-aware planning constraints
- ISO 26262 and SOTIF compliance for planning functions

**Example Activations**:
- "How do I implement a lattice-based motion planner?"
- "Show me a polynomial trajectory generation algorithm"
- "Design a state machine for highway lane changes"
- "What's the best approach for real-time trajectory optimization?"
- "Help me define ODD constraints for urban driving"

**Collaboration Interfaces**:
- Inputs: Object lists, drivable area from perception agent
- Outputs: Target trajectory, speed profile to control agent
- Constraints: Traffic rules, vehicle dynamics limits

**Planning Hierarchy**:
1. Route planning (graph search on road network)
2. Behavioral planning (tactical decisions)
3. Motion planning (geometric path + velocity profile)
4. Trajectory smoothing (kinematic feasibility)

---

### 7. automotive-adas-control-engineer

**Instruction File**: `.github/copilot/instructions/automotive-adas-control-engineer.md`

**Domain**: Vehicle motion control (longitudinal and lateral)

**Expertise**:
- Longitudinal control (adaptive cruise control, speed tracking)
- Lateral control (lane keeping, path tracking)
- Model Predictive Control (MPC) design
- PID control with gain scheduling
- Vehicle dynamics modeling (bicycle model, tire models)
- Actuator coordination (throttle, brake, steering)
- ISO 26262 ASIL-D control implementations

**Example Activations**:
- "How do I tune an MPC for lane keeping?"
- "Show me an adaptive cruise control algorithm"
- "Design a gain-scheduled PID for vehicle speed control"
- "What's the bicycle model and how do I use it?"
- "Help me implement a pure pursuit controller"

**Collaboration Interfaces**:
- Inputs: Target trajectory from planning agent
- Outputs: Actuator commands (throttle, brake, steering)
- Feedback: Vehicle state estimation from sensors

**Control Benchmarks**:
| Controller | Update Rate | Latency Budget | Typical Use |
|-----------|------------|----------------|-------------|
| MPC Lateral | 100 Hz | < 10 ms | Lane keeping |
| PID Longitudinal | 100 Hz | < 5 ms | ACC |
| Pure Pursuit | 50 Hz | < 20 ms | Low-speed tracking |

---

### 8. automotive-powertrain-control-engineer

**Instruction File**: `.github/copilot/instructions/automotive-powertrain-control-engineer.md`

**Domain**: Engine, transmission, and electric powertrain control

**Expertise**:
- Engine control (air-fuel ratio, ignition timing, torque management)
- Transmission control (shift scheduling, clutch control)
- Electric motor control (FOC, torque control, field weakening)
- Hybrid powertrain coordination
- Emissions compliance (OBD, evaporative emissions)
- Drivability optimization
- ISO 26262 compliance for powertrain safety

**Example Activations**:
- "How do I implement field-oriented control for a PMSM?"
- "Show me a transmission shift scheduling algorithm"
- "Design an air-fuel ratio controller for stoichiometric operation"
- "What's the best approach for torque blending in a hybrid?"
- "Help me define OBD monitors for catalyst efficiency"

**Collaboration Interfaces**:
- Inputs: Driver demand (pedal position), vehicle state
- Outputs: Torque commands to actuators
- Coordination: Chassis systems for traction control

**Powertrain Types**:
- ICE: Spark ignition, compression ignition
- Electric: PMSM, induction motor, switched reluctance
- Hybrid: Series, parallel, power-split architectures

---

### 9. automotive-chassis-systems-engineer

**Instruction File**: `.github/copilot/instructions/automotive-chassis-systems-engineer.md`

**Domain**: Chassis control systems (brake, steering, suspension)

**Expertise**:
- Electronic Stability Control (ESC) algorithms
- Anti-lock Braking System (ABS)
- Electric Power Steering (EPS) control
- Active suspension control
- Brake blending (regenerative + friction)
- Torque vectoring
- ISO 26262 ASIL-D chassis safety

**Example Activations**:
- "How do I implement ABS slip control?"
- "Show me an ESC yaw stability algorithm"
- "Design a torque vectoring controller for AWD"
- "What's the best approach for brake pedal feel emulation?"
- "Help me tune an active suspension controller"

**Collaboration Interfaces**:
- Inputs: Wheel speeds, yaw rate, lateral acceleration
- Outputs: Brake pressure, steering torque, damping commands
- Safety: Redundant sensor processing with perception agent

**Chassis Systems**:
| System | ASIL | Update Rate | Key Sensors |
|--------|------|-------------|-------------|
| ABS | D | 100 Hz | Wheel speed x4 |
| ESC | D | 100 Hz | Yaw rate, IMU |
| EPS | D | 100 Hz | Torque sensor, angle |
| Active Suspension | B | 50 Hz | Accelerometers x4 |

---

### 10. automotive-diagnostics-engineer

**Instruction File**: `.github/copilot/instructions/automotive-diagnostics-engineer.md`

**Domain**: Vehicle diagnostics and service protocols

**Expertise**:
- UDS (Unified Diagnostic Services, ISO 14229)
- OBD-II (On-Board Diagnostics)
- DTC (Diagnostic Trouble Code) management
- Diagnostic communication (DoIP, CAN diagnostics)
- Security access (seed-key, challenge-response)
- Flash bootloading and reprogramming
- ISO 26262 diagnostics for safety functions

**Example Activations**:
- "How do I implement UDS service 0x22 (ReadDataByIdentifier)?"
- "Show me a DTC structure per ISO 14229"
- "Design a security access algorithm for protected services"
- "What's the difference between OBD-II Mode 1 and Mode 6?"
- "Help me define diagnostic services for a BMS ECU"

**Collaboration Interfaces**:
- Inputs: Fault data from all domain agents
- Outputs: DTC status, freeze frame data
- Integration: Security for protected diagnostic access

**Key UDS Services**:
| Service ID | Name | Use Case |
|------------|------|----------|
| 0x10 | DiagnosticSessionControl | Enter extended/programming session |
| 0x22 | ReadDataByIdentifier | Read calibration, DTC info |
| 0x27 | SecurityAccess | Unlock protected services |
| 0x2E | WriteDataByIdentifier | Write calibration parameters |
| 0x31 | RoutineControl | Execute OBD tests, cell balancing |
| 0x34 | RequestDownload | Prepare for flash download |
| 0x36 | TransferData | Send firmware blocks |
| 0x3E | TesterPresent | Keep session alive |

---

## Installation

### Prerequisites

- VS Code 1.90 or later
- GitHub Copilot extension 1.100 or later
- GitHub Copilot Chat enabled

### Quick Install

**Windows (PowerShell)**:
```powershell
cd automotive-copilot-agents
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\setup.ps1
.\scripts\validate-install.ps1
```

**Linux/macOS (Bash)**:
```bash
cd automotive-copilot-agents
chmod +x scripts/setup.sh
./scripts/setup.sh
./scripts/setup.sh --status
```

### Verify Installation

```powershell
# Windows
.\scripts\validate-install.ps1 -Verbose

# Linux/macOS
./scripts/setup.sh --status
```

Expected output:
- 10+ agent instruction files
- 10+ skill context files
- 20+ knowledge files
- No empty files detected

---

## Usage Patterns

### Activating Agents in Copilot Chat

1. **Direct mention**: Start your question with `@agent-name`
   ```
   @automotive-adas-perception-engineer How do I fuse camera and radar detections?
   ```

2. **Contextual activation**: Use domain keywords
   ```
   I'm implementing sensor fusion for L2 ADAS. What's the best EKF structure?
   ```

3. **Multi-agent collaboration**: Reference multiple agents
   ```
   @automotive-functional-safety-engineer @automotive-adas-perception-engineer
   What ASIL level applies to camera-radar fusion?
   ```

### Using Context Files (@-mention)

Context files provide reference material for specific topics:

**ADAS Context**:
- `@context/skills/adas/sensor-fusion.md` - EKF/UKF fusion algorithms
- `@context/skills/adas/camera-processing.md` - 2D/3D vision pipelines
- `@context/skills/adas/radar-processing.md` - FMCW radar processing
- `@context/skills/adas/lidar-processing.md` - Point cloud processing
- `@context/skills/adas/object-tracking.md` - SORT, DeepSORT algorithms
- `@context/skills/adas/calibration.md` - Extrinsic calibration methods
- `@context/skills/adas/sotif-testing.md` - SOTIF scenario testing

### Running Workflows (VS Code Tasks)

Access tasks via **Terminal > Run Task...** or `Ctrl+Shift+P > Tasks: Run Task`

**Installation Tasks**:
- `Agents: Install` - Install all agents to .github/copilot
- `Agents: Check Status` - Show current installation status
- `Agents: Uninstall` - Remove agents (with confirmation)

**Validation Tasks**:
- `Validate: Installation` - Run comprehensive validation
- `Validate: Verbose` - Detailed validation with file listing
- `Validate: Export JSON` - Export results to JSON for CI/CD

**Domain Workflows**:
- `ADAS: Perception Pipeline Test` - Test perception algorithms
- `AUTOSAR: Validate ARXML` - Check ARXML configuration
- `Diagnostics: UDS Service Scan` - Scan for UDS services
- `Safety: Run FMEA Analysis` - Generate FMEA workbook
- `Security: Run TARA Analysis` - Perform threat analysis

---

## Cross-Agent Collaboration

### ADAS Pipeline

```
@automotive-adas-perception-engineer
         |
         v (ObjectList, DrivableArea)
@automotive-adas-planning-engineer
         |
         v (Trajectory, Speed Profile)
@automotive-adas-control-engineer
         |
         v (Actuator Commands)
Vehicle (Throttle, Brake, Steering)
```

### Safety Integration

```
@automotive-functional-safety-engineer
         |
         v (Safety Requirements)
All Domain Agents
         |
         v (Safety Mechanisms)
@automotive-diagnostics-engineer
         |
         v (DTC Storage, Fault Reporting)
```

### Security Integration

```
@automotive-cybersecurity-engineer
         |
         v (Security Requirements)
@automotive-autosar-architect
         |
         v (Secure Architecture)
All Domain Agents
         |
         v (Secure Boot, SecOC)
@automotive-diagnostics-engineer
         |
         v (Secure Diagnostic Access)
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-22 | Initial Phase 1 catalog with 10 agents |

---

## Related Documentation

- [GETTING-STARTED.md](GETTING-STARTED.md) - Installation and first steps
- [CONTEXT-REFERENCE.md](CONTEXT-REFERENCE.md) - Complete context file reference
- [MIGRATION-PLAN.md](../MIGRATION-PLAN.md) - Migration strategy from Claude Code

---

*Automotive Copilot Agents v1.0 - Foundation Phase Complete*
