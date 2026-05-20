"""
data_cleaning.py
Preparation des donnees EDS Cameroun 2018 pour la regression logistique
et le machine learning - Mortalite infantile
"""
import pandas as pd
import numpy as np
import pyreadstat
import warnings
warnings.filterwarnings('ignore')

DATA_PATH = r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\CMIR71FL.dta"

# --------------------------------------------------------------------------
# 1. CHARGEMENT DES DONNEES
# --------------------------------------------------------------------------

def load_data():
    print("Chargement des donnees EDS Cameroun 2018...")
    df, meta = pyreadstat.read_dta(DATA_PATH)
    print(f"Donnees brutes : {df.shape[0]} observations, {df.shape[1]} variables")

    # Dictionnaire label -> nom de variable pour reference
    label_map = {meta.column_labels[i]: name for i, name in enumerate(meta.column_names)}
    value_labels = meta.variable_value_labels

    return df, meta, value_labels


# --------------------------------------------------------------------------
# 2. SELECTION DES VARIABLES PERTINENTES
# --------------------------------------------------------------------------

VARIABLES_CLES = {
    # Sondage (design variables)
    'V005': 'poids',
    'V021': 'cluster_psu',
    'V022': 'strate',

    # Variable dependante (construction de Y)
    'V201': 'nb_enfants_nes_vivants',
    'V206': 'fils_decedes',
    'V207': 'filles_decedees',
    'V218': 'nb_enfants_vivants',

    # Sociodemographiques
    'V012': 'age',
    'V013': 'age_groupe',
    'V106': 'niveau_education',
    'V149': 'niveau_education_atteint',
    'V025': 'milieu_residence',
    'V024': 'region',
    'V130': 'religion',
    'V501': 'statut_matrimonial',
    'V190': 'quintile_richesse',

    # Emploi
    'V714': 'travaille_actuellement',
    'V731': 'travaille_12mois',

    # Fecondite
    'V212': 'age_premiere_naissance',
    'V208': 'naissances_5ans',
    'V228': 'grossesse_interrompue',
    'V213': 'enceinte_actuellement',
    'V511': 'age_premier_mariage',

    # Sante / acces aux soins
    'V481': 'assurance_maladie',
    'V467B': 'pb_permission_sante',
    'V467C': 'pb_argent_sante',
    'V467D': 'pb_distance_sante',
    'V467F': 'pb_aller_seule',
    'V393': 'visite_agent_sante',
    'V394': 'consultation_etablissement',

    # Contraception
    'V313': 'contraception_actuelle',
    'V302A': 'deja_utilise_contraception',

    # Caracteristiques menage
    'V136': 'taille_menage',
    'V137': 'enfants_moins5',
    'V119': 'electricite',
    'V155': 'literacie',

    # Soins prenataux (pour dernier enfant - V4xx series)
    'V367': 'voulait_dernier_enfant',
}


def select_and_rename(df):
    """Selectionner les variables utiles et les renommer."""
    cols_present = {k: v for k, v in VARIABLES_CLES.items() if k in df.columns}
    cols_absent = [k for k in VARIABLES_CLES if k not in df.columns]
    if cols_absent:
        print(f"Variables absentes (ignorees) : {cols_absent}")

    df_sel = df[list(cols_present.keys())].copy()
    df_sel = df_sel.rename(columns=cols_present)
    print(f"Variables selectionnees : {df_sel.shape[1]}")
    return df_sel


# --------------------------------------------------------------------------
# 3. CONSTRUCTION DE LA VARIABLE CIBLE Y
# --------------------------------------------------------------------------

def build_target(df):
    """
    Y = 1 si la femme a perdu au moins un enfant (fils ou fille decede)
    Y = 0 sinon
    """
    # Methode 1 : somme directe des deces
    if 'fils_decedes' in df.columns and 'filles_decedees' in df.columns:
        df['enfants_decedes'] = df['fils_decedes'].fillna(0) + df['filles_decedees'].fillna(0)
    elif 'nb_enfants_nes_vivants' in df.columns and 'nb_enfants_vivants' in df.columns:
        # Methode 2 : difference
        df['enfants_decedes'] = (
            df['nb_enfants_nes_vivants'].fillna(0) - df['nb_enfants_vivants'].fillna(0)
        ).clip(lower=0)
    else:
        raise ValueError("Impossible de construire la variable mortalite")

    # Y binaire
    df['Y'] = (df['enfants_decedes'] > 0).astype(int)

    # Coherence : si jamais eu d'enfant -> deces impossible -> Y = 0
    if 'nb_enfants_nes_vivants' in df.columns:
        mask_nullipare = df['nb_enfants_nes_vivants'] == 0
        df.loc[mask_nullipare, 'Y'] = 0
        df.loc[mask_nullipare, 'enfants_decedes'] = 0

    # Verification
    n_total = len(df)
    n_deces = df['Y'].sum()
    print(f"\nVariable cible construite :")
    print(f"  Y = 1 (au moins un enfant decede) : {n_deces} ({n_deces/n_total*100:.1f}%)")
    print(f"  Y = 0 (aucun enfant decede)        : {n_total - n_deces} ({(n_total-n_deces)/n_total*100:.1f}%)")

    return df


