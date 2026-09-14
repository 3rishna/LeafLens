import os
import json
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split, GroupKFold, LeaveOneGroupOut
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

os.makedirs('outputs/tables', exist_ok=True)
os.makedirs('outputs/models', exist_ok=True)

# Single, consistent hyperparameter set used everywhere in the pipeline (train, ablation,
# SHAP, optimization sweep). These were selected via RandomizedSearchCV and are recorded
# in outputs/models/best_params.json - previously the paper, this script, and the
# ablation/optimization scripts each used a different, undocumented configuration.
with open('outputs/models/best_params.json') as f:
    BEST_PARAMS = json.load(f)
BEST_PARAMS['random_state'] = 42

# 1. Load Clean Feature Matrix
df = pd.read_csv('data/processed/training_data.csv')

# Define Biophysical Baseline Calculator (Medlyn/Leuning-type model)
def calc_biophysical_wue(row):
    ca = row['CO2_ppm']
    vpd = row['VPD_kPa']
    red = row['Relative_Stomatal_Reduction_Pct']
    # Biophysical baseline: Intrinsic WUE scales with CO2 / (1.6 * (1 + VPD/D0))
    d0 = 1.5  # Stomatal sensitivity constant (heuristic, not fit to data)
    base_wue = (ca * (1.0 - 0.25 * red / 100.0)) / (1.6 * (1.0 + vpd / d0))
    return base_wue

df['WUE_phys_baseline'] = df.apply(calc_biophysical_wue, axis=1)
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
y = df['WUE_intrinsic']
phys_baseline = df['WUE_phys_baseline']
groups = df['Genotype_Line'] + '_' + df['Paper_ID']  # unique per genotype-line per study
study_groups = df['Paper_ID']

print("=== Phase 5: Biophysics-Guided Hybrid Model Training ===")
print(f"n = {len(df)} rows, {groups.nunique()} unique genotype-line groups, params = {BEST_PARAMS}")

# --- 2. TRAIN / TEST SPLIT (80/20, grouped by genotype so no genotype leaks across split) ---
uniq_groups = groups.unique()
rng = np.random.RandomState(42)
test_groups = set(rng.choice(uniq_groups, size=max(1, int(0.2 * len(uniq_groups))), replace=False))
test_mask = groups.isin(test_groups)

X_tr, X_te = X[~test_mask], X[test_mask]
y_tr, y_te = y[~test_mask], y[test_mask]
phys_tr, phys_te = phys_baseline[~test_mask], phys_baseline[test_mask]
y_res_tr = y_tr - phys_tr

xgb_residual = XGBRegressor(**BEST_PARAMS)
xgb_residual.fit(X_tr, y_res_tr)

res_preds_te = xgb_residual.predict(X_te)
hybrid_preds_te = phys_te + res_preds_te

hybrid_r2 = r2_score(y_te, hybrid_preds_te)
hybrid_rmse = np.sqrt(mean_squared_error(y_te, hybrid_preds_te))
hybrid_mae = mean_absolute_error(y_te, hybrid_preds_te)
phys_only_r2 = r2_score(y_te, phys_te)

# Naive ML: XGBoost predicting WUE directly from the same features, no physics prior
naive_ml = XGBRegressor(**BEST_PARAMS)
naive_ml.fit(X_tr, y_tr)
naive_preds_te = naive_ml.predict(X_te)
naive_r2 = r2_score(y_te, naive_preds_te)

print("\n--- 80/20 Group-Held-Out Test Set Performance ---")
print(f"Pure Physics Baseline R2:        {phys_only_r2:.3f}")
print(f"Naive ML (no physics prior) R2:  {naive_r2:.3f}")
print(f"Physics-Informed Hybrid R2:      {hybrid_r2:.3f} | RMSE: {hybrid_rmse:.2f} | MAE: {hybrid_mae:.2f}")

# --- 3. GROUPED 5-FOLD CROSS VALIDATION (grouped by genotype line to prevent leakage) ---
gkf = GroupKFold(n_splits=5)
cv_r2_scores, cv_naive_r2_scores = [], []

