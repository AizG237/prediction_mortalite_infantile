"""
Inspection ciblee des variables DHS cles
"""
import pyreadstat

DATA_PATH = r"c:\Users\Ing Yannick\Desktop\MaSaJe\stats Mult\projet_regression_python\CMIR71FL.dta"
df, meta = pyreadstat.read_dta(DATA_PATH, row_limit=100)

col_map = {ci: meta.column_labels[i] for i, ci in enumerate(meta.column_names)}

# Variables cles connues (uppercase dans ce fichier)
key_vars = [
    'V005', 'V021', 'V022', 'V023', 'V012', 'V013', 'V106', 'V107', 'V149',
    'V025', 'V024', 'V101', 'V130', 'V501', 'V502', 'V190', 'V191',
    'V714', 'V716', 'V731', 'V732',
    'V201', 'V202', 'V203', 'V204', 'V205', 'V206', 'V207', 'V208',
    'V218', 'V219', 'V220',
    'V212', 'V213', 'V511', 'V512',
    'V228', 'V229', 'V230',
    'V481', 'V467A', 'V467B', 'V467C', 'V467D', 'V467E', 'V467F',
    'V137', 'V136', 'V135', 'V138',
    'V155', 'V157', 'V158',
    'V302', 'V313', 'V326',
    'V367', 'V376', 'V393', 'V394', 'V404',
    'M14', 'M15', 'M17', 'M18', 'M19', 'M19A',
    'V301', 'V302A',
    'V133', 'V119', 'V120', 'V121', 'V122', 'V123',
    'V124', 'V125', 'V126', 'V127', 'V128', 'V129',
]

print("=== Variables cles trouvees ===")
for v in key_vars:
    if v in df.columns:
        label = col_map.get(v, '')
        sample_vals = df[v].dropna().unique()[:5]
        print(f"{v}: {label}")
        print(f"   Vals: {sample_vals}")
    else:
        print(f"{v}: NON TROUVE")

# Variables de mortalite specifiques
print("\n=== Variables mortalite ===")
mort_keywords = ['dead', 'alive', 'living', 'surviv', 'mort', 'deces', 'enfant', 'born', 'birth', 'child ever']
for name, label in col_map.items():
    for kw in mort_keywords:
        if kw.lower() in label.lower() and not name.startswith('_'):
            print(f"{name}: {label}")
            break

print("\n=== Recherche V2xx (variables enfants) ===")
for name, label in col_map.items():
    if name.startswith('V2') and not name.startswith('_'):
        print(f"{name}: {label}")

print("\n=== Variables M (maternite) non-prefixees ===")
for name, label in col_map.items():
    if len(name) >= 2 and name[0] == 'M' and name[1:].replace('_','').isdigit() and not name.startswith('_'):
        print(f"{name}: {label}")
