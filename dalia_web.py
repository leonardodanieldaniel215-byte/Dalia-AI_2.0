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
from duckduckgo_search import DDGS  # Optimizado para la versión actual

# ============================================================
# CONFIGURACIÓN (Optimizada para la nube)
# ============================================================
st.set_page_config(page_title="Dalia AI", page_icon="🤖", layout="centered")

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
VOZ_HUMANA = "es-MX-DaliaNeural"
client = Groq(api_key=GROQ_API_KEY)

# ============================================================
# ESTADOS DE SESIÓN (Reemplazan las listas globales de Tkinter)
# ============================================================
if "modo_actual" not in st.session_state: st.session_state.modo_actual = "normal"
if "voz_activa" not in st.session_state: st.session_state.voz_activa = True
if "historiales" not in st.session_state: st.session_state.historiales = {"normal": [], "matematica": [], "code": []}
if "uploader_key" not in st.session_state: st.session_state.uploader_key = 0

# ============================================================
# INSTRUCCIONES (Intactas)
# ============================================================
INSTRUCCION_NORMAL = (
    "Eres Dalia, asistente personal de Leonardo. Eres una chica joven, inteligente, amable, alegre y un poco tímida. "
    "Hablas de forma natural y relajada, como una persona normal. Usas expresiones cotidianas: 'claro', 'exacto', 'mira', 'la verdad', 'te digo', 'o sea', 'está bien difícil'. "
    "Cuando buscas en internet analiza bien toda la información antes de responder. Sintetiza, compara y da la respuesta más completa posible. "
    "SOLO responde lo que preguntan. Sin frases de relleno. Responde y punto."
)

INSTRUCCION_MATEMATICA = (
    "Eres Dalia en modo MATEMÁTICA 2.0. Experta en matemáticas, física e ingeniería. PASOS: "
    "1. RESUMEN: Una frase explicando qué vamos a hacer. "
    "2. DATOS: Lista clara de los valores. "
    "3. DESARROLLO: Paso a paso explicando POR QUÉ haces cada paso. "
    "4. RESULTADO: Resultado final con unidades. "
    "5. COMPROBACIÓN: Por qué el resultado tiene sentido. "
    "Sin frases de relleno, solo ve al grano."
)

INSTRUCCION_CODE = (
    "Eres Dalia en modo CODE. Experta en todos los lenguajes de programación. Cuando te pidan código: "
    "1. Explica brevemente qué hace. 2. Escribe el código limpio y bien comentado. 3. Explica las partes importantes. "
    "4. Si hay errores, encuéntralos y corrígelos. 5. Si te mandan imagen con código o error, analízala y da la solución. "
    "Habla de forma clara y directa. Sin frases de relleno."
)

INSTRUCCION_VISION = (
    "Eres Dalia analizando una imagen. Describe detalladamente lo que ves: objetos, personas, colores, texto, contexto. "
    "Si es un diagrama o esquema técnico, explica qué representa. Si es código, analízalo. Si es un error, explica qué significa. "
    "Si es una foto cotidiana, descríbela de forma natural y amigable. Habla de forma clara, natural y directa."
)


# ============================================================
# FUNCIONES LÓGICAS (Intactas)
# ============================================================
def agregar_al_historial(rol, contenido):
    st.session_state.historiales[st.session_state.modo_actual].append({"role": rol, "content": contenido})
    if len(st.session_state.historiales[st.session_state.modo_actual]) > 20:
        st.session_state.historiales[st.session_state.modo_actual].pop(0)


def encode_image_pil(pil_img):
    if pil_img.mode in ("RGBA", "P", "LA"):
        pil_img = pil_img.convert("RGB")
    buffer = BytesIO()
    pil_img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def analizar_imagen(imagen_b64, prompt=""):
    try:
        modo = st.session_state.modo_actual
        if modo == "code":
            system = INSTRUCCION_CODE
        elif modo == "matematica":
            system = INSTRUCCION_MATEMATICA
        else:
            system = INSTRUCCION_VISION

        texto = prompt if prompt else "Analiza esta imagen detalladamente y describe todo lo que ves."

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",  # Usando tu modelo exacto
            max_tokens=1000,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": [
                    {"type": "text", "text": texto},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagen_b64}"}}
                ]}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"No pude analizar la imagen: {e}"


def buscar_imagen_internet(query):
    try:
        with DDGS() as ddgs:
            resultados = list(ddgs.images(query, max_results=8, region="mx-es"))
        for r in resultados:
            try:
                url = r.get("image", "")
                if not url: continue
                resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200:
                    img = Image.open(BytesIO(resp.content))
                    return img, url
            except:
                continue
        return None, None
    except Exception as e:
        print(f"Error buscando imagen: {e}")
        return None, None


def necesita_imagen_internet(texto):
    palabras = ["muéstrame una imagen", "muestrame una imagen", "busca una imagen", "busca imagen", "imagen de",
                "foto de", "muéstrame", "muestrame", "quiero ver", "dame una imagen", "ponme una imagen", "busca foto"]
    return any(p in texto.lower() for p in palabras)


def extraer_query_imagen(texto):
    t = texto.lower()
    for p in ["muéstrame una imagen de", "muestrame una imagen de", "busca una imagen de", "busca imagen de",
              "imagen de", "foto de", "muéstrame de", "muestrame de", "quiero ver", "dame una imagen de",
              "ponme una imagen de", "busca foto de"]:
        t = t.replace(p, "").strip()
    return t if t else texto


def buscar_internet(query):
    try:
        fuentes = []
        textos = []
        with DDGS() as ddgs:
            resultados = list(ddgs.text(query, max_results=6, region="mx-es"))
            for r in resultados:
                textos.append(f"- {r['title']}: {r['body']}")
                fuentes.append(r.get('href', ''))
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
    palabras = ["busca", "investiga", "qué es", "que es", "googlea", "noticias", "precio de", "quién es", "quien es",
                "qué pasó", "que paso", "actualmente", "dónde", "donde"]
    return any(p in texto.lower() for p in palabras)


