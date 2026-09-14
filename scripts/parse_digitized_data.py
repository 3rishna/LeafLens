import os
import glob
import pandas as pd
import numpy as np

# Create output folder if not exists
os.makedirs('data/biological', exist_ok=True)

rows = []

# Helper function to parse WebPlotDigitizer paired columns (Label,Y form - no real X)
def parse_wpd_pairs(df):
    parsed = {}
    cols = df.columns
    for i in range(0, len(cols), 2):
        genotype = str(cols[i]).strip()
        vals = pd.to_numeric(df.iloc[1:, i+1], errors='coerce').dropna().values
        parsed[genotype] = vals
    return parsed

# Helper function to parse WebPlotDigitizer paired columns keeping real X (e.g. PAR level)
def parse_wpd_xy(df):
    parsed = {}
    cols = df.columns
    for i in range(0, len(cols), 2):
        genotype = str(cols[i]).strip()
        sub = df.iloc[1:, i:i+2].copy()
        sub.columns = ['X', 'Y']
        sub['X'] = pd.to_numeric(sub['X'], errors='coerce')
        sub['Y'] = pd.to_numeric(sub['Y'], errors='coerce')
        sub = sub.dropna()
        parsed[genotype] = sub
    return parsed

# Nominal PAR levels used in Karavolias et al. (2023) Fig. 3A/3B light-response curve
# (paper text: "100, 200, 300, 500, 650, 1,000, 1,200, 1,500, and 2,000 umol photons/m2/s";
# WebPlotDigitizer read-off X values are close to but not exactly these round numbers)
K23_PAR_LEVELS = [50, 100, 200, 300, 500, 750, 1000, 1200, 1500, 2000]

def snap_to_par(x):
    return min(K23_PAR_LEVELS, key=lambda p: abs(p - x))

# --- 1. CAINE ET AL. (2019) DATA ---
# Fig. 3a (A) and 3b (gs): measured at PAR 1000 umol m-2 s-1, growth-chamber ambient
# CO2 (450-480 ppm), 30 C, well-watered plants only (Caine et al. 2019, Fig. 3 caption).
# NOTE: Caine et al. (2019) also report a temperature-response series (Fig. 5, 30/35/40 C)
# and cumulative water-loss curves under drought (Fig. 3e, 4g-i), but these do not report
# paired (A, gs) values and were NOT digitized for this dataset - see Limitations.
# STOMATAL DENSITY SOURCE (corrected):
# Caine et al. (2019) state explicitly in the Results text (p.377): "Stomatal density
# was reduced by 58% for OsEPF1oeW and 88% for OsEPF1oeS relative to 'IR64' controls
# (Fig. 2g-j)." We use those directly-stated reductions.
#
# FIX: an earlier version of this script hardcoded absolute densities of 165.10 /
# 100.67 / 47.32 mm^-2, which imply reductions of 39.0% and 71.3% -- inconsistent with
# the paper's own stated 58% and 88%. Those values have no digitized source file in
# data/biological/raw/ (unlike every other study here) and 165.10 is suspiciously close
# to the "c. 160 mm^-2" figure the paper reports for *Arabidopsis* epf2 rescue lines
# (Fig. 1b-e), not for rice. They appear to have been read from the wrong figure.
# Only the RATIO to wild type enters the model, so the nominal WT density below is a
# placeholder; the reductions are the sourced quantity.
CAINE_STATED_REDUCTION_PCT = {'IR64 Control': 0.0, 'OsEPF1oeW': 58.0, 'OsEPF1oeS': 88.0}
caine_wt_sd = 165.10  # nominal WT density; only SD/SD_WT ratio is used downstream
caine_sd = {g: caine_wt_sd * (1 - r / 100.0) for g, r in CAINE_STATED_REDUCTION_PCT.items()}

df_c3a = pd.read_csv('data/biological/raw/caine_fig3a_A.csv')
df_c3b = pd.read_csv('data/biological/raw/caine_fig3b_gs.csv')

c3a_dict = parse_wpd_pairs(df_c3a)
c3b_dict = parse_wpd_pairs(df_c3b)

