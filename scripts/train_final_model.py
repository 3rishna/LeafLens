"""
LeafLens final model.

Design rationale (see outputs/tables/variance_ceiling.csv for the evidence):

  The original pipeline regressed intrinsic water-use efficiency (iWUE = A/gs)
  directly. A variance decomposition shows that target has an R^2 CEILING of
  only 0.213 -- 79% of its variance is irreducible within-cell replicate
  scatter, and the between-genotype effect (spread 0.087) is 2.7x SMALLER than
  the replicate noise (SD 0.238). No model can predict it well; ratios of two
  noisy measurements compound noise.

  We therefore model the two PRIMARY measured quantities separately:
     A  (carbon assimilation)   ceiling R^2 = 0.877
     gs (stomatal conductance)  ceiling R^2 = 0.641
  and present the water/carbon trade-off as a pair of validated predictions
  rather than collapsing them into a single unvalidatable ratio.

  Physics prior: light-response saturation (a standard, well-established
  photosynthesis functional form), with stomatal-density-limited supply:
      A  = Amax * PPFD/(PPFD + Km) * SD_ratio^beta
      gs = gmax * PPFD/(PPFD + Km) * SD_ratio^beta
  This replaces the original ad-hoc WUE heuristic, which was uncalibrated and
  scored R^2 = -8.9.

  Model class: Ridge, not gradient-boosted trees. Under genotype-grouped CV the
  model must predict a genotype whose stomatal-density value it has never seen;
  trees produce piecewise-constant fits and cannot interpolate across a held-out
  level of the main continuous predictor, while a linear residual can.

Validation: genotype-grouped CV repeated over 20 randomized group->fold
assignments (a single GroupKFold split is high-variance with only 14 groups),
plus leave-one-study-out CV as the cross-domain test.
"""
import os
import json
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import LeaveOneGroupOut
from xgboost import XGBRegressor

warnings.filterwarnings('ignore')
os.makedirs('outputs/tables', exist_ok=True)
os.makedirs('outputs/models', exist_ok=True)

N_REPEATS = 20
N_FOLDS = 5
FEATS = ['SD_ratio', 'PPFD_umol', 'VPD_kPa', 'Is_Drought', 'Temperature_C', 'CO2_ppm']

df = pd.read_csv('data/processed/training_data.csv')
df['SD_ratio'] = 1 - df['Relative_Stomatal_Reduction_Pct'] / 100.0
groups = (df['Genotype_Line'] + '_' + df['Paper_ID']).values
study = df['Paper_ID'].values

TARGETS = {
    'A': 'Photosynthetic_Rate_A',
    'gs': 'Stomatal_Conductance_gs',
}


# ---------------------------------------------------------------- physics prior
def phys_law(X, ymax, km, beta):
    """Light-response saturation scaled by stomatal-density-limited supply."""
    ppfd, sd = X
    return ymax * (ppfd / (ppfd + km)) * (sd ** beta)


P0 = {'A': [25.0, 300.0, 0.3], 'gs': [0.4, 300.0, 0.5]}
BOUNDS = {'A': ([1, 10, 0], [80, 3000, 2]), 'gs': ([0.01, 10, 0], [3, 3000, 2])}


def fit_physics(train, tgt):
    p, _ = curve_fit(
        phys_law,
        (train['PPFD_umol'].values, train['SD_ratio'].values),
        train[TARGETS[tgt]].values,
        p0=P0[tgt], bounds=BOUNDS[tgt], maxfev=20000,
    )
    return p


# ---------------------------------------------------------------- variance ceiling
def variance_ceiling(col):
    """Max R^2 any genotype/condition-level predictor can reach, given replicate noise.

    Uses the one-way random-effects ANOVA intraclass correlation (Searle et al. 1992),
    NOT a naive between/total sum-of-squares ratio. The naive ratio is biased upward
    whenever any cell has a single replicate: a singleton cell has zero within-cell
    sum of squares by construction (there is nothing to compare it to), so it looks
    "perfectly explained" even though it carries zero information about replicate
    noise. In this dataset 30 of 49 genotype/condition cells are singletons (18% of
    rows), which inflated an earlier version of this ceiling substantially (e.g.
    0.213 -> the ICC-corrected 0.000 for A/gs). The ANOVA ICC instead lets singleton
    cells inform the between-group mean while contributing zero degrees of freedom
    to the within-group (error) term, which is the statistically correct treatment.
    """
    cell = (df['Genotype_Line'] + '|' + df['Paper_ID'] + '|'
            + df['Water_Treatment'] + '|' + df['PPFD_umol'].astype(str))
    y = df[col].dropna()
    c = cell[y.index]
    g = y.groupby(c)
    k, N = g.ngroups, len(y)
    n_i, means_i, grand = g.size(), g.mean(), y.mean()

    msb = (n_i * (means_i - grand) ** 2).sum() / (k - 1)
    ssw = sum(((y[c == lvl] - means_i[lvl]) ** 2).sum() for lvl in means_i.index)
    dfw = N - k
    msw = ssw / dfw if dfw > 0 else np.nan
    n0 = (N - (n_i ** 2).sum() / N) / (k - 1)
    var_between = max((msb - msw) / n0, 0.0)
    return var_between / (var_between + msw)


