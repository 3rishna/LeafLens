import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

os.makedirs('outputs/figures', exist_ok=True)
os.makedirs('data/processed', exist_ok=True)

# Set clean style
sns.set_theme(style='whitegrid')
plt.rcParams.update({'font.size': 11})

# Load datasets
bio = pd.read_csv('data/biological/bio_master.csv')
climate = pd.read_csv('data/climate/telangana_climate.csv')

# Compute experimental VPD on biological data (Tetens Equation)
T_bio = bio['Temperature_C']
RH_bio = bio['RH_Pct'].fillna(60.0) # Assume 60% standard chamber RH if not reported
es_bio = 0.6108 * np.exp(17.27 * T_bio / (T_bio + 237.3))
ea_bio = es_bio * (RH_bio / 100.0)
bio['VPD_kPa'] = es_bio - ea_bio

print("=== Running Phase 3: Exploratory Data Analysis ===")

# --- 1. BIOLOGICAL EDA PLOTS ---

# Fig A: Stomatal Reduction Distribution across Papers
fig, ax = plt.subplots(figsize=(8, 5))
sns.histplot(data=bio, x='Relative_Stomatal_Reduction_Pct', hue='Paper_ID', bins=20, kde=True, ax=ax, palette='Set2')
ax.set_title('Distribution of Relative Stomatal Reduction (%) Across Studies')
ax.set_xlabel('Stomatal Reduction (%)')
ax.set_ylabel('Record Count')
plt.tight_layout()
plt.savefig('outputs/figures/eda_reduction_distribution.png', dpi=300)
plt.close()

# Fig B: Reduction % vs Instantaneous WUE
fig, ax = plt.subplots(figsize=(8, 5))
sns.scatterplot(data=bio, x='Relative_Stomatal_Reduction_Pct', y='WUE_instantaneous', hue='Paper_ID', style='Water_Treatment', s=80, ax=ax, palette='Set2')
ax.set_title('Stomatal Reduction (%) vs Instantaneous Water Use Efficiency (A/E)')
ax.set_xlabel('Stomatal Reduction (%)')
ax.set_ylabel('WUE (A/E)')
plt.tight_layout()
plt.savefig('outputs/figures/eda_reduction_vs_wue.png', dpi=300)
plt.close()

# Fig C: Reduction % vs Photosynthesis (A) and Conductance (gs)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
sns.scatterplot(data=bio, x='Relative_Stomatal_Reduction_Pct', y='Photosynthetic_Rate_A', hue='Paper_ID', ax=ax1, palette='Set2')
ax1.set_title('Stomatal Reduction (%) vs Photosynthesis (A)')
ax1.set_xlabel('Stomatal Reduction (%)')
ax1.set_ylabel('A (umol CO2 m-2 s-1)')

sns.scatterplot(data=bio, x='Relative_Stomatal_Reduction_Pct', y='Stomatal_Conductance_gs', hue='Paper_ID', ax=ax2, palette='Set2')
ax2.set_title('Stomatal Reduction (%) vs Conductance (gs)')
ax2.set_xlabel('Stomatal Reduction (%)')
ax2.set_ylabel('gs (mol H2O m-2 s-1)')
plt.tight_layout()
plt.savefig('outputs/figures/eda_photosynthesis_conductance.png', dpi=300)
plt.close()

# --- 2. CLIMATE EDA PLOTS ---

# Fig D: Monthly VPD Across Telangana Districts
fig, ax = plt.subplots(figsize=(10, 5))
sns.boxplot(data=climate, x='Month', y='VPD_kPa', hue='Season', ax=ax, palette='coolwarm')
ax.set_title('Monthly Vapor Pressure Deficit (VPD) in Telangana (2015-2026)')
ax.set_xlabel('Month')
ax.set_ylabel('VPD (kPa)')
plt.tight_layout()
plt.savefig('outputs/figures/eda_monthly_vpd.png', dpi=300)
plt.close()

# --- 3. EXTRAPOLATION DIAGNOSTIC ---

print("\n=== Running Extrapolation Diagnostic ===")

# Set ambient CO2 for climate
climate['CO2_ppm'] = 420.0

vars_map = [
    ('Temperature_C', 'T2M', 'Temperature (C)'),
    ('CO2_ppm', 'CO2_ppm', 'CO2 Concentration (ppm)'),
    ('PPFD_umol', 'PPFD_estimated_umol', 'PPFD Light (umol m-2 s-1)'),
    ('VPD_kPa', 'VPD_kPa', 'VPD (kPa)'),
]

diag_records = []

for bio_col, clim_col, label in vars_map:
    bio_min, bio_max = bio[bio_col].min(), bio[bio_col].max()
    clim_min = climate[clim_col].quantile(0.05)
    clim_max = climate[clim_col].quantile(0.95)
    
    # Check domain overlap
    in_range = (clim_min >= bio_min * 0.8) and (clim_max <= bio_max * 1.2)
    status = "PASS: Interpolation (Within Domain)" if in_range else "FLAG: Partial Extrapolation"
    
    diag_records.append({
        'Variable': label,
        'Bio_Train_Min': round(bio_min, 2),
        'Bio_Train_Max': round(bio_max, 2),
        'Telangana_5th_Pct': round(clim_min, 2),
        'Telangana_95th_Pct': round(clim_max, 2),
        'Domain_Status': status
    })

diag_df = pd.DataFrame(diag_records)
diag_path = 'data/processed/extrapolation_check.csv'
diag_df.to_csv(diag_path, index=False)

print("\n" + diag_df.to_string(index=False))
print(f"\nSUCCESS: Saved figures to outputs/figures/")
print(f"SUCCESS: Saved extrapolation diagnostic to {diag_path}")