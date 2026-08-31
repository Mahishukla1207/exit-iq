import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health, simulation, routing, risk, prediction, websocket, cv_api
from app.simulation.simulation_engine import SimulationEngine
from app.cv.cv_pipeline import CVPipeline

app = FastAPI(
    title="ExitIQ API",
    description="AI-Powered Intelligent Emergency Evacuation & Dynamic Route Optimization Engine",
    version="1.0.0",
)

# Enable CORS for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate core simulation engine & CV pipeline
engine = SimulationEngine()
simulation.set_simulation_engine(engine)

cv_pipeline = CVPipeline(simulation_engine=engine)
cv_api.set_cv_pipeline(cv_pipeline)

# Register routers
app.include_router(health.router)
app.include_router(simulation.router, prefix="/api/v1")
app.include_router(routing.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(prediction.router, prefix="/api/v1")
app.include_router(cv_api.router, prefix="/api/v1")
app.include_router(websocket.router)


@app.get("/")
def root():
    return {
        "app": "ExitIQ Backend Service",
        "tagline": "Nearest exit nahi. Safest exit.",
        "status": "OPERATIONAL",
        "docs": "/docs",
    }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
