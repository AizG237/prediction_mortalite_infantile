"""
statistical_model.py
Regression logistique binaire ponderee - EDS Cameroun 2018
Facteurs associes a la mortalite infantile
"""
import pandas as pd
import numpy as np
import pickle
import warnings
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor
# hosmer_lemeshow_test sera defini localement
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.preprocessing import LabelEncoder
import joblib
import os
warnings.filterwarnings('ignore')


def hosmer_lemeshow(y_true, y_pred, groups=10):
    """Test de Hosmer-Lemeshow implementation manuelle."""
    df_hl = pd.DataFrame({'y': y_true, 'p': y_pred})
    df_hl['decile'] = pd.qcut(df_hl['p'], q=groups, duplicates='drop', labels=False)
    obs = df_hl.groupby('decile')['y'].agg(['sum', 'count'])
    exp = df_hl.groupby('decile')['p'].agg(['sum', 'count'])
    O1 = obs['sum']
    E1 = exp['sum']
    O0 = obs['count'] - O1
    E0 = obs['count'] - E1
    hl_stat = ((O1 - E1)**2 / (E1 + 1e-10) + (O0 - E0)**2 / (E0 + 1e-10)).sum()
    dof = len(obs) - 2
    p_val = 1 - stats.chi2.cdf(hl_stat, dof)
    return hl_stat, p_val

OUTPUT_DIR = r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\outputs_stat"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# CHARGEMENT DES DONNEES PREPAREES
# --------------------------------------------------------------------------

