import streamlit as st
import io
import zipfile
from PIL import Image

# 1. Configuration de la page
st.set_page_config(
    page_title="Elite Auto Vision Studio", 
    layout="wide"
)

# Fonction pour charger l'IA TURBO (Ultra-légère, rapide et économique en mémoire)
@st.cache_resource
def load_ai_model():
    from rembg import new_session
    # Utilisation du modèle "u2netp" : optimisé pour s'exécuter en quelques secondes
    return new_session("u2netp")

# Titre de l'application
st.title("🚗 ELITE AUTO VISION - STUDIO")
st.write("Interface d'automatisation ultra-rapide avec affichage du résultat en direct et suivi précis.")

# 2. Zone de dépôt des fichiers
col_f, col_v = st.columns(2)

with col_f:
    st.subheader("1. Image de fond fixe (Concession)")
    bg_upload = st.file_uploader("Déposez la photo de la concession", type=["jpg", "jpeg", "png"], key="bg")

with col_v:
    st.subheader("2. Photos des véhicules sales (Max 20)")
    car_uploads = st.file_uploader("Déposez les photos des voitures", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="cars")

# 3. Logique de traitement au clic
if st.button("Lancer l'automatisation intelligente (Batch)", type="primary"):
    if not bg_upload:
        st.error("Veuillez fournir une image de fond (votre concession).")
    elif not car_uploads:
        st.error("Veuillez fournir au moins une image de véhicule.")
    elif len(car_uploads) > 20:
        st.error("Désolé, l'outil est limité à 20 images maximum.")
    else:
        # Initialisation des éléments de progression demandés
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        try:
            from rembg import remove
            
            # Récupération immédiate du modèle IA Turbo mis en cache
            session = load_ai_model()
            
            bg_img_raw = Image.open(bg_upload)
            bg_w, bg_h = bg_img_raw.size
            processed_images = {}
            total_files = len(car_uploads)
            
            # Zone d'affichage dynamique pour le rendu visuel
            st.write("### 🖼️ Aperçu en direct de la fusion :")
            preview_container = st.empty()
            
            for i, car_upload in enumerate(car_uploads):
                # Calcul et affichage précis du pourcentage (%)
                percent_complete = int((i / total_files) * 100)
                status_text.markdown(f"⏳ **Avancement : {percent_complete}%** — Traitement du véhicule {i+1} sur {total_files}...")
                progress_bar.progress(i / total_files)
                
                car_img_raw = Image.open(car_upload).convert("RGBA")
                
                # Détourage ultra-rapide par l'IA (2 à 4 secondes)
                car_cleaned_no_bg = remove(car_img_raw, session=session)
                
                # Composition sur le fond de la concession
                bg_copy = bg_img_raw.copy().convert("RGBA")
                
                ratio = car_cleaned_no_bg.height / car_cleaned_no_bg.width
                new_width = int(bg_w * 0.65) # Taille proportionnelle de la voiture
                new_height = int(new_width * ratio)
                car_resized = car_cleaned_no_bg.resize((new_width, new_height))
                
                # Ajustement de la position sur la zone asphaltée
                pos_x = (bg_w - car_resized.width) // 2
                pos_y = bg_h - car_resized.height - int(bg_h * 0.05)
                
                bg_copy.paste(car_resized, (pos_x, pos_y), car_resized)
                final_img = bg_copy.convert("RGB")
                
                # Sauvegarde en mémoire
                img_byte_arr = io.BytesIO()
                final_img.save(img_byte_arr, format='JPEG', quality=85)
                processed_images[f"elite_auto_vision_{i+1}_{car_upload.name}"] = img_byte_arr.getvalue()
                
                # AFFICHAGE DU RÉSULTAT : Rend le travail visible à l'écran instantanément
                preview_container.image(final_img, caption=f"Rendu final généré : {car_upload.name}")
                
            # Finalisation à 100%
            status_text.markdown("🏆 **Avancement : 100% — Opération complétée avec succès !**")
            progress_bar.progress(1.0)
            st.success(f"Traitement terminé pour vos {total_files} photo(s).")
            
            # Archive ZIP pour téléchargement groupé
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
            st.error(f"Une erreur est survenue pendant l'exécution : {e}")
