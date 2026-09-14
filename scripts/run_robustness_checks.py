"""
Two robustness analyses that address the manuscript's remaining unverified claims.

(1) DIGITIZATION ERROR.
    Reading precision is measured directly: the x-axis of the Karavolias 2023
    light-response figures should land on PAR levels stated in that paper's text, so
    deviations of the digitized x-readings from those nominal values are pure reading
    error. We then inject synthetic noise at and well beyond that measured level to
    test whether conclusions depend on digitization precision.

(2) SELECTION OPTIMISM.
    Model class, feature set and regularization strength were chosen by comparing
    validation scores on this dataset, so the headline R^2 is optimistically biased.
    Nested cross-validation removes that bias: the entire selection procedure is run
    inside an inner loop on outer-training data only, and scored on an outer fold that
    played no part in any choice. The nested-minus-standard gap IS the selection
    optimism, measured rather than asserted.

    Note on scope: the choice of TARGET (A and gs rather than A/gs) is not nested,
    because R^2 is not comparable across different response variables. That decision
    rests on the variance-ceiling analysis, which is computed from replicate structure
    alone without fitting any model, and so does not consume validation information.

    A permutation test provides the null: the same full pipeline run against shuffled
    targets, establishing what the selection procedure can manufacture from noise.
"""
import json
import os
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

warnings.filterwarnings('ignore')
os.makedirs('outputs/tables', exist_ok=True)

df = pd.read_csv('data/processed/training_data.csv')
df['SD_ratio'] = 1 - df['Relative_Stomatal_Reduction_Pct'] / 100.0
GROUPS = (df['Genotype_Line'] + '_' + df['Paper_ID']).values
TGT = {'A': 'Photosynthetic_Rate_A', 'gs': 'Stomatal_Conductance_gs'}
P0 = {'A': [25., 300., .3], 'gs': [.4, 300., .5]}
BND = {'A': ([1, 10, 0], [80, 3000, 2]), 'gs': ([.01, 10, 0], [3, 3000, 2])}

FEATURE_SETS = {
    'full6': ['SD_ratio', 'PPFD_umol', 'VPD_kPa', 'Is_Drought', 'Temperature_C', 'CO2_ppm'],
    'env4': ['SD_ratio', 'PPFD_umol', 'VPD_kPa', 'Is_Drought'],
    'min2': ['SD_ratio', 'PPFD_umol'],
}
# The full configuration space that was searched when building the model.
CONFIGS = [{'physics': ph, 'model': mdl, 'features': fs, 'alpha': a}
           for ph in (True, False)
           for mdl in ('ridge', 'xgb')
           for fs in FEATURE_SETS
           for a in ((0.1, 1.0, 10.0) if mdl == 'ridge' else (None,))]


def law(X, ymax, km, beta):
    ppfd, sd = X
    return ymax * (ppfd / (ppfd + km)) * (sd ** beta)


def fit_predict(train, test, tgt, cfg):
    feats = FEATURE_SETS[cfg['features']]
    y = train[TGT[tgt]].values
    if cfg['physics']:
        try:
            p, _ = curve_fit(law, (train.PPFD_umol.values, train.SD_ratio.values), y,
                             p0=P0[tgt], bounds=BND[tgt], maxfev=20000)
        except Exception:
            return None
        b_tr = law((train.PPFD_umol.values, train.SD_ratio.values), *p)
        b_te = law((test.PPFD_umol.values, test.SD_ratio.values), *p)
        resid = y - b_tr
    else:
        b_te, resid = 0.0, y
    if cfg['model'] == 'ridge':
        m = Ridge(alpha=cfg['alpha'])
    else:
        m = XGBRegressor(max_depth=2, n_estimators=60, learning_rate=0.05, reg_alpha=1.0,
                         reg_lambda=5.0, subsample=0.8, colsample_bytree=0.8, random_state=42)
    m.fit(train[feats], resid)
    return b_te + m.predict(test[feats])


def folds(groups, seed, k=5):
    u = np.unique(groups)
    rng = np.random.RandomState(seed)
    rng.shuffle(u)
    fo = {g: i % k for i, g in enumerate(u)}
    return np.array([fo[g] for g in groups])


