import streamlit as st
import asyncio
import base64
import os
import time
import json
import re
from io import BytesIO
from datetime import datetime

import edge_tts
import requests
from groq import Groq
from PIL import Image

# ============================================================
# CONFIGURACIÓN DE PÁGINA — OPTIMIZADA PARA MÓVIL
# ============================================================
st.set_page_config(
    page_title="Dalia",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CSS CUSTOM — ESTÉTICA MÓVIL TIPO CHATGPT/WHATSAPP
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

    /* Chat messages — más compactos para móvil */
    .stChatMessage {
        background-color: #0d0d0d !important;
        border-radius: 12px !important;
        border: 1px solid #2a2a3e !important;
        padding: 8px 12px !important;
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
        padding: 40px 20px !important;
        max-width: 400px !important;
        margin: 0 auto !important;
        text-align: center !important;
    }

    /* Scrollbar oscura */
    ::-webkit-scrollbar {
        width: 6px !important;
    }
    ::-webkit-scrollbar-track {
        background: #000000 !important;
    }
    ::-webkit-scrollbar-thumb {
        background: #3e3e5e !important;
        border-radius: 3px !important;
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
       BARRA DE INPUT TIPO WHATSAPP/CHATGPT
       ========================================== */

    /* Contenedor principal de la barra */
    .input-bar-container {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        background-color: #000000 !important;
        padding: 8px 12px 20px 12px !important;
        border-top: 1px solid #2a2a3e !important;
        z-index: 1000 !important;
    }

    /* Barra interna redondeada */
    .input-bar-inner {
        background-color: #2d2d2d !important;
        border-radius: 24px !important;
        padding: 4px 8px !important;
        border: 1px solid #3e3e3e !important;
        display: flex !important;
        align-items: center !important;
        gap: 4px !important;
    }

    /* Botón ▼ (opciones) */
    .btn-options .stButton > button {
        background: transparent !important;
        border: none !important;
        color: #e2e2e2 !important;
        font-size: 16px !important;
        padding: 0 !important;
        width: 36px !important;
        height: 36px !important;
        border-radius: 50% !important;
    }
    .btn-options .stButton > button:hover {
        background: #3e3e3e !important;
    }

    /* Input de texto */
    .input-bar-inner .stTextInput > div > div > input {
        background: transparent !important;
        border: none !important;
        color: #ffffff !important;
        font-size: 15px !important;
        padding: 8px 4px !important;
        box-shadow: none !important;
    }
    .input-bar-inner .stTextInput > div > div > input::placeholder {
        color: #9ca3af !important;
    }

    /* Botón micrófono */
    .btn-mic .stButton > button {
        background: transparent !important;
        border: none !important;
        color: #e2e2e2 !important;
        font-size: 18px !important;
        padding: 0 !important;
        width: 36px !important;
        height: 36px !important;
        border-radius: 50% !important;
    }
    .btn-mic .stButton > button:hover {
        background: #3e3e3e !important;
    }

    /* Botón enviar ▶ */
    .btn-send .stButton > button {
        background: #e2e2e2 !important;
        color: #000000 !important;
        border: none !important;
        border-radius: 50% !important;
        width: 36px !important;
        height: 36px !important;
        font-size: 14px !important;
        padding: 0 !important;
        font-weight: bold !important;
    }
    .btn-send .stButton > button:hover {
        background: #ffffff !important;
    }

    /* Popover menu */
    div[data-testid="stPopoverPopover"] {
        background-color: #1a1a1a !important;
        border: 1px solid #3e3e3e !important;
        border-radius: 12px !important;
    }

    /* Modo label */
    .modo-label-top {
        text-align: center !important;
        font-weight: bold !important;
        font-size: 0.9em !important;
        margin-bottom: 8px !important;
        padding: 3px 10px !important;
        border-radius: 16px !important;
        display: inline-block !important;
    }

    /* Reporte de fuentes */
    .reporte-fuentes {
        background-color: #1a1a2e !important;
        border-left: 3px solid #a78bfa !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        margin-bottom: 10px !important;
        color: #c4b5fd !important;
        font-size: 0.88em !important;
    }

    /* Memoria tags */
    .memoria-tag {
        background-color: #2a1a3e !important;
        border: 1px solid #7c3aed !important;
        color: #d8b4fe !important;
        padding: 3px 8px !important;
        border-radius: 10px !important;
        font-size: 0.78em !important;
        display: inline-block !important;
        margin: 2px !important;
    }

    /* Espacio al final para la barra fija */
    .spacer-bottom {
        height: 80px !important;
    }

    /* Preview de imagen */
    .img-preview {
        color: #34d399 !important;
        font-size: 0.85em !important;
        margin-bottom: 4px !important;
        padding-left: 12px !important;
    }

    /* Sidebar más compacta en móvil */
    [data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CREDENCIALES Y CLIENTES
# ============================================================
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "PON-TU-KEY-AQUÍ")
VOZ_HUMANA   = "es-MX-DaliaNeural"
client       = Groq(api_key=GROQ_API_KEY)

# ============================================================
# USUARIOS AUTORIZADOS
# ============================================================
USUARIOS = {
    "chris123":  "CHRISTIAN",
    "emanu123":  "EMMANUEL",
    "leo123":    "LEONARDO"
}

# ============================================================
# MEMORIA PERSISTENTE
# ============================================================
MEMORIA_DIR = ".memoria_dalia"
os.makedirs(MEMORIA_DIR, exist_ok=True)

def _archivo_memoria(usuario):
    return os.path.join(MEMORIA_DIR, f"memoria_{usuario.lower()}.json")

def cargar_memoria(usuario):
    try:
        with open(_archivo_memoria(usuario), "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "gustos": [], "hechos_importantes": [], "temas_frecuentes": [],
            "ultima_sesion": None, "preferencias": {}, "contador_mensajes": 0
        }

def guardar_memoria(usuario, datos):
    try:
        with open(_archivo_memoria(usuario), "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except:
        pass

def actualizar_memoria(usuario, mensaje_usuario, mensaje_dalia):
    memoria = cargar_memoria(usuario)
    memoria["contador_mensajes"] += 2
    memoria["ultima_sesion"] = datetime.now().isoformat()

    t = mensaje_usuario.lower()
    patrones_gusto = [
        (r"me gusta (.+)", "gusta"), (r"me encanta (.+)", "encanta"),
        (r"amo (.+)", "ama"), (r"odio (.+)", "odia"),
        (r"mi favorito es (.+)", "favorito"), (r"prefiero (.+)", "prefiere"),
        (r"soy fan de (.+)", "fan"), (r"me apasiona (.+)", "apasiona"),
    ]
    for patron, tipo in patrones_gusto:
        match = re.search(patron, t)
        if match:
            gusto = match.group(1).strip().rstrip(".?!")
            if 2 < len(gusto) < 100:
                nuevo = {"que": gusto, "tipo": tipo, "cuando": datetime.now().isoformat()}
                if not any(g["que"] == gusto for g in memoria["gustos"]):
                    memoria["gustos"].append(nuevo)
                    if len(memoria["gustos"]) > 30: memoria["gustos"].pop(0)

    patrones_hecho = [
        (r"mi cumpleaños es el? (.+)", "cumpleaños"), (r"trabajo en (.+)", "trabajo"),
        (r"soy (.+) de profesión", "profesion"), (r"estudio (.+)", "estudios"),
        (r"vivo en (.+)", "ubicacion"), (r"tengo (\d+) años", "edad"),
    ]
    for patron, tipo in patrones_hecho:
        match = re.search(patron, t)
        if match:
            hecho = match.group(1).strip().rstrip(".?!")
            if 1 < len(hecho) < 100:
                nuevo = {"que": hecho, "tipo": tipo, "cuando": datetime.now().isoformat()}
                if not any(h["que"] == hecho for h in memoria["hechos_importantes"]):
                    memoria["hechos_importantes"].append(nuevo)
                    if len(memoria["hechos_importantes"]) > 20: memoria["hechos_importantes"].pop(0)

    temas_clave = ["python", "javascript", "matemáticas", "física", "programación",
                   "música", "juegos", "películas", "comida", "deportes", "tecnología",
                   "ia", "inteligencia artificial", "dinero", "crypto", "viajes"]
    for tema in temas_clave:
        if tema in t and tema not in memoria["temas_frecuentes"]:
            memoria["temas_frecuentes"].append(tema)
            if len(memoria["temas_frecuentes"]) > 15: memoria["temas_frecuentes"].pop(0)

    guardar_memoria(usuario, memoria)
    return memoria

def construir_contexto_memoria(usuario):
    memoria = cargar_memoria(usuario)
    contextos = []
    if memoria["gustos"]:
        lista = ", ".join([f"{g['que']} ({g['tipo']})" for g in memoria["gustos"][-8:]])
        contextos.append(f"GUSTOS: {lista}")
    if memoria["hechos_importantes"]:
        lista = ", ".join([f"{h['tipo']}: {h['que']}" for h in memoria["hechos_importantes"][-5:]])
        contextos.append(f"DATOS: {lista}")
    if memoria["temas_frecuentes"]:
        contextos.append(f"TEMAS: {', '.join(memoria['temas_frecuentes'][-5:])}")
    if contextos:
        return "\n[MEMORIA]\n" + "\n".join(contextos) + "\n[FIN]\n"
    return ""

# ============================================================
# INSTRUCCIONES ADAPTATIVAS
# ============================================================
def construir_instruccion(modo, usuario):
    memoria_ctx = construir_contexto_memoria(usuario)

    base = (
        "Eres Dalia, asistente personal de Leonardo. "
        "Eres una chica joven, inteligente, amable, alegre y un poco tímida. "
        "Hablas de forma natural y relajada. "
        f"{memoria_ctx}"
        "\n\nREGLAS: "
        "- Si es conversación casual, responde con TU CRITERIO sin buscar internet. "
        "- Solo busca cuando detectes información actual, noticias o datos específicos. "
        "- Usa la memoria del usuario para personalizar respuestas. "
    )

    if modo == "matematica":
        return base + (
            "\n\nMODO MATEMÁTICA: "
            "1. RESUMEN → 2. DATOS → 3. DESARROLLO → 4. RESULTADO → 5. COMPROBACIÓN. "
            "Sin relleno, ve al grano."
        )
    elif modo == "code":
        return base + (
            "\n\nMODO CODE: "
            "Explica brevemente, código limpio comentado, explica partes importantes, "
            "corrige errores. Sin relleno."
        )
    return base + (
        "\n\nMODO NORMAL: "
        "Cuando busques: 1.🔍 Fuentes → 2.📊 Comparación → 3. Respuesta final. "
        "Sintetiza todo. Responde y punto."
    )

INSTRUCCION_VISION = (
    "Eres Dalia analizando una imagen. Describe detalladamente: objetos, personas, "
    "colores, texto, contexto. Si es código o error, analízalo. Habla claro y natural."
)

# ============================================================
# ESTADO GLOBAL
# ============================================================
def init_state():
    defaults = {
        "authenticated": False, "username": "", "modo_actual": "normal",
        "voz_activa": True, "imagen_pil": None, "messages": [],
        "historiales": {"normal": [], "matematica": [], "code": []},
        "input_buffer": "", "enviar_trigger": False,
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
def encode_image_pil(pil_img):
    if pil_img.mode in ("RGBA", "P", "LA"):
        pil_img = pil_img.convert("RGB")
    buffer = BytesIO()
    pil_img.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# ============================================================
# BÚSQUEDA WEB
# ============================================================
def _ddg_buscar(query, max_results=8):
    try:
        url = "https://html.duckduckgo.com/html/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        data = {"q": query, "kl": "mx-es"}
        resp = requests.post(url, data=data, headers=headers, timeout=10)
        if resp.status_code != 200: return []
        from html.parser import HTMLParser
        class DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []; self.in_result = False; self.in_title = False
                self.in_snippet = False; self.current = {}; self.link_href = ""
            def handle_starttag(self, tag, attrs):
                attrs_dict = dict(attrs)
                if tag == "div" and "result" in attrs_dict.get("class", ""):
                    self.in_result = True; self.current = {}
                elif self.in_result and tag == "a" and "result__a" in attrs_dict.get("class", ""):
                    self.in_title = True; self.link_href = attrs_dict.get("href", "")
                elif self.in_result and tag == "a" and "result__snippet" in attrs_dict.get("class", ""):
                    self.in_snippet = True; self.current["href"] = attrs_dict.get("href", "")
            def handle_endtag(self, tag):
                if tag == "div" and self.in_result:
                    if self.current.get("title") and self.current.get("body"):
                        self.results.append(self.current)
                    self.in_result = False; self.current = {}
                elif tag == "a" and self.in_title: self.in_title = False
                elif tag == "a" and self.in_snippet: self.in_snippet = False
            def handle_data(self, data):
                if self.in_title: self.current["title"] = data.strip(); self.current["href"] = self.link_href
                elif self.in_snippet: self.current["body"] = data.strip()
        parser = DDGParser(); parser.feed(resp.text)
        return parser.results[:max_results]
    except: return []

def buscar_web_normal(query):
    fuentes_consultadas = []; textos_totales = []
    resultados = _ddg_buscar(query, 6)
    if resultados:
        fuentes_consultadas.append("🌐 Web general")
        for r in resultados: textos_totales.append(f"- {r.get('title', '')}: {r.get('body', '')}")
    noticias = _ddg_buscar(f"{query} noticias", 3)
    if noticias:
        fuentes_consultadas.append("📰 Noticias")
        for r in noticias: textos_totales.append(f"- [Noticia] {r.get('title', '')}: {r.get('body', '')}")
    wiki = _ddg_buscar(f"{query} site:wikipedia.org", 2)
    if wiki:
        fuentes_consultadas.append("📚 Wikipedia")
        for r in wiki: textos_totales.append(f"- [Wiki] {r.get('title', '')}: {r.get('body', '')}")
    redes = _ddg_buscar(f"{query} site:reddit.com", 2)
    if redes:
        fuentes_consultadas.append("💬 Reddit")
        for r in redes: textos_totales.append(f"- [Reddit] {r.get('title', '')}: {r.get('body', '')}")
    fuentes_limpias = []
    for r in resultados + noticias + wiki + redes:
        href = r.get("href", "")
        if href:
            try:
                dominio = href.split("/")[2].replace("www.", "")
                if dominio not in fuentes_limpias: fuentes_limpias.append(dominio)
            except: pass
    return "\n".join(textos_totales), fuentes_limpias[:5], fuentes_consultadas

def buscar_web_matematica(query):
    fuentes_consultadas = []; textos_totales = []
    math_se = _ddg_buscar(f"{query} site:math.stackexchange.com", 3)
    if math_se:
        fuentes_consultadas.append("📐 Math.SE")
        for r in math_se: textos_totales.append(f"- [Math] {r.get('title', '')}: {r.get('body', '')}")
    khan = _ddg_buscar(f"{query} site:khanacademy.org", 2)
    if khan:
        fuentes_consultadas.append("🎓 Khan")
        for r in khan: textos_totales.append(f"- [Khan] {r.get('title', '')}: {r.get('body', '')}")
    wolfram = _ddg_buscar(f"{query} site:wolframalpha.com", 2)
    if wolfram:
        fuentes_consultadas.append("🔢 Wolfram")
        for r in wolfram: textos_totales.append(f"- [Wolfram] {r.get('title', '')}: {r.get('body', '')}")
    general = _ddg_buscar(query, 3)
    if general:
        fuentes_consultadas.append("🌐 General")
        for r in general: textos_totales.append(f"- {r.get('title', '')}: {r.get('body', '')}")
    fuentes_limpias = []
    for r in math_se + khan + wolfram + general:
        href = r.get("href", "")
        if href:
            try:
                dominio = href.split("/")[2].replace("www.", "")
                if dominio not in fuentes_limpias: fuentes_limpias.append(dominio)
            except: pass
    return "\n".join(textos_totales), fuentes_limpias[:5], fuentes_consultadas

def buscar_web_code(query):
    fuentes_consultadas = []; textos_totales = []
    so = _ddg_buscar(f"{query} site:stackoverflow.com", 4)
    if so:
        fuentes_consultadas.append("💻 StackOverflow")
        for r in so: textos_totales.append(f"- [SO] {r.get('title', '')}: {r.get('body', '')}")
    gh = _ddg_buscar(f"{query} site:github.com", 3)
    if gh:
        fuentes_consultadas.append("🐙 GitHub")
        for r in gh: textos_totales.append(f"- [GH] {r.get('title', '')}: {r.get('body', '')}")
    docs = _ddg_buscar(f"{query} site:docs.python.org OR site:developer.mozilla.org", 2)
    if docs:
        fuentes_consultadas.append("📖 Docs")
        for r in docs: textos_totales.append(f"- [Docs] {r.get('title', '')}: {r.get('body', '')}")
    general = _ddg_buscar(query, 2)
    if general:
        fuentes_consultadas.append("🌐 General")
        for r in general: textos_totales.append(f"- {r.get('title', '')}: {r.get('body', '')}")
    fuentes_limpias = []
    for r in so + gh + docs + general:
        href = r.get("href", "")
        if href:
            try:
                dominio = href.split("/")[2].replace("www.", "")
                if dominio not in fuentes_limpias: fuentes_limpias.append(dominio)
            except: pass
    return "\n".join(textos_totales), fuentes_limpias[:5], fuentes_consultadas

# ============================================================
# BÚSQUEDA DE IMÁGENES — MEJORADA
# ============================================================
def buscar_imagen_ddg(query):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    # Intento 1: DuckDuckGo
    try:
        url = "https://duckduckgo.com/"
        resp = requests.get(url, params={"q": query}, headers=headers, timeout=10)
        vqd = ""
        for line in resp.text.split("\n"):
            if "vqd=" in line:
                try: vqd = line.split("vqd=")[1].split("&")[0].split("\"")[0]; break
                except: pass
        if vqd:
            img_url = "https://duckduckgo.com/i.js"
            params = {"l": "mx-es", "o": "json", "q": query, "vqd": vqd, "f": ",,," , "p": "1"}
            resp_img = requests.get(img_url, params=params, headers=headers, timeout=10)
            data = resp_img.json()
            for r in data.get("results", [])[:8]:
                try:
                    img_url = r.get("image", "")
                    if not img_url: continue
                    img_resp = requests.get(img_url, timeout=5, headers=headers)
                    if img_resp.status_code == 200:
                        img = Image.open(BytesIO(img_resp.content))
                        return img, img_url
                except: continue
    except: pass
    # Intento 2: Unsplash
    try:
        unsplash_url = f"https://source.unsplash.com/400x300/?{query.replace(' ', ',')}"
        img_resp = requests.get(unsplash_url, timeout=10, headers=headers, allow_redirects=True)
        if img_resp.status_code == 200:
            img = Image.open(BytesIO(img_resp.content))
            return img, img_resp.url
    except: pass
    return None, None

# ============================================================
# ANALIZAR IMAGEN
# ============================================================
def analizar_imagen(imagen_b64, prompt=""):
    try:
        texto = prompt if prompt else "Analiza esta imagen detalladamente y describe todo lo que ves."
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            max_tokens=1000,
            messages=[
                {"role": "system", "content": INSTRUCCION_VISION},
                {"role": "user", "content": [
                    {"type": "text", "text": texto},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{imagen_b64}"}}
                ]}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"No pude analizar la imagen: {e}"

# ============================================================
# DETECTOR INTELIGENTE
# ============================================================
def es_conversacion_casual(texto):
    t = texto.lower().strip()
    saludos = ["hola", "buenos días", "buenas tardes", "buenas noches",
               "hey", "qué tal", "cómo estás", "como estas", "qué onda",
               "adiós", "hasta luego", "nos vemos", "bye"]
    personales = ["cómo te llamas", "quién eres", "quien eres", "cuántos años tienes",
                  "de dónde eres", "te gusta", "tu favorito", "tu color",
                  "me cuentas", "cuéntame", "platica", "platicame", "chiste", "broma",
                  "qué andas haciendo", "que andas haciendo", "qué haces", "que haces",
                  "estás ocupada", "estas ocupada", "cómo va tu día", "como va tu dia",
                  "te extrañé", "te extranhe", "te extraño", "te extrano",
                  "gracias", "te amo", "te quiero", "eres bonita", "eres linda",
                  "me caes bien", "eres inteligente", "eres divertida"]
    opiniones = ["qué opinas", "que opinas", "qué te parece", "que te parece",
                 "crees que", "piensas que", "tú crees", "tu crees",
                 "recomiendas", "sugieres", "aconsejas"]
    for patron in saludos + personales + opiniones:
        if patron in t: return True
    palabras = t.split()
    if len(palabras) <= 4:
        busqueda = ["busca", "investiga", "googlea", "noticias", "precio",
                    "quién es", "quien es", "qué pasó", "que paso",
                    "actualmente", "dónde", "donde", "cuándo", "cuando",
                    " último ", " última ", "reciente", "nuevo", "nueva",
                    "tutorial", "ejemplo", "review", "opinión"]
        if not any(p in t for p in busqueda): return True
    return False

def necesita_buscar(texto):
    t = texto.lower().strip()
    if es_conversacion_casual(t): return False
    busqueda_explicita = [
        "busca", "investiga", "googlea", "buscar",
        "noticias de", "noticias sobre", "últimas noticias", "ultimas noticias",
        "precio de", "precio actual", "cuánto cuesta", "cuanto cuesta",
        "dónde queda", "donde queda", "cómo llegar", "como llegar",
        "fecha de", "cuándo es", "cuando es", "horario de",
        "estadísticas de", "estadisticas de", "datos de", "cifras de",
        "ranking de", "lista de", "top 10", "mejores ", "peores ",
        "evento de", "concierto de", "película de", "pelicula de",
        "biografía de", "biografia de", "historia de",
        "tutorial de", "cómo hacer", "como hacer", "pasos para",
        "review de", "reseña de", "resena de", "opiniones de",
        "comparación de", "comparacion de", "vs", "versus",
        "actualización de", "actualizacion de", "nueva versión", "nueva version",
        "rumores de", "filtraciones de", "leaks de",
        "pronóstico", "pronostico", "predicción", "prediccion",
        "resultados de", "marcador de", "score de"
    ]
    if any(p in t for p in busqueda_explicita): return True
    if re.search(r'^(quién|quien|qué|que|cuál|cual|cuándo|cuando|dónde|donde|por qué|por que)\s+(es|fue|son|eran|está|esta|pasó|paso)', t):
        filosofico = ["sentido de la vida", "amor", "felicidad", "éxito", "exito",
                      "realidad", "verdad", "justicia", "libertad", "destino"]
        if not any(f in t for f in filosofico): return True
    return False

def extraer_query(texto):
    query = texto.lower()
    for p in ["busca", "investiga", "googlea", "qué es", "que es",
              "quién es", "quien es", "noticias de", "noticias sobre",
              "dame información sobre", "información de", "info de",
              "cuéntame sobre", "cuentame sobre", "explícame", "explicame",
              "muéstrame", "muestrame", "dame una imagen de", "imagen de",
              "foto de", "busca imagen de", "busca una imagen de"]:
        query = query.replace(p, "").strip()
    return query if query else texto

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

def buscar_internet_inteligente(query):
    if st.session_state.modo_actual == "matematica": return buscar_web_matematica(query)
    elif st.session_state.modo_actual == "code": return buscar_web_code(query)
    else: return buscar_web_normal(query)

# ============================================================
# PREGUNTAR A DALIA
# ============================================================
def preguntar_a_dalia(mensaje, imagen_b64=None):
    usuario = st.session_state.username
    contexto_extra = ""; fuentes = []; reporte_fuentes = []

    if imagen_b64:
        respuesta = analizar_imagen(imagen_b64, mensaje)
        actualizar_memoria(usuario, mensaje, respuesta)
        return respuesta, [], None, []

    if necesita_imagen_internet(mensaje):
        query_img = extraer_query_imagen(mensaje)
        img, fuente = buscar_imagen_ddg(query_img)
        if img:
            respuesta = f"Aquí está la imagen de: {query_img} 🔍"
            actualizar_memoria(usuario, mensaje, respuesta)
            return respuesta, [], img, []
        respuesta = "No encontré ninguna imagen de eso, intenta con otras palabras."
        actualizar_memoria(usuario, mensaje, respuesta)
        return respuesta, [], None, []

    debe_buscar = necesita_buscar(mensaje)
    if debe_buscar:
        query = extraer_query(mensaje)
        info, fuentes, reporte_fuentes = buscar_internet_inteligente(query)
        if info:
            contexto_extra = (
                f"[Información de internet sobre '{query}']:\n{info}\n\n"
                f"Analiza bien toda esta información antes de responder. "
                f"PRIMERO lista las fuentes consultadas, LUEGO compara la información, "
                f"y AL FINAL da tu respuesta completa.\n\n"
            )
        else:
            contexto_extra = "[No pude obtener resultados de internet, responde con tu conocimiento interno]\n\n"

    mensaje_final = f"{contexto_extra}Leonardo: {mensaje}"
    agregar_al_historial("user", mensaje_final)
    system = construir_instruccion(st.session_state.modo_actual, usuario)
    max_tok = 1500 if st.session_state.modo_actual in ("matematica", "code") else 800

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
    actualizar_memoria(usuario, mensaje, respuesta)
    return respuesta, fuentes, None, reporte_fuentes

# ============================================================
# VOZ
# ============================================================
async def _generar_audio_async(texto):
    t = texto.replace('*', '').replace('#', '')
    archivo = f"temp_voz_{abs(hash(t)) % 100000}.mp3"
    com = edge_tts.Communicate(t, VOZ_HUMANA)
    await com.save(archivo)
    return archivo

def hablar(texto):
    if not st.session_state.voz_activa: return
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        archivo = loop.run_until_complete(_generar_audio_async(texto))
        st.audio(archivo, format="audio/mp3", autoplay=True)
    except Exception as e:
        st.toast(f"🔇 Error de voz: {e}")

# ============================================================
# LOGIN
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
                "🔑 Contraseña", type="password", label_visibility="collapsed",
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
memoria_usuario = cargar_memoria(nombre_amigo)

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

if es_creador:
    st.markdown(f"<h2 style='text-align:center;'>🤖 Dalia <span class='creator-badge'>CREADOR</span></h2>", unsafe_allow_html=True)
else:
    st.markdown("<h2 style='text-align:center;'>🤖 Dalia</h2>", unsafe_allow_html=True)

st.markdown(f"<p style='text-align:center; color:#a78bfa;'>Bienvenido, <b>{nombre_amigo}</b> 💜</p>", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("<h3 style='color:#a78bfa;'>⚙️ Controles</h3>", unsafe_allow_html=True)
    st.session_state.voz_activa = st.toggle(
        "🔊 Voz: ON" if st.session_state.voz_activa else "🔇 Voz: OFF",
        value=st.session_state.voz_activa
    )
    st.divider()
    if memoria_usuario["gustos"] or memoria_usuario["hechos_importantes"]:
        st.markdown("<p style='color:#a78bfa; font-weight:bold;'>🧠 Tu memoria</p>", unsafe_allow_html=True)
        if memoria_usuario["gustos"]:
            st.markdown("<p style='color:#d8b4fe; font-size:0.85em; margin-bottom:4px;'><b>Gustos:</b></p>", unsafe_allow_html=True)
            for g in memoria_usuario["gustos"][-5:]:
                emoji = {"gusta": "❤️", "encanta": "💖", "ama": "🥰", "odia": "💔",
                         "no_gusta": "👎", "favorito": "⭐", "prefiere": "👍",
                         "fan": "🤩", "apasiona": "🔥"}.get(g["tipo"], "💜")
                st.markdown(f"<span class='memoria-tag'>{emoji} {g['que']}</span>", unsafe_allow_html=True)
        if memoria_usuario["hechos_importantes"]:
            st.markdown("<p style='color:#d8b4fe; font-size:0.85em; margin-bottom:4px; margin-top:8px;'><b>Datos:</b></p>", unsafe_allow_html=True)
            for h in memoria_usuario["hechos_importantes"][-3:]:
                emoji = {"cumpleaños": "🎂", "nacimiento": "👶", "trabajo": "💼",
                         "profesion": "🎓", "estudios": "📚", "ubicacion": "📍",
                         "origen": "🏠", "edad": "🔢", "pareja": "💕",
                         "familia": "👨‍👩‍👧‍👦"}.get(h["tipo"], "📌")
                st.markdown(f"<span class='memoria-tag'>{emoji} {h['que']}</span>", unsafe_allow_html=True)
        if memoria_usuario["temas_frecuentes"]:
            st.markdown("<p style='color:#d8b4fe; font-size:0.85em; margin-bottom:4px; margin-top:8px;'><b>Temas:</b></p>", unsafe_allow_html=True)
            st.markdown(f"<span class='memoria-tag'>🔖 {', '.join(memoria_usuario['temas_frecuentes'][-5:])}</span>", unsafe_allow_html=True)
        st.divider()
    st.markdown("<p style='color:#a78bfa; font-weight:bold;'>📷 O sube imagen aquí</p>", unsafe_allow_html=True)
    archivo_img_sidebar = st.file_uploader(
        "Sube imagen sidebar", type=["jpg", "jpeg", "png", "bmp", "webp"],
        label_visibility="collapsed", key="sidebar_uploader"
    )
    if archivo_img_sidebar:
        img = Image.open(archivo_img_sidebar)
        if img.mode in ("RGBA", "P", "LA"): img = img.convert("RGB")
        st.session_state.imagen_pil = img
        st.image(img, caption="✅ Imagen lista", width=200)
    st.divider()
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

# ============================================================
# INDICADOR DE MODO
# ============================================================
modos_colores = {
    "normal": ("💬 Normal", "#a78bfa", "#2a2a3e"),
    "matematica": ("📐 MATEMÁTICA 2.0", "#f59e0b", "#2a1a0a"),
    "code": ("💻 CODE", "#10b981", "#0a2a1a")
}
modo_txt, modo_color, modo_bg = modos_colores[st.session_state.modo_actual]
st.markdown(
    f"<div style='text-align:center;'><span class='modo-label-top' style='color:{modo_color}; background-color:{modo_bg}; border:1px solid {modo_color};'>"
    f"{modo_txt}</span></div>", unsafe_allow_html=True
)

# ============================================================
# CHAT
# ============================================================
if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": SALUDO_INICIO})
    if st.session_state.voz_activa: hablar(SALUDO_INICIO)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(f"<span style='color:#34d399; font-weight:bold;'>🚀 Tú</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color:#a78bfa; font-weight:bold;'>🤖 Dalia</span>", unsafe_allow_html=True)
        if msg.get("reporte_fuentes"):
            st.markdown(
                f"<div class='reporte-fuentes'><b>🔍 Fuentes:</b><br>{' • '.join(msg['reporte_fuentes'])}</div>",
                unsafe_allow_html=True
            )
        st.markdown(msg["content"])
        if msg.get("image"): st.image(msg["image"], width=350)
        if msg.get("fuentes"): st.caption("🔍 Fuentes: " + "  ".join([f"`{f}`" for f in msg["fuentes"]]))

# ============================================================
# ESPACIO PARA LA BARRA FIJA
# ============================================================
st.markdown("<div class='spacer-bottom'></div>", unsafe_allow_html=True)

# ============================================================
# BARRA FIJA TIPO WHATSAPP — [▼] [TEXTO] [🎙️] [▶]
# ============================================================
st.markdown('<div class="input-bar-container">', unsafe_allow_html=True)

# Preview de imagen
if st.session_state.imagen_pil:
    st.markdown(f"<p class='img-preview'>📷 Imagen lista</p>", unsafe_allow_html=True)

st.markdown('<div class="input-bar-inner">', unsafe_allow_html=True)

col_options, col_input, col_mic, col_send = st.columns([1, 8, 1, 1])

with col_options:
    st.markdown('<div class="btn-options">', unsafe_allow_html=True)
    with st.popover("▼", use_container_width=True):
        st.markdown("<p style='color:#a78bfa; font-weight:bold; margin-bottom:10px;'>⚙️ Opciones</p>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("💬 Normal", use_container_width=True, key="pop_normal"):
                st.session_state.modo_actual = "normal"; st.rerun()
        with c2:
            if st.button("📐 MATE", use_container_width=True, key="pop_mate"):
                st.session_state.modo_actual = "matematica"; st.rerun()
        with c3:
            if st.button("💻 CODE", use_container_width=True, key="pop_code"):
                st.session_state.modo_actual = "code"; st.rerun()
        st.divider()
        st.markdown("<p style='color:#a78bfa; font-weight:bold;'>📷 Subir imagen</p>", unsafe_allow_html=True)
        archivo_img_pop = st.file_uploader(
            "Selecciona imagen", type=["jpg", "jpeg", "png", "bmp", "webp"],
            label_visibility="collapsed", key="pop_uploader"
        )
        if archivo_img_pop:
            img = Image.open(archivo_img_pop)
            if img.mode in ("RGBA", "P", "LA"): img = img.convert("RGB")
            st.session_state.imagen_pil = img
            st.success("✅ Imagen cargada. Cierra y escribe.")
            st.image(img, width=150)
    st.markdown('</div>', unsafe_allow_html=True)

with col_input:
    # Input controlado por session_state — se limpia automáticamente
    def on_input_change():
        """Cuando el usuario presiona Enter, guarda el texto y limpia."""
        valor = st.session_state.get("chat_input", "")
        if valor.strip():
            st.session_state.input_buffer = valor.strip()
            st.session_state.enviar_trigger = True
            st.session_state.chat_input = ""  # Limpiar inmediatamente

    st.text_input(
        "Mensaje",
        key="chat_input",
        label_visibility="collapsed",
        placeholder="Preguntar a Dalia",
        on_change=on_input_change,
    )

with col_mic:
    st.markdown('<div class="btn-mic">', unsafe_allow_html=True)
    mic_emoji = "🎙️" if st.session_state.voz_activa else "🔇"
    if st.button(mic_emoji, key="btn_mic", use_container_width=True):
        st.session_state.voz_activa = not st.session_state.voz_activa
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_send:
    st.markdown('<div class="btn-send">', unsafe_allow_html=True)
    if st.button("▶", key="btn_enviar", use_container_width=True):
        # Tomar el valor actual del input
        valor = st.session_state.get("chat_input", "")
        if valor.strip():
            st.session_state.input_buffer = valor.strip()
            st.session_state.enviar_trigger = True
            st.session_state.chat_input = ""  # Limpiar
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # input-bar-inner
st.markdown('</div>', unsafe_allow_html=True)  # input-bar-container

# ============================================================
# PROCESAR ENVÍO — SE LIMPIA COMO WHATSAPP
# ============================================================
if st.session_state.enviar_trigger and st.session_state.input_buffer:
    prompt = st.session_state.input_buffer
    st.session_state.input_buffer = ""
    st.session_state.enviar_trigger = False

    st.session_state.messages.append({"role": "user", "content": prompt})

    imagen_b64 = None
    if st.session_state.imagen_pil:
        imagen_b64 = encode_image_pil(st.session_state.imagen_pil)
        st.session_state.imagen_pil = None

    with st.spinner("Dalia está pensando... 💭"):
        respuesta, fuentes, img_result, reporte_fuentes = preguntar_a_dalia(prompt, imagen_b64)

    msg_asistente = {
        "role": "assistant",
        "content": respuesta,
        "fuentes": fuentes,
        "reporte_fuentes": reporte_fuentes
    }
    if img_result: msg_asistente["image"] = img_result
    st.session_state.messages.append(msg_asistente)

    if st.session_state.voz_activa: hablar(respuesta)

    st.rerun()