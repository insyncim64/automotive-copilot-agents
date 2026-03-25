# Security TARA Analysis Demo

This example project demonstrates the ISO/SAE 21434 Threat Analysis and Risk Assessment (TARA) workflow for automotive cybersecurity analysis.

## Overview

This demo showcases:
- Asset identification and classification (CIA triad)
- STRIDE threat analysis
- Attack tree generation for critical assets
- Risk assessment using SAE-J3061 methodology
- Security control selection and residual risk evaluation
- TARA report generation and traceability

## Project Structure

```
tara-analysis-demo/
├── README.md
├── architecture/
│   ├── system-overview.md       # High-level architecture
│   ├── network-topology.md      # CAN/Ethernet topology
│   ├── trust-boundaries.md      # Security trust boundaries
│   └── data-flow-diagrams/
│       ├── external-dfd.md      # Context-level DFD
│       ├── level0-dfd.md        # System-level DFD
│       └── level1-dfd.md        # Component-level DFD
├── security/
│   ├── assets/
│   │   ├── ecu-inventory.yaml   # ECU asset list
│   │   ├── interfaces.yaml      # Communication interfaces
│   │   ├── data-assets.yaml     # Data asset catalog
│   │   ├── classified-assets.yaml   # CIA classification
│   │   ├── data-flow-diagram.yaml   # Trust boundary flows
│   │   └── dependency-map.md    # Asset dependencies
│   ├── threats/
│   │   ├── stride-catalog.yaml  # STRIDE analysis results
│   │   ├── cve-mapping.yaml     # CVE cross-reference
│   │   ├── attack-trees/
│   │   │   ├── remote-access.yaml
│   │   │   ├── firmware-tamper.yaml
│   │   │   └── can-injection.yaml
│   │   └── threat-catalog.md  # Consolidated threat list
│   ├── risks/
│   │   ├── safety-impact.yaml     # ISO 26262 linkage
│   │   ├── business-impact.yaml   # Financial/operational
│   │   ├── feasibility-assessment.yaml  # Attack feasibility
│   │   ├── risk-assessment.yaml   # Risk levels
│   │   ├── risk-matrix.png        # Visual risk matrix
│   │   └── prioritized-threats.md # Ranked threat list
│   ├── goals/
│   │   └── cybersecurity-goals.yaml  # Security goals
│   ├── controls/
│   │   ├── security-controls.yaml    # Selected controls
│   │   └── control-effectiveness.md  # Effectiveness analysis
│   ├── requirements/
│   │   └── security-requirements.yaml # Derived requirements
│   ├── tara-report.md           # Final TARA report
│   ├── tara-traceability.md     # Traceability matrix
│   └── tara-review-checklist.md # Review checklist
├── config/
│   └── security/
│       ├── classification-criteria.yaml  # Asset classification
│       ├── impact-criteria.yaml          # Impact scoring
│       ├── risk-matrix.yaml              # Risk calculation
│       └── acceptance-criteria.yaml      # Risk acceptance thresholds
├── data/
│   └── automotive-cves.json     # Automotive CVE database
├── templates/
│   └── tara-report.md           # TARA report template
├── tools/
│   ├── enumerate_assets.py      # Asset enumeration
│   ├── stride_analysis.py       # STRIDE analysis
│   ├── generate_attack_trees.py # Attack tree generation
│   ├── cve_cross_reference.py   # CVE mapping
│   ├── assess_safety_impact.py  # ISO 26262 linkage
│   ├── evaluate_feasibility.py  # Feasibility scoring
│   ├── calculate_risk.py        # Risk calculation
│   ├── select_controls.py       # Control selection
│   └── compile_tara_report.py   # Report generation
└── scripts/
    └── run-tara.sh              # Complete TARA workflow
```

## Prerequisites

1. **Hardware Requirements**:
   - x86_64 Linux workstation
   - 8 GB RAM minimum
   - 50 GB free disk space

2. **Software Requirements**:
   - Python 3.10+
   - Graphviz (for attack tree visualization)
   - pyyaml, graphviz, cvss Python packages

3. **Knowledge Requirements**:
   - ISO/SAE 21434 cybersecurity standard
   - STRIDE threat modeling methodology
   - SAE-J3061 cybersecurity guidebook
   - Basic understanding of automotive E/E architecture

## Architecture Documentation

### System Overview

