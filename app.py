import streamlit as st
import pandas as pd
from data_loader import DataLoader
from analyzer import SEOAnalyzer
from visualizer import SEOVisualizer
from config import TOP_N_PAGES_TO_BOOST, TOP_K_SUGGESTIONS_PER_PAGE

# Configuration de la page
st.set_page_config(
    page_title="Optimiseur de Maillage Interne SEO",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    .main-header {
        font-size: 48px;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 10px;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 30px;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<p class="main-header">🔗 Optimiseur de Maillage Interne</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Analyse SEO basée sur Screaming Frog & Google Search Console</p>', unsafe_allow_html=True)

# Initialisation de la session
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.loader = DataLoader()
    st.session_state.merged_data = None
    st.session_state.opportunities = None

# Sidebar pour le chargement des fichiers
with st.sidebar:
    st.header("📁 Chargement des données")
    
    st.subheader("1️⃣ Crawl Screaming Frog *")
    sf_file = st.file_uploader(
        "Export CSV/Excel du crawl",
        type=['csv', 'xlsx'],
        key='sf_file',
        help="Fichier contenant: Address, Link Score, Unique Inlinks, Crawl Depth"
    )
    
    st.subheader("2️⃣ Google Search Console")
    gsc_file = st.file_uploader(
        "Export GSC (optionnel)",
        type=['csv', 'xlsx'],
        key='gsc_file',
        help="Données GSC: Page, Clicks, Impressions, CTR, Position"
    )
    
    st.subheader("3️⃣ Liens Entrants Internes")
    inlinks_file = st.file_uploader(
        "Export des liens internes (optionnel)",
        type=['csv', 'xlsx'],
        key='inlinks_file',
        help="Fichier contenant: Source, Destination, Anchor"
    )
    
    st.markdown("---")
    
    # Bouton de chargement
    if st.button("🚀 Charger et Analyser", type="primary", use_container_width=True):
        if sf_file is None:
            st.error("⚠️ Le fichier Screaming Frog est obligatoire")
        else:
            with st.spinner("Chargement des données..."):
                # Charger SF
                st.session_state.loader.load_screaming_frog(sf_file)
                
                # Charger GSC si fourni
                if gsc_file:
                    st.session_state.loader.load_gsc_data(gsc_file)
                
                # Charger Inlinks si fourni
                if inlinks_file:
                    st.session_state.loader.load_inlinks(inlinks_file)
                
                # Fusionner les données
                st.session_state.merged_data = st.session_state.loader.merge_data()
                
                if st.session_state.merged_data is not None:
                    st.session_state.data_loaded = True
                    st.rerun()
    
    if st.session_state.data_loaded:
        st.success("✅ Données chargées avec succès!")
        
        if st.button("🔄 Réinitialiser", use_container_width=True):
            st.session_state.data_loaded = False
            st.session_state.merged_data = None
            st.session_state.opportunities = None
            st.rerun()

# Interface principale
if not st.session_state.data_loaded:
    st.info("👈 Commencez par charger vos fichiers dans la barre latérale")
    
    # Instructions
    with st.expander("📖 Guide d'utilisation"):
        st.markdown("""
        ### Comment utiliser cet outil ?
        
        **1. Préparez vos fichiers:**
        - **Screaming Frog (obligatoire):** Export du crawl contenant au minimum Address, Link Score, Unique Inlinks, Crawl Depth
        - **Google Search Console (optionnel):** Export avec les colonnes Page, Clicks, Impressions, CTR, Position
        - **Liens internes (optionnel):** Export SF des liens avec Source, Destination, Anchor
        
        **2. Chargez les fichiers** via la barre latérale
        
        **3. Analysez les résultats:**
        - Visualisez les statistiques globales
        - Identifiez les pages à fort potentiel
        - Découvrez les opportunités de liens recommandées
        - Exportez les recommandations en CSV
        
        **4. Implémentez les liens** suggérés pour améliorer votre maillage interne
        """)
    
    with st.expander("⚙️ Configuration de l'algorithme"):
        st.markdown("""
        ### Algorithme de scoring
        
        **Score de Priorité des Pages:**
        - 30% Impressions GSC (potentiel de trafic)
        - 20% Position moyenne (pages proches de la 1ère page)
        - 30% Link Score inversé (pages faibles à booster)
        - 20% Profondeur de crawl (pages trop profondes)
        
        **Score des Opportunités de Liens:**
        - 40% Force de la page source (Link Score élevé)
        - 40% Similarité thématique (pertinence du lien)
        - 10% Pénalité liens sortants (éviter surcharge)
        - 10% Besoin de la page cible (peu de liens entrants)
        
        Vous pouvez modifier ces pondérations dans `config.py`
        """)

else:
    # Analyse des données
    analyzer = SEOAnalyzer(
        st.session_state.merged_data,
        st.session_state.loader.inlinks_data
    )
    visualizer = SEOVisualizer()
    
    # Calculer les scores de priorité une seule fois
    if 'priority_data' not in st.session_state:
        with st.spinner("Calcul des scores de priorité..."):
            st.session_state.priority_data = analyzer.calculate_priority_score()
    
    # Onglets principaux
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Vue d'ensemble",
        "🎯 Pages Prioritaires",
        "🔗 Opportunités de Liens",
        "📈 Visualisations"
    ])
    
    # TAB 1: Vue d'ensemble
    with tab1:
        st.header("📊 Statistiques Globales")
        
        stats = analyzer.get_statistics()
        st.markdown(visualizer.display_stats_cards(stats), unsafe_allow_html=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📉 Distribution des Scores de Priorité")
            fig_ls = visualizer.plot_priority_distribution(st.session_state.priority_data)
            st.plotly_chart(fig_ls, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Link Score vs Profondeur")
            fig_scatter = visualizer.plot_link_score_vs_depth(st.session_state.priority_data)
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        if st.session_state.loader.gsc_data is not None:
            st.subheader("🏆 Top Pages GSC")
            fig_gsc = visualizer.plot_gsc_performance(st.session_state.merged_data)
            st.plotly_chart(fig_gsc, use_container_width=True)
    
    # TAB 2: Pages Prioritaires
    with tab2:
        st.header("🎯 Pages à Prioriser pour le Maillage")
        
        with st.spinner("Calcul des scores de priorité..."):
            df_priority = analyzer.calculate_priority_score()
        
        st.markdown(f"""
        Les **{TOP_N_PAGES_TO_BOOST} pages** ci-dessous ont le plus fort potentiel d'amélioration.
        Elles combinent un bon potentiel GSC avec un Link Score faible.
        """)
        
        # Filtres
        col1, col2, col3 = st.columns(3)
        with col1:
            min_impressions = st.number_input("Impressions min.", 0, int(df_priority['Impressions'].max()), 0)
        with col2:
            max_position = st.number_input("Position max.", 1, 100, 100)
        with col3:
            show_potential_only = st.checkbox("Uniquement pages à fort potentiel", value=False)
        
        # Appliquer les filtres
        filtered = df_priority[
            (df_priority['Impressions'] >= min_impressions) &
            (df_priority['Position'] <= max_position)
        ]
        
        if show_potential_only:
            filtered = filtered[filtered['Has_Potential'] == True]
        
        # Affichage
        display_cols = [
            'Address', 'Priority_Score', 'Link Score', 'Unique Inlinks',
            'Crawl Depth', 'Impressions', 'Clicks', 'Position', 'Has_Potential'
        ]
        
        st.dataframe(
            filtered[display_cols].head(100),
            use_container_width=True,
            height=400
        )
        
        # Export
        csv_priority = filtered[display_cols].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Télécharger les pages prioritaires (CSV)",
            data=csv_priority,
            file_name="pages_prioritaires_seo.csv",
            mime="text/csv"
        )
    
    # TAB 3: Opportunités de Liens
    with tab3:
        st.header("🔗 Recommandations de Liens Internes")
        
        if st.session_state.opportunities is None:
            with st.spinner("Génération des opportunités de liens... Cela peut prendre quelques minutes."):
                st.session_state.opportunities = analyzer.generate_link_opportunities()
        
        opportunities = st.session_state.opportunities
        
        if len(opportunities) == 0:
            st.warning("⚠️ Aucune opportunité de lien trouvée avec les critères actuels.")
            st.info("Essayez de réduire le seuil de similarité dans config.py ou vérifiez vos données.")
        else:
            st.success(f"✅ {len(opportunities)} opportunités de liens identifiées!")
            
            st.markdown(f"""
            Chaque page cible reçoit jusqu'à **{TOP_K_SUGGESTIONS_PER_PAGE} suggestions** de liens entrants.
            Les recommandations sont triées par score d'opportunité (pertinence × impact potentiel).
            """)
            
            # Filtres
            col1, col2 = st.columns(2)
            with col1:
                min_similarity = st.slider(
                    "Similarité minimale",
                    0.0, 1.0, 0.1, 0.05,
                    help="Filtrer les liens par pertinence thématique"
                )
            with col2:
                min_source_ls = st.number_input(
                    "Link Score source min.",
                    0, 100, 0,
                    help="Filtrer par force de la page source"
                )
            
            # Appliquer les filtres
            filtered_opp = opportunities[
                (opportunities['Similarity'] >= min_similarity) &
                (opportunities['Source_LinkScore'] >= min_source_ls)
            ]
            
            st.metric("Opportunités filtrées", len(filtered_opp))
            
            # Affichage du tableau
            display_opp_cols = [
                'Source', 'Target', 'Opportunity_Score', 'Similarity',
                'Source_LinkScore', 'Target_LinkScore', 'Source_Outlinks',
                'Target_Inlinks', 'Target_Impressions', 'Target_Position'
            ]
            
            st.dataframe(
                filtered_opp[display_opp_cols],
                use_container_width=True,
                height=500
            )
            
            # Section détails pour une opportunité
            st.markdown("---")
            st.subheader("🔍 Détails d'une Opportunité")
            
            if len(filtered_opp) > 0:
                selected_idx = st.selectbox(
                    "Sélectionnez une opportunité",
                    range(len(filtered_opp)),
                    format_func=lambda x: f"#{x+1}: {filtered_opp.iloc[x]['Source'][:50]}... → {filtered_opp.iloc[x]['Target'][:50]}..."
                )
                
                selected = filtered_opp.iloc[selected_idx]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📤 Page Source**")
                    st.write(f"URL: `{selected['Source']}`")
                    st.write(f"Link Score: **{selected['Source_LinkScore']:.1f}**")
                    st.write(f"Liens sortants actuels: {selected['Source_Outlinks']}")
                
                with col2:
                    st.markdown("**📥 Page Cible**")
                    st.write(f"URL: `{selected['Target']}`")
                    st.write(f"Link Score: **{selected['Target_LinkScore']:.1f}**")
                    st.write(f"Liens entrants: {selected['Target_Inlinks']}")
                    st.write(f"Impressions GSC: {selected['Target_Impressions']:.0f}")
                    st.write(f"Position: {selected['Target_Position']:.1f}")
                
                st.markdown("**📊 Scores**")
                score_col1, score_col2, score_col3 = st.columns(3)
                score_col1.metric("Score Opportunité", f"{selected['Opportunity_Score']:.3f}")
                score_col2.metric("Similarité", f"{selected['Similarity']:.3f}")
                score_col3.metric("Priorité Cible", f"{selected['Target_Priority_Score']:.3f}")
            
            # Export
            csv_opportunities = filtered_opp.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Télécharger les recommandations (CSV)",
                data=csv_opportunities,
                file_name="opportunites_liens_seo.csv",
                mime="text/csv",
                type="primary"
            )
    
    # TAB 4: Visualisations
    with tab4:
        st.header("📈 Visualisations Avancées")
        
        if st.session_state.opportunities is not None and len(st.session_state.opportunities) > 0:
            st.subheader("🕸️ Graphe de Maillage Recommandé")
            
            max_links_graph = st.slider(
                "Nombre de liens à afficher",
                10, 100, 50, 10,
                help="Limiter pour améliorer la lisibilité"
            )
            
            with st.spinner("Génération du graphe..."):
                fig_network = visualizer.plot_network_graph(
                    st.session_state.opportunities,
                    max_links=max_links_graph
                )
                st.plotly_chart(fig_network, use_container_width=True)
            
            st.info("💡 Les nœuds représentent les pages, les flèches les liens recommandés. La taille et la couleur indiquent le nombre de connexions.")
        else:
            st.warning("⚠️ Générez d'abord les opportunités de liens dans l'onglet précédent.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🔗 Optimiseur de Maillage Interne SEO | Développé avec Streamlit</p>
    <p>Données: Screaming Frog + Google Search Console</p>
</div>
""", unsafe_allow_html=True)
