import pandas as pd
import streamlit as st
from typing import Optional, Dict
from config import SF_REQUIRED_COLUMNS, GSC_REQUIRED_COLUMNS, INLINKS_REQUIRED_COLUMNS


class DataLoader:
    """Classe pour charger et valider les données d'entrée"""
    
    def __init__(self):
        self.crawl_data = None
        self.gsc_data = None
        self.inlinks_data = None
        self.html_content = None
    
    @staticmethod
    def validate_columns(df: pd.DataFrame, required_cols: list, file_type: str) -> bool:
        """Valide la présence des colonnes requises"""
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            st.error(f"❌ Colonnes manquantes dans {file_type}: {', '.join(missing)}")
            return False
        return True
    
    def load_screaming_frog(self, file) -> Optional[pd.DataFrame]:
        """Charge le fichier de crawl Screaming Frog"""
        try:
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            
            # Nettoyage des noms de colonnes
            df.columns = df.columns.str.strip()
            
            # Validation flexible des colonnes
            if not self.validate_columns(df, SF_REQUIRED_COLUMNS, "Screaming Frog"):
                st.warning("⚠️ Certaines colonnes sont manquantes. L'analyse sera limitée.")
            
            # Nettoyage des données
            df['Link Score'] = pd.to_numeric(df.get('Link Score', 0), errors='coerce').fillna(0)
            df['Unique Inlinks'] = pd.to_numeric(df.get('Unique Inlinks', 0), errors='coerce').fillna(0)
            df['Crawl Depth'] = pd.to_numeric(df.get('Crawl Depth', 0), errors='coerce').fillna(0)
            
            # Filtrer les pages indexables avec status 200
            if 'Status Code' in df.columns:
                df = df[df['Status Code'] == 200]
            if 'Indexability' in df.columns:
                df = df[df['Indexability'] == 'Indexable']
            
            self.crawl_data = df
            st.success(f"✅ {len(df)} pages chargées depuis Screaming Frog")
            return df
            
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement du fichier SF: {str(e)}")
            return None
    
    def load_gsc_data(self, file) -> Optional[pd.DataFrame]:
        """Charge les données Google Search Console"""
        try:
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            df.columns = df.columns.str.strip()
            
            # Normaliser le nom de la colonne URL
            url_col = next((col for col in df.columns if 'page' in col.lower() or 'url' in col.lower()), None)
            if url_col and url_col != 'Page':
                df.rename(columns={url_col: 'Page'}, inplace=True)
            
            if not self.validate_columns(df, GSC_REQUIRED_COLUMNS, "Google Search Console"):
                return None
            
            # Nettoyage
            df['Clicks'] = pd.to_numeric(df['Clicks'], errors='coerce').fillna(0)
            df['Impressions'] = pd.to_numeric(df['Impressions'], errors='coerce').fillna(0)
            df['Position'] = pd.to_numeric(df['Position'], errors='coerce').fillna(100)
            df['CTR'] = pd.to_numeric(df['CTR'], errors='coerce').fillna(0)
            
            self.gsc_data = df
            st.success(f"✅ {len(df)} pages GSC chargées")
            return df
            
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement GSC: {str(e)}")
            return None
    
    def load_inlinks(self, file) -> Optional[pd.DataFrame]:
        """Charge le fichier des liens entrants"""
        try:
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            df.columns = df.columns.str.strip()
            
            if not self.validate_columns(df, INLINKS_REQUIRED_COLUMNS, "Liens entrants"):
                return None
            
            self.inlinks_data = df
            st.success(f"✅ {len(df)} liens internes chargés")
            return df
            
        except Exception as e:
            st.error(f"❌ Erreur lors du chargement des liens: {str(e)}")
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
            merged = merged.merge(
                self.gsc_data,
                left_on='Address',
                right_on='Page',
                how='left'
            )
            merged.drop(columns=['Page'], inplace=True, errors='ignore')
            merged[['Clicks', 'Impressions', 'Position']] = merged[['Clicks', 'Impressions', 'Position']].fillna(0)
        else:
            merged['Clicks'] = 0
            merged['Impressions'] = 0
            merged['Position'] = 100
            merged['CTR'] = 0
        
        st.success(f"✅ Données fusionnées: {len(merged)} pages")
        return merged
