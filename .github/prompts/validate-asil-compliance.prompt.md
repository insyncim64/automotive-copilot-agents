---
mode: ask
description: "Validate implementation and requirements against ISO 26262 ASIL expectations"
---
Perform an ISO 26262-oriented compliance review for the provided requirements/design/code/test artifacts.

Inputs:
- ASIL target (A/B/C/D)
- Safety goals and technical safety requirements
- Architecture and software design excerpts
- Test evidence (unit, integration, HiL/vehicle)
- Diagnostic and fault-handling behavior

Review output:
- Non-conformities ordered by severity (with rationale)
- Missing safety mechanisms (monitoring, plausibility, watchdog, safe state)
- Gaps in traceability from safety goals to verification artifacts
- Recommended corrective actions with implementation priority
- Required additional test scenarios and acceptance criteria

Rules:
- Focus on actionable engineering feedback
- Distinguish assumptions from verified evidence
- Keep recommendations implementable for embedded ECU constraints
