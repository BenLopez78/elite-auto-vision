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

st.title("🚗 ELITE AUTO VISION - STUDIO (Vitesse Cloud API)")
st.write("Détourage IA et intégration réaliste au premier plan.")

# 2. Zone de configuration de la clé API
st.sidebar.subheader("🔑 Configuration")
api_key = st.sidebar.text_input("Entrez votre clé Remove.bg API", type="password")
st.sidebar.markdown("[Obtenir une clé gratuite ici](https://www.remove.bg/fr/api)")

# 3. Zone de dépôt des fichiers
col_f, col_v = st.columns(2)

with col_f:
    st.subheader("1. Image de fond fixe (Concession)")
    bg_upload = st.file_uploader("Déposez la photo de la concession", type=["jpg", "jpeg", "png"], key="bg")

with col_v:
    st.subheader("2. Photos des véhicules sales")
    car_uploads = st.file_uploader("Déposez les photos des voitures", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="cars")

# 4. Logique de traitement au clic
if st.button("Lancer l'automatisation réaliste", type="primary"):
    if not api_key:
        st.error("Veuillez entrer votre clé API dans la barre latérale gauche.")
    elif not bg_upload:
        st.error("Veuillez fournir une image de fond.")
    elif not car_uploads:
        st.error("Veuillez fournir au moins une image de véhicule.")
    else:
        status_tracker = st.empty()
        progress_bar = st.progress(0)
        
        try:
            bg_img_raw = Image.open(bg_upload)
            bg_w, bg_h = bg_img_raw.size
            processed_images = {}
            total_files = len(car_uploads)
            
            st.write("### 🖼️ Aperçu du catalogue généré (Rendu réaliste) :")
            preview_container = st.empty()
            
            for i, car_upload in enumerate(car_uploads):
                percent_complete = int((i / total_files) * 100)
                status_tracker.markdown(f"🚀 **Envoi au cloud ({percent_complete}%)** — Traitement du véhicule {i+1}/{total_files}...")
                progress_bar.progress(i / total_files)
                
                # Appel de l'API externe
                response = requests.post(
                    'https://api.remove.bg/v1.0/removebg',
                    files={'image_file': car_upload.getvalue()},
                    data={'size': 'auto'},
                    headers={'X-API-Key': api_key},
                )
                
                if response.status_code == 200:
                    car_cleaned_no_bg = Image.open(io.BytesIO(response.content))
                    
                    # Composition sur la concession
                    bg_copy = bg_img_raw.copy().convert("RGBA")
                    ratio = car_cleaned_no_bg.height / car_cleaned_no_bg.width
                    
                    # --- CORRECTION DE TAILLE DEMANDÉE ---
                    new_width = int(bg_w * 0.45) # Plus petit (45%), pour un rendu réaliste
                    new_height = int(new_width * ratio)
                    car_resized = car_cleaned_no_bg.resize((new_width, new_height))
                    
                    # --- CORRECTION DE POSITIONNEMENT DEMANDÉE (ATTERRISSAGE) ---
                    # 1. Centré horizontalement (X)
                    pos_x = (bg_w - car_resized.width) // 2
                    
                    # 2. Ancré au bas (Y) : On calcule pos_y pour que le BAS de la voiture soit à 96% du bas
                    # Cela "pose" les roues sur l'asphalte
                    pos_y = int(bg_h * 0.96) - car_resized.height
                    
                    bg_copy.paste(car_resized, (pos_x, pos_y), car_resized)
                    final_img = bg_copy.convert("RGB")
                    
                    # Sauvegarde en mémoire
                    img_byte_arr = io.BytesIO()
                    final_img.save(img_byte_arr, format='JPEG', quality=85)
                    processed_images[f"elite_auto_vision_{i+1}_{car_upload.name}"] = img_byte_arr.getvalue()
                    
                    # Affichage immédiat du résultat corrigé
                    preview_container.image(final_img, caption=f"Rendu final réaliste (Ancré au sol) : {car_upload.name}")
                else:
                    st.error(f"Erreur de détourage sur {car_upload.name} : {response.text}")
            
            status_tracker.markdown("🏆 **Toutes les photos sont prêtes, stationnées et ancrées au sol !**")
            progress_bar.progress(1.0)
            
            # Création du ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for filename, img_data in processed_images.items():
                    zf.writestr(filename, img_data)
                    
            st.download_button(
                label="📦 Télécharger le catalogue finalisé (.ZIP)",
                data=zip_buffer.getvalue(),
                file_name="auto_leclair_catalogue.zip",
                mime="application/zip",
                help="Ce fichier contient les véhicules stationnés devant la concession de Saint-Jérôme."
            )
            
        except Exception as e:
            st.error(f"❌ Une erreur est survenue pendant la création du rendu : {e}")
