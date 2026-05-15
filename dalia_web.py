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

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
VOZ_HUMANA = "es-MX-DaliaNeural"
client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# SISTEMA DE ACCESO SECRETO (LOGIN)
# ============================================================
# Aquí defines las contraseñas y a quién pertenecen
USUARIOS = {
    "leo123": "Leonardo",
    "chris123": "Christian",
    "manu123": "Manuel"
}

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_nombre = ""

# Si no están autenticados, solo ven esta pantalla
if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center; color: #a78bfa;'>🔐 Acceso a Dalia AI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Ingresa tu código para hablar con Dalia.</p>", unsafe_allow_html=True)

    codigo = st.text_input("Código secreto:", type="password")

    if st.button("Entrar", use_container_width=True):
        if codigo in USUARIOS:
            st.session_state.autenticado = True
            st.session_state.usuario_nombre = USUARIOS[codigo]
            st.rerun()
        else:
            st.error("Código incorrecto. Pregúntale a Leonardo cuál es tu clave.")

    st.stop()  # Esto detiene la app para que no puedan ver nada más abajo

# ============================================================
# SI PASA DE AQUÍ, YA INICIÓ SESIÓN
# ============================================================
nombre_usuario = st.session_state.usuario_nombre

# ESTADOS DE SESIÓN (Memoria de Dalia)
if "modo_actual" not in st.session_state: st.session_state.modo_actual = "normal"
if "voz_activa" not in st.session_state: st.session_state.voz_activa = True
if "historiales" not in st.session_state: st.session_state.historiales = {"normal": [], "matematica": [], "code": []}
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0
if "saludo_dado" not in st.session_state: st.session_state.saludo_dado = False

# INSTRUCCIONES PERSONALIZADAS (Dalia sabe con quién habla)
INSTRUCCIONES = {
    "normal": (
        f"Eres Dalia, asistente personal de {nombre_usuario}. Eres una chica joven, inteligente, amable, alegre y un poco tímida. "
        "Hablas de forma natural y relajada. Usas expresiones: 'claro', 'la verdad', 'o sea', 'está bien difícil'. "
        "Cuando busques en internet sintetiza y da la respuesta más completa. "
        "SOLO responde lo que preguntan. Sin frases de relleno. Responde y punto."
    ),
    "matematica": (
        "Eres Dalia en modo MATEMÁTICA 2.0. Experta en ingeniería. PASOS: 1. RESUMEN. 2. DATOS. 3. DESARROLLO paso a paso. 4. RESULTADO. 5. COMPROBACIÓN."
    ),
    "code": (
        "Eres Dalia en modo CODE. Experta en programación. Explica qué hace el código, escríbelo limpio y comenta lo importante."
    ),
    "vision": (
        "Eres Dalia analizando una imagen. Describe detalladamente objetos, personas, colores y texto de forma natural y amigable."
    )
}

# SALUDO DINÁMICO
SALUDO_INICIO = f"¡Hola {nombre_usuario}! Mi caramelito de chocolate 💜 Me alegra que estés aquí. Soy Dalia, tu asistente personal. ¿En qué te puedo ayudar hoy?"


# ============================================================
# FUNCIONES DE APOYO
# ============================================================
def agregar_al_historial(rol, contenido):
    st.session_state.historiales[st.session_state.modo_actual].append({"role": rol, "content": contenido})
    if len(st.session_state.historiales[st.session_state.modo_actual]) > 20:
        st.session_state.historiales[st.session_state.modo_actual].pop(0)


def encode_image_pil(pil_img):
    if pil_img.mode in ("RGBA", "P", "LA"): pil_img = pil_img.convert("RGB")
    buffer = BytesIO()
    pil_img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def analizar_imagen_groq(imagen_b64, prompt=""):
    try:
        modelo_vision = "llama-3.2-11b-vision-preview"
        system_prompt = INSTRUCCIONES["vision"]
        texto_usuario = prompt if prompt else "Analiza esta imagen detalladamente."

        response = client.chat.completions.create(
            model=modelo_vision,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "text", "text": texto_usuario},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagen_b64}"}}
                ]}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Dalia dice: Hubo un detalle con la imagen (Error: {e})"


