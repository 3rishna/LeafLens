# LeafLens — Project Notes: Methodology, Corrections, and Rationale

This document explains what the project does, why each modelling decision was made, and
what was found wrong and fixed along the way. It is deliberately explicit about the
errors, because several of them are instructive and because the corrections changed the
paper's conclusions.

---

## 1. The scientific problem

Stomata are microscopic pores on a leaf. They admit CO₂ for photosynthesis and lose water
vapour by transpiration — the same opening does both, so the plant cannot increase carbon
gain without paying in water. Under the high temperatures and high vapour-pressure deficit
of a Telangana pre-monsoon season, that cost is severe.

CRISPR-Cas9 editing of the Epidermal Patterning Factor gene family (`OsEPF1`, `OsEPFL10`,
`OsSTOMAGEN`) can reduce how many stomata a leaf develops. Published work establishes this
works. What it does not provide is a quantitative answer to the engineering question: for
a given climate, how large a reduction is worth making before the photosynthetic cost
outweighs the water saving?

LeafLens is an attempt to answer that from the published literature alone.

---

## 2. The data

165 leaf gas-exchange measurements compiled from three studies:

| Study | Cultivar | Gene target | n | Conditions |
|---|---|---|---|---|
| Caine et al. 2019 | IR64 | `OsEPF1` overexpression | 15 | PAR 1000, 30 °C, well-watered |
| Karavolias et al. 2023 | Nipponbare | `OsEPFL10` / `OsSTOMAGEN` KO | 30 | PAR 50–2000 (light-response curve), 28 °C |
| Karavolias et al. 2024 | Kitaake | `OsSTOMAGEN` promoter edits | 120 | PAR 1500, 29/31 °C, watered + drought |

Spanning **14 genotype lines** (12 distinct names; `stomagen` and wild type each appear in
two different cultivar backgrounds and are biologically distinct lines).

Values were digitized from published figures with WebPlotDigitizer, or read from values
stated numerically in the source text. Each row carries an `A_Source` provenance flag.
Climate data is 11.5 years of daily NASA POWER records for five Telangana districts.

---

## 3. The model

### Physics prior

A saturating light-response curve, scaled by relative stomatal density:

```
ŷ_phys = y_max · PPFD/(PPFD + K_m) · S^β        where S = 1 − reduction/100
```

The saturating term is the standard description of light-limited assimilation. The `S^β`
term expresses supply limitation by pore density, with `β` *estimated from data* rather
than assumed proportional. Parameters are refit on the training fold only, never on the
held-out fold.

Fitted on the full dataset:

```
A  = 20.51 · PPFD/(PPFD + 198) · S^0.046
gs = 0.291 · PPFD/(PPFD + 167) · S^0.130
```

Both half-saturation constants sit in the expected range for C3 light-response curves.
The exponents are the biologically interesting part: `β_gs ≈ 2.8 × β_A`, meaning
conductance falls substantially faster than assimilation as density drops — which is
precisely why stomatal engineering can work. Both exponents are well below 1, so neither
quantity scales proportionally with anatomical pore density.

### Residual learner

Ridge regression (α = 1) on `ε = y − ŷ_phys`, over
`(S, PPFD, VPD, drought, temperature, CO₂)`.

**Why ridge, not gradient boosting?** Under genotype-grouped validation the model must
predict a genotype whose stomatal-density value it has never seen. Tree ensembles produce
piecewise-constant fits and cannot interpolate across a held-out level of the principal
continuous predictor; a linear residual can. Empirically every tree variant was worse and
far less stable (SDs up to 1.4 versus 0.17 for ridge).

### Validation

- **Genotype-grouped 5-fold CV**, repeated over **20 randomized group→fold assignments**
  (a single split is high-variance with only 14 groups). Primary metric.
- **Leave-one-study-out CV** — cross-domain transfer test.
- **Leave-one-genotype-out** — per-genotype reliability breakdown.
- **Paired comparison** of hybrid vs. no-physics on *identical* folds, to isolate the
  prior's contribution.
- Shuffled (ungrouped) CV is computed **only** to quantify leakage, never as a result.

---

## 4. Target selection — the most consequential decision

The natural target is intrinsic water-use efficiency, `iWUE = A/gs`, since that is the
quantity of agronomic interest. It is also unlearnable from this data, and we can show
that before fitting anything.

A predictor built from genotype and environment features can only distinguish observations
that differ in those features; it cannot resolve replicate scatter among measurements
sharing identical feature values. That bounds the achievable R². Computing this bound with
the one-way random-effects ANOVA intraclass correlation:

| Target | R² ceiling | Irreducible noise |
|---|---|---|
| `A` | 0.830 | 17% |
| `gs` | 0.501 | 50% |
| **`A/gs`** | **0.000** | **100%** |

