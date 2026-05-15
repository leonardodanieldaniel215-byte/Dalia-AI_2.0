import streamlit as st
import asyncio
import os
import edge_tts
import base64
import time
from PIL import Image
from io import BytesIO
from groq import Groq
from duckduckgo_search import DDGS

# ============================================================
# CONFIGURACIÓN Y LLAVES
# ============================================================
st.set_page_config(page_title="Dalia AI", page_icon="🤖", layout="centered")

# Usar st.secrets para la llave en la nube
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
VOZ_HUMANA = "es-MX-DaliaNeural"
client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# SISTEMA DE ACCESO (LOGIN)
# ============================================================
USUARIOS = {
    "leo123": "Leonardo",
    "chris123": "Christian",
    "manu123": "Manuel"
}

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_nombre = ""

if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center; color: #a78bfa;'>🔐 Acceso a Dalia AI</h2>", unsafe_allow_html=True)
    codigo = st.text_input("Código secreto:", type="password")
    if st.button("Entrar", use_container_width=True):
        if codigo in USUARIOS:
            st.session_state.autenticado = True
            st.session_state.usuario_nombre = USUARIOS[codigo]
            st.rerun()
        else:
            st.error("Código incorrecto.")
    st.stop()

# ============================================================
# CONFIGURACIÓN DE DALIA
# ============================================================
nombre_usuario = st.session_state.usuario_nombre

if "modo_actual" not in st.session_state: st.session_state.modo_actual = "normal"
if "voz_activa" not in st.session_state: st.session_state.voz_activa = True
if "historiales" not in st.session_state: st.session_state.historiales = {"normal": [], "matematica": [], "code": []}
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "saludo_dado" not in st.session_state: st.session_state.saludo_dado = False

INSTRUCCIONES = {
    "normal": f"Eres Dalia, asistente de {nombre_usuario}. Eres joven, alegre y un poco tímida. Hablas natural: 'o sea', 'claro'.",
    "matematica": "Eres Dalia modo MATEMÁTICA. Resumen, Datos, Desarrollo, Resultado y Comprobación.",
    "code": "Eres Dalia modo CODE. Código limpio y bien explicado.",
    "vision": "Analiza la imagen detalladamente para {nombre_usuario}."
}

SALUDO_INICIO = f"¡Hola {nombre_usuario}! Mi caramelito de chocolate 💜 Me alegra que estés aquí. ¿En qué te ayudo?"


# ============================================================
# FUNCIONES (CORRECCIÓN ERROR 400)
# ============================================================
def agregar_al_historial(rol, contenido):
    st.session_state.historiales[st.session_state.modo_actual].append({"role": rol, "content": contenido})
    if len(st.session_state.historiales[st.session_state.modo_actual]) > 15:
        st.session_state.historiales[st.session_state.modo_actual].pop(0)


def procesar_imagen_fuerte(img_file):
    """Optimiza la imagen para evitar el Error 400."""
    img = Image.open(img_file)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Redimensionar si es muy grande (máximo 1024px)
    img.thumbnail((1024, 1024))

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=70)  # Bajar calidad un poco para que pase el filtro
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def analizar_imagen_groq(imagen_b64, prompt=""):
    try:
        # Usamos el modelo de visión más estable
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt if prompt else "Describe esta imagen."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagen_b64}"}}
                ]}
            ],
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Perdón {nombre_usuario}, me dio un error la imagen: {e}"


def buscar_internet(query):
    try:
        textos = []
        with DDGS() as ddgs:
            for r in list(ddgs.text(query, max_results=3, region="mx-es")):
                textos.append(f"{r['title']}: {r['body']}")
        return "\n".join(textos)
    except:
        return None


async def generar_audio(texto):
    archivo = f"v_{int(time.time())}.mp3"
    try:
        com = edge_tts.Communicate(texto[:200], VOZ_HUMANA)
        await com.save(archivo)
        return archivo
    except:
        return None


# ============================================================
# INTERFAZ (UI)
# ============================================================
st.markdown(f"<h1 style='text-align: center; color: #a78bfa;'>🤖 Dalia AI</h1>", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("💬 Normal"): st.session_state.modo_actual = "normal"
with c2:
    if st.button("📐 Mate"): st.session_state.modo_actual = "matematica"
with c3:
    if st.button("💻 Code"): st.session_state.modo_actual = "code"
with c4:
    if st.button("🔊 Voz"): st.session_state.voz_activa = not st.session_state.voz_activa

# Mostrar Chat
for msj in st.session_state.historiales[st.session_state.modo_actual]:
    with st.chat_message(msj["role"]): st.markdown(msj["content"])

if not st.session_state.saludo_dado:
    with st.chat_message("assistant"):
        st.markdown(SALUDO_INICIO)
        if st.session_state.voz_activa:
            a = asyncio.run(generar_audio(SALUDO_INICIO))
            if a: st.audio(a, autoplay=True)
    st.session_state.saludo_dado = True

# SUBIR FOTO
img_file = st.file_uploader("Sube una foto", type=['jpg', 'jpeg', 'png'], key=f"u_{st.session_state.uploader_key}")

if prompt := st.chat_input("Escribe aquí..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        if img_file:
            with st.spinner("Viendo..."):
                b64 = procesar_imagen_fuerte(img_file)
                res = analizar_imagen_groq(b64, prompt)
                st.session_state.uploader_key += 1
        else:
            agregar_al_historial("user", prompt)
            with st.spinner("Pensando..."):
                # Lógica de búsqueda simple
                ctx = ""
                if "busca" in prompt.lower():
                    info = buscar_internet(prompt)
                    if info: ctx = f"Info: {info}\n\n"

                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": INSTRUCCIONES[st.session_state.modo_actual]},
                              *st.session_state.historiales[st.session_state.modo_actual]]
                )
                res = resp.choices[0].message.content

        st.markdown(res)
        agregar_al_historial("assistant", res)
        if st.session_state.voz_activa:
            a = asyncio.run(generar_audio(res))
            if a: st.audio(a, autoplay=True)

    if img_file: st.rerun()