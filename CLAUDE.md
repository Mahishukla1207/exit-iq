# ExitIQ Local Development Guide

This repository uses the native ExitIQ stack only.

- Do not use, reference, or depend on the RocketRide engine or RocketRide SDK.
- Keep all work aligned with the project architecture in this repo.
- Backend logic lives under the Python FastAPI app in backend/.
- Frontend logic lives under the React + Vite app in frontend/.
- Use the project README and the existing tests as the source of truth for behavior.

## Working rules

1. Prefer the existing ExitIQ backend, routing, risk, and simulation modules.
2. Keep feature work scoped to the real project architecture rather than external pipeline tooling.
3. Validate changes with the relevant tests before considering them complete.
4. For demo or simulation work, use the built-in simulation engine and scenario flow already implemented in the app.

## Notes

RocketRide is intentionally not part of this project and should not be introduced into development, prompts, or instructions.

<!-- ROCKETRIDE:BEGIN -->

# RocketRide: AI Pipeline Builder

Use RocketRide when building AI pipelines, document processing, RAG systems, or data integration.

## Documentation

Full docs: `.rocketride/docs/`

**Read the relevant doc(s) before generating any RocketRide code.**

| File                              | Read when...                                                      |
| --------------------------------- | ----------------------------------------------------------------- |
| ROCKETRIDE_README.md              | Starting any RocketRide work: overview + mandatory setup steps   |
| ROCKETRIDE_QUICKSTART.md          | Writing first pipeline: complete working examples (Python & TS)  |
| ROCKETRIDE_PIPELINE_RULES.md      | Defining pipelines: structure, lane wiring, config rules         |
| ROCKETRIDE_COMPONENT_REFERENCE.md | Choosing/configuring components: all providers and config fields |
| ROCKETRIDE_COMMON_MISTAKES.md     | Before finalizing: known pitfalls to avoid                       |
| ROCKETRIDE_python_API.md          | Python SDK: client methods, types, patterns                      |
| ROCKETRIDE_typescript_API.md      | TypeScript SDK: client methods, types, patterns                  |
| ROCKETRIDE_OBSERVABILITY.md       | Consuming runtime logs, lifecycle events, and pipeline traces     |

## Before Writing ANY RocketRide Code

1. Read `.rocketride/docs/ROCKETRIDE_README.md` for mandatory setup requirements
2. Read the relevant API doc (Python or TypeScript) for your language
3. Read `.rocketride/docs/ROCKETRIDE_PIPELINE_RULES.md` + `.rocketride/docs/ROCKETRIDE_COMPONENT_REFERENCE.md`
4. Read `.rocketride/docs/ROCKETRIDE_COMMON_MISTAKES.md` before finalizing
<!-- ROCKETRIDE:END -->