```markdown
# System Architecture: Advanced Brake Control ECU

## Description
Electronic brake control system with ASIL-D safety classification,
featuring redundant sensor processing and fail-operative capability.

## Key Components
- Main MCU: Infineon TC397 (TriCore, 300 MHz, lockstep)
- Safety MCU: NXP S32K144 (ARM Cortex-M4, 112 MHz)
- Sensors: Wheel speed (4x), brake pressure (2x), pedal position (2x)
- Actuators: Hydraulic pump, valve bank (12 channels)
- Communication: CAN-FD (3 channels), Ethernet (1 channel)

## Safety Classification
- Overall system: ASIL D (ISO 26262)
- Primary brake control: ASIL D
- Diagnostics: ASIL B
- Communication gateway: ASIL B
```

### Network Topology

```markdown
# Network Topology

## CAN Buses
- Powertrain CAN (500 kbps): Engine, transmission, brake ECU
- Chassis CAN (500 kbps): Suspension, steering, brake ECU
- Body CAN (500 kbps): Doors, lights, HVAC (isolated from safety)

## Ethernet
- Diagnostic Ethernet (100 Mbps): OBD-II, external diagnostic access
- ADAS Ethernet (1000 Mbps): Camera, radar, sensor fusion (isolated)

## Gateway Architecture
                    +-------------------+
                    |   Central Gateway |
        +-----------+   (Firewall + IDS)|-----------+
        |           +-------------------+           |
+-------v------+                           +-------v-------+
| Safety Zone  |                           | Body Zone     |
| - Powertrain |                           | - Infotainment|
| - Chassis    |                           | - Telematics  |
| - Brakes     |                           | - OBD-II      |
+--------------+                           +---------------+

Trust boundary: Gateway enforces strict message filtering
```

### Trust Boundaries

```markdown
# Trust Boundaries

## Trust Boundary 1: Vehicle Exterior Interface
- Crossing: OBD-II port, cellular modem, Wi-Fi, Bluetooth
- Threats: Remote exploitation, physical access attacks
- Controls: Firewall, authentication, rate limiting

## Trust Boundary 2: Network Zone Boundary
- Crossing: Gateway ECU (CAN to CAN, Ethernet to CAN)
- Threats: Message injection, spoofing, lateral movement
- Controls: Message authentication (SecOC), whitelisting

## Trust Boundary 3: Safety Partition Boundary
- Crossing: MPU between ASIL-D and QM partitions
- Threats: Freedom from interference violations
- Controls: Memory protection, timing isolation

## Trust Boundary 4: Supply Chain Boundary
- Crossing: Tier 1 -> OEM integration
- Threats: Compromised firmware, counterfeit hardware
- Controls: Secure boot, supply chain verification
```

## Running the Demo

### Complete TARA Workflow

```bash
# Execute complete TARA analysis
./scripts/run-tara.sh \
  --architecture architecture/ \
  --output security/ \
  --config config/security/
```

### Individual Analysis Steps

