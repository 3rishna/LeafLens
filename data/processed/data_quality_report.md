# Data Quality Audit Report — Biological Dataset

**Generated:** Phase 1 Complete
**File Audited:** 

---

## 1. Summary Overview
- **Total Records:** 168
- **Papers Included:** Caine2019, Karavolias2023, Karavolias2024
- **Cultivars Covered:** IR64, Nipponbare, Kitaake
- **Genes Targeted:** OsEPF1, OsEPFL9/10, OsSTOMAGEN

---

## 2. Scientific & Logical Integrity Checks
| Check | Requirement | Result | Status |
| :--- | :--- | :--- | :--- |
| **Negative WUE** | Should be 0 | 0 rows | ✅ PASS |
| **Zero/Negative Stomatal Density** | Should be 0 | 0 rows | ✅ PASS |
| **WT Stomatal Reduction == 0%** | Should be 0 errors | 0 errors | ✅ PASS |
| **Duplicate Rows** | Should be 0 | 3 duplicates | ⚠️ WARNING |

---

## 3. Variable Ranges & Distributions
- **Relative Stomatal Reduction:** -18.0% to 78.7%
- **Photosynthetic Rate (A):** 1.70 to 30.39 µmol CO₂ m⁻² s⁻¹
- **Stomatal Conductance (gₛ):** 0.035 to 0.494 mol H₂O m⁻² s⁻¹
- **Instantaneous WUE (A/E):** 4.34 to 52.62

---

## 4. Missing Values Audit
- **Paper_ID:** 0 missing (0.0%)
- **DOI:** 0 missing (0.0%)
- **Source:** 0 missing (0.0%)
- **Cultivar:** 0 missing (0.0%)
- **Gene_Target:** 0 missing (0.0%)
- **Modification_Type:** 0 missing (0.0%)
- **Genotype_Line:** 0 missing (0.0%)
- **Stomatal_Density_mm2:** 0 missing (0.0%)
- **WT_Stomatal_Density_mm2:** 0 missing (0.0%)
- **Relative_Stomatal_Reduction_Pct:** 0 missing (0.0%)
- **Photosynthetic_Rate_A:** 0 missing (0.0%)
- **Stomatal_Conductance_gs:** 0 missing (0.0%)
- **Transpiration_Rate_E:** 0 missing (0.0%)
- **WUE_instantaneous:** 0 missing (0.0%)
- **WUE_intrinsic:** 0 missing (0.0%)
- **CO2_ppm:** 0 missing (0.0%)
- **PPFD_umol:** 0 missing (0.0%)
- **Temperature_C:** 0 missing (0.0%)
- **RH_Pct:** 0 missing (0.0%)
- **Water_Treatment:** 0 missing (0.0%)
- **Extraction_Method:** 0 missing (0.0%)

---

## 5. Audit Conclusion
- All core target variables (, , ) passed physical sanity checks.
- Dataset is ready for feature engineering and ML pipeline.
