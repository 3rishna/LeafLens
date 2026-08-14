# 🌾 Physics-Informed Machine Learning to Optimize CRISPR Stomatal Engineering for Climate-Resilient Rice in Telangana

> **Physics-Informed ML & Agricultural Biotechnology Platform**  
> **Authors / Collaborators:** Department of Computer Science & Engineering, JNTUH & Research Team  
> **Domain:** Biophysics + Physics-Informed ML + Agricultural Biotechnology + Climate Adaptation

---

## 📌 Abstract & Overview

Rising atmospheric temperatures and extreme Vapor Pressure Deficit (VPD) events in Telangana (Warangal, Nizamabad, Karimnagar, Nalgonda, Khammam) cause severe transpirational water stress and yield penalty in *Oryza sativa* (rice). While CRISPR-Cas9 genome editing targeting promoter regions of stomatal development genes (*OsEPF1*, *OsEPFL9/10*, *OsSTOMAGEN*) allows precise reduction of stomatal density ($N_s$), non-linear trade-offs between water-use efficiency (WUE) and photosynthetic carbon assimilation ($A$) vary dramatically under regional micro-climates.

This system combines a **Medlyn biophysical stomatal conductance model ($g_s$)** with a **Physics-Informed XGBoost Machine Learning architecture** trained on 168 digitized experimental measurements from peer-reviewed literature (Caine et al. 2019, Karavolias et al. 2023, Karavolias et al. 2024) and 11 years of NASA POWER daily climate data (2015–2026).

---

## 🚀 Key Features

1. **Decoupled Architecture**:
   - **FastAPI Python Backend**: REST endpoints & Real-time Server-Sent Events (SSE) streaming predictions.
   - **Vite React Tailwind Frontend**: Modern agricultural technology user portal with Framer Motion animations, Recharts, Plotly 3D rotatable surfaces, and SHAP explainability.
2. **Physics-Informed Hybrid ML Model**:
   - Outperforms pure physical Medlyn baselines ($R^2 = +0.183$ vs $R^2 = -0.266$, $+44.9$ percentage point gain).
   - 5-Fold Cross Validation ($0.174 \pm 0.078$).
3. **Interactive Visual Cards & Source Research Papers**:
   - Clickable lightbox views of authentic *Oryza sativa* SEM 1000x leaf microscopy and Telangana paddy field cultivation.
   - Direct DOI links to foundational literature.

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 18+ and npm

### 1. Backend Setup
```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/crispr-rice-engineering.git
cd crispr-rice-engineering

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn backend.main:app --port 8000 --reload
```

### 2. Frontend Setup
```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 📊 Repository Structure

```text
paddy_project/
├── backend/                # FastAPI backend application
│   ├── routes/             # REST & SSE streaming endpoints
│   ├── services/           # Model inference & biophysical calculation logic
│   └── main.py             # FastAPI entry point
├── frontend/               # Vite + React + Tailwind frontend application
│   ├── src/                # React components (ControlPanel, MetricCards, etc.)
│   └── public/figures/     # Authentic rice plant & microscopy images
├── data/                   # Master biological & NASA climate datasets
├── scripts/                # Data pipeline & model training scripts
├── outputs/                # Saved model artifacts & figure exports
├── README.md               # GitHub project overview & documentation
└── requirements.txt        # Python dependency requirements
```

---

## 📜 Citation & References

- **Caine et al. (2019)** – *Rice plants with reduced stomatal density exhibit improved water-use efficiency and drought tolerance*. New Phytologist. DOI: [10.1111/nph.15344](https://doi.org/10.1111/nph.15344)
- **Karavolias et al. (2023)** – *Paralogous OsEPFL genes modulate stomatal density in rice*. Plant Physiology. DOI: [10.1093/plphys/kiad183](https://doi.org/10.1093/plphys/kiad183)
- **Karavolias et al. (2024)** – *Promoter editing of OsSTOMAGEN tunes stomatal density and yield traits in rice*. Plant Biotechnology Journal. DOI: [10.1111/pbi.14464](https://doi.org/10.1111/pbi.14464)