```bash
# Step 1: Asset Identification
python tools/enumerate_assets.py \
  --architecture architecture/ \
  --output security/assets/ecu-inventory.yaml

python tools/identify_interfaces.py \
  --architecture architecture/ \
  --output security/assets/interfaces.yaml

python tools/catalog_data_assets.py \
  --architecture architecture/ \
  --output security/assets/data-assets.yaml

python tools/classify_assets.py \
  --assets security/assets/ \
  --criteria config/security/classification-criteria.yaml \
  --output security/assets/classified-assets.yaml

python tools/map_data_flows.py \
  --assets security/assets/ \
  --architecture architecture/ \
  --output security/assets/data-flow-diagram.yaml

# Step 2: Threat Identification
python tools/stride_analysis.py \
  --assets security/assets/ \
  --data-flows security/assets/data-flow-diagram.yaml \
  --output security/threats/stride-catalog.yaml

python tools/cve_cross_reference.py \
  --assets security/assets/ \
  --cve-database data/automotive-cves.json \
  --output security/threats/cve-mapping.yaml

python tools/generate_attack_trees.py \
  --assets security/assets/classified-assets.yaml \
  --critical-only \
  --output security/threats/attack-trees/

# Step 3: Risk Assessment
python tools/assess_safety_impact.py \
  --threats security/threats/stride-catalog.yaml \
  --hara security/safety/hara-report.yaml \
  --output security/risks/safety-impact.yaml

python tools/assess_business_impact.py \
  --threats security/threats/stride-catalog.yaml \
  --criteria config/security/impact-criteria.yaml \
  --output security/risks/business-impact.yaml

python tools/evaluate_feasibility.py \
  --threats security/threats/stride-catalog.yaml \
  --methodology SAE-J3061 \
  --output security/risks/feasibility-assessment.yaml

python tools/calculate_risk.py \
  --impact security/risks/safety-impact.yaml \
  --feasibility security/risks/feasibility-assessment.yaml \
  --matrix config/security/risk-matrix.yaml \
  --output security/risks/risk-assessment.yaml

python tools/visualize_risk_matrix.py \
  --risks security/risks/risk-assessment.yaml \
  --output security/risks/risk-matrix.png

# Step 4: Risk Treatment
python tools/define_cybersecurity_goals.py \
  --risks security/risks/prioritized-threats.md \
  --unacceptable-threshold HIGH \
  --output security/goals/cybersecurity-goals.yaml

python tools/select_controls.py \
  --threats security/risks/prioritized-threats.md \
  --control-catalog data/security-controls.yaml \
  --output security/controls/security-controls.yaml

python tools/evaluate_residual_risk.py \
  --risks security/risks/risk-assessment.yaml \
  --controls security/controls/security-controls.yaml \
  --output security/risks/residual-risk.yaml

python tools/generate_security_requirements.py \
  --goals security/goals/cybersecurity-goals.yaml \
  --controls security/controls/security-controls.yaml \
  --output security/requirements/security-requirements.yaml

# Step 5: Documentation
python tools/compile_tara_report.py \
  --inputs security/ \
  --template templates/tara-report.md \
  --output security/tara-report.md

python tools/generate_traceability.py \
  --assets security/assets/ \
  --threats security/threats/ \
  --risks security/risks/ \
  --controls security/controls/ \
  --output security/tara-traceability.md
```

## Configuration

### Asset Classification Criteria

```yaml
# config/security/classification-criteria.yaml
cia_classification:
  confidentiality:
    levels:
      - name: PUBLIC
        description: "No impact from disclosure"
        examples: ["Marketing materials", "Public specifications"]

      - name: INTERNAL
        description: "Internal use only, low impact"
        examples: ["Internal procedures", "Meeting notes"]

      - name: CONFIDENTIAL
        description: "Competitive advantage, moderate impact"
        examples: ["Design documents", "Calibration data"]

      - name: RESTRICTED
        description: "High impact, safety/security critical"
        examples: ["Cryptographic keys", "Security architecture"]

  integrity:
    levels:
      - name: QM
        description: "No safety/security impact"
        examples: ["Infotainment settings", "Display themes"]

      - name: SAFETY_RELEVANT
        description: "Potential safety impact"
        examples: ["Sensor calibration", "Control parameters"]

      - name: SAFETY_CRITICAL
        description: "Direct safety impact, ASIL-related"
        examples: ["Brake control code", "Safety state machine"]

  availability:
    levels:
      - name: OPTIONAL
        description: "Service degradation acceptable"
        examples: ["Navigation updates", "Media streaming"]

      - name: REQUIRED
        description: "Required for normal operation"
        examples: ["CAN communication", "Sensor data"]

      - name: CRITICAL
        description: "Loss leads to unsafe state"
        examples: ["Brake control", "Steering control"]
```

### Risk Matrix Configuration

