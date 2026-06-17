import streamlit as st
from rembg import remove, new_session
from PIL import Image
import io
import zipfile

# Configuration de la page
st.set_page_config(page_title="Elite Auto Vision Studio - Groupe Auto Leclair", layout="wide")

# --- FORCE LE THÈME SOMBRE POUR ÉVITER LE BLANC SUR BLANC ---
st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #0a0a0a !important;
        }
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0) !important;
        }
        .stButton>button { 
            background-color: #e31937 !important; 
            color: white !important; 
            border-radius: 8px !important; 
            font-weight: bold !important;
            border: none !important;
            padding: 0.5rem 2rem !important;
            width: 100% !important;
        }
        .stButton>button:hover { 
            background-color: #b1142b !important; 
        }
        h1, h2, h3, p, label, span, div { 
            color: #ffffff !important; 
        }
        [data-testid="stFileUploadDropzone"] {
            background-color: #161616 !important;
            border: 2px dashed #333 !important;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🚗 ELITE AUTO VISION - STUDIO")
st.write("Automatisez la préparation de vos 20 véhicules : nettoyage virtuel, détourage et fusion sur le fond de la concession.")

# -- Interface de Dépôt --
col_f, col_v = st.columns(2)

with col_f:
    st.subheader("1. Image de fond fixe (Concession)")
    bg_upload = st.file_uploader("Déposez la photo de la concession", type=["jpg", "jpeg", "png"], key="bg")

with col_v:
    st.subheader("2. Photos des véhicules sales (Max 20)")
    car_uploads = st.file_uploader("Déposez les photos des voitures", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="cars")

# -- Logique de Traitement --
if st.button("Lancer l'automatisation intelligente (Batch)", type="primary"):
    if not bg_upload:
        st.error("Veuillez fournir une image de fond (votre concession).")
    elif not car_uploads:
        st.error("Veuillez fournir au moins une image de véhicule.")
    elif len(car_uploads) > 20:
        st.error("Désolé, l'outil est limité à 20 images maximum.")
    else:
        st.info("⚡ Traitement IA en cours... Le premier véhicule peut prendre un peu plus de temps pour réveiller le moteur de détourage.")
        
        bg_img_raw = Image.open(bg_upload)
        bg_w, bg_h = bg_img_raw.size
        processed_images = {}
        
        # Initialisation propre de la session de détourage
        session = new_session("u2net")
        progress_bar = st.progress(0)
        
        for i, car_upload in enumerate(car_uploads):
            car_img_raw = Image.open(car_upload).convert("RGBA")
            
            # Détourage automatique par l'IA
            car_cleaned_no_bg = remove(car_img_raw, session=session)
            
            # Composition
            bg_copy = bg_img_raw.copy().convert("RGBA")
            
            ratio = car_cleaned_no_bg.height / car_cleaned_no_bg.width
            new_width = int(bg_w * 0.7)
            new_height = int(new_width * ratio)
            car_resized = car_cleaned_no_bg.resize((new_width, new_height))
            
            pos_x = (bg_w - car_resized.width) // 2
            pos_y = bg_h - car_resized.height - 100
            
            bg_copy.paste(car_resized, (pos_x, pos_y), car_resized)
            final_img = bg_copy.convert("RGB")
            
            img_byte_arr = io.BytesIO()
            final_img.save(img_byte_arr, format='JPEG', quality=90)
            processed_images[f"elite_auto_vision_{i+1}_{car_upload.name}"] = img_byte_arr.getvalue()
            
            progress_bar.progress((i + 1) / len(car_uploads))
            
        st.success("🏆 Toutes les images ont été traitées avec succès !")
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for filename, img_data in processed_images.items():
                zf.writestr(filename, img_data)
                
        st.download_button(
            label="📦 Télécharger l'archive des véhicules (.ZIP)",
            data=zip_buffer.getvalue(),
            file_name="auto_leclair_catalogue.zip",
            mime="application/zip"
        )
