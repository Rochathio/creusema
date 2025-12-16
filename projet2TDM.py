import streamlit as st
import pandas as pd
import requests
import ast 
import os
from sklearn.neighbors import NearestNeighbors

# --- 1. Configuration de la Page (Doit être la première commande Streamlit) ---
st.set_page_config(
    page_title="CREUSÉMA - Cinéma",
    page_icon="🎬",
    layout="wide"
)

# --- 2. Initialisation de l'État (Session State) ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'Accueil'
if 'film_selectionne' not in st.session_state:
    st.session_state['film_selectionne'] = None
# S'assurer que la clé du selectbox existe pour la navigation
if 'film_selectbox' not in st.session_state:
    st.session_state['film_selectbox'] = ""

# --- 3. Constantes et Configuration API ---
VIDEO_URL = "/Users/thiagorocha/WCS/ProjetLITE/videos/Video creusema.mp4"
LOGO_PATH = "/Users/thiagorocha/WCS/ProjetLITE/images/logo_creusema.png" 

API_KEY = "25d64f0557c373d5bec7a1242553ff40" 
BASE_API_URL = "https://api.themoviedb.org/3/movie/now_playing"
MOVIE_DETAILS_URL = "https://api.themoviedb.org/3/movie"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500" 

# --- 4. CSS Personnalisé ---
st.markdown("""
    <style>
    .stApp {
        background-color: rgb(18, 4, 38);
        color: white;
    }
    
    /* Boutons principaux */
    div.stButton > button {
        border-radius: 8px;
        border: none;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    div.stButton > button[data-testid="base-button-secondary"] {
        background-color: #333345;
        color: #FFFFFF;
    }
    
    div.stButton > button[data-testid="base-button-secondary"]:hover {
        background-color: #444456;
        transform: translateY(-2px);
    }
    
    div.stButton > button[data-testid="base-button-primary"] {
        background-color: #cb6ce6;
        color: white;
    }
    
    div.stButton > button[data-testid="base-button-primary"]:hover {
        background-color: #d688ed;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(203, 108, 230, 0.4);
    }
    
    /* Conteneurs */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #262730;
        border-radius: 10px;
    }
    
    /* Carte de film */
    .film-card {
        background: linear-gradient(135deg, #262730 0%, #1a1a2e 100%);
        border-radius: 12px;
        padding: 15px;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    
    .film-card:hover {
        transform: translateY(-5px);
        border-color: #cb6ce6;
        box-shadow: 0 8px 20px rgba(203, 108, 230, 0.3);
    }
    
    /* Section détails film */
    .film-details {
        background: linear-gradient(135deg, #2d2d3f 0%, #1f1f2e 100%);
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        border-left: 4px solid #cb6ce6;
        animation: slideIn 0.4s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .film-title {
        color: #cb6ce6;
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 15px;
    }
    
    .film-info {
        color: #e0e0e0;
        line-height: 1.8;
        font-size: 16px;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        background-color: #cb6ce6;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        margin: 5px;
        font-size: 14px;
        font-weight: bold;
    }
    
    /* Selectbox personnalisé */
    div[data-baseweb="select"] {
        border-radius: 8px;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #262730;
        border-color: #cb6ce6;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 10px;
    }
    
    /* Images de film */
    .film-poster {
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease;
    }
    
    .film-poster:hover {
        transform: scale(1.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- 5. Chargement des Données et Fonctions API ---

@st.cache_data
def charger_donnees_csv():
    """Charge les données depuis le CSV GitHub et effectue le nettoyage initial."""
    try:
        df = pd.read_csv("https://raw.githubusercontent.com/Rochathio/creusema/refs/heads/main/films_final_extended.csv")
        df = df.dropna(subset=['lien_poster'])
        df['genres'] = df['genres'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erreur de chargement du CSV : {e}")
        return pd.DataFrame()

def fetch_now_playing_movies():
    """Récupère la liste des films actuellement en salle depuis TMDB."""
    params = {
        'api_key': API_KEY,
        'language': 'fr-FR',
        'region': 'FR'
    }
    try:
        response = requests.get(BASE_API_URL, params=params)
        response.raise_for_status() 
        data = response.json()
        return data.get('results', []) 
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur API TMDB : {e}")
        return []

def fetch_movie_details(movie_id):
    """Récupère les détails complets d'un film via TMDB (description, vidéos)."""
    params = {
        'api_key': API_KEY,
        'language': 'fr-FR',
        'append_to_response': 'videos'
    }
    try:
        response = requests.get(f"{MOVIE_DETAILS_URL}/{movie_id}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

# Chargement initial des données
df_films = charger_donnees_csv()

# --- 6. Système de Recommandation (Machine Learning) ---

@st.cache_resource
def entrainer_modele_recommandation(df):
    """Prépare la matrice de genres et entraîne le modèle KNN."""
    if df.empty:
        return None, None

    # Nettoyage des genres pour le One-Hot Encoding
    clean_genres = df['genres'].str.replace("['", "").str.replace("']", "").str.replace("', '", ",")
    X = clean_genres.str.get_dummies(sep=',')
    
    model = NearestNeighbors(n_neighbors=6, metric='cosine', algorithm='brute')
    model.fit(X)
    
    return model, X

modele_knn, X_matrix = entrainer_modele_recommandation(df_films)

def recommander_film(nom_du_film, df, model, X):
    """Retourne les films recommandés basés sur le titre donné."""
    try:
        idx = df[df['titre'] == nom_du_film].index[0]
        distances, indices = model.kneighbors(X.iloc[idx].values.reshape(1, -1))
        # On exclut le premier résultat car c'est le film lui-même
        indices_voisins = indices[0][1:]
        return df.iloc[indices_voisins]
    except IndexError:
        return None
    except Exception as e:
        st.error(f"Erreur lors de la recommandation : {e}")
        return None

# --- 7. Fonctions Utilitaires et d'Affichage ---

def set_page(page_name):
    """Change la page active et réinitialise les états temporaires."""
    st.session_state['page'] = page_name
    st.session_state['film_selectionne'] = None
    if 'film_selectbox' in st.session_state:
         st.session_state['film_selectbox'] = "" 

def nettoyer_genres(genre_str):
    """Nettoie la chaîne de genre pour un affichage lisible."""
    try:
        liste = ast.literal_eval(genre_str)
        if isinstance(liste, list):
            return " / ".join(liste[:2]) 
        return genre_str
    except:
        return str(genre_str).replace("['", "").replace("']", "").replace("', '", " / ")

def get_synopsis_safe(row):
    """Cherche le synopsis dans plusieurs colonnes possibles pour éviter les erreurs."""
    colonnes_possibles = ['synopsis', 'overview', 'description', 'plot']
    texte_synopsis = ""
    
    for col in colonnes_possibles:
        if col in row and pd.notna(row[col]):
            valeur = str(row[col]).strip()
            if valeur and valeur.lower() != 'nan':
                texte_synopsis = valeur
                break
    return texte_synopsis

def handle_reco_click(title):
    """
    Callback function pour mettre à jour les états lorsque l'utilisateur clique
    sur un film recommandé. Modifie les états dans un contexte sûr.
    """
    st.session_state["film_selectbox"] = title
    st.session_state['film_selectionne'] = title

def afficher_carte_film(titre, image_url, sous_titre=None, horaire=None, movie_id=None, clickable=True):
    """Affiche une carte de film simple (utilisé sur l'Accueil)."""
    container = st.container()
    
    with container:
        if clickable and movie_id:
            if st.button("🎬", key=f"btn_{movie_id}", help=f"Voir les détails de {titre}", use_container_width=True):
                st.session_state['film_selectionne'] = movie_id
                st.rerun()
        
        if image_url:
            st.markdown(f'<img src="{image_url}" class="film-poster" style="width:100%; border-radius:10px;">', unsafe_allow_html=True)
        else:
            st.warning("Pas d'image")
        
        st.markdown(f"**{titre}**")
        if sous_titre:
            st.caption(sous_titre)
        if horaire:
            st.info(f"🕒 Séance : {horaire}")

def afficher_details_film(movie_id):
    """Affiche les détails complets d'un film depuis l'API TMDB (utilisé sur l'Accueil)."""
    details = fetch_movie_details(movie_id)
    
    if not details:
        st.error("Impossible de charger les détails du film.")
        return
    
    st.markdown('<div class="film-details">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        poster_path = details.get('poster_path')
        if poster_path:
            st.image(IMAGE_BASE_URL + poster_path, use_container_width=True)
    
    with col2:
        st.markdown(f'<div class="film-title">{details.get("title", "Titre inconnu")}</div>', unsafe_allow_html=True)
        
        # Badges
        genres = [g['name'] for g in details.get('genres', [])]
        for genre in genres[:3]:
            st.markdown(f'<span class="badge">{genre}</span>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Infos
        st.markdown(f'<div class="film-info">', unsafe_allow_html=True)
        st.markdown(f"**📅 Date de sortie :** {details.get('release_date', 'N/A')}")
        st.markdown(f"**⭐ Note :** {details.get('vote_average', 'N/A')}/10 ({details.get('vote_count', 0)} votes)")
        st.markdown(f"**⏱️ Durée :** {details.get('runtime', 'N/A')} minutes")
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Synopsis
        st.markdown("### 📖 Synopsis")
        st.markdown(f'<div class="film-info">{details.get("overview", "Pas de synopsis disponible.")}</div>', unsafe_allow_html=True)
    
    # Vidéo
    videos = details.get('videos', {}).get('results', [])
    trailers = [v for v in videos if v['type'] == 'Trailer' and v['site'] == 'YouTube']
    
    if trailers:
        st.markdown("---")
        st.markdown("### 🎥 Bande-annonce")
        trailer = trailers[0]
        video_url = f"https://www.youtube.com/watch?v={trailer['key']}"
        st.video(video_url)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if st.button("← Retour", type="secondary"):
        st.session_state['film_selectionne'] = None
        st.rerun()

# --- 8. Barre Latérale (Navigation) ---

with st.sidebar:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("CREUSÉMA")
    with col2:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=50)
        else:
            st.markdown("🎬")

    st.markdown("---")
    st.subheader("Navigation")

    PAGES = {
        "Accueil": "🏠 Accueil",
        "Recommandations": "💡 Recommandations",
        "Infos Pratiques": "🗺️ Infos Pratiques",
        "Presentation": "🎥 Présentation"
    }

    for page_key, page_label in PAGES.items():
        is_active = st.session_state['page'] == page_key
        button_type = "primary" if is_active else "secondary"
        
        st.button(
            page_label, 
            key=page_key, 
            type=button_type, 
            on_click=set_page, 
            args=[page_key],
            use_container_width=True
        )

    st.markdown("---")
    st.caption("© 2025 Creuséma Cinéma - 2TDM")

page = st.session_state['page'] 

# --- 9. Logique des Pages ---

if page == "Accueil":
    st.title("🎬 Bienvenue dans votre cinéma Creuséma")
    
    # Vérification: Sur l'accueil, film_selectionne doit être un ID (int/digit)
    if st.session_state['film_selectionne'] and isinstance(st.session_state['film_selectionne'], (int, str)) and str(st.session_state['film_selectionne']).isdigit():
        afficher_details_film(st.session_state['film_selectionne'])
    else:
        # Nettoyage si on vient des recommandations (où c'est un titre)
        if st.session_state['film_selectionne'] and not str(st.session_state['film_selectionne']).isdigit():
             st.session_state['film_selectionne'] = None

        st.subheader("Actuellement en salle")
        
        movies = fetch_now_playing_movies()
        
        if movies:
            selection_accueil = movies[:4] 
            horaires = ["18h00", "20h30", "21h00", "22h15"]
            
            cols = st.columns(4)
            for i, movie in enumerate(selection_accueil):
                with cols[i]:
                    titre = movie.get('title')
                    poster_path = movie.get('poster_path')
                    image_url = IMAGE_BASE_URL + poster_path if poster_path else None
                    sous_titre = f"Sortie: {movie.get('release_date', 'N/A')}"
                    movie_id = movie.get('id')
                    
                    afficher_carte_film(titre, image_url, sous_titre, horaires[i], movie_id)
        else:
            st.info("Impossible de charger les films à l'affiche.")

elif page == "Recommandations":
    st.title("💡 Je ne sais pas quoi regarder...")
    st.subheader("Quel film avez-vous aimé récemment ?")

    col_search, col_btn = st.columns([3, 1])
    
    liste_titres = sorted(df_films['titre'].unique().tolist()) if not df_films.empty else []

    with col_search:
        # La selectbox est liée à session_state via 'key'
        film_choisi = st.selectbox(
            "Recherche", 
            options=[""] + liste_titres,
            label_visibility="collapsed",
            placeholder="Choisissez un film...",
            key="film_selectbox"
        )

    with col_btn:
        rechercher = st.button("Trouver mon film", type="primary", use_container_width=True)

    st.markdown("---")

    # Mise à jour du film sélectionné si on clique sur "Rechercher"
    if rechercher and film_choisi:
        st.session_state['film_selectionne'] = film_choisi

    # Récupération du film actif
    current_movie_title = st.session_state.get('film_selectionne')
    
    # Validation
    is_valid_movie = (
        current_movie_title 
        and isinstance(current_movie_title, str) 
        and not df_films.empty 
        and current_movie_title in df_films['titre'].values
    )

    if is_valid_movie:
        # Affichage du Film Principal
        row = df_films[df_films['titre'] == current_movie_title].iloc[0]
        
        st.success(f"✨ Film sélectionné :")
        st.markdown('<div class="film-details">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.image(row['lien_poster'], use_container_width=True)
        
        with col2:
            st.markdown(f'<div class="film-title">{row["titre"]}</div>', unsafe_allow_html=True)
            genres = nettoyer_genres(row['genres'])
            for genre in genres.split(' / '):
                st.markdown(f'<span class="badge">{genre}</span>', unsafe_allow_html=True)
            st.markdown("---")
            st.markdown(f"**⭐ Note :** {row['note']}/10")
            
            # Synopsis
            synopsis = get_synopsis_safe(row)
            if synopsis:
                st.markdown("### 📖 Synopsis")
                st.markdown(f'<div class="film-info">{synopsis}</div>', unsafe_allow_html=True)
            
            # Vidéo
            if 'lien_trailer' in row and pd.notna(row['lien_trailer']) and str(row['lien_trailer']).strip():
                st.markdown("---")
                st.markdown("### 🎥 Bande-annonce")
                st.video(row['lien_trailer'])
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Calcul des Recommandations
        resultats = recommander_film(current_movie_title, df_films, modele_knn, X_matrix)
        
        if resultats is not None and not resultats.empty:
            st.header(f"🎯 Films similaires à {current_movie_title} :")
            st.caption("Cliquez sur un film pour voir ses détails et de nouvelles recommandations.")
            
            cols = st.columns(5)
            for i, (index, row_rec) in enumerate(resultats.iterrows()):
                if i < 5:
                    with cols[i]:
                        genres_rec = nettoyer_genres(row_rec['genres'])
                        note_rec = f"⭐ {row_rec['note']}/10"
                        
                        # Bouton de mise à jour dynamique (Utilise le callback pour éviter l'erreur API)
                        st.button(
                            "📖", 
                            key=f"reco_{i}_{row_rec['titre']}", 
                            help=f"Voir {row_rec['titre']}", 
                            use_container_width=True,
                            on_click=handle_reco_click, 
                            args=[row_rec['titre']]
                        )
                        
                        st.image(row_rec['lien_poster'], use_container_width=True)
                        st.markdown(f"**{row_rec['titre']}**")
                        st.caption(f"{genres_rec} • {note_rec}")
        else:
            st.error("Pas de recommandations disponibles pour ce film.")

    elif rechercher and not film_choisi:
        st.warning("⚠️ Veuillez sélectionner un film dans la liste.")
    
    elif not is_valid_movie:
        st.info("👆 Sélectionnez un film que vous avez aimé pour obtenir des recommandations personnalisées.")

elif page == "Presentation":
    st.title("🎥 Vidéo de présentation")
    if os.path.exists(VIDEO_URL):
        st.video(VIDEO_URL, format="video/mp4")
    else:
        st.warning("La vidéo de présentation n'est pas disponible.")
        st.info("Vérifiez que le fichier existe : " + VIDEO_URL)

elif page == "Infos Pratiques":
    st.title("📍 Nous trouver & Tarifs")
    col_carte, col_infos = st.columns([2, 1], gap="large")
    with col_carte:
        st.map(data={"lat": [46.237], "lon": [1.486]}, zoom=14)
        st.caption("📍 Rue du Cinéma, 23300 La Souterraine")
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
