"""
Reproduces every remaining quantitative claim in the manuscript that is not produced
by train_final_model.py, so that no number in the paper is unreproducible from the repo.

Covers:
  1. Cross-validation leakage demonstration (shuffled vs genotype-grouped, SAME model,
     SAME target, SAME fold count -- an apples-to-apples comparison, unlike an earlier
     version that compared a random-split test R^2 against a grouped CV R^2).
  2. Why the iWUE target fails: direct regression, and the post-hoc ratio of separately
     predicted A and gs.
  3. Effect size vs. replicate noise for the relative (wild-type-normalized) targets.
  4. Cross-study transfer after within-study wild-type normalization.
  5. Characterization of the leave-one-genotype-out reliability pattern (is it driven by
     reduction severity, by source study, or both?).
  6. Data coverage across the stomatal-reduction range.
"""
import json
import os
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.model_selection import GroupKFold, KFold, LeaveOneGroupOut

warnings.filterwarnings('ignore')
os.makedirs('outputs/tables', exist_ok=True)

df = pd.read_csv('data/processed/training_data.csv')
df['SD_ratio'] = 1 - df['Relative_Stomatal_Reduction_Pct'] / 100.0
groups = (df['Genotype_Line'] + '_' + df['Paper_ID'])
study = df['Paper_ID']
results = {}

FEATS = ['SD_ratio', 'PPFD_umol', 'VPD_kPa', 'Is_Drought', 'Temperature_C', 'CO2_ppm']
IWUE_FEATS = ['Relative_Stomatal_Reduction_Pct', 'Reduction_Squared', 'Temperature_C',
              'CO2_ppm', 'PPFD_umol', 'VPD_kPa', 'VPD_x_Reduction', 'PPFD_x_Reduction',
              'Is_Drought']


def phys_law(X, ymax, km, beta):
    ppfd, sd = X
    return ymax * (ppfd / (ppfd + km)) * (sd ** beta)


P0 = {'A': [25., 300., .3], 'gs': [.4, 300., .5]}
BOUNDS = {'A': ([1, 10, 0], [80, 3000, 2]), 'gs': ([.01, 10, 0], [3, 3000, 2])}
TGT = {'A': 'Photosynthetic_Rate_A', 'gs': 'Stomatal_Conductance_gs'}

# ---------------------------------------------------------------- 1. leakage demo
print('=' * 95)
print('1. CROSS-VALIDATION LEAKAGE: shuffled vs genotype-grouped, identical model/target')
print('=' * 95)
leak = {}
for tname, ycol, feats in [('iWUE (A/gs)', 'WUE_intrinsic', IWUE_FEATS),
                           ('A', 'Photosynthetic_Rate_A', FEATS),
                           ('gs', 'Stomatal_Conductance_gs', FEATS)]:
    y = df[ycol]
    X = df[feats]
    shuffled, grouped = [], []
    for seed in range(20):
        kf = KFold(n_splits=5, shuffle=True, random_state=seed)
        s = [r2_score(y.iloc[te], Ridge(alpha=1.0).fit(X.iloc[tr], y.iloc[tr]).predict(X.iloc[te]))
             for tr, te in kf.split(X)]
        shuffled.append(np.mean(s))

        uniq = groups.unique().copy()
        rng = np.random.RandomState(seed)
        rng.shuffle(uniq)
        fold_of = {g: i % 5 for i, g in enumerate(uniq)}
        fold = groups.map(fold_of).values
        g_sc = []
        for f in range(5):
            tr, te = fold != f, fold == f
            if te.sum() < 3:
                continue
            g_sc.append(r2_score(y[te], Ridge(alpha=1.0).fit(X[tr], y[tr]).predict(X[te])))
        grouped.append(np.mean(g_sc))
    infl = np.mean(shuffled) - np.mean(grouped)
    leak[tname] = {'shuffled_R2': round(float(np.mean(shuffled)), 3),
                   'grouped_R2': round(float(np.mean(grouped)), 3),
                   'inflation': round(float(infl), 3)}
    print(f'  {tname:14s} shuffled={np.mean(shuffled):+.3f}  grouped={np.mean(grouped):+.3f}'
          f'  => leakage inflation = {infl:+.3f}')
results['leakage'] = leak

# ---------------------------------------------------------------- 2. why iWUE fails
print('\n' + '=' * 95)
print('2. iWUE TARGET: direct regression vs. ratio of separately predicted A and gs')
print('=' * 95)


