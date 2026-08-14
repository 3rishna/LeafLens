import os
import json
import shap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from xgboost import XGBRegressor
from sklearn.inspection import PartialDependenceDisplay

os.makedirs('outputs/figures', exist_ok=True)
os.makedirs('outputs/tables', exist_ok=True)

sns.set_theme(style='whitegrid')
plt.rcParams.update({'font.size': 11})

# 1. Load Data & Model
df = pd.read_csv('data/processed/training_data.csv')

FEATURE_COLS = [
    'Relative_Stomatal_Reduction_Pct',
    'Reduction_Squared',
    'Temperature_C',
    'CO2_ppm',
    'PPFD_umol',
    'VPD_kPa',
    'VPD_x_Reduction',
    'PPFD_x_Reduction',
    'Is_Drought',
    'Study_Karavolias2023',
    'Study_Karavolias2024'
]

X = df[FEATURE_COLS]

model = XGBRegressor()
model.load_model('outputs/models/xgboost_wue_model.json')

print("=== Phase 6: SHAP Interpretation of Biophysical Residuals ===")

# --- 2. COMPUTE SHAP VALUES ---
explainer = shap.TreeExplainer(model)
shap_values = explainer(X)

# --- 3. MECHANISM INDEPENDENCE TEST ---
mean_abs_shap = np.abs(shap_values.values).mean(axis=0)
total_shap_importance = mean_abs_shap.sum()

feature_importance_df = pd.DataFrame({
    'Feature': FEATURE_COLS,
    'Mean_Abs_SHAP': mean_abs_shap,
    'Pct_Importance': (mean_abs_shap / total_shap_importance) * 100
}).sort_values(by='Mean_Abs_SHAP', ascending=False)

study_importance_pct = feature_importance_df[
    feature_importance_df['Feature'].str.contains('Study')
]['Pct_Importance'].sum()

print("\n--- Feature Importance Table (Hybrid Model Residuals) ---")
print(feature_importance_df.to_string(index=False))

print(f"\n[Mechanism-Independence Check]")
print(f"Total Study Dummy Contribution: {study_importance_pct:.2f}% of total SHAP importance.")
if study_importance_pct < 15.0:
    print("✅ TEST PASSED: Study dummy contribution is low (< 15%). Biophysical features dominate residual learning!")
else:
    print("⚠️ NOTE: Study dummy contribution is >= 15%. Cultivar background differences present.")

feature_importance_df.to_csv('outputs/tables/shap_feature_importance.csv', index=False)

# --- 4. GENERATE SHAP PLOTS ---

# Fig A: SHAP Summary Bar Plot
plt.figure(figsize=(9, 6))
shap.plots.bar(shap_values, show=False)
plt.title('SHAP Feature Importance (Biophysical Hybrid Residuals)')
plt.tight_layout()
plt.savefig('outputs/figures/shap_summary_bar.png', dpi=300)
plt.close()

# Fig B: SHAP Beeswarm Plot
plt.figure(figsize=(10, 6))
shap.plots.beeswarm(shap_values, show=False)
plt.title('SHAP Beeswarm Plot (Directional Residual Impact)')
plt.tight_layout()
plt.savefig('outputs/figures/shap_beeswarm.png', dpi=300)
plt.close()

# Fig C: Dependence Plot (Reduction % vs SHAP value colored by VPD)
plt.figure(figsize=(8, 5))
shap.dependence_plot('Relative_Stomatal_Reduction_Pct', shap_values.values, X, interaction_index='VPD_kPa', show=False)
plt.title('SHAP Dependence: Stomatal Reduction (%) vs Residual Impact (Colored by VPD)')
plt.tight_layout()
plt.savefig('outputs/figures/shap_dependence_reduction.png', dpi=300)
plt.close()

# --- 5. 2D PARTIAL DEPENDENCE PLOT (THE NOVELTY FIGURE) ---
fig, ax = plt.subplots(figsize=(9, 6))
disp = PartialDependenceDisplay.from_estimator(
    model,
    X,
    features=[('Relative_Stomatal_Reduction_Pct', 'VPD_kPa')],
    grid_resolution=30,
    ax=ax
)
plt.title('2D Partial Dependence of WUE Residuals on Reduction (%) and VPD (kPa)')
plt.tight_layout()
plt.savefig('outputs/figures/pdp_reduction_vpd.png', dpi=300)
plt.close()

print("\n" + "="*60)
print("SUCCESS: Regenerated all 4 SHAP & PDP Interpretation Plots!")
print("Saved plots to: outputs/figures/")