import os
import pickle
import numpy as np
import pandas as pd

try:
    import lightgbm as lgb
    HAS_LIGHTGBM = True
except ImportError:
    HAS_LIGHTGBM = False

from typing import Dict, Any, Optional
from app.prediction.synthetic_generator import generate_synthetic_crowd_dataset
from app.models.schemas import ZoneCrowd, CongestionPrediction, Hazard

# Canonical models directory under backend/models/
CANONICAL_MODEL_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "models")
)


class LightGBMPredictor:
    """
    LightGBM Near-Future Congestion Predictor.
    Estimates crowd congestion probability for zone nodes T+60s into the future.
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

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = model_dir or CANONICAL_MODEL_DIR
        self.model_path = os.path.join(self.model_dir, "lightgbm_congestion_model.pkl")
        self.model = None
        self.is_trained = False
        self._initialize_model()

    def _initialize_model(self):
        """Loads serialized LightGBM model or trains baseline model if missing."""
        if os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                self.is_trained = True
                return
            except Exception as e:
                print(f"[LightGBM] Failed to load model file: {e}")

        # Train baseline LightGBM model on synthetic dataset
        self.train_baseline_model()

    def train_baseline_model(self):
        """Trains LightGBM model on synthetic crowd evacuation dataset."""
        df = generate_synthetic_crowd_dataset(num_samples=3000)

        X = df[self.FEATURE_COLUMNS]
        y = df["future_congestion_prob"]

        if HAS_LIGHTGBM:
            params = {
                "objective": "regression",
                "metric": "rmse",
                "learning_rate": 0.05,
                "num_leaves": 31,
                "verbosity": -1,
                "n_estimators": 100,
                "random_state": 42,
            }
            self.model = lgb.LGBMRegressor(**params)
            self.model.fit(X, y)
            self.is_trained = True

            os.makedirs(self.model_dir, exist_ok=True)
            with open(self.model_path, "wb") as f:
                pickle.dump(self.model, f)
            print("[LightGBM] Baseline congestion prediction model trained & saved successfully.")
        else:
            print("[LightGBM] Warning: lightgbm library not installed. Falling back to analytical heuristic.")

    def predict_zone_congestion(
        self,
        zone_id: str,
        crowd: ZoneCrowd,
        nearby_density: float = 0.5,
        exit_proximity: float = 20.0,
        hazard_severity: float = 0.0,
    ) -> CongestionPrediction:
        """
        Predicts 1-minute near-future congestion probability for a specific zone.
        """
        features = pd.DataFrame(
            [
                {
                    "current_density": crowd.density,
                    "density_change_rate": crowd.inflow_rate - crowd.outflow_rate,
                    "people_inflow": crowd.inflow_rate,
                    "people_outflow": crowd.outflow_rate,
                    "avg_movement_speed": crowd.avg_speed,
                    "nearby_zone_density": nearby_density,
                    "exit_proximity": exit_proximity,
                    "hazard_severity": hazard_severity,
                }
            ]
        )

        if HAS_LIGHTGBM and self.model and self.is_trained:
            pred_prob = float(self.model.predict(features[self.FEATURE_COLUMNS])[0])
            pred_prob = float(np.clip(pred_prob, 0.0, 1.0))
        else:
            # Fallback heuristic calculation if LightGBM model is not ready
            pred_prob = min(1.0, (crowd.density / 3.0) + (crowd.inflow_rate * 0.05) + (hazard_severity * 0.2))

        pred_density_1m = round(crowd.density * (1.0 + (pred_prob - 0.5) * 0.8), 2)
        pred_density_3m = round(pred_density_1m * (1.0 + (pred_prob - 0.5) * 0.5), 2)

        trend = "RISING" if pred_prob > 0.6 else ("FALLING" if pred_prob < 0.3 else "STABLE")

        return CongestionPrediction(
            zone_id=zone_id,
            current_density=round(crowd.density, 2),
            predicted_density_1m=pred_density_1m,
            predicted_density_3m=pred_density_3m,
            predicted_congestion_prob=round(pred_prob, 3),
            trend=trend,
        )
