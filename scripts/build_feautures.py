import os
import pandas as pd
import numpy as np

os.makedirs('data/processed', exist_ok=True)

# 1. Recompute Climate PPFD from NASA POWER shortwave radiation
#
# FIX: previously this line overwrote the climate PPFD with
# `ALLSKY_SFC_SW_DWN * 200.0`, treating a daily total in MJ m-2 day-1 as if it were an
# instantaneous W m-2 reading. That produced daytime PPFD "estimates" up to ~5600 umol
# m-2 s-1 - physically impossible (full tropical noon sun is ~2000-2200 umol m-2 s-1).
# It also silently overwrote the different (and also unvalidated) x3.3 conversion
# applied upstream in download_climate.py, so two inconsistent PPFD values existed
# across the pipeline.
#
# We now use a single, standard, documented conversion from daily-total shortwave
# radiation (MJ m-2 day-1) to a daytime-average PPFD (umol m-2 s-1):
#   PPFD = SW_down[MJ/m2/day] * 1e6[J/MJ] * PAR_FRACTION * QUANTUM_FACTOR[umol/J] / DAYLIGHT_S
# with PAR_FRACTION = 0.45 (fraction of broadband shortwave that is photosynthetically
# active, McCree 1972) and QUANTUM_FACTOR = 4.6 umol/J (standard PAR conversion), and
# DAYLIGHT_S = 12h = 43200 s assumed daylight duration (Telangana ~17-19N; actual
# day length varies seasonally by roughly +/-1h, not modeled here).
PAR_FRACTION = 0.45
QUANTUM_FACTOR = 4.6  # umol photons per J of PAR
DAYLIGHT_SECONDS = 12 * 3600

climate = pd.read_csv('data/climate/telangana_climate.csv')
climate['PPFD_estimated_umol'] = (
    climate['ALLSKY_SFC_SW_DWN'] * 1e6 * PAR_FRACTION * QUANTUM_FACTOR / DAYLIGHT_SECONDS
)
climate.to_csv('data/climate/telangana_climate.csv', index=False)
print(f"Recomputed climate PPFD. Range: {climate['PPFD_estimated_umol'].min():.0f}"
      f" - {climate['PPFD_estimated_umol'].max():.0f} umol m-2 s-1"
      f" (mean {climate['PPFD_estimated_umol'].mean():.0f})")

# 2. Load Biological Master Data
bio = pd.read_csv('data/biological/bio_master.csv')

print("=== Phase 4: Feature Engineering (Clean Intrinsic Target) ===")

# --- A. ATMOSPHERIC PHYSICS FEATURES ---
T = bio['Temperature_C']
RH = bio['RH_Pct'].fillna(60.0)

# VPD (Tetens/Murray approximation of saturation vapor pressure; see Allen et al. 1998,
# FAO Irrigation & Drainage Paper 56, Eq. 11)
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

# Clean dataset (duplicate rows were already dropped in parse_digitized_data.py)
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
print(f"\nA_Source breakdown in final training set:")
print(training_df['A_Source'].value_counts())
