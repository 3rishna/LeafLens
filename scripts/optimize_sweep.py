import os
import json
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

with open('outputs/models/best_params.json') as f:
    BEST_PARAMS = json.load(f)
BEST_PARAMS['random_state'] = None  # varied across bootstrap resamples below

# Training-data domain bounds, used to flag extrapolated sweep/recommendation points.
# NOTE: gradient-boosted trees cannot extrapolate beyond the range of the training data
# for a feature - predictions outside this envelope reduce to the nearest training leaf
# and should not be read as validated forecasts.
DOMAIN = {
    'Temperature_C': (df['Temperature_C'].min(), df['Temperature_C'].max()),
    'VPD_kPa': (df['VPD_kPa'].min(), df['VPD_kPa'].max()),
    'PPFD_umol': (df['PPFD_umol'].min(), df['PPFD_umol'].max()),
}

def in_domain(t, vpd, ppfd):
    return (DOMAIN['Temperature_C'][0] <= t <= DOMAIN['Temperature_C'][1] and
            DOMAIN['VPD_kPa'][0] <= vpd <= DOMAIN['VPD_kPa'][1] and
            DOMAIN['PPFD_umol'][0] <= ppfd <= DOMAIN['PPFD_umol'][1])

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
print("CAUTION: grouped cross-validation (see outputs/tables/model_comparison.csv and")
print("loso_cv_results.csv) shows this model has ~0 or negative R^2 on held-out")
print("genotypes/studies. The sweep below is exploratory / hypothesis-generating and")
print("is NOT a validated trait-design recommendation.")

N_BOOTSTRAP = 500
reductions = np.arange(0, 86, 5)

districts = ['Warangal', 'Nizamabad', 'Karimnagar', 'Nalgonda', 'Khammam']
seasons = ['Kharif', 'Pre_Monsoon']

rng = np.random.RandomState(42)
bootstrap_models = []
print(f"Training {N_BOOTSTRAP} bootstrap XGBoost residual models...")
for b in range(N_BOOTSTRAP):
    sample_idx = rng.choice(len(df), size=len(df), replace=True)
    X_b, y_b = X.iloc[sample_idx], y_residual.iloc[sample_idx]
    params_b = dict(BEST_PARAMS)
    params_b['random_state'] = b
    m = XGBRegressor(**params_b)
    m.fit(X_b, y_b)
    bootstrap_models.append(m)

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
        is_drought_val = 1

        domain_ok = in_domain(mean_t, mean_vpd, mean_ppfd)

        best_red_all, best_wue_all, best_ci_all = 0, -1e9, (0, 0)
        best_red_dom, best_wue_dom, best_ci_dom = None, -1e9, (0, 0)

        for red in reductions:
            red_sq = red ** 2
            vpd_x_red = mean_vpd * red
            ppfd_x_red = (mean_ppfd * red) / 1000.0

            phys_base_val = calc_biophysical_wue(co2_val, mean_vpd, red)

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

            boot_hybrid_preds = [phys_base_val + m.predict(grid_row)[0] for m in bootstrap_models]
            mean_hybrid_pred = np.mean(boot_hybrid_preds)
            lower_ci = np.percentile(boot_hybrid_preds, 2.5)
            upper_ci = np.percentile(boot_hybrid_preds, 97.5)
            red_domain_ok = domain_ok  # reduction itself is not a climate extrapolation axis

            sweep_plot_records.append({
                'District': dist, 'Season': season, 'Reduction_Pct': red,
                'Mean_WUE': mean_hybrid_pred, 'Lower_CI': lower_ci, 'Upper_CI': upper_ci,
                'In_Training_Domain': domain_ok
            })

            if mean_hybrid_pred > best_wue_all:
                best_wue_all, best_red_all, best_ci_all = mean_hybrid_pred, red, (lower_ci, upper_ci)
            if domain_ok and mean_hybrid_pred > best_wue_dom:
                best_wue_dom, best_red_dom, best_ci_dom = mean_hybrid_pred, red, (lower_ci, upper_ci)

        recommendations.append({
            'District': dist, 'Season': season,
            'Mean_Temp_C': round(mean_t, 1), 'Mean_VPD_kPa': round(mean_vpd, 2),
            'Mean_PPFD_umol': round(mean_ppfd, 0),
            'In_Training_Domain': domain_ok,
            'Optimal_Reduction_Pct': int(best_red_all),
            'Predicted_Intrinsic_WUE': round(best_wue_all, 2),
            'WUE_95CI_Lower': round(best_ci_all[0], 2), 'WUE_95CI_Upper': round(best_ci_all[1], 2),
        })

rec_df = pd.DataFrame(recommendations)
rec_path = 'outputs/tables/district_optimal_recommendations.csv'
rec_df.to_csv(rec_path, index=False)
rec_df.to_csv('district_recommendations.csv', index=False)

print("\n" + "="*90)
print("=== EXPLORATORY STOMATAL-REDUCTION SWEEP (TELANGANA) - hypothesis-generating only ===")
print("="*90)
print(rec_df.to_string(index=False))
n_out = (~rec_df['In_Training_Domain']).sum()
print(f"\n{n_out}/{len(rec_df)} district-season scenarios fall outside the training data's")
print("temperature/VPD/PPFD envelope and are extrapolated predictions.")

sweep_df = pd.DataFrame(sweep_plot_records)

fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
for idx, season in enumerate(seasons):
    ax = axes[idx]
    season_data = sweep_df[sweep_df['Season'] == season]
    for dist in districts:
        d_sub = season_data[season_data['District'] == dist]
        ax.plot(d_sub['Reduction_Pct'], d_sub['Mean_WUE'], label=dist, linewidth=2.5)
        ax.fill_between(d_sub['Reduction_Pct'], d_sub['Lower_CI'], d_sub['Upper_CI'], alpha=0.15)

    domain_flag = season_data['In_Training_Domain'].iloc[0] if len(season_data) else True
    tag = '' if domain_flag else '  [extrapolated beyond training domain]'
    ax.set_title(f'Bootstrap Sweep - {season} Season (Irrigation Scarcity){tag}', fontsize=12, fontweight='bold')
    ax.set_xlabel('Stomatal Reduction (%)', fontsize=11)
    if idx == 0:
        ax.set_ylabel('Predicted Intrinsic WUE (A/gs)', fontsize=11)
    ax.legend(title='District', loc='lower right', fontsize=9)
    ax.set_xlim(0, 85)

fig.suptitle('Exploratory only - model shows ~0 held-out R$^2$ under grouped/LOSO CV (see Table: model_comparison.csv)', fontsize=10, y=1.02)
plt.tight_layout()
plt.savefig('outputs/figures/optimization_curves_bootstrap.png', dpi=300, bbox_inches='tight')
plt.close()

print("\n" + "="*90)
print("SUCCESS: Sweep complete (exploratory - see CV caveat above).")
print(f"Saved recommendations table to: {rec_path}")
print("Saved figure to: outputs/figures/optimization_curves_bootstrap.png")
