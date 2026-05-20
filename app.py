"""
app.py
Application Streamlit - Evaluation du Risque de Mortalite Infantile
EDS Cameroun 2018 | Double methode : Statistique + Machine Learning
"""
import streamlit as st
import pandas as pd
import numpy as np
import pickle
import joblib
import warnings
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import statsmodels.api as sm
import os

warnings.filterwarnings('ignore')

# --------------------------------------------------------------------------
# CONFIGURATION PAGE
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="Risque de Mortalite Infantile - Cameroun",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# CSS PERSONNALISE
# --------------------------------------------------------------------------

st.markdown("""
<style>
    /* Fond general */
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }

    /* Forcer le texte sombre sur fond clair - correction couleurs Streamlit */
    .stApp, .main .block-container, .stMarkdown, .stText,
    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] ul,
    [data-testid="stMarkdownContainer"] h1,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4,
    .stExpander label,
    .stExpander [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    .element-container p,
    .element-container li {
        color: #1a1a2e !important;
    }

    /* Titres de sections Streamlit */
    h1, h2, h3, h4, h5, h6 {
        color: #1a3a5c !important;
    }

    /* Metriques Streamlit */
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricDelta"] {
        color: #1a1a2e !important;
    }

    /* Checkbox et radio labels */
    .stCheckbox label,
    .stRadio label,
    .stSelectbox label,
    .stSlider label,
    .stNumberInput label,
    label {
        color: #1a1a2e !important;
    }

    /* Sidebar fond blanc et texte sombre */
    section[data-testid="stSidebar"] {
        background: white;
    }
    section[data-testid="stSidebar"] * {
        color: #1a1a2e !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        color: #1a3a5c !important;
    }

    /* Success / warning / error messages */
    .stSuccess, .stWarning, .stError, .stInfo {
        color: #1a1a2e !important;
    }
    .stSuccess p, .stWarning p, .stError p, .stInfo p {
        color: #1a1a2e !important;
    }

    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #1a3a5c 0%, #2C5F8A 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(44, 95, 138, 0.2);
    }

    .main-header h1 {
        color: white !important;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .main-header p {
        color: rgba(255,255,255,0.85);
        font-size: 1rem;
        margin: 0.5rem 0 0 0;
    }

    /* Cartes de resultats */
    .result-card {
        background: white;
        border-radius: 16px;
        padding: 1.8rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border-left: 5px solid #2C5F8A;
        color: #1a1a2e !important;
    }
    .result-card small {
        color: #555 !important;
    }

    .result-card-risk-low {
        border-left-color: #27AE60;
    }

    .result-card-risk-moderate {
        border-left-color: #F39C12;
    }

    .result-card-risk-high {
        border-left-color: #E74C3C;
    }

    /* Probabilite affichee */
    .probability-display {
        font-size: 3.5rem;
        font-weight: 800;
        text-align: center;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
    }

    .prob-low { color: #27AE60; background: #eafaf1; }
    .prob-moderate { color: #F39C12; background: #fef9e7; }
    .prob-high { color: #E74C3C; background: #fdedec; }

    /* Section info */
    .info-box {
        background: #EBF5FB;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border-left: 4px solid #2C5F8A;
        color: #1a3a5c !important;
    }
    .info-box * { color: #1a3a5c !important; }

    /* Methodologie card */
    .method-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        margin-bottom: 1rem;
        color: #1a1a2e !important;
    }
    .method-card * { color: #1a1a2e !important; }
    .method-card h4 { color: #1a3a5c !important; }

    .method-badge-stat {
        background: #2C5F8A;
        color: white;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .method-badge-ml {
        background: #27AE60;
        color: white;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }

    /* Sidebar */
    .css-1d391kg {
        background: white;
    }

    /* Bouton */
    .stButton > button {
        background: linear-gradient(135deg, #2C5F8A 0%, #1a3a5c 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.7rem 2rem;
        font-size: 1.05rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s;
        box-shadow: 0 4px 12px rgba(44,95,138,0.3);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(44,95,138,0.4);
    }

    /* Separateur */
    hr { margin: 1.5rem 0; border-color: #e0e0e0; }

    /* Footer */
    .footer {
        text-align: center;
        color: #888 !important;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding: 1rem;
        border-top: 1px solid #e0e0e0;
    }

    /* Override global Streamlit text color - force dark on light bg */
    .stApp p, .stApp span, .stApp div,
    .stApp li, .stApp ul, .stApp ol,
    .stApp small, .stApp strong, .stApp em,
    .main p, .main span, .main div,
    .block-container p, .block-container span,
    .block-container div, .block-container li {
        color: #1a1a2e;
    }

    /* Titres Streamlit natifs */
    .stApp h1, .stApp h2, .stApp h3,
    .stApp h4, .stApp h5, .stApp h6,
    .block-container h1, .block-container h2,
    .block-container h3, .block-container h4 {
        color: #1a3a5c !important;
    }

    /* Forcer texte sombre sur fond blanc - surcharge finale */
    [data-testid="stVerticalBlock"] p,
    [data-testid="stVerticalBlock"] span,
    [data-testid="stVerticalBlock"] li,
    [data-testid="stHorizontalBlock"] p,
    [data-testid="stHorizontalBlock"] span {
        color: #1a1a2e !important;
    }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# CHARGEMENT DES MODELES
# --------------------------------------------------------------------------

# Chemin de base : dossier contenant app.py (fonctionne en local ET sur Streamlit Cloud)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_resource
def load_models():
    """Charger les deux modeles sauvegardes."""
    models = {}

    stat_path = os.path.join(BASE_DIR, 'stat_model_artifacts.pkl')
    if os.path.exists(stat_path):
        with open(stat_path, 'rb') as f:
            models['stat'] = pickle.load(f)
    else:
        models['stat'] = None

    ml_path = os.path.join(BASE_DIR, 'ml_model_artifacts.pkl')
    if os.path.exists(ml_path):
        with open(ml_path, 'rb') as f:
            models['ml'] = pickle.load(f)
    else:
        models['ml'] = None

    return models


models = load_models()


# --------------------------------------------------------------------------
# FONCTIONS DE PREDICTION
# --------------------------------------------------------------------------

def predict_statistical(user_input):
    """
    Prediction via le modele de regression logistique ponderee.
    Reconstruit le vecteur de features dummy a partir des entrees utilisateur.
    """
    if models['stat'] is None:
        return None, None

    result = models['stat']['result']
    predictors = models['stat']['predictors']

    # Construire un vecteur de features identique a celui du modele
    feature_vector = {p: 0.0 for p in predictors}

    # --- Variables continues ---
    feature_vector['age'] = float(user_input['age'])
    feature_vector['naissances_5ans'] = float(user_input.get('naissances_5ans', 0))
    feature_vector['score_pb_acces_sante'] = float(user_input.get('score_pb_acces_sante', 0))
    feature_vector['taille_menage'] = float(user_input.get('taille_menage', 5))

    # --- Variables binaires ---
    feature_vector['grossesse_interrompue'] = float(user_input.get('grossesse_interrompue', 0))
    feature_vector['visite_agent_sante'] = float(user_input.get('visite_agent_sante', 0))
    feature_vector['consultation_etablissement'] = float(user_input.get('consultation_etablissement', 0))
    feature_vector['electricite'] = float(user_input.get('electricite', 0))

    # --- Education (reference = Superieur) ---
    edu = user_input.get('education', 'Superieur')
    for cat in ['Aucun', 'Primaire', 'Secondaire']:
        key = f'education_cat_{cat}'
        if key in feature_vector:
            feature_vector[key] = 1.0 if edu == cat else 0.0

    # --- Milieu (reference = Urbain) ---
    milieu = user_input.get('milieu', 'Urbain')
    key = 'milieu_cat_Rural'
    if key in feature_vector:
        feature_vector[key] = 1.0 if milieu == 'Rural' else 0.0

    # --- Region (reference = Littoral) ---
    region = user_input.get('region', 'Littoral')
    regions = ['Adamawa', 'Centre', 'Est', 'Extreme-Nord', 'Nord', 'Nord-Ouest',
               'Ouest', 'Sud', 'Sud-Ouest', 'Autre']
    for r in regions:
        key = f'region_cat_{r}'
        if key in feature_vector:
            feature_vector[key] = 1.0 if region == r else 0.0

    # --- Religion (reference = Catholique) ---
    religion = user_input.get('religion', 'Catholique')
    religions = ['Protestant', 'Muslman', 'Autre_Chretien', 'Animiste', 'Autre']
    for rel in religions:
        key = f'religion_cat_{rel}'
        if key in feature_vector:
            feature_vector[key] = 1.0 if religion == rel else 0.0
    # Correction orthographe Musulman
    key_musulman = 'religion_cat_Musulman'
    if key_musulman in feature_vector:
        feature_vector[key_musulman] = 1.0 if religion == 'Musulman' else 0.0

    # --- Statut matrimonial (reference = En_union) ---
    union = user_input.get('statut_matrimonial', 'En_union')
    for u_cat in ['Jamais_union', 'Ex_union']:
        key = f'union_cat_{u_cat}'
        if key in feature_vector:
            feature_vector[key] = 1.0 if union == u_cat else 0.0

    # --- Richesse (reference = Tres_riche) ---
    richesse = user_input.get('richesse', 'Tres_riche')
    for r_cat in ['Tres_pauvre', 'Pauvre', 'Moyen', 'Riche']:
        key = f'richesse_cat_{r_cat}'
        if key in feature_vector:
            feature_vector[key] = 1.0 if richesse == r_cat else 0.0

    # --- Emploi (reference = Oui) ---
    emploi = user_input.get('emploi', 'Oui')
    key = 'emploi_cat_Non'
    if key in feature_vector:
        feature_vector[key] = 1.0 if emploi == 'Non' else 0.0

    # --- Assurance (reference = Oui) ---
    assurance = user_input.get('assurance', 'Oui')
    key = 'assurance_cat_Non'
    if key in feature_vector:
        feature_vector[key] = 1.0 if assurance == 'Non' else 0.0

    # --- Age premiere naissance (reference = 25_et_plus) ---
    age_prb = user_input.get('age_prb_cat', '25_et_plus')
    for a_cat in ['Moins_18ans', '18_19ans', '20_24ans']:
        key = f'age_prb_cat_{a_cat}'
        if key in feature_vector:
            feature_vector[key] = 1.0 if age_prb == a_cat else 0.0

    # Construire le vecteur final dans l'ordre des predicteurs
    x_vals = np.array([[feature_vector.get(p, 0.0) for p in predictors]], dtype=float)
    x_with_const = np.column_stack([np.ones(1), x_vals])

    try:
        prob = float(result.predict(x_with_const)[0])
        prob = max(0.0, min(1.0, prob))
        return prob, feature_vector
    except Exception as e:
        return None, str(e)


def predict_ml(user_input):
    """
    Prediction via le meilleur modele ML (XGBoost pipeline).
    """
    if models['ml'] is None:
        return None

    pipeline = models['ml']['best_pipeline']
    threshold = models['ml']['optimal_threshold']

    # Construire le DataFrame utilisateur
    row = {
        'age': float(user_input.get('age', 25)),
        'age_premiere_naissance': float(user_input.get('age_premiere_naissance', 22)),
        'naissances_5ans': float(user_input.get('naissances_5ans', 0)),
        'taille_menage': float(user_input.get('taille_menage', 5)),
        'score_pb_acces_sante': float(user_input.get('score_pb_acces_sante', 1)),
        'nb_enfants_nes_vivants': float(user_input.get('nb_enfants', 0)),
        'niveau_education': {
            'Aucun': 0, 'Primaire': 1, 'Secondaire': 2, 'Superieur': 3
        }.get(user_input.get('education', 'Secondaire'), 2),
        'quintile_richesse': {
            'Tres_pauvre': 1, 'Pauvre': 2, 'Moyen': 3, 'Riche': 4, 'Tres_riche': 5
        }.get(user_input.get('richesse', 'Moyen'), 3),
        'statut_matrimonial': {
            'Jamais_union': 0, 'En_union': 1, 'Ex_union': 3
        }.get(user_input.get('statut_matrimonial', 'En_union'), 1),
        'milieu_residence': {'Urbain': 1, 'Rural': 2}.get(user_input.get('milieu', 'Urbain'), 1),
        'travaille_actuellement': {'Oui': 1, 'Non': 0}.get(user_input.get('emploi', 'Oui'), 1),
        'assurance_maladie': {'Oui': 1, 'Non': 0}.get(user_input.get('assurance', 'Non'), 0),
        'grossesse_interrompue': int(user_input.get('grossesse_interrompue', 0)),
        'visite_agent_sante': int(user_input.get('visite_agent_sante', 0)),
        'consultation_etablissement': int(user_input.get('consultation_etablissement', 0)),
        'electricite': int(user_input.get('electricite', 0)),
        'pb_argent_sante': int(user_input.get('pb_argent_sante', 0)),
        'pb_distance_sante': int(user_input.get('pb_distance_sante', 0)),
        'pb_permission_sante': int(user_input.get('pb_permission_sante', 0)),
        'pb_aller_seule': int(user_input.get('pb_aller_seule', 0)),
        'region': {
            'Adamawa': 1, 'Centre': 2, 'Est': 3, 'Extreme-Nord': 4,
            'Littoral': 5, 'Nord': 6, 'Nord-Ouest': 7, 'Ouest': 8, 'Sud': 9, 'Sud-Ouest': 10
        }.get(user_input.get('region', 'Centre'), 2),
        'religion': {
            'Catholique': 1, 'Protestant': 2, 'Autre_Chretien': 3,
            'Musulman': 4, 'Animiste': 5, 'Autre': 6
        }.get(user_input.get('religion', 'Catholique'), 1),
    }

    X_user = pd.DataFrame([row])

    # Aligner les colonnes avec ce que le modele attend
    feature_names = models['ml']['feature_names']
    for col in feature_names:
        if col not in X_user.columns:
            X_user[col] = 0
    X_user = X_user[feature_names]

    try:
        prob = float(pipeline.predict_proba(X_user)[0, 1])
        prob = max(0.0, min(1.0, prob))
        return prob
    except Exception as e:
        return None


# --------------------------------------------------------------------------
# FONCTIONS D'AFFICHAGE DES RESULTATS
# --------------------------------------------------------------------------

def get_risk_level(prob):
    if prob < 0.15:
        return 'faible', '#27AE60', 'prob-low', 'result-card-risk-low'
    elif prob < 0.35:
        return 'modere', '#F39C12', 'prob-moderate', 'result-card-risk-moderate'
    else:
        return 'eleve', '#E74C3C', 'prob-high', 'result-card-risk-high'


def get_risk_comment(prob, method='stat'):
    level, _, _, _ = get_risk_level(prob)
    pct = prob * 100

    if level == 'faible':
        main = (
            f"Le risque estime est faible ({pct:.1f}%). "
            "Votre profil presente plusieurs facteurs protecteurs. "
            "Un suivi medical regulier reste recommande."
        )
        conseils = [
            "Continuez a consulter regulierement un professionnel de sante.",
            "Maintenez les consultations prenatales en cas de grossesse.",
            "Assurez-vous que vos enfants beneficient de tous les vaccins."
        ]
    elif level == 'modere':
        main = (
            f"Le risque estime est modere ({pct:.1f}%). "
            "Certains facteurs de vulnerabilite ont ete identifies. "
            "Un suivi renforce est recommande."
        )
        conseils = [
            "Consultez regulierement un agent de sante ou une sage-femme.",
            "Si possible, accouchez dans un etablissement de sante.",
            "Informez-vous sur la planification familiale et l espacement des naissances.",
            "Signalez tout probleme de sante de votre enfant des les premiers signes."
        ]
    else:
        main = (
            f"Le risque estime est eleve ({pct:.1f}%). "
            "Votre profil presente plusieurs facteurs de risque combines. "
            "Un accompagnement medical etroit est fortement recommande."
        )
        conseils = [
            "Consultez un professionnel de sante dans les meilleurs delais.",
            "Assurez-vous de suivre toutes les consultations prenatales recommandees.",
            "Privilegiez l accouchement en milieu medical.",
            "Discutez avec votre medecin des mesures preventives disponibles.",
            "Renseignez-vous sur les programmes de sante communautaire dans votre region."
        ]

    return main, conseils


def display_gauge(prob, title, color):
    """Afficher une jauge visuelle de probabilite."""
    fig, ax = plt.subplots(figsize=(5, 2.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Barre de fond
    ax.barh(0.5, 1, 0.4, left=0, color='#f0f0f0', align='center')

    # Barre de probabilite
    ax.barh(0.5, prob, 0.4, left=0, color=color, align='center', alpha=0.9)

    # Zones
    ax.axvline(x=0.15, color='#27AE60', lw=2, linestyle='--', alpha=0.5)
    ax.axvline(x=0.35, color='#E74C3C', lw=2, linestyle='--', alpha=0.5)

    # Labels
    ax.text(0.075, 0.05, 'Faible', ha='center', fontsize=7, color='#27AE60')
    ax.text(0.25, 0.05, 'Modere', ha='center', fontsize=7, color='#F39C12')
    ax.text(0.65, 0.05, 'Eleve', ha='center', fontsize=7, color='#E74C3C')

    ax.text(prob, 0.92, f'{prob*100:.1f}%', ha='center', fontsize=14,
            fontweight='bold', color=color)
    ax.set_title(title, fontsize=10, fontweight='bold', pad=5)
    fig.patch.set_alpha(0)
    ax.set_facecolor('none')
    plt.tight_layout()
    return fig


# --------------------------------------------------------------------------
# INTERFACE PRINCIPALE
# --------------------------------------------------------------------------

# Header
st.markdown("""
<div class="main-header">
    <h1>Estimation du Risque de Mortalite Infantile</h1>
    <p>Outil base sur les donnees de l Enquete Demographique et de Sante (EDS) du Cameroun 2018
    | Femmes agees de 15 a 49 ans</p>
</div>
""", unsafe_allow_html=True)

# Description et avertissement
with st.expander("A propos de cet outil", expanded=False):
    st.markdown("""
    **Cet outil estime la probabilite statistique qu une femme ayant le profil
    saisi ait perdu au moins un enfant, selon deux methodes complementaires.**

    Les resultats sont issus d analyses statistiques et de machine learning realises sur un echantillon
    representatif de **14 677 femmes camerounaises** (EDS 2018). Ils refletent des probabilites
    populationnelles et non une certitude individuelle.

    **Ce n est pas un outil de diagnostic medical.** Les resultats doivent etre interpretes
    avec l aide d un professionnel de sante.

    Sources des donnees : Programme DHS (Demographic and Health Surveys), Cameroun 2018.
    """)


# --------------------------------------------------------------------------
# SIDEBAR : FORMULAIRE DE SAISIE
# --------------------------------------------------------------------------

st.sidebar.markdown("## Votre profil")
st.sidebar.markdown("---")

# AGE
age = st.sidebar.slider(
    "Age (annees)", min_value=15, max_value=49, value=28,
    help="Votre age actuel en annees completes"
)

# EDUCATION
education = st.sidebar.selectbox(
    "Niveau d education",
    options=['Superieur', 'Secondaire', 'Primaire', 'Aucun'],
    index=1,
    help="Le plus haut niveau d education atteint"
)

# REGION
region = st.sidebar.selectbox(
    "Region de residence",
    options=['Adamawa', 'Centre', 'Est', 'Extreme-Nord', 'Littoral',
             'Nord', 'Nord-Ouest', 'Ouest', 'Sud', 'Sud-Ouest'],
    index=1
)

# MILIEU
milieu = st.sidebar.radio(
    "Milieu de residence",
    options=['Urbain', 'Rural'],
    index=0
)

# RICHESSE
richesse = st.sidebar.selectbox(
    "Niveau de richesse du menage",
    options=['Tres_riche', 'Riche', 'Moyen', 'Pauvre', 'Tres_pauvre'],
    format_func=lambda x: x.replace('_', ' '),
    index=2
)

# STATUT MATRIMONIAL
statut = st.sidebar.selectbox(
    "Situation matrimoniale",
    options=['En_union', 'Jamais_union', 'Ex_union'],
    format_func=lambda x: {
        'En_union': 'En union (mariee ou cohabitant)',
        'Jamais_union': 'Jamais en union (celibataire)',
        'Ex_union': 'Ancienne union (divorcee / veuve)'
    }[x],
    index=0
)

# RELIGION
religion = st.sidebar.selectbox(
    "Religion",
    options=['Catholique', 'Protestant', 'Muslman', 'Autre_Chretien', 'Animiste', 'Autre'],
    format_func=lambda x: x.replace('_', ' ').replace('Muslman', 'Musulman'),
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Historique reproductif**")

# NB ENFANTS
nb_enfants = st.sidebar.number_input(
    "Nombre d enfants nes vivants",
    min_value=0, max_value=20, value=2,
    help="Nombre total d enfants que vous avez mis au monde vivants"
)

# AGE PREMIERE NAISSANCE
if nb_enfants > 0:
    age_premiere_naissance = st.sidebar.slider(
        "Age a la premiere naissance",
        min_value=10, max_value=49, value=20,
        help="Votre age quand vous avez eu votre premier enfant"
    )
    if age_premiere_naissance < 18:
        age_prb_cat = 'Moins_18ans'
    elif age_premiere_naissance < 20:
        age_prb_cat = '18_19ans'
    elif age_premiere_naissance < 25:
        age_prb_cat = '20_24ans'
    else:
        age_prb_cat = '25_et_plus'
else:
    age_premiere_naissance = 22
    age_prb_cat = '25_et_plus'

# NAISSANCES 5 ANS
naissances_5ans = st.sidebar.slider(
    "Naissances dans les 5 dernieres annees",
    min_value=0, max_value=5, value=0
)

# GROSSESSE INTERROMPUE
grossesse_interrompue = st.sidebar.checkbox(
    "Grossesse interrompue (fausse couche / avortement)",
    value=False
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Acces aux soins**")

# EMPLOI
emploi = st.sidebar.radio("Actuellement en emploi", ['Oui', 'Non'], index=0)

# ASSURANCE
assurance = st.sidebar.radio("Couverture par assurance maladie", ['Non', 'Oui'], index=0)

# CONSULTATION
consultation_etablissement = st.sidebar.checkbox(
    "Consultee un etablissement de sante (12 derniers mois)", value=False
)
visite_agent_sante = st.sidebar.checkbox(
    "Visitee par un agent de sante (12 derniers mois)", value=False
)
electricite = st.sidebar.checkbox("Menage avec electricite", value=False)

# TAILLE MENAGE
taille_menage = st.sidebar.slider("Taille du menage (personnes)", 1, 20, 5)

# PROBLEMES ACCES SANTE
st.sidebar.markdown("**Obstacles a l acces aux soins**")
st.sidebar.markdown("*Cocher si c est un gros probleme pour vous :*")
pb_permission = st.sidebar.checkbox("Obtenir la permission de se soigner", False)
pb_argent = st.sidebar.checkbox("Trouver l argent necessaire", False)
pb_distance = st.sidebar.checkbox("Distance jusqu a l etablissement de sante", False)
pb_seule = st.sidebar.checkbox("Ne pas vouloir y aller seule", False)

score_pb_acces = sum([pb_permission, pb_argent, pb_distance, pb_seule])

# --------------------------------------------------------------------------
# BOUTON ET CALCUL
# --------------------------------------------------------------------------

st.markdown("---")
col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
with col_btn2:
    calculer = st.button("Estimer mon risque")

if calculer:
    # Construire l'entree utilisateur
    user_input = {
        'age': age,
        'education': education,
        'milieu': milieu,
        'region': region,
        'richesse': richesse,
        'statut_matrimonial': statut,
        'religion': religion.replace('Muslman', 'Musulman'),
        'emploi': emploi,
        'assurance': assurance,
        'nb_enfants': nb_enfants,
        'age_premiere_naissance': age_premiere_naissance,
        'age_prb_cat': age_prb_cat,
        'naissances_5ans': naissances_5ans,
        'grossesse_interrompue': int(grossesse_interrompue),
        'consultation_etablissement': int(consultation_etablissement),
        'visite_agent_sante': int(visite_agent_sante),
        'electricite': int(electricite),
        'taille_menage': taille_menage,
        'score_pb_acces_sante': score_pb_acces,
        'pb_permission_sante': int(pb_permission),
        'pb_argent_sante': int(pb_argent),
        'pb_distance_sante': int(pb_distance),
        'pb_aller_seule': int(pb_seule),
    }

    # Predictions
    prob_stat, feat_stat = predict_statistical(user_input)
    prob_ml = predict_ml(user_input)

    # ----------- AFFICHAGE DES RESULTATS -----------
    st.markdown("## Resultats de l estimation")
    st.markdown("""
    <div class="info-box">
    Les deux methodes ci-dessous utilisent des approches differentes mais des donnees identiques.
    Un accord entre les deux methodes renforce la fiabilite de l estimation.
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    # --- METHODE STATISTIQUE ---
    with col1:
        st.markdown('<span class="method-badge-stat">Methode Statistique</span>', unsafe_allow_html=True)
        st.markdown("#### Regression Logistique Ponderee")

        if prob_stat is not None:
            level, color, prob_class, card_class = get_risk_level(prob_stat)
            fig_gauge = display_gauge(prob_stat, "Probabilite estimee", color)
            st.pyplot(fig_gauge, use_container_width=True)
            plt.close()

            risk_labels = {'faible': 'RISQUE FAIBLE', 'modere': 'RISQUE MODERE', 'eleve': 'RISQUE ELEVE'}
            st.markdown(f"""
            <div class="result-card {card_class}">
                <h3 style="color:{color}; margin:0;">{risk_labels[level]}</h3>
                <h2 style="color:{color}; font-size:2.5rem; margin:0.3rem 0;">{prob_stat*100:.1f}%</h2>
                <small>Probabilite estimee d avoir perdu au moins un enfant</small>
            </div>
            """, unsafe_allow_html=True)

            main_comment, conseils = get_risk_comment(prob_stat, 'stat')
            st.markdown(f"**Interpretation :** {main_comment}")

            st.markdown("**Indicateurs du modele :**")
            stat_info = models['stat']
            if stat_info:
                c1, c2 = st.columns(2)
                c1.metric("AUC", f"{stat_info.get('auc', 0):.3f}")
                c2.metric("R2 Nagelkerke", f"{stat_info.get('nagelkerke', 0):.3f}")
        else:
            st.error("Modele statistique non disponible.")

    # --- METHODE ML ---
    with col2:
        st.markdown('<span class="method-badge-ml">Methode Machine Learning</span>', unsafe_allow_html=True)
        best_name = models['ml'].get('best_model_name', 'XGBoost') if models['ml'] else 'XGBoost'
        st.markdown(f"#### {best_name}")

        if prob_ml is not None:
            level_ml, color_ml, prob_class_ml, card_class_ml = get_risk_level(prob_ml)
            fig_gauge_ml = display_gauge(prob_ml, "Probabilite estimee", color_ml)
            st.pyplot(fig_gauge_ml, use_container_width=True)
            plt.close()

            risk_labels = {'faible': 'RISQUE FAIBLE', 'modere': 'RISQUE MODERE', 'eleve': 'RISQUE ELEVE'}
            st.markdown(f"""
            <div class="result-card {card_class_ml}">
                <h3 style="color:{color_ml}; margin:0;">{risk_labels[level_ml]}</h3>
                <h2 style="color:{color_ml}; font-size:2.5rem; margin:0.3rem 0;">{prob_ml*100:.1f}%</h2>
                <small>Probabilite estimee d avoir perdu au moins un enfant</small>
            </div>
            """, unsafe_allow_html=True)

            main_comment_ml, conseils_ml = get_risk_comment(prob_ml, 'ml')
            st.markdown(f"**Interpretation :** {main_comment_ml}")

            st.markdown("**Indicateurs du modele :**")
            if models['ml']:
                c1, c2 = st.columns(2)
                test_results = models['ml'].get('test_results', {})
                best = test_results.get(best_name, {})
                c1.metric("AUC", f"{best.get('AUC', 0):.3f}")
                c2.metric("F1-Score", f"{best.get('F1', 0):.3f}")
        else:
            st.error("Modele ML non disponible.")

    # --- CONSEILS ---
    st.markdown("---")
    st.markdown("### Recommandations")

    if prob_stat is not None:
        _, conseils = get_risk_comment(max(prob_stat, prob_ml if prob_ml else 0))
        cols = st.columns(min(3, len(conseils)))
        for i, conseil in enumerate(conseils):
            with cols[i % len(cols)]:
                st.markdown(f"""
                <div class="method-card">
                    <p style="margin:0; font-size:0.9rem;">{conseil}</p>
                </div>
                """, unsafe_allow_html=True)

    # --- ACCORD ENTRE METHODES ---
    if prob_stat is not None and prob_ml is not None:
        diff = abs(prob_stat - prob_ml)
        st.markdown("---")
        st.markdown("### Concordance entre les deux methodes")
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Probabilite Statistique", f"{prob_stat*100:.1f}%")
        col_b.metric("Probabilite ML", f"{prob_ml*100:.1f}%")
        col_c.metric("Ecart entre methodes", f"{diff*100:.1f} pts")

        if diff < 0.10:
            st.success("Les deux methodes sont en bon accord (ecart < 10 points). L estimation est fiable.")
        elif diff < 0.20:
            st.warning("Les deux methodes divergent moderement (ecart entre 10 et 20 points). A interpreter avec precaution.")
        else:
            st.error("Les deux methodes divergent significativement (ecart > 20 points). Consultez un professionnel.")

    # Disclaimer
    st.markdown("""
    <div style="background:#fff3cd; border-radius:8px; padding:1rem; border-left:4px solid #ffc107; margin-top:1rem; color:#6d4c00 !important;">
    <strong style="color:#6d4c00;">Avertissement :</strong>
    <span style="color:#6d4c00;"> Cet outil a une vocation exclusivement informative et educative.
    Les probabilites affichees sont des estimations populationnelles issues de modeles statistiques.
    Elles ne constituent pas un diagnostic medical individuel et ne doivent pas se substituer
    a une consultation medicale professionnelle.</span>
    </div>
    """, unsafe_allow_html=True)

else:
    # Ecran d'accueil
    st.markdown("""
    <div style="text-align:center; padding:3rem;">
        <h2 style="color:#2C5F8A;">Comment utiliser cet outil ?</h2>
        <p style="font-size:1.1rem; color:#555; max-width:700px; margin:auto;">
        Remplissez le formulaire dans la barre laterale gauche avec votre profil
        (age, niveau d education, region, situation economique, acces aux soins, etc.),
        puis cliquez sur "Estimer mon risque" pour obtenir une estimation personnalisee.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Methodologie
    st.markdown("### Les deux methodes utilisees")
    col_m1, col_m2 = st.columns(2, gap="large")

    with col_m1:
        st.markdown("""
        <div class="method-card">
            <span class="method-badge-stat">Statistique</span>
            <h4 style="margin-top:0.8rem;">Regression Logistique Ponderee</h4>
            <p>Modele econometrique classique tenant compte du plan de sondage complexe
            de l EDS (ponderation, grappes, stratification). Fournit des Odds Ratios
            interpretables et des tests de significativite rigoureuses.</p>
            <ul>
                <li>10 494 femmes pares analysees</li>
                <li>AUC = 0.75</li>
                <li>Pseudo R2 Nagelkerke = 0.23</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col_m2:
        st.markdown("""
        <div class="method-card">
            <span class="method-badge-ml">Machine Learning</span>
            <h4 style="margin-top:0.8rem;">XGBoost (meilleur modele)</h4>
            <p>Algorithme de gradient boosting optimise pour les donnees tabulaires.
            Evalue par validation croisee 5-fold et teste sur un echantillon
            vierge de 25% des donnees.</p>
            <ul>
                <li>14 677 femmes analysees</li>
                <li>AUC = 0.889</li>
                <li>F1-Score = 0.64</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    # Facteurs cles
    st.markdown("### Principaux facteurs identifies")

    facteurs = {
        "Age a la premiere naissance < 18 ans": ("Facteur de risque majeur", "E74C3C"),
        "Absence d education formelle": ("Facteur de risque eleve", "E74C3C"),
        "Pauvrete severe": ("Facteur de risque modere", "E74C3C"),
        "Consultation d un etablissement de sante": ("Facteur protecteur", "27AE60"),
        "Visite par un agent de sante": ("Facteur protecteur", "27AE60"),
    }

    cols_f = st.columns(len(facteurs))
    for i, (facteur, (desc, clr)) in enumerate(facteurs.items()):
        with cols_f[i]:
            st.markdown(f"""
            <div style="background:white; border-radius:10px; padding:1rem;
                        box-shadow:0 2px 10px rgba(0,0,0,0.07);
                        border-top:4px solid #{clr}; height:120px;">
                <p style="font-size:0.8rem; font-weight:600; color:#{clr}; margin:0;">{desc}</p>
                <p style="font-size:0.85rem; margin:0.4rem 0 0 0; color:#1a1a2e;">{facteur}</p>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer" style="color:#666 !important;">
    Outil developpe a partir des donnees EDS Cameroun 2018 (Programme DHS / ICF International).
    Modeles de regression logistique ponderee et XGBoost. A des fins de recherche et d information uniquement.
</div>
""", unsafe_allow_html=True)