def extraer_query(texto):
    query = texto.lower()
    for p in ["busca", "investiga", "googlea", "qué es", "que es", "quién es", "quien es", "noticias de"]:
        query = query.replace(p, "").strip()
    return query if query else texto


# ============================================================
# VOZ EDGE-TTS (Adaptado para la web)
# ============================================================
async def generar_audio(texto):
    t = texto.replace('*', '').replace('#', '')
    archivo = f"audio_{int(time.time())}.mp3"
    try:
        com = edge_tts.Communicate(t, VOZ_HUMANA)
        await com.save(archivo)
        return archivo
    except Exception as e:
        print(f"Error voz: {e}")
        return None


# ============================================================
# INTERFAZ STREAMLIT
# ============================================================
st.markdown("<h1 style='text-align: center; color: #a78bfa;'>🤖 Dalia AI</h1>", unsafe_allow_html=True)

# Botones de Modos
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("💬 Normal", use_container_width=True): st.session_state.modo_actual = "normal"
with col2:
    if st.button("📐 Mate", use_container_width=True): st.session_state.modo_actual = "matematica"
with col3:
    if st.button("💻 Code", use_container_width=True): st.session_state.modo_actual = "code"
with col4:
    estado_voz = "🔊 ON" if st.session_state.voz_activa else "🔇 OFF"
    if st.button(f"Voz: {estado_voz}", use_container_width=True):
        st.session_state.voz_activa = not st.session_state.voz_activa
        st.rerun()

st.markdown(f"<p style='text-align: center; color: #a78bfa;'>MODO ACTUAL: {st.session_state.modo_actual.upper()}</p>",
            unsafe_allow_html=True)

# Historial
for msj in st.session_state.historiales[st.session_state.modo_actual]:
    with st.chat_message(msj["role"]):
        st.markdown(msj["content"])

# Uploader Dinámico
imagen_adjunta = st.file_uploader("📷 Adjunta imagen", type=["jpg", "png", "jpeg"],
                                  key=f"foto_{st.session_state.uploader_key}")

if prompt := st.chat_input("Dime algo, Leonardo..."):
    tiene_foto = imagen_adjunta is not None

    with st.chat_message("user"):
        st.markdown(prompt)
        if tiene_foto: st.image(imagen_adjunta, width=300)

    # Preparar el contexto
    contexto_extra = ""
    fuentes_encontradas = []
    imagen_internet_obj = None
    respuesta_dalia = ""

    # Evaluar imagen subida
    if tiene_foto:
        img_pil = Image.open(imagen_adjunta)
        b64 = encode_image_pil(img_pil)
        st.info("Analizando la imagen...")
        respuesta_dalia = analizar_imagen(b64, prompt)
        st.session_state.uploader_key += 1  # Limpia el recuadro
        agregar_al_historial("user", prompt)  # Solo guardamos el texto

    # Evaluar búsqueda de imagen en internet
    elif necesita_imagen_internet(prompt):
        query_img = extraer_query_imagen(prompt)
        st.info(f"Buscando imagen de: {query_img}...")
        img, fuente = buscar_imagen_internet(query_img)
        if img:
            respuesta_dalia = f"Aquí está la imagen de: {query_img} 🔍"
            imagen_internet_obj = img
        else:
            respuesta_dalia = "No encontré ninguna imagen de eso, intenta con otras palabras."
        agregar_al_historial("user", prompt)

    # Evaluar búsqueda de texto en internet
    else:
        if st.session_state.modo_actual == "normal" and necesita_buscar(prompt):
            query = extraer_query(prompt)
            st.info(f"Buscando en internet sobre: {query}...")
            info, fuentes_encontradas = buscar_internet(query)
            if info:
                contexto_extra = f"[Información de internet sobre '{query}']:\n{info}\n\nAnaliza bien toda esta información antes de responder.\n\n"

        mensaje_final = f"{contexto_extra}Leonardo: {prompt}"
        agregar_al_historial("user", mensaje_final)

        modo = st.session_state.modo_actual
        if modo == "matematica":
            system = INSTRUCCION_MATEMATICA
        elif modo == "code":
            system = INSTRUCCION_CODE
        else:
            system = INSTRUCCION_NORMAL

        max_tok = 1200 if modo in ("matematica", "code") else 600

        with st.chat_message("assistant"):
            with st.spinner("Dalia está escribiendo..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    max_tokens=max_tok,
                    messages=[
                        {"role": "system", "content": system},
                        *st.session_state.historiales[modo]
                    ]
                )
                respuesta_dalia = response.choices[0].message.content.strip()

    # Mostrar respuesta si no se mostró arriba (cuando no es texto normal)
    if tiene_foto or necesita_imagen_internet(prompt):
        with st.chat_message("assistant"):
            st.markdown(respuesta_dalia)
            if imagen_internet_obj:
                st.image(imagen_internet_obj)

    agregar_al_historial("assistant", respuesta_dalia)

    # Fuentes
    if fuentes_encontradas:
        st.caption("🔍 Fuentes: " + " | ".join(fuentes_encontradas))

    # Reproducción de voz (Adaptada para web)
    if st.session_state.voz_activa:
        archivo_audio = asyncio.run(generar_audio(respuesta_dalia))
        if archivo_audio:
            st.audio(archivo_audio, format="audio/mp3", autoplay=True)
            # Limpiar el archivo para no saturar el servidor
            if os.path.exists(archivo_audio): os.remove(archivo_audio)

    if tiene_foto: st.rerun()