```yaml
# config/security/risk-matrix.yaml
risk_matrix:
  # Impact levels from safety + business assessment
  impact_levels:
    - name: NEGLIGIBLE
      safety_impact: "No safety impact"
      business_impact: "< $10K, no reputation impact"
      score: 1

    - name: MINOR
      safety_impact: "Minor injury possible (S1)"
      business_impact: "$10K-$100K, minor reputation"
      score: 2

    - name: MODERATE
      safety_impact: "Moderate injury (S2)"
      business_impact: "$100K-$1M, moderate reputation"
      score: 3

    - name: CRITICAL
      safety_impact: "Severe injury (S3)"
      business_impact: "$1M-$10M, significant reputation"
      score: 4

    - name: CATASTROPHIC
      safety_impact: "Fatal (S3)"
      business_impact: "> $10M, brand-damaging"
      score: 5

  # Feasibility levels per SAE-J3061
  feasibility_levels:
    - name: VERY_LOW
      description: "Requires sophisticated equipment, expert knowledge"
      score: 1

    - name: LOW
      description: "Requires specialized equipment, above-average skill"
      score: 2

    - name: MODERATE
      description: "Requires basic equipment, average skill"
      score: 3

    - name: HIGH
      description: "Minimal equipment, below-average skill"
      score: 4

    - name: VERY_HIGH
      description: "No equipment, script kiddie level"
      score: 5

  # Risk calculation: Risk = Impact × Feasibility
  risk_thresholds:
    LOW: "1-4"
    MEDIUM: "5-12"
    HIGH: "13-19"
    CRITICAL: "20-25"

  # Treatment strategy per risk level
  treatment_strategy:
    LOW: "Accept - no additional controls required"
    MEDIUM: "Mitigate - implement cost-effective controls"
    HIGH: "Mitigate - mandatory controls required"
    CRITICAL: "Avoid/Eliminate - redesign required"
```

## Asset Inventory Example

```yaml
# security/assets/ecu-inventory.yaml
ecu_inventory:
  - asset_id: ECU-001
    name: "Brake Control ECU"
    part_number: "BCU-2024-001"
    manufacturer: "OEM Internal"
    hw_version: "Rev C"
    sw_version: "v2.4.0"
    location: "Engine compartment"
    safety_classification: ASIL_D
    security_classification:
      confidentiality: CONFIDENTIAL
      integrity: SAFETY_CRITICAL
      availability: CRITICAL
    interfaces:
      - type: CAN
        name: "Powertrain CAN"
        pins: [6, 14]
      - type: CAN
        name: "Chassis CAN"
        pins: [3, 11]
      - type: Ethernet
        name: "Diagnostic Ethernet"
        pins: [8, 9]
      - type: Power
        voltage: "12V nominal"
        pins: [30, 31]
    internal_assets:
      - "Main MCU firmware"
      - "Calibration parameters"
      - "Cryptographic keys"
      - "Diagnostic trouble codes"

  - asset_id: ECU-002
    name: "Central Gateway ECU"
    part_number: "GW-2024-002"
    manufacturer: "OEM Internal"
    hw_version: "Rev B"
    sw_version: "v1.8.0"
    location: "Dashboard center"
    safety_classification: ASIL_B
    security_classification:
      confidentiality: CONFIDENTIAL
      integrity: SAFETY_CRITICAL
      availability: CRITICAL
    interfaces:
      - type: CAN
        count: 5
      - type: Ethernet
        count: 3
      - type: LIN
        count: 4
```

## Threat Catalog Example

```yaml
# security/threats/stride-catalog.yaml
threats:
  - threat_id: THR-001
    asset: ECU-001
    stride_category: SPOOFING
    description: "Attacker spoofs brake ECU identity on Powertrain CAN"
    attack_vector: "Connect to OBD-II port, transmit forged CAN messages"
    motivation: "Cause unintended braking, disable brakes"
    affected_interfaces: ["Powertrain CAN"]
    cwe_id: "CWE-347: Improper Verification of Cryptographic Signature"

  - threat_id: THR-002
    asset: ECU-001
    stride_category: TAMPERING
    description: "Attacker modifies firmware flash memory"
    attack_vector: "Physical access to debug interface (JTAG/SWD)"
    motivation: "Disable safety functions, install backdoor"
    affected_interfaces: ["Debug interface (production disabled)"]
    cwe_id: "CWE-754: Improper Check for Unusual or Exceptional Conditions"

  - threat_id: THR-003
    asset: ECU-002
    stride_category: INFORMATION_DISCLOSURE
    description: "Attacker eavesdrops on diagnostic session"
    attack_vector: "Monitor diagnostic CAN bus via OBD-II"
    motivation: "Extract sensitive vehicle data, calibration secrets"
    affected_interfaces: ["Diagnostic CAN"]
    cwe_id: "CWE-319: Cleartext Transmission of Sensitive Information"

  - threat_id: THR-004
    asset: ECU-002
    stride_category: DENIAL_OF_SERVICE
    description: "Flood gateway with high-priority CAN messages"
    attack_vector: "Transmit continuous CAN frames at max rate"
    motivation: "Disrupt safety-critical communication"
    affected_interfaces: ["All CAN interfaces"]
    cwe_id: "CWE-770: Allocation of Resources Without Limits or Throttling"
```

