import streamlit as st
import requests
from PIL import Image, ImageDraw
from io import BytesIO

import os
AZURE_FACE_KEY = os.getenv("AZURE_FACE_KEY")

# ============================
# CONFIGURAÇÕES
# ============================
ENDPOINT = "https://face-api-britto-demo.cognitiveservices.azure.com/"
KEY = AZURE_FACE_KEY

# ============================
# INTERFACE STREAMLIT
# ============================
st.set_page_config(page_title="ReadingFaceAPI", page_icon="🧑‍🤝‍🧑")
st.title("🧑‍🤝‍🧑 ReadingFaceAPI - Azure Face API Demo")
st.write("Carregue uma imagem e detecte rostos usando a Azure Face API")

# Upload de imagem
uploaded_file = st.file_uploader("Escolha uma imagem", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Mostrar imagem original
    image = Image.open(uploaded_file)
    st.image(image, caption="Imagem carregada", use_container_width=True)

    # Botão para enviar à API
    if st.button("🔍 Detectar rostos"):
        face_api_url = ENDPOINT + "face/v1.0/detect"
        headers = {
            "Ocp-Apim-Subscription-Key": KEY,
            "Content-Type": "application/octet-stream"
        }
        params = {"returnFaceAttributes": "glasses,blur,exposure,noise,occlusion"}

        response = requests.post(
            face_api_url,
            headers=headers,
            params=params,
            data=uploaded_file.getvalue()
        )

        if response.status_code == 200:
            faces = response.json()

            if len(faces) == 0:
                st.warning("Nenhum rosto detectado.")
            else:
                draw = ImageDraw.Draw(image)
                for i, face in enumerate(faces):
                    rect = face["faceRectangle"]
                    left, top = rect["left"], rect["top"]
                    width, height = rect["width"], rect["height"]
                    draw.rectangle([left, top, left+width, top+height], outline="red", width=3)

                    attrs = face["faceAttributes"]
                    st.subheader(f"Rosto {i+1}")
                    st.write(f"👓 Óculos: {attrs['glasses']}")
                    st.write(f"📷 Blur: {attrs['blur']}")
                    st.write(f"☀️ Exposição: {attrs['exposure']}")
                    st.write(f"🔊 Ruído: {attrs['noise']}")
                    st.write(f"🙈 Oclusão: {attrs['occlusion']}")
                    st.write("---")

                st.image(image, caption="Rostos detectados", use_container_width=True)
        else:
            st.error(f"Erro na chamada à API: {response.status_code} - {response.text}")
