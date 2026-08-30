# ExitIQ REST API Documentation

Base URL: `http://localhost:8000/api/v1`

---

## Endpoints Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server status check |
| `GET` | `/api/v1/simulation/state` | Returns full simulation graph, nodes, hazards, predictions & metrics |
| `POST` | `/api/v1/simulation/start` | Starts real-time simulation clock |
| `POST` | `/api/v1/simulation/pause` | Pauses simulation clock |
| `POST` | `/api/v1/simulation/reset` | Resets floor map to default clean state |
| `POST` | `/api/v1/simulation/scenario/{name}` | Loads preset scenario (1-6) |
| `POST` | `/api/v1/simulation/hazard` | Injects environmental hazard (fire/smoke/obstacle) |
| `DELETE` | `/api/v1/simulation/hazard/{id}` | Clears active hazard by ID |
| `POST` | `/api/v1/simulation/crowd` | Updates zone crowd density |
| `POST` | `/api/v1/simulation/edge/block` | Toggles corridor blockage state |
| `GET` | `/api/v1/route` | Returns currently calculated safest evacuation route |
| `POST` | `/api/v1/route/recalculate` | Forces recalculation of evacuation route with optional weight overrides |
| `GET` | `/api/v1/prediction` | Returns LightGBM zone congestion forecasts |
| `GET` | `/api/v1/risk-map` | Returns dynamic edge risk metrics |