## Attack Tree Example

```yaml
# security/threats/attack-trees/firmware-tamper.yaml
attack_tree:
  root:
    goal: "Tamper with brake ECU firmware"
    type: OR
    children:
      - goal: "Gain physical access to ECU"
        type: AND
        children:
          - goal: "Locate brake ECU in vehicle"
            type: LEAF
            feasibility: VERY_HIGH
            mitigations: ["ECU location not publicly documented"]

          - goal: "Access ECU enclosure"
            type: LEAF
            feasibility: MODERATE
            mitigations: ["Tamper-evident seals", "Secure mounting"]

      - goal: "Bypass secure boot"
        type: AND
        children:
          - goal: "Extract signing key"
            type: OR
            children:
              - goal: "Side-channel attack on HSM"
                type: LEAF
                feasibility: VERY_LOW
                mitigations: ["FIPS 140-2 Level 3 HSM", "Shielding"]

              - goal: "Social engineering attack on OEM"
                type: LEAF
                feasibility: LOW
                mitigations: ["Key management procedures", "Dual custody"]

          - goal: "Sign malicious firmware"
            type: LEAF
            feasibility: LOW
            mitigations: ["HSM key never exported", "Offline signing"]

      - goal: "Exploit debug interface"
        type: OR
        children:
          - goal: "Enable JTAG/SWD access"
            type: LEAF
            feasibility: LOW
            mitigations: ["Debug disabled in production fuses"]

          - goal: "Fault injection attack"
            type: LEAF
            feasibility: VERY_LOW
            mitigations: ["Glitch detection", "Voltage monitoring"]
```

## Risk Assessment Results

```yaml
# security/risks/risk-assessment.yaml
risk_assessment:
  - threat_id: THR-001
    impact_analysis:
      safety_impact: CATASTROPHIC  # ASIL-D system compromise
      safety_rationale: "Brake ECU spoofing could cause unintended braking at highway speeds"
      business_impact: CRITICAL
      business_rationale: "Recall cost > $10M, brand reputation damage"
      overall_impact_score: 5

    feasibility_analysis:
      attack_feasibility: HIGH  # CAN spoofing is well-documented
      required_expertise: "Automotive CAN knowledge, basic electronics"
      required_equipment: "CAN interface device ($200), laptop"
      window_of_opportunity: "Physical access to OBD-II port"
      overall_feasibility_score: 4

    risk_level: CRITICAL  # 5 × 4 = 20
    risk_score: 20

    treatment_required: true
    treatment_priority: 1  # Highest priority

  - threat_id: THR-004
    impact_analysis:
      safety_impact: CRITICAL  # DoS on safety bus
      safety_rationale: "Could prevent brake ECU from receiving critical messages"
      business_impact: MODERATE
      business_rationale: "Warranty claims, potential recall"
      overall_impact_score: 4

    feasibility_analysis:
      attack_feasibility: VERY_HIGH  # Simple flooding attack
      required_expertise: "Basic CAN knowledge"
      required_equipment: "Any CAN device"
      window_of_opportunity: "Physical access to OBD-II"
      overall_feasibility_score: 5

    risk_level: CRITICAL  # 4 × 5 = 20
    risk_score: 20

    treatment_required: true
    treatment_priority: 1
```

## Security Controls

```yaml
# security/controls/security-controls.yaml
security_controls:
  - control_id: CTRL-001
    name: "SecOC Message Authentication"
    standard: "AUTOSAR SecOC"
    description: "Implement CAN message authentication using truncated MAC"
    mitigates_threats: [THR-001, THR-004]
    implementation:
      algorithm: "AES-128-CMAC truncated to 32 bits"
      freshness: "32-bit rolling counter"
      key_management: "HSM-managed session keys"
    effectiveness:
      residual_feasibility: MODERATE  # Reduced from HIGH
      coverage: 95%
    cost_estimate: "2 developer-weeks"
    asil_impact: None (QM component)

  - control_id: CTRL-002
    name: "Secure Boot Chain"
    standard: "ISO 21434 15.4.2"
    description: "Verify firmware signature at boot and runtime"
    mitigates_threats: [THR-002]
    implementation:
      algorithm: "ECDSA P-256"
      root_of_trust: "HSM embedded root key"
      verification: "Boot ROM -> Bootloader -> Application"
    effectiveness:
      residual_feasibility: VERY_LOW  # Reduced from LOW
      coverage: 99%
    cost_estimate: "3 developer-weeks"
    asil_impact: Supports ASIL-D safety mechanism

  - control_id: CTRL-003
    name: "Diagnostic Authentication"
    standard: "UDS ISO 14229-1 + SecAccess"
    description: "Require challenge-response authentication for protected services"
    mitigates_threats: [THR-003]
    implementation:
      algorithm: "HMAC-SHA256"
      seed_key_length: "32 bytes"
      lockout_policy: "3 attempts, 10-minute lockout"
    effectiveness:
      residual_feasibility: MODERATE  # Reduced from HIGH
      coverage: 90%
    cost_estimate: "1 developer-week"
    asil_impact: ASIL-B
```

