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
        background-color:rgb(18, 4, 38);
        color: white;
    }
    div.stButton > button:first-child {
        background-color:rgb(150, 33, 218);
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
video = "/Users/thiagorocha/WCS/ProjetLITE/videos/Video creusema.mp4"
# --- 2. Chargement des Données ---

@st.cache_data
def charger_donnees():
    try:
        # Charge le CSV
        df = pd.read_csv("https://raw.githubusercontent.com/Rochathio/creusema/refs/heads/main/films_final_extended.csv")
        
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
#-----#
import requests
import streamlit as st

# --- Configuration TMDB ---
#-------- API pour le fiml #
API_KEY = "25d64f0557c373d5bec7a1242553ff40" 
BASE_API_URL = "https://api.themoviedb.org/3/movie/now_playing"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500" # Taille d'image courante

# --- Fonction de récupération des données ---

def fetch_now_playing_movies():
    """Récupère la liste des films actuellement en salle depuis TMDB."""
    params = {
        'api_key': API_KEY,
        'language': 'fr-FR' # Demande des titres et résumés en français
    }
    
    if API_KEY == "VOTRE_CLE_API_TMDB":
        st.warning("Veuillez remplacer 'VOTRE_CLE_API_TMDB' par votre clé API réelle.")
        return []

    try:
        response = requests.get(BASE_API_URL, params=params)
        response.raise_for_status() 
        data = response.json()
        return data.get('results', []) 
    
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à l'API TMDB : {e}")
        return []

# --- Fonctions personnalisées (À AJUSTER SI ELLES SONT DÉFINIES AILLEURS) ---
# NOTE: J'ai inclus une version simple de vos fonctions pour l'exemple.
def afficher_carte_film(titre, image_url, sous_titre, horaire):
    """Affiche une carte de film simplifiée (à remplacer par votre propre fonction)."""
    if image_url:
        st.image(image_url, caption=titre)
    else:
        st.write(f"**{titre}**")
    st.caption(sous_titre)
    st.info(f"Séance : {horaire}")

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
    col1, col2 = st.columns([1, 1])
    with col1:
        st.title("CREUSÉMA")
    st.header("Navigation")
    with col2:
        st.image("/Users/thiagorocha/WCS/ProjetLITE/images/logo_creusema.png", width=50) #LOGO cinema
    page = st.radio(
        "Aller vers",
        ["Accueil", "Presentation", "Recommandations", "Infos Pratiques"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.markdown("© 2025 Creuséma Cinéma - 2TDM")

# --- 5. Contenu des Pages ---

# Supposons que 'page' est la variable qui contient la page sélectionnée ("Accueil", "Recherche", etc.)

if page == "Accueil":
    st.title("Bienvenue dans votre cinéma Creuséma")
    st.subheader("Actuellement en salle")
    
    # 1. Récupérer les films de l'API TMDB
    movies = fetch_now_playing_movies()
    
    if movies:
        # 2. Sélectionner les 4 premiers films de la liste (pour correspondre à l'affichage précédent)
        selection_accueil = movies[:4]
        
        # Horaires fictifs conservés pour l'exemple
        horaires = ["18h00", "20h30", "21h00", "22h15"]
        
        # 3. Afficher en colonnes
        cols = st.columns(4)
        
        for i, movie in enumerate(selection_accueil):
            with cols[i]:
                titre = movie.get('title')
                poster_path = movie.get('poster_path')
                
                # Construire l'URL de l'affiche
                image_url = IMAGE_BASE_URL + poster_path if poster_path else None
                
                # Utiliser la date de sortie comme sous-titre (à la place du genre)
                sous_titre = f"Sortie: {movie.get('release_date', 'N/A')}"
                horaire = horaires[i]
                
                # Appel à votre fonction d'affichage
                afficher_carte_film(
                    titre=titre,
                    image_url=image_url,
                    sous_titre=sous_titre,
                    horaire=horaire
                )
    else:
        st.info("Aucun film en cours de diffusion n'a pu être chargé.")

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
    st.header("Voici 5 pépites sélectionnées pour vous :")

    if not df_films.empty:
        # Sélection aléatoire de 5 films pour les recommandations
        # (Dans un vrai système, on utiliserait un algorithme de recommandation ici)
        selection_reco = df_films.sample(n=5)
        
        cols = st.columns(5)
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
    st.video(video, format="video/mp4", loop=False, autoplay=False, muted=False)

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
