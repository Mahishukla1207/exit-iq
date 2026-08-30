import numpy as np
import pandas as pd
from typing import Tuple


def generate_synthetic_crowd_dataset(num_samples: int = 2500, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates a realistic synthetic dataset of crowd dynamics in an emergency evacuation setting.
    Features:
    - current_density (people / m^2): [0.1, 4.5]
    - density_change_rate (change per min): [-1.5, 2.5]
    - people_inflow (people / sec): [0, 15]
    - people_outflow (people / sec): [0, 12]
    - avg_movement_speed (m/s): [0.2, 1.8] (inversely proportional to density)
    - nearby_zone_density (people / m^2): [0.1, 4.0]
    - exit_proximity (meters): [5.0, 60.0]
    - current_hazard_severity: [0.0, 1.0]

    Target:
    - future_congestion_prob: Probability [0.0, 1.0] of zone becoming bottleneck/congested in T+60s.
    - future_density_1m: Estimated crowd density in 1 minute.
    """
    np.random.seed(random_seed)

    current_density = np.random.uniform(0.1, 4.5, num_samples)
    density_change_rate = np.random.uniform(-1.2, 2.2, num_samples)
    people_inflow = np.random.uniform(0.0, 12.0, num_samples)
    people_outflow = np.random.uniform(0.0, 10.0, num_samples)
    
    # Speed drops as density increases (fundamental diagram of crowd dynamics)
    avg_movement_speed = np.clip(1.4 - 0.28 * current_density + np.random.normal(0, 0.08, num_samples), 0.15, 1.8)
    
    nearby_zone_density = np.random.uniform(0.1, 4.0, num_samples)
    exit_proximity = np.random.uniform(5.0, 65.0, num_samples)
    current_hazard_severity = np.random.uniform(0.0, 1.0, num_samples)

    # Future density physics approximation:
    # Future = Current + Change + (Inflow - Outflow)*0.1 + Nearby Spillover - Speed Factor
    net_inflow_factor = (people_inflow - people_outflow) * 0.08
    spillover_factor = nearby_zone_density * 0.15
    hazard_panic_surge = current_hazard_severity * 0.4
    
    future_density_1m = np.clip(
        current_density + density_change_rate * 0.6 + net_inflow_factor + spillover_factor + hazard_panic_surge,
        0.0,
        5.0
    )

    # Congestion probability threshold: > 2.5 people/m^2 constitutes bottleneck
    future_congestion_prob = 1.0 / (1.0 + np.exp(-3.0 * (future_density_1m - 2.2)))

    df = pd.DataFrame({
        "current_density": np.round(current_density, 3),
        "density_change_rate": np.round(density_change_rate, 3),
        "people_inflow": np.round(people_inflow, 2),
        "people_outflow": np.round(people_outflow, 2),
        "avg_movement_speed": np.round(avg_movement_speed, 3),
        "nearby_zone_density": np.round(nearby_zone_density, 3),
        "exit_proximity": np.round(exit_proximity, 1),
        "hazard_severity": np.round(current_hazard_severity, 2),
        "future_density_1m": np.round(future_density_1m, 3),
        "future_congestion_prob": np.round(future_congestion_prob, 3),
    })

    return df


if __name__ == "__main__":
    df = generate_synthetic_crowd_dataset(100)
    print(f"Synthetic dataset generated with {len(df)} rows:")
    print(df.head())
