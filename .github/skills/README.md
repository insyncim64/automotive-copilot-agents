# Reusable Copilot Skills

This directory contains reusable Copilot skill packages converted from source domain notes in `.github/copilot/context/skills/`.

## Structure

- One folder per topic: `.github/skills/<domain>-<topic>/`
- Required skill entry file: `SKILL.md`

## Source Mapping Pattern

- Source: `.github/copilot/context/skills/<domain>/<topic>.md`
- Converted: `.github/skills/<domain>-<topic>/SKILL.md`

## Notes

- Converted files include frontmatter with `name` and `description` for skill discovery.
- Original source files are retained and unchanged.

## Regeneration

Use the repository conversion script to regenerate reusable skills and instructions:

```powershell
./scripts/convert_copilot_customizations.ps1
```

Optional modes:

```powershell
./scripts/convert_copilot_customizations.ps1 -SkillsOnly
./scripts/convert_copilot_customizations.ps1 -InstructionsOnly
```