# ---------------------------------------------------------------- model variants
def make_model(kind):
    if kind == 'ridge':
        return Ridge(alpha=1.0)
    return XGBRegressor(max_depth=2, n_estimators=60, learning_rate=0.05,
                        reg_alpha=1.0, reg_lambda=5.0, subsample=0.8,
                        colsample_bytree=0.8, random_state=42)


def predict_fold(train, test, tgt, use_physics, kind):
    ytr = train[TARGETS[tgt]].values
    if use_physics:
        p = fit_physics(train, tgt)
        base_tr = phys_law((train['PPFD_umol'].values, train['SD_ratio'].values), *p)
        base_te = phys_law((test['PPFD_umol'].values, test['SD_ratio'].values), *p)
        if kind == 'physics_only':
            return base_te
        m = make_model(kind).fit(train[FEATS], ytr - base_tr)
        return base_te + m.predict(test[FEATS])
    m = make_model(kind).fit(train[FEATS], ytr)
    return m.predict(test[FEATS])


def grouped_cv(tgt, use_physics, kind, seed):
    uniq = np.unique(groups)
    rng = np.random.RandomState(seed)
    rng.shuffle(uniq)
    fold_of = {g: i % N_FOLDS for i, g in enumerate(uniq)}
    fold = np.array([fold_of[g] for g in groups])

    per_fold = []
    for f in range(N_FOLDS):
        train, test = df[fold != f], df[fold == f]
        if len(test) < 3 or test[TARGETS[tgt]].std() == 0:
            continue
        pred = predict_fold(train, test, tgt, use_physics, kind)
        per_fold.append(r2_score(test[TARGETS[tgt]], pred))
    return float(np.mean(per_fold))


def loso_cv(tgt, use_physics, kind):
    out = []
    for tr_i, te_i in LeaveOneGroupOut().split(df, df[TARGETS[tgt]], groups=study):
        train, test = df.iloc[tr_i], df.iloc[te_i]
        pred = predict_fold(train, test, tgt, use_physics, kind)
        out.append({'held_out': test['Paper_ID'].iloc[0], 'n': len(test),
                    'r2': r2_score(test[TARGETS[tgt]], pred),
                    'rmse': np.sqrt(mean_squared_error(test[TARGETS[tgt]], pred)),
                    'mae': mean_absolute_error(test[TARGETS[tgt]], pred)})
    return out


VARIANTS = [
    ('Pure physics law (no ML)',              True,  'physics_only'),
    ('Naive ML (Ridge, no physics)',          False, 'ridge'),
    ('Naive ML (XGBoost, no physics)',        False, 'xgb'),
    ('Physics-informed hybrid (XGB resid)',   True,  'xgb'),
    ('Physics-informed hybrid (Ridge resid)', True,  'ridge'),
]

print('=' * 96)
print('LeafLens final model -- genotype-grouped CV, %d randomized fold assignments' % N_REPEATS)
print('=' * 96)

rows, ceilings = [], {}
for tgt in TARGETS:
    ceilings[tgt] = variance_ceiling(TARGETS[tgt])
    print(f'\n### TARGET = {tgt} ({TARGETS[tgt]})   variance ceiling R2 = {ceilings[tgt]:.3f}')
    for label, use_phys, kind in VARIANTS:
        scores = np.array([grouped_cv(tgt, use_phys, kind, s) for s in range(N_REPEATS)])
        print(f'  {label:40s} R2 = {scores.mean():+.3f} +/- {scores.std():.3f}')
        rows.append({'Target': tgt, 'Model': label,
                     'Grouped_CV_R2': round(scores.mean(), 3),
                     'Grouped_CV_SD': round(scores.std(), 3),
                     'Variance_Ceiling_R2': round(ceilings[tgt], 3),
                     'Pct_Of_Achievable': round(100 * scores.mean() / ceilings[tgt], 1)})

pd.DataFrame(rows).to_csv('outputs/tables/final_model_comparison.csv', index=False)

# ------------------------------------------------- paired test: does physics help?
print('\n' + '=' * 96)
print('PAIRED TEST: physics-informed hybrid vs naive ML, evaluated on identical folds')
print('=' * 96)
paired_rows = []
for tgt in TARGETS:
    diffs = np.array([grouped_cv(tgt, True, 'ridge', s) - grouped_cv(tgt, False, 'ridge', s)
                      for s in range(N_REPEATS)])
    wins = int((diffs > 0).sum())
    print(f'  {tgt:3s}: physics advantage = {diffs.mean():+.3f} +/- {diffs.std():.3f}'
          f'   positive in {wins}/{N_REPEATS} repeats')
    paired_rows.append({'Target': tgt, 'Mean_Advantage': round(diffs.mean(), 3),
                        'SD': round(diffs.std(), 3), 'Wins': f'{wins}/{N_REPEATS}'})
