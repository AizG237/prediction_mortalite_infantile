"""Script temporaire : exécute le projet jusqu'au contrôle VIF uniquement."""
import pickle, warnings
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

warnings.filterwarnings('ignore')

PKL = r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\data_prepared.pkl"

# ── 1. Chargement ────────────────────────────────────────────────────────────
with open(PKL, 'rb') as f:
    data = pickle.load(f)

df_stat  = data['df_stat']
df_clean = data['df_clean']

# ── 2. Restriction aux femmes parentes (parité ≥ 1) ──────────────────────────
mask = df_clean['nb_enfants_nes_vivants'].fillna(0) >= 1
df_stat = df_stat[mask.values].copy()
print(f"Dataset analytique : {df_stat.shape}  |  Prévalence Y=1 : {df_stat['Y'].mean()*100:.2f}%\n")

# ── 3. Création des dummies (même logique que prepare_regression_data) ────────
df_reg = df_stat.copy()
cat_dummies = {
    'education_cat': 'Superieur',
    'milieu_cat':    'Urbain',
    'richesse_cat':  'Tres_riche',
    'union_cat':     'En_union',
    'religion_cat':  'Catholique',
    'emploi_cat':    'Oui',
    'assurance_cat': 'Oui',
    'age_prb_cat':   '25_et_plus',
}
dummy_cols = []
for var, ref in cat_dummies.items():
    if var not in df_reg.columns:
        continue
    dummies = pd.get_dummies(df_reg[var], prefix=var, drop_first=False)
    ref_col = f"{var}_{ref}"
    if ref_col in dummies.columns:
        dummies = dummies.drop(columns=[ref_col])
    df_reg = pd.concat([df_reg, dummies], axis=1)
    dummy_cols.extend(dummies.columns.tolist())

if 'region_cat' in df_reg.columns:
    dummies_reg = pd.get_dummies(df_reg['region_cat'], prefix='region_cat', drop_first=False)
    if 'region_cat_Littoral' in dummies_reg.columns:
        dummies_reg = dummies_reg.drop(columns=['region_cat_Littoral'])
    df_reg = pd.concat([df_reg, dummies_reg], axis=1)
    dummy_cols.extend(dummies_reg.columns.tolist())

cont_cols = ['age', 'naissances_5ans', 'score_pb_acces_sante', 'taille_menage']
bin_cols  = ['grossesse_interrompue', 'visite_agent_sante', 'consultation_etablissement', 'electricite']
cont_present = [c for c in cont_cols if c in df_reg.columns]
bin_present  = [c for c in bin_cols  if c in df_reg.columns]
all_predictors = cont_present + bin_present + dummy_cols

# Supprimer les colonnes à variance nulle
cols_zero_var = [c for c in all_predictors if df_reg[c].std() == 0]
if cols_zero_var:
    print(f"Colonnes variance nulle supprimées : {cols_zero_var}")
    all_predictors = [c for c in all_predictors if c not in cols_zero_var]

print(f"Nombre de prédicteurs : {len(all_predictors)}\n")

# ── 4. Calcul du VIF ─────────────────────────────────────────────────────────
print("=" * 65)
print("CONTROLE DE MULTICOLINEARITE - Facteur d'Inflation de la Variance (VIF)")
print("=" * 65)

df_sample = df_reg[all_predictors].dropna().sample(min(5000, len(df_reg)), random_state=42)
# Forcer les booléens (get_dummies pandas 2.x) en int puis float
X = df_sample.copy()
for col in X.columns:
    if X[col].dtype == bool:
        X[col] = X[col].astype(int)
X = X.apply(pd.to_numeric, errors='coerce').fillna(0).astype(float)
X_with_const = sm.add_constant(X, has_constant='add')

vif_data = []
for i, col in enumerate(X.columns):
    try:
        vif = variance_inflation_factor(X_with_const.values, i + 1)
        vif_data.append({'Variable': col, 'VIF': round(vif, 2)})
    except Exception:
        vif_data.append({'Variable': col, 'VIF': float('nan')})

vif_df = pd.DataFrame(vif_data).sort_values('VIF', ascending=False).reset_index(drop=True)

# ── 5. Affichage complet ──────────────────────────────────────────────────────
pd.set_option('display.max_rows', 200)
pd.set_option('display.width', 100)

print(vif_df.to_string(index=False))

# Diagnostic
problematic = vif_df[vif_df['VIF'] > 10]
print("\n" + "-" * 65)
if len(problematic) > 0:
    print(f"ATTENTION : Variables avec VIF > 10 (multicolinearite probable) :")
    print(problematic.to_string(index=False))
else:
    print("OK : Aucune multicolinearite severe - tous les VIF <= 10")
print("-" * 65)
