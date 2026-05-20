"""
Inspection rapide des noms de colonnes du fichier DHS
"""
import pyreadstat
import json

DATA_PATH = r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\CMIR71FL.dta"

print("Chargement des metadonnees uniquement...")
# Lire seulement quelques lignes pour inspecter les colonnes
df, meta = pyreadstat.read_dta(DATA_PATH, row_limit=5)

print(f"Nombre de colonnes : {len(df.columns)}")
print(f"Nombre de lignes (sample) : {len(df)}")

# Sauvegarder tous les noms de colonnes avec leurs labels
col_info = []
for i, col in enumerate(meta.column_names):
    label = meta.column_labels[i] if i < len(meta.column_labels) else ''
    col_info.append({'name': col, 'label': label})

# Sauvegarder en fichier texte
with open('column_names.txt', 'w', encoding='utf-8') as f:
    for ci in col_info:
        f.write(f"{ci['name']}: {ci['label']}\n")

print("Fichier column_names.txt cree.")

# Chercher les variables DHS standards
print("\n--- Recherche variables cles DHS ---")
keywords = ['weight', 'poids', 'cluster', 'strat', 'age', 'education', 'urban', 'region',
            'religion', 'wealth', 'birth', 'child', 'death', 'mort', 'enfant', 'nais',
            'prenatal', 'antenatal', 'delivery', 'income', 'employ']

for kw in keywords:
    matches = [(ci['name'], ci['label']) for ci in col_info
               if kw.lower() in ci['label'].lower() or kw.lower() in ci['name'].lower()]
    if matches:
        print(f"\n[{kw}] -> {len(matches)} matches")
        for name, label in matches[:5]:
            print(f"  {name}: {label}")

# Afficher les 50 premieres colonnes
print("\n--- 50 premieres colonnes ---")
for ci in col_info[:50]:
    print(f"{ci['name']}: {ci['label']}")

# Afficher les colonnes qui ressemblent aux codes DHS standard
print("\n--- Colonnes type DHS (v + chiffres) ---")
dhs_cols = [(ci['name'], ci['label']) for ci in col_info
            if ci['name'].startswith('v') and ci['name'][1:].isdigit()]
print(f"Nombre : {len(dhs_cols)}")
for name, label in dhs_cols[:30]:
    print(f"  {name}: {label}")

# Colonnes commencant par des lettres standards DHS
print("\n--- Colonnes type b (births) ---")
b_cols = [(ci['name'], ci['label']) for ci in col_info
          if ci['name'].startswith('b') and len(ci['name']) > 1]
for name, label in b_cols[:20]:
    print(f"  {name}: {label}")

print("\n--- Sample des premieres valeurs ---")
print(df.iloc[0])
