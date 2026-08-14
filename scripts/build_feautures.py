import os
import pandas as pd
import numpy as np

os.makedirs('data/processed', exist_ok=True)

# 1. Update Climate PPFD to Peak Midday Light
climate = pd.read_csv('data/climate/telangana_climate.csv')
climate['PPFD_estimated_umol'] = climate['ALLSKY_SFC_SW_DWN'] * 200.0  # Midday peak PAR
climate.to_csv('data/climate/telangana_climate.csv', index=False)

# 2. Load Biological Master Data
bio = pd.read_csv('data/biological/bio_master.csv')

print("=== Phase 4: Feature Engineering (Clean Intrinsic Target) ===")

# --- A. ATMOSPHERIC PHYSICS FEATURES ---
T = bio['Temperature_C']
RH = bio['RH_Pct'].fillna(60.0)

# VPD (Tetens Equation)
es = 0.6108 * np.exp(17.27 * T / (T + 237.3))
ea = es * (RH / 100.0)
bio['VPD_kPa'] = es - ea

# --- B. INTERACTION & NON-LINEAR FEATURES ---
bio['VPD_x_Reduction'] = bio['VPD_kPa'] * bio['Relative_Stomatal_Reduction_Pct']
bio['PPFD_x_Reduction'] = (bio['PPFD_umol'] * bio['Relative_Stomatal_Reduction_Pct']) / 1000.0
bio['Reduction_Squared'] = bio['Relative_Stomatal_Reduction_Pct'] ** 2

# --- C. CATEGORICAL & STUDY DUMMIES ---
bio['Is_Drought'] = (bio['Water_Treatment'] != 'Well_Watered').astype(int)

# Study dummies (one-hot encoding)
study_dummies = pd.get_dummies(bio['Paper_ID'], prefix='Study', drop_first=False)
bio['Study_Karavolias2023'] = study_dummies['Study_Karavolias2023'].astype(int)
bio['Study_Karavolias2024'] = study_dummies['Study_Karavolias2024'].astype(int)

# --- D. FINAL CLEAN FEATURE MATRIX ---
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

TARGET = 'WUE_intrinsic'

# Clean dataset
training_df = bio.dropna(subset=FEATURE_COLS + [TARGET]).copy()

# Save final feature matrix
out_path = 'data/processed/training_data.csv'
training_df.to_csv(out_path, index=False)

print("="*60)
print(f"SUCCESS: Feature matrix built with {len(training_df)} rows and {len(FEATURE_COLS)} features!")
print("Saved to:", out_path)
print("\n--- Feature List ---")
for idx, col in enumerate(FEATURE_COLS, 1):
    print(f"  {idx}. {col}")
print(f"\nTarget Variable: {TARGET} (Mean: {training_df[TARGET].mean():.2f}, Std: {training_df[TARGET].std():.2f})")