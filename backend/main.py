import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.services.model_service import ModelService
from backend.routes.api import create_api_router

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

app = FastAPI(
    title="CRISPR Rice Engineering System API",
    description="Backend API for Physics-Informed Stomatal Reduction Prioritization Portal",
    version="2.0.0"
)

# Enable CORS for React frontend (Vite port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_service = ModelService(PROJECT_ROOT)
app.include_router(create_api_router(model_service))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
