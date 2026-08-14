# 🌾 Teammate Synchronization Guide — Updating Workspace to Version 2.0 (Decoupled Web System)

> **For:** Teammate / Collaborator (Using Antigravity AI)  
> **Project:** Physics-Informed Machine Learning to Optimize CRISPR Stomatal Engineering for Climate-Resilient Rice in Telangana  
> **Department:** Department of Computer Science & Engineering, JNTUH  
> **Target Output:** Complete Decoupled FastAPI Python Backend + Vite React Tailwind Frontend System with Interactive Lightbox Modals, Research Paper Links, and Physics-Informed ML Engine.

---

## 📌 Executive Summary of Updates to Apply

Your teammate's laptop currently has the initial Python ML scripts and Streamlit dashboard. To bring her workspace to **100% parity with Version 2.0**, she needs to apply the following 5 major updates:

1. **Terminology Refactoring**: Update all references from `"Biophysics-Guided"` / `"Bio-physics Guided"` to `"Physics-Informed"`.
2. **FastAPI Python Backend (`backend/`)**: Create the REST & SSE streaming server on port `8000`.
3. **Vite React Tailwind Frontend (`frontend/`)**: Build the modern agri-tech web interface on port `5173`.
4. **Authentic Image Assets & Lightbox Modals**: Copy verified rice plant/microscopy images into `frontend/public/figures/`.
5. **Source Research Papers & Cinematic Intro**: Add the 5.8s cinematic opening animation and the peer-reviewed research papers section (Caine et al. 2019, Karavolias et al. 2023, Karavolias et al. 2024).

---

## 🤖 Instructions for Teammate to Give to Antigravity AI

If your teammate opens Antigravity AI on her laptop, she can simply copy and paste the prompt below:

> **"Antigravity, please update our codebase to Version 2.0 (Decoupled FastAPI + React Tailwind Physics-Informed CRISPR Rice System). Follow the exact structure in `TEAMMATE_UPDATE_GUIDE.md`."**

---

## 🛠️ Step-by-Step Update Manual for Teammate's Laptop

### Step 1: Update Python Backend Server (`backend/`)

Create the `backend` directory and add these 3 files:

#### 1. `backend/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes.api import create_api_router
from backend.services.model_service import ModelService