For `iWUE` the between-genotype signal (SD 0.087) is **2.7× smaller** than the
within-genotype replicate scatter (SD 0.238). A ratio of two independently noisy
measurements compounds the noise of both. Empirically: direct regression gives R² = −0.40,
and deriving the ratio from separately predicted `A` and `gs` gives −0.36.

**Recommendation for similar work:** compute this ceiling before modelling any ratio,
index, or derived target. It costs nothing and bounds what any subsequent effort can
achieve. Use the ANOVA ICC, not a naive between/total sum-of-squares ratio — see §5.2.

---

## 5. Corrections log

Each of these was found by re-auditing work that had already been "finished". They are
recorded because several changed the conclusions.

### 5.1 Data errors

**Hardcoded photosynthesis values (73% of the dataset).** The original pipeline assigned
every Karavolias 2024 row a flat `A` (24.0 well-watered, 18.0 drought) regardless of
genotype, while the target was `A/gs`. Real per-genotype assimilation existed in
already-digitized but unused files (`k24_fig2a.csv`, `k24_fig2b.csv`) from that paper's
Fig. 2B. Now used. For the drought cohort, where no paired `A` was reported, values are
estimated from measured `gs` via a regression fitted on that study's own steady-state data
(R² = 0.931, n = 8) and flagged as `estimated_regression`. Imputation dropped from 73% to
36%, and from an arbitrary constant to a data-derived estimate.

**Fabricated constant light level.** Karavolias 2023 Fig. 3A/3B is a genuine light-response
curve across ten PAR levels, and the digitized files retained the true PAR on their x-axis
— but the pipeline discarded it and assigned a constant PPFD of 1200 to all 30 rows. This
erased a real experimental gradient and replaced it with noise. Now uses the real per-row
PAR value.

**Wrong stomatal densities for Caine et al.** The pipeline hardcoded densities implying
39% and 71% reductions. The source paper states plainly: *"Stomatal density was reduced by
58% for OsEPF1oeW and 88% for OsEPF1oeS relative to 'IR64' controls."* The hardcoded WT
value (165.10) is suspiciously close to the "c. 160 mm⁻²" the paper reports for
*Arabidopsis* rescue lines — it appears to have been read from the wrong figure. There was
no `caine_*_sd.csv` digitized file, unlike every other study. Now uses the stated values.

*This correction mattered:* it moved a genotype to 58% reduction, invalidating the earlier
claim that no data existed between 40% and 70%.

**Climate PPFD unit error.** `build_feautures.py` multiplied NASA POWER's daily-total
shortwave irradiance (MJ m⁻² day⁻¹) by 200, producing "PPFD" up to 5638 µmol m⁻² s⁻¹ —
roughly 2.5× the physical maximum of full tropical noon sun, as a *daily* figure. Replaced
with a documented conversion (PAR fraction 0.45, quantum factor 4.6 µmol J⁻¹, 12-h
photoperiod), giving a plausible 51–1351 µmol m⁻² s⁻¹.

**Three duplicate rows** dropped.

### 5.2 Methodological errors

**Cross-validation leakage.** The original 5-fold CV shuffled all rows without grouping by
genotype, so replicate measurements of the same genotype appeared in both training and test
folds. Measured directly, holding everything else fixed:

| Target | Shuffled R² | Genotype-grouped R² | Inflation |
|---|---|---|---|
| `A` | +0.686 | +0.464 | **+0.222** |
| `gs` | +0.491 | +0.314 | **+0.177** |
| `A/gs` | −0.001 | −0.397 | **+0.396** |

**Biased variance ceiling.** The ceiling was first computed as a between/total
sum-of-squares ratio. That is biased upward whenever a cell has a single replicate: a
singleton has zero within-cell sum of squares by construction, so it appears "perfectly
explained" while carrying no information about noise. 30 of 49 cells here are singletons.
Switching to the ANOVA ICC changed the ceilings from 0.877/0.641/0.213 to
**0.830/0.501/0.000**.

**Inconsistent hyperparameters.** Three mutually inconsistent configurations existed across
the manuscript text, the training script and the saved model. Now one configuration is used
everywhere. Ridge α was fixed after a sensitivity check across α ∈ [0.1, 30] rather than
nested tuning — results are stable across that range but α was not formally optimized.

**Broken scripts.** `run_ablation.py` and `run_eda.py` referenced a target column
(`WUE_instantaneous`) that does not exist in the dataset and would raise `KeyError`.

**Fabricated citation.** Karavolias et al. 2024 was cited as *Global Change Biology* 30(1)
e17100. It is *Plant Biotechnology Journal* 22, 3442–3452 — verified against the DOI in the
source PDF.

**Unreproducible numbers.** Several values in the manuscript came from ad-hoc exploratory
runs with no committed script. `run_supporting_analyses.py` now reproduces every remaining
number and writes them to `outputs/tables/supporting_analyses.json`.

