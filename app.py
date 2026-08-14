"""Streamlit dashboard — Biophysics-Guided Hybrid ML for CRISPR stomatal engineering targets."""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from xgboost import XGBRegressor

ROOT = Path(__file__).parent
FIGURES = ROOT / "figures"
RECOMMENDATIONS_CSV = ROOT / "district_recommendations.csv"
MODEL_PATH = ROOT / "outputs" / "models" / "xgboost_wue_model.json"
CLIMATE_CSV = ROOT / "data" / "climate" / "telangana_climate.csv"

DISTRICTS = ["Warangal", "Nizamabad", "Karimnagar", "Nalgonda", "Khammam"]
SEASON_OPTIONS = {
    "Kharif (Monsoon)": "Kharif",
    "Pre-Monsoon (Summer)": "Pre_Monsoon",
}
SEASONAL_RANGES = {
    "Kharif": "~20%",
    "Pre_Monsoon": "40–50%",
}

st.set_page_config(
    page_title="CRISPR Stomatal Engineering — Telangana Rice",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1200px; }
        [data-testid="stMetric"] {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 0.75rem 1rem;
        }
        .model-box {
            background: #f1f5f9;
            border-left: 4px solid #2563eb;
            border-radius: 8px;
            padding: 1rem 1.25rem;
            margin: 1rem 0 1.5rem 0;
            font-size: 0.95rem;
            line-height: 1.6;
            color: #334155;
        }
        .limitations {
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-radius: 8px;
            padding: 1rem 1.25rem;
            font-size: 0.88rem;
            color: #78350f;
            line-height: 1.55;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_recommendations() -> pd.DataFrame:
    return pd.read_csv(RECOMMENDATIONS_CSV)


@st.cache_data
def load_climate() -> pd.DataFrame:
    return pd.read_csv(CLIMATE_CSV)


@st.cache_resource
def load_model() -> XGBRegressor:
    model = XGBRegressor()
    model.load_model(MODEL_PATH)
    return model


def calc_biophysical_wue(ca: float, vpd: float, reduction: float) -> float:
    """Medlyn/Leuning-style intrinsic WUE baseline (μmol CO₂ / mol H₂O)."""
    d0 = 1.5
    return (ca * (1.0 - 0.25 * reduction / 100.0)) / (1.6 * (1.0 + vpd / d0))


def build_feature_row(
    reduction: float,
    temp: float,
    vpd: float,
    ppfd: float,
    co2: float = 420.0,
    is_drought: int = 1,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Relative_Stomatal_Reduction_Pct": reduction,
                "Reduction_Squared": reduction**2,
                "Temperature_C": temp,
                "CO2_ppm": co2,
                "PPFD_umol": ppfd,
                "VPD_kPa": vpd,
                "VPD_x_Reduction": vpd * reduction,
                "PPFD_x_Reduction": (ppfd * reduction) / 1000.0,
                "Is_Drought": is_drought,
                "Study_Karavolias2023": 0,
                "Study_Karavolias2024": 0,
            }
        ]
    )


def get_climate_context(district: str, season_key: str) -> dict:
    climate = load_climate()
    subset = climate[
        (climate["District"] == district) & (climate["Season"] == season_key)
    ]
    if subset.empty:
        return {"temp": 28.0, "vpd": 1.5, "ppfd": 1200.0}
    return {
        "temp": float(subset["T2M"].mean()),
        "vpd": float(subset["VPD_kPa"].mean()),
        "ppfd": float(subset["PPFD_estimated_umol"].mean()),
    }


def physics_vs_hybrid_curve(district: str, season_key: str) -> go.Figure:
    ctx = get_climate_context(district, season_key)
    model = load_model()
    reductions = np.arange(0, 86, 2)

    physics = [calc_biophysical_wue(420.0, ctx["vpd"], r) for r in reductions]
    hybrid = [
        physics[i] + model.predict(build_feature_row(r, ctx["temp"], ctx["vpd"], ctx["ppfd"]))[0]
        for i, r in enumerate(reductions)
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=reductions,
            y=physics,
            mode="lines",
            name="Pure physics baseline",
            line=dict(color="#94a3b8", width=2.5, dash="dash"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=reductions,
            y=hybrid,
            mode="lines",
            name="Hybrid (physics + XGBoost residual)",
            line=dict(color="#2563eb", width=3),
        )
    )
    fig.update_layout(
        title=f"Physics baseline vs hybrid model — {district}, {season_key.replace('_', '-')} season",
        xaxis_title="Stomatal reduction (%)",
        yaxis_title="Intrinsic WUEᵢ (μmol CO₂ / mol H₂O)",
        template="plotly_white",
        height=380,
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )
    return fig


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configuration")
    district = st.selectbox("District", DISTRICTS, index=0)
    season_label = st.selectbox("Season", list(SEASON_OPTIONS.keys()), index=0)
    season_key = SEASON_OPTIONS[season_label]

    st.divider()
    st.caption(
        "Recommendations are derived from district-level climate means "
        "(temperature, VPD, PPFD) under an irrigation-scarcity scenario."
    )