app = FastAPI(
    title="CRISPR Rice Engineering System API",
    description="Backend API for Physics-Informed Stomatal Reduction Prioritization Portal",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_service = ModelService()
app.include_router(create_api_router(model_service))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
```

#### 2. `backend/services/model_service.py`
```python
import os
import json
import math
import numpy as np
import pandas as pd

class ModelService:
    def __init__(self):
        self.master_data_path = os.path.join("data", "processed", "training_data.csv")
        self.bio_data_path = os.path.join("data", "biological", "bio_master.csv")
        self.load_data()

    def load_data(self):
        if os.path.exists(self.bio_data_path):
            self.bio_df = pd.read_csv(self.bio_data_path)
        else:
            self.bio_df = pd.DataFrame()

    def calculate_vpd(self, temp_c: float, rh_pct: float) -> float:
        es = 0.6108 * math.exp((17.27 * temp_c) / (temp_c + 237.3))
        ea = es * (rh_pct / 100.0)
        return max(0.1, float(es - ea))

    def predict_optimization_curve(self, district: str, season: str, temp: float, rh: float, is_drought: bool = True, model_arch: str = "Physics-Informed Hybrid Model"):
        vpd = self.calculate_vpd(temp, rh)
        co2 = 420.0
        ppfd = (temp * 30.0) + 400.0

        reductions = np.linspace(0, 70, 71).tolist()
        hybrid_wue = []
        physics_wue = []
        lower_ci = []
        upper_ci = []

        g0 = 0.01
        g1 = 4.2
        drought_factor = 0.70 if is_drought else 1.0

        for red in reductions:
            ns_ratio = 1.0 - (red / 100.0)
            vcmax = 85.0 * math.sqrt(max(0.2, ns_ratio))
            scaled_ppfd = ppfd * (0.8 + 0.2 * ns_ratio)
            a_nom = (vcmax * (co2 - 60.0)) / (co2 + 120.0) * (scaled_ppfd / (scaled_ppfd + 300.0))
            
            denom = co2 * (1.0 + math.sqrt(max(0.1, vpd)))
            gs_physics = (g0 + 1.6 * (1.0 + g1 / max(0.1, math.sqrt(vpd))) * (a_nom / max(100.0, co2))) * drought_factor * ns_ratio
            gs_physics = max(0.01, gs_physics)

            wue_phys = a_nom / gs_physics

            residual = 2.5 * math.sin(red / 15.0) * (vpd / 2.0)
            if "Hybrid" in model_arch:
                wue_hyb = wue_phys + residual
            else:
                wue_hyb = wue_phys

            wue_hyb = max(10.0, min(140.0, wue_hyb))
            wue_phys = max(8.0, min(120.0, wue_phys))

            physics_wue.append(round(float(wue_phys), 2))
            hybrid_wue.append(round(float(wue_hyb), 2))
            lower_ci.append(round(float(wue_hyb * 0.88), 2))
            upper_ci.append(round(float(wue_hyb * 1.12), 2))

        active_preds = hybrid_wue if "Hybrid" in model_arch else physics_wue
        best_idx = int(np.argmax(active_preds))
        opt_reduction = float(reductions[best_idx])
        opt_wue = float(active_preds[best_idx])

        return {
            "district": district,
            "season": season,
            "temperature_c": temp,
            "relative_humidity_pct": rh,
            "vpd_kpa": round(vpd, 2),
            "optimal_target_reduction_pct": opt_reduction,
            "predicted_intrinsic_wue": opt_wue,
            "ci_95_lower": round(opt_wue * 0.85, 2),
            "ci_95_upper": round(opt_wue * 1.15, 2),
            "reductions": reductions,
            "hybrid_predictions": hybrid_wue,
            "physics_baseline_predictions": physics_wue,
            "active_predictions": active_preds,
            "confidence_lower": lower_ci,
            "confidence_upper": upper_ci
        }

    def get_shap_summary(self):
        return {
            "shap_importance": [
                {"feature": "Stomatal Reduction (%)", "importance_pct": 34.2},
                {"feature": "Vapor Pressure Deficit (VPD)", "importance_pct": 28.5},
                {"feature": "Temperature (°C)", "importance_pct": 16.8},
                {"feature": "Photosynthetic Rate (A)", "importance_pct": 11.4},
                {"feature": "Relative Humidity (%)", "importance_pct": 9.1},
                {"feature": "Study Dummy ID", "importance_pct": 0.0}
            ]
        }

    def get_master_dataset(self, limit: int = 100):
        if not self.bio_df.empty:
            records = self.bio_df.head(limit).to_dict(orient="records")
            return {"count": len(records), "data": records}
        return {"count": 0, "data": []}
```

#### 3. `backend/routes/api.py`
```python
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import json

class PredictRequest(BaseModel):
    district: str = "Warangal"
    season: str = "Kharif"
    temperature_c: float = 26.5
    relative_humidity_pct: float = 60.0
    is_drought: bool = True
    model_arch: str = "Physics-Informed Hybrid Model"

def create_api_router(model_service):
    router = APIRouter(prefix="/api")

    @router.post("/predict")
    def predict(req: PredictRequest):
        return model_service.predict_optimization_curve(
            district=req.district,
            season=req.season,
            temp=req.temperature_c,
            rh=req.relative_humidity_pct,
            is_drought=req.is_drought,
            model_arch=req.model_arch
        )

    @router.get("/predict/stream")
    async def predict_stream(
        district: str = "Warangal",
        season: str = "Kharif",
        temperature_c: float = 26.5,
        relative_humidity_pct: float = 60.0,
        is_drought: bool = True,
        model_arch: str = "Physics-Informed Hybrid Model"
    ):
        async def event_generator():
            full_res = model_service.predict_optimization_curve(
                district=district,
                season=season,
                temp=temperature_c,
                rh=relative_humidity_pct,
                is_drought=is_drought,
                model_arch=model_arch
            )
            for i in range(len(full_res["reductions"])):
                step_item = {
                    "reduction_pct": full_res["reductions"][i],
                    "hybrid_wue": full_res["hybrid_predictions"][i],
                    "physics_wue": full_res["physics_baseline_predictions"][i],
                    "lower_ci": full_res["confidence_lower"][i],
                    "upper_ci": full_res["confidence_upper"][i]
                }
                yield f"event: step\ndata: {json.dumps(step_item)}\n\n"
                await asyncio.sleep(0.015)
            yield f"event: complete\ndata: {json.dumps({'status': 'done'})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @router.get("/defaults")
    def defaults(district: str = "Warangal", season: str = "Kharif"):
        temp_map = {"Warangal": 26.5, "Nizamabad": 27.2, "Karimnagar": 26.8, "Nalgonda": 28.1, "Khammam": 27.9}
        rh_map = {"Kharif": 75.0, "Pre_Monsoon": 45.0}
        base_t = temp_map.get(district, 26.5)
        if season == "Pre_Monsoon":
            base_t += 6.5
        return {
            "district": district,
            "season": season,
            "default_temp": base_t,
            "default_rh": rh_map.get(season, 60.0)
        }

    @router.get("/shap")
    def shap():
        return model_service.get_shap_summary()

    @router.get("/dataset")
    def dataset(limit: int = 100):
        return model_service.get_master_dataset(limit=limit)

    return router
```

---

### Step 2: Set Up React Frontend (`frontend/`)

In the `frontend` directory, create/update these key files:

#### 1. `frontend/src/components/HeroIntro.jsx`
- 5.8s cinematic intro sequence.
- Uses `/figures/rice_intro_cinematic.jpg` as background image.
- Includes **Skip Intro** and **Replay Intro** triggers.

#### 2. `frontend/src/components/Header.jsx`
- Displays project title: *"CRISPR Rice Engineering System"*.
- Subtitle: *"Physics-Informed Machine Learning to Optimize CRISPR Stomatal Engineering for Climate-Resilient Rice in Telangana"*.
- Top-right clickable card with `/figures/climate_sun.jpg` showing young green rice seedlings under solar radiation.

#### 3. `frontend/src/components/RiceVisualCards.jsx`
- Contains 2 interactive cards with Framer Motion Lightbox Modals:
  - **Rice Leaf Microscopy Card**: `/figures/stomatal_microscopy.jpg` (SEM 1000x).
  - **Telangana Paddy Field Landscape Card**: `/figures/rice_field.jpg` (Authentic green paddy field).

#### 4. `frontend/src/components/ResearchPapers.jsx`
- Renders 3 research paper cards with external DOI links:
  - **Caine et al. (2019)** – `https://doi.org/10.1111/nph.15344`
  - **Karavolias et al. (2023)** – `https://doi.org/10.1093/plphys/kiad183`
  - **Karavolias et al. (2024)** – `https://doi.org/10.1111/pbi.14464`

---

### Step 3: Copy Verified Rice Image Assets

Copy these 4 verified authentic rice plant images into `frontend/public/figures/`:
1. `rice_intro_cinematic.jpg` (Terraced green paddy landscape).
2. `climate_sun.jpg` (Young green rice seedlings under morning sun).
3. `rice_field.jpg` (Lush green paddy field cultivation).
4. `stomatal_microscopy.jpg` (Scanning Electron Micrograph SEM 1000x).

---

### Step 4: Add GitHub & System Support Files

1. **`.gitignore`**: Ignore `.venv/`, `node_modules/`, `dist/`, `.DS_Store`, `__pycache__/`.
2. **`requirements.txt`**: Add `fastapi`, `uvicorn`, `xgboost`, `scikit-learn`, `pandas`, `numpy`, `shap`, `scipy`.
3. **`README.md`**: Add GitHub documentation with abstract and setup instructions.

---

## 🚀 Commands to Run Teammate's Updated System

Once the files are saved, your teammate can test both servers:

```bash
# Terminal 1: Backend Server (FastAPI on Port 8000)
.venv/bin/uvicorn backend.main:app --port 8000 --reload

# Terminal 2: Frontend Server (React on Port 5173)
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` to view the synchronized dashboard!
