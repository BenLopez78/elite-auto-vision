# --- 1. SÉCURITÉ ANTI-BLOCAGE (À laisser impérativement tout en haut) ---
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["ORT_PROV_ONLY_CPU"] = "1"  # Force ONNX à ignorer la recherche de carte graphique (Évite le freeze)

import streamlit as st
import io
import zipfile
from PIL import Image

# --- 2. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Elite Auto Vision Studio - Groupe Auto Leclair", 
    layout="wide"
)

# --- 3. CHARGEMENT DES MODULES LOURDS AU DÉMARRAGE ---
# Streamlit va gérer l'attente proprement à l'ouverture de la page
from rembg import remove, new_session

@st.cache_resource
def load_model():
    return new_session("u2netp")

# Initialisation globale du modèle
session = load_model()

# --- 4. INTERFACE GRAPHIQUE ---
st.title("🚗 ELITE AUTO VISION - STUDIO")
st.write("Interface d'automatisation optimisée : détourage IA et intégration sur la devanture de la concession.")

col_f, col_v = st.columns(2)

with col_f:
    st.subheader("1. Image de fond fixe (Concession)")
    bg_upload = st.file_uploader("Déposez la photo de la concession", type=["jpg", "jpeg", "png"], key="bg")

with col_v:
    st.subheader("2. Photos des véhicules sales (Max 20)")
    car_uploads = st.file_uploader("Déposez les photos des voitures", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="cars")

# --- 5. LOGIQUE DE TRAITEMENT ---
if st.button("Lancer l'automatisation intelligente (Batch)", type="primary"):
    if not bg_upload:
        st.error("Veuillez fournir une image de fond (votre concession).")
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
            
            st.write("### 🖼️ Aperçu du catalogue généré :")
            preview_container = st.empty()
            
            for i, car_upload in enumerate(car_uploads):
                # Calcul et affichage en temps réel du pourcentage (%)
                percent_complete = int((i / total_files) * 100)
                status_tracker.markdown(f"⚡ **Avancement : {percent_complete}%** — Traitement du véhicule {i+1}/{total_files} ({car_upload.name})...")
                progress_bar.progress(i / total_files)
                
                car_img_raw = Image.open(car_upload).convert("RGBA")
                
                # Détourage immédiat (Le moteur est déjà chargé en mémoire)
                car_cleaned_no_bg = remove(car_img_raw, session=session)
                
                # Fusion sur le fond de la concession
                bg_copy = bg_img_raw.copy().convert("RGBA")
                ratio = car_cleaned_no_bg.height / car_cleaned_no_bg.width
                new_width = int(bg_w * 0.65)
                new_height = int(new_width * ratio)
                car_resized = car_cleaned_no_bg.resize((new_width, new_height))
                
                pos_x = (bg_w - car_resized.width) // 2
                pos_y = bg_h - car_resized.height - int(bg_h * 0.05)
                
                bg_copy.paste(car_resized, (pos_x, pos_y), car_resized)
                final_img = bg_copy.convert("RGB")
                
                # Sauvegarde en mémoire
                img_byte_arr = io.BytesIO()
                final_img.save(img_byte_arr, format='JPEG', quality=85)
                processed_images[f"elite_auto_vision_{i+1}_{car_upload.name}"] = img_byte_arr.getvalue()
                
                # Affichage immédiat du résultat à l'écran
                preview_container.image(final_img, caption=f"Rendu final : {car_upload.name}")
            
            # Fin du processus à 100%
            status_tracker.markdown("🏆 **Avancement : 100% — Traitement complété avec succès !**")
            progress_bar.progress(1.0)
            
            # Création de l'archive ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for filename, img_data in processed_images.items():
                    zf.writestr(filename, img_data)
                    
            st.download_button(
                label="📦 Télécharger toutes les photos détourées (.ZIP)",
                data=zip_buffer.getvalue(),
                file_name="auto_leclair_catalogue.zip",
                mime="application/zip"
            )
            
        except Exception as e:
            status_tracker.empty()
            st.error(f"❌ Une erreur technique est survenue : {e}")
