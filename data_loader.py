import pandas as pd
import streamlit as st
from typing import Optional, Dict, List


class DataLoader:
    """Classe pour charger et valider les données d'entrée"""
    
    def __init__(self):
        self.crawl_data = None
        self.gsc_data = None
        self.inlinks_data = None
        self.html_content = None
    
    @staticmethod
    def find_column(df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Trouve une colonne en testant plusieurs noms possibles (insensible à la casse)"""
        df_cols_lower = {col.lower().strip(): col for col in df.columns}
        
        for name in possible_names:
            name_lower = name.lower().strip()
            if name_lower in df_cols_lower:
                return df_cols_lower[name_lower]
        return None
    
    @staticmethod
    def normalize_column_names(df: pd.DataFrame, column_mapping: Dict[str, List[str]]) -> pd.DataFrame:
        """Normalise les noms de colonnes selon un mapping de noms possibles"""
        df = df.copy()
        
        for standard_name, possible_names in column_mapping.items():
            found_col = DataLoader.find_column(df, possible_names)
            if found_col and found_col != standard_name:
                df.rename(columns={found_col: standard_name}, inplace=True)
        
        return df
    
    def load_screaming_frog(self, file) -> Optional[pd.DataFrame]:
        """Charge le fichier de crawl Screaming Frog"""
        try:
            # Chargement du fichier
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8-sig')
            else:
                df = pd.read_excel(file)
            
            # Nettoyage des noms de colonnes
            df.columns = df.columns.str.strip()
            
            st.info(f"📋 Colonnes détectées dans le fichier: {', '.join(df.columns[:10])}...")
            
            # Mapping des colonnes possibles
            column_mapping = {
                'Address': ['address', 'url', 'page url', 'page', 'source'],
                'Link Score': ['link score', 'linkscore', 'score', 'link equity'],
                'Unique Inlinks': ['unique inlinks', 'inlinks', 'unique inlink', 'inbound links', 'internal links in'],
                'Crawl Depth': ['crawl depth', 'depth', 'distance', 'level'],
                'Status Code': ['status code', 'status', 'http status code', 'response code'],
                'Indexability': ['indexability', 'indexable', 'index status', 'indexability status']
            }
            
            # Normaliser les colonnes
            df = self.normalize_column_names(df, column_mapping)
            
            # Vérifier les colonnes manquantes
            missing = []
            for col in ['Address', 'Link Score', 'Unique Inlinks', 'Crawl Depth']:
                if col not in df.columns:
                    missing.append(col)
            
            if 'Address' not in df.columns:
                st.error("❌ Impossible de trouver la colonne URL/Address. Colonnes disponibles: " + ", ".join(df.columns))
                return None
            
            if missing:
                st.warning(f"⚠️ Colonnes non trouvées: {', '.join(missing)}. Des valeurs par défaut seront utilisées.")
            
            # Créer les colonnes manquantes avec des valeurs par défaut
            if 'Link Score' not in df.columns:
                df['Link Score'] = 0
                st.info("ℹ️ Colonne 'Link Score' absente, valeurs = 0")
            
            if 'Unique Inlinks' not in df.columns:
                df['Unique Inlinks'] = 0
                st.info("ℹ️ Colonne 'Unique Inlinks' absente, valeurs = 0")
            
            if 'Crawl Depth' not in df.columns:
                df['Crawl Depth'] = 1
                st.info("ℹ️ Colonne 'Crawl Depth' absente, valeurs = 1")
            
            # Nettoyage des données
            df['Link Score'] = pd.to_numeric(df['Link Score'], errors='coerce').fillna(0)
            df['Unique Inlinks'] = pd.to_numeric(df['Unique Inlinks'], errors='coerce').fillna(0)
            df['Crawl Depth'] = pd.to_numeric(df['Crawl Depth'], errors='coerce').fillna(1)
            
            # Filtrer les pages indexables avec status 200 (si disponible)
            initial_count = len(df)
            
            if 'Status Code' in df.columns:
                df['Status Code'] = pd.to_numeric(df['Status Code'], errors='coerce')
                df = df[df['Status Code'] == 200]
                st.info(f"✅ Filtrage Status Code 200: {len(df)}/{initial_count} pages conservées")
            
            if 'Indexability' in df.columns:
                df = df[df['Indexability'].str.lower().str.contains('indexable', na=False)]
                st.info(f"✅ Filtrage pages indexables: {len(df)} pages conservées")
            
            # Supprimer les doublons d'URL
            df = df.drop_duplicates(subset=['Address'], keep='first')
            
            self.crawl_data = df
            st.success(f"✅ {len(df)} pages chargées depuis Screaming Frog")
            
            return df
            
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement du fichier SF: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None
    
    def load_gsc_data(self, file) -> Optional[pd.DataFrame]:
        """Charge les données Google Search Console"""
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8-sig')
            else:
                df = pd.read_excel(file)
            
            df.columns = df.columns.str.strip()
            
            st.info(f"📋 Colonnes GSC détectées: {', '.join(df.columns)}")
            
            # Mapping des colonnes GSC
            column_mapping = {
                'Page': ['page', 'url', 'landing page', 'top pages', 'page url'],
                'Clicks': ['clicks', 'click', 'clics'],
                'Impressions': ['impressions', 'impression', 'impress'],
                'CTR': ['ctr', 'click-through rate', 'taux de clic'],
                'Position': ['position', 'avg position', 'average position', 'pos']
            }
            
            df = self.normalize_column_names(df, column_mapping)
            
            # Vérifier la colonne URL
            if 'Page' not in df.columns:
                st.error("❌ Impossible de trouver la colonne URL/Page dans GSC. Colonnes: " + ", ".join(df.columns))
                return None
            
            # Créer les colonnes manquantes
            for col in ['Clicks', 'Impressions', 'CTR', 'Position']:
                if col not in df.columns:
                    if col == 'Position':
                        df[col] = 100
                    else:
                        df[col] = 0
                    st.warning(f"⚠️ Colonne '{col}' absente dans GSC, valeurs par défaut utilisées")
            
            # Nettoyage
            df['Clicks'] = pd.to_numeric(df['Clicks'], errors='coerce').fillna(0)
            df['Impressions'] = pd.to_numeric(df['Impressions'], errors='coerce').fillna(0)
            df['Position'] = pd.to_numeric(df['Position'], errors='coerce').fillna(100)
            df['CTR'] = pd.to_numeric(df['CTR'], errors='coerce').fillna(0)
            
            # Supprimer les doublons
            df = df.drop_duplicates(subset=['Page'], keep='first')
            
            self.gsc_data = df
            st.success(f"✅ {len(df)} pages GSC chargées")
            return df
            
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement GSC: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None
    
    def load_inlinks(self, file) -> Optional[pd.DataFrame]:
        """Charge le fichier des liens entrants"""
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file, encoding='utf-8-sig')
            else:
                df = pd.read_excel(file)
            
            df.columns = df.columns.str.strip()
            
            st.info(f"📋 Colonnes Inlinks détectées: {', '.join(df.columns[:10])}...")
            
            # Mapping des colonnes de liens
            column_mapping = {
                'Source': ['source', 'source url', 'from', 'source address', 'link from'],
                'Destination': ['destination', 'target', 'destination url', 'to', 'destination address', 'link to'],
                'Anchor': ['anchor', 'anchor text', 'link text', 'ancre']
            }
            
            df = self.normalize_column_names(df, column_mapping)
            
            # Vérifier les colonnes essentielles
            if 'Source' not in df.columns or 'Destination' not in df.columns:
                st.error(f"❌ Colonnes Source/Destination manquantes. Colonnes: {', '.join(df.columns)}")
                return None
            
            if 'Anchor' not in df.columns:
                df['Anchor'] = ''
                st.warning("⚠️ Colonne 'Anchor' absente, valeurs vides utilisées")
            
            # Supprimer les doublons
            df = df.drop_duplicates(subset=['Source', 'Destination'], keep='first')
            
            self.inlinks_data = df
            st.success(f"✅ {len(df)} liens internes chargés")
            return df
            
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement des liens: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
            return None
    
    def load_html_content(self, file) -> Optional[Dict]:
        """Charge le fichier HTML (optionnel pour visualisation)"""
        try:
            content = file.read().decode('utf-8')
            self.html_content = {'filename': file.name, 'content': content}
            st.success(f"✅ Contenu HTML chargé: {file.name}")
            return self.html_content
            
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement HTML: {str(e)}")
            return None
    
    def merge_data(self) -> Optional[pd.DataFrame]:
        """Fusionne toutes les données en un DataFrame unique"""
        if self.crawl_data is None:
            st.error("❌ Données Screaming Frog manquantes")
            return None
        
        merged = self.crawl_data.copy()
        
        # Fusion avec GSC
        if self.gsc_data is not None:
            # Normaliser les URLs pour améliorer le matching
            merged['Address_clean'] = merged['Address'].str.lower().str.strip().str.rstrip('/')
            gsc_clean = self.gsc_data.copy()
            gsc_clean['Page_clean'] = gsc_clean['Page'].str.lower().str.strip().str.rstrip('/')
            
            merged = merged.merge(
                gsc_clean,
                left_on='Address_clean',
                right_on='Page_clean',
                how='left'
            )
            merged.drop(columns=['Page', 'Address_clean', 'Page_clean'], inplace=True, errors='ignore')
            
            # Remplir les valeurs manquantes
            merged['Clicks'] = merged['Clicks'].fillna(0)
            merged['Impressions'] = merged['Impressions'].fillna(0)
            merged['Position'] = merged['Position'].fillna(100)
            merged['CTR'] = merged['CTR'].fillna(0)
            
            matched = merged['Clicks'].notna().sum()
            st.info(f"🔗 {matched} pages matchées avec les données GSC")
        else:
            merged['Clicks'] = 0
            merged['Impressions'] = 0
            merged['Position'] = 100
            merged['CTR'] = 0
        
        st.success(f"✅ Données fusionnées: {len(merged)} pages au total")
        return merged
