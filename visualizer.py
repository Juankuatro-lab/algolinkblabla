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
        fig = px.scatter(
            df,
            x='Crawl Depth',
            y='Link Score',
            size='Impressions',
            color='Priority_Score',
            hover_data=['Address', 'Clicks'],
            title='Link Score vs Profondeur de Crawl',
            labels={
                'Crawl Depth': 'Profondeur',
                'Link Score': 'Link Score',
                'Priority_Score': 'Score Priorité'
            },
            color_continuous_scale='Viridis'
        )
        return fig
    
    @staticmethod
    def plot_gsc_performance(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
        """Graphique des performances GSC (top pages)"""
        top_pages = df.nlargest(top_n, 'Impressions')
        
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
            title=f'Top {top_n} Pages - Performances GSC',
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
            return go.Figure().add_annotation(
                text="Aucune opportunité de lien trouvée",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
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
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Extraire les coordonnées
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
            mode='lines'
        )
        
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            # Tronquer l'URL pour l'affichage
            display_url = node.split('/')[-1][:30] if '/' in node else node[:30]
            node_text.append(display_url)
            # Taille basée sur le degré
            node_size.append(10 + G.degree(node) * 5)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="top center",
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=node_size,
                color=[G.degree(node) for node in G.nodes()],
                colorbar=dict(
                    thickness=15,
                    title='Connexions',
                    xanchor='left',
                    titleside='right'
                ),
                line_width=2
            )
        )
        
        fig = go.Figure(data=[edge_trace, node_trace],
                       layout=go.Layout(
                           title=f'Graphe des Opportunités de Liens (Top {max_links})',
                           titlefont_size=16,
                           showlegend=False,
                           hovermode='closest',
                           margin=dict(b=0, l=0, r=0, t=40),
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           height=600
                       ))
        
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
