# Configuration globale de l'outil

# Pondérations pour le score de priorité des pages
PRIORITY_WEIGHTS = {
    'impressions': 0.3,
    'position': 0.2,
    'link_score': 0.3,
    'depth': 0.2
}

# Pondérations pour le score des opportunités de liens
LINK_OPPORTUNITY_WEIGHTS = {
    'source_strength': 0.4,
    'thematic_similarity': 0.4,
    'outlinks_penalty': 0.1,
    'target_need': 0.1
}

# Seuils et limites
MIN_SIMILARITY_THRESHOLD = 0.1  # Similarité minimale pour considérer un lien
MAX_OUTLINKS_WARNING = 100  # Seuil d'alerte pour trop de liens sortants
TOP_N_PAGES_TO_BOOST = 50  # Nombre de pages prioritaires à analyser
TOP_K_SUGGESTIONS_PER_PAGE = 10  # Nombre de suggestions par page cible

# Colonnes attendues du crawl Screaming Frog
SF_REQUIRED_COLUMNS = [
    'Address',
    'Link Score',
    'Unique Inlinks',
    'Crawl Depth',
    'Status Code',
    'Indexability'
]

# Colonnes attendues de Google Search Console
GSC_REQUIRED_COLUMNS = [
    'Page',
    'Clicks',
    'Impressions',
    'CTR',
    'Position'
]

# Colonnes attendues du fichier des liens entrants
INLINKS_REQUIRED_COLUMNS = [
    'Source',
    'Destination',
    'Anchor'
]