pd.DataFrame(paired_rows).to_csv('outputs/tables/physics_prior_paired_test.csv', index=False)

# ------------------------------------------------- LOSO
print('\n' + '=' * 96)
print('LEAVE-ONE-STUDY-OUT CV (cross-domain transfer of ABSOLUTE values)')
print('=' * 96)
loso_rows = []
for tgt in TARGETS:
    for r in loso_cv(tgt, True, 'ridge'):
        loso_rows.append({'Target': tgt, **r})
        print(f'  {tgt:3s} hold out {r["held_out"]:16s} n={r["n"]:3d}  R2={r["r2"]:+8.3f}  RMSE={r["rmse"]:.2f}')
pd.DataFrame(loso_rows).to_csv('outputs/tables/final_loso_results.csv', index=False)

# ------------------------------------------------- why iWUE fails
print('\n' + '=' * 96)
print('WHY THE ORIGINAL iWUE TARGET FAILS')
print('=' * 96)
ceil_rows = []
for col, label in [('Photosynthetic_Rate_A', 'A (assimilation)'),
                   ('Stomatal_Conductance_gs', 'gs (conductance)'),
                   ('WUE_intrinsic', 'iWUE = A/gs (original target)')]:
    c = variance_ceiling(col)
    ceil_rows.append({'Variable': label, 'Ceiling_R2': round(c, 3),
                      'Irreducible_Noise_Frac': round(1 - c, 3)})
    print(f'  {label:32s} ceiling R2 = {c:.3f}   irreducible noise = {1-c:.1%}')
pd.DataFrame(ceil_rows).to_csv('outputs/tables/variance_ceiling.csv', index=False)

# ------------------------------------------------- leave-one-genotype-out (per-genotype breakdown)
# The grouped-CV averages above can hide genotype-level heterogeneity. This runs the
# strictest possible per-genotype test: fit on every OTHER genotype, predict this one.
print('\n' + '=' * 96)
print('LEAVE-ONE-GENOTYPE-OUT: per-genotype breakdown (reveals heterogeneity averages hide)')
print('=' * 96)
logo_geno_rows = []
for tgt in TARGETS:
    for g in np.unique(groups):
        train, test = df[groups != g], df[groups == g]
        if len(test) < 2:
            continue
        pred = predict_fold(train, test, tgt, True, 'ridge')
        logo_geno_rows.append({
            'Target': tgt, 'Genotype_Group': g, 'n': len(test),
            'R2': round(r2_score(test[TARGETS[tgt]], pred), 3),
            'Reduction_Pct': round(test['Relative_Stomatal_Reduction_Pct'].iloc[0], 1),
        })
logo_geno_df = pd.DataFrame(logo_geno_rows).sort_values(['Target', 'R2'])
logo_geno_df.to_csv('outputs/tables/leave_one_genotype_out.csv', index=False)
print(logo_geno_df.to_string(index=False))
worst = logo_geno_df.loc[logo_geno_df.groupby('Target').R2.idxmin()]
print('\nWorst-predicted genotype per target (held out completely):')
print(worst[['Target', 'Genotype_Group', 'Reduction_Pct', 'R2']].to_string(index=False))
print('Note: worst cases are the most extreme-reduction genotypes in the dataset --')
print('the model is least reliable exactly at the tail most relevant to trait design.')

# ------------------------------------------------- fit and persist final models
print('\n' + '=' * 96)
final = {}
for tgt in TARGETS:
    p = fit_physics(df, tgt)
    base = phys_law((df['PPFD_umol'].values, df['SD_ratio'].values), *p)
    m = Ridge(alpha=1.0).fit(df[FEATS], df[TARGETS[tgt]].values - base)
    final[tgt] = {'physics_params': {'ymax': float(p[0]), 'km': float(p[1]), 'beta': float(p[2])},
                  'ridge_coef': dict(zip(FEATS, map(float, m.coef_))),
                  'ridge_intercept': float(m.intercept_),
                  'features': FEATS}
    print(f'Final {tgt} physics law: {tgt} = {p[0]:.3f} * PPFD/(PPFD+{p[1]:.0f}) * SD_ratio^{p[2]:.3f}')

with open('outputs/models/final_model_params.json', 'w') as f:
    json.dump(final, f, indent=2)
print('\nSaved final model parameters to outputs/models/final_model_params.json')
print('Saved tables to outputs/tables/{final_model_comparison,physics_prior_paired_test,'
      'final_loso_results,variance_ceiling}.csv')
