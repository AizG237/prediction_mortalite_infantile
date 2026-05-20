"""
Exploration initiale des donnees EDS Cameroun 2018
Fichier femmes (IR file) : CMIR71FL.dta
"""
import pandas as pd
import numpy as np
import pyreadstat
import warnings
warnings.filterwarnings('ignore')

DATA_PATH = r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\CMIR71FL.dta"

print("Chargement des donnees...")
df, meta = pyreadstat.read_dta(DATA_PATH)
print(f"Dimensions : {df.shape}")
print(f"Nombre de variables : {df.shape[1]}")
print(f"Nombre d'observations : {df.shape[0]}")

# Variables cles pour la construction de Y
key_vars = [
    'v005',   # poids echantillonnage
    'v021',   # cluster (PSU)
    'v022',   # strate
    'v012',   # age de la femme
    'v106',   # niveau d'education
    'v025',   # milieu de residence (urbain/rural)
    'v024',   # region
    'v130',   # religion
    'v501',   # statut matrimonial
    'v190',   # indice de richesse
    'v714',   # emploi actuel
    'v201',   # nombre total d'enfants nes vivants
    'v218',   # nombre d'enfants vivants actuellement
    'v228',   # fausse couche, avortement
    'v208',   # naissance dans les 5 dernieres annees
    'v212',   # age a la premiere naissance
    'v511',   # age au premier mariage
    'v313',   # methode contraceptive actuelle
    'v302',   # connaissance contraception
    'v326',   # source de la methode actuelle
    'm14',    # nombre de visites prenatales
    'v393',   # consulte medecin pour soi
    'v394',   # consulte sage-femme pour soi
    'v367',   # voulait derniere naissance
    'v376',   # raison non utilisation contraception
    'v404',   # allaitement actuellement
    'b5_01',  # dernier enfant vivant
    'v137',   # enfants moins de 5 ans dans menage
    'v136',   # nombre membres menage
    'v149',   # niveau education atteint
    'v155',   # literacie
    'v716',   # occupation
    'v731',   # travaillé pendant 12 derniers mois
    'v481',   # assurance maladie
    'v467d',  # distance = gros probleme acces sante
    'v467b',  # permission sortir = gros probleme acces sante
    'v467f',  # avoir argent = gros probleme acces sante
    'v467c',  # ne pas vouloir aller seule
]

print("\n--- Verification des variables cles ---")
existing = []
missing = []
for v in key_vars:
    if v in df.columns:
        existing.append(v)
    else:
        missing.append(v)

print(f"Variables presentes : {len(existing)}")
print(f"Variables absentes : {len(missing)}")
if missing:
    print(f"Absentes : {missing}")

print("\n--- Variables pour construction de Y ---")
y_vars = ['v201', 'v218']
for v in y_vars:
    if v in df.columns:
        print(f"\n{v}:")
        print(df[v].describe())
        print(f"NaN: {df[v].isna().sum()}")

# Construction de Y
if 'v201' in df.columns and 'v218' in df.columns:
    df['enfants_decedes'] = df['v201'] - df['v218']
    df['Y'] = (df['enfants_decedes'] > 0).astype(int)
    print(f"\nDistribution de Y (deces enfant):")
    print(df['Y'].value_counts())
    print(f"Prevalence : {df['Y'].mean()*100:.2f}%")

print("\n--- Toutes les colonnes disponibles (echantillon) ---")
# Chercher les variables pertinentes par nom
dhs_vars_interest = [c for c in df.columns if c.startswith(('v0', 'v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'm', 'b', 'ml', 's'))]
print(f"Variables DHS disponibles : {len(dhs_vars_interest)}")
print(dhs_vars_interest[:100])

# Sauvegarder les metadata
with open(r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\variable_labels.txt", 'w', encoding='utf-8') as f:
    for col in df.columns:
        label = meta.column_labels[meta.column_names.index(col)] if col in meta.column_names else ''
        f.write(f"{col}: {label}\n")

print("\nLabels des variables sauvegardes dans variable_labels.txt")
print("\n--- Apercu des labels des variables cles ---")
for v in existing[:20]:
    idx = meta.column_names.index(v)
    print(f"{v}: {meta.column_labels[idx]}")