def buscar_internet(query):
    try:
        fuentes = []
        textos = []
        with DDGS() as ddgs:
            resultados = list(ddgs.text(query, max_results=5, region="mx-es"))
            for r in resultados:
                textos.append(f"- {r['title']}: {r['body']}")
                fuentes.append(r.get('href', ''))
        return "\n".join(textos), [f.split('/')[2] for f in fuentes if f][:4]
    except:
        return None, []


async def generar_audio(texto):
    t = texto.replace('*', '').replace('#', '')
    archivo = f"audio_{int(time.time())}.mp3"
    try:
        com = edge_tts.Communicate(t, VOZ_HUMANA)
        await com.save(archivo)
        return archivo
    except:
        return None


# ============================================================
# INTERFAZ PRINCIPAL (UI)
# ============================================================
st.markdown("<h1 style='text-align: center; color: #a78bfa;'>🤖 Dalia AI</h1>", unsafe_allow_html=True)

# Botones de Modo
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💬 Normal"): st.session_state.modo_actual = "normal"
with col2:
    if st.button("📐 Mate"): st.session_state.modo_actual = "matematica"
with col3:
    if st.button("💻 Code"): st.session_state.modo_actual = "code"
with col4:
    icon_v = "🔊" if st.session_state.voz_activa else "🔇"
    if st.button(f"{icon_v} Voz"):
        st.session_state.voz_activa = not st.session_state.voz_activa
        st.rerun()

st.caption(f"Modo actual: {st.session_state.modo_actual.upper()}")

# Mostrar Historial
for msj in st.session_state.historiales[st.session_state.modo_actual]:
    with st.chat_message(msj["role"]):
        st.markdown(msj["content"])

# Saludo inicial
if not st.session_state.saludo_dado:
    with st.chat_message("assistant"):
        st.markdown(SALUDO_INICIO)
        if st.session_state.voz_activa:
            audio_file = asyncio.run(generar_audio(SALUDO_INICIO))
            if audio_file: st.audio(audio_file, autoplay=True)
    st.session_state.saludo_dado = True

# Subida de imagen
img_file = st.file_uploader("📷 Sube una foto para Dalia", type=['png', 'jpg', 'jpeg'],
                            key=f"up_{st.session_state.uploader_key}")

# Entrada de Chat
if prompt := st.chat_input("Escribe tu mensaje..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        respuesta_dalia = ""
        fuentes_url = []

        # IMAGEN
        if img_file:
            with st.spinner("Dalia está mirando la foto..."):
                img_pil = Image.open(img_file)
                b64 = encode_image_pil(img_pil)
                respuesta_dalia = analizar_imagen_groq(b64, prompt)
                st.session_state.uploader_key += 1

                # INTERNET
        elif st.session_state.modo_actual == "normal" and any(
                p in prompt.lower() for p in ["busca", "qué es", "quién es", "noticias"]):
            with st.spinner("Investigando en la web..."):
                info, fuentes_url = buscar_internet(prompt)
                contexto = f"INFO INTERNET: {info}\n\n{nombre_usuario} pregunta: {prompt}"
                agregar_al_historial("user", contexto)

                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": INSTRUCCIONES["normal"]},
                              *st.session_state.historiales["normal"]]
                )
                respuesta_dalia = resp.choices[0].message.content

        # CHAT NORMAL
        else:
            agregar_al_historial("user", prompt)
            with st.spinner("Escribiendo..."):
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": INSTRUCCIONES[st.session_state.modo_actual]},
                              *st.session_state.historiales[st.session_state.modo_actual]]
                )
                respuesta_dalia = resp.choices[0].message.content

        st.markdown(respuesta_dalia)
        if fuentes_url: st.caption(f"🔍 Fuentes: {' | '.join(fuentes_url)}")

        if st.session_state.voz_activa:
            audio_file = asyncio.run(generar_audio(respuesta_dalia))
            if audio_file:
                st.audio(audio_file, autoplay=True)
                if os.path.exists(audio_file): os.remove(audio_file)

        agregar_al_historial("assistant", respuesta_dalia)

    if img_file: st.rerun()