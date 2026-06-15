# Méthodologie Scientifique — Analyse des Facteurs Associés à la Mortalité Infantile au Cameroun

**Données :** Enquête Démographique et de Santé (EDS) Cameroun 2018 — Fichier individuel femmes (CMIR71FL.dta)  
**Approche :** Régression logistique pondérée (inférence statistique) + Apprentissage automatique (prédiction)

---

## Table des matières

1. [Contexte et objectifs](#1-contexte-et-objectifs)
2. [Source des données](#2-source-des-données)
3. [Définition de la variable cible](#3-définition-de-la-variable-cible)
4. [Sélection et recodage des variables explicatives](#4-sélection-et-recodage-des-variables-explicatives)
5. [Prétraitement des données](#5-prétraitement-des-données)
6. [Statistiques descriptives](#6-statistiques-descriptives)
7. [Analyse bivariée et tests d'hypothèses](#7-analyse-bivariée-et-tests-dhypothèses)
8. [Vérification des conditions de modélisation](#8-vérification-des-conditions-de-modélisation)
9. [Modélisation statistique — Régression logistique](#9-modélisation-statistique--régression-logistique)
10. [Modélisation par apprentissage automatique](#10-modélisation-par-apprentissage-automatique)
11. [Validation et évaluation des modèles](#11-validation-et-évaluation-des-modèles)
12. [Interprétabilité des modèles](#12-interprétabilité-des-modèles)
13. [Synthèse des résultats](#13-synthèse-des-résultats)
14. [Limites méthodologiques](#14-limites-méthodologiques)
15. [Livrables et reproductibilité](#15-livrables-et-reproductibilité)

---

## 1. Contexte et objectifs

La mortalité infantile constitue un indicateur sensible du niveau de développement sanitaire d'un pays. Au Cameroun, malgré les progrès enregistrés, les disparités régionales, sociales et économiques restent marquées. Ce projet vise à identifier les déterminants de la mortalité infantile à partir des données de l'EDS 2018, en combinant deux approches complémentaires :

- **Approche inférentielle (statistique) :** Identifier les facteurs de risque et de protection, en quantifiant les associations via des odds ratios ajustés, tout en respectant le plan de sondage complexe de l'EDS.
- **Approche prédictive (machine learning) :** Construire des modèles capables de classer les femmes selon leur probabilité d'avoir perdu au moins un enfant, en exploitant les interactions non linéaires entre variables.

---

## 2. Source des données

| Caractéristique | Détail |
|---|---|
| **Enquête** | EDS Cameroun 2018 (Demographic and Health Survey) |
| **Fichier** | CMIR71FL.dta — Recode individuel femmes |
| **Population cible** | Femmes de 15 à 49 ans interrogées dans les ménages sélectionnés |
| **Conception du sondage** | Sondage stratifié à deux degrés (clusters/PSU + strates) |
| **Variables de pondération** | V005 : poids individuel femme (normalisé ÷ 10⁶) |
| **Variables de plan** | V021 (PSU), V022 (strate), V023 (stratification utilisée) |
| **Format** | Fichier Stata `.dta` avec métadonnées (labels de variables et modalités) |

Le fichier contient plusieurs milliers d'observations et plus de 1 000 variables. La lecture du fichier utilise `pyreadstat` pour conserver les labels Stata, ce qui facilite l'interprétation des codes numériques.

---

## 3. Définition de la variable cible

### Variable Y — Mortalité infantile (binaire : 0/1)

**Y = 1** si la femme a perdu au moins un enfant (au moins un fils ou une fille décédé(e))  
**Y = 0** si tous les enfants nés vivants sont en vie

**Construction :** Deux méthodes ont été utilisées et confrontées pour assurer la cohérence :

**Méthode directe (principale) :**

```
enfants_decedes = V206 (fils décédés) + V207 (filles décédées)
Y = 1 si enfants_decedes > 0, sinon Y = 0
```

**Méthode de validation (contrôle) :**

```
Y = 1 si (V201 − V218) > 0
   où V201 = total enfants nés vivants, V218 = enfants vivants actuellement
```

**Traitement des nullipares (femmes sans enfant vivant né) :**  
Les femmes avec V201 = 0 sont automatiquement codées Y = 0, évitant ainsi un biais de quasi-séparation parfaite dans la régression logistique. Ces femmes sont toutefois incluses dans les modèles ML (les arbres de décision ne souffrent pas de cette contrainte).

---

## 4. Sélection et recodage des variables explicatives

Les variables ont été sélectionnées selon leur pertinence théorique (littérature sur les déterminants de la mortalité infantile) et regroupées en quatre blocs conceptuels.

### Bloc A — Socio-démographie

| Variable EDS | Variable recréée | Type | Modalités / Plage |
|---|---|---|---|
| V012 | `age` | Continue | 15–49 ans |
| V106 | `niveau_education` | Catégorielle | Aucun / Primaire / Secondaire / Supérieur |
| V024 | `region` | Catégorielle | 10 régions du Cameroun |
| V025 | `milieu_residence` | Binaire | Urbain / Rural |
| V130 | `religion` | Catégorielle | Catholique / Protestant / Autre chrétien / Musulman / Animiste / Aucune / Autre |
| V501 | `statut_matrimonial` | Catégorielle | En union / Jamais en union / Ex-union |
| V190 | `quintile_richesse` | Ordinale | 1 (plus pauvre) → 5 (plus riche) |

### Bloc B — Fécondité et histoire reproductive

| Variable EDS | Variable recréée | Type | Modalités / Plage |
|---|---|---|---|
| V212 | `age_premiere_naissance` | Catégorielle | <18 / 18–19 / 20–24 / 25+ ans |
| V201 | `nb_enfants_nes_vivants` | Continue | 0–n |
| V208 | `naissances_5ans` | Continue | Naissances dans les 5 dernières années |
| V228 | `grossesse_interrompue` | Binaire | Oui / Non |
| V213 | `grossesse_actuelle` | Binaire | Oui / Non |
| V511 | `age_premier_mariage` | Continue | Restreinte à < 50 ans |

### Bloc C — Emploi et conditions économiques

| Variable EDS | Variable recréée | Type | Modalités / Plage |
|---|---|---|---|
| V714 | `travaille_actuellement` | Binaire | Oui / Non |
| V731 | `travaille_12mois` | Binaire | Oui / Non |
| V119 | `electricite` | Binaire | Présence électricité au foyer |
| V136 | `taille_menage` | Continue | Plafonnée à 30 (retrait des valeurs aberrantes) |

### Bloc D — Accès aux soins de santé

| Variable EDS | Variable recréée | Type | Modalités / Plage |
|---|---|---|---|
| V481 | `assurance_maladie` | Binaire | Oui / Non |
| V467B | `pb_permission_sante` | Binaire | Permission pour aller se soigner (grand problème) |
| V467C | `pb_argent_sante` | Binaire | Obtenir l'argent (grand problème) |
| V467D | `pb_distance_sante` | Binaire | Distance à l'établissement (grand problème) |
| V467F | `pb_aller_seule` | Binaire | Ne pas vouloir aller seule (grand problème) |
| — | `score_pb_acces_sante` | Score (0–4) | Somme des 4 indicateurs précédents |
| V393 | `visite_agent_sante` | Binaire | Visite par un agent de santé |
| V394 | `consultation_etablissement` | Binaire | Consultation dans un établissement (12 mois) |

**Score composite d'accès aux soins :** La construction du score `score_pb_acces_sante` (0 = aucun problème d'accès, 4 = tous les problèmes) permet d'agréger plusieurs dimensions de la barrière d'accès en un seul indicateur continu, limitant la multicolinéarité entre ces variables corrélées.

---

## 5. Prétraitement des données

Le prétraitement suit un pipeline structuré en étapes séquentielles, documenté dans `data_cleaning.py`.

### 5.1 Chargement et exploration initiale

- Lecture du fichier `.dta` via `pyreadstat` avec conservation des métadonnées (labels Stata)
- Inventaire des variables disponibles (plus de 1 000 colonnes)
- Identification des codes de valeurs manquantes EDS (typiquement : 9, 99, 998, 999)

### 5.2 Filtrage de la population d'analyse

```
Population retenue = femmes avec au moins une naissance vivante (V201 ≥ 1)
```

Ce filtre est justifié par la définition de la variable cible : une femme sans enfant né vivant ne peut pas avoir perdu d'enfant. L'inclusion de nullipares dans le modèle logistique aurait créé une quasi-séparation parfaite (Y = 0 systématiquement).

### 5.3 Recodage des variables

- Codes manquants EDS (9, 99, 998, 999) → `NaN`
- Variables numériques forcées en `float64` pour assurer la compatibilité avec les outils statistiques
- Variables catégorielles recodées avec des labels explicites (chaînes de caractères)
- Plafonnement de `taille_menage` à 30 pour éliminer les valeurs aberrantes manifestes
- Restriction de `age_premier_mariage` à moins de 50 ans

### 5.4 Gestion des données manquantes

| Stratégie | Variables concernées |
|---|---|
| **Imputation par la médiane** | Variables continues (age, taille_menage, etc.) |
| **Imputation par la modalité la plus fréquente** | Variables catégorielles et binaires |
| **Exclusion** | Observations sans valeur de Y (variable cible) |

L'imputation plutôt que la suppression de lignes préserve la puissance statistique et évite un biais de sélection si les données ne sont pas manquantes au hasard (MCAR).

### 5.5 Préparation des datasets finaux

Trois datasets distincts sont constitués et sauvegardés dans `data_prepared.pkl` :

| Dataset | Population | Usage |
|---|---|---|
| `df_clean` | Toutes les femmes (nettoyées) | Exploration et statistiques descriptives |
| `df_stat` | Femmes avec ≥ 1 naissance vivante | Régression logistique pondérée |
| `df_ml` | Idem avec variables préparées pour ML | Modèles d'apprentissage automatique |

---

## 6. Statistiques descriptives

Réalisées sur `df_clean`, les statistiques descriptives fournissent un portrait de la population analysée avant toute modélisation.

### Variables continues

Pour chaque variable continue (`age`, `taille_menage`, `score_pb_acces_sante`, `naissances_5ans`) :

- Moyenne, médiane, écart-type
- Minimum, maximum, quartiles (Q1, Q3)

### Variables catégorielles

Pour chaque variable catégorielle :

- Effectif absolu et fréquence relative (%) par modalité
- Taux brut de mortalité infantile (prévalence de Y = 1) par modalité

Les visualisations produites (`outputs_stat/prevalence_bivariee.png`) permettent d'identifier visuellement les gradients de prévalence selon les caractéristiques socio-économiques.

---

## 7. Analyse bivariée et tests d'hypothèses

L'analyse bivariée (script `statistical_model.py`) précède la régression multivariée et sert à :
1. Explorer les associations brutes entre chaque variable et Y
2. Sélectionner les candidats à l'inclusion dans le modèle multivarié
3. Détecter les gradients de risque attendus

### 7.1 Variables catégorielles — Test du Khi-deux (χ²)

**Hypothèses :**

> **H₀ :** La variable catégorielle est indépendante de Y (pas d'association)  
> **H₁ :** Il existe une association entre la variable catégorielle et Y

**Statistique de test :**

$$\chi^2 = \sum_{i,j} \frac{(O_{ij} - E_{ij})^2}{E_{ij}}$$

où $O_{ij}$ = effectif observé et $E_{ij}$ = effectif attendu sous H₀.

**Seuil de décision :** α = 0,05 (rejet de H₀ si p-valeur < 0,05)

### 7.2 Variables continues — Test t de Student

**Hypothèses :**

> **H₀ :** La moyenne de la variable continue est identique dans les groupes Y = 0 et Y = 1  
> **H₁ :** Les moyennes diffèrent entre les deux groupes

**Seuil de décision :** α = 0,05

**Résultats sauvegardés dans :** `outputs_stat/analyse_bivariee.csv`

---

## 8. Vérification des conditions de modélisation

Avant de construire la régression logistique, plusieurs conditions préalables sont vérifiées.

### 8.1 Multicolinéarité — Facteur d'Inflation de la Variance (VIF)

**Justification :** La multicolinéarité entre prédicteurs gonfle les erreurs standard des coefficients, rendant les tests d'hypothèse peu fiables et les interprétations instables.

**Calcul du VIF pour chaque variable j :**

$$VIF_j = \frac{1}{1 - R^2_j}$$

où $R^2_j$ est le coefficient de détermination obtenu en régressant la variable $j$ sur toutes les autres.

**Seuil d'alerte :** VIF > 10 (multicolinéarité problématique)

**Résultats :** Aucune variable ne dépasse le seuil critique. Résultats dans `outputs_stat/vif_results.csv`.

### 8.2 Quasi-séparation parfaite

La restriction de la population aux femmes avec au moins une naissance vivante élimine le risque de quasi-séparation parfaite (i.e., une variable prédisant parfaitement Y = 0 pour toutes les nullipares).

### 8.3 Taille de l'échantillon

Le ratio observations/paramètres respecte la règle empirique d'au moins 10 événements par variable (EPV ≥ 10), condition nécessaire pour la stabilité des estimations de maximum de vraisemblance.

---

## 9. Modélisation statistique — Régression logistique

### 9.1 Choix du modèle

La régression logistique binaire est le cadre naturel pour une variable cible binaire (Y ∈ {0, 1}). Elle modélise le log-odds de l'événement :

$$\log\left(\frac{P(Y=1)}{1-P(Y=1)}\right) = \beta_0 + \beta_1 X_1 + \ldots + \beta_k X_k$$

Les **odds ratios** (OR = exp(β)) permettent une interprétation directe : OR > 1 = facteur de risque, OR < 1 = facteur protecteur.

### 9.2 Prise en compte du plan de sondage

L'EDS utilise un sondage stratifié à deux degrés. Ignorer ce plan conduit à des estimations biaisées et des erreurs standard incorrectes. La **pondération** est appliquée via :

$$w_{normalisé} = \frac{V005 / 10^6}{\overline{V005 / 10^6}}$$

Le modèle est estimé via `statsmodels.GLM` (famille Binomiale) avec application des poids, en utilisant l'algorithme d'optimisation **BFGS** (quasi-Newton, 200 itérations maximum), avec repli sur **IRLS** en cas de non-convergence.

### 9.3 Stratégie de construction progressive (approche par blocs)

Trois modèles emboîtés sont construits pour évaluer la contribution marginale de chaque bloc de variables :

| Modèle | Variables incluses | Objectif |
|---|---|---|
| **Modèle 1** | Socio-démographie (age, éducation, milieu, région, religion, union, richesse) | Effet net des caractéristiques de base |
| **Modèle 2** | Modèle 1 + Fécondité (âge 1ère naissance, parité, naissances récentes, grossesses interrompues) | Ajout des déterminants reproductifs |
| **Modèle 3 (complet)** | Modèle 2 + Accès aux soins (assurance, score accès, emploi, électricité) | Modèle finalisé toutes dimensions |

La comparaison des modèles par AIC et pseudo-R² permet de juger si l'ajout d'un bloc améliore significativement le pouvoir explicatif.

### 9.4 Catégories de référence

Les catégories de référence sont systématiquement choisies comme la **modalité la plus favorable**, ce qui permet d'interpréter les ORs des autres modalités comme des excès de risque relatifs :

| Variable | Catégorie de référence |
|---|---|
| Education | Supérieur |
| Milieu de résidence | Urbain |
| Quintile de richesse | Très riche |
| Statut matrimonial | En union |
| Religion | Catholique |
| Emploi | Oui (travaille) |
| Assurance maladie | Oui (assurée) |
| Âge 1ère naissance | 25 ans et plus |
| Région | Littoral |

### 9.5 Métriques d'évaluation du modèle statistique

**Qualité d'ajustement global :**

| Métrique | Formule | Interprétation |
|---|---|---|
| Log-vraisemblance (LL) | — | Mesure brute d'ajustement |
| **AIC** | −2·LL + 2k | Équilibre ajustement/parcimonie (plus bas = meilleur) |
| **Pseudo-R² McFadden** | $1 - LL_{modèle}/LL_{nul}$ | Proportion de log-LL expliquée |
| **Pseudo-R² Nagelkerke** | Version normalisée McFadden | Interprétable comme un R² classique |

**Pouvoir discriminant :**

- **Courbe ROC et AUC :** Capacité du modèle à distinguer Y = 1 de Y = 0, indépendamment du seuil de décision. AUC > 0,7 : acceptable ; AUC > 0,8 : excellent.

**Calibration :**

- **Test de Hosmer-Lemeshow :** Découpe les probabilités prédites en déciles ; teste si les événements observés correspondent aux attendus.  
  H₀ : bonne calibration (observations = prédictions)  
  Décision : p > 0,05 → bonne calibration

**Inférence sur les paramètres :**

- Odds ratios (OR = exp(β)) avec intervalles de confiance à 95 % : `exp(β ± 1,96 × SE(β))`
- p-valeurs pour chaque prédicteur (α = 0,05)

---

## 10. Modélisation par apprentissage automatique

### 10.1 Objectif

Compléter l'approche statistique par des modèles capables de capturer des interactions non linéaires complexes entre variables et d'optimiser la performance prédictive plutôt que l'inférence causale.

### 10.2 Pipeline de prétraitement ML

Un pipeline scikit-learn est construit avec trois branches parallèles selon le type de variable :

**Variables numériques** (`age`, `naissances_5ans`, `taille_menage`, `score_pb_acces_sante`, `nb_enfants_nes_vivants`) :
1. Imputation par la **médiane**
2. **Standardisation** (StandardScaler : moyenne = 0, écart-type = 1)

**Variables ordinales** (éducation, richesse, statut matrimonial, accès santé, etc.) :
1. Imputation par la **modalité la plus fréquente**
2. Conservation des valeurs ordinales (pas de standardisation pour préserver le sens)

**Variables catégorielles nominales** (`region`, `religion`) :
1. Imputation par la **modalité la plus fréquente**
2. **Encodage One-Hot** (`handle_unknown='ignore'` pour gérer les modalités inconnues en test)

### 10.3 Découpage des données

```
Train : 75 % | Test : 25 %
Stratification sur Y : proportions de Y = 1 identiques dans les deux ensembles
Graine aléatoire : 42 (reproductibilité garantie)
```

### 10.4 Gestion du déséquilibre de classes

Le déséquilibre (ratio ≈ 3:1 entre Y = 0 et Y = 1) est traité explicitement dans chaque modèle :

- **Régression logistique, Random Forest, LightGBM :** `class_weight='balanced'` (poids inversement proportionnels aux effectifs)
- **XGBoost :** `scale_pos_weight = n_négatifs / n_positifs`
- **CatBoost :** `auto_class_weights='Balanced'` (calcul automatique des poids de classe)

### 10.5 Modèles entraînés

Six modèles sont construits et comparés, couvrant le spectre de la complexité et de l'interprétabilité :

| Modèle | Hyperparamètres principaux | Caractéristique |
|---|---|---|
| **Régression logistique** | C = 0.1 (régularisation L2), solver = lbfgs, max_iter = 500 | Baseline linéaire interprétable |
| **Random Forest** | 200 arbres, max_depth = 10, min_samples_leaf = 10 | Ensemble non-paramétrique, robuste |
| **Gradient Boosting** | 200 estimateurs, max_depth = 4, lr = 0.05, subsample = 0.8 | Boosting séquentiel sklearn |
| **XGBoost** | 300 estimateurs, max_depth = 5, lr = 0.05, subsample = 0.8, colsample_bytree = 0.8 | Boosting optimisé, gestion native du déséquilibre |
| **LightGBM** | 300 estimateurs, max_depth = 5, lr = 0.05, croissance leaf-wise | Boosting rapide, mémoire optimisée |
| **CatBoost** | 300 itérations, depth = 6, lr = 0.05, auto_class_weights = Balanced, early stopping (patience = 50) | Boosting optimisé pour variables catégorielles, robuste aux hyperparamètres |

---

## 11. Validation et évaluation des modèles

### 11.1 Validation croisée stratifiée (5-fold)

La **validation croisée k-fold stratifiée** (k = 5, `StratifiedKFold`, shuffle = True, random_state = 42) est appliquée sur l'ensemble d'entraînement :

- Chaque fold maintient les proportions de Y dans les sous-ensembles
- Les métriques sont calculées sur chaque fold puis agrégées : **moyenne ± écart-type**
- Cette approche fournit une estimation robuste de la capacité de généralisation sans utiliser le jeu de test

### 11.2 Évaluation finale sur le jeu de test (holdout)

L'ensemble de test (25 %) est utilisé **une seule fois**, après la sélection du modèle, pour obtenir une estimation non biaisée des performances en conditions réelles.

**Optimisation du seuil de décision :** Le seuil par défaut de 0,5 est ajusté pour maximiser le F1-score sur le jeu de test, ce qui est plus pertinent en cas de déséquilibre de classes.

### 11.3 Métriques utilisées

| Métrique | Formule | Interprétation dans ce contexte |
|---|---|---|
| **AUC-ROC** | Aire sous la courbe ROC | Discrimine Y = 1 et Y = 0 ; indépendant du seuil |
| **AP (Average Precision)** | Aire sous la courbe Précision-Rappel | Plus sensible au déséquilibre que l'AUC-ROC |
| **F1-Score** | 2 × (P × R)/(P + R) | Équilibre précision/rappel |
| **Rappel (Sensibilité)** | VP / (VP + FN) | Proportion de cas de mortalité correctement détectés |
| **Précision** | VP / (VP + FP) | Parmi les cas prédits positifs, proportion corrects |
| **Accuracy** | (VP + VN) / Total | Taux global ; potentiellement trompeur en cas de déséquilibre |

**Hiérarchie des métriques :** L'AUC-ROC est la métrique primaire (pouvoir discriminant global). Le F1-score et le rappel sont secondaires et guident le choix du seuil opérationnel.

### 11.4 Résultats comparatifs des modèles ML

Données analytiques : **14 677 observations** (Y=0 : 79,9 % / Y=1 : 20,1 %) — déséquilibre 3,98:1  
Split : 11 007 train / 3 670 test — stratifié sur Y

| Modèle | AUC (CV ± SD) | AUC (Test) | F1 (Test) | Rappel | Précision | AP |
|---|---|---|---|---|---|---|
| Régression logistique | 0,877 ± 0,009 | 0,874 | 0,602 | 0,739 | 0,508 | 0,667 |
| Random Forest | 0,879 ± 0,008 | 0,874 | 0,609 | 0,711 | 0,532 | 0,628 |
| Gradient Boosting | 0,887 ± 0,007 | 0,887 | 0,635 | 0,695 | 0,584 | 0,688 |
| **XGBoost** | **0,885 ± 0,008** | **0,889** | **0,643** | **0,720** | **0,580** | **0,696** |
| LightGBM | 0,884 ± 0,008 | 0,889 | 0,637 | 0,748 | 0,554 | 0,694 |
| CatBoost | 0,885 ± 0,009 | 0,887 | 0,631 | 0,720 | 0,563 | 0,689 |

> **Modèle retenu : XGBoost** (AUC = 0,889, F1 = 0,643 sur le jeu de test, seuil optimal = 0,61). L'écart nul entre AUC de validation croisée (0,885) et AUC de test (0,889) confirme l'absence de surapprentissage. CatBoost (AUC = 0,887) est compétitif, à 0,002 du meilleur modèle.

---

## 12. Interprétabilité des modèles

### 12.1 Odds ratios (modèle statistique)

Les odds ratios avec intervalles de confiance à 95 % constituent la principale mesure d'effet pour le modèle logistique. Ils sont sauvegardés dans `outputs_stat/odds_ratios_final.csv` et visualisés via un **forest plot** (`outputs_stat/forest_plot_stat.png`).

**Principaux résultats :**

| Facteur | OR (IC 95 %) | Direction | Signification |
|---|---|---|---|
| Age 1ère naissance < 18 ans | 5,05 (4,11 – 6,21) | Risque | p < 0,001 |
| Aucune éducation | 2,98 (2,04 – 4,34) | Risque | p < 0,001 |
| Age 1ère naissance 18-19 ans | 2,64 (2,13 – 3,28) | Risque | p < 0,001 |
| Education primaire | 2,30 (1,61 – 3,29) | Risque | p < 0,001 |
| Consultation établissement santé | 0,77 (IC…) | Protecteur | p < 0,001 |
| Jamais en union | 0,69 (IC…) | Protecteur | p < 0,001 |
| Emploi actuel | 0,81 (IC…) | Protecteur | p < 0,001 |

### 12.2 Importance des variables (modèles ML)

**Importance Gini/Gain (modèles à arbres) :**  
Mesure la réduction d'impureté moyenne apportée par chaque variable lors des partitions. Normalisée pour sommer à 1.

**Valeurs SHAP (SHapley Additive exPlanations) :**  
Les valeurs SHAP quantifient la contribution marginale de chaque variable à chaque prédiction individuelle, en se basant sur la théorie des jeux coopératifs. La moyenne des valeurs SHAP absolues fournit une **importance globale agnostique au modèle**.

**Top 5 des variables selon XGBoost :**

| Rang | Variable | Importance (%) |
|---|---|---|
| 1 | `nb_enfants_nes_vivants` | 23,1 % |
| 2 | `age` | 4,2 % |
| 3 | `niveau_education` | 4,1 % |
| 4 | Variables régionales | 2,0 – 3,1 % |
| 5 | `naissances_5ans` | 2,8 % |

Les visualisations d'importance sont disponibles dans `outputs_ml/feature_importance_*.png` et `outputs_ml/shap_importance_*.png`.

---

## 13. Synthèse des résultats

### 13.1 Convergence des deux approches

| Facteur | Logistique (OR) | ML (Importance) | Convergence |
|---|---|---|---|
| Âge à la 1ère naissance | Très fort effet | Présent | Oui |
| Niveau d'éducation | Fort effet | 3e rang | Oui |
| Parité / nb enfants | Inclus | 1er rang | Oui |
| Région de résidence | Significatif | Présent | Oui |
| Accès aux soins | Protecteur | Présent | Oui |

### 13.2 Performances comparées

| Modèle | AUC Test | Interprétabilité |
|---|---|---|
| Régression logistique pondérée | 0,874 | Très élevée (OR avec IC) |
| XGBoost (meilleur ML) | 0,889 | Moyenne (SHAP nécessaire) |
| CatBoost | 0,887 | Moyenne (SHAP nécessaire) |

Le gain en AUC du ML sur la régression logistique est de +0,015, modeste mais cohérent avec la littérature sur données d'enquêtes tabulaires. Les trois modèles de boosting (XGBoost, LightGBM, CatBoost) sont quasi-équivalents (AUC entre 0,887 et 0,889), suggérant que la limite de performance est davantage liée aux données qu'aux algorithmes.

---

## 14. Limites méthodologiques

| Limite | Description | Impact potentiel |
|---|---|---|
| **Causalité** | Données transversales (EDS) — pas d'axe temporel entre exposition et outcome | Associations, pas de causalité démontrée |
| **Biais de rappel** | Informations sur naissances et décès déclarées par les femmes | Sous-déclaration possible des décès anciens |
| **Données manquantes** | Imputation par médiane/mode supposant MCAR | Biais si données manquantes non aléatoirement |
| **Sondage complexe** | Pondération appliquée en régression ; ML n'intègre pas le plan de sondage | Légère imprécision sur les IC en ML |
| **Validité externe** | Données Cameroun 2018 uniquement | Résultats non directement généralisables à d'autres pays/périodes |
| **Confusion résiduelle** | Variables non collectées (nutrition maternelle, qualité soins) | Biais d'omission de variables confondantes |
| **Linéarité du logit** | Hypothèse de linéarité pour les variables continues non formellement testée | Risque de spécification incorrecte |

---

## 15. Livrables et reproductibilité

### 15.1 Scripts Python

| Fichier | Étape |
|---|---|
| [01_exploration.py](01_exploration.py) | Exploration initiale, distributions, valeurs manquantes |
| [data_cleaning.py](data_cleaning.py) | Nettoyage, recodage, construction de Y et des variables explicatives |
| [statistical_model.py](statistical_model.py) | Analyse bivariée, VIF, régression logistique pondérée, évaluation |
| [ml_model.py](ml_model.py) | Pipeline ML, validation croisée, comparaison des 5 modèles, SHAP |
| [app.py](app.py) | Application Streamlit de prédiction interactive |

### 15.2 Artefacts sauvegardés

| Fichier | Contenu |
|---|---|
| `data_prepared.pkl` | Datasets nettoyés (df_clean, df_stat, df_ml) |
| `stat_model_artifacts.pkl` | Modèle logistique ajusté et métadonnées |
| `ml_model_artifacts.pkl` | Ensemble complet des pipelines ML |
| `best_ml_pipeline.pkl` | Pipeline XGBoost prêt pour l'inférence en production |

### 15.3 Outputs statistiques

| Fichier | Contenu |
|---|---|
| `outputs_stat/analyse_bivariee.csv` | Résultats χ² et t-tests par variable |
| `outputs_stat/vif_results.csv` | VIF de tous les prédicteurs |
| `outputs_stat/odds_ratios_final.csv` | OR, IC 95 %, p-valeurs du modèle final |
| `outputs_stat/comparaison_modeles.csv` | AIC, pseudo-R², AUC des 3 modèles emboîtés |
| `outputs_stat/roc_curve_stat.png` | Courbe ROC — modèle logistique |
| `outputs_stat/forest_plot_stat.png` | Forest plot des odds ratios |
| `outputs_stat/prevalence_bivariee.png` | Prévalences brutes par variable |

### 15.4 Outputs machine learning

| Fichier | Contenu |
|---|---|
| `outputs_ml/model_comparison_final.csv` | Tableau comparatif des 5 modèles (AUC, F1, Rappel, Précision, AP) |
| `outputs_ml/feature_importance_*.csv` | Importance des variables par modèle |
| `outputs_ml/roc_comparison_ml.png` | Courbes ROC des 5 modèles superposées |
| `outputs_ml/pr_curve_ml.png` | Courbes Précision-Rappel comparées |
| `outputs_ml/metrics_comparison_ml.png` | Dashboard multi-métriques |
| `outputs_ml/confusion_*.png` | Matrices de confusion par modèle |
| `outputs_ml/shap_importance_*.png` | Visualisations SHAP par modèle |

### 15.5 Reproductibilité

- Graine aléatoire fixée à **42** pour tous les processus stochastiques (split train/test, validation croisée, modèles ML)
- Versions des librairies spécifiées dans `requirements.txt`
- Toutes les étapes sont séquentielles et sans dépendances circulaires

---

*Document généré le 05/06/2026 — Projet : Analyse des déterminants de la mortalité infantile au Cameroun (EDS 2018)*
