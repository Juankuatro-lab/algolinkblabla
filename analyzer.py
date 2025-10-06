import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Tuple, Dict, List
from config import (
    PRIORITY_WEIGHTS, 
    LINK_OPPORTUNITY_WEIGHTS,
    MIN_SIMILARITY_THRESHOLD,
    TOP_N_PAGES_TO_BOOST,
    TOP_K_SUGGESTIONS_PER_PAGE,
    MAX_OUTLINKS_WARNING
)


class SEOAnalyzer:
    """Analyse le maillage interne et génère des recommandations"""
    
    def __init__(self, merged_data: pd.DataFrame, inlinks_data: pd.DataFrame = None):
        self.data = merged_data
        self.inlinks = inlinks_data
        self.similarity_matrix = None
        self.url_to_idx = {}
        self.idx_to_url = {}
    
    def calculate_priority_score(self) -> pd.DataFrame:
        """Calcule le score de priorité pour chaque page"""
        df = self.data.copy()
        
        # Normalisation des métriques (0-1)
        df['norm_impressions'] = self._normalize(df['Impressions'])
        df['norm_position'] = self._normalize(1 / (df['Position'] + 1))  # Inverse car position basse = mieux
        df['norm_link_score'] = self._normalize(1 / (df['Link Score'] + 1))  # Inverse car on cherche les faibles
        df['norm_depth'] = self._normalize(1 / (df['Crawl Depth'] + 1))  # Inverse car profondeur faible = mieux
        
        # Calcul du score pondéré
        df['Priority_Score'] = (
            df['norm_impressions'] * PRIORITY_WEIGHTS['impressions'] +
            df['norm_position'] * PRIORITY_WEIGHTS['position'] +
            df['norm_link_score'] * PRIORITY_WEIGHTS['link_score'] +
            df['norm_depth'] * PRIORITY_WEIGHTS['depth']
        )
        
        # Identifier le potentiel
        df['Has_Potential'] = (
            (df['Impressions'] > df['Impressions'].median()) &
            (df['Position'] > 10) &
            (df['Link Score'] < df['Link Score'].median())
        )
        
        return df.sort_values('Priority_Score', ascending=False)
    
    def compute_similarity_matrix(self, text_column: str = 'Address') -> np.ndarray:
        """Calcule la matrice de similarité thématique basée sur les URLs"""
        urls = self.data[text_column].fillna('').astype(str).tolist()
        
        # Créer un mapping URL <-> index
        self.url_to_idx = {url: idx for idx, url in enumerate(urls)}
        self.idx_to_url = {idx: url for idx, url in enumerate(urls)}
        
        # Vectorisation TF-IDF des URLs (mots-clés dans le chemin)
        # Pour une meilleure précision, utiliser Title + H1 si disponibles
        vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            token_pattern=r'\b\w+\b',
            stop_words='english'
        )
        
        tfidf_matrix = vectorizer.fit_transform(urls)
        self.similarity_matrix = cosine_similarity(tfidf_matrix)
        
        return self.similarity_matrix
    
    def get_existing_links(self) -> set:
        """Récupère tous les liens existants (source, destination)"""
        if self.inlinks is None:
            return set()
        
        existing = set()
        for _, row in self.inlinks.iterrows():
            existing.add((row['Source'], row['Destination']))
        
        return existing
    
    def calculate_outlinks_count(self) -> Dict[str, int]:
        """Compte le nombre de liens sortants par page source"""
        if self.inlinks is None:
            return {}
        
        outlinks_count = self.inlinks.groupby('Source').size().to_dict()
        return outlinks_count
    
    def generate_link_opportunities(self, top_n: int = TOP_N_PAGES_TO_BOOST) -> pd.DataFrame:
        """Génère les opportunités de liens pour les pages prioritaires"""
        
        # Calculer les scores de priorité
        df_priority = self.calculate_priority_score()
        
        # Calculer la similarité si pas déjà fait
        if self.similarity_matrix is None:
            self.compute_similarity_matrix()
        
        # Récupérer les liens existants
        existing_links = self.get_existing_links()
        outlinks_count = self.calculate_outlinks_count()
        
        # Sélectionner les pages cibles (à booster)
        target_pages = df_priority.head(top_n)
        
        opportunities = []
        
        for _, target in target_pages.iterrows():
            target_url = target['Address']
            target_idx = self.url_to_idx.get(target_url)
            
            if target_idx is None:
                continue
            
            # Trouver les pages sources candidates (fort Link Score)
            sources = df_priority[
                (df_priority['Link Score'] > df_priority['Link Score'].median()) &
                (df_priority['Address'] != target_url)
            ].copy()
            
            for _, source in sources.iterrows():
                source_url = source['Address']
                source_idx = self.url_to_idx.get(source_url)
                
                if source_idx is None:
                    continue
                
                # Vérifier si le lien existe déjà
                if (source_url, target_url) in existing_links:
                    continue
                
                # Calculer la similarité
                similarity = self.similarity_matrix[source_idx, target_idx]
                
                if similarity < MIN_SIMILARITY_THRESHOLD:
                    continue
                
                # Calculer le score de l'opportunité
                source_strength = source['Link Score'] / 100  # Normaliser
                outlinks = outlinks_count.get(source_url, 0)
                outlinks_penalty = 1 / (1 + outlinks / MAX_OUTLINKS_WARNING)
                target_need = 1 / (1 + target['Unique Inlinks'])
                
                opportunity_score = (
                    source_strength * LINK_OPPORTUNITY_WEIGHTS['source_strength'] +
                    similarity * LINK_OPPORTUNITY_WEIGHTS['thematic_similarity'] +
                    outlinks_penalty * LINK_OPPORTUNITY_WEIGHTS['outlinks_penalty'] +
                    target_need * LINK_OPPORTUNITY_WEIGHTS['target_need']
                )
                
                opportunities.append({
                    'Source': source_url,
                    'Target': target_url,
                    'Source_LinkScore': source['Link Score'],
                    'Target_LinkScore': target['Link Score'],
                    'Target_Priority_Score': target['Priority_Score'],
                    'Similarity': similarity,
                    'Source_Outlinks': outlinks,
                    'Target_Inlinks': target['Unique Inlinks'],
                    'Target_Impressions': target['Impressions'],
                    'Target_Position': target['Position'],
                    'Opportunity_Score': opportunity_score
                })
        
        # Convertir en DataFrame et trier
        df_opportunities = pd.DataFrame(opportunities)
        
        if len(df_opportunities) == 0:
            return df_opportunities
        
        df_opportunities = df_opportunities.sort_values('Opportunity_Score', ascending=False)
        
        # Limiter le nombre de suggestions par page cible
        df_opportunities = df_opportunities.groupby('Target').head(TOP_K_SUGGESTIONS_PER_PAGE).reset_index(drop=True)
        
        return df_opportunities
    
    @staticmethod
    def _normalize(series: pd.Series) -> pd.Series:
        """Normalise une série entre 0 et 1"""
        if series.max() == series.min():
            return series * 0
        return (series - series.min()) / (series.max() - series.min())
    
    def get_statistics(self) -> Dict:
        """Calcule des statistiques globales sur le maillage"""
        stats = {
            'total_pages': len(self.data),
            'avg_link_score': self.data['Link Score'].mean(),
            'avg_depth': self.data['Crawl Depth'].mean(),
            'avg_inlinks': self.data['Unique Inlinks'].mean(),
            'pages_with_gsc': len(self.data[self.data['Impressions'] > 0]),
            'total_impressions': self.data['Impressions'].sum(),
            'total_clicks': self.data['Clicks'].sum(),
        }
        
        if self.inlinks is not None:
            stats['total_internal_links'] = len(self.inlinks)
        
        return stats