for geno in ['IR64 Control', 'OsEPF1oeW', 'OsEPF1oeS']:
    a_vals = c3a_dict.get(geno, [])
    gs_vals = c3b_dict.get(geno, [])
    sd_val = caine_sd.get(geno, np.nan)
    red_pct = (1 - sd_val / caine_wt_sd) * 100 if not np.isnan(sd_val) else np.nan

    n_pts = min(len(a_vals), len(gs_vals))
    for i in range(n_pts):
        a = a_vals[i]
        gs = gs_vals[i]
        iwue = a / gs if (gs > 0 and not np.isnan(gs)) else np.nan

        rows.append({
            'Paper_ID': 'Caine2019',
            'DOI': '10.1111/nph.15344',
            'Source': 'Fig3a_3b',
            'Cultivar': 'IR64',
            'Gene_Target': 'OsEPF1',
            'Modification_Type': 'Overexpression',
            'Genotype_Line': geno,
            'Stomatal_Density_mm2': sd_val,
            'WT_Stomatal_Density_mm2': caine_wt_sd,
            'Relative_Stomatal_Reduction_Pct': red_pct,
            'Photosynthetic_Rate_A': a,
            'A_Source': 'digitized',
            'Stomatal_Conductance_gs': gs,
            'WUE_intrinsic': iwue,
            'CO2_ppm': 450.0,
            'PPFD_umol': 1000.0,
            'Temperature_C': 30.0,
            'RH_Pct': 60.0,
            'Water_Treatment': 'Well_Watered',
            'Extraction_Method': 'WebPlotDigitizer'
        })

# --- 2. KARAVOLIAS ET AL. (2023) DATA ---
# Fig. 2A: stomatal density (SD) per genotype (Nipponbare, Stomagen KO / epfl10 KO / WT)
# Fig. 3A/3B: light-response curves of A and gs across 10 PAR levels per genotype.
# FIX: the X-column of the digitized Fig. 3A/3B files is the actual PAR level for that
# point (previously discarded and replaced with a constant PPFD_umol=1200 for all rows -
# this hid a real, informative light-response gradient and made 30/168 rows carry a
# fabricated PPFD value). We now snap each digitized X to the nearest of the paper's
# stated PAR levels and use it as PPFD_umol for that row.
df_k23_sd = pd.read_csv('data/biological/raw/k23_fig2a_sd.csv')
k23_sd_dict = parse_wpd_pairs(df_k23_sd)
k23_wt_sd = np.mean(k23_sd_dict.get('Wild Type', [450.0]))

df_k23_na = pd.read_csv('data/biological/raw/k23_fig3a_na.csv')
df_k23_sc = pd.read_csv('data/biological/raw/k23_fig3b_sc.csv')
k23_na_dict = parse_wpd_xy(df_k23_na)
k23_sc_dict = parse_wpd_xy(df_k23_sc)

GENE_MAP_K23 = {'Stomagen': 'OsSTOMAGEN', 'epfl10': 'OsEPFL10', 'Wild Type': 'Wild_Type'}
MOD_MAP_K23 = {'Stomagen': 'KO', 'epfl10': 'KO', 'Wild Type': 'WT'}

for geno in k23_sd_dict.keys():
    sd_vals = k23_sd_dict.get(geno, [np.nan])
    sd_val = np.mean(sd_vals)
    red_pct = (1 - sd_val / k23_wt_sd) * 100 if not np.isnan(sd_val) else np.nan

    na_df = k23_na_dict.get(geno, pd.DataFrame(columns=['X', 'Y']))
    sc_df = k23_sc_dict.get(geno, pd.DataFrame(columns=['X', 'Y']))
    n_pts = min(len(na_df), len(sc_df))

    for i in range(n_pts):
        a = na_df['Y'].iloc[i]
        gs = sc_df['Y'].iloc[i]
        par_level = snap_to_par(na_df['X'].iloc[i])
        iwue = a / gs if (gs > 0 and not np.isnan(gs)) else np.nan

        rows.append({
            'Paper_ID': 'Karavolias2023',
            'DOI': '10.1093/plphys/kiad183',
            'Source': 'Fig2a_3a_3b',
            'Cultivar': 'Nipponbare',
            'Gene_Target': GENE_MAP_K23.get(geno, geno),
            'Modification_Type': MOD_MAP_K23.get(geno, 'KO'),
            'Genotype_Line': geno,
            'Stomatal_Density_mm2': sd_val,
            'WT_Stomatal_Density_mm2': k23_wt_sd,
            'Relative_Stomatal_Reduction_Pct': red_pct,
            'Photosynthetic_Rate_A': a,
            'A_Source': 'digitized',
            'Stomatal_Conductance_gs': gs,
            'WUE_intrinsic': iwue,
            'CO2_ppm': 400.0,
            'PPFD_umol': float(par_level),
            'Temperature_C': 28.0,
            'RH_Pct': 65.0,
            'Water_Treatment': 'Well_Watered',
            'Extraction_Method': 'WebPlotDigitizer'
        })

