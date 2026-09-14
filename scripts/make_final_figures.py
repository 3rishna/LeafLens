"""Figures for the final LeafLens model (targets: A and gs)."""
import json
import os
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.optimize import curve_fit
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score

warnings.filterwarnings('ignore')
os.makedirs('outputs/figures', exist_ok=True)
sns.set_theme(style='whitegrid')
plt.rcParams.update({'font.size': 11})

FEATS = ['SD_ratio', 'PPFD_umol', 'VPD_kPa', 'Is_Drought', 'Temperature_C', 'CO2_ppm']
TARGETS = {'A': 'Photosynthetic_Rate_A', 'gs': 'Stomatal_Conductance_gs'}
LABELS = {'A': 'Assimilation $A$ ($\\mu$mol CO$_2$ m$^{-2}$ s$^{-1}$)',
          'gs': 'Conductance $g_s$ (mol H$_2$O m$^{-2}$ s$^{-1}$)'}
_ceil = pd.read_csv('outputs/tables/variance_ceiling.csv').set_index('Variable').Ceiling_R2
CEILING = {'A': float(_ceil['A (assimilation)']), 'gs': float(_ceil['gs (conductance)'])}

df = pd.read_csv('data/processed/training_data.csv')
df['SD_ratio'] = 1 - df['Relative_Stomatal_Reduction_Pct'] / 100.0
groups = (df['Genotype_Line'] + '_' + df['Paper_ID']).values


def phys_law(X, ymax, km, beta):
    ppfd, sd = X
    return ymax * (ppfd / (ppfd + km)) * (sd ** beta)


P0 = {'A': [25.0, 300.0, 0.3], 'gs': [0.4, 300.0, 0.5]}
BOUNDS = {'A': ([1, 10, 0], [80, 3000, 2]), 'gs': ([0.01, 10, 0], [3, 3000, 2])}


def fit_physics(train, tgt):
    p, _ = curve_fit(phys_law, (train['PPFD_umol'].values, train['SD_ratio'].values),
                     train[TARGETS[tgt]].values, p0=P0[tgt], bounds=BOUNDS[tgt], maxfev=20000)
    return p


def cv_predictions(tgt, seed=0):
    """Out-of-fold predictions under genotype-grouped CV."""
    uniq = np.unique(groups)
    rng = np.random.RandomState(seed)
    rng.shuffle(uniq)
    fold_of = {g: i % 5 for i, g in enumerate(uniq)}
    fold = np.array([fold_of[g] for g in groups])
    pred = np.full(len(df), np.nan)
    for f in range(5):
        tr, te = df[fold != f], df[fold == f]
        if len(te) < 3:
            continue
        p = fit_physics(tr, tgt)
        b_tr = phys_law((tr['PPFD_umol'].values, tr['SD_ratio'].values), *p)
        b_te = phys_law((te['PPFD_umol'].values, te['SD_ratio'].values), *p)
        m = Ridge(alpha=1.0).fit(tr[FEATS], tr[TARGETS[tgt]].values - b_tr)
        pred[fold == f] = b_te + m.predict(te[FEATS])
    return pred


# ---------------------------------------------------------------- Fig 1: model comparison
comp = pd.read_csv('outputs/tables/final_model_comparison.csv')
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
for ax, tgt in zip(axes, ['A', 'gs']):
    sub = comp[comp.Target == tgt].sort_values('Grouped_CV_R2')
    colors = ['#c44e52' if 'Pure physics' in m else
              '#dd8452' if 'Naive' in m else '#4c72b0' for m in sub.Model]
    ax.barh(range(len(sub)), sub.Grouped_CV_R2, xerr=sub.Grouped_CV_SD,
            color=colors, alpha=0.85, capsize=4)
    ax.set_yticks(range(len(sub)))
    ax.set_yticklabels([m.replace(' (', '\n(') for m in sub.Model], fontsize=9)
    ax.axvline(0, color='k', lw=1)
    ax.axvline(CEILING[tgt], color='green', ls='--', lw=2,
               label=f'variance ceiling ({CEILING[tgt]:.2f})')
    ax.set_xlabel('Genotype-grouped CV $R^2$ (20 randomized fold assignments)')
    ax.set_title(f'Target: {tgt}', fontweight='bold')
    ax.legend(loc='lower right', fontsize=9)
plt.tight_layout()
plt.savefig('outputs/figures/fig_model_performance.png', dpi=300, bbox_inches='tight')
plt.close()

