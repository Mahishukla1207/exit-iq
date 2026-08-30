import time
import numpy as np
import pandas as pd
from typing import Dict, List, Any

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from app.prediction.synthetic_generator import generate_synthetic_crowd_dataset

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False


class MLBenchmarkSuite:
    """
    ML Model Comparison & Benchmark Suite.
    Evaluates LightGBM, XGBoost / GradientBoosting, RandomForest, and Ridge Regression
    on crowd evacuation congestion metrics.
    """

    FEATURE_COLUMNS = [
        "current_density",
        "density_change_rate",
        "people_inflow",
        "people_outflow",
        "avg_movement_speed",
        "nearby_zone_density",
        "exit_proximity",
        "hazard_severity",
    ]

    def run_benchmark(self, num_samples: int = 2500) -> Dict[str, Any]:
        """Runs full comparative benchmark across candidate models."""
        df = generate_synthetic_crowd_dataset(num_samples=num_samples, random_seed=42)

        X = df[self.FEATURE_COLUMNS]
        y = df["future_congestion_prob"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

        models = {}

        # 1. LightGBM
        if HAS_LIGHTGBM:
            models["LightGBM"] = lgb.LGBMRegressor(
                objective="regression", n_estimators=100, learning_rate=0.05, num_leaves=31, random_state=42, verbosity=-1
            )
        else:
            models["LightGBM (Simulated)"] = GradientBoostingRegressor(n_estimators=80, random_state=42)

        # 2. XGBoost / Gradient Boosting
        if HAS_XGBOOST:
            models["XGBoost"] = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=6, random_state=42)
        else:
            models["GradientBoosting (XGB Alt)"] = GradientBoostingRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42)

        # 3. RandomForest
        models["RandomForest"] = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)

        # 4. Ridge Regression Baseline
        models["Ridge Baseline"] = Ridge(alpha=1.0)

        results = []

        for name, model in models.items():
            t0 = time.time()
            model.fit(X_train, y_train)
            train_time = round((time.time() - t0) * 1000, 2)

            t0 = time.time()
            preds = model.predict(X_test)
            inference_time_us = round(((time.time() - t0) / len(X_test)) * 1e6, 2)

            mae = round(float(mean_absolute_error(y_test, preds)), 4)
            rmse = round(float(np.sqrt(mean_squared_error(y_test, preds))), 4)
            r2 = round(float(r2_score(y_test, preds)), 4)

            results.append({
                "model_name": name,
                "mae": mae,
                "rmse": rmse,
                "r2_score": r2,
                "train_time_ms": train_time,
                "inference_latency_us": inference_time_us,
                "is_recommended": "LightGBM" in name,
            })

        results.sort(key=lambda r: r["mae"])

        return {
            "num_test_samples": len(X_test),
            "benchmark_timestamp": time.time(),
            "target_variable": "future_congestion_prob",
            "models_evaluated": results,
            "best_model": results[0]["model_name"],
        }


if __name__ == "__main__":
    suite = MLBenchmarkSuite()
    print(suite.run_benchmark())