### 5.3 A claim that reversed under scrutiny

An exploratory analysis suggested that normalizing to within-study wild-type controls
rescued cross-study transfer (LOSO R² of +0.15 for `A`, +0.07 for `gs`). Re-run rigorously
with a pre-specified minimal feature set, the same test gives **−0.28** and **−0.04**.
The sign flipped on an arbitrary modelling choice.

This is recorded in the paper as a caution against our own earlier analysis. With three
studies, leave-one-study-out rests on three folds and is unstable enough that no
configuration-specific value should be trusted. The honest summary is *cross-study transfer
is not demonstrated*, rather than either signed estimate.

---

## 6. What would most improve this

In order of expected value:

1. **Genotypes in the 30–70% reduction band.** The entire published literature has one,
   contributing 5 measurements. This is where a practical optimum would lie and it is
   essentially unmeasured.
2. **Shared-protocol phenotyping across temperature and VPD ranges that overlap field
   conditions**, with a wild-type control in every environment. All current source data sits
   at 28–31 °C; every Telangana district-season scenario is an extrapolation.
3. **More genotypes at the severe end**, where reliability currently collapses.
4. **A hierarchical model with study-level random effects**, which would use the
   cross-study structure more efficiently than post-hoc normalization.
5. Coupling validated `A` and `gs` predictions to a canopy or crop-growth model, to connect
   leaf-level trade-offs to season-scale yield and water budgets.

---

## 7. Robustness: the two residual risks, quantified

Two threats were previously disclosed but unmeasured. Both are now quantified
(`scripts/run_robustness_checks.py`).

### Digitization error — measured, and shown not to matter

The x-axis of the Karavolias 2023 light-response figures corresponds to PAR levels stated
numerically in that paper's text, so deviation of each digitized x-reading from its nominal
level is **pure reading error**. Across 60 such points:

| statistic | reading error (% of axis span) |
|---|---|
| mean | 0.19% |
| 95th percentile | 0.41% |
| maximum | 0.45% |

Injecting Gaussian noise into every digitized quantity and re-running the pipeline:

| injected noise | A R² | gs R² |
|---|---|---|
| 0% (baseline) | 0.495 | 0.314 |
| 0.41% (measured) | 0.496 | 0.337 |
| 2% | 0.488 | 0.325 |
| 5% (~12× measured) | 0.447 | 0.327 |
| 10% (~25× measured) | 0.375 | 0.271 |

Conclusions are insensitive to digitization quality until roughly 25× the measured error.
What this does *not* capture: independent re-digitization by a second operator, which would
also measure operator bias rather than reading precision alone.

### Selection optimism — measured by nested cross-validation

Model class, feature set and ridge penalty were chosen by comparing validation scores on
this dataset. Nested CV runs that entire search (24 configurations) inside an inner loop on
outer-training data only, scoring on an outer fold that informed no choice:

| target | standard R² | nested (unbiased) R² | selection optimism |
|---|---|---|---|
| A | 0.495 | 0.428 ± 0.644 | **+0.067** |
| gs | 0.314 | 0.173 ± 0.573 | **+0.141** |

Optimism is real, larger for the noisier target, and small enough that both nested estimates
remain positive. Two supporting observations:

- The inner loop, which has no knowledge of our choices, **independently selected the
  physics-informed ridge architecture in most outer folds** (28/47 for A, 26/46 for gs) —
  the architecture is not an artifact of our search.
- A **permutation test** (pipeline re-run against shuffled targets) gives a null centred at
  R² ≈ −0.10 with a 95th percentile of ≈ 0.00. No permutation of 30 approached the observed
  performance for either target, p < 0.001.

Not nested: the choice of *target* (A and gs rather than A/gs), because R² is not comparable
across different response variables. That decision rests on the variance-ceiling analysis,
which is computed from replicate structure alone without fitting a model and so consumes no
validation information — but it remains a choice made with knowledge of this dataset, and
only independent replication can fully rule out dataset-specific tailoring.

---

## 8. Honest scope statement

This is a methods contribution and a research prototype:

- It predicts `A` and `gs` within a moderate-reduction, growth-chamber domain at roughly
  two-thirds of the achievable ceiling, with a physics prior that demonstrably helps.
- It does **not** provide a validated optimal stomatal-density target for field deployment.
- It does **not** transfer to unseen studies, cultivars, or field climates.
- Selection optimism is measured, not assumed: nested CV puts it at +0.07 (A) and +0.14
  (gs), so headline values should be discounted accordingly. Permutation testing rejects
  the null at p < 0.001 for both targets, and digitization error is immaterial at the
  measured precision (§7).
- What remains genuinely open: independent re-digitization by a second operator, and
  external replication on a dataset not used to make any modelling choice.