# ---------------------------------------------------------------- Fig 2: predicted vs observed
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
for ax, tgt in zip(axes, ['A', 'gs']):
    pred = cv_predictions(tgt)
    obs = df[TARGETS[tgt]].values
    ok = ~np.isnan(pred)
    for study, c in zip(['Caine2019', 'Karavolias2023', 'Karavolias2024'],
                        ['#4c72b0', '#dd8452', '#55a868']):
        m = ok & (df.Paper_ID == study).values
        ax.scatter(obs[m], pred[m], alpha=0.65, s=42, color=c, label=study, edgecolor='none')
    lo, hi = np.nanmin([obs.min(), np.nanmin(pred)]), np.nanmax([obs.max(), np.nanmax(pred)])
    ax.plot([lo, hi], [lo, hi], 'k--', lw=1.2, label='1:1')
    ax.set_xlabel(f'Observed {LABELS[tgt]}')
    ax.set_ylabel(f'Predicted (out-of-fold)')
    ax.set_title(f'{tgt}: out-of-fold $R^2$ = {r2_score(obs[ok], pred[ok]):.3f}', fontweight='bold')
    ax.legend(fontsize=8, loc='upper left')
plt.tight_layout()
plt.savefig('outputs/figures/fig_pred_vs_obs.png', dpi=300, bbox_inches='tight')
plt.close()

# ---------------------------------------------------------------- Fig 3: fitted light-response law
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
k23 = df[df.Paper_ID == 'Karavolias2023']
for ax, tgt in zip(axes, ['A', 'gs']):
    p = fit_physics(df, tgt)
    grid = np.linspace(30, 2050, 200)
    for sd, c, lbl in [(1.0, '#4c72b0', 'wild-type density'),
                       (0.7, '#dd8452', '30% reduction'),
                       (0.4, '#c44e52', '60% reduction')]:
        ax.plot(grid, phys_law((grid, np.full_like(grid, sd)), *p), color=c, lw=2.2, label=lbl)
    for geno, mk in [('Wild Type', 'o'), ('epfl10', 's'), ('Stomagen', '^')]:
        s = k23[k23.Genotype_Line == geno]
        if len(s):
            ax.scatter(s.PPFD_umol, s[TARGETS[tgt]], marker=mk, s=55, alpha=0.8,
                       edgecolor='k', linewidth=0.5, label=f'observed: {geno}')
    ax.set_xlabel('PPFD ($\\mu$mol photons m$^{-2}$ s$^{-1}$)')
    ax.set_ylabel(LABELS[tgt])
    ax.set_title(f'Fitted physics prior: {tgt} = {p[0]:.2f}·PPFD/(PPFD+{p[1]:.0f})·$SD^{{{p[2]:.2f}}}$',
                 fontsize=10, fontweight='bold')
    ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig('outputs/figures/fig_light_response.png', dpi=300, bbox_inches='tight')
plt.close()

# ---------------------------------------------------------------- Fig 4: carbon/water trade-off
params = {t: fit_physics(df, t) for t in TARGETS}
models = {}
for t in TARGETS:
    base = phys_law((df['PPFD_umol'].values, df['SD_ratio'].values), *params[t])
    models[t] = Ridge(alpha=1.0).fit(df[FEATS], df[TARGETS[t]].values - base)

red_grid = np.arange(0, 81, 2.5)
TRAIN_MIN, TRAIN_MAX = df.Relative_Stomatal_Reduction_Pct.min(), df.Relative_Stomatal_Reduction_Pct.max()

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
for ax, (ppfd, vpd, t_c, lbl) in zip(
        axes,
        [(1500, 1.6, 29, 'Growth-chamber conditions (in training domain)'),
         (1085, 3.39, 33.2, 'Telangana pre-monsoon (EXTRAPOLATED)')]):
    curves = {}
    for t in TARGETS:
        grid = pd.DataFrame({'SD_ratio': 1 - red_grid / 100, 'PPFD_umol': ppfd,
                             'VPD_kPa': vpd, 'Is_Drought': 1,
                             'Temperature_C': t_c, 'CO2_ppm': 420.0})
        base = phys_law((grid.PPFD_umol.values, grid.SD_ratio.values), *params[t])
        curves[t] = base + models[t].predict(grid[FEATS])
    ax.plot(red_grid, 100 * curves['A'] / curves['A'][0], color='#55a868', lw=2.6,
            label='Carbon gain (A), % of unedited')
    ax.plot(red_grid, 100 * curves['gs'] / curves['gs'][0], color='#4c72b0', lw=2.6,
            label='Water loss ($g_s$), % of unedited')
    ax.axvspan(28.5, 58, color='grey', alpha=0.18)
    ax.text(43, 55, 'no genotypes\nin this range', ha='center', fontsize=9, color='#444')
    ax.axhline(100, color='k', lw=0.8, ls=':')
    ax.set_xlabel('Stomatal density reduction (%)')
    ax.set_ylabel('% of unedited wild-type')
    ax.set_title(lbl, fontsize=10, fontweight='bold')
    ax.set_ylim(40, 110)
    ax.legend(fontsize=9, loc='lower left')
