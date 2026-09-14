import os
import json
import pandas as pd
import numpy as np

from sklearn.model_selection import GroupKFold
from xgboost import XGBRegressor
from sklearn.metrics import r2_score

os.makedirs('outputs/tables', exist_ok=True)

df = pd.read_csv('data/processed/training_data.csv')
# FIX: previous version targeted 'WUE_instantaneous', a column that does not exist in
# this dataset (this script would raise a KeyError if actually executed) and used
# unshuffled-by-genotype KFold, which leaks replicate measurements of the same genotype
# across train/test and inflates every R^2 reported here.
TARGET = 'WUE_intrinsic'
GROUP_COL = df['Genotype_Line'] + '_' + df['Paper_ID']

with open('outputs/models/best_params.json') as f:
    BEST_PARAMS = json.load(f)
BEST_PARAMS['random_state'] = 42

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
    'Ablation D (Naive ML - No Physics Features)': [
        'Relative_Stomatal_Reduction_Pct', 'Temperature_C', 'CO2_ppm',
        'PPFD_umol', 'Is_Drought'
    ]
}

print("=== Phase 8: Feature Ablation Study (grouped 5-fold CV by genotype) ===")

gkf = GroupKFold(n_splits=5)
ablation_results = []
full_model_r2 = None

for name, feature_list in ABLATION_SETS.items():
    X_sub = df[feature_list]
    y = df[TARGET]

    scores = []
    for train_idx, test_idx in gkf.split(X_sub, y, groups=GROUP_COL):
        m = XGBRegressor(**BEST_PARAMS)
        m.fit(X_sub.iloc[train_idx], y.iloc[train_idx])
        scores.append(r2_score(y.iloc[test_idx], m.predict(X_sub.iloc[test_idx])))
    scores = np.array(scores)

    mean_r2, std_r2 = scores.mean(), scores.std()
    if full_model_r2 is None:
        full_model_r2 = mean_r2

    ablation_results.append({
        'Model_Variant': name,
        'Num_Features': len(feature_list),
        'Mean_5Fold_R2': round(mean_r2, 3),
        'R2_Std_Dev': round(std_r2, 3),
        'R2_Drop_Vs_Full': round(full_model_r2 - mean_r2, 3)
    })

ablation_df = pd.DataFrame(ablation_results)
out_path = 'outputs/tables/ablation_study_results.csv'
ablation_df.to_csv(out_path, index=False)

print("\n" + "="*70)
print("=== FEATURE ABLATION STUDY RESULTS (grouped by genotype) ===")
print("="*70)
print(ablation_df.to_string(index=False))
print(f"\nSUCCESS: Saved ablation results to: {out_path}")
