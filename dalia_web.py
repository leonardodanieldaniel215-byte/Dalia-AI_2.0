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
# CONFIGURACIÓN Y LLAVES (SECRETOS)
# ============================================================
st.set_page_config(page_title="Dalia AI", page_icon="🤖", layout="centered")

# IMPORTANTE: Asegúrate de tener GROQ_API_KEY en los Secrets de Streamlit
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
    codigo = st.text_input("Ingresa tu código secreto:", type="password")
    if st.button("Entrar", use_container_width=True):
        if codigo in USUARIOS:
            st.session_state.autenticado = True
            st.session_state.usuario_nombre = USUARIOS[codigo]
            st.rerun()
        else:
            st.error("Código incorrecto. Pídeselo a Leonardo.")
    st.stop()

# ============================================================
# PERSONALIDAD Y ESTADOS
# ============================================================
nombre_usuario = st.session_state.usuario_nombre

if "modo_actual" not in st.session_state: st.session_state.modo_actual = "normal"
if "voz_activa" not in st.session_state: st.session_state.voz_activa = True
if "historiales" not in st.session_state: st.session_state.historiales = {"normal": [], "matematica": [], "code": []}
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "saludo_dado" not in st.session_state: st.session_state.saludo_dado = False

# Instrucciones mejoradas del código de Claude
INSTRUCCIONES = {
    "normal": f"Eres Dalia, asistente de {nombre_usuario}. Eres joven, inteligente y un poco tímida. Hablas natural: 'claro', 'o sea', 'está bien difícil'. Sintetiza info de internet sin relleno.",
    "matematica": "Eres Dalia modo MATEMÁTICA. Estilo ingeniería: Resumen, Datos, Desarrollo paso a paso, Resultado y Comprobación.",
    "code": "Eres Dalia modo CODE. Experta en programación. Código limpio, comentarios útiles y solución de errores.",
    "vision": "Eres Dalia analizando una imagen. Describe detalladamente objetos, colores, texto y contexto de forma natural."
}

SALUDO_INICIO = f"¡Hola {nombre_usuario}! Mi caramelito de chocolate 💜 Me alegra que estés aquí. Soy Dalia. ¿Qué vamos a hacer hoy?"


# ============================================================
# FUNCIONES DE VISIÓN Y BÚSQUEDA (MEJORADAS)
# ============================================================
def procesar_imagen_para_groq(img_file):
    """Optimiza la imagen para evitar el Error 400 de tamaño."""
    img = Image.open(img_file)
    if img.mode != "RGB": img = img.convert("RGB")
    img.thumbnail((1024, 1024))  # Reducir tamaño si es muy grande
    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=80)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def analizar_imagen_groq(imagen_b64, prompt=""):
    """Lógica de visión mejorada."""
    try:
        # Elegir instrucción según el modo actual
        if st.session_state.modo_actual == "code":
            system = INSTRUCCIONES["code"]
        elif st.session_state.modo_actual == "matematica":
            system = INSTRUCCIONES["matematica"]
        else:
            system = INSTRUCCIONES["vision"]

        texto_query = prompt if prompt else "Analiza esta imagen detalladamente."

        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",  # Modelo de visión real y estable
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": [
                    {"type": "text", "text": texto_query},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagen_b64}"}}
                ]}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Lo siento {nombre_usuario}, hubo un problema con la imagen: {e}"


def buscar_imagen_en_web(query):
    """Nueva función para que Dalia busque fotos para ti."""
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.images(query, max_results=5))
            if resultados:
                return resultados[0]['image']  # Retorna la URL de la primera imagen
        return None
    except:
        return None


def buscar_texto_internet(query):
    try:
        textos = []
        with DDGS() as ddgs:
            res = list(ddgs.text(query, max_results=3, region="mx-es"))
            for r in res: textos.append(f"{r['title']}: {r['body']}")
        return "\n".join(textos)
    except:
        return None


