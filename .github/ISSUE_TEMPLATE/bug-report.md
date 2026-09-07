---
name: Bug Report
about: Report a bug in the code, tools, wrappers, or build system
title: "[Bug]: [short description]"
labels: bug
assignees: ""
---

## Bug Description

[Clear and concise description of the bug.]

## Component

Which part of the project is affected?

- [ ] `schema.json` — Schema validation
- [ ] `tools/validate.py` — Validator
- [ ] `tools/build.py` — Build script
- [ ] `tools/generate_dates.py` — Recurrence engine
- [ ] Python wrapper (`wrappers/python/`)
- [ ] JavaScript wrapper (`wrappers/javascript/`)
- [ ] TypeScript definitions (`wrappers/javascript/src/index.d.ts`)
- [ ] Go wrapper (`wrappers/go/`)
- [ ] Rust wrapper (`wrappers/rust/`)
- [ ] Tests (`tests/`)
- [ ] CI workflow (`.github/workflows/`)
- [ ] Documentation
- [ ] Other: [specify]

## Environment

- **OS:** [e.g., Ubuntu 24.04, macOS 15, Windows 11]
- **Python version:** [e.g., 3.12.3] (if applicable)
- **Node.js version:** [e.g., 20.11.0] (if applicable)
- **Go version:** [e.g., 1.21.5] (if applicable)
- **Rust version:** [e.g., 1.97.1] (if applicable)
- **Project version/commit:** [e.g., v2.0.0, commit hash]

## Steps to Reproduce

1. [First step]
2. [Second step]
3. [Third step]

## Expected Behavior

[What should happen.]

## Actual Behavior

[What actually happens — include error messages, stack traces, or screenshots.]

## Severity

- [ ] **Critical** — data corruption, wrong holiday dates, wrong market status
- [ ] **High** — validator fails, build fails, tests fail
- [ ] **Medium** — wrapper API inconsistency, error handling issue
- [ ] **Low** — documentation error, cosmetic issue

## Checklist

- [ ] I have searched existing issues for this bug
- [ ] I can reproduce this bug consistently
- [ ] I have provided the full error output
- [ ] I have provided a minimal reproduction
- [ ] I have identified the affected component
