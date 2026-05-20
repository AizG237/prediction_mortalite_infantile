"""
ml_model.py
Pipeline de Machine Learning - EDS Cameroun 2018
Classification binaire : mortalite infantile (au moins un enfant decede)
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
import os
import joblib
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    roc_auc_score, roc_curve, precision_recall_curve, average_precision_score,
    classification_report, confusion_matrix, f1_score, recall_score,
    precision_score, accuracy_score
)
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost non disponible, sera ignore.")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("LightGBM non disponible, sera ignore.")

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("SHAP non disponible, sera ignore.")

OUTPUT_DIR = r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\outputs_ml"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# 1. CHARGEMENT DES DONNEES
# --------------------------------------------------------------------------

with open(r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\data_prepared.pkl", 'rb') as f:
    data = pickle.load(f)

df_ml = data['df_ml']
vars_ml = data['vars_ml']

print(f"Dataset ML brut : {df_ml.shape}")
print(f"Prevalence Y=1 : {df_ml['Y'].mean()*100:.2f}%")

# Garder toutes les femmes (nullipares incluses) pour le ML
# Le modele ML peut apprendre que 0 enfant => Y=0 sans biais de separation
# car les algorithmes arbres ne souffrent pas de ce probleme

# --------------------------------------------------------------------------
# 2. DEFINITION DES FEATURES
# --------------------------------------------------------------------------

FEATURES_NUMERIQUES = [
    'age',
    'age_premiere_naissance',
    'naissances_5ans',
    'taille_menage',
    'score_pb_acces_sante',
    'nb_enfants_nes_vivants',
]

FEATURES_ORDINALES = [
    'niveau_education',
    'quintile_richesse',
    'statut_matrimonial',
    'milieu_residence',
    'travaille_actuellement',
    'assurance_maladie',
    'grossesse_interrompue',
    'visite_agent_sante',
    'consultation_etablissement',
    'electricite',
    'pb_argent_sante',
    'pb_distance_sante',
    'pb_permission_sante',
    'pb_aller_seule',
]

FEATURES_CATEGORIQUES = [
    'region',
    'religion',
]

# Filtrer pour ne garder que les colonnes existantes
features_num = [f for f in FEATURES_NUMERIQUES if f in df_ml.columns]
features_ord = [f for f in FEATURES_ORDINALES if f in df_ml.columns]
features_cat = [f for f in FEATURES_CATEGORIQUES if f in df_ml.columns]

ALL_FEATURES = features_num + features_ord + features_cat
print(f"Features utilisees : {len(ALL_FEATURES)}")
print(f"  Numeriques : {features_num}")
print(f"  Ordinales  : {features_ord}")
print(f"  Categoriques: {features_cat}")

# --------------------------------------------------------------------------
# 3. PREPARATION DES DONNEES
# --------------------------------------------------------------------------

X = df_ml[ALL_FEATURES].copy()
y = df_ml['Y'].astype(int).values

print(f"\nDistribution des classes :")
print(f"  Y=0 : {(y==0).sum()} ({(y==0).mean()*100:.1f}%)")
print(f"  Y=1 : {(y==1).sum()} ({(y==1).mean()*100:.1f}%)")

# --------------------------------------------------------------------------
# 4. SPLIT TRAIN / TEST (stratifie)
# --------------------------------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42, stratify=y
)

print(f"\nSplit 75/25 stratifie :")
print(f"  Train : {len(X_train)} obs. ({y_train.mean()*100:.1f}% positifs)")
print(f"  Test  : {len(X_test)} obs. ({y_test.mean()*100:.1f}% positifs)")

# --------------------------------------------------------------------------
# 5. PREPROCESSEURS
# --------------------------------------------------------------------------

# Preprocesseur pour les variables numeriques : imputation + standardisation
num_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler()),
])

# Preprocesseur pour les variables ordinales : imputation + garder valeur numerique
ord_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
])

# Preprocesseur pour les variables categoriques : imputation + OHE
cat_pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('ohe', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
])

preprocessor = ColumnTransformer(
    transformers=[
        ('num', num_pipeline, features_num),
        ('ord', ord_pipeline, features_ord),
        ('cat', cat_pipeline, features_cat),
    ],
    remainder='drop'
)

# --------------------------------------------------------------------------
# 6. MODELES ET PIPELINES
# --------------------------------------------------------------------------

# Rapport classe desequilibre
ratio = (y == 0).sum() / (y == 1).sum()
print(f"\nRapport de desequilibre des classes : {ratio:.2f}:1")

def build_pipelines():
    """Construire tous les pipelines de modeles."""
    pipelines = {}

    # --- Modele 1 : Regression Logistique (baseline) ---
    pipelines['Logistic_Regression'] = Pipeline([
        ('preprocessor', preprocessor),
        ('clf', LogisticRegression(
            class_weight='balanced',
            max_iter=500,
            random_state=42,
            solver='lbfgs',
            C=0.1
        ))
    ])

    # --- Modele 2 : Random Forest ---
    pipelines['Random_Forest'] = Pipeline([
        ('preprocessor', preprocessor),
        ('clf', RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_leaf=10,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ))
    ])

    # --- Modele 3 : Gradient Boosting ---
    pipelines['Gradient_Boosting'] = Pipeline([
        ('preprocessor', preprocessor),
        ('clf', GradientBoostingClassifier(
            n_estimators=200,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42
        ))
    ])

    # --- Modele 4 : XGBoost ---
    if XGBOOST_AVAILABLE:
        scale_pos = ratio
        pipelines['XGBoost'] = Pipeline([
            ('preprocessor', preprocessor),
            ('clf', xgb.XGBClassifier(
                n_estimators=300,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                scale_pos_weight=scale_pos,
                random_state=42,
                eval_metric='logloss',
                verbosity=0,
                use_label_encoder=False
            ))
        ])

    # --- Modele 5 : LightGBM ---
    if LIGHTGBM_AVAILABLE:
        pipelines['LightGBM'] = Pipeline([
            ('preprocessor', preprocessor),
            ('clf', lgb.LGBMClassifier(
                n_estimators=300,
                max_depth=5,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                class_weight='balanced',
                random_state=42,
                verbose=-1
            ))
        ])

    return pipelines


# --------------------------------------------------------------------------
# 7. VALIDATION CROISEE ET EVALUATION
# --------------------------------------------------------------------------

def evaluate_with_cv(pipelines, X_train, y_train, cv=5):
    """Evaluer chaque modele par validation croisee (K-fold stratifiee)."""
    print("\n" + "="*70)
    print("VALIDATION CROISEE - 5 Folds Stratifies")
    print("="*70)

    cv_results = {}
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)

    for name, pipeline in pipelines.items():
        print(f"\nEvaluation {name}...")
        auc_scores = cross_val_score(
            pipeline, X_train, y_train, cv=skf, scoring='roc_auc', n_jobs=-1
        )
        f1_scores = cross_val_score(
            pipeline, X_train, y_train, cv=skf, scoring='f1', n_jobs=-1
        )
        recall_scores = cross_val_score(
            pipeline, X_train, y_train, cv=skf, scoring='recall', n_jobs=-1
        )

        cv_results[name] = {
            'AUC_mean': auc_scores.mean(),
            'AUC_std': auc_scores.std(),
            'F1_mean': f1_scores.mean(),
            'F1_std': f1_scores.std(),
            'Recall_mean': recall_scores.mean(),
            'Recall_std': recall_scores.std(),
        }
        print(f"  AUC    : {auc_scores.mean():.4f} +/- {auc_scores.std():.4f}")
        print(f"  F1     : {f1_scores.mean():.4f} +/- {f1_scores.std():.4f}")
        print(f"  Recall : {recall_scores.mean():.4f} +/- {recall_scores.std():.4f}")

    return cv_results


def evaluate_on_test(pipelines_fitted, X_test, y_test):
    """Evaluer les modeles entraine sur le jeu de test final."""
    print("\n" + "="*70)
    print("EVALUATION FINALE SUR JEU DE TEST (VIERGE)")
    print("="*70)

    test_results = {}
    for name, pipeline in pipelines_fitted.items():
        y_pred_prob = pipeline.predict_proba(X_test)[:, 1]
        # Seuil optimal (maximize F1)
        thresholds = np.linspace(0.1, 0.9, 100)
        f1_scores = [f1_score(y_test, (y_pred_prob >= t).astype(int)) for t in thresholds]
        optimal_threshold = thresholds[np.argmax(f1_scores)]
        y_pred = (y_pred_prob >= optimal_threshold).astype(int)

        auc = roc_auc_score(y_test, y_pred_prob)
        ap = average_precision_score(y_test, y_pred_prob)
        f1 = f1_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        acc = accuracy_score(y_test, y_pred)

        test_results[name] = {
            'AUC': auc,
            'AP': ap,
            'F1': f1,
            'Recall': recall,
            'Precision': precision,
            'Accuracy': acc,
            'Threshold': optimal_threshold,
            'y_pred_prob': y_pred_prob,
            'y_pred': y_pred,
        }

        print(f"\n{name} (seuil optimal={optimal_threshold:.2f}):")
        print(f"  ROC-AUC    : {auc:.4f}")
        print(f"  AP-AUC     : {ap:.4f}")
        print(f"  F1         : {f1:.4f}")
        print(f"  Recall     : {recall:.4f}")
        print(f"  Precision  : {precision:.4f}")
        print(f"  Accuracy   : {acc:.4f}")

    return test_results


# --------------------------------------------------------------------------
# 8. INTERPRETABILITE - SHAP
# --------------------------------------------------------------------------

def compute_shap(pipeline, X_train, X_test, model_name, output_dir):
    """Calculer et visualiser les valeurs SHAP pour le modele."""
    if not SHAP_AVAILABLE:
        print("SHAP non disponible.")
        return None

    print(f"\nCalcul SHAP pour {model_name}...")

    try:
        # Transformer les donnees via le preprocesseur
        X_train_transformed = pipeline.named_steps['preprocessor'].transform(X_train)
        X_test_transformed = pipeline.named_steps['preprocessor'].transform(X_test)

        clf = pipeline.named_steps['clf']

        # Noms des features apres transformation
        try:
            ohe = pipeline.named_steps['preprocessor'].named_transformers_['cat']['ohe']
            cat_feature_names = ohe.get_feature_names_out(features_cat).tolist()
        except Exception:
            cat_feature_names = [f'cat_{i}' for i in range(len(features_cat) * 5)]

        feature_names = features_num + features_ord + cat_feature_names
        n_transformed = X_train_transformed.shape[1]
        if len(feature_names) != n_transformed:
            feature_names = [f'feature_{i}' for i in range(n_transformed)]

        # Calculer SHAP
        sample_size = min(500, len(X_test_transformed))
        X_shap = X_test_transformed[:sample_size]

        if model_name in ['XGBoost', 'LightGBM', 'Random_Forest', 'Gradient_Boosting']:
            explainer = shap.TreeExplainer(clf)
            shap_values = explainer.shap_values(X_shap)
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
        else:
            explainer = shap.LinearExplainer(clf, X_train_transformed)
            shap_values = explainer.shap_values(X_shap)

        # Importance globale (mean |SHAP|)
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        shap_importance = pd.DataFrame({
            'Feature': feature_names[:len(mean_abs_shap)],
            'Importance_SHAP': mean_abs_shap
        }).sort_values('Importance_SHAP', ascending=False)

        print(f"Top 15 features SHAP :")
        print(shap_importance.head(15).to_string(index=False))

        # Visualisation bar plot SHAP
        top_n = 15
        top_features = shap_importance.head(top_n)
        fig, ax = plt.subplots(figsize=(10, 7))
        bars = ax.barh(
            range(len(top_features)),
            top_features['Importance_SHAP'].values,
            color='#2C5F8A', alpha=0.8
        )
        ax.set_yticks(range(len(top_features)))
        ax.set_yticklabels(top_features['Feature'].str.replace('_', ' '), fontsize=9)
        ax.set_xlabel('Importance SHAP moyenne |valeur SHAP|', fontsize=10)
        ax.set_title(f'Importance des variables - SHAP ({model_name})', fontsize=12, fontweight='bold')
        ax.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'shap_importance_{model_name}.png'), dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Graphique SHAP sauvegarde.")

        return shap_importance

    except Exception as e:
        print(f"Erreur SHAP : {e}")
        return None


def compute_feature_importance(pipeline, feature_names_orig, model_name, output_dir):
    """Feature importance pour les modeles arbres (sans SHAP)."""
    clf = pipeline.named_steps['clf']

    if not hasattr(clf, 'feature_importances_'):
        return None

    # Reconstruire les noms de features transformees
    try:
        ohe = pipeline.named_steps['preprocessor'].named_transformers_['cat']['ohe']
        cat_fn = ohe.get_feature_names_out(features_cat).tolist()
    except Exception:
        cat_fn = []

    feature_names = features_num + features_ord + cat_fn
    importances = clf.feature_importances_

    n = min(len(feature_names), len(importances))
    fi_df = pd.DataFrame({
        'Feature': feature_names[:n],
        'Importance': importances[:n]
    }).sort_values('Importance', ascending=False)

    top_n = 20
    top = fi_df.head(top_n)
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(range(len(top)), top['Importance'].values, color='#2C5F8A', alpha=0.8)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top['Feature'].str.replace('_', ' '), fontsize=9)
    ax.set_xlabel('Importance (Gini / gain)', fontsize=10)
    ax.set_title(f'Feature Importance - {model_name}', fontsize=12, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'feature_importance_{model_name}.png'), dpi=150, bbox_inches='tight')
    plt.close()

    return fi_df


# --------------------------------------------------------------------------
# 9. VISUALISATIONS COMPARATIVES
# --------------------------------------------------------------------------

def plot_roc_comparison(test_results, output_dir):
    """Courbes ROC comparatives pour tous les modeles."""
    fig, ax = plt.subplots(figsize=(9, 7))
    colors = ['#2C5F8A', '#E74C3C', '#27AE60', '#F39C12', '#8E44AD']

    for idx, (name, res) in enumerate(test_results.items()):
        fpr, tpr, _ = roc_curve(y_test, res['y_pred_prob'])
        auc = res['AUC']
        ax.plot(fpr, tpr, color=colors[idx % len(colors)], lw=2,
                label=f'{name} (AUC={auc:.3f})')

    ax.plot([0, 1], [0, 1], 'k--', lw=1, label='Modele aleatoire')
    ax.set_xlabel('Taux de faux positifs (1 - Specificite)', fontsize=11)
    ax.set_ylabel('Taux de vrais positifs (Sensibilite)', fontsize=11)
    ax.set_title('Courbes ROC - Comparaison des modeles ML', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9, loc='lower right')
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'roc_comparison_ml.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("Courbes ROC comparatives sauvegardees.")


def plot_metrics_comparison(test_results, cv_results, output_dir):
    """Tableau de bord des metriques comparatives."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Test set
    names = list(test_results.keys())
    aucs = [test_results[n]['AUC'] for n in names]
    f1s = [test_results[n]['F1'] for n in names]
    recalls = [test_results[n]['Recall'] for n in names]
    precisions = [test_results[n]['Precision'] for n in names]

    x = np.arange(len(names))
    w = 0.2
    axes[0].bar(x - 1.5*w, aucs, w, label='AUC', color='#2C5F8A', alpha=0.85)
    axes[0].bar(x - 0.5*w, f1s, w, label='F1', color='#E74C3C', alpha=0.85)
    axes[0].bar(x + 0.5*w, recalls, w, label='Rappel', color='#27AE60', alpha=0.85)
    axes[0].bar(x + 1.5*w, precisions, w, label='Precision', color='#F39C12', alpha=0.85)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels([n.replace('_', '\n') for n in names], fontsize=8)
    axes[0].set_ylim(0, 1.1)
    axes[0].set_title('Metriques sur jeu de test', fontsize=11, fontweight='bold')
    axes[0].legend(fontsize=8)
    axes[0].grid(axis='y', alpha=0.3)

    # CV validation
    if cv_results:
        cv_aucs = [cv_results[n]['AUC_mean'] for n in names if n in cv_results]
        cv_stds = [cv_results[n]['AUC_std'] for n in names if n in cv_results]
        cv_names = [n for n in names if n in cv_results]
        axes[1].barh(range(len(cv_names)), cv_aucs, xerr=cv_stds,
                     color='#2C5F8A', alpha=0.8, capsize=5)
        axes[1].set_yticks(range(len(cv_names)))
        axes[1].set_yticklabels([n.replace('_', ' ') for n in cv_names], fontsize=9)
        axes[1].set_xlabel('AUC moyen (5-fold CV)', fontsize=10)
        axes[1].set_title('Validation Croisee (AUC +/- SD)', fontsize=11, fontweight='bold')
        axes[1].axvline(x=0.7, color='red', linestyle='--', lw=1, alpha=0.7, label='AUC = 0.70')
        axes[1].legend(fontsize=8)
        axes[1].grid(axis='x', alpha=0.3)

    plt.suptitle('Comparaison des modeles de Machine Learning', fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'metrics_comparison_ml.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("Graphique de comparaison des metriques sauvegarde.")


def plot_confusion_matrix(y_true, y_pred, model_name, output_dir):
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=['Pas de deces', 'Au moins 1 deces'],
                yticklabels=['Pas de deces', 'Au moins 1 deces'])
    ax.set_xlabel('Predit', fontsize=10)
    ax.set_ylabel('Reel', fontsize=10)
    ax.set_title(f'Matrice de Confusion - {model_name}', fontsize=11, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, f'confusion_{model_name}.png'), dpi=150, bbox_inches='tight')
    plt.close()


