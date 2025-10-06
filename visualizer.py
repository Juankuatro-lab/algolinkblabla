import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import pandas as pd
from typing import Optional


class SEOVisualizer:
    """Classe pour créer les visualisations"""
    
    @staticmethod
    def plot_priority_distribution(df: pd.DataFrame) -> go.Figure:
        """Graphique de distribution des scores de priorité"""
        fig = px.histogram(
            df,
            x='Priority_Score',
            nbins=50,
            title='Distribution des Scores de Priorité',
            labels={'Priority_Score': 'Score de Priorité', 'count': 'Nombre de pages'},
            color_discrete_sequence=['#1f77b4']
        )
        fig.update_layout(showlegend=False)
        return fig
    
    @staticmethod
    def plot_link_score_vs_depth(df: pd.DataFrame) -> go.Figure:
        """Scatter plot Link Score vs Profondeur"""
        # Nettoyer les données pour la visualisation
        df_clean = df.copy()
        df_clean['Impressions'] = pd.to_numeric(df_clean['Impressions'], errors='coerce').fillna(0)
        df_clean['Impressions'] = df_clean['Impressions'].clip(lower=0)
        
        # Ajouter une petite valeur pour éviter les points de taille 0
        df_clean['Impressions_viz'] = df_clean['Impressions'] + 1
        
        fig = px.scatter(
            df_clean,
            x='Crawl Depth',
            y='Link Score',
            size='Impressions_viz',
            color='Priority_Score',
            hover_data=['Address', 'Clicks', 'Impressions'],
            title='Link Score vs Profondeur de Crawl',
            labels={
                'Crawl Depth': 'Profondeur',
                'Link Score': 'Link Score',
                'Priority_Score': 'Score Priorité',
                'Impressions_viz': 'Impressions'
            },
            color_continuous_scale='Viridis'
        )
        return fig
    
    @staticmethod
    def plot_gsc_performance(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
        """Graphique des performances GSC (top pages)"""
        # Nettoyer les données
        df_clean = df.copy()
        df_clean['Impressions'] = pd.to_numeric(df_clean['Impressions'], errors='coerce').fillna(0)
        df_clean['Clicks'] = pd.to_numeric(df_clean['Clicks'], errors='coerce').fillna(0)
        
        # Filtrer les pages avec des impressions
        df_clean = df_clean[df_clean['Impressions'] > 0]
        
        if len(df_clean) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="Aucune donnée GSC disponible",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        top_pages = df_clean.nlargest(top_n, 'Impressions')
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Impressions',
            x=top_pages['Address'].str[-30:],  # Tronquer l'URL
            y=top_pages['Impressions'],
            yaxis='y',
            offsetgroup=1
        ))
        
        fig.add_trace(go.Bar(
            name='Clics',
            x=top_pages['Address'].str[-30:],
            y=top_pages['Clicks'],
            yaxis='y',
            offsetgroup=2
        ))
        
        fig.update_layout(
            title=f'Top {len(top_pages)} Pages - Performances GSC',
            xaxis={'title': 'URL (fin)', 'tickangle': -45},
            yaxis={'title': 'Nombre'},
            barmode='group',
            height=500
        )
        
        return fig
    
    @staticmethod
    def plot_network_graph(opportunities: pd.DataFrame, max_links: int = 50) -> go.Figure:
        """Visualisation du graphe de liens recommandés"""
        
        if len(opportunities) == 0:
            fig = go.Figure()
            fig.add_annotation(
                text="Aucune opportunité de lien trouvée",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
        
        # Limiter le nombre de liens pour la lisibilité
        top_opportunities = opportunities.head(max_links)
        
        # Créer le graphe
        G = nx.DiGraph()
        
        for _, row in top_opportunities.iterrows():
            G.add_edge(
                row['Source'],
                row['Target'],
                weight=row['Opportunity_Score']
            )
        
        # Position des noeuds
        try:
            pos = nx.spring_layout(G, k=2, iterations=50)
        except:
            pos = nx.random_layout(G)
        
        # Extraire les coordonnées des arêtes
        edge_x = []
        edge_y = []
        
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        )
        
        # Extraire les coordonnées des noeuds
        node_x = []
        node_y = []
        node_text = []
        node_hover = []
        node_size = []
        node_color = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # Tronquer l'URL pour l'affichage
            display_url = node.split('/')[-1][:30] if '/' in node else node[:30]
            node_text.append(display_url)
            
            # Info au survol
            degree = G.degree(node)
            node_hover.append(f"{node}<br>Connexions: {degree}")
            
            # Taille et couleur basées sur le degré
            node_size.append(15 + degree * 3)
            node_color.append(float(degree))
        
        # Créer le trace des noeuds SANS colorbar problématique
        node_trace = go.Scatter(
            x=node_x, 
            y=node_y,
            mode='markers+text',
            hovertext=node_hover,
            hoverinfo='text',
            text=node_text,
            textposition="top center",
            textfont=dict(size=8),
            showlegend=False,
            marker=dict(
                size=node_size,
                color=node_color,
                colorscale='Viridis',
                line=dict(width=1, color='white')
            )
        )
        
        # Créer la figure
        fig = go.Figure(data=[edge_trace, node_trace])
        
        fig.update_layout(
            title=dict(
                text=f'Graphe des Opportunités de Liens (Top {len(top_opportunities)})',
                font=dict(size=16)
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(
                showgrid=False, 
                zeroline=False, 
                showticklabels=False
            ),
            yaxis=dict(
                showgrid=False, 
                zeroline=False, 
                showticklabels=False
            ),
            height=600,
            plot_bgcolor='white'
        )
        
        return fig
    
    @staticmethod
    def display_stats_cards(stats: dict) -> str:
        """Génère le HTML pour afficher les statistiques sous forme de cartes"""
        html = """
        <style>
        .stats-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            font-size: 14px;
            opacity: 0.9;
        }
        </style>
        <div class="stats-container">
        """
        
        cards_data = [
            ("Pages analysées", stats.get('total_pages', 0), "📄"),
            ("Link Score moyen", f"{stats.get('avg_link_score', 0):.1f}", "⭐"),
            ("Profondeur moyenne", f"{stats.get('avg_depth', 0):.1f}", "🎯"),
            ("Liens entrants moyens", f"{stats.get('avg_inlinks', 0):.1f}", "🔗"),
            ("Total Impressions", f"{stats.get('total_impressions', 0):,.0f}", "👁️"),
            ("Total Clics", f"{stats.get('total_clicks', 0):,.0f}", "🖱️"),
        ]
        
        for label, value, emoji in cards_data:
            html += f"""
            <div class="stat-card">
                <div class="stat-label">{emoji} {label}</div>
                <div class="stat-value">{value}</div>
            </div>
            """
        
        html += "</div>"
        return html
