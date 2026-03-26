---
name: safety-asil-decomposition
description: "Use when: Skill: ASIL Decomposition and Dependency Analysis topics are needed for automotive embedded and systems engineering tasks."
---
# Skill: ASIL Decomposition and Dependency Analysis

## Skill Intent
- Reusable Copilot skill converted from context source: .github/copilot/context/skills/safety/asil-decomposition.md
- Apply this skill when domain-specific design, implementation, safety, diagnostics, or validation guidance is requested.

## Guidance
## Standards Compliance

- ISO 26262 ASIL C/D
- ASPICE Level 3
- AUTOSAR 4.4
- ISO 21434

## Core Competencies

Expert in ASIL decomposition and dependent failure analysis for automotive safety systems.

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Valid decomposition schemes | D→D+D, D→C+A, D→B+B, C→B+A, B→A+A | Per ISO 26262 Part 9 |
| Independence requirement | Freedom from common cause failures | DFA mandatory |
| Diagnostic coverage targets | ASIL B: ≥90%, ASIL C: ≥97%, ASIL D: ≥99% | Single-point fault metric |
| Latent fault targets | ASIL B: ≥60%, ASIL C: ≥80%, ASIL D: ≥90% | Latent fault metric |

## Domain-Specific Content

### ASIL Decomposition Rules

**Valid Decomposition Combinations:**

| Original ASIL | Element 1 | Element 2 | Element 3 |
|--------------|-----------|-----------|-----------|
| ASIL D | ASIL D(D) | ASIL D(D) | N/A |
| ASIL D | ASIL C(D) | ASIL A(D) | N/A |
| ASIL D | ASIL B(D) | ASIL B(D) | N/A |
| ASIL D | ASIL B(D) | ASIL A(D) | ASIL A(D) |
| ASIL C | ASIL C(C) | ASIL C(C) | N/A |
| ASIL C | ASIL B(C) | ASIL A(C) | N/A |
| ASIL B | ASIL B(B) | ASIL B(B) | N/A |
| ASIL B | ASIL A(B) | ASIL A(B) | N/A |

**Notation**: ASIL X(Y) = developed to ASIL X, contributing to ASIL Y decomposition

### Independence Requirements

For ASIL decomposition to be valid, elements must be **sufficiently independent**:

1. **Hardware Independence**
   - Separate processors or cores
   - Separate sensors (different physical principle preferred)
   - Separate power supplies
   - Separate communication paths
   - Independent clock sources

2. **Software Independence**
   - No shared source code
   - No shared libraries (including RTOS, HAL, math libraries)
   - Different compilers or compiler versions (recommended for ASIL D)
   - Independent build pipelines
   - No shared configuration files

3. **Process Independence**
   - Different development teams (recommended for ASIL D)
   - Independent reviews
   - Independent testing
   - Diverse algorithms (recommended)

### Dependent Failure Analysis (DFA) Process

```
Step 1: Identify decomposed elements and interfaces
        ↓
Step 2: Analyze Common Cause Failures (CCF)
        ↓
Step 3: Analyze Cascading Failures (CF)
        ↓
Step 4: Determine independence measures
        ↓
Step 5: Verify residual risk is acceptable
        ↓
Step 6: Document in DFA report
```

### Common Cause Failure Categories

| Category | Description | Example |
|----------|-------------|---------|
| Hardware CCF | Shared physical components | Same power supply, PCB |
| Software CCF | Shared code or libraries | Same RTOS, compiler |
| Environmental CCF | Shared environment | Temperature, EMI |
| Process CCF | Same development process | Same team, tools |
| Systematic CCF | Same design methodology | Same algorithm approach |

### Architectural Patterns

**Redundant Monitor Pattern:**

```
+------------------+     +------------------+
|  Primary Path    |     |  Monitor Path    |
|  (ASIL B(D))     |     |  (ASIL B(D))     |
|                  |     |                  |
|  Sensor A ------>|     |  Sensor B ------>|
|  Algorithm 1 --->|     |  Algorithm 2 --->|
|  Output 1 ------>+--+--+<------ Output 2  |
                      |
                 Comparator
                      |
              +-------+-------+
              | Outputs agree? |
              +-------+-------+
                  |       |
                 YES      NO
                  |       |
              Execute   Safe State
              Command   (Fail-safe)
```

## Implementation Approach

1. Analyze requirements against automotive standards
2. Design solution following AUTOSAR patterns
3. Implement with safety and security considerations
4. Validate per ISO 26262 requirements

## Deliverables

- Technical specification
- Implementation (C/C++/Model)
- Test cases and results
- Safety documentation

## Constraints

- ISO 26262 functional safety compliance
- Real-time performance requirements
- Resource constraints (CPU/Memory)
- AUTOSAR architecture adherence

## Required Tools

- MATLAB/Simulink
- Vector CANoe/CANalyzer
- Static analyzer (Polyspace/Klocwork)
- AUTOSAR toolchain

## Metadata

- **Author**: Automotive Claude Code Agents
- **Last Updated**: 2026-03-19
- **Maturity**: Production
- **Complexity**: Intermediate

## Related Context

- @context/skills/safety/iso-26262-overview.md
- @context/skills/safety/fmea.md
- @context/skills/safety/fta.md
- @context/skills/autosar/classic-platform.md