with open(r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\data_prepared.pkl", 'rb') as f:
    data = pickle.load(f)

df_stat = data['df_stat']
vars_stat = data['vars_stat']
df_clean = data['df_clean']

print(f"Dataset initial : {df_stat.shape}")

# Restriction aux femmes ayant eu au moins un enfant ne vivant
# Approche standard DHS : la mortalite infantile n est pertinente
# que pour les femmes qui ont deja eu au moins un enfant (parite >= 1).
# Les nullipares ont Y=0 par definition - les inclure creeraient un biais
# de quasi-separation parfaite dans le modele logistique.
mask_pares = df_clean['nb_enfants_nes_vivants'].fillna(0) >= 1
n_avant = len(df_stat)
df_stat = df_stat[mask_pares.values].copy()
print(f"Restriction aux femmes pares (parite >= 1) : {n_avant} -> {len(df_stat)} obs.")
print(f"Femmes nullipares exclues : {n_avant - len(df_stat)}")
print(f"Dataset analytique : {df_stat.shape}")
print(f"Prevalence Y=1 : {df_stat['Y'].mean()*100:.2f}%")

# --------------------------------------------------------------------------
# 1. ANALYSE DESCRIPTIVE UNIVARIEE
# --------------------------------------------------------------------------

def analyse_univariee(df):
    print("\n" + "="*70)
    print("ANALYSE DESCRIPTIVE UNIVARIEE")
    print("="*70)

    # Variables numeriques
    num_vars = ['age', 'score_pb_acces_sante', 'naissances_5ans', 'taille_menage']
    for v in num_vars:
        if v in df.columns:
            col = df[v]
            print(f"\n{v}:")
            print(f"  Moyenne : {col.mean():.2f}")
            print(f"  Mediane : {col.median():.2f}")
            print(f"  Ecart-type : {col.std():.2f}")
            print(f"  [Min - Max] : [{col.min():.0f} - {col.max():.0f}]")

    # Variables categoriques
    cat_vars = ['education_cat', 'milieu_cat', 'region_cat', 'religion_cat',
                'union_cat', 'richesse_cat', 'emploi_cat', 'assurance_cat']
    for v in cat_vars:
        if v in df.columns:
            print(f"\n{v}:")
            freq = df[v].value_counts(normalize=True) * 100
            for cat, pct in freq.items():
                n = df[v].value_counts()[cat]
                print(f"  {cat}: {n} ({pct:.1f}%)")


# --------------------------------------------------------------------------
# 2. ANALYSE BIVARIEE (Y vs chaque variable)
# --------------------------------------------------------------------------

def analyse_bivariee(df):
    print("\n" + "="*70)
    print("ANALYSE BIVARIEE (Association avec Y)")
    print("="*70)

    results = []

    # Variables categoriques -> Chi-deux
    cat_vars = ['education_cat', 'milieu_cat', 'region_cat', 'religion_cat',
                'union_cat', 'richesse_cat', 'emploi_cat', 'assurance_cat',
                'age_prb_cat', 'parite_cat']

    for v in cat_vars:
        if v in df.columns:
            ct = pd.crosstab(df[v], df['Y'])
            chi2, p, dof, _ = stats.chi2_contingency(ct)
            # Prevalence de Y=1 par categorie
            prev = df.groupby(v)['Y'].mean() * 100
            print(f"\n{v} (Chi2={chi2:.2f}, p={p:.4f}):")
            for cat in prev.index:
                n = df[v].value_counts().get(cat, 0)
                print(f"  {cat}: {prev[cat]:.1f}% (n={n})")
            results.append({'variable': v, 'test': 'Chi2', 'stat': chi2, 'p_value': p})

    # Variables continues -> t-test
    num_vars = ['age', 'score_pb_acces_sante', 'naissances_5ans', 'taille_menage']
    for v in num_vars:
        if v in df.columns:
            g0 = df.loc[df['Y'] == 0, v].dropna()
            g1 = df.loc[df['Y'] == 1, v].dropna()
            t_stat, p = stats.ttest_ind(g0, g1)
            print(f"\n{v} (t={t_stat:.3f}, p={p:.4f}):")
            print(f"  Y=0 : moyenne={g0.mean():.2f}, ecart-type={g0.std():.2f}")
            print(f"  Y=1 : moyenne={g1.mean():.2f}, ecart-type={g1.std():.2f}")
            results.append({'variable': v, 'test': 't-test', 'stat': t_stat, 'p_value': p})

    results_df = pd.DataFrame(results).sort_values('p_value')
    print(f"\nVariables significatives (p<0.05) : {(results_df['p_value'] < 0.05).sum()}")
    return results_df


# --------------------------------------------------------------------------
# 3. PREPARATION POUR LA REGRESSION
# --------------------------------------------------------------------------

def prepare_regression_data(df):
    """
    Creer les variables dummies pour la regression.
    Categories de reference choisies selon la logique theorique :
    - education_cat : 'Superieur' (plus favorise)
    - milieu_cat : 'Urbain'
    - richesse_cat : 'Tres_riche'
    - union_cat : 'En_union'
    - religion_cat : 'Catholique'
    - region_cat : 'Littoral'
    - emploi_cat : 'Oui'
    - assurance_cat : 'Oui'
    - age_prb_cat : '25_et_plus'
    - parite_cat : '0'
    """
    df_reg = df.copy()

    # Variables categoriques avec leur reference
    cat_dummies = {
        'education_cat': 'Superieur',
        'milieu_cat': 'Urbain',
        'richesse_cat': 'Tres_riche',
        'union_cat': 'En_union',
        'religion_cat': 'Catholique',
        'emploi_cat': 'Oui',
        'assurance_cat': 'Oui',
        'age_prb_cat': '25_et_plus',
        # parite_cat exclu : cause separation parfaite (parite=0 => Y=0 par construction)
        # L analyse est restreinte aux femmes pares => parite non pertinent ici
    }

    dummy_cols = []
    for var, ref in cat_dummies.items():
        if var in df_reg.columns:
            # S'assurer que la reference est bien dans les donnees
            modalities = df_reg[var].unique()
            if ref not in modalities:
                ref = df_reg[var].mode()[0]
                print(f"  Attention : reference modifiee pour {var} -> {ref}")

            dummies = pd.get_dummies(df_reg[var], prefix=var, drop_first=False)
            # Supprimer la categorie de reference
            ref_col = f"{var}_{ref}"
            if ref_col in dummies.columns:
                dummies = dummies.drop(columns=[ref_col])
            df_reg = pd.concat([df_reg, dummies], axis=1)
            dummy_cols.extend(dummies.columns.tolist())

    # Region : reference Littoral
    if 'region_cat' in df_reg.columns:
        dummies_reg = pd.get_dummies(df_reg['region_cat'], prefix='region_cat', drop_first=False)
        ref_col = 'region_cat_Littoral'
        if ref_col in dummies_reg.columns:
            dummies_reg = dummies_reg.drop(columns=[ref_col])
        df_reg = pd.concat([df_reg, dummies_reg], axis=1)
        dummy_cols.extend(dummies_reg.columns.tolist())

    # Variables continues a inclure
    cont_cols = ['age', 'naissances_5ans', 'score_pb_acces_sante', 'taille_menage']
    cont_cols_present = [c for c in cont_cols if c in df_reg.columns]

    # Variables binaires directes
    bin_cols = ['grossesse_interrompue', 'visite_agent_sante', 'consultation_etablissement', 'electricite']
    bin_cols_present = [c for c in bin_cols if c in df_reg.columns]

    all_predictors = cont_cols_present + bin_cols_present + dummy_cols

    # Nettoyer : supprimer les colonnes avec variance nulle
    X_check = df_reg[all_predictors].copy()
    cols_to_remove = [c for c in all_predictors if X_check[c].std() == 0]
    if cols_to_remove:
        print(f"Colonnes variance nulle supprimees : {cols_to_remove}")
        all_predictors = [c for c in all_predictors if c not in cols_to_remove]

    print(f"Nombre de predicteurs : {len(all_predictors)}")
    return df_reg, all_predictors


# --------------------------------------------------------------------------
# 4. TEST DE MULTICOLINEARITE (VIF)
# --------------------------------------------------------------------------

def test_vif(df_reg, predictors, sample_size=5000):
    """Calculer le VIF pour detecter la multicolinearite."""
    print("\n--- Test de multicolinearite (VIF) ---")

    # Utiliser un echantillon pour VIF si dataset grand
    df_sample = df_reg[predictors].dropna().sample(
        min(sample_size, len(df_reg)), random_state=42
    )

    # Convertir en numerique et remplacer les NaN
    X = df_sample.apply(pd.to_numeric, errors='coerce').fillna(0)
    X_with_const = sm.add_constant(X)

    vif_data = []
    for i, col in enumerate(X.columns):
        try:
            vif = variance_inflation_factor(X_with_const.values, i + 1)
            vif_data.append({'Variable': col, 'VIF': round(vif, 2)})
        except Exception:
            vif_data.append({'Variable': col, 'VIF': np.nan})

    vif_df = pd.DataFrame(vif_data).sort_values('VIF', ascending=False)
    problematic = vif_df[vif_df['VIF'] > 10]
    if len(problematic) > 0:
        print(f"Variables avec VIF > 10 (multicolinearite probable) :")
        print(problematic.to_string())
    else:
        print("Aucune multicolinearite severe detectee (tous VIF <= 10)")

    print("\nTop 10 VIF :")
    print(vif_df.head(10).to_string())

    return vif_df


# --------------------------------------------------------------------------
# 5. REGRESSION LOGISTIQUE PONDEREE - MODELE PAR MODELE
# --------------------------------------------------------------------------

def run_logistic_model(df_reg, predictors, weights, model_name="Modele"):
    """
    Executer une regression logistique ponderee via statsmodels GLM (Binomial).
    """
    print(f"\n--- {model_name} ---")

    y = df_reg['Y'].astype(float).values
    # Supprimer les doublons de predicteurs
    predictors_uniq = list(dict.fromkeys(predictors))
    X_data = df_reg[predictors_uniq].copy()
    # Forcer tout en float64 - critique pour statsmodels
    X_data = X_data.apply(lambda s: pd.to_numeric(s, errors='coerce').fillna(0)).astype(float)
    X_with_const = sm.add_constant(X_data, has_constant='add')

    # Normaliser les poids
    w = pd.to_numeric(weights, errors='coerce').fillna(1.0).values
    w_norm = w / w.mean()

    try:
        model = sm.GLM(
            y, X_with_const,
            family=sm.families.Binomial(),
            var_weights=w_norm
        )
        result = model.fit(method='bfgs', maxiter=200, disp=False)
        print(f"Convergence : {'OUI' if result.converged else 'NON'}")
        print(f"Log-vraisemblance : {result.llf:.4f}")
        print(f"AIC : {result.aic:.4f}")
        llnull = sm.GLM(y, np.ones((len(y), 1)), family=sm.families.Binomial()).fit().llf
        mcfadden = 1 - result.llf / llnull
        print(f"Pseudo R2 (McFadden) : {mcfadden:.4f}")
        result._llnull = llnull
        result._mcfadden = mcfadden
        return result
    except Exception as e:
        print(f"GLM bfgs echoue ({e}), essai IRLS...")
        model = sm.GLM(y, X_with_const, family=sm.families.Binomial(), var_weights=w_norm)
        result = model.fit(maxiter=200, disp=False)
        llnull = sm.GLM(y, np.ones((len(y), 1)), family=sm.families.Binomial()).fit().llf
        result._llnull = llnull
        result._mcfadden = 1 - result.llf / llnull
        return result


def extract_odds_ratios(result, predictors):
    """Extraire les OR avec intervalles de confiance a 95%."""
    params = result.params
    conf = result.conf_int()
    pvals = result.pvalues

    or_df = pd.DataFrame({
        'Variable': params.index,
        'Coefficient': params.values,
        'OR': np.exp(params.values),
        'IC_inf_95': np.exp(conf.iloc[:, 0].values),
        'IC_sup_95': np.exp(conf.iloc[:, 1].values),
        'p_value': pvals.values
    })
    or_df['Significatif'] = or_df['p_value'] < 0.05
    or_df = or_df[or_df['Variable'] != 'const']
    or_df = or_df.sort_values('OR', ascending=False)
    return or_df


# --------------------------------------------------------------------------
# 6. QUALITE DU MODELE FINAL
# --------------------------------------------------------------------------

def evaluate_model(result, df_reg, predictors, weights):
    """Evaluer la qualite du modele final."""
    print("\n--- Qualite du modele ---")

    y = df_reg['Y'].astype(float).values
    X_data = df_reg[predictors].copy()
    for col in X_data.columns:
        X_data[col] = pd.to_numeric(X_data[col], errors='coerce').fillna(0).astype(float)
    X_with_const = sm.add_constant(X_data.astype(float), has_constant='add')

    # Probabilites predites
    y_pred_prob = result.predict(X_with_const)
    y_pred_class = (y_pred_prob >= 0.5).astype(int)

    # ROC-AUC
    auc = roc_auc_score(y, y_pred_prob)
    print(f"ROC-AUC : {auc:.4f}")

    # Hosmer-Lemeshow (implementation manuelle)
    try:
        hl_stat, hl_p = hosmer_lemeshow(y, y_pred_prob, groups=10)
        print(f"Hosmer-Lemeshow : statistique={hl_stat:.4f}, p={hl_p:.4f}")
        if hl_p > 0.05:
            print("  -> Ajustement acceptable (p > 0.05)")
        else:
            print("  -> Ajustement potentiellement insuffisant (p <= 0.05)")
    except Exception as e:
        print(f"Test Hosmer-Lemeshow : {e}")

    # Pseudo R2 supplementaires
    llf = result.llf
    llnull = getattr(result, '_llnull', None)
    if llnull is None:
        llnull = sm.GLM(y, np.ones((len(y), 1)), family=sm.families.Binomial()).fit().llf
    nagelkerke = (1 - np.exp(-2*(llf - llnull)/len(y))) / (1 - np.exp(2*llnull/len(y)))
    mcfadden = getattr(result, '_mcfadden', 1 - llf/llnull)
    print(f"Pseudo R2 de Nagelkerke : {nagelkerke:.4f}")
    print(f"Pseudo R2 de McFadden : {mcfadden:.4f}")

    # Matrice de confusion
    from sklearn.metrics import confusion_matrix, classification_report
    cm = confusion_matrix(y, y_pred_class)
    print(f"\nMatrice de confusion :")
    print(f"  VN={cm[0,0]}, FP={cm[0,1]}, FN={cm[1,0]}, VP={cm[1,1]}")
    print(f"\nRapport de classification :")
    print(classification_report(y, y_pred_class, target_names=['Pas de deces', 'Au moins 1 deces']))

    return auc, y_pred_prob, nagelkerke, mcfadden


# --------------------------------------------------------------------------
# 7. VISUALISATIONS
# --------------------------------------------------------------------------

def plot_roc_curve(y_true, y_pred_prob, auc, output_dir):
    fpr, tpr, _ = roc_curve(y_true, y_pred_prob)
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='#2C5F8A', lw=2, label=f'Courbe ROC (AUC = {auc:.3f})')
    plt.plot([0, 1], [0, 1], 'k--', lw=1, label='Modele aleatoire')
    plt.xlabel('Taux de faux positifs (1 - Specificite)', fontsize=12)
    plt.ylabel('Taux de vrais positifs (Sensibilite)', fontsize=12)
    plt.title('Courbe ROC - Regression Logistique Ponderee', fontsize=14, fontweight='bold')
    plt.legend(loc='lower right', fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'roc_curve_stat.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Courbe ROC sauvegardee.")


def plot_or_forest(or_df, output_dir, title="Odds Ratios - Modele Final", top_n=20):
    """Forest plot des OR significatifs."""
    or_sig = or_df[or_df['Significatif']].head(top_n).sort_values('OR')

    if len(or_sig) == 0:
        print("Aucune variable significative a afficher.")
        return

    fig, ax = plt.subplots(figsize=(10, max(6, len(or_sig) * 0.5)))

    colors = ['#C0392B' if row['OR'] > 1 else '#27AE60' for _, row in or_sig.iterrows()]

    y_pos = range(len(or_sig))
    ax.barh(y_pos, or_sig['OR'] - 1, left=1, color=colors, alpha=0.7, height=0.6)
    ax.errorbar(
        or_sig['OR'], y_pos,
        xerr=[or_sig['OR'] - or_sig['IC_inf_95'], or_sig['IC_sup_95'] - or_sig['OR']],
        fmt='none', color='black', capsize=3, lw=1.5
    )
    ax.scatter(or_sig['OR'], y_pos, color='black', zorder=5, s=30)

    ax.axvline(x=1, color='black', linestyle='--', lw=1.5, label='OR = 1 (pas d effet)')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(or_sig['Variable'].str.replace('_', ' '), fontsize=9)
    ax.set_xlabel('Odds Ratio (IC 95%)', fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold')

    rouge = mpatches.Patch(color='#C0392B', alpha=0.7, label='Facteur de risque (OR > 1)')
    vert = mpatches.Patch(color='#27AE60', alpha=0.7, label='Facteur protecteur (OR < 1)')
    ax.legend(handles=[rouge, vert], fontsize=9, loc='lower right')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'forest_plot_stat.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("Forest plot des OR sauvegarde.")


def plot_prevalence_by_variable(df, output_dir):
    """Prevalence de Y=1 par variables categoriques cles."""
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()

    vars_to_plot = [
        ('education_cat', "Niveau d education"),
        ('milieu_cat', "Milieu de residence"),
        ('richesse_cat', "Quintile de richesse"),
        ('region_cat', "Region"),
        ('union_cat', "Statut matrimonial"),
        ('parite_cat', "Parite"),
    ]

    for idx, (var, label) in enumerate(vars_to_plot):
        if var not in df.columns:
            continue
        ax = axes[idx]
        prev = df.groupby(var)['Y'].mean().sort_values(ascending=False) * 100
        bars = ax.bar(range(len(prev)), prev.values, color='#2C5F8A', alpha=0.8, edgecolor='white')
        ax.set_xticks(range(len(prev)))
        ax.set_xticklabels(prev.index, rotation=45, ha='right', fontsize=8)
        ax.set_ylabel('Prevalence (%)', fontsize=9)
        ax.set_title(label, fontsize=10, fontweight='bold')
        ax.set_ylim(0, min(prev.max() * 1.3, 100))
        for bar, val in zip(bars, prev.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{val:.1f}%', ha='center', va='bottom', fontsize=7)
        ax.axhline(y=df['Y'].mean()*100, color='red', linestyle='--', lw=1, alpha=0.7, label='Prevalence globale')
        ax.legend(fontsize=7)
        ax.grid(axis='y', alpha=0.3)

    plt.suptitle("Prevalence de la mortalite infantile par variables sociodemographiques",
                 fontsize=13, fontweight='bold', y=1.01)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'prevalence_bivariee.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("Graphique de prevalence bivariee sauvegarde.")


# --------------------------------------------------------------------------
# 8. MODELES PROGRESSIFS (Approche blocs)
# --------------------------------------------------------------------------

def run_progressive_models(df_reg, all_predictors, weights):
    """
    Construire 3 modeles progressifs :
    - Modele 1 : Variables sociodemographiques
    - Modele 2 : + Variables de fecondite
    - Modele 3 : + Variables sanitaires (modele complet)
    """
    # Bloc 1 : Sociodemographique
    bloc1_vars = [p for p in all_predictors if any(
        p.startswith(pref) for pref in [
            'education_cat', 'milieu_cat', 'region_cat', 'religion_cat',
            'union_cat', 'richesse_cat', 'emploi_cat', 'age'
        ]
    )]
    bloc1_vars = [p for p in bloc1_vars if p in df_reg.columns]

    # Bloc 2 : + Fecondite
    bloc2_adds = [p for p in all_predictors if any(
        p.startswith(pref) for pref in [
            'parite_cat', 'age_prb_cat', 'naissances_5ans', 'grossesse_interrompue'
        ]
    )]
    bloc2_vars = bloc1_vars + [p for p in bloc2_adds if p in df_reg.columns]

    # Bloc 3 : + Sante (modele complet)
    bloc3_vars = all_predictors

    models = {}

    result1 = run_logistic_model(df_reg, bloc1_vars, weights, "Modele 1 - Sociodemographique")
    models['M1'] = {'result': result1, 'predictors': bloc1_vars}
    or1 = extract_odds_ratios(result1, bloc1_vars)
    print("\nOR Modele 1 (variables significatives) :")
    print(or1[or1['Significatif']].to_string(index=False))

    result2 = run_logistic_model(df_reg, bloc2_vars, weights, "Modele 2 - + Fecondite")
    models['M2'] = {'result': result2, 'predictors': bloc2_vars}
    or2 = extract_odds_ratios(result2, bloc2_vars)
    print("\nOR Modele 2 (variables significatives) :")
    print(or2[or2['Significatif']].to_string(index=False))

    result3 = run_logistic_model(df_reg, bloc3_vars, weights, "Modele 3 - Complet (+ Sante)")
    models['M3'] = {'result': result3, 'predictors': bloc3_vars}
    or3 = extract_odds_ratios(result3, bloc3_vars)
    print("\nOR Modele 3 - Complet (toutes variables) :")
    print(or3.to_string(index=False))

    return models, or1, or2, or3


# --------------------------------------------------------------------------
# 9. TABLEAU DE COMPARAISON DES MODELES
# --------------------------------------------------------------------------

def compare_models(models):
    """Comparer les indicateurs de qualite des 3 modeles."""
    print("\n" + "="*70)
    print("COMPARAISON DES MODELES")
    print("="*70)

    rows = []
    for name, m in models.items():
        r = m['result']
        rows.append({
            'Modele': name,
            'Variables': len(m['predictors']),
            'Log-vraisemblance': round(r.llf, 2),
            'AIC': round(r.aic, 2),
            'BIC': round(r.bic, 2),
            'McFadden R2': round(getattr(r, '_mcfadden', 0), 4),
        })

    comp_df = pd.DataFrame(rows)
    print(comp_df.to_string(index=False))
    return comp_df


# --------------------------------------------------------------------------
# 10. PIPELINE PRINCIPAL
# --------------------------------------------------------------------------

def main():
    print("="*70)
    print("REGRESSION LOGISTIQUE BINAIRE - EDS CAMEROUN 2018")
    print("Facteurs associes a la mortalite infantile")
    print("="*70)

    # Analyse descriptive
    analyse_univariee(df_stat)
    bivariee_results = analyse_bivariee(df_stat)
    bivariee_results.to_csv(os.path.join(OUTPUT_DIR, 'analyse_bivariee.csv'), index=False)

    # Visualisation prevalence
    plot_prevalence_by_variable(df_stat, OUTPUT_DIR)

    # Preparation pour regression
    df_reg, all_predictors = prepare_regression_data(df_stat)
    weights = df_stat['poids_normalise'].fillna(1.0)

    # Test VIF
    vif_df = test_vif(df_reg, all_predictors)
    vif_df.to_csv(os.path.join(OUTPUT_DIR, 'vif_results.csv'), index=False)

    # Supprimer variables avec VIF > 10
    high_vif = vif_df[vif_df['VIF'] > 10]['Variable'].tolist()
    if high_vif:
        print(f"\nSuppression variables VIF > 10 : {high_vif}")
        all_predictors = [p for p in all_predictors if p not in high_vif]

    # Modeles progressifs
    models, or1, or2, or3 = run_progressive_models(df_reg, all_predictors, weights)

    # Comparaison
    comp_df = compare_models(models)
    comp_df.to_csv(os.path.join(OUTPUT_DIR, 'comparaison_modeles.csv'), index=False)

    # Evaluation du modele final
    result_final = models['M3']['result']
    predictors_final = models['M3']['predictors']
    auc, y_pred_prob, nagelkerke, mcfadden = evaluate_model(result_final, df_reg, predictors_final, weights)

    # Visualisations
    y_true = df_reg['Y'].values
    plot_roc_curve(y_true, y_pred_prob, auc, OUTPUT_DIR)
    or3_sorted = extract_odds_ratios(result_final, predictors_final)
    plot_or_forest(or3_sorted, OUTPUT_DIR, "Forest Plot - Odds Ratios Modele Final")

    # Sauvegarder les OR du modele final
    or3_sorted.to_csv(os.path.join(OUTPUT_DIR, 'odds_ratios_final.csv'), index=False)

    # Sauvegarder le modele final pour l'application
    model_artifacts = {
        'result': result_final,
        'predictors': predictors_final,
        'df_reg': df_reg,
        'auc': auc,
        'nagelkerke': nagelkerke,
        'mcfadden': mcfadden,
        'or_df': or3_sorted,
        'bivariee': bivariee_results,
        'comp_models': comp_df,
    }

    with open(r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\stat_model_artifacts.pkl", 'wb') as f:
        pickle.dump(model_artifacts, f)

    print(f"\nModele statistique sauvegarde.")
    print(f"AUC finale : {auc:.4f}")
    print(f"Pseudo R2 Nagelkerke : {nagelkerke:.4f}")

    return model_artifacts


if __name__ == '__main__':
    artifacts = main()