# --------------------------------------------------------------------------
# 4. NETTOYAGE ET RECODAGE DES VARIABLES
# --------------------------------------------------------------------------

def clean_variables(df):
    """Nettoyage systematique des variables."""

    # --- Age ---
    df['age'] = pd.to_numeric(df['age'], errors='coerce')
    df.loc[(df['age'] < 15) | (df['age'] > 49), 'age'] = np.nan

    # --- Niveau d'education ---
    # 0=Aucun, 1=Primaire, 2=Secondaire, 3=Superieur
    df['niveau_education'] = pd.to_numeric(df['niveau_education'], errors='coerce')
    df['education_cat'] = df['niveau_education'].map({
        0: 'Aucun',
        1: 'Primaire',
        2: 'Secondaire',
        3: 'Superieur'
    })

    # --- Milieu de residence ---
    # 1=Urbain, 2=Rural
    df['milieu_residence'] = pd.to_numeric(df['milieu_residence'], errors='coerce')
    df['milieu_cat'] = df['milieu_residence'].map({1: 'Urbain', 2: 'Rural'})

    # --- Region ---
    df['region'] = pd.to_numeric(df['region'], errors='coerce')
    # Regions Cameroun 2018 : 1-10 correspondant aux 10 regions
    region_labels = {
        1: 'Adamawa', 2: 'Centre', 3: 'Est', 4: 'Extreme-Nord',
        5: 'Littoral', 6: 'Nord', 7: 'Nord-Ouest', 8: 'Ouest',
        9: 'Sud', 10: 'Sud-Ouest'
    }
    df['region_cat'] = df['region'].map(region_labels)
    df.loc[df['region_cat'].isna() & df['region'].notna(), 'region_cat'] = 'Autre'

    # --- Religion ---
    df['religion'] = pd.to_numeric(df['religion'], errors='coerce')
    religion_labels = {
        1: 'Catholique', 2: 'Protestant', 3: 'Autre_Chretien',
        4: 'Musulman', 5: 'Animiste', 6: 'Aucune', 96: 'Autre'
    }
    df['religion_cat'] = df['religion'].map(religion_labels)
    df.loc[df['religion_cat'].isna() & df['religion'].notna(), 'religion_cat'] = 'Autre'

    # --- Statut matrimonial ---
    df['statut_matrimonial'] = pd.to_numeric(df['statut_matrimonial'], errors='coerce')
    df['union_cat'] = df['statut_matrimonial'].apply(lambda x:
        'En_union' if x in [1, 2] else ('Jamais_union' if x == 0 else ('Ex_union' if x in [3, 4, 5] else np.nan))
    )

    # --- Quintile de richesse ---
    df['quintile_richesse'] = pd.to_numeric(df['quintile_richesse'], errors='coerce')
    richesse_labels = {
        1: 'Tres_pauvre', 2: 'Pauvre', 3: 'Moyen', 4: 'Riche', 5: 'Tres_riche'
    }
    df['richesse_cat'] = df['quintile_richesse'].map(richesse_labels)

    # --- Emploi ---
    df['travaille_actuellement'] = pd.to_numeric(df['travaille_actuellement'], errors='coerce')
    df['emploi_cat'] = df['travaille_actuellement'].map({0: 'Non', 1: 'Oui'})

    # --- Age premiere naissance ---
    df['age_premiere_naissance'] = pd.to_numeric(df['age_premiere_naissance'], errors='coerce')
    df.loc[df['age_premiere_naissance'] > 49, 'age_premiere_naissance'] = np.nan

    # Recoder en categories
    def categorise_age_prb(age):
        if pd.isna(age):
            return np.nan
        elif age < 18:
            return 'Moins_18ans'
        elif age < 20:
            return '18_19ans'
        elif age < 25:
            return '20_24ans'
        else:
            return '25_et_plus'
    df['age_prb_cat'] = df['age_premiere_naissance'].apply(categorise_age_prb)

    # --- Nombre de naissances recentes ---
    df['naissances_5ans'] = pd.to_numeric(df['naissances_5ans'], errors='coerce')

    # --- Assurance maladie ---
    df['assurance_maladie'] = pd.to_numeric(df['assurance_maladie'], errors='coerce')
    df['assurance_cat'] = df['assurance_maladie'].map({0: 'Non', 1: 'Oui'})

    # --- Acces aux soins ---
    for col in ['pb_permission_sante', 'pb_argent_sante', 'pb_distance_sante', 'pb_aller_seule']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].map({1: 1, 2: 0})  # 1=gros probleme, 2=pas probleme -> 1/0

    # Score acces sante (0 = bon acces, 4 = tres mauvais acces)
    pb_cols = [c for c in ['pb_permission_sante', 'pb_argent_sante', 'pb_distance_sante', 'pb_aller_seule']
               if c in df.columns]
    if pb_cols:
        df['score_pb_acces_sante'] = df[pb_cols].sum(axis=1, min_count=1)

    # --- Contraception ---
    df['contraception_actuelle'] = pd.to_numeric(df['contraception_actuelle'], errors='coerce')
    df['contraception_cat'] = df['contraception_actuelle'].apply(lambda x:
        'Aucune' if x == 0 else ('Moderne' if x == 3 else ('Traditionnelle' if x == 2 else ('Folklore' if x == 1 else np.nan)))
    )

    # --- Visite sante ---
    df['visite_agent_sante'] = pd.to_numeric(df['visite_agent_sante'], errors='coerce').map({0: 0, 1: 1})
    df['consultation_etablissement'] = pd.to_numeric(df['consultation_etablissement'], errors='coerce').map({0: 0, 1: 1})

    # --- Electricite menage ---
    df['electricite'] = pd.to_numeric(df['electricite'], errors='coerce')
    df['electricite'] = df['electricite'].apply(lambda x: 1 if x == 1 else (0 if x == 0 else np.nan))

    # --- Literacie ---
    df['literacie'] = pd.to_numeric(df['literacie'], errors='coerce')
    df['literacie_cat'] = df['literacie'].map({0: 'Analphabete', 1: 'Partiellement', 2: 'Completement'})

    # --- Grossesse interrompue ---
    df['grossesse_interrompue'] = pd.to_numeric(df['grossesse_interrompue'], errors='coerce').map({0: 0, 1: 1})

    # --- Taille menage ---
    df['taille_menage'] = pd.to_numeric(df['taille_menage'], errors='coerce')
    df.loc[df['taille_menage'] > 30, 'taille_menage'] = np.nan  # valeurs aberrantes

    # --- Nb enfants nes vivants ---
    df['nb_enfants_nes_vivants'] = pd.to_numeric(df['nb_enfants_nes_vivants'], errors='coerce')

    # Parite : nombre d'enfants (variable continue + categorielle)
    df['parite_cat'] = df['nb_enfants_nes_vivants'].apply(lambda x:
        '0' if x == 0 else ('1_2' if x <= 2 else ('3_4' if x <= 4 else '5_plus'))
        if not pd.isna(x) else np.nan
    )

    # --- Age au mariage ---
    if 'age_premier_mariage' in df.columns:
        df['age_premier_mariage'] = pd.to_numeric(df['age_premier_mariage'], errors='coerce')
        df.loc[df['age_premier_mariage'] > 49, 'age_premier_mariage'] = np.nan

    # --- Voulait dernier enfant ---
    if 'voulait_dernier_enfant' in df.columns:
        df['voulait_dernier_enfant'] = pd.to_numeric(df['voulait_dernier_enfant'], errors='coerce')
        df['voulait_enfant_cat'] = df['voulait_dernier_enfant'].map({
            1: 'Voulait_alors', 2: 'Voulait_plus_tard', 3: 'Ne_voulait_plus'
        })

    # --- Poids d'echantillonnage ---
    df['poids'] = pd.to_numeric(df['poids'], errors='coerce')
    df['poids_normalise'] = df['poids'] / 1_000_000  # Division par 10^6 selon standard DHS

    print("Nettoyage et recodage effectues.")
    return df


