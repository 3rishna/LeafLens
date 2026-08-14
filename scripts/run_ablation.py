import os
import pandas as pd
import numpy as np

from sklearn.model_selection import KFold, cross_val_score
from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error, r2_score

os.makedirs('outputs/tables', exist_ok=True)

df = pd.read_csv('data/processed/training_data.csv')
TARGET = 'WUE_instantaneous'

# Define Feature Sets for Ablation
ABLATION_SETS = {
    'Full Physics-Informed Model': [
        'Relative_Stomatal_Reduction_Pct', 'Reduction_Squared', 'Temperature_C',
        'CO2_ppm', 'PPFD_umol', 'VPD_kPa', 'VPD_x_Reduction', 'PPFD_x_Reduction',
        'Is_Drought', 'Study_Karavolias2023', 'Study_Karavolias2024'
    ],
    'Ablation A (Drop VPD Features)': [
        'Relative_Stomatal_Reduction_Pct', 'Reduction_Squared', 'Temperature_C',
        'CO2_ppm', 'PPFD_umol', 'PPFD_x_Reduction',
        'Is_Drought', 'Study_Karavolias2023', 'Study_Karavolias2024'
    ],
    'Ablation B (Drop Interaction Terms)': [
        'Relative_Stomatal_Reduction_Pct', 'Temperature_C', 'CO2_ppm',
        'PPFD_umol', 'VPD_kPa', 'Is_Drought',
        'Study_Karavolias2023', 'Study_Karavolias2024'
    ],
    'Ablation C (Drop Study Dummies)': [
        'Relative_Stomatal_Reduction_Pct', 'Reduction_Squared', 'Temperature_C',
        'CO2_ppm', 'PPFD_umol', 'VPD_kPa', 'VPD_x_Reduction', 'PPFD_x_Reduction',
        'Is_Drought'
    ],
    'Ablation D (Naive ML - No Physics)': [
        'Relative_Stomatal_Reduction_Pct', 'Temperature_C', 'CO2_ppm',
        'PPFD_umol', 'Is_Drought'
    ]
}

print("=== Phase 8: Feature Ablation Study ===")

kf = KFold(n_splits=5, shuffle=True, random_state=42)
ablation_results = []

for name, feature_list in ABLATION_SETS.items():
    X_sub = df[feature_list]
    y = df[TARGET]
    
    model = XGBRegressor(n_estimators=50, max_depth=3, learning_rate=0.03, reg_alpha=1.0, reg_lambda=5.0, random_state=42)
    scores = cross_val_score(model, X_sub, y, cv=kf, scoring='r2')
    
    mean_r2 = scores.mean()
    std_r2 = scores.std()
    
    ablation_results.append({
        'Model_Variant': name,
        'Num_Features': len(feature_list),
        'Mean_5Fold_R2': round(mean_r2, 3),
        'R2_Std_Dev': round(std_r2, 3),
        'R2_Drop_Vs_Full': round(ablation_results[0]['Mean_5Fold_R2'] - mean_r2, 3) if len(ablation_results) > 0 else 0.0
    })

ablation_df = pd.DataFrame(ablation_results)
out_path = 'outputs/tables/ablation_study_results.csv'
ablation_df.to_csv(out_path, index=False)

print("\n" + "="*70)
print("=== FEATURE ABLATION STUDY RESULTS ===")
print("="*70)
print(ablation_df.to_string(index=False))
print(f"\nSUCCESS: Saved ablation results to: {out_path}")