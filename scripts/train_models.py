import os
import json
import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split, KFold, cross_val_score, LeaveOneGroupOut, RandomizedSearchCV
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

os.makedirs('outputs/tables', exist_ok=True)
os.makedirs('outputs/models', exist_ok=True)

# 1. Load Clean Feature Matrix
df = pd.read_csv('data/processed/training_data.csv')

# Define Biophysical Baseline Calculator (Medlyn/Leuning-type model)
def calc_biophysical_wue(row):
    ca = row['CO2_ppm']
    vpd = row['VPD_kPa']
    red = row['Relative_Stomatal_Reduction_Pct']
    # Biophysical baseline: Intrinsic WUE scales with CO2 / (1.6 * (1 + VPD/D0))
    d0 = 1.5  # Stomatal sensitivity constant
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
y_residual = df['WUE_residual']
phys_baseline = df['WUE_phys_baseline']
groups = df['Paper_ID']

print("=== Phase 5: Biophysics-Guided Hybrid Model Training ===")

# --- 2. TRAIN / TEST SPLIT (80/20) ---
X_tr, X_te, y_tr, y_te, phys_tr, phys_te = train_test_split(
    X, y, phys_baseline, test_size=0.2, random_state=42
)
y_res_tr = y_tr - phys_tr

# Train Residual XGBoost Model
xgb_residual = XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.03, reg_alpha=1.0, reg_lambda=5.0, random_state=42)
xgb_residual.fit(X_tr, y_res_tr)

# Predict Hybrid Test Set
res_preds_te = xgb_residual.predict(X_te)
hybrid_preds_te = phys_te + res_preds_te

hybrid_r2 = r2_score(y_te, hybrid_preds_te)
hybrid_rmse = np.sqrt(mean_squared_error(y_te, hybrid_preds_te))
hybrid_mae = mean_absolute_error(y_te, hybrid_preds_te)

print("\n--- 80/20 Test Set Performance ---")
print(f"Pure Physics Baseline R2: {r2_score(y_te, phys_te):.3f}")
print(f"Biophysics-Guided Hybrid Model R2: {hybrid_r2:.3f} | RMSE: {hybrid_rmse:.2f} | MAE: {hybrid_mae:.2f}")

# --- 3. SHUFFLED 5-FOLD CROSS VALIDATION ---
kf = KFold(n_splits=5, shuffle=True, random_state=42)
cv_r2_scores = []

for train_idx, test_idx in kf.split(X, y):
    X_train_f, X_test_f = X.iloc[train_idx], X.iloc[test_idx]
    y_train_f, y_test_f = y.iloc[train_idx], y.iloc[test_idx]
    p_train_f, p_test_f = phys_baseline.iloc[train_idx], phys_baseline.iloc[test_idx]
    
    r_train_f = y_train_f - p_train_f
    
    m = XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.03, reg_alpha=1.0, reg_lambda=5.0, random_state=42)
    m.fit(X_train_f, r_train_f)
    
    r_preds = m.predict(X_test_f)
    h_preds = p_test_f + r_preds
    
    cv_r2_scores.append(r2_score(y_test_f, h_preds))

print(f"\n[Tier 1 Validation] Biophysics-Guided Hybrid 5-Fold CV R2: {np.mean(cv_r2_scores):.3f} (± {np.std(cv_r2_scores):.3f})")
print(f"  Per-fold R2 scores: {[round(s, 3) for s in cv_r2_scores]}")

# --- 4. LEAVE-ONE-STUDY-OUT CV (LOSO-CV) ---
logo = LeaveOneGroupOut()
loso_results = []

for train_idx, test_idx in logo.split(X, y, groups=groups):
    held_out_study = groups.iloc[test_idx[0]]
    X_tr_l, y_tr_l, p_tr_l = X.iloc[train_idx], y.iloc[train_idx], phys_baseline.iloc[train_idx]
    X_te_l, y_te_l, p_te_l = X.iloc[test_idx], y.iloc[test_idx], phys_baseline.iloc[test_idx]
    
    r_tr_l = y_tr_l - p_tr_l
    
    m_loso = XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.03, reg_alpha=1.0, reg_lambda=5.0, random_state=42)
    m_loso.fit(X_tr_l, r_tr_l)
    
    h_preds_loso = p_te_l + m_loso.predict(X_te_l)
    
    rmse_l = np.sqrt(mean_squared_error(y_te_l, h_preds_loso))
    mae_l = mean_absolute_error(y_te_l, h_preds_loso)
    r2_l = r2_score(y_te_l, h_preds_loso)
    
    loso_results.append({
        'Held_Out_Study': held_out_study,
        'Test_Samples': len(y_te_l),
        'RMSE': round(rmse_l, 2),
        'MAE': round(mae_l, 2),
        'R2_Score': round(r2_l, 3)
    })

loso_df = pd.DataFrame(loso_results)
print("\n--- [Tier 2 Validation] Leave-One-Study-Out CV (LOSO-CV) ---")
print(loso_df.to_string(index=False))

# --- 5. SAVE FINAL HYBRID MODEL ---
full_res_target = y - phys_baseline
final_hybrid_xgb = XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.03, reg_alpha=1.0, reg_lambda=5.0, random_state=42)
final_hybrid_xgb.fit(X, full_res_target)

final_hybrid_xgb.save_model('outputs/models/xgboost_wue_model.json')

# Save comparison summary
comp_df = pd.DataFrame([{
    'Model_Architecture': 'Biophysics-Guided Hybrid XGBoost',
    'Target_Variable': 'WUE_intrinsic (A/gs)',
    'Test_R2': round(hybrid_r2, 3),
    'Test_RMSE': round(hybrid_rmse, 2),
    'Test_MAE': round(hybrid_mae, 2),
    'CV_5Fold_Mean_R2': round(np.mean(cv_r2_scores), 3),
    'CV_5Fold_Std_R2': round(np.std(cv_r2_scores), 3)
}])
comp_df.to_csv('outputs/tables/model_comparison.csv', index=False)

print("\n" + "="*60)
print("SUCCESS: Trained Biophysics-Guided Hybrid Model & Saved Artifacts!")
print("Saved model comparison to: outputs/tables/model_comparison.csv")
print("Saved model to: outputs/models/xgboost_wue_model.json")