## Using MCP Tools

This demo leverages the following MCP tools:

```bash
# Run TARA analysis workflow
security:tara-analyze --architecture architecture/ --output security/

# Scan for vulnerabilities
security:vuln-scan --target ECU-001 --methodology cvss

# Audit cryptographic implementation
security:crypto-audit --target security/

# Generate security bill of materials
security:sbom-generate --input src/ --output security/sbom.json

# Manage certificates
security:certificate-manage --action list --store vehicle
```

## Expected Results

After successful execution, you'll find:

```
security/
├── assets/
│   ├── classified-assets.yaml     # 45 assets classified
│   └── dependency-map.md          # Asset dependency graph
├── threats/
│   ├── stride-catalog.yaml        # 127 threats identified
│   ├── attack-trees/              # 8 attack trees generated
│   └── threat-catalog.md          # Consolidated catalog
├── risks/
│   ├── risk-assessment.yaml       # Risk levels calculated
│   ├── risk-matrix.png            # 5×5 risk matrix
│   └── prioritized-threats.md     # Ranked by risk score
├── goals/
│   └── cybersecurity-goals.yaml   # 15 cybersecurity goals
├── controls/
│   └── security-controls.yaml     # 23 security controls
├── requirements/
│   └── security-requirements.yaml # 45 security requirements
├── tara-report.md                 # 85-page TARA report
└── tara-traceability.md           # Full traceability matrix
```

### Risk Summary

| Risk Level | Count | Percentage |
|------------|-------|------------|
| CRITICAL | 8 | 6% |
| HIGH | 24 | 19% |
| MEDIUM | 52 | 41% |
| LOW | 43 | 34% |

### Top 5 Prioritized Threats

1. **THR-001**: Brake ECU spoofing (CRITICAL, score 20)
2. **THR-004**: Gateway CAN flooding (CRITICAL, score 20)
3. **THR-002**: Firmware tampering (CRITICAL, score 16)
4. **THR-015**: Key extraction via debug (CRITICAL, score 15)
5. **THR-008**: V2X message replay (HIGH, score 12)

## Troubleshooting

### Common Issues

1. **Asset inventory incomplete**
   - Review architecture documentation for missing components
   - Interview system architects for undocumented interfaces
   - Check ECU extraction from system description

2. **Attack trees too complex**
   - Focus on high-risk assets first (ASIL-D, security-critical)
   - Use abstraction levels (strategic vs. tactical)
   - Limit depth to 5 levels maximum

3. **Risk scores seem inflated**
   - Review feasibility scoring criteria
   - Consider existing mitigations in feasibility assessment
   - Calibrate with historical incident data

### Getting Help

- Review ISO/SAE 21434 Part 3 (Concept phase)
- Check SAE-J3061 Cybersecurity Guidebook
- Consult NIST Cybersecurity Framework for automotive
- Review UNECE R155 CSMS requirements

## Next Steps

After successful demo execution:

1. Review TARA report with cybersecurity team
2. Complete review checklist with stakeholders
3. Create GitHub issue for high-priority threat mitigation
4. Update security requirements in system design
5. Plan security control implementation sprints

## References

- [Security TARA Analysis Workflow](../../.github/workflows/security-tara.yaml)
- [ISO/SAE 21434 Standard](../../knowledge-base/standards/iso-21434/)
- [SAE-J3061 Cybersecurity Guidebook](../../knowledge-base/standards/sae-j3061/)
- [UNECE R155 CSMS Requirements](../../knowledge-base/regulations/unece-r155/)
- [NIST Cybersecurity Framework](../../knowledge-base/frameworks/nist-csf/)
