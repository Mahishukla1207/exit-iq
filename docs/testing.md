# ExitIQ Automated Testing Guide

ExitIQ features an automated test suite powered by `pytest`.

## Running Backend Tests

```bash
python -m pytest backend/tests -v
```

## Scenario Test Coverage

1. **Scenario 1: Normal Evacuation**
   - Asserts shortest safe path is selected when zero hazards are active.
2. **Scenario 2: Fire Corridor Avoidance**
   - Injects fire in North Corridor; verifies A* automatically avoids `node_north_hall` and redirects to alternate safe corridor.
3. **Scenario 3: Exit Congestion**
   - Increases density in West Gate (Exit A) to 4.2 p/m²; asserts system selects Exit B, C, or D.
4. **Scenario 4: Predictive Congestion (LightGBM)**
   - Simulates high inflow rate triggering LightGBM prediction surge; verifies explainability rationale explicitly references forecast.
5. **Scenario 5: Multi-Hazard Escalation**
   - Combines fire in North + smoke in West; asserts path finding resolves safe remaining path.
6. **Scenario 6: All Exits Blocked**
   - Blocks all evacuation corridors; verifies system returns `is_safe: false` and displays "NO SAFE EVACUATION ROUTE AVAILABLE" rather than hallucinating an impassable path.