def grouped_folds(seed):
    uniq = groups.unique().copy()
    rng = np.random.RandomState(seed)
    rng.shuffle(uniq)
    fold_of = {g: i % 5 for i, g in enumerate(uniq)}
    return groups.map(fold_of).values


direct, derived = [], []
for seed in range(20):
    fold = grouped_folds(seed)
    d_sc, r_sc = [], []
    for f in range(5):
        tr_m, te_m = fold != f, fold == f
        if te_m.sum() < 3:
            continue
        tr, te = df[tr_m], df[te_m]
        d_sc.append(r2_score(te.WUE_intrinsic,
                             Ridge(alpha=1.0).fit(tr[IWUE_FEATS], tr.WUE_intrinsic).predict(te[IWUE_FEATS])))
        preds = {}
        for t in ('A', 'gs'):
            p, _ = curve_fit(phys_law, (tr.PPFD_umol.values, tr.SD_ratio.values), tr[TGT[t]].values,
                             p0=P0[t], bounds=BOUNDS[t], maxfev=20000)
            b_tr = phys_law((tr.PPFD_umol.values, tr.SD_ratio.values), *p)
            b_te = phys_law((te.PPFD_umol.values, te.SD_ratio.values), *p)
            m = Ridge(alpha=1.0).fit(tr[FEATS], tr[TGT[t]].values - b_tr)
            preds[t] = b_te + m.predict(te[FEATS])
        r_sc.append(r2_score(te.WUE_intrinsic, preds['A'] / np.clip(preds['gs'], 0.01, None)))
    direct.append(np.mean(d_sc))
    derived.append(np.mean(r_sc))
print(f'  direct regression on A/gs      R2 = {np.mean(direct):+.3f} +/- {np.std(direct):.3f}')
print(f'  ratio of predicted A / pred gs R2 = {np.mean(derived):+.3f} +/- {np.std(derived):.3f}')
results['iwue'] = {'direct_R2': round(float(np.mean(direct)), 3),
                   'direct_SD': round(float(np.std(direct)), 3),
                   'derived_R2': round(float(np.mean(derived)), 3),
                   'derived_SD': round(float(np.std(derived)), 3)}

# ---------------------------------------------------------------- 3+4. WT-normalized
print('\n' + '=' * 95)
print('3+4. WILD-TYPE-NORMALIZED TARGETS: effect size vs noise, and cross-study transfer')
print('=' * 95)


def wt_ref(col):
    ref = {}
    for p in df.Paper_ID.unique():
        for wt in df.Water_Treatment.unique():
            for ppfd in df.PPFD_umol.unique():
                s = df[(df.Paper_ID == p) & (df.Water_Treatment == wt) &
                       (df.PPFD_umol == ppfd) & (df.Relative_Stomatal_Reduction_Pct.abs() < 3)]
                if len(s):
                    ref[(p, wt, ppfd)] = s[col].mean()
    return ref


rel = {}
for col, lbl in [('Stomatal_Conductance_gs', 'gs'), ('Photosynthetic_Rate_A', 'A'),
                 ('WUE_intrinsic', 'iWUE')]:
    r = wt_ref(col)
    v = df.apply(lambda x: x[col] / r.get((x.Paper_ID, x.Water_Treatment, x.PPFD_umol), np.nan), axis=1)
    df[f'{lbl}_relWT'] = v
    gm = v.groupby(groups).mean()
    within = v.groupby(groups).std().mean()
    rel[lbl] = {'genotype_mean_min': round(float(gm.min()), 3), 'genotype_mean_max': round(float(gm.max()), 3),
                'between_genotype_SD': round(float(gm.std()), 3), 'within_genotype_SD': round(float(within), 3),
                'noise_to_signal': round(float(within / gm.std()), 2)}
    print(f'  {lbl:5s} relWT: genotype means {gm.min():.2f}-{gm.max():.2f} '
          f'(between-SD {gm.std():.3f}) vs within-genotype SD {within:.3f} '
          f'=> noise/signal = {within/gm.std():.2f}x')
results['relative_effect_size'] = rel

