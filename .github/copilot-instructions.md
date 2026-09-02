# ExitIQ Local Development Guide

This repository uses the native ExitIQ stack only.

- Keep all work aligned with the project architecture in this repo.
- Backend logic lives under the Python FastAPI app in backend/.
- Frontend logic lives under the React + Vite app in frontend/.
- Use the project README and the existing tests as the source of truth for behavior.

## Working rules

1. Prefer the existing ExitIQ backend, routing, risk, and simulation modules.
2. Keep feature work scoped to the real project architecture rather than external pipeline tooling.
3. Validate changes with the relevant tests before considering them complete.
4. For demo or simulation work, use the built-in simulation engine and scenario flow already implemented in the app.