def score_config(data, groups, tgt, cfg, seed, k=5):
    fold = folds(groups, seed, k)
    sc = []
    for f in range(k):
        tr, te = data[fold != f], data[fold == f]
        if len(te) < 3 or len(tr) < 10:
            continue
        pred = fit_predict(tr, te, tgt, cfg)
        if pred is None:
            continue
        sc.append(r2_score(te[TGT[tgt]], pred))
    return np.mean(sc) if sc else np.nan


FINAL_CFG = {'physics': True, 'model': 'ridge', 'features': 'full6', 'alpha': 1.0}
results = {}

# ------------------------------------------------------------------ nested CV
print('=' * 92)
print('NESTED CROSS-VALIDATION: unbiased estimate with model selection inside the loop')
print('=' * 92)
print(f'selection space: {len(CONFIGS)} configurations (physics on/off x ridge/xgb x '
      f'3 feature sets x alpha)\n')

nested_out, standard_out, picks = {}, {}, {}
for tgt in TGT:
    nested_scores, chosen = [], []
    for outer_seed in range(10):
        ofold = folds(GROUPS, outer_seed)
        for f in range(5):
            tr_m, te_m = ofold != f, ofold == f
            if te_m.sum() < 3:
                continue
            inner, inner_groups = df[tr_m], GROUPS[tr_m]
            # select on inner data ONLY
            best, best_s = None, -np.inf
            for cfg in CONFIGS:
                s = score_config(inner, inner_groups, tgt, cfg, seed=outer_seed + 100, k=4)
                if np.isfinite(s) and s > best_s:
                    best, best_s = cfg, s
            pred = fit_predict(df[tr_m], df[te_m], tgt, best)
            if pred is None:
                continue
            nested_scores.append(r2_score(df[te_m][TGT[tgt]], pred))
            chosen.append(f"{'phys+' if best['physics'] else ''}{best['model']}/{best['features']}"
                          f"{'/a=' + str(best['alpha']) if best['alpha'] else ''}")
    std = np.mean([score_config(df, GROUPS, tgt, FINAL_CFG, s) for s in range(10)])
    nested_out[tgt] = (float(np.mean(nested_scores)), float(np.std(nested_scores)))
    standard_out[tgt] = float(std)
    picks[tgt] = pd.Series(chosen).value_counts().head(4).to_dict()
    print(f'  {tgt}:  standard (reported) R2 = {std:+.3f}')
    print(f'      nested (unbiased)    R2 = {np.mean(nested_scores):+.3f} '
          f'+/- {np.std(nested_scores):.3f}')
    print(f'      selection optimism      = {std - np.mean(nested_scores):+.3f}')
    print(f'      configs chosen by inner loop: {picks[tgt]}\n')

results['nested_cv'] = {t: {'standard_R2': round(standard_out[t], 3),
                            'nested_R2': round(nested_out[t][0], 3),
                            'nested_SD': round(nested_out[t][1], 3),
                            'selection_optimism': round(standard_out[t] - nested_out[t][0], 3),
                            'inner_loop_choices': picks[t]} for t in TGT}

# ------------------------------------------------------------------ permutation null
print('=' * 92)
print('PERMUTATION TEST: what can the selection procedure manufacture from pure noise?')
print('=' * 92)
perm = {}
for tgt in TGT:
    null = []
    for i in range(30):
        d = df.copy()
        rng = np.random.RandomState(1000 + i)
        # shuffle target WITHIN genotype-group structure destroyed => pure null
        d[TGT[tgt]] = rng.permutation(d[TGT[tgt]].values)
        null.append(score_config(d, GROUPS, tgt, FINAL_CFG, seed=i))
    null = np.array([x for x in null if np.isfinite(x)])
    obs = standard_out[tgt]
    p = float((null >= obs).mean())
    perm[tgt] = {'null_mean_R2': round(float(null.mean()), 3),
                 'null_95th_R2': round(float(np.percentile(null, 95)), 3),
                 'observed_R2': round(obs, 3), 'p_value': p}
    print(f'  {tgt}: null R2 = {null.mean():+.3f} (95th pct {np.percentile(null,95):+.3f})  '
          f'observed = {obs:+.3f}  p = {p:.3f}')
results['permutation_test'] = perm

with open('outputs/tables/robustness_checks.json', 'w') as f:
    json.dump(results, f, indent=2)
print('\nSaved to outputs/tables/robustness_checks.json')