print('\n  Cross-study (leave-one-study-out) transfer of WT-normalized targets:')
transfer = {}
RFEATS = ['SD_ratio', 'PPFD_umol', 'VPD_kPa', 'Is_Drought']
for lbl in ('A', 'gs', 'iWUE'):
    y = df[f'{lbl}_relWT']
    ok = y.notna()
    sc = []
    for tr, te in LeaveOneGroupOut().split(df[ok], y[ok], groups=study[ok]):
        Xa, ya = df[ok][RFEATS], y[ok]
        sc.append(r2_score(ya.iloc[te], Ridge(alpha=1.0).fit(Xa.iloc[tr], ya.iloc[tr]).predict(Xa.iloc[te])))
    transfer[lbl] = {'loso_mean_R2': round(float(np.mean(sc)), 3), 'folds': [round(s, 3) for s in sc]}
    print(f'    {lbl:5s} LOSO R2 = {np.mean(sc):+.3f}   folds={[round(s,2) for s in sc]}')
results['wt_normalized_transfer'] = transfer

# ---------------------------------------------------------------- 5. reliability pattern
print('\n' + '=' * 95)
print('5. IS LEAVE-ONE-GENOTYPE-OUT RELIABILITY DRIVEN BY SEVERITY, BY STUDY, OR BOTH?')
print('=' * 95)
logo = pd.read_csv('outputs/tables/leave_one_genotype_out.csv')
pattern = {}
for tgt in ('A', 'gs'):
    s = logo[logo.Target == tgt].copy()
    s['is_caine'] = s.Genotype_Group.str.contains('Caine')
    s['abs_red'] = s.Reduction_Pct.abs()
    rho = s[['abs_red', 'R2']].corr(method='spearman').iloc[0, 1]
    caine_med, other_med = s[s.is_caine].R2.median(), s[~s.is_caine].R2.median()
    severe = s[s.Reduction_Pct >= 58]
    moderate = s[(s.Reduction_Pct > -25) & (s.Reduction_Pct < 58)]
    pattern[tgt] = {'spearman_absreduction_vs_R2': round(float(rho), 3),
                    'median_R2_severe_ge58pct': round(float(severe.R2.median()), 3),
                    'median_R2_moderate_lt58pct': round(float(moderate.R2.median()), 3),
                    'median_R2_caine': round(float(caine_med), 3),
                    'median_R2_other_studies': round(float(other_med), 3)}
    print(f'  {tgt}: Spearman(|reduction|, R2) = {rho:+.3f}')
    print(f'     median R2  severe (>=58% reduction) = {severe.R2.median():+.3f}  (n={len(severe)})')
    print(f'     median R2  moderate (<58%)          = {moderate.R2.median():+.3f}  (n={len(moderate)})')
    print(f'     median R2  Caine lines = {caine_med:+.3f}   other studies = {other_med:+.3f}')
results['reliability_pattern'] = pattern

# ---------------------------------------------------------------- 6. data coverage
print('\n' + '=' * 95)
print('6. DATA COVERAGE ACROSS THE STOMATAL-REDUCTION RANGE')
print('=' * 95)
red = df.Relative_Stomatal_Reduction_Pct
levels = sorted(red.round(1).unique())
print(f'  distinct genotype reduction levels: {levels}')
gaps = [(levels[i], levels[i + 1], levels[i + 1] - levels[i]) for i in range(len(levels) - 1)]
biggest = max(gaps, key=lambda g: g[2])
mid = df[(red > 30) & (red < 70)]
print(f'  largest gap between adjacent levels: {biggest[0]}% -> {biggest[1]}% ({biggest[2]:.1f} points)')
print(f'  rows in the decision-relevant 30-70% band: {len(mid)} '
      f'from {mid.Genotype_Line.nunique()} genotype(s): {list(mid.Genotype_Line.unique())}')
results['coverage'] = {'levels': [float(x) for x in levels],
                       'largest_gap': [float(biggest[0]), float(biggest[1]), float(biggest[2])],
                       'rows_30_to_70pct': int(len(mid)),
                       'genotypes_30_to_70pct': list(mid.Genotype_Line.unique())}
print(f'  distinct genotype LINES (genotype x study): {groups.nunique()}  '
      f'(distinct genotype NAMES: {df.Genotype_Line.nunique()})')
results['n_genotype_lines'] = int(groups.nunique())

with open('outputs/tables/supporting_analyses.json', 'w') as f:
    json.dump(results, f, indent=2)
print('\nSaved all supporting numbers to outputs/tables/supporting_analyses.json')