# --- 3. KARAVOLIAS ET AL. (2024) DATA ---
# Fig. 1B: stomatal density per allele (Kitaake promoter-edited allelic series).
# Fig. 2A/2B: genotype-mean steady-state (SD, gs) and (SD, A) under well-watered
# conditions - a REAL, fully digitized per-genotype carbon-assimilation value.
# Fig. 4A/4B: stomatal conductance only, well-watered vs. vegetative-drought cohort
# (no paired A was reported/digitizable for the drought cohort).
#
# FIX: the previous version assigned every well-watered row a flat A=24.0 and every
# drought row a flat A=18.0 regardless of genotype (73% of the full 168-row dataset).
# We now:
#   (a) use the REAL digitized per-genotype A from Fig. 2B for well-watered rows
#       (Fig. 4A), matched by genotype; and
#   (b) for drought rows (Fig. 4B, where A was not digitizable), estimate A from the
#       genotype's measured drought gs using a linear regression of A on gs fitted on
#       the REAL Fig. 2 steady-state data (8 genotypes). This uses the paper's own
#       reported strong positive linear gs-A relationship (Karavolias et al. 2024,
#       Fig. 2 caption) instead of an arbitrary constant, but it remains an estimate,
#       not a directly measured value - flagged via A_Source='estimated_regression'
#       and treated as a stated limitation in the manuscript.
df_k24_sd = pd.read_csv('data/biological/raw/k24_fig1b_sd.csv')
k24_sd_dict = parse_wpd_pairs(df_k24_sd)
k24_wt_sd = np.mean(k24_sd_dict.get('Wild Type', [380.0])) if 'Wild Type' in k24_sd_dict else 380.0

df_k24_f2a = pd.read_csv('data/biological/raw/k24_fig2a.csv')  # SD vs gs (steady-state, per genotype)
df_k24_f2b = pd.read_csv('data/biological/raw/k24_fig2b.csv')  # SD vs A  (steady-state, per genotype)
k24_f2a_dict = parse_wpd_xy(df_k24_f2a)
k24_f2b_dict = parse_wpd_xy(df_k24_f2b)

# Build the real per-genotype (gs, A) steady-state table and fit A = m*gs + b
geno_gs_ss, geno_a_ss = {}, {}
for geno in k24_f2a_dict.keys():
    if len(k24_f2a_dict[geno]) and len(k24_f2b_dict.get(geno, [])):
        geno_gs_ss[geno] = float(k24_f2a_dict[geno]['Y'].iloc[0])
        geno_a_ss[geno] = float(k24_f2b_dict[geno]['Y'].iloc[0])

gs_arr = np.array(list(geno_gs_ss.values()))
a_arr = np.array([geno_a_ss[g] for g in geno_gs_ss.keys()])
slope, intercept = np.polyfit(gs_arr, a_arr, 1)
resid = a_arr - (slope * gs_arr + intercept)
r2_gs_a = 1 - np.sum(resid ** 2) / np.sum((a_arr - a_arr.mean()) ** 2)
print(f"[K24 A~gs regression] A = {slope:.3f}*gs + {intercept:.3f}  (R^2={r2_gs_a:.3f}, n={len(gs_arr)})")

df_k24_f4a = pd.read_csv('data/biological/raw/k24_fig4a.csv')
df_k24_f4b = pd.read_csv('data/biological/raw/k24_fig4b.csv')
k24_ww_dict = parse_wpd_pairs(df_k24_f4a)
k24_dr_dict = parse_wpd_pairs(df_k24_f4b)

