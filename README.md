# LeafLens — Physics-Informed ML for CRISPR Stomatal Engineering in Rice

A physics-informed machine-learning framework that predicts leaf gas exchange
(carbon assimilation $A$ and stomatal conductance $g_s$) in CRISPR stomatal-engineered
rice, built on a harmonized 165-measurement dataset compiled from three published
studies and validated with genotype-grouped cross-validation.

**Authors:** P. Thrishna Sai, N. Jenika — Centre for Biotechnology, JNTUH-UCESTH, Hyderabad

---

## What this project does

CRISPR editing of stomatal-patterning genes (`OsEPF1`, `OsEPFL10`, `OsSTOMAGEN`) can
reduce the density of stomatal pores on a rice leaf, cutting water loss. The design
question is *how much* reduction is appropriate: fewer pores save water but also
restrict the CO₂ supply that drives photosynthesis.

LeafLens models that trade-off. It combines a **light-response saturation prior** from
photosynthesis physiology with a **ridge-regression residual learner**:

```
y = y_max · PPFD/(PPFD + K_m) · S^β   +   f_ridge(S, PPFD, VPD, drought, T, CO₂)
        └────────── physics prior ──────────┘   └──────── learned residual ────────┘
```

where `S` is stomatal density relative to wild type.

### Headline results (genotype-grouped CV, 20 randomized fold assignments)

| Target | R² | Variance ceiling | % of achievable |
|---|---|---|---|
| Assimilation `A` | **0.531 ± 0.166** | 0.830 | 64% |
| Conductance `g_s` | **0.362 ± 0.152** | 0.501 | 72% |

The physics prior earns its place: it improves R² by **+0.116 ± 0.091** (`A`) and
**+0.042 ± 0.023** (`g_s`) over an otherwise identical model without it, winning in
**20 of 20** paired repeats for both targets.

Within the validated domain, a **30% stomatal-density reduction** is predicted to retain
**94.9%** of wild-type assimilation while reducing conductance to **92.0%** — water loss
falls faster than carbon gain, which is the quantitative basis for stomatal engineering.

---

## Three findings that constrain how far this can be pushed

These are reported as prominently as the performance numbers, because they bound it.

1. **Intrinsic water-use efficiency (`A/g_s`) is not a learnable target here.** An ANOVA
   intraclass-correlation analysis gives it an R² ceiling of **0.00** — its replicate
   noise is 2.7× its genotype effect. Modelling `A` and `g_s` separately works; modelling
   their ratio cannot. We recommend running this diagnostic *before* modelling any
   derived/ratio target.

2. **Cross-study transfer is not demonstrated.** Leave-one-study-out R² is strongly
   negative, and normalizing to within-study wild-type controls does **not** repair it
   (−0.28 for `A`, −0.04 for `g_s`). With three studies these estimates are unstable
   enough that no signed value should be trusted.

3. **The decision-relevant range is nearly unmeasured.** Across the whole published
   literature, stomatal-reduction levels jump from 28.5% to 58.0% — a 29.5-point gap —
   and the entire 30–70% band rests on a **single genotype** (5 of 165 measurements).
   Predictive reliability also declines with reduction severity (Spearman ρ = −0.50 for
   `A`, −0.58 for `g_s`).

---

## Repository layout

```
scripts/
  parse_digitized_data.py     # build bio_master.csv from digitized figure data
  build_feautures.py          # feature engineering + climate PPFD conversion
  train_final_model.py        # FINAL model: physics prior + ridge, all validation
  run_supporting_analyses.py  # reproduces every remaining number in the paper
  make_final_figures.py       # all manuscript figures
  run_eda.py                  # exploratory plots + extrapolation diagnostic
  download_climate.py         # NASA POWER retrieval
  train_models.py             # legacy iWUE-target pipeline (superseded; see paper §4.7)
  optimize_sweep.py, run_shap.py, run_ablation.py   # legacy analyses
data/
  biological/raw/             # WebPlotDigitizer exports from source figures
  processed/training_data.csv # final 165-row feature matrix
  climate/                    # NASA POWER daily records, 5 Telangana districts
outputs/tables/               # all result tables (CSV/JSON)
outputs/figures/              # all generated figures
paper/
  main.tex                    # manuscript (Springer Nature sn-jnl class)
  main_llncs_render.tex       # locally-compilable rendering (identical content)
  LeafLens_paper.pdf          # compiled PDF
papers/                       # source publications (PDFs)
PROJECT_NOTES.md              # full methodology, corrections log, and rationale
```

## Reproducing

```bash
python scripts/parse_digitized_data.py      # rebuild dataset from digitized figures
python scripts/build_feautures.py           # feature matrix + climate conversion
python scripts/train_final_model.py         # model, validation, ceiling analysis
python scripts/run_supporting_analyses.py   # leakage, transfer, coverage analyses
python scripts/make_final_figures.py        # figures
```

Every quantitative claim in the manuscript is produced by one of these scripts and
written to `outputs/tables/`.

## Data provenance

All gas-exchange values are digitized from published figures using WebPlotDigitizer, or
taken from values stated numerically in the source text. Each row carries an `A_Source`
flag: `digitized`, `digitized_genotype_mean`, or `estimated_regression` (59 rows where the
source study reported conductance but not paired assimilation under drought; estimated via
a regression fitted on that study's own steady-state data, R²=0.931).

Sources: Caine et al. 2019 (New Phytologist, [10.1111/nph.15344](https://doi.org/10.1111/nph.15344)) ·
Karavolias et al. 2023 (Plant Physiology, [10.1093/plphys/kiad183](https://doi.org/10.1093/plphys/kiad183)) ·
Karavolias et al. 2024 (Plant Biotechnology Journal, [10.1111/pbi.14464](https://doi.org/10.1111/pbi.14464)) ·
climate from [NASA POWER](https://power.larc.nasa.gov/).

## Status

This is a research prototype and a methods contribution, not a deployment-ready trait-design
tool. See `PROJECT_NOTES.md` for the full correction history and the reasoning behind each
modelling decision.
