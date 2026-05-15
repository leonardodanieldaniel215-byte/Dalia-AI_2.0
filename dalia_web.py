import streamlit as st
import asyncio
import base64
import os
import time
from io import BytesIO

import edge_tts
import requests
from groq import Groq
from ddgs import DDGS
from PIL import Image
import speech_recognition as sr

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(page_title="Dalia", page_icon="🤖", layout="centered")

# ============================================================
# CSS CUSTOM — ESTÉTICA ORIGINAL + BARRA TIPO CHATGPT EXACTA
# ============================================================
st.markdown("""
<style>
    /* Fondo general negro */
    .stApp {
        background-color: #000000 !important;
    }

    /* Texto general */
    html, body, [class*="css"] {
        color: #e2e2e2 !important;
        font-family: 'Arial', sans-serif !important;
    }

    /* Título principal */
    h1, h2, h3 {
        color: #a78bfa !important;
        font-weight: bold !important;
        text-align: center !important;
    }

    /* Chat messages */
    .stChatMessage {
        background-color: #0d0d0d !important;
        border-radius: 12px !important;
        border: 1px solid #2a2a3e !important;
    }

    /* Caption/fuentes */
    .stCaption {
        color: #4f9cf9 !important;
        font-size: 0.85em !important;
    }

    /* Spinner */
    .stSpinner > div {
        color: #a78bfa !important;
    }

    /* Divider */
    hr {
        border-color: #2a2a3e !important;
    }

    /* Login card */
    .login-card {
        background-color: #0d0d0d !important;
        border: 1px solid #2a2a3e !important;
        border-radius: 16px !important;
        padding: 40px !important;
        max-width: 400px !important;
        margin: 0 auto !important;
        text-align: center !important;
    }

    /* Scrollbar oscura */
    ::-webkit-scrollbar {
        width: 8px !important;
    }
    ::-webkit-scrollbar-track {
        background: #000000 !important;
    }
    ::-webkit-scrollbar-thumb {
        background: #3e3e5e !important;
        border-radius: 4px !important;
    }

    /* Creador badge */
    .creator-badge {
        background: linear-gradient(135deg, #7c3aed, #a78bfa) !important;
        color: white !important;
        padding: 2px 10px !important;
        border-radius: 12px !important;
        font-size: 0.75em !important;
        font-weight: bold !important;
        margin-left: 8px !important;
    }

    /* ==========================================
       BARRA TIPO CHATGPT — EXACTA A LA IMAGEN
       ========================================== */

    /* Contenedor padre de la barra */
    .chatgpt-bar-wrapper {
        background-color: #2d2d2d !important;
        border-radius: 24px !important;
        padding: 6px 10px !important;
        border: 1px solid #3e3e3e !important;
        display: flex !important;
        align-items: center !important;
        margin-bottom: 20px !important;
    }

    /* Input de texto — sin bordes, fondo transparente */
    .chatgpt-bar-wrapper .stTextInput > div > div > input {
        background: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 15px !important;
        padding: 8px 4px !important;
        box-shadow: none !important;
    }
    .chatgpt-bar-wrapper .stTextInput > div > div > input::placeholder {
        color: #9ca3af !important;
    }

    /* Botón + (popover trigger) */
    .chatgpt-bar-wrapper div[data-testid="stPopover"] > button {
        background: transparent !important;
        border: none !important;
        color: #e2e2e2 !important;
        font-size: 22px !important;
        padding: 0 !important;
        width: 32px !important;
        height: 32px !important;
        border-radius: 50% !important;
    }
    .chatgpt-bar-wrapper div[data-testid="stPopover"] > button:hover {
        background: #3e3e3e !important;
    }
    .chatgpt-bar-wrapper div[data-testid="stPopover"] > button p {
        font-size: 0px !important;
    }
    .chatgpt-bar-wrapper div[data-testid="stPopover"] > button::before {
        content: "➕" !important;
        font-size: 18px !important;
    }

    /* Botón micrófono */
    .chatgpt-bar-wrapper .btn-mic .stButton > button {
        background: transparent !important;
        border: none !important;
        color: #e2e2e2 !important;
        font-size: 18px !important;
        padding: 0 !important;
        width: 32px !important;
        height: 32px !important;
        border-radius: 50% !important;
    }
    .chatgpt-bar-wrapper .btn-mic .stButton > button:hover {
        background: #3e3e3e !important;
    }

    /* Botón enviar circular (derecha) */
    .chatgpt-bar-wrapper .btn-send .stButton > button {
        background: #e2e2e2 !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 50% !important;
        width: 32px !important;
        height: 32px !important;
        font-size: 14px !important;
        padding: 0 !important;
        font-weight: bold !important;
    }
    .chatgpt-bar-wrapper .btn-send .stButton > button:hover {
        background: #ffffff !important;
    }

    /* Popover menu */
    div[data-testid="stPopoverPopover"] {
        background-color: #1a1a1a !important;
        border: 1px solid #3e3e3e !important;
        border-radius: 12px !important;
    }

    /* Modo label arriba del chat */
    .modo-label-top {
        text-align: center !important;
        font-weight: bold !important;
        font-size: 1em !important;
        margin-bottom: 10px !important;
        padding: 4px 12px !important;
        border-radius: 16px !important;
        display: inline-block !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CREDENCIALES Y CLIENTES
# ============================================================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "PON-TU-KEY-AQUÍ")
VOZ_HUMANA = "es-MX-DaliaNeural"
client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# USUARIOS AUTORIZADOS
# ============================================================
USUARIOS = {
    "chris123": "CHRISTIAN",
    "emanu123": "EMMANUEL",
    "leo123": "LEONARDO"
}

# ============================================================
# INSTRUCCIONES (IGUALES QUE TU ORIGINAL)
# ============================================================
INSTRUCCION_NORMAL = (
    "Eres Dalia, asistente personal de Leonardo. "
    "Eres una chica joven, inteligente, amable, alegre y un poco tímida. "
    "Hablas de forma natural y relajada, como una persona normal. "
    "Usas expresiones cotidianas: 'claro', 'exacto', 'mira', 'la verdad', "
    "'te digo', 'o sea', 'está bien difícil'. "
    "Cuando buscas en internet analiza bien toda la información antes de responder. "
    "Sintetiza, compara y da la respuesta más completa posible. "
    "SOLO responde lo que preguntan. Sin frases de relleno. Responde y punto."
)

INSTRUCCION_MATEMATICA = (
    "Eres Dalia en modo MATEMÁTICA 2.0. Experta en matemáticas, física e ingeniería. "
    "PASOS: "
    "1. RESUMEN: Una frase explicando qué vamos a hacer. "
    "2. DATOS: Lista clara de los valores. "
    "3. DESARROLLO: Paso a paso explicando POR QUÉ haces cada paso. "
    "4. RESULTADO: Resultado final con unidades. "
    "5. COMPROBACIÓN: Por qué el resultado tiene sentido. "
    "Sin frases de relleno, solo ve al grano."
)

INSTRUCCION_CODE = (
    "Eres Dalia en modo CODE. Experta en todos los lenguajes de programación. "
    "Cuando te pidan código: "
    "1. Explica brevemente qué hace. "
    "2. Escribe el código limpio y bien comentado. "
    "3. Explica las partes importantes. "
    "4. Si hay errores, encuéntralos y corrígelos. "
    "5. Si te mandan imagen con código o error, analízala y da la solución. "
    "Habla de forma clara y directa. Sin frases de relleno."
)

INSTRUCCION_VISION = (
    "Eres Dalia analizando una imagen. "
    "Describe detalladamente lo que ves: objetos, personas, colores, texto, contexto. "
    "Si es un diagrama o esquema técnico, explica qué representa. "
    "Si es código, analízalo. Si es un error, explica qué significa. "
    "Si es una foto cotidiana, descríbela de forma natural y amigable. "
    "Habla de forma clara, natural y directa."
)


# ============================================================
# ESTADO GLOBAL (SESSION STATE)
# ============================================================
def init_state():
    defaults = {
        "authenticated": False,
        "username": "",
        "modo_actual": "normal",
        "voz_activa": True,
        "imagen_pil": None,
        "messages": [],
        "historiales": {"normal": [], "matematica": [], "code": []},
        "input_texto": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ============================================================
# HISTORIALES
# ============================================================
def agregar_al_historial(rol, contenido):
    modo = st.session_state.modo_actual
    st.session_state.historiales[modo].append({"role": rol, "content": contenido})
    if len(st.session_state.historiales[modo]) > 20:
        st.session_state.historiales[modo].pop(0)


# ============================================================
# IMAGEN — ENCODE
# ============================================================
def encode_image_path(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode('utf-8')


def encode_image_pil(pil_img):
    if pil_img.mode in ("RGBA", "P", "LA"):
        pil_img = pil_img.convert("RGB")
    buffer = BytesIO()
    pil_img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


# ============================================================
# ANALIZAR IMAGEN CON GROQ VISION
# ============================================================
def analizar_imagen(imagen_b64, prompt=""):
    try:
        if st.session_state.modo_actual == "code":
            system = INSTRUCCION_CODE
        elif st.session_state.modo_actual == "matematica":
            system = INSTRUCCION_MATEMATICA
        else:
            system = INSTRUCCION_VISION

        texto = prompt if prompt else "Analiza esta imagen detalladamente y describe todo lo que ves."

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            max_tokens=1000,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": [
                    {"type": "text", "text": texto},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{imagen_b64}"
                    }}
                ]}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"No pude analizar la imagen: {e}"


# ============================================================
# BUSCAR IMAGEN EN INTERNET
# ============================================================
def buscar_imagen_internet(query):
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.images(query, max_results=8, region="mx-es"))
        for r in resultados:
            try:
                url = r.get("image", "")
                if not url:
                    continue
                resp = requests.get(url, timeout=5,
                                    headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    img = Image.open(BytesIO(resp.content))
                    return img, url
            except:
                continue
        return None, None
    except Exception as e:
        return None, None


def necesita_imagen_internet(texto):
    palabras = ["muéstrame una imagen", "muestrame una imagen",
                "busca una imagen", "busca imagen",
                "imagen de", "foto de", "muéstrame",
                "muestrame", "quiero ver", "dame una imagen",
                "ponme una imagen", "busca foto"]
    return any(p in texto.lower() for p in palabras)


def extraer_query_imagen(texto):
    t = texto.lower()
    for p in ["muéstrame una imagen de", "muestrame una imagen de",
              "busca una imagen de", "busca imagen de",
              "imagen de", "foto de", "muéstrame de",
              "muestrame de", "quiero ver", "dame una imagen de",
              "ponme una imagen de", "busca foto de"]:
        t = t.replace(p, "").strip()
    return t if t else texto


# ============================================================
# INTERNET — TEXTO
# ============================================================
def buscar_internet(query):
    try:
        fuentes = []
        textos = []
        with DDGS() as ddgs:
            resultados = list(ddgs.text(query, max_results=6, region="mx-es"))
            for r in resultados:
                textos.append(f"- {r['title']}: {r['body']}")
                fuentes.append(r.get('href', ''))
            try:
                noticias = list(ddgs.news(query, max_results=3, region="mx-es"))
                for n in noticias:
                    textos.append(f"- [Noticia] {n['title']}: {n['body']}")
                    fuentes.append(n.get('url', ''))
            except:
                pass
        fuentes_limpias = []
        for f in fuentes:
            if f:
                try:
                    dominio = f.split('/')[2].replace('www.', '')
                    if dominio not in fuentes_limpias:
                        fuentes_limpias.append(dominio)
                except:
                    pass
        return "\n".join(textos), fuentes_limpias[:5]
    except:
        return None, []


def necesita_buscar(texto):
    palabras = ["busca", "investiga", "qué es", "que es", "googlea",
                "noticias", "precio de", "quién es", "quien es",
                "qué pasó", "que paso", "actualmente", "dónde", "donde"]
    return any(p in texto.lower() for p in palabras)


def extraer_query(texto):
    query = texto.lower()
    for p in ["busca", "investiga", "googlea", "qué es", "que es",
              "quién es", "quien es", "noticias de"]:
        query = query.replace(p, "").strip()
    return query if query else texto


# ============================================================
# PREGUNTAR A DALIA (LÓGICA ORIGINAL PRESERVADA)
# ============================================================
def preguntar_a_dalia(mensaje, imagen_b64=None):
    contexto_extra = ""
    fuentes = []

    # ── Con imagen — análisis visual ──
    if imagen_b64:
        respuesta = analizar_imagen(imagen_b64, mensaje)
        return respuesta, [], None

    # ── Buscar imagen en internet ──
    if necesita_imagen_internet(mensaje):
        query_img = extraer_query_imagen(mensaje)
        img, fuente = buscar_imagen_internet(query_img)
        if img:
            return f"Aquí está la imagen de: {query_img} 🔍", [], img
        return "No encontré ninguna imagen de eso, intenta con otras palabras.", [], None

    # ── Búsqueda de texto ──
    if st.session_state.modo_actual == "normal" and necesita_buscar(mensaje):
        query = extraer_query(mensaje)
        info, fuentes = buscar_internet(query)
        if info:
            contexto_extra = (
                f"[Información de internet sobre '{query}']:\n{info}\n\n"
                f"Analiza bien toda esta información antes de responder.\n\n"
            )

    mensaje_final = f"{contexto_extra}Leonardo: {mensaje}"
    agregar_al_historial("user", mensaje_final)

    if st.session_state.modo_actual == "matematica":
        system = INSTRUCCION_MATEMATICA
    elif st.session_state.modo_actual == "code":
        system = INSTRUCCION_CODE
    else:
        system = INSTRUCCION_NORMAL

    max_tok = 1200 if st.session_state.modo_actual in ("matematica", "code") else 600

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=max_tok,
        messages=[
            {"role": "system", "content": system},
            *st.session_state.historiales[st.session_state.modo_actual]
        ]
    )

    respuesta = response.choices[0].message.content.strip()
    agregar_al_historial("assistant", respuesta)
    return respuesta, fuentes, None


# ============================================================
# VOZ (ADAPTADA A STREAMLIT)
# ============================================================
async def _generar_audio_async(texto):
    t = texto.replace('*', '').replace('#', '')
    archivo = f"temp_voz_{abs(hash(t)) % 100000}.mp3"
    com = edge_tts.Communicate(t, VOZ_HUMANA)
    await com.save(archivo)
    return archivo


def hablar(texto):
    if not st.session_state.voz_activa:
        return
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        archivo = loop.run_until_complete(_generar_audio_async(texto))
        st.audio(archivo, format="audio/mp3", autoplay=True)
    except Exception as e:
        st.toast(f"🔇 Error de voz: {e}")


# ============================================================
# LOGIN — PANTALLA DE ACCESO
# ============================================================
if not st.session_state.authenticated:
    st.markdown("""
        <div class="login-card">
            <h1 style="color:#a78bfa; margin-bottom:5px;">🤖 Dalia</h1>
            <p style="color:#a78bfa; font-size:0.95em; margin-bottom:25px;">
                Solo para amigos autorizados 💜
            </p>
        </div>
    """, unsafe_allow_html=True)

    with st.container():
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            password = st.text_input(
                "🔑 Contraseña",
                type="password",
                label_visibility="collapsed",
                placeholder="Escribe tu contraseña..."
            )

            if st.button("Entrar", use_container_width=True):
                if password in USUARIOS:
                    st.session_state.authenticated = True
                    st.session_state.username = USUARIOS[password]
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta. No eres de los míos 😢")

    st.stop()

# ============================================================
# INTERFAZ PRINCIPAL
# ============================================================
nombre_amigo = st.session_state.username
es_creador = (nombre_amigo == "LEONARDO")

# Saludo personalizado
if es_creador:
    SALUDO_INICIO = (
        f"Hola mi creador {nombre_amigo}! 💜✨ Mi caramelito de chocolate favorito. "
        f"Me alegra verte aquí. Soy Dalia, tu asistente personal. "
        f"Puedo platicar contigo, buscar en internet, "
        f"resolver matemáticas, ayudarte con código, "
        f"analizar imágenes y buscar fotos de lo que necesites. "
        f"¿En qué te puedo ayudar hoy, jefe? 😊"
    )
else:
    SALUDO_INICIO = (
        f"Hola {nombre_amigo}! Mi caramelito de chocolate 💜 Me alegra que estés aquí. "
        f"Soy Dalia, tu asistente personal. "
        f"Puedo platicar contigo, buscar en internet, "
        f"resolver matemáticas, ayudarte con código, "
        f"analizar imágenes y buscar fotos de lo que necesites. "
        f"¿En qué te puedo ayudar hoy?"
    )

# Título principal
if es_creador:
    st.markdown(
        f"<h2 style='text-align:center;'>🤖 Dalia <span class='creator-badge'>CREADOR</span></h2>",
        unsafe_allow_html=True
    )
else:
    st.markdown("<h2 style='text-align:center;'>🤖 Dalia</h2>", unsafe_allow_html=True)

st.markdown(
    f"<p style='text-align:center; color:#a78bfa;'>Bienvenido, <b>{nombre_amigo}</b> 💜</p>",
    unsafe_allow_html=True
)

# ============================================================
# SIDEBAR — CONTROLES ADICIONALES
# ============================================================
with st.sidebar:
    st.markdown("<h3 style='color:#a78bfa;'>⚙️ Controles</h3>", unsafe_allow_html=True)

    # Toggle voz
    st.session_state.voz_activa = st.toggle(
        "🔊 Voz: ON" if st.session_state.voz_activa else "🔇 Voz: OFF",
        value=st.session_state.voz_activa
    )

    st.divider()

    # Subir imagen desde sidebar también (opcional)
    st.markdown("<p style='color:#a78bfa; font-weight:bold;'>📷 O sube imagen aquí</p>", unsafe_allow_html=True)
    archivo_img_sidebar = st.file_uploader(
        "Sube imagen sidebar",
        type=["jpg", "jpeg", "png", "bmp", "webp"],
        label_visibility="collapsed",
        key="sidebar_uploader"
    )
    if archivo_img_sidebar:
        img = Image.open(archivo_img_sidebar)
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        st.session_state.imagen_pil = img
        st.image(img, caption="✅ Imagen lista", width=200)

    st.divider()

    if st.button("🚪 Cerrar sesión", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ============================================================
# INDICADOR DE MODO ACTUAL
# ============================================================
modos_colores = {
    "normal": ("💬 Normal", "#a78bfa", "#2a2a3e"),
    "matematica": ("📐 MATEMÁTICA 2.0", "#f59e0b", "#2a1a0a"),
    "code": ("💻 CODE", "#10b981", "#0a2a1a")
}
modo_txt, modo_color, modo_bg = modos_colores[st.session_state.modo_actual]

st.markdown(
    f"<div style='text-align:center;'><span class='modo-label-top' style='color:{modo_color}; background-color:{modo_bg}; border:1px solid {modo_color};'>"
    f"{modo_txt}</span></div>",
    unsafe_allow_html=True
)

# ============================================================
# CHAT — MENSAJES
# ============================================================
if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": SALUDO_INICIO})
    if st.session_state.voz_activa:
        hablar(SALUDO_INICIO)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(f"<span style='color:#34d399; font-weight:bold;'>🚀 Tú</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:#a78bfa; font-weight:bold;'>🤖 Dalia</span>", unsafe_allow_html=True)

        st.markdown(msg["content"])

        if msg.get("image"):
            st.image(msg["image"], width=350)
        if msg.get("fuentes"):
            st.caption("🔍 Fuentes: " + "  ".join([f"`{f}`" for f in msg["fuentes"]]))

# ============================================================
# BARRA TIPO CHATGPT EXACTA — [ + ] [ TEXTO ] [ 🎙️ ] [ ➤ ]
# ============================================================
st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

# Preview de imagen si hay una cargada desde el menú +
if st.session_state.imagen_pil:
    st.markdown(
        f"<p style='color:#34d399; font-size:0.9em; margin-bottom:5px;'>"
        f"📷 Imagen lista para enviar</p>",
        unsafe_allow_html=True
    )

# Contenedor con clase CSS para estilizar como barra ChatGPT
with st.container():
    st.markdown('<div class="chatgpt-bar-wrapper">', unsafe_allow_html=True)

    col_plus, col_texto, col_mic, col_enviar = st.columns([1, 10, 1, 1])

    with col_plus:
        # Menú popover con la cruseta +
        with st.popover("", use_container_width=True):
            st.markdown("<p style='color:#a78bfa; font-weight:bold; margin-bottom:10px;'>⚙️ Opciones</p>",
                        unsafe_allow_html=True)

            # Opciones de modo
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("💬 Normal", use_container_width=True, key="pop_normal"):
                    st.session_state.modo_actual = "normal"
                    st.rerun()
            with c2:
                if st.button("📐 MATE", use_container_width=True, key="pop_mate"):
                    st.session_state.modo_actual = "matematica"
                    st.rerun()
            with c3:
                if st.button("💻 CODE", use_container_width=True, key="pop_code"):
                    st.session_state.modo_actual = "code"
                    st.rerun()

            st.divider()

            # Subir imagen desde el menú +
            st.markdown("<p style='color:#a78bfa; font-weight:bold;'>📷 Subir imagen</p>", unsafe_allow_html=True)
            archivo_img_pop = st.file_uploader(
                "Selecciona imagen",
                type=["jpg", "jpeg", "png", "bmp", "webp"],
                label_visibility="collapsed",
                key="pop_uploader"
            )
            if archivo_img_pop:
                img = Image.open(archivo_img_pop)
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGB")
                st.session_state.imagen_pil = img
                st.success("✅ Imagen cargada. Cierra y escribe tu pregunta.")
                st.image(img, width=150)

    with col_texto:
        texto_input = st.text_input(
            "Mensaje",
            value=st.session_state.get("input_texto", ""),
            label_visibility="collapsed",
            placeholder="Preguntar a Dalia",
            key="texto_input"
        )

    with col_mic:
        st.markdown('<div class="btn-mic">', unsafe_allow_html=True)
        # Toggle rápido de voz al tocar el micrófono
        mic_emoji = "🎙️" if st.session_state.voz_activa else "🔇"
        if st.button(mic_emoji, key="btn_mic", use_container_width=True):
            st.session_state.voz_activa = not st.session_state.voz_activa
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col_enviar:
        st.markdown('<div class="btn-send">', unsafe_allow_html=True)
        enviar_btn = st.button("➤", key="btn_enviar", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# PROCESAR ENVÍO
# ============================================================
if enviar_btn and texto_input.strip():
    prompt = texto_input.strip()

    # Guardar mensaje usuario
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Preparar imagen si hay
    imagen_b64 = None
    if st.session_state.imagen_pil:
        imagen_b64 = encode_image_pil(st.session_state.imagen_pil)
        st.session_state.imagen_pil = None

    # Procesar respuesta
    with st.spinner("Dalia está pensando..."):
        respuesta, fuentes, img_result = preguntar_a_dalia(prompt, imagen_b64)

    # Guardar respuesta asistente
    msg_asistente = {
        "role": "assistant",
        "content": respuesta,
        "fuentes": fuentes
    }
    if img_result:
        msg_asistente["image"] = img_result
    st.session_state.messages.append(msg_asistente)

    # Voz
    if st.session_state.voz_activa:
        hablar(respuesta)

    # Limpiar input
    st.session_state.input_texto = ""
    st.rerun()