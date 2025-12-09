import streamlit as st
import pandas as pd
import os
import ast # Pour nettoyer la colonne genres

# --- 1. Configuration et CSS ---
st.set_page_config(
    page_title="CREUSÉMA - Cinéma",
    page_icon="🎬",
    layout="wide"
)

# CSS Personnalisé
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: white;
    }
    div.stButton > button:first-child {
        background-color: #FF7F00;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #262730;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. Chargement des Données ---

@st.cache_data
def charger_donnees():
    try:
        # Charge le CSV
        df = pd.read_csv("/Users/thiagorocha/WCS/ProjetLITE/films_final_extended.csv")
        
        # Filtre pour ne garder que les films qui ont une image (lien_poster non vide)
        df = df.dropna(subset=['lien_poster'])
        
        # Optionnel : On peut filtrer pour ne garder que les films récents ou populaires si on veut
        # df = df[df['annee_sortie'] > 2000] 
        
        return df
    except FileNotFoundError:
        st.error("Le fichier 'films_final_extended.csv' est introuvable. Veuillez le placer dans le même dossier.")
        return pd.DataFrame() # Retourne un dataframe vide en cas d'erreur

# Chargement initial
df_films = charger_donnees()

# --- 3. Fonctions Utilitaires ---

def nettoyer_genres(genre_str):
    """Convertit la chaine "['Comedy', 'Drama']" en "Comedy / Drama" """
    try:
        # Evalue la chaine comme une liste python
        liste = ast.literal_eval(genre_str)
        if isinstance(liste, list):
            return " / ".join(liste[:2]) # On garde max 2 genres pour l'affichage
        return genre_str
    except:
        return str(genre_str).replace("['", "").replace("']", "").replace("', '", " / ")

def afficher_carte_film(titre, image_url, sous_titre=None, horaire=None):
    """Affiche une carte de film standardisée avec URL"""
    
    # Affiche l'image depuis l'URL du CSV
    st.image(image_url, use_column_width=True)
    
    st.markdown(f"**{titre}**")
    if sous_titre:
        st.caption(sous_titre)
    if horaire:
        st.write(f"🕒 Séance : **{horaire}**")

# --- 4. Barre Latérale ---

with st.sidebar:
    st.title("CREUSÉMA")
    st.header("Navigation")
    page = st.radio(
        "Aller vers",
        ["Accueil", "Presentation", "Recommandations", "Infos Pratiques"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.info(f"📚 {len(df_films)} films disponibles dans la base !")

# --- 5. Contenu des Pages ---

if page == "Accueil":
    st.title("Bienvenue dans votre cinéma Creuséma")
    st.subheader("Actuellement en salle")
    
    if not df_films.empty:
        # Sélection aléatoire de 4 films pour l'affiche
        selection_accueil = df_films.sample(n=4)
        
        # Horaires fictifs pour l'exemple
        horaires = ["18h00", "20h30", "21h00", "22h15"]
        
        cols = st.columns(4)
        for i, (index, row) in enumerate(selection_accueil.iterrows()):
            with cols[i]:
                genres = nettoyer_genres(row['genres'])
                afficher_carte_film(
                    titre=row['titre'],
                    image_url=row['lien_poster'],
                    sous_titre=genres,
                    horaire=horaires[i]
                )
    else:
        st.warning("Aucune donnée de film chargée.")

elif page == "Recommandations":
    st.title("Je ne sais pas quoi regarder...")
    st.subheader("Quel film avez-vous aimé récemment ?")

    col_search, col_btn = st.columns([3, 1])
    with col_search:
        film_aime = st.text_input("Recherche", placeholder="Ex : Titanic", label_visibility="collapsed")
    with col_btn:
        if st.button("Trouver mon prochain film", type="primary", use_container_width=True):
            st.success(f"Recherche basée sur '{film_aime}'...")

    st.markdown("---")
    st.header("Voici 3 pépites sélectionnées pour vous :")

    if not df_films.empty:
        # Sélection aléatoire de 3 films pour les recommandations
        # (Dans un vrai système, on utiliserait un algorithme de recommandation ici)
        selection_reco = df_films.sample(n=3)
        
        cols = st.columns(3)
        for i, (index, row) in enumerate(selection_reco.iterrows()):
            with cols[i]:
                genres = nettoyer_genres(row['genres'])
                note = f"⭐ {row['note']}/10"
                afficher_carte_film(
                    titre=row['titre'],
                    image_url=row['lien_poster'],
                    sous_titre=f"{genres} • {note}"
                )
elif page == "Presentation":
    st.title("Video presentation")
    st.subheader("Quel film avez-vous aimé récemment ?")

    st.video(data, format="video/mp4", loop=False, autoplay=False, muted=False, width="stretch")


elif page == "Infos Pratiques":
    st.title("Nous trouver & Tarifs")

    col_carte, col_infos = st.columns([2, 1], gap="large")

    with col_carte:
        # Carte par défaut si pas d'image locale
        st.map(data={"lat": [46.237], "lon": [1.486]}, zoom=14)
        st.caption("Rue du Cinéma, 23300 La Souterraine")

    with col_infos:
        infos = [
            {"icon": "📍", "titre": "ADRESSE", "desc": "Rue du Cinéma,\n23300 La Souterraine"},
            {"icon": "🎟️", "titre": "TARIFS", "desc": "Plein : **8,00 €**\nRéduit : **6,00 €**"},
            {"icon": "📞", "titre": "CONTACT", "desc": "05 55 55 44 77"}
        ]
        
        for item in infos:
            with st.container(border=True):
                st.markdown(f"### {item['icon']} {item['titre']}")
                st.markdown(item['desc'])