# --------------------------------------------------------------------------
# 5. GESTION DES VALEURS MANQUANTES
# --------------------------------------------------------------------------

def handle_missing(df, variables_modelisation):
    """
    Gestion des valeurs manquantes pour les variables du modele.
    Approche : exclusion des observations avec NA sur les variables critiques,
    imputation par la mediane/mode pour les autres.
    """
    df_model = df[variables_modelisation + ['Y', 'poids_normalise', 'cluster_psu', 'strate']].copy()

    print(f"\nObservations initiales : {len(df_model)}")

    # Valeurs manquantes par variable
    na_counts = df_model.isnull().sum()
    print("\nValeurs manquantes :")
    for col, n in na_counts[na_counts > 0].items():
        print(f"  {col}: {n} ({n/len(df_model)*100:.1f}%)")

    # Supprimer les observations avec Y manquant
    df_model = df_model.dropna(subset=['Y'])

    # Pour les variables explicatives, imputer
    # Variables numeriques -> mediane
    num_cols = df_model.select_dtypes(include=[np.number]).columns.tolist()
    num_cols = [c for c in num_cols if c not in ['Y', 'poids_normalise', 'cluster_psu', 'strate']]
    for col in num_cols:
        if df_model[col].isna().sum() > 0:
            median_val = df_model[col].median()
            df_model[col] = df_model[col].fillna(median_val)

    # Variables categoriques -> mode
    cat_cols = df_model.select_dtypes(include=['object']).columns.tolist()
    for col in cat_cols:
        if df_model[col].isna().sum() > 0:
            mode_val = df_model[col].mode()[0] if not df_model[col].mode().empty else 'Inconnu'
            df_model[col] = df_model[col].fillna(mode_val)

    print(f"Observations apres nettoyage : {len(df_model)}")
    print(f"Prevalence Y=1 : {df_model['Y'].mean()*100:.2f}%")

    return df_model


