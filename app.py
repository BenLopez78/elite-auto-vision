import streamlit as st
import io
import zipfile
import requests
from PIL import Image

# 1. Configuration de la page
st.set_page_config(
    page_title="Elite Auto Vision Studio - Groupe Auto Leclair", 
    layout="wide"
)

st.title("🚗 ELITE AUTO VISION - STUDIO PRO (Version Éditeur)")
st.write("Étape 1 : Détourez via l'IA. Étape 2 : Positionnez au millimètre près en temps réel.")

# 2. Barre latérale de configuration
st.sidebar.subheader("🔑 Configuration")
api_key = st.sidebar.text_input("Entrez votre clé Remove.bg API", type="password")
st.sidebar.markdown("[Obtenir une clé gratuite ici](https://www.remove.bg/fr/api)")

# Initialisation de la mémoire Streamlit (évite de rappeler l'API à chaque mouvement de curseur)
if "voitures_detourees" not in st.session_state:
    st.session_state.voitures_detourees = {}

# 3. Zone de dépôt des fichiers
col_f, col_v = st.columns(2)

with col_f:
    st.subheader("1. Image de fond fixe (Concession)")
    bg_upload = st.file_uploader("Déposez la photo de la concession", type=["jpg", "jpeg", "png"], key="bg")

with col_v:
    st.subheader("2. Photos des véhicules (Max 2)")
    car_uploads = st.file_uploader("Déposez les photos des voitures", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="cars")

# Limitation de sécurité pour le mode gratuit
if car_uploads and len(car_uploads) > 2:
    st.warning("⚠️ Mode démo activé : Seules les 2 premières images seront traitées.")
    car_uploads = car_uploads[:2]

# Bouton de déclenchement du détourage (Étape 1)
if st.button("🚀 Étape 1 : Lancer le détourage IA (Consomme des crédits)", type="primary"):
    if not api_key:
        st.error("Veuillez entrer votre clé API dans la barre latérale gauche.")
    elif not bg_upload:
        st.error("Veuillez fournir une image de fond (concession).")
    elif not car_uploads:
        st.error("Veuillez fournir au moins une image de véhicule.")
    else:
        with st.spinner("Extraction de la silhouette du véhicule par l'IA..."):
            for car_upload in car_uploads:
                response = requests.post(
                    'https://api.remove.bg/v1.0/removebg',
                    files={'image_file': car_upload.getvalue()},
                    data={'size': 'auto'},
                    headers={'X-API-Key': api_key},
                )
                
                if response.status_code == 200:
                    # Sauvegarde du détourage transparent dans la mémoire de l'application
                    img_transparent = Image.open(io.BytesIO(response.content))
                    st.session_state.voitures_detourees[car_upload.name] = img_transparent
                    st.success(f"✅ Détourage réussi pour {car_upload.name} !")
                else:
                    st.error(f"Erreur du serveur sur {car_upload.name} : {response.text}")

# Zone d'ajustement géométrique (Étape 2 - S'affiche uniquement si des images sont détourées)
if st.session_state.voitures_detourees and bg_upload:
    st.write("---")
    st.subheader("🛠️ Étape 2 : Ajustement de précision (Ajustez les lignes en temps réel)")
    st.info("💡 Bougez les curseurs ci-dessous. Le calcul est instantané et gratuit.")
    
    bg_img_raw = Image.open(bg_upload)
    bg_w, bg_h = bg_img_raw.size
    images_finales_dict = {}
    
    # Génération des outils de contrôle pour chaque voiture détourée
    for file_name, car_transparent in st.session_state.voitures_detourees.items():
        st.markdown(f"#### ⚙️ Réglages pour : `{file_name}`")
        
        col_sliders, col_render = st.columns([1, 2])
        
        with col_sliders:
            # Curseurs manuels intuitifs
            zoom = st.slider("🔍 Zoom / Échelle du véhicule (%)", min_value=15, max_value=100, value=42, key=f"zoom_{file_name}")
            pos_x_pct = st.slider("↔️ Position Horizontale (Gauche à Droite %)", min_value=0, max_value=100, value=50, key=f"x_{file_name}")
            pos_y_pct = st.slider("↕️ Position Verticale (Hauteur sur l'asphalte %)", min_value=50, max_value=100, value=96, key=f"y_{file_name}")
            
        # Calcul de la composition Pillow en direct
        bg_copy = bg_img_raw.copy().convert("RGBA")
        ratio = car_transparent.height / car_transparent.width
        
        # Application du zoom basé sur la largeur du fond
        new_width = int(bg_w * (zoom / 100))
        new_height = int(new_width * ratio)
        car_resized = car_transparent.resize((new_width, new_height))
        
        # Positionnement horizontal (0% = collé à gauche, 100% = collé à droite)
        pos_x = int((bg_w - car_resized.width) * (pos_x_pct / 100))
        
        # Positionnement vertical basé sur le BAS des roues
        bas_des_roues = int(bg_h * (pos_y_pct / 100))
        pos_y = bas_des_roues - car_resized.height
        
        # Collage transparent
        bg_copy.paste(car_resized, (pos_x, pos_y), car_resized)
        final_img = bg_copy.convert("RGB")
        
        # Affichage du rendu en temps réel
        with col_render:
            st.image(final_img, caption=f"Rendu final personnalisé - {file_name}")
            
        # Préparation du fichier final pour le téléchargement
        img_byte_arr = io.BytesIO()
        final_img.save(img_byte_arr, format='JPEG', quality=88)
        images_finales_dict[f"elite_studio_{file_name}"] = img_byte_arr.getvalue()
        
    # Section finale de téléchargement du catalogue
    st.write("---")
    if images_finales_dict:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for fname, img_bytes in images_finales_dict.items():
                zf.writestr(fname, img_bytes)
                
        st.download_button(
            label="📦 Télécharger les rendus ajustés (.ZIP)",
            data=zip_buffer.getvalue(),
            file_name="catalogue_elite_ajuste.zip",
            mime="application/zip",
            help="Cliquez ici pour récupérer vos photos parfaitement stationnées."
        )