plt.tight_layout()
plt.savefig('outputs/figures/fig_tradeoff.png', dpi=300, bbox_inches='tight')
plt.close()

# ---------------------------------------------------------------- Fig 5: variance ceiling
ceil = pd.read_csv('outputs/tables/variance_ceiling.csv')
fig, ax = plt.subplots(figsize=(8.5, 4.6))
y = range(len(ceil))
ax.barh(y, ceil.Ceiling_R2, color='#55a868', alpha=0.9, label='learnable (between-genotype signal)')
ax.barh(y, ceil.Irreducible_Noise_Frac, left=ceil.Ceiling_R2, color='#c44e52', alpha=0.55,
        label='irreducible replicate noise')
ax.set_yticks(y)
ax.set_yticklabels(ceil.Variable)
ax.set_xlabel('Fraction of total variance')
ax.set_title('Why the original $A/g_s$ target could not work', fontweight='bold')
for i, r in ceil.iterrows():
    if r.Ceiling_R2 > 0.08:
        ax.text(r.Ceiling_R2 / 2, i, f'{r.Ceiling_R2:.2f}', ha='center', va='center',
                color='white', fontweight='bold', fontsize=10)
    else:
        ax.text(0.015, i, f'{r.Ceiling_R2:.2f}', ha='left', va='center',
                color='black', fontweight='bold', fontsize=10)
ax.legend(loc='lower right', fontsize=9)
plt.tight_layout()
plt.savefig('outputs/figures/fig_variance_ceiling.png', dpi=300, bbox_inches='tight')
plt.close()

# ---------------------------------------------------------------- Fig 6: genotype reliability
logo = pd.read_csv('outputs/tables/leave_one_genotype_out.csv')
fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
for ax, tgt in zip(axes, ['A', 'gs']):
    sub = logo[logo.Target == tgt].sort_values('Reduction_Pct')
    colors = ['#c44e52' if r2 < 0 else '#55a868' for r2 in sub.R2]
    ax.scatter(sub.Reduction_Pct, sub.R2, c=colors, s=70, edgecolor='k', linewidth=0.5, zorder=3)
    ax.axhline(0, color='k', lw=1, ls='--')
    ax.axvspan(28.5, 58, color='grey', alpha=0.15)
    ax.set_xlabel('Stomatal density reduction of held-out genotype (%)')
    ax.set_ylabel('Leave-one-genotype-out $R^2$')
    ax.set_title(f'{tgt}: reliability vs. reduction magnitude', fontweight='bold')
    worst = sub.loc[sub.R2.idxmin()]
    ax.annotate(f"{worst.Genotype_Group.split('_')[0]}\n(most severe)",
                xy=(worst.Reduction_Pct, worst.R2), xytext=(worst.Reduction_Pct - 25, worst.R2 + 1.5),
                fontsize=8, arrowprops=dict(arrowstyle='->', lw=1))
plt.tight_layout()
plt.savefig('outputs/figures/fig_genotype_reliability.png', dpi=300, bbox_inches='tight')
plt.close()

print('Wrote: fig_model_performance, fig_pred_vs_obs, fig_light_response, '
      'fig_tradeoff, fig_variance_ceiling, fig_genotype_reliability')

# quantify the trade-off for the manuscript text
print('\nTrade-off at growth-chamber conditions (in-domain):')
grid = pd.DataFrame({'SD_ratio': 1 - red_grid / 100, 'PPFD_umol': 1500, 'VPD_kPa': 1.6,
                     'Is_Drought': 1, 'Temperature_C': 29, 'CO2_ppm': 420.0})
out = {}
for t in TARGETS:
    base = phys_law((grid.PPFD_umol.values, grid.SD_ratio.values), *params[t])
    out[t] = base + models[t].predict(grid[FEATS])
for r in [10, 20, 30, 40]:
    i = list(red_grid).index(r)
    print(f'  {r:2d}% reduction -> A retained {100*out["A"][i]/out["A"][0]:.1f}%, '
          f'gs retained {100*out["gs"][i]/out["gs"][0]:.1f}%')
