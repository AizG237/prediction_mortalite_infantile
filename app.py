"""
app.py
Application Streamlit - Évaluation du Risque de Mortalité Infantile
EDS Cameroun 2018 | Double méthode : Statistique + Machine Learning
"""
import streamlit as st
import pandas as pd
import numpy as np
import pickle
import warnings
import os

warnings.filterwarnings('ignore')

# --------------------------------------------------------------------------
# CONFIGURATION PAGE
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="Risque de Mortalité Infantile · Cameroun",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------
# CSS PERSONNALISÉ — design moderne, épuré, animé
# --------------------------------------------------------------------------

st.markdown("""
<style>
    /* ---------- Police moderne ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    :root {
        --ink:       #1e2a3a;
        --muted:     #64748b;
        --primary:   #2563eb;
        --primary-d: #1e3a8a;
        --surface:   #ffffff;
        --bg-1:      #f6f9ff;
        --bg-2:      #eaf1fb;
        --green:     #10b981;
        --amber:     #f59e0b;
        --red:       #ef4444;
        --ring:      rgba(37, 99, 235, 0.12);
        --shadow:    0 10px 40px rgba(30, 58, 138, 0.07);
        --shadow-h:  0 18px 50px rgba(30, 58, 138, 0.14);
        --radius:    20px;
    }

    /* Appliquer la police partout */
    html, body, [class*="css"], .stApp, .stMarkdown, button, input, select, textarea,
    [data-testid="stMarkdownContainer"], [data-testid="stMetricValue"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* ---------- Fond animé doux ---------- */
    .stApp {
        background:
            radial-gradient(1100px 600px at 8% -5%, rgba(124, 58, 237, 0.06), transparent 60%),
            radial-gradient(900px 600px at 100% 0%, rgba(37, 99, 235, 0.08), transparent 55%),
            linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%);
        background-attachment: fixed;
    }

    .block-container { padding-top: 2.2rem; max-width: 1180px; }

    /* ---------- Couleurs de texte (toujours sombre sur clair) ---------- */
    .stApp, .stMarkdown, [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    .element-container p, .element-container li {
        color: var(--ink);
    }
    h1, h2, h3, h4, h5, h6,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4 {
        color: var(--primary-d) !important;
        letter-spacing: -0.4px;
        font-weight: 700;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {
        color: var(--ink) !important;
    }
    label, .stCheckbox label, .stRadio label, .stSelectbox label,
    .stSlider label, .stNumberInput label {
        color: var(--ink) !important;
        font-weight: 600;
    }

    /* ---------- Animations clés ---------- */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(16px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes popIn {
        0%   { opacity: 0; transform: scale(0.9); }
        60%  { transform: scale(1.03); }
        100% { opacity: 1; transform: scale(1); }
    }
    @keyframes gaugeSlide {
        from { left: 0; }
        to   { left: var(--target); }
    }
    @keyframes softPulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(0,0,0,0.0); transform: scale(1); }
        50%      { transform: scale(1.18); }
    }
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-6px); }
    }

    .fade-up { animation: fadeUp 0.7s cubic-bezier(.21,.61,.35,1) both; }

    /* ---------- Header héro ---------- */
    .main-header {
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 55%, #3b82f6 100%);
        padding: 2.4rem 2.6rem;
        border-radius: 26px;
        margin-bottom: 1.8rem;
        box-shadow: 0 20px 50px rgba(37, 99, 235, 0.28);
        animation: fadeUp 0.7s cubic-bezier(.21,.61,.35,1) both;
    }
    .main-header::after {
        content: "";
        position: absolute;
        top: -40%; right: -10%;
        width: 380px; height: 380px;
        background: radial-gradient(circle, rgba(255,255,255,0.18), transparent 70%);
        border-radius: 50%;
        animation: float 6s ease-in-out infinite;
    }
    .main-header h1 {
        color: #ffffff !important;
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.8px;
        position: relative; z-index: 1;
    }
    .main-header p {
        color: rgba(255,255,255,0.9) !important;
        font-size: 1.02rem;
        margin: 0.7rem 0 0 0;
        max-width: 760px;
        position: relative; z-index: 1;
    }
    .header-pill {
        display: inline-block;
        background: rgba(255,255,255,0.16);
        border: 1px solid rgba(255,255,255,0.25);
        color: #fff !important;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 0.32rem 0.9rem;
        border-radius: 999px;
        margin-bottom: 1rem;
        backdrop-filter: blur(6px);
        position: relative; z-index: 1;
    }

    /* ---------- Cartes ---------- */
    .result-card {
        background: var(--surface);
        border-radius: var(--radius);
        padding: 1.8rem;
        box-shadow: var(--shadow);
        margin-bottom: 1.2rem;
        border: 1px solid rgba(30, 58, 138, 0.06);
        border-left: 5px solid var(--primary);
        animation: popIn 0.6s cubic-bezier(.21,.61,.35,1) both;
        transition: transform .25s ease, box-shadow .25s ease;
    }
    .result-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-h); }
    .result-card small { color: var(--muted) !important; }
    .result-card-risk-low      { border-left-color: var(--green); }
    .result-card-risk-moderate { border-left-color: var(--amber); }
    .result-card-risk-high     { border-left-color: var(--red); }

    .risk-badge {
        display: inline-flex; align-items: center; gap: 0.5rem;
        font-size: 0.82rem; font-weight: 700; letter-spacing: 0.3px;
        padding: 0.34rem 0.85rem; border-radius: 999px;
    }
    .risk-badge .dot {
        width: 9px; height: 9px; border-radius: 50%;
        animation: softPulse 1.8s ease-in-out infinite;
    }
    .badge-low      { background: #e7f8f1; color: #0d8a63; }
    .badge-low .dot { background: var(--green); box-shadow: 0 0 0 4px rgba(16,185,129,.18); }
    .badge-moderate      { background: #fef6e7; color: #b9760a; }
    .badge-moderate .dot { background: var(--amber); box-shadow: 0 0 0 4px rgba(245,158,11,.18); }
    .badge-high      { background: #fdecec; color: #c0392b; }
    .badge-high .dot { background: var(--red); box-shadow: 0 0 0 4px rgba(239,68,68,.18); }

    .prob-number {
        font-size: 3.1rem; font-weight: 800; line-height: 1;
        margin: 0.7rem 0 0.2rem 0;
        animation: popIn 0.7s cubic-bezier(.21,.61,.35,1) both;
    }

    /* ---------- Jauge animée HTML ---------- */
    .gauge { position: relative; margin: 1.6rem 0 1.2rem 0; padding-top: 2rem; }
    .gauge-track {
        height: 14px; border-radius: 999px;
        background: linear-gradient(90deg,
            var(--green) 0%, var(--green) 15%,
            var(--amber) 15%, var(--amber) 35%,
            var(--red) 35%, var(--red) 100%);
        opacity: 0.28;
    }
    .gauge-needle {
        position: absolute; top: 1.7rem;
        width: 4px; height: 22px; border-radius: 4px;
        background: var(--ink);
        transform: translateX(-50%);
        animation: gaugeSlide 1.1s cubic-bezier(.34,1.2,.4,1) both;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
    }
    .gauge-bubble {
        position: absolute; top: 0;
        transform: translateX(-50%);
        font-weight: 800; font-size: 1.05rem;
        padding: 0.15rem 0.6rem; border-radius: 999px;
        background: #fff; box-shadow: var(--shadow);
        animation: gaugeSlide 1.1s cubic-bezier(.34,1.2,.4,1) both;
        white-space: nowrap;
    }
    .gauge-scale {
        display: flex; justify-content: space-between;
        margin-top: 0.6rem; font-size: 0.72rem; font-weight: 600;
    }
    .gauge-scale .s-low { color: var(--green); }
    .gauge-scale .s-mod { color: var(--amber); }
    .gauge-scale .s-high { color: var(--red); }

    /* ---------- Encadré info ---------- */
    .info-box {
        background: linear-gradient(135deg, #eef4ff 0%, #e8f0fe 100%);
        border-radius: 14px;
        padding: 1rem 1.4rem;
        margin: 0.6rem 0 1.4rem 0;
        border-left: 4px solid var(--primary);
        color: var(--primary-d) !important;
        animation: fadeUp 0.6s ease both;
    }
    .info-box * { color: var(--primary-d) !important; }

    /* ---------- Cartes méthode / conseils / facteurs ---------- */
    .method-card {
        background: var(--surface);
        border-radius: 16px;
        padding: 1.4rem 1.6rem;
        box-shadow: var(--shadow);
        margin-bottom: 1rem;
        border: 1px solid rgba(30, 58, 138, 0.06);
        transition: transform .25s ease, box-shadow .25s ease;
        animation: fadeUp 0.6s ease both;
        height: 100%;
    }
    .method-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-h); }
    .method-card * { color: var(--ink); }
    .method-card h4 { color: var(--primary-d) !important; margin-top: 0.8rem; }
    .method-card ul { padding-left: 1.1rem; }
    .method-card li { margin: 0.25rem 0; }

    .method-badge-stat, .method-badge-ml {
        color: #fff !important;
        padding: 0.28rem 0.85rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    .method-badge-stat { background: linear-gradient(135deg, #2563eb, #1e3a8a); }
    .method-badge-ml   { background: linear-gradient(135deg, #10b981, #059669); }

    .conseil-card {
        background: var(--surface);
        border-radius: 14px;
        padding: 1.1rem 1.2rem;
        box-shadow: var(--shadow);
        border: 1px solid rgba(30,58,138,0.06);
        height: 100%;
        transition: transform .25s ease, box-shadow .25s ease;
        animation: fadeUp 0.6s ease both;
    }
    .conseil-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-h); }
    .conseil-card p { margin: 0; font-size: 0.92rem; color: var(--ink); }
    .conseil-num {
        display: inline-flex; align-items: center; justify-content: center;
        width: 26px; height: 26px; border-radius: 8px;
        background: var(--ring); color: var(--primary) !important;
        font-weight: 800; font-size: 0.85rem; margin-bottom: 0.5rem;
    }

    .factor-card {
        background: var(--surface);
        border-radius: 14px;
        padding: 1.1rem;
        box-shadow: var(--shadow);
        border-top: 4px solid var(--primary);
        height: 132px;
        transition: transform .25s ease, box-shadow .25s ease;
        animation: fadeUp 0.6s ease both;
    }
    .factor-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-h); }

    /* ---------- Sidebar ---------- */
    section[data-testid="stSidebar"] {
        background: rgba(255,255,255,0.92);
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(30,58,138,0.06);
    }
    section[data-testid="stSidebar"] * { color: var(--ink) !important; }
    section[data-testid="stSidebar"] h2 { color: var(--primary-d) !important; }
    .sidebar-title {
        font-size: 1.15rem; font-weight: 800; color: var(--primary-d) !important;
        margin-bottom: 0.2rem;
    }
    .sidebar-sub {
        font-size: 0.8rem; color: var(--muted) !important; margin-bottom: 0.4rem;
    }
    .sidebar-section {
        font-size: 0.78rem; font-weight: 700; letter-spacing: 0.6px;
        text-transform: uppercase; color: var(--primary) !important;
        margin: 0.4rem 0 0.2rem 0;
    }

    /* Inputs arrondis */
    section[data-testid="stSidebar"] [data-baseweb="select"] > div,
    section[data-testid="stSidebar"] .stNumberInput input {
        border-radius: 10px !important;
    }

    /* ---------- Bouton ---------- */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1e3a8a 100%);
        color: #ffffff !important;
        border: none;
        border-radius: 14px;
        padding: 0.8rem 2rem;
        font-size: 1.05rem;
        font-weight: 700;
        width: 100%;
        transition: transform .25s ease, box-shadow .25s ease;
        box-shadow: 0 8px 22px rgba(37,99,235,0.35);
    }
    .stButton > button p,
    .stButton > button span,
    .stButton > button * {
        color: #ffffff !important;
    }
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 14px 32px rgba(37,99,235,0.45);
    }
    .stButton > button:active { transform: translateY(-1px); }

    /* Expander */
    .streamlit-expanderHeader, [data-testid="stExpander"] summary {
        color: var(--primary-d) !important;
        font-weight: 600;
    }
    [data-testid="stExpander"] {
        border-radius: 16px !important;
        border: 1px solid rgba(30,58,138,0.08) !important;
        box-shadow: var(--shadow);
        background: var(--surface);
    }

    /* Messages */
    .stSuccess, .stWarning, .stError, .stInfo { border-radius: 12px; }

    /* Metric containers */
    [data-testid="stMetric"] {
        background: var(--surface);
        border-radius: 14px;
        padding: 0.8rem 1rem;
        box-shadow: var(--shadow);
        border: 1px solid rgba(30,58,138,0.06);
    }

    hr { margin: 1.6rem 0; border: none; border-top: 1px solid rgba(30,58,138,0.08); }

    /* Footer */
    .footer {
        text-align: center;
        color: var(--muted) !important;
        font-size: 0.8rem;
        margin-top: 3rem;
        padding: 1.4rem;
        border-top: 1px solid rgba(30,58,138,0.08);
    }

    /* Écran d'accueil */
    .welcome {
        text-align: center; padding: 2.6rem 1rem 1.6rem 1rem;
        animation: fadeUp 0.7s ease both;
    }
    .welcome h2 { color: var(--primary-d) !important; font-size: 1.7rem; }
    .welcome p { font-size: 1.08rem; color: var(--muted) !important; max-width: 720px; margin: 0.6rem auto 0 auto; }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# CHARGEMENT DES MODÈLES
# --------------------------------------------------------------------------

# Chemin de base : dossier contenant app.py (fonctionne en local ET sur Streamlit Cloud)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_resource
def load_models():
    """Charger le modèle ML sauvegardé."""
    models = {}

    ml_path = os.path.join(BASE_DIR, 'ml_model_artifacts.pkl')
    if os.path.exists(ml_path):
        try:
            with open(ml_path, 'rb') as f:
                models['ml'] = pickle.load(f)
        except Exception as e:
            st.warning(f"Modèle ML non chargé : {e}")
            models['ml'] = None
    else:
        models['ml'] = None

    return models


models = load_models()


# --------------------------------------------------------------------------
# FONCTIONS DE PRÉDICTION
# --------------------------------------------------------------------------

def predict_ml(user_input):
    """
    Prédiction via le meilleur modèle ML (pipeline XGBoost).
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

    # Aligner les colonnes avec ce que le modèle attend
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
# FONCTIONS D'AFFICHAGE DES RÉSULTATS
# --------------------------------------------------------------------------

def get_risk_level(prob):
    if prob < 0.15:
        return 'faible', '#10b981', 'low', 'result-card-risk-low'
    elif prob < 0.35:
        return 'modere', '#f59e0b', 'moderate', 'result-card-risk-moderate'
    else:
        return 'eleve', '#ef4444', 'high', 'result-card-risk-high'


def get_risk_comment(prob):
    level, _, _, _ = get_risk_level(prob)
    pct = prob * 100

    if level == 'faible':
        main = (
            f"Le risque estimé est faible ({pct:.1f}%). "
            "Votre profil présente plusieurs facteurs protecteurs. "
            "Un suivi médical régulier reste recommandé."
        )
        conseils = [
            "Continuez à consulter régulièrement un professionnel de santé.",
            "Maintenez les consultations prénatales en cas de grossesse.",
            "Assurez-vous que vos enfants bénéficient de tous les vaccins."
        ]
    elif level == 'modere':
        main = (
            f"Le risque estimé est modéré ({pct:.1f}%). "
            "Certains facteurs de vulnérabilité ont été identifiés. "
            "Un suivi renforcé est recommandé."
        )
        conseils = [
            "Consultez régulièrement un agent de santé ou une sage-femme.",
            "Si possible, accouchez dans un établissement de santé.",
            "Informez-vous sur la planification familiale et l'espacement des naissances.",
            "Signalez tout problème de santé de votre enfant dès les premiers signes."
        ]
    else:
        main = (
            f"Le risque estimé est élevé ({pct:.1f}%). "
            "Votre profil présente plusieurs facteurs de risque combinés. "
            "Un accompagnement médical étroit est fortement recommandé."
        )
        conseils = [
            "Consultez un professionnel de santé dans les meilleurs délais.",
            "Assurez-vous de suivre toutes les consultations prénatales recommandées.",
            "Privilégiez l'accouchement en milieu médical.",
            "Discutez avec votre médecin des mesures préventives disponibles.",
            "Renseignez-vous sur les programmes de santé communautaire dans votre région."
        ]

    return main, conseils


def gauge_html(prob, color):
    """Jauge linéaire animée en HTML/CSS (légère, sans matplotlib)."""
    pct = max(0.0, min(1.0, prob)) * 100
    return f"""
    <div class="gauge" style="--target:{pct:.1f}%;">
        <div class="gauge-bubble" style="color:{color};">{pct:.1f}%</div>
        <div class="gauge-track"></div>
        <div class="gauge-needle" style="background:{color};"></div>
        <div class="gauge-scale">
            <span class="s-low">Faible</span>
            <span class="s-mod">Modéré</span>
            <span class="s-high">Élevé</span>
        </div>
    </div>
    """


# --------------------------------------------------------------------------
# INTERFACE PRINCIPALE
# --------------------------------------------------------------------------

# Header
st.markdown("""
<div class="main-header">
    <span class="header-pill">EDS Cameroun 2018 · Femmes de 15 à 49 ans</span>
    <h1>Estimation du Risque de Mortalité Infantile</h1>
    <p>Outil d'aide à la sensibilisation basé sur les données de l'Enquête Démographique
    et de Santé (EDS) du Cameroun — propulsé par un modèle XGBoost évalué par
    validation croisée 5-fold sur 14 677 femmes (AUC = 0,889).</p>
</div>
""", unsafe_allow_html=True)

# Description et avertissement
with st.expander("À propos de cet outil", expanded=False):
    st.markdown("""
    **Cet outil estime la probabilité qu'une femme ayant le profil saisi
    ait perdu au moins un enfant, à partir d'un modèle de machine learning.**

    Les résultats sont issus d'une analyse de machine learning réalisée sur un échantillon
    représentatif de **14 677 femmes camerounaises** (EDS 2018). Six algorithmes ont été comparés
    (Régression Logistique, Random Forest, Gradient Boosting, XGBoost, LightGBM, CatBoost) ;
    XGBoost a obtenu les meilleures performances (AUC = 0,889). Les résultats reflètent
    des probabilités populationnelles et non une certitude individuelle.

    **Ce n'est pas un outil de diagnostic médical.** Les résultats doivent être interprétés
    avec l'aide d'un professionnel de santé.

    *Sources des données : Programme DHS (Demographic and Health Surveys), Cameroun 2018.*
    """)


# --------------------------------------------------------------------------
# SIDEBAR : FORMULAIRE DE SAISIE
# --------------------------------------------------------------------------

st.sidebar.markdown('<div class="sidebar-title">Votre profil</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sidebar-sub">Renseignez les informations ci-dessous</div>', unsafe_allow_html=True)
st.sidebar.markdown("---")

# AGE
age = st.sidebar.slider(
    "Âge (années)", min_value=15, max_value=49, value=28,
    help="Votre âge actuel en années complètes"
)

# EDUCATION
education = st.sidebar.selectbox(
    "Niveau d'éducation",
    options=['Superieur', 'Secondaire', 'Primaire', 'Aucun'],
    format_func=lambda x: {'Superieur': 'Supérieur', 'Secondaire': 'Secondaire',
                           'Primaire': 'Primaire', 'Aucun': 'Aucun'}[x],
    index=1,
    help="Le plus haut niveau d'éducation atteint"
)

# REGION
region = st.sidebar.selectbox(
    "Région de résidence",
    options=['Adamawa', 'Centre', 'Est', 'Extreme-Nord', 'Littoral',
             'Nord', 'Nord-Ouest', 'Ouest', 'Sud', 'Sud-Ouest'],
    format_func=lambda x: x.replace('Extreme-Nord', 'Extrême-Nord'),
    index=1
)

# MILIEU
milieu = st.sidebar.radio(
    "Milieu de résidence",
    options=['Urbain', 'Rural'],
    index=0,
    horizontal=True
)

# RICHESSE
richesse = st.sidebar.selectbox(
    "Niveau de richesse du ménage",
    options=['Tres_riche', 'Riche', 'Moyen', 'Pauvre', 'Tres_pauvre'],
    format_func=lambda x: {'Tres_riche': 'Très riche', 'Riche': 'Riche', 'Moyen': 'Moyen',
                           'Pauvre': 'Pauvre', 'Tres_pauvre': 'Très pauvre'}[x],
    index=2
)

# STATUT MATRIMONIAL
statut = st.sidebar.selectbox(
    "Situation matrimoniale",
    options=['En_union', 'Jamais_union', 'Ex_union'],
    format_func=lambda x: {
        'En_union': 'En union (mariée ou cohabitant)',
        'Jamais_union': 'Jamais en union (célibataire)',
        'Ex_union': 'Ancienne union (divorcée / veuve)'
    }[x],
    index=0
)

# RELIGION
religion = st.sidebar.selectbox(
    "Religion",
    options=['Catholique', 'Protestant', 'Muslman', 'Autre_Chretien', 'Animiste', 'Autre'],
    format_func=lambda x: {
        'Catholique': 'Catholique', 'Protestant': 'Protestant', 'Muslman': 'Musulman',
        'Autre_Chretien': 'Autre chrétien', 'Animiste': 'Animiste', 'Autre': 'Autre'
    }[x],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown('<div class="sidebar-section">Historique reproductif</div>', unsafe_allow_html=True)

# NB ENFANTS
nb_enfants = st.sidebar.number_input(
    "Nombre d'enfants nés vivants",
    min_value=0, max_value=20, value=2,
    help="Nombre total d'enfants que vous avez mis au monde vivants"
)

# AGE PREMIERE NAISSANCE
if nb_enfants > 0:
    age_premiere_naissance = st.sidebar.slider(
        "Âge à la première naissance",
        min_value=10, max_value=49, value=20,
        help="Votre âge quand vous avez eu votre premier enfant"
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
    "Naissances dans les 5 dernières années",
    min_value=0, max_value=5, value=0
)

# GROSSESSE INTERROMPUE
grossesse_interrompue = st.sidebar.checkbox(
    "Grossesse interrompue (fausse couche / avortement)",
    value=False
)

st.sidebar.markdown("---")
st.sidebar.markdown('<div class="sidebar-section">Accès aux soins</div>', unsafe_allow_html=True)

# EMPLOI
emploi = st.sidebar.radio("Actuellement en emploi", ['Oui', 'Non'], index=0, horizontal=True)

# ASSURANCE
assurance = st.sidebar.radio("Couverture par assurance maladie", ['Non', 'Oui'], index=0, horizontal=True)

# CONSULTATION
consultation_etablissement = st.sidebar.checkbox(
    "Consulté un établissement de santé (12 derniers mois)", value=False
)
visite_agent_sante = st.sidebar.checkbox(
    "Visitée par un agent de santé (12 derniers mois)", value=False
)
electricite = st.sidebar.checkbox("Ménage avec électricité", value=False)

# TAILLE MENAGE
taille_menage = st.sidebar.slider("Taille du ménage (personnes)", 1, 20, 5)

# PROBLEMES ACCES SANTE
st.sidebar.markdown('<div class="sidebar-section">Obstacles à l\'accès aux soins</div>', unsafe_allow_html=True)
st.sidebar.markdown("*Cochez si c'est un gros problème pour vous :*")
pb_permission = st.sidebar.checkbox("Obtenir la permission de se soigner", False)
pb_argent = st.sidebar.checkbox("Trouver l'argent nécessaire", False)
pb_distance = st.sidebar.checkbox("Distance jusqu'à l'établissement de santé", False)
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
    # Construire l'entrée utilisateur
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

    # Prédiction ML
    prob_ml = predict_ml(user_input)

    # ----------- AFFICHAGE DES RÉSULTATS -----------
    st.markdown("## Résultats de l'estimation")

    risk_labels = {'faible': 'RISQUE FAIBLE', 'modere': 'RISQUE MODÉRÉ', 'eleve': 'RISQUE ÉLEVÉ'}
    badge_classes = {'faible': 'badge-low', 'modere': 'badge-moderate', 'eleve': 'badge-high'}

    best_name = models['ml'].get('best_model_name', 'XGBoost') if models['ml'] else 'XGBoost'
    st.markdown(f'<span class="method-badge-ml">Machine Learning · {best_name}</span>', unsafe_allow_html=True)

    if prob_ml is not None:
        level_ml, color_ml, _, card_class_ml = get_risk_level(prob_ml)
        st.markdown(gauge_html(prob_ml, color_ml), unsafe_allow_html=True)

        st.markdown(f"""
        <div class="result-card {card_class_ml}">
            <span class="risk-badge {badge_classes[level_ml]}"><span class="dot"></span>{risk_labels[level_ml]}</span>
            <div class="prob-number" style="color:{color_ml};">{prob_ml*100:.1f}%</div>
            <small>Probabilité estimée d'avoir perdu au moins un enfant</small>
        </div>
        """, unsafe_allow_html=True)

        main_comment_ml, conseils_ml = get_risk_comment(prob_ml)
        st.markdown(f"**Interprétation :** {main_comment_ml}")

        st.markdown("**Indicateurs du modèle :**")
        if models['ml']:
            c1, c2, c3 = st.columns(3)
            test_results_ml = models['ml'].get('test_results', {})
            best = test_results_ml.get(best_name, {})
            c1.metric("AUC-ROC", f"{best.get('AUC', 0):.3f}")
            c2.metric("F1-Score", f"{best.get('F1', 0):.3f}")
            c3.metric("Rappel", f"{best.get('Recall', 0):.3f}")
    else:
        st.error("Modèle ML non disponible.")

    # --- RECOMMANDATIONS ---
    st.markdown("---")
    st.markdown("### Recommandations")

    if prob_ml is not None:
        _, conseils = get_risk_comment(prob_ml)
        cols = st.columns(min(3, len(conseils)))
        for i, conseil in enumerate(conseils):
            with cols[i % len(cols)]:
                st.markdown(f"""
                <div class="conseil-card">
                    <span class="conseil-num">{i+1}</span>
                    <p>{conseil}</p>
                </div>
                """, unsafe_allow_html=True)

    # Disclaimer
    st.markdown("""
    <div style="background:linear-gradient(135deg,#fff8e6,#fff3cd); border-radius:14px; padding:1.1rem 1.4rem;
                border-left:4px solid #f59e0b; margin-top:1.2rem; color:#7a5400;">
    <strong style="color:#7a5400;">Avertissement :</strong>
    <span style="color:#7a5400;"> Cet outil a une vocation exclusivement informative et éducative.
    Les probabilités affichées sont des estimations populationnelles issues de modèles de machine learning.
    Elles ne constituent pas un diagnostic médical individuel et ne doivent pas se substituer
    à une consultation médicale professionnelle.</span>
    </div>
    """, unsafe_allow_html=True)

else:
    # Écran d'accueil
    st.markdown("""
    <div class="welcome">
        <h2>Comment utiliser cet outil ?</h2>
        <p>
        Remplissez le formulaire dans la barre latérale gauche avec votre profil
        (âge, niveau d'éducation, région, situation économique, accès aux soins, etc.),
        puis cliquez sur « Estimer mon risque » pour obtenir une estimation personnalisée.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Méthodologie
    st.markdown("### Méthode utilisée")

    st.markdown("""
    <div class="method-card">
        <span class="method-badge-ml">Machine Learning</span>
        <h4>XGBoost — meilleur modèle (AUC = 0,889)</h4>
        <p>Six algorithmes de classification supervisée ont été comparés sur les données EDS 2018 :
        Régression Logistique, Random Forest, Gradient Boosting, XGBoost, LightGBM et CatBoost.
        XGBoost a obtenu les meilleures performances, confirmées par validation croisée 5-fold
        et évaluation sur un échantillon de test vierge (25 %).</p>
        <ul>
            <li>14 677 femmes camerounaises analysées</li>
            <li>AUC = 0,889 · F1-Score = 0,64 · Rappel = 0,72</li>
            <li>Interprétabilité assurée par les valeurs SHAP</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Facteurs clés
    st.markdown("### Principaux facteurs identifiés (SHAP + Régression logistique)")

    facteurs = {
        "Âge à la première naissance < 18 ans": ("Facteur de risque majeur", "ef4444"),
        "Absence d'éducation formelle": ("Facteur de risque élevé", "ef4444"),
        "Pauvreté sévère": ("Facteur de risque modéré", "f59e0b"),
        "Consultation d'un établissement de santé": ("Facteur protecteur", "10b981"),
        "Visite par un agent de santé": ("Facteur protecteur", "10b981"),
    }

    cols_f = st.columns(len(facteurs))
    for i, (facteur, (desc, clr)) in enumerate(facteurs.items()):
        with cols_f[i]:
            st.markdown(f"""
            <div class="factor-card" style="border-top-color:#{clr};">
                <p style="font-size:0.78rem; font-weight:700; color:#{clr}; margin:0;">{desc}</p>
                <p style="font-size:0.85rem; margin:0.45rem 0 0 0; color:#1e2a3a;">{facteur}</p>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    Outil développé à partir des données EDS Cameroun 2018 (Programme DHS / ICF International).
    Modèle XGBoost évalué par validation croisée 5-fold. À des fins de recherche et d'information uniquement.
</div>
""", unsafe_allow_html=True)
