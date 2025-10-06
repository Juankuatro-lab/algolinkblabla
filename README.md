# 🔗 ALGOLINK
Outil Python pour analyser et optimiser le maillage interne de votre site web basé sur les données Screaming Frog et Google Search Console.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 🎯 Fonctionnalités

- **Analyse du Link Score** : Identification des pages avec un faible Link Score mais à fort potentiel
- **Score de Priorité** : Calcul intelligent basé sur GSC (impressions, position) + métriques de crawl
- **Recommandations de Liens** : Suggestions automatiques de liens internes pertinents
- **Visualisations** : Graphes interactifs du maillage et des performances
- **Export CSV** : Téléchargement des recommandations pour implémentation

## 📋 Prérequis

- Python 3.8 ou supérieur
- Fichiers d'export Screaming Frog (obligatoire)
- Fichiers Google Search Console (optionnel mais recommandé)

## 🚀 Installation

1. Clonez le repository :
```bash
git clone https://github.com/votre-username/seo-internal-linking-optimizer.git
cd seo-internal-linking-optimizer
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Lancez l'application :
```bash
streamlit run app.py
```

L'interface s'ouvrira automatiquement dans votre navigateur à `http://localhost:8501`

## 📁 Structure du Projet

```
seo-internal-linking-optimizer/
│
├── app.py                 # Application Streamlit principale
├── config.py              # Configuration et paramètres
├── data_loader.py         # Chargement et validation des données
├── analyzer.py            # Algorithmes d'analyse SEO
├── visualizer.py          # Création des visualisations
├── requirements.txt       # Dépendances Python
└── README.md             # Documentation
```

## 📊 Préparation des Données

### 1. Export Screaming Frog (Obligatoire)

Effectuez un crawl complet de votre site avec Screaming Frog, puis exportez :

**Colonnes requises :**
- `Address` : URL de la page
- `Link Score` : Score de lien calculé par SF
- `Unique Inlinks` : Nombre de liens entrants uniques
- `Crawl Depth` : Profondeur depuis la homepage
- `Status Code` : Code HTTP (200 recommandé)
- `Indexability` : Statut d'indexation

**Export** : Bulk Export > All > CSV ou Excel

### 2. Export Google Search Console (Optionnel)

Exportez vos données de performance GSC (derniers 3-6 mois) :

**Colonnes requises :**
- `Page` : URL de la page
- `Clicks` : Nombre de clics
- `Impressions` : Nombre d'impressions
- `CTR` : Taux de clic
- `Position` : Position moyenne

**Export** : Performance > Pages > Export

### 3. Export Liens Internes (Optionnel)

Dans Screaming Frog, exportez les liens internes :

**Colonnes requises :**
- `Source` : URL source du lien
- `Destination` : URL destination
- `Anchor` : Texte d'ancre

**Export** : Bulk Export > All Inlinks

## 🎮 Utilisation

### 1. Charger les Données

1. Cliquez sur le bouton de chargement dans la barre latérale
2. Uploadez vos fichiers (SF obligatoire, GSC + Inlinks recommandés)
3. Cliquez sur **"🚀 Charger et Analyser"**

### 2. Explorer les Résultats

L'outil propose 4 onglets :

#### 📊 Vue d'Ensemble
- Statistiques globales du site
- Distributions des métriques
- Performances GSC

#### 🎯 Pages Prioritaires
- Top pages à booster (fort potentiel + faible Link Score)
- Filtrage par impressions, position
- Export CSV des pages prioritaires

#### 🔗 Opportunités de Liens
- Recommandations de liens source → cible
- Score d'opportunité calculé par l'algorithme
- Filtrage par similarité et Link Score
- Détails de chaque recommandation
- Export CSV pour implémentation

#### 📈 Visualisations
- Graphe réseau du maillage recommandé
- Visualisations interactives Plotly

### 3. Exporter et Implémenter

1. Filtrez les recommandations selon vos critères
2. Téléchargez le CSV des opportunités
3. Implémentez les liens dans vos contenus
4. Re-crawlez après quelques semaines pour mesurer l'impact

## ⚙️ Configuration de l'Algorithme

Modifiez `config.py` pour ajuster les pondérations :

### Score de Priorité des Pages

```python
PRIORITY_WEIGHTS = {
    'impressions': 0.3,    # Potentiel de trafic GSC
    'position': 0.2,       # Proximité 1ère page
    'link_score': 0.3,     # Faiblesse du Link Score
    'depth': 0.2           # Profondeur de crawl
}
```

### Score des Opportunités de Liens

```python
LINK_OPPORTUNITY_WEIGHTS = {
    'source_strength': 0.4,        # Puissance de la source
    'thematic_similarity': 0.4,    # Pertinence thématique
    'outlinks_penalty': 0.1,       # Pénalité si trop de liens sortants
    'target_need': 0.1             # Besoin de la cible
}
```

### Autres Paramètres

```python
MIN_SIMILARITY_THRESHOLD = 0.1     # Similarité min pour un lien
MAX_OUTLINKS_WARNING = 100         # Seuil alerte liens sortants
TOP_N_PAGES_TO_BOOST = 50         # Nombre de pages analysées
TOP_K_SUGGESTIONS_PER_PAGE = 10   # Suggestions par page
```

## 🧮 Fonctionnement de l'Algorithme

### 1. Calcul du Score de Priorité

Pour chaque page, l'outil calcule un score combinant :
- **Impressions GSC** : Pages avec du potentiel de trafic
- **Position moyenne** : Pages proches de la 1ère page (positions 11-30)
- **Link Score inversé** : Pages faibles à renforcer
- **Profondeur** : Pages trop profondes dans l'arborescence

### 2. Analyse de Similarité Thématique

Utilisation de **TF-IDF + Cosine Similarity** sur les URLs pour déterminer la pertinence des liens potentiels.

### 3. Calcul du Score d'Opportunité

Pour chaque paire (Source → Cible) :
- **Force de la source** : Link Score élevé = plus de jus transmis
- **Similarité** : Pertinence thématique entre les pages
- **Pénalité outlinks** : Éviter les pages avec trop de liens sortants
- **Besoin de la cible** : Pages avec peu de liens entrants

## 📈 Interprétation des Résultats

### Pages Prioritaires

- **Priority_Score > 0.7** : Très haute priorité
- **Priority_Score 0.4-0.7** : Priorité moyenne
- **Has_Potential = True** : Page avec fort potentiel inexploité

### Opportunités de Liens

- **Opportunity_Score > 0.6** : Lien très recommandé
- **Similarity > 0.3** : Forte pertinence thématique
- **Source_LinkScore > 50** : Source puissante

## 🛠️ Améliorations Futures

- [ ] Analyse sémantique avancée (embeddings, BERT)
- [ ] Simulation d'impact du PageRank
- [ ] Suggestions de textes d'ancre optimisés
- [ ] Détection automatique de clusters thématiques
- [ ] Intégration API Screaming Frog
- [ ] Support multi-langues
- [ ] Analyse de la cannibalisation SEO

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
1. Fork le projet
2. Créer une branche (`git checkout -b feature/amelioration`)
3. Commit vos changements (`git commit -m 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 👨‍💻 Auteur

Créé pour optimiser le maillage interne et booster les performances SEO.

## 🙏 Remerciements

- [Screaming Frog](https://www.screamingfrog.co.uk/) pour l'outil de crawl
- [Streamlit](https://streamlit.io/) pour le framework d'interface
- La communauté SEO pour les bonnes pratiques

---

**⭐ Si cet outil vous est utile, n'hésitez pas à mettre une étoile sur GitHub !**