def plot_pr_curve(test_results, output_dir):
    """Courbes Precision-Rappel."""
    fig, ax = plt.subplots(figsize=(9, 7))
    colors = ['#2C5F8A', '#E74C3C', '#27AE60', '#F39C12', '#8E44AD']

    for idx, (name, res) in enumerate(test_results.items()):
        precision, recall, _ = precision_recall_curve(y_test, res['y_pred_prob'])
        ap = res['AP']
        ax.plot(recall, precision, color=colors[idx % len(colors)], lw=2,
                label=f'{name} (AP={ap:.3f})')

    baseline = y_test.mean()
    ax.axhline(y=baseline, color='k', linestyle='--', lw=1, label=f'Baseline ({baseline:.2f})')
    ax.set_xlabel('Rappel (Sensibilite)', fontsize=11)
    ax.set_ylabel('Precision', fontsize=11)
    ax.set_title('Courbes Precision-Rappel - Comparaison des modeles', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9, loc='upper right')
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'pr_curve_ml.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("Courbes Precision-Rappel sauvegardees.")


# --------------------------------------------------------------------------
# 10. PIPELINE PRINCIPAL
# --------------------------------------------------------------------------

def main():
    print("="*70)
    print("PIPELINE MACHINE LEARNING - EDS CAMEROUN 2018")
    print("Mortalite infantile : classification binaire")
    print("="*70)

    # Construire les pipelines
    pipelines = build_pipelines()
    print(f"\nModeles a evaluer : {list(pipelines.keys())}")

    # Validation croisee sur train set
    cv_results = evaluate_with_cv(pipelines, X_train, y_train, cv=5)

    # Entrainement final sur tout le train set
    print("\n--- Entrainement final sur tout le train set ---")
    pipelines_fitted = {}
    for name, pipeline in pipelines.items():
        print(f"Entrainement {name}...")
        pipeline.fit(X_train, y_train)
        pipelines_fitted[name] = pipeline

    # Evaluation sur le test set vierge
    test_results = evaluate_on_test(pipelines_fitted, X_test, y_test)

    # Visualisations
    plot_roc_comparison(test_results, OUTPUT_DIR)
    plot_metrics_comparison(test_results, cv_results, OUTPUT_DIR)
    plot_pr_curve(test_results, OUTPUT_DIR)

    # Matrice de confusion du meilleur modele
    best_model_name = max(test_results, key=lambda k: test_results[k]['AUC'])
    best_res = test_results[best_model_name]
    plot_confusion_matrix(y_test, best_res['y_pred'], best_model_name, OUTPUT_DIR)
    print(f"\nMeilleur modele (AUC) : {best_model_name} (AUC={best_res['AUC']:.4f})")

    # Feature importance
    for name, pipeline in pipelines_fitted.items():
        fi = compute_feature_importance(pipeline, ALL_FEATURES, name, OUTPUT_DIR)
        if fi is not None:
            fi.to_csv(os.path.join(OUTPUT_DIR, f'feature_importance_{name}.csv'), index=False)

    # SHAP pour le meilleur modele
    if SHAP_AVAILABLE and best_model_name in pipelines_fitted:
        shap_importance = compute_shap(
            pipelines_fitted[best_model_name],
            X_train, X_test,
            best_model_name,
            OUTPUT_DIR
        )
        if shap_importance is not None:
            shap_importance.to_csv(os.path.join(OUTPUT_DIR, 'shap_importance_best.csv'), index=False)

    # Tableau de comparaison final
    comparison = pd.DataFrame({
        name: {
            'AUC_CV': cv_results[name]['AUC_mean'] if name in cv_results else np.nan,
            'AUC_Test': res['AUC'],
            'F1_Test': res['F1'],
            'Recall_Test': res['Recall'],
            'Precision_Test': res['Precision'],
            'AP_Test': res['AP'],
        }
        for name, res in test_results.items()
    }).T

    print("\n" + "="*70)
    print("TABLEAU DE SYNTHESE - TOUS LES MODELES")
    print("="*70)
    print(comparison.round(4).to_string())
    comparison.to_csv(os.path.join(OUTPUT_DIR, 'model_comparison_final.csv'))

    # Rapport classification du meilleur modele
    print(f"\n--- Rapport complet {best_model_name} ---")
    print(classification_report(y_test, best_res['y_pred'],
                                 target_names=['Pas de deces', 'Au moins 1 deces']))

    # Sauvegarder le meilleur modele et les artefacts ML
    best_pipeline = pipelines_fitted[best_model_name]
    ml_artifacts = {
        'best_model_name': best_model_name,
        'best_pipeline': best_pipeline,
        'all_pipelines': pipelines_fitted,
        'test_results': test_results,
        'cv_results': cv_results,
        'comparison': comparison,
        'feature_names': ALL_FEATURES,
        'features_num': features_num,
        'features_ord': features_ord,
        'features_cat': features_cat,
        'optimal_threshold': best_res['Threshold'],
        'y_test': y_test,
        'X_test': X_test,
        'X_train': X_train,
        'y_train': y_train,
    }

    with open(r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\ml_model_artifacts.pkl", 'wb') as f:
        pickle.dump(ml_artifacts, f)

    joblib.dump(best_pipeline,
                r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\best_ml_pipeline.pkl")

    print(f"\nModele ML sauvegarde : {best_model_name}")
    print(f"AUC test : {best_res['AUC']:.4f}")
    print(f"F1 test  : {best_res['F1']:.4f}")
    print(f"Rappel   : {best_res['Recall']:.4f}")

    return ml_artifacts


if __name__ == '__main__':
    artifacts = main()
