import streamlit as st
import pandas as pd
import random

# Configuration de la page
st.set_page_config(page_title="Jeu de vocabulaire", layout="centered")
st.title("🔗 Associez les mots")

# --- CSS pour uniformiser la taille et l'apparence des boutons et cases désactivées ---
st.markdown("""
<style>
/* Boutons pleine largeur et hauteur fixe */
div.stButton > button {
    width: 100% !important;
    height: 50px !important;
}
/* Case statique grisée pour mots trouvés */
.slot-disabled {
    width: 100% !important;
    height: 50px !important;
    background-color: #cccccc;
    color: #666666;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    margin-bottom: 8px;
}
/* Marge uniforme entre boutons */
div.stButton {
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- Validation d'une paire (callback) ---
def valider_paire(mot_cible):
    sel = st.session_state.selection
    if sel and sel[0] == "src":
        mot_source = sel[1]
        if (mot_source, mot_cible) in st.session_state.paires_restantes:
            st.session_state.score += 1
            st.session_state.trouves.extend([mot_source, mot_cible])
            st.session_state.paires_restantes.remove((mot_source, mot_cible))
        else:
            st.session_state.score -= 1
        st.session_state.selection = None

# --- Chargement du fichier Excel ---
@st.cache_data
def charger_vocabulaire(fichier):
    df = pd.read_excel(fichier)
    colonnes = df.columns.tolist()
    return df, colonnes

# --- Initialisation de la session ---
if "en_cours" not in st.session_state:
    st.session_state.en_cours = False
    st.session_state.score = 0
    st.session_state.série = 1
    st.session_state.nb_slots = 6
    st.session_state.paires_restantes = []
    st.session_state.selection = None
    st.session_state.utilisés = []
    st.session_state.trouves = []
    st.session_state.langue_source = None
    st.session_state.langue_cible = None
    st.session_state.order_source = []
    st.session_state.order_target = []

# --- Nouvelle série ---
def nouvelle_série(df):
    df_dispo = df[~df.index.isin(st.session_state.utilisés)]
    if len(df_dispo) < st.session_state.nb_slots:
        st.session_state.utilisés = []
        df_dispo = df
    paires = df_dispo.sample(st.session_state.nb_slots, random_state=random.randint(0, 10000))
    st.session_state.utilisés += list(paires.index)
    new_pairs = list(zip(
        paires[st.session_state.langue_source],
        paires[st.session_state.langue_cible]
    ))
    st.session_state.paires_restantes = new_pairs
    st.session_state.trouves = []
    order_source = [pair[0] for pair in new_pairs]
    order_target = [pair[1] for pair in new_pairs]
    random.shuffle(order_source)
    random.shuffle(order_target)
    st.session_state.order_source = order_source
    st.session_state.order_target = order_target
    st.session_state.selection = None

# --- Affichage et logique du jeu ---
def afficher_jeu(df):
    # Passage à la série suivante si nécessaire
    if not st.session_state.paires_restantes:
        if st.session_state.série < 5:
            st.session_state.série += 1
            nouvelle_série(df)
            st.balloons()
        else:
            st.markdown("## 🎉 Partie terminée !")
            st.markdown(f"### Score final : **{st.session_state.score}** points")
            if st.button("🔁 Rejouer une partie"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
            return

    st.subheader(f"Série {st.session_state.série} / 5")
    st.markdown(f"Langue : **{st.session_state.langue_source}** → **{st.session_state.langue_cible}**")
    st.markdown(f"Score : **{st.session_state.score}** points")

    max_buttons = st.session_state.nb_slots
    col1, col2 = st.columns(2)

    # Colonne source
    with col1:
        st.markdown("### 🔸 Source")
        for i in range(max_buttons):
            if i < len(st.session_state.order_source):
                mot = st.session_state.order_source[i]
                if mot in st.session_state.trouves:
                    st.markdown(f"<div class='slot-disabled'>{mot}</div>", unsafe_allow_html=True)
                else:
                    if st.button(mot, key=f"src_{mot}"):
                        st.session_state.selection = ("src", mot)
            else:
                st.markdown("<div style='height:50px; margin-bottom:8px;'></div>", unsafe_allow_html=True)

    # Colonne cible
    with col2:
        st.markdown("### 🔹 Cible")
        for i in range(max_buttons):
            if i < len(st.session_state.order_target):
                mot = st.session_state.order_target[i]
                if mot in st.session_state.trouves:
                    st.markdown(f"<div class='slot-disabled'>{mot}</div>", unsafe_allow_html=True)
                else:
                    st.button(
                        mot,
                        key=f"cib_{mot}",
                        on_click=valider_paire,
                        args=(mot,)
                    )
            else:
                st.markdown("<div style='height:50px; margin-bottom:8px;'></div>", unsafe_allow_html=True)

# --- Chargement du fichier Excel et configuration ---
fichier_excel = "vocabulaire_allemand_traduit_depuis_allemand.xlsx"
try:
    df, colonnes = charger_vocabulaire(fichier_excel)
except Exception as e:
    st.error("Erreur de chargement du fichier Excel.")
    st.exception(e)
    st.stop()

langues_autorisées = [l for l in ["Deutsch", "Français", "English"] if l in colonnes]

with st.sidebar:
    st.header("Paramètres de la partie")
    if len(langues_autorisées) < 2:
        st.error("Le fichier Excel doit contenir au moins deux colonnes parmi : Deutsch, Français, English.")
        st.stop()
    if not st.session_state.en_cours:
        src = st.selectbox("Langue source", langues_autorisées, index=0)
        tgt = st.selectbox("Langue cible", [l for l in langues_autorisées if l != src], index=0)
        if st.button("🎮 Commencer la partie"):
            st.session_state.langue_source = src
            st.session_state.langue_cible = tgt
            st.session_state.en_cours = True
            nouvelle_série(df)
    else:
        st.info("Une partie est en cours...")
        if st.button("❌ Fermer le jeu"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.stop()

# --- Lancement du jeu ---
if st.session_state.en_cours:
    afficher_jeu(df)
else:
    st.info("Bienvenue ! Sélectionnez vos langues et commencez une partie.")
