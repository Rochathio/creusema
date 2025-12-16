import streamlit as st
import pandas as pd
import requests
import ast 
import os
from sklearn.neighbors import NearestNeighbors

# --- 1. Configuration de la Page (Doit être la première commande) ---
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
if 'film_selectbox' not in st.session_state:
    st.session_state['film_selectbox'] = ""

# --- 3. Constantes et Configuration API ---
# Note: Les chemins locaux ne fonctionneront pas si l'app est déployée en ligne (Streamlit Cloud).
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
    div.stButton > button {
        border-radius: 8px; border: none; font-weight: bold; transition: all 0.3s ease;
    }
    div.stButton > button[data-testid="base-button-secondary"] {
        background-color: #333345; color: #FFFFFF;
    }
    div.stButton > button[data-testid="base-button-secondary"]:hover {
        background-color: #444456; transform: translateY(-2px);
    }
    div.stButton > button[data-testid="base-button-primary"] {
        background-color: #cb6ce6; color: white;
    }
    div.stButton > button[data-testid="base-button-primary"]:hover {
        background-color: #d688ed; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(203, 108, 230, 0.4);
    }
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #262730; border-radius: 10px;
    }
    .film-details {
        background: linear-gradient(135deg, #2d2d3f 0%, #1f1f2e 100%);
        border-radius: 15px; padding: 25px; margin: 20px 0;
        border-left: 4px solid #cb6ce6; animation: slideIn 0.4s ease-out;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .film-title { color: #cb6ce6; font-size: 28px; font-weight: bold; margin-bottom: 15px; }
    .film-info { color: #e0e0e0; line-height: 1.8; font-size: 16px; }
    .badge {
        display: inline-block; background-color: #cb6ce6; color: white;
        padding: 5px 12px; border-radius: 20px; margin: 5px; font-size: 14px; font-weight: bold;
    }
    div[data-baseweb="select"] { border-radius: 8px; }
    div[data-baseweb="select"] > div { background-color: #262730; border-color: #cb6ce6; }
    .film-poster {
        border-radius: 10px; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.5); transition: transform 0.3s ease;
    }
    .film-poster:hover { transform: scale(1.05); }
    </style>
""", unsafe_allow_html=True)

# --- 5. Fonctions Utilitaires & API ---

@st.cache_data
def charger_donnees_csv():
    try:
        df = pd.read_csv("https://raw.githubusercontent.com/Rochathio/creusema/refs/heads/main/films_final_extended.csv")
        df = df.dropna(subset=['lien_poster'])
        df['genres'] = df['genres'].astype(str)
        return df
    except Exception as e:
        st.error(f"Erreur CSV : {e}")
        return pd.DataFrame()

def nettoyer_genres(genre_str):
    try:
        liste = ast.literal_eval(genre_str)
        if isinstance(liste, list): return " / ".join(liste[:2]) 
        return genre_str
    except:
        return str(genre_str).replace("['", "").replace("']", "").replace("', '", " / ")

def get_synopsis_safe(row):
    for col in ['synopsis', 'overview', 'description', 'plot']:
        if col in row and pd.notna(row[col]):
            val = str(row[col]).strip()
            if val and val.lower() != 'nan': return val
    return ""

# --- Fonction Popup (Recommandation) ---
@st.dialog("Détails du film")
def afficher_popup_reco(row):
    """Affiche les détails + la vidéo (si dispo) dans une fenêtre modale."""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image(row['lien_poster'], use_container_width=True)
    with col2:
        st.subheader(row['titre'])
        st.markdown(f"**Genre(s) :** {nettoyer_genres(row['genres'])}")
        st.markdown(f"**Note :** ⭐ {row['note']}/10")
        
        synopsis = get_synopsis_safe(row)
        if synopsis:
            st.markdown("### 📖 Synopsis")
            st.write(synopsis)
    
    # Affichage Vidéo si disponible dans le CSV
    if 'lien_trailer' in row and pd.notna(row['lien_trailer']):
        lien = str(row['lien_trailer']).strip()
        if lien.startswith('http'):
            st.markdown("---")
            st.caption("🎥 Bande-annonce")
            st.video(lien)

# --- Fonctions API TMDB ---
def fetch_now_playing_movies():
    try:
        response = requests.get(BASE_API_URL, params={'api_key': API_KEY, 'language': 'fr-FR', 'region': 'FR'})
        response.raise_for_status() 
        return response.json().get('results', []) 
    except: return []

def fetch_movie_details(movie_id):
    try:
        response = requests.get(f"{MOVIE_DETAILS_URL}/{movie_id}", params={'api_key': API_KEY, 'language': 'fr-FR', 'append_to_response': 'videos'})
        response.raise_for_status()
        return response.json()
    except: return None

def afficher_details_film_tmdb(movie_id):
    details = fetch_movie_details(movie_id)
    if not details:
        st.error("Détails indisponibles.")
        return
    
    st.markdown('<div class="film-details">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        if details.get('poster_path'): st.image(IMAGE_BASE_URL + details.get('poster_path'), use_container_width=True)
    with c2:
        st.markdown(f'<div class="film-title">{details.get("title")}</div>', unsafe_allow_html=True)
        genres = [g['name'] for g in details.get('genres', [])][:3]
        for g in genres: st.markdown(f'<span class="badge">{g}</span>', unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(f"**Sortie:** {details.get('release_date')} | **Note:** {details.get('vote_average')}/10 | **Durée:** {details.get('runtime')} min")
        st.markdown(f"### 📖 Synopsis\n{details.get('overview')}")
    
    videos = details.get('videos', {}).get('results', [])
    trailers = [v for v in videos if v['type'] == 'Trailer' and v['site'] == 'YouTube']
    if trailers:
        st.markdown("---")
        st.video(f"https://www.youtube.com/watch?v={trailers[0]['key']}")
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("← Retour", type="secondary"):
        st.session_state['film_selectionne'] = None
        st.rerun()

def afficher_carte_film(titre, image_url, sous_titre, horaires, movie_id):
    with st.container():
        if movie_id:
            if st.button("🎬", key=f"btn_{movie_id}", help=f"Voir {titre}", use_container_width=True):
                st.session_state['film_selectionne'] = movie_id
                st.rerun()
        if image_url: st.markdown(f'<img src="{image_url}" class="film-poster" style="width:100%; border-radius:10px;">', unsafe_allow_html=True)
        st.markdown(f"**{titre}**")
        if sous_titre: st.caption(sous_titre)
        if horaires: st.info(f"🕒 Séance : {horaires}")

# --- 6. Machine Learning ---
df_films = charger_donnees_csv()

@st.cache_resource
def entrainer_modele(df):
    if df.empty: return None, None
    clean_genres = df['genres'].str.replace("['", "").str.replace("']", "").str.replace("', '", ",")
    X = clean_genres.str.get_dummies(sep=',')
    model = NearestNeighbors(n_neighbors=6, metric='cosine', algorithm='brute')
    model.fit(X)
    return model, X

modele_knn, X_matrix = entrainer_modele(df_films)

def recommander_film(titre, df, model, X):
    try:
        idx = df[df['titre'] == titre].index[0]
        distances, indices = model.kneighbors(X.iloc[idx].values.reshape(1, -1))
        return df.iloc[indices[0][1:]]
    except: return None

# --- 7. Navigation ---
def set_page(p):
    st.session_state['page'] = p
    st.session_state['film_selectionne'] = None
    if 'film_selectbox' in st.session_state: st.session_state['film_selectbox'] = ""

with st.sidebar:
    c1, c2 = st.columns([2, 1])
    with c1: st.title("CREUSÉMA")
    with c2: 
        if os.path.exists(LOGO_PATH): st.image(LOGO_PATH, width=50)
        else: st.markdown("🎬")
    st.markdown("---")
    for p_key, p_label in {"Accueil": "🏠 Accueil", "Recommandations": "💡 Recommandations", "Infos Pratiques": "🗺️ Infos", "Presentation": "🎥 Présentation"}.items():
        st.button(p_label, key=p_key, type="primary" if st.session_state['page'] == p_key else "secondary", on_click=set_page, args=[p_key], use_container_width=True)
    st.markdown("---")
    st.caption("© 2025 Creuséma Cinéma")

# --- 8. Logique des Pages ---
page = st.session_state['page']

if page == "Accueil":
    st.title("🎬 Bienvenue dans votre cinéma Creuséma")
    sel = st.session_state['film_selectionne']
    # Vérifie si selection est un ID TMDB (int/digit)
    if sel and isinstance(sel, (int, str)) and str(sel).isdigit():
        afficher_details_film_tmdb(sel)
    else:
        # Reset si on vient des recos
        if sel and not str(sel).isdigit(): st.session_state['film_selectionne'] = None
        
        st.subheader("Actuellement en salle")
        movies = fetch_now_playing_movies()
        if movies:
            cols = st.columns(4)
            horaires = ["18h00", "20h30", "21h00", "22h15"]
            for i, m in enumerate(movies[:4]):
                with cols[i]:
                    poster = IMAGE_BASE_URL + m.get('poster_path') if m.get('poster_path') else None
                    afficher_carte_film(m.get('title'), poster, f"Sortie: {m.get('release_date')}", horaires[i], m.get('id'))
        else: st.info("Impossible de charger les films.")

elif page == "Recommandations":
    st.title("💡 Je ne sais pas quoi regarder...")
    st.subheader("Quel film avez-vous aimé récemment ?")

    c_search, c_btn = st.columns([3, 1])
    liste = sorted(df_films['titre'].unique().tolist()) if not df_films.empty else []
    
    with c_search:
        choix = st.selectbox("Recherche", [""] + liste, label_visibility="collapsed", placeholder="Choisissez un film...", key="film_selectbox")
    with c_btn:
        rechercher = st.button("Trouver mon film", type="primary", use_container_width=True)

    if rechercher and choix:
        st.session_state['film_selectionne'] = choix
    
    current_movie = st.session_state.get('film_selectionne')
    is_valid = current_movie and isinstance(current_movie, str) and current_movie in df_films['titre'].values

    st.markdown("---")

    if is_valid:
        # --- PARTIE 1 : RECOMMANDATIONS (En Premier) ---
        recos = recommander_film(current_movie, df_films, modele_knn, X_matrix)
        
        if recos is not None and not recos.empty:
            st.header(f"🎯 Si vous avez aimé {current_movie}, regardez ça :")
            st.caption("Cliquez sur 📖 pour voir le détail et la bande-annonce.")
            
            cols = st.columns(5)
            for i, (idx, row_rec) in enumerate(recos.iterrows()):
                if i < 5:
                    with cols[i]:
                        # Bouton Popup
                        if st.button("📖 Détails", key=f"btn_rec_{i}", use_container_width=True):
                            afficher_popup_reco(row_rec)
                        
                        st.image(row_rec['lien_poster'], use_container_width=True)
                        st.markdown(f"**{row_rec['titre']}**")
        else:
            st.warning("Pas de recommandations trouvées.")

        st.markdown("<br><hr>", unsafe_allow_html=True)

        # --- PARTIE 2 : DÉTAILS DU FILM RECHERCHÉ (En Second) ---
        row_main = df_films[df_films['titre'] == current_movie].iloc[0]
        st.subheader(f"🎞️ Votre sélection : {current_movie}")
        
        st.markdown('<div class="film-details">', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 3])
        with c1: st.image(row_main['lien_poster'], use_container_width=True)
        with c2:
            st.markdown(f'<div class="film-title">{row_main["titre"]}</div>', unsafe_allow_html=True)
            for g in nettoyer_genres(row_main['genres']).split(' / '):
                st.markdown(f'<span class="badge">{g}</span>', unsafe_allow_html=True)
            st.markdown(f"**Note :** ⭐ {row_main['note']}/10")
            syn = get_synopsis_safe(row_main)
            if syn:
                st.markdown("### 📖 Synopsis")
                st.write(syn)
            
            # Vidéo Film Principal
            if 'lien_trailer' in row_main and pd.notna(row_main['lien_trailer']):
                url = str(row_main['lien_trailer']).strip()
                if url.startswith('http'):
                    st.markdown("### 🎥 Bande-annonce")
                    st.video(url)
        st.markdown('</div>', unsafe_allow_html=True)

    elif not is_valid:
        st.info("Sélectionnez un film pour voir nos suggestions.")

elif page == "Presentation":
    st.title("🎥 Présentation")
    if os.path.exists(VIDEO_URL): st.video(VIDEO_URL)
    else: st.warning(f"Vidéo introuvable : {VIDEO_URL}")

elif page == "Infos Pratiques":
    st.title("📍 Infos Pratiques")
    c1, c2 = st.columns([2, 1], gap="large")
    with c1:
        st.map(data={"lat": [46.237], "lon": [1.486]}, zoom=14)
        st.caption("Rue du Cinéma, 23300 La Souterraine")
    with c2:
        for i in [{"icon":"📍","t":"ADRESSE","d":"23300 La Souterraine"}, {"icon":"🎟️","t":"TARIFS","d":"Plein: 8€ / Réduit: 6€"}, {"icon":"📞","t":"CONTACT","d":"05 55 55 44 77"}]:
            with st.container(border=True):
                st.markdown(f"### {i['icon']} {i['t']}")
                st.markdown(i['d'])