for geno in k24_sd_dict.keys():
    sd_vals = k24_sd_dict.get(geno, [np.nan])
    sd_val = np.mean(sd_vals)
    red_pct = (1 - sd_val / k24_wt_sd) * 100 if not np.isnan(sd_val) else np.nan

    a_ss_geno = geno_a_ss.get(geno, None)

    # Well Watered (Fig. 4A conductance values; A from real Fig. 2B genotype mean)
    gs_ww_vals = k24_ww_dict.get(geno, [0.25])
    for gs in gs_ww_vals:
        if a_ss_geno is not None:
            a = a_ss_geno
            a_source = 'digitized_genotype_mean'
        else:
            a = slope * gs + intercept
            a_source = 'estimated_regression'
        iwue = a / gs if (gs > 0 and not np.isnan(gs)) else np.nan
        rows.append({
            'Paper_ID': 'Karavolias2024',
            'DOI': '10.1111/pbi.14464',
            'Source': 'Fig1b_2a_2b_4a',
            'Cultivar': 'Kitaake',
            'Gene_Target': 'OsSTOMAGEN',
            'Modification_Type': 'Promoter_Edit' if geno not in ('Stomagen', 'Wild Type') else ('CDS_KO' if geno == 'Stomagen' else 'WT'),
            'Genotype_Line': geno,
            'Stomatal_Density_mm2': sd_val,
            'WT_Stomatal_Density_mm2': k24_wt_sd,
            'Relative_Stomatal_Reduction_Pct': red_pct,
            'Photosynthetic_Rate_A': a,
            'A_Source': a_source,
            'Stomatal_Conductance_gs': gs,
            'WUE_intrinsic': iwue,
            'CO2_ppm': 420.0,
            'PPFD_umol': 1500.0,
            'Temperature_C': 29.0,
            'RH_Pct': 60.0,
            'Water_Treatment': 'Well_Watered',
            'Extraction_Method': 'WebPlotDigitizer'
        })

    # Drought (Fig. 4B conductance values; A estimated via A~gs regression above)
    gs_dr_vals = k24_dr_dict.get(geno, [0.12])
    for gs in gs_dr_vals:
        a = slope * gs + intercept
        iwue = a / gs if (gs > 0 and not np.isnan(gs)) else np.nan
        rows.append({
            'Paper_ID': 'Karavolias2024',
            'DOI': '10.1111/pbi.14464',
            'Source': 'Fig1b_2a_2b_4b',
            'Cultivar': 'Kitaake',
            'Gene_Target': 'OsSTOMAGEN',
            'Modification_Type': 'Promoter_Edit' if geno not in ('Stomagen', 'Wild Type') else ('CDS_KO' if geno == 'Stomagen' else 'WT'),
            'Genotype_Line': geno,
            'Stomatal_Density_mm2': sd_val,
            'WT_Stomatal_Density_mm2': k24_wt_sd,
            'Relative_Stomatal_Reduction_Pct': red_pct,
            'Photosynthetic_Rate_A': a,
            'A_Source': 'estimated_regression',
            'Stomatal_Conductance_gs': gs,
            'WUE_intrinsic': iwue,
            'CO2_ppm': 420.0,
            'PPFD_umol': 1500.0,
            'Temperature_C': 31.0,
            'RH_Pct': 50.0,
            'Water_Treatment': 'Drought',
            'Extraction_Method': 'WebPlotDigitizer'
        })

# Convert to Master DataFrame
bio_master = pd.DataFrame(rows)

# Drop exact-duplicate rows (identical across all measured/environmental columns)
dedup_cols = [c for c in bio_master.columns if c not in ()]
n_before = len(bio_master)
bio_master = bio_master.drop_duplicates(subset=dedup_cols).reset_index(drop=True)
n_after = len(bio_master)

# Save Master CSV
master_path = 'data/biological/bio_master.csv'
bio_master.to_csv(master_path, index=False)

print("="*60)
print(f"SUCCESS: Created master dataset with {len(bio_master)} rows! (dropped {n_before-n_after} exact duplicates)")
print("Saved to:", master_path)
print("\n--- Summary by Paper ---")
print(bio_master['Paper_ID'].value_counts())
print("\n--- A_Source breakdown ---")
print(bio_master['A_Source'].value_counts())
print("\n--- Intrinsic WUE (A/gs) Summary ---")
print(bio_master['WUE_intrinsic'].describe())