for train_idx, test_idx in gkf.split(X, y, groups=groups):
    X_train_f, X_test_f = X.iloc[train_idx], X.iloc[test_idx]
    y_train_f, y_test_f = y.iloc[train_idx], y.iloc[test_idx]
    p_train_f, p_test_f = phys_baseline.iloc[train_idx], phys_baseline.iloc[test_idx]

    r_train_f = y_train_f - p_train_f

    m = XGBRegressor(**BEST_PARAMS)
    m.fit(X_train_f, r_train_f)
    h_preds = p_test_f + m.predict(X_test_f)
    cv_r2_scores.append(r2_score(y_test_f, h_preds))

    m_naive = XGBRegressor(**BEST_PARAMS)
    m_naive.fit(X_train_f, y_train_f)
    cv_naive_r2_scores.append(r2_score(y_test_f, m_naive.predict(X_test_f)))

print(f"\n[Tier 1 Validation] Grouped 5-Fold CV (by genotype line):")
print(f"  Physics-Informed Hybrid R2: {np.mean(cv_r2_scores):.3f} (+/- {np.std(cv_r2_scores):.3f})")
print(f"  Naive ML (no physics) R2:   {np.mean(cv_naive_r2_scores):.3f} (+/- {np.std(cv_naive_r2_scores):.3f})")
print(f"  Per-fold hybrid R2 scores: {[round(s, 3) for s in cv_r2_scores]}")

# --- 4. LEAVE-ONE-STUDY-OUT CV (LOSO-CV) --- the primary generalization test: can the
# model transfer to a study (cultivar/gene target/environment) it has never seen?
logo = LeaveOneGroupOut()
loso_results = []

for train_idx, test_idx in logo.split(X, y, groups=study_groups):
    held_out_study = study_groups.iloc[test_idx[0]]
    X_tr_l, y_tr_l, p_tr_l = X.iloc[train_idx], y.iloc[train_idx], phys_baseline.iloc[train_idx]
    X_te_l, y_te_l, p_te_l = X.iloc[test_idx], y.iloc[test_idx], phys_baseline.iloc[test_idx]

    r_tr_l = y_tr_l - p_tr_l

    m_loso = XGBRegressor(**BEST_PARAMS)
    m_loso.fit(X_tr_l, r_tr_l)
    h_preds_loso = p_te_l + m_loso.predict(X_te_l)

    loso_results.append({
        'Held_Out_Study': held_out_study,
        'Test_Samples': len(y_te_l),
        'RMSE': round(np.sqrt(mean_squared_error(y_te_l, h_preds_loso)), 2),
        'MAE': round(mean_absolute_error(y_te_l, h_preds_loso), 2),
        'R2_Score': round(r2_score(y_te_l, h_preds_loso), 3)
    })

loso_df = pd.DataFrame(loso_results)
loso_path = 'outputs/tables/loso_cv_results.csv'
loso_df.to_csv(loso_path, index=False)

print("\n--- [Tier 2 Validation] Leave-One-Study-Out CV (LOSO-CV) ---")
print(loso_df.to_string(index=False))
print(f"Saved LOSO-CV results to: {loso_path}")

# --- 5. SAVE FINAL HYBRID MODEL (fit on all data) ---
full_res_target = y - phys_baseline
final_hybrid_xgb = XGBRegressor(**BEST_PARAMS)
final_hybrid_xgb.fit(X, full_res_target)
final_hybrid_xgb.save_model('outputs/models/xgboost_wue_model.json')

# Save comparison summary
comp_df = pd.DataFrame([
    {'Model_Architecture': 'Pure Physics Baseline (no ML)', 'Test_R2': round(phys_only_r2, 3),
     'CV_5Fold_Mean_R2': np.nan, 'CV_5Fold_Std_R2': np.nan, 'LOSO_Mean_R2': np.nan},
    {'Model_Architecture': 'Naive ML (XGBoost, no physics prior)', 'Test_R2': round(naive_r2, 3),
     'CV_5Fold_Mean_R2': round(np.mean(cv_naive_r2_scores), 3), 'CV_5Fold_Std_R2': round(np.std(cv_naive_r2_scores), 3),
     'LOSO_Mean_R2': np.nan},
    {'Model_Architecture': 'Physics-Informed Hybrid XGBoost (LeafLens)', 'Test_R2': round(hybrid_r2, 3),
     'CV_5Fold_Mean_R2': round(np.mean(cv_r2_scores), 3), 'CV_5Fold_Std_R2': round(np.std(cv_r2_scores), 3),
     'LOSO_Mean_R2': round(loso_df['R2_Score'].mean(), 3)},
])
comp_df.to_csv('outputs/tables/model_comparison.csv', index=False)

print("\n" + "="*60)
print("SUCCESS: Trained Biophysics-Guided Hybrid Model & Saved Artifacts!")
print(comp_df.to_string(index=False))