# ── Header ───────────────────────────────────────────────────────────────────
st.title("Biophysics-Guided Hybrid ML for CRISPR Stomatal Engineering")
st.caption(
    "Prioritising stomatal reduction targets for rice water-use efficiency "
    "across Telangana districts using a Medlyn/Leuning baseline with XGBoost residual correction."
)

# ── Hybrid model explanation ─────────────────────────────────────────────────
st.markdown(
    """
    <div class="model-box">
    <strong>Hybrid model architecture.</strong>
    Intrinsic water-use efficiency (WUEᵢ) is predicted as
    <em>WUE<sub>hybrid</sub> = WUE<sub>physics</sub> + ΔWUE<sub>ML</sub></em>, where
    <em>WUE<sub>physics</sub></em> follows a Medlyn/Leuning biophysical baseline
    (CO₂, VPD, stomatal reduction) and an XGBoost regressor learns the
    non-linear residual (ΔWUE) from published stomatal-engineering experiments.
    Bootstrap resampling (500 iterations) yields 95% confidence intervals on optimal targets.
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Load district-season recommendation ─────────────────────────────────────
recs = load_recommendations()
row = recs[(recs["District"] == district) & (recs["Season"] == season_key)].iloc[0]

reduction_pct = int(row["Optimal_Reduction_Pct"])
wue_pred = float(row["Predicted_Intrinsic_WUE"])
ci_lower = float(row["WUE_95CI_Lower"])
ci_upper = float(row["WUE_95CI_Upper"])
seasonal_hint = SEASONAL_RANGES[season_key]

# ── Metric cards ─────────────────────────────────────────────────────────────
m1, m2, m3 = st.columns(3)

with m1:
    st.metric(
        label="Candidate reduction range",
        value=f"{reduction_pct}%",
        delta=f"Seasonal target {seasonal_hint}",
        delta_color="off",
    )

with m2:
    st.metric(
        label="Predicted WUEᵢ",
        value=f"{wue_pred:.1f}",
        help="Intrinsic water-use efficiency (μmol CO₂ / mol H₂O)",
    )

with m3:
    st.metric(
        label="95% CI (bootstrap)",
        value=f"[{ci_lower:.1f}, {ci_upper:.1f}]",
        help="Bootstrap 95% confidence interval on predicted WUEᵢ at the optimal reduction.",
    )

st.markdown("")

# ── Figures ──────────────────────────────────────────────────────────────────
fig_col1, fig_col2 = st.columns(2)

with fig_col1:
    st.subheader("Bootstrap optimisation curve")
    st.image(
        str(FIGURES / "optimization_curves_bootstrap.png"),
        use_container_width=True,
    )
    st.caption(
        f"**{district}** — follow the coloured line in the "
        f"{'left (Kharif)' if season_key == 'Kharif' else 'right (Pre-Monsoon)'} panel. "
        "Shaded bands are bootstrap 95% CIs across 500 XGBoost residual models."
    )

with fig_col2:
    st.subheader("2D partial dependence (Reduction × VPD)")
    st.image(
        str(FIGURES / "pdp_reduction_vpd.png"),
        use_container_width=True,
    )
    st.caption(
        "Partial dependence of hybrid WUEᵢ on stomatal reduction and vapour pressure deficit, "
        "holding other features at their training-set medians."
    )

# ── Optional physics vs hybrid toggle ─────────────────────────────────────────
show_comparison = st.toggle(
    "Show pure physics baseline vs hybrid residual",
    value=False,
    help="Overlay Medlyn/Leuning baseline against the full hybrid prediction for the selected district and season.",
)

if show_comparison:
    st.plotly_chart(
        physics_vs_hybrid_curve(district, season_key),
        use_container_width=True,
    )

# ── District detail strip ────────────────────────────────────────────────────
with st.expander("District climate context for this recommendation"):
    detail1, detail2, detail3 = st.columns(3)
    detail1.write(f"**Mean temperature:** {row['Mean_Temp_C']:.1f} °C")
    detail2.write(f"**Mean VPD:** {row['Mean_VPD_kPa']:.2f} kPa")
    detail3.write(f"**Optimal reduction:** {reduction_pct}%")

    st.dataframe(
        recs.assign(
            Season=recs["Season"].str.replace("_", "-"),
        ),
        use_container_width=True,
        hide_index=True,
    )

# ── Limitations ──────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
    <div class="limitations">
    <strong>Limitations.</strong>
    This tool is intended for <em>hypothesis generation</em> and
    <em>search-space reduction</em> prior to greenhouse or field validation — not as a
    standalone breeding decision system. Predictions synthesise published stomatal-engineering
    experiments with district-level climate aggregates; genotype-specific, soil, and management
    effects are not resolved.     Optimal reduction targets should be validated experimentally before
    CRISPR target prioritisation.
    </div>
    """,
    unsafe_allow_html=True,
)
