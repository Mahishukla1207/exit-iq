# ExitIQ Methodology & Mathematics

## 1. Dynamic Risk Cost Function

Each corridor edge $e = (u, v)$ in the evacuation graph is assigned a dynamic risk cost:

$$\text{Cost}(e) = \text{distance}(e) \cdot \left[ 1.0 + w_{\text{hazard}} \cdot R_{\text{hazard}}(e) + w_{\text{crowd}} \cdot R_{\text{crowd}}(e) + w_{\text{pred}} \cdot R_{\text{pred}}(e) \right]$$

Where:
- $R_{\text{hazard}}(e) \in [0.0, 1.0]$: Maximum severity of active fire/smoke/debris affecting edge $e$. Fire has a $1.0$ multiplier, Smoke has a $0.6$ multiplier. If $R_{\text{hazard}} \ge 0.90$, cost is set to $\infty$ (impassable).
- $R_{\text{crowd}}(e) \in [0.0, 1.0]$: Scaled crowd density $\min\left(1.0, \frac{\text{density}}{3.5}\right)$.
- $R_{\text{pred}}(e) \in [0.0, 1.0]$: LightGBM near-future predicted congestion probability at $T+60\text{s}$.
- Default Configurable Weights: $w_{\text{hazard}} = 5.0$, $w_{\text{crowd}} = 2.5$, $w_{\text{pred}} = 3.0$, $w_{\text{distance}} = 1.0$.

## 2. Weighted Risk-Aware A* Algorithm

Standard A* evaluates $f(n) = g(n) + h(n)$. In ExitIQ:
- $g(n)$: Accumulated dynamic risk traversal cost from the start assembly location to node $n$.
- $h(n)$: Euclidean distance heuristic to target exit:
  $$h(n) = \sqrt{(x_n - x_{\text{exit}})^2 + (y_n - y_{\text{exit}})^2}$$

The pathfinder evaluates all active emergency exits and selects the exit and path that minimizes $f(n^*)$.

## 3. LightGBM Near-Future Congestion Predictor

The prediction engine forecasts whether crowd density in zone $z$ will reach bottleneck levels ($>2.5 \text{ people/m}^2$) within 60 seconds.

Features utilized:
1. `current_density`: People per square meter
2. `density_change_rate`: Density gradient per minute
3. `people_inflow`: Inflow rate (people/sec)
4. `people_outflow`: Outflow rate (people/sec)
5. `avg_movement_speed`: Crowd movement velocity (m/s)
6. `nearby_zone_density`: Spillover density from adjacent zones
7. `exit_proximity`: Distance to nearest exit
8. `hazard_severity`: Hazard severity in zone

Model architecture: `LightGBM Regressor` trained on synthetic crowd evacuation dynamics dataset (3,000 samples).
