# Automotive Copilot Workspace Instructions

This workspace contains automotive requirements engineering assets, embedded-system implementation details, and verification workflows.

## Scope

Use this workspace guidance for:
- automotive systems engineering
- C/C++ and embedded implementation guidance
- AUTOSAR, diagnostics, networking, and safety-aligned recommendations
- requirement traceability and signal-level analysis

## Instruction Discovery

File-scoped instruction files are available under `.github/instructions/`.
Reusable agent profiles are available under `.github/agents/`.
Choose instruction context that best matches user intent, domain, and artifact type.

## Context And Knowledge Usage

When domain context is required, prioritize:
- `.github/copilot/context/CONTEXT-REFERENCE.md`
- `.github/copilot/context/adas/`
- `.github/copilot/context/skills/`
- `.github/copilot/knowledge/INDEX.md`
- `.github/copilot/knowledge/KNOWLEDGE-INDEX.md`

Use these sources to ground responses in automotive standards, architecture, safety, and validation workflows.

## Engineering Priorities

- keep outputs production-oriented and testable
- prioritize safety, diagnostics, and robustness
- align recommendations with embedded constraints (timing, memory, determinism)
- preserve requirement traceability when proposing implementation changes