async def generar_audio(texto):
    t = texto.replace('*', '').replace('#', '')
    archivo = f"temp_vo_{int(time.time())}.mp3"
    try:
        com = edge_tts.Communicate(t[:300], VOZ_HUMANA)
        await com.save(archivo)
        return archivo
    except:
        return None


# ============================================================
# INTERFAZ DE USUARIO (WEB)
# ============================================================
st.markdown("<h1 style='text-align: center; color: #a78bfa;'>🤖 Dalia AI</h1>", unsafe_allow_html=True)

# Botones de Control
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("💬 Normal"): st.session_state.modo_actual = "normal"
with c2:
    if st.button("📐 Mate"): st.session_state.modo_actual = "matematica"
with c3:
    if st.button("💻 Code"): st.session_state.modo_actual = "code"
with c4:
    icon = "🔊" if st.session_state.voz_activa else "🔇"
    if st.button(f"{icon} Voz"):
        st.session_state.voz_activa = not st.session_state.voz_activa
        st.rerun()

st.caption(f"Dalia está en modo: {st.session_state.modo_actual.upper()} | Usuario: {nombre_usuario}")

# Mostrar Historial
for m in st.session_state.historiales[st.session_state.modo_actual]:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Saludo Inicial
if not st.session_state.saludo_dado:
    with st.chat_message("assistant"):
        st.markdown(SALUDO_INICIO)
        if st.session_state.voz_activa:
            aud = asyncio.run(generar_audio(SALUDO_INICIO))
            if aud: st.audio(aud, autoplay=True)
    st.session_state.saludo_dado = True

# SUBIDA DE ARCHIVOS
img_subida = st.file_uploader("📷 Sube una foto o pega una captura", type=['png', 'jpg', 'jpeg'],
                              key=f"up_{st.session_state.uploader_key}")

# CHAT INPUT
if prompt := st.chat_input("Dime algo..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # CASO 1: HAY IMAGEN SUBIDA
        if img_subida:
            with st.spinner("Analizando imagen..."):
                b64 = procesar_imagen_para_groq(img_subida)
                respuesta = analizar_imagen_groq(b64, prompt)
                st.session_state.uploader_key += 1  # Reset uploader

        # CASO 2: PEDIR IMAGEN A INTERNET
        elif any(p in prompt.lower() for p in ["busca una imagen de", "muéstrame una foto de", "enséñame un"]):
            with st.spinner("Buscando imagen..."):
                url_img = buscar_imagen_en_web(prompt)
                if url_img:
                    st.image(url_img, caption=f"Resultado para: {prompt}")
                    respuesta = f"Aquí tienes la imagen que encontré de {prompt}. ¿Te gusta?"
                else:
                    respuesta = "No pude encontrar una imagen sobre eso."

        # CASO 3: BÚSQUEDA DE TEXTO O CHAT NORMAL
        else:
            with st.spinner("Dalia está pensando..."):
                contexto_web = ""
                if "busca" in prompt.lower() or "quién es" in prompt.lower():
                    info = buscar_texto_internet(prompt)
                    if info: contexto_web = f"INFORMACIÓN WEB: {info}\n\n"

                # Memoria
                st.session_state.historiales[st.session_state.modo_actual].append(
                    {"role": "user", "content": f"{contexto_web}{prompt}"})

                completions = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": INSTRUCCIONES[st.session_state.modo_actual]},
                              *st.session_state.historiales[st.session_state.modo_actual]]
                )
                respuesta = completions.choices[0].message.content

        # Mostrar respuesta y hablar
        st.markdown(respuesta)
        st.session_state.historiales[st.session_state.modo_actual].append({"role": "assistant", "content": respuesta})

        if st.session_state.voz_activa:
            aud = asyncio.run(generar_audio(respuesta))
            if aud: st.audio(aud, autoplay=True)

    if img_subida: st.rerun()