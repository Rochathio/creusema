import streamlit as st
import pandas as pd
import requests
import ast 
import os
from sklearn.neighbors import NearestNeighbors # Import pour la recommandation

# --- 1. Initialisation de l'État et Configuration ---

if 'page' not in st.session_state:
    st.session_state['page'] = 'Accueil' 

st.set_page_config(
    page_title="CREUSÉMA - Cinéma",
    page_icon="🎬",
    layout="wide"
)

# Constantes
VIDEO_URL = "/Users/thiagorocha/WCS/ProjetLITE/videos/Video creusema.mp4"
LOGO_PATH = "/Users/thiagorocha/WCS/ProjetLITE/images/logo_creusema.png" 

# Configuration API TMDB
API_KEY = "25d64f0557c373d5bec7a1242553ff40" 
BASE_API_URL = "https://api.themoviedb.org/3/movie/now_playing"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500" 

# --- CSS Personnalisé ---
st.markdown("""
    <style>
    .stApp {
        background-color:rgb(18, 4, 38);
        color: white;
    }
    div.stButton > button {
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    div.stButton > button[data-testid="base-button-secondary"] {
        background-color: #333345;
        color: #FFFFFF;
    }
    div.stButton > button[data-testid="base-button-primary"] {
        background-color:rgb(150, 33, 218);
        color: white;
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #262730;
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)


# --- 2. Chargement des Données et API ---

@st.cache_data
def charger_donnees_csv():
    """Charge les données depuis le CSV GitHub."""
    try:
        df = pd.read_csv("https://raw.githubusercontent.com/Rochathio/creusema/refs/heads/main/films_final_extended.csv")
        df = df.dropna(subset=['lien_poster'])
        # On s'assure que les genres sont des strings pour le traitement
        df['genres'] = df['genres'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erreur de chargement du CSV : {e}")
        return pd.DataFrame()

def fetch_now_playing_movies():
    """Récupère la liste des films actuellement en salle depuis TMDB."""
    params = {
        'api_key': API_KEY,
        'language': 'fr-FR' 
    }
    try:
        response = requests.get(BASE_API_URL, params=params)
        response.raise_for_status() 
        data = response.json()
        return data.get('results', []) 
    except requests.exceptions.RequestException:
        return []

# Chargement initial des données CSV
df_films = charger_donnees_csv()

# --- 3. Système de Recommandation (Machine Learning) ---

@st.cache_resource
def entrainer_modele_recommandation(df):
    """
    Prépare la matrice X et entraîne le modèle KNN.
    Mis en cache pour ne pas recalculer à chaque clic.
    """
    if df.empty:
        return None, None

    # 1. Création de la matrice X (One-Hot Encoding des genres)
    # Nettoyage : "['Action', 'Comedy']" -> "Action,Comedy"
    clean_genres = df['genres'].str.replace("['", "").str.replace("']", "").str.replace("', '", ",")
    
    # Création des colonnes binaires pour chaque genre
    X = clean_genres.str.get_dummies(sep=',')
    
    # 2. Entraînement du modèle (KNN)
    # n_neighbors=6 car le résultat inclut le film lui-même (qu'on retirera)
    model = NearestNeighbors(n_neighbors=6, metric='cosine', algorithm='brute')
    model.fit(X)
    
    return model, X

# Initialisation du modèle
modele_knn, X_matrix = entrainer_modele_recommandation(df_films)

def recommander_film(nom_du_film, df, model, X):
    """Fonction qui retourne les films recommandés (Logique du Notebook)."""
    try:
        # 1. Trouver l'index du film dans le DataFrame
        idx = df[df['titre'] == nom_du_film].index[0]
        
        # 2. Demander au modèle les voisins
        distances, indices = model.kneighbors(X.iloc[idx].values.reshape(1, -1))
        
        # 3. Récupérer les indices (on ignore le premier [1:] car c'est le film lui-même)
        indices_voisins = indices[0][1:]
        
        # 4. Retourner les films trouvés
        return df.iloc[indices_voisins]
        
    except IndexError:
        return None # Film pas trouvé
    except Exception as e:
        st.error(f"Erreur lors de la recommandation : {e}")
        return None

# --- 4. Fonctions Utilitaires et d'Affichage ---

def set_page(page_name):
    st.session_state['page'] = page_name

def nettoyer_genres(genre_str):
    try:
        liste = ast.literal_eval(genre_str)
        if isinstance(liste, list):
            return " / ".join(liste[:2]) 
        return genre_str
    except:
        return str(genre_str).replace("['", "").replace("']", "").replace("', '", " / ")

def afficher_carte_film(titre, image_url, sous_titre=None, horaire=None):
    if image_url:
        st.image(image_url, width="stretch") # Optimisé pour Streamlit
    else:
        st.warning("Pas d'image")
    
    st.markdown(f"**{titre}**")
    if sous_titre:
        st.caption(sous_titre)
    if horaire:
        st.info(f"🕒 Séance : {horaire}")

# --- 5. Barre Latérale (Navigation) ---

with st.sidebar:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("CREUSÉMA")
    with col2:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=50)
        else:
            st.write("🎬")

    st.markdown("---")
    st.subheader("Navigation")

    PAGES = {
        "Accueil": "🏠 Accueil",
        "Presentation": "🎥 Présentation",
        "Recommandations": "💡 Recommandations",
        "Infos Pratiques": "🗺️ Infos Pratiques"
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
            width="stretch"
        )

    st.markdown("---")
    st.caption("© 2025 Creuséma Cinéma - 2TDM")

page = st.session_state['page'] 

# --- 6. Contenu des Pages ---

if page == "Accueil":
    st.title("Bienvenue dans votre cinéma Creuséma")
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
                
                afficher_carte_film(titre, image_url, sous_titre, horaires[i])
    else:
        st.info("Impossible de charger les films à l'affiche.")

elif page == "Recommandations":
    st.title("Je ne sais pas quoi regarder...")
    st.subheader("Quel film avez-vous aimé récemment ?")

    # --- Adaptation pour la Recommandation ---
    col_search, col_btn = st.columns([3, 1])
    
    # Liste pour le selectbox (évite les fautes de frappe qui cassent le KNN)
    liste_titres = sorted(df_films['titre'].unique().tolist()) if not df_films.empty else []

    with col_search:
        film_choisi = st.selectbox(
            "Recherche", 
            options=[""] + liste_titres,
            label_visibility="collapsed",
            placeholder="Choisissez un film..."
        )

    with col_btn:
        rechercher = st.button("Trouver mon film", type="primary", width="stretch")

    st.markdown("---")

    if rechercher and film_choisi and not df_films.empty:
        st.success(f"Recherche de films similaires à : **{film_choisi}**")
        
        # Appel du modèle KNN
        resultats = recommander_film(film_choisi, df_films, modele_knn, X_matrix)
        
        if resultats is not None and not resultats.empty:
            st.header("Voici 5 pépites pour vous :")
            cols = st.columns(5)
            for i, (index, row) in enumerate(resultats.iterrows()):
                if i < 5: # Sécurité d'affichage
                    with cols[i]:
                        genres = nettoyer_genres(row['genres'])
                        note = f"⭐ {row['note']}/10"
                        # Utilise le lien poster du CSV
                        afficher_carte_film(row['titre'], row['lien_poster'], f"{genres} • {note}")
        else:
            st.error("Désolé, nous n'avons pas trouvé de recommandations proches.")
            
    elif rechercher and not film_choisi:
        st.warning("Veuillez sélectionner un film dans la liste.")
    
    elif not df_films.empty:
         # Affichage par défaut (random)
        st.write("Suggestions aléatoires :")
        selection_reco = df_films.sample(n=5)
        cols = st.columns(5)
        for i, (index, row) in enumerate(selection_reco.iterrows()):
            with cols[i]:
                genres = nettoyer_genres(row['genres'])
                afficher_carte_film(row['titre'], row['lien_poster'], genres)

elif page == "Presentation":
    st.title("Vidéo de présentation")
    st.video(VIDEO_URL, format="video/mp4")

elif page == "Infos Pratiques":
    st.title("Nous trouver & Tarifs")
    col_carte, col_infos = st.columns([2, 1], gap="large")
    with col_carte:
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