# --------------------------------------------------------------------------
# 6. PIPELINE COMPLET
# --------------------------------------------------------------------------

# Variables pour la modelisation statistique
VARIABLES_STAT = [
    'age',
    'education_cat',
    'milieu_cat',
    'region_cat',
    'religion_cat',
    'union_cat',
    'richesse_cat',
    'emploi_cat',
    'age_prb_cat',
    'parite_cat',
    'assurance_cat',
    'grossesse_interrompue',
    'visite_agent_sante',
    'consultation_etablissement',
    'score_pb_acces_sante',
    'naissances_5ans',
    'electricite',
    'taille_menage',
]

# Variables pour le modele ML (inclut les variables numeriques brutes)
VARIABLES_ML = [
    'age',
    'niveau_education',
    'milieu_residence',
    'region',
    'religion',
    'statut_matrimonial',
    'quintile_richesse',
    'travaille_actuellement',
    'age_premiere_naissance',
    'naissances_5ans',
    'assurance_maladie',
    'grossesse_interrompue',
    'visite_agent_sante',
    'consultation_etablissement',
    'score_pb_acces_sante',
    'electricite',
    'taille_menage',
    'nb_enfants_nes_vivants',
    'pb_argent_sante',
    'pb_distance_sante',
    'pb_permission_sante',
    'pb_aller_seule',
]


def run_pipeline():
    """Pipeline complet de preparation des donnees."""
    df_raw, meta, value_labels = load_data()
    df_sel = select_and_rename(df_raw)
    df_clean = clean_variables(df_sel)
    df_clean = build_target(df_clean)

    # Filtrer les femmes ayant deja eu au moins un enfant pour eviter biais
    # (une femme sans enfant ne peut pas avoir perdu un enfant)
    # Mais on garde les nullipares comme Y=0 pour refleter la vraie population
    # -> Decision : inclure TOUTES les femmes de 15-49 ans

    # Verifier la coherence
    if 'nb_enfants_nes_vivants' in df_clean.columns:
        incoherence = (
            (df_clean['nb_enfants_nes_vivants'] == 0) & (df_clean['Y'] == 1)
        ).sum()
        if incoherence > 0:
            print(f"Incoherences corrigees : {incoherence} femmes sans enfant marquees Y=1")
            df_clean.loc[df_clean['nb_enfants_nes_vivants'] == 0, 'Y'] = 0

    # Nettoyer les variables ML
    vars_ml_present = [v for v in VARIABLES_ML if v in df_clean.columns]
    df_ml = handle_missing(df_clean, vars_ml_present)

    # Nettoyer les variables stat
    vars_stat_present = [v for v in VARIABLES_STAT if v in df_clean.columns]
    df_stat = handle_missing(df_clean, vars_stat_present)

    return df_clean, df_stat, df_ml, vars_stat_present, vars_ml_present


if __name__ == '__main__':
    df_clean, df_stat, df_ml, vars_stat, vars_ml = run_pipeline()

    print("\n=== Resume final ===")
    print(f"Dataset statistique : {df_stat.shape}")
    print(f"Dataset ML : {df_ml.shape}")
    print(f"\nVariables statistique : {vars_stat}")
    print(f"\nVariables ML : {vars_ml}")

    # Sauvegarder pour reutilisation
    import pickle
    with open('data_prepared.pkl', 'wb') as f:
        pickle.dump({
            'df_clean': df_clean,
            'df_stat': df_stat,
            'df_ml': df_ml,
            'vars_stat': vars_stat,
            'vars_ml': vars_ml
        }, f)
    print("\nDonnees sauvegardees dans data_prepared.pkl")
