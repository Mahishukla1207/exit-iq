from fastapi import APIRouter
from app.api.simulation import simulation_engine

router = APIRouter(prefix="/prediction", tags=["Prediction"])


@router.get("")
def get_predictions():
    if not simulation_engine:
        return {}
    return {
        "predictions": simulation_engine.predictions,
        "is_model_trained": simulation_engine.prediction_engine.is_trained,
        "model_type": "LightGBM Regressor (Near-Future Congestion Predictor)",
    }
