import streamlit as st
import asyncio
import os
import edge_tts
import base64
import time
import requests
from PIL import Image
from io import BytesIO
from groq import Groq
from duckduckgo_search import DDGS

# ============================================================
# CONFIGURACIÓN Y LLAVES
# ============================================================
st.set_page_config(page_title="Dalia AI 2.0", page_icon="🤖", layout="centered")

# IMPORTANTE: Asegúrate de que en Streamlit Cloud tengas tu llave
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
VOZ_HUMANA = "es-MX-DaliaNeural"
client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# SISTEMA DE ACCESO
# ============================================================
USUARIOS = {"leo123": "Leonardo", "chris123": "Christian", "manu123": "Manuel"}

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
# ESTADOS Y PERSONALIDAD
# ============================================================
nombre_usuario = st.session_state.usuario_nombre

if "modo_actual" not in st.session_state: st.session_state.modo_actual = "normal"
if "voz_activa" not in st.session_state: st.session_state.voz_activa = True
if "historiales" not in st.session_state: st.session_state.historiales = {"normal": [], "matematica": [], "code": []}
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "saludo_dado" not in st.session_state: st.session_state.saludo_dado = False

INSTRUCCIONES = {
    "normal": f"Eres Dalia, asistente de {nombre_usuario}. Eres alegre y un poco tímida. Hablas natural (o sea, claro).",
    "matematica": "Eres Dalia modo MATEMÁTICA. Resumen, Datos, Desarrollo, Resultado y Comprobación.",
    "code": "Eres Dalia modo CODE. Código limpio y bien explicado.",
    "vision": "Analiza la imagen detalladamente para Leonardo."
}


# ============================================================
# HERRAMIENTAS ARREGLADAS
# ============================================================

def buscar_imagen_en_web(query):
    """Busca fotos reales en internet."""
    try:
        # Limpiamos la pregunta para que la búsqueda sea mejor
        for p in ["busca una imagen de", "muéstrame", "enséñame", "foto de", "internet de"]:
            query = query.lower().replace(p, "")

        with DDGS() as ddgs:
            resultados = list(ddgs.images(query.strip(), max_results=5))
            if resultados:
                return resultados[0]['image']
        return None
    except:
        return None


def procesar_imagen_segura(img_file):
    img = Image.open(img_file)
    if img.mode != "RGB": img = img.convert("RGB")
    img.thumbnail((800, 800))  # Más pequeña para evitar errores
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=75)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def analizar_vision_actualizada(imagen_b64, prompt=""):
    """Cambiamos al modelo Llama 3.2 90B que NO está apagado."""
    try:
        # Usamos el modelo 90B que es más potente y sigue activo
        response = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[
                {"role": "user", "content": [
                    {"type": "text", "text": prompt if prompt else "Describe esto."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagen_b64}"}}
                ]}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Dalia dice: Hubo un lío con el servidor de Groq ({e})."


async def hablar(texto):
    t = texto.replace('*', '').replace('#', '')
    archivo = f"voz_{int(time.time())}.mp3"
    try:
        com = edge_tts.Communicate(t[:250], VOZ_HUMANA)
        await com.save(archivo)
        return archivo
    except:
        return None


# ============================================================
# INTERFAZ (UI)
# ============================================================
st.markdown("<h1 style='text-align: center; color: #a78bfa;'>🤖 Dalia AI</h1>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💬 Normal"): st.session_state.modo_actual = "normal"
with col2:
    if st.button("📐 Mate"): st.session_state.modo_actual = "matematica"
with col3:
    if st.button("💻 Code"): st.session_state.modo_actual = "code"
with col4:
    if st.button("🔊 Voz" if st.session_state.voz_activa else "🔇 Voz"):
        st.session_state.voz_activa = not st.session_state.voz_activa
        st.rerun()

# Chat
for m in st.session_state.historiales[st.session_state.modo_actual]:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if not st.session_state.saludo_dado:
    saludo = f"¡Hola {nombre_usuario}! Mi caramelito de chocolate 💜 ¿Qué investigamos hoy?"
    with st.chat_message("assistant"): st.markdown(saludo)
    st.session_state.saludo_dado = True

# SUBIR FOTO
img_input = st.file_uploader("📷 Sube algo aquí", type=['png', 'jpg', 'jpeg'], key=f"up_{st.session_state.uploader_key}")

# INPUT PRINCIPAL
if prompt := st.chat_input("Dime algo..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # 1. Si hay imagen subida
        if img_input:
            with st.spinner("Dalia está mirando..."):
                b64 = procesar_imagen_segura(img_input)
                res = analizar_vision_actualizada(b64, prompt)
                st.session_state.uploader_key += 1

        # 2. Si pides BUSCAR una imagen (Filtro mejorado)
        elif any(x in prompt.lower() for x in ["busca una imagen", "foto de", "muéstrame", "enséñame"]):
            with st.spinner("Buscando en internet..."):
                url = buscar_imagen_en_web(prompt)
                if url:
                    st.image(url)
                    res = f"¡Mira {nombre_usuario}! Encontré esto para ti. ¿Es lo que buscabas?"
                else:
                    res = "No encontré imágenes recientes, pero puedo buscarte info si quieres."

        # 3. Chat normal
        else:
            with st.spinner("Pensando..."):
                st.session_state.historiales[st.session_state.modo_actual].append({"role": "user", "content": prompt})
                comp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": INSTRUCCIONES[st.session_state.modo_actual]},
                              *st.session_state.historiales[st.session_state.modo_actual]]
                )
                res = comp.choices[0].message.content

        st.markdown(res)
        st.session_state.historiales[st.session_state.modo_actual].append({"role": "assistant", "content": res})

        if st.session_state.voz_activa:
            a = asyncio.run(hablar(res))
            if a: st.audio(a, autoplay=True)

    if img_input: st.rerun()