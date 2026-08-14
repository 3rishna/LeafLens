import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from xgboost import XGBRegressor

os.makedirs('outputs/tables', exist_ok=True)
os.makedirs('outputs/figures', exist_ok=True)

sns.set_theme(style='whitegrid')
plt.rcParams.update({'font.size': 11})

# 1. Load Clean Data
df = pd.read_csv('data/processed/training_data.csv')
climate = pd.read_csv('data/climate/telangana_climate.csv')

def calc_biophysical_wue(ca, vpd, red):
    d0 = 1.5
    return (ca * (1.0 - 0.25 * red / 100.0)) / (1.6 * (1.0 + vpd / d0))

df['WUE_phys_baseline'] = df.apply(lambda r: calc_biophysical_wue(r['CO2_ppm'], r['VPD_kPa'], r['Relative_Stomatal_Reduction_Pct']), axis=1)
df['WUE_residual'] = df['WUE_intrinsic'] - df['WUE_phys_baseline']

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
y_residual = df['WUE_residual']

print("=== Phase 7: Biophysics-Guided Optimization Sweep & Bootstrap Uncertainty ===")

# --- 2. BOOTSTRAP RESAMPLING (500 ITERATIONS) ---
N_BOOTSTRAP = 500
reductions = np.arange(0, 86, 5) # 0%, 5%, 10%, ..., 85%

districts = ['Warangal', 'Nizamabad', 'Karimnagar', 'Nalgonda', 'Khammam']
seasons = ['Kharif', 'Pre_Monsoon']

bootstrap_models = []

print(f"Training {N_BOOTSTRAP} bootstrap XGBoost residual models...")
for b in range(N_BOOTSTRAP):
    sample_idx = np.random.choice(len(df), size=len(df), replace=True)
    X_b, y_b = X.iloc[sample_idx], y_residual.iloc[sample_idx]
    
    m = XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.03, reg_alpha=1.0, reg_lambda=5.0, random_state=b)
    m.fit(X_b, y_b)
    bootstrap_models.append(m)

# --- 3. PREDICTION SWEEP ---
recommendations = []
sweep_plot_records = []

for dist in districts:
    for season in seasons:
        sub_clim = climate[(climate['District'] == dist) & (climate['Season'] == season)]
        if len(sub_clim) == 0:
            continue
            
        mean_t = sub_clim['T2M'].mean()
        mean_vpd = sub_clim['VPD_kPa'].mean()
        mean_ppfd = sub_clim['PPFD_estimated_umol'].mean()
        co2_val = 420.0
        is_drought_val = 1 # Irrigation scarcity scenario
        
        best_red = 0
        best_wue = -999.0
        best_ci = (0, 0)
        
        for red in reductions:
            red_sq = red ** 2
            vpd_x_red = mean_vpd * red
            ppfd_x_red = (mean_ppfd * red) / 1000.0
            
            # 1. Physics Baseline Prediction
            phys_base_val = calc_biophysical_wue(co2_val, mean_vpd, red)
            
            # 2. ML Residual Grid Row
            grid_row = pd.DataFrame([{
                'Relative_Stomatal_Reduction_Pct': red,
                'Reduction_Squared': red_sq,
                'Temperature_C': mean_t,
                'CO2_ppm': co2_val,
                'PPFD_umol': mean_ppfd,
                'VPD_kPa': mean_vpd,
                'VPD_x_Reduction': vpd_x_red,
                'PPFD_x_Reduction': ppfd_x_red,
                'Is_Drought': is_drought_val,
                'Study_Karavolias2023': 0,
                'Study_Karavolias2024': 0
            }])
            
            # 3. Hybrid Bootstrap Predictions
            boot_hybrid_preds = [phys_base_val + m.predict(grid_row)[0] for m in bootstrap_models]
            mean_hybrid_pred = np.mean(boot_hybrid_preds)
            lower_ci = np.percentile(boot_hybrid_preds, 2.5)
            upper_ci = np.percentile(boot_hybrid_preds, 97.5)
            
            sweep_plot_records.append({
                'District': dist,
                'Season': season,
                'Reduction_Pct': red,
                'Mean_WUE': mean_hybrid_pred,
                'Lower_CI': lower_ci,
                'Upper_CI': upper_ci
            })
            
            if mean_hybrid_pred > best_wue:
                best_wue = mean_hybrid_pred
                best_red = red
                best_ci = (lower_ci, upper_ci)
                
        recommendations.append({
            'District': dist,
            'Season': season,
            'Mean_Temp_C': round(mean_t, 1),
            'Mean_VPD_kPa': round(mean_vpd, 2),
            'Optimal_Reduction_Pct': int(best_red),
            'Predicted_Intrinsic_WUE': round(best_wue, 2),
            'WUE_95CI_Lower': round(best_ci[0], 2),
            'WUE_95CI_Upper': round(best_ci[1], 2)
        })

rec_df = pd.DataFrame(recommendations)
rec_path = 'outputs/tables/district_optimal_recommendations.csv'
rec_df.to_csv(rec_path, index=False)

print("\n" + "="*75)
print("=== OPTIMAL STOMATAL REDUCTION CANDIDATE RANGES (TELANGANA) ===")
print("="*75)
print(rec_df.to_string(index=False))

# --- 4. PLOT OPTIMIZATION CURVES WITH BOOTSTRAP CONFIDENCE BANDS ---
sweep_df = pd.DataFrame(sweep_plot_records)

fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)

for idx, season in enumerate(seasons):
    ax = axes[idx]
    season_data = sweep_df[sweep_df['Season'] == season]
    
    for dist in districts:
        d_sub = season_data[season_data['District'] == dist]
        ax.plot(d_sub['Reduction_Pct'], d_sub['Mean_WUE'], label=dist, linewidth=2.5)
        ax.fill_between(d_sub['Reduction_Pct'], d_sub['Lower_CI'], d_sub['Upper_CI'], alpha=0.15)
        
    ax.set_title(f'Hybrid Optimization Sweep — {season} Season (Irrigation Scarcity)', fontsize=13, fontweight='bold')
    ax.set_xlabel('Stomatal Reduction (%)', fontsize=11)
    if idx == 0:
        ax.set_ylabel('Predicted Intrinsic WUE (A/gs)', fontsize=11)
    ax.legend(title='District', loc='lower right')
    ax.set_xlim(0, 85)

plt.tight_layout()
plt.savefig('outputs/figures/optimization_curves_bootstrap.png', dpi=300)
plt.close()

print("\n" + "="*75)
print("SUCCESS: Biophysics-Guided Optimization Sweep Complete!")
print(f"Saved recommendations table to: {rec_path}")
print("Saved key result figure to: outputs/figures/optimization_curves_bootstrap.png")