import os
import streamlit as st
import requests
from PIL import Image, ImageDraw
from io import BytesIO

# Optional: support Managed Identity tokens if azure-identity is available
USE_MANAGED_IDENTITY = os.getenv("USE_MANAGED_IDENTITY", "false").lower() in ("1", "true", "yes")

# Environment variable resolution (priority)
ENDPOINT = os.getenv("FACE_API_ENDPOINT") or os.getenv("AZURE_FACE_ENDPOINT") or "https://face-api-britto.cognitiveservices.azure.com/"
KEY = os.getenv("FACE_API_KEY") or os.getenv("AZURE_FACE_KEY")

# If using managed identity, try to obtain a token (optional)
access_token = None
if USE_MANAGED_IDENTITY:
    try:
        # Dynamically import to avoid static analysis/linter errors when azure-identity
        # is not installed in the environment.
        import importlib
        azure_identity = importlib.import_module("azure.identity")
        DefaultAzureCredential = getattr(azure_identity, "DefaultAzureCredential")
        cred = DefaultAzureCredential()
        token = cred.get_token("https://cognitiveservices.azure.com/.default")
        access_token = token.token
    except ModuleNotFoundError:
        # azure-identity is not installed; report and fall back to key-based auth if available
        st.warning("Managed Identity requested but azure-identity is not installed. Falling back to key-based auth if available.")
        access_token = None
    except Exception as e:
        # If there's any other error obtaining a token, report it but continue to allow key-based usage
        st.warning("Managed Identity requested but failed to get token. Falling back to key-based auth if available.")
        access_token = None

# Streamlit UI
st.set_page_config(page_title="ReadingFaceAPI", page_icon="🧑‍🤝‍🧑")
st.title("🧑‍🤝‍🧑 ReadingFaceAPI - Azure Face API Demo")
st.write("Carregue uma imagem e detecte rostos usando a Azure Face API")

# Show configured endpoint/key (but not the key itself)
st.markdown(f"**Endpoint:** `{ENDPOINT}`")
if KEY:
    st.markdown("**Auth:** Using subscription key from environment.")
elif access_token:
    st.markdown("**Auth:** Using Managed Identity / AAD token.")
else:
    st.error("Nenhuma credencial encontrada. Configure FACE_API_KEY (ou AZURE_FACE_KEY) OR enable USE_MANAGED_IDENTITY and assign a Managed Identity to the Web App.")
    st.stop()

# File upload
uploaded_file = st.file_uploader("Escolha uma imagem", type=["jpg", "jpeg", "png"])

def make_face_call(image_bytes):
    # prepare URL (ensure single slash)
    base = ENDPOINT.rstrip('/') + '/'
    url = base + "face/v1.0/detect"
    params = {"returnFaceAttributes": "glasses,blur,exposure,noise,occlusion"}
    headers = {"Content-Type": "application/octet-stream"}

    # choose auth method
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    elif KEY:
        headers["Ocp-Apim-Subscription-Key"] = KEY
    else:
        raise RuntimeError("No authentication available for Face API request.")

    resp = requests.post(url, params=params, headers=headers, data=image_bytes, timeout=30)
    resp.raise_for_status()
    return resp.json()

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Imagem carregada", use_container_width=True)

    if st.button("🔍 Detectar rostos"):
        # Read bytes (reset pointer)
        uploaded_file.seek(0)
        image_bytes = uploaded_file.read()

        with st.spinner("Enviando imagem para Azure Face API..."):
            try:
                faces = make_face_call(image_bytes)
            except requests.exceptions.HTTPError as he:
                st.error(f"Erro HTTP na chamada à Face API: {he.response.status_code} - {he.response.text}")
                faces = None
            except Exception as e:
                st.error(f"Erro ao chamar Face API: {e}")
                faces = None

        if faces is None:
            st.stop()

        if len(faces) == 0:
            st.warning("Nenhum rosto detectado.")
        else:
            # Draw rectangles
            draw = ImageDraw.Draw(image)
            for i, face in enumerate(faces):
                rect = face.get("faceRectangle", {})
                left, top = rect.get("left", 0), rect.get("top", 0)
                width, height = rect.get("width", 0), rect.get("height", 0)
                draw.rectangle([left, top, left + width, top + height], outline="red", width=3)

                attrs = face.get("faceAttributes", {})
                st.subheader(f"Rosto {i+1}")
                st.write(f"👓 Óculos: {attrs.get('glasses')}")
                st.write(f"📷 Blur: {attrs.get('blur')}")
                st.write(f"☀️ Exposição: {attrs.get('exposure')}")
                st.write(f"🔊 Ruído: {attrs.get('noise')}")
                st.write(f"🙈 Oclusão: {attrs.get('occlusion')}")
                st.write("---")

            st.image(image, caption="Rostos detectados", use_container_width=True)
