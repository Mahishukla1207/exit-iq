from fastapi import APIRouter
from app.api import simulation as simulation_api

router = APIRouter(prefix="/prediction", tags=["Prediction"])


from app.prediction.benchmark import MLBenchmarkSuite

@router.get("")
def get_predictions():
    if not simulation_api.simulation_engine:
        return {}
    return {
        "predictions": simulation_api.simulation_engine.predictions,
        "is_model_trained": simulation_api.simulation_engine.prediction_engine.is_trained,
        "model_type": "LightGBM Regressor (Near-Future Congestion Predictor)",
    }


@router.get("/benchmark")
def get_ml_benchmark():
    suite = MLBenchmarkSuite()
    return suite.run_benchmark(num_samples=2000)
