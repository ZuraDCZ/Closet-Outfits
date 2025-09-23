import streamlit as st
import pandas as pd
import requests
from pathlib import Path
import os
import json

st.set_page_config(page_title="Closet Automático", layout="wide")

# --------------------------
# Configuración API clima
# --------------------------
API_KEY = os.environ.get("OPENWEATHER_API_KEY")  # define esta variable en Streamlit Cloud
CITY = "Ciudad de México,MX"

def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=es"
        r = requests.get(url).json()
        if "main" not in r:
            st.warning(f"No se pudo obtener el clima: {r.get('message','Error desconocido')}")
            return "todo"
        temp = r["main"]["temp"]
        weather = r["weather"][0]["main"].lower()
        if "rain" in weather:
            return "lluvia"
        elif temp > 25:
            return "calor"
        elif temp < 15:
            return "frio"
        else:
            return "templado"
    except:
        return "todo"

# --------------------------
# Rueda de colores
# --------------------------
color_wheel = {
    "rojo": 0,
    "naranja": 30,
    "amarillo": 60,
    "verde": 120,
    "cyan": 180,
    "azul": 240,
    "morado": 300,
    "rosa": 330,
    "negro": None,
    "blanco": None,
    "gris": None,
    "beige": None
}

def armonia_colores(colores):
    """Evalúa si los colores forman una combinación armónica."""
    tonos = [color_wheel.get(c.lower(), None) for c in colores]

    # Neutros: siempre válidos
    if all(t is None for t in tonos):
        return True

    # Quitar neutros
    tonos = [t for t in tonos if t is not None]

    if len(tonos) <= 1:
        return True  # monocromático o solo un color real

    # Diferencias en grados
    difs = []
    for i in range(len(tonos)):
        for j in range(i+1, len(tonos)):
            d = abs(tonos[i] - tonos[j])
            difs.append(min(d, 360-d))

    # Reglas:
    if all(d <= 30 for d in difs):  # análogo
        return True
    if any(abs(d-180) <= 20 for d in difs):  # complementario
        return True
    if len(tonos) == 3 and all(abs(d-120) <= 20 for d in difs):  # tríada
        return True

    return False

# --------------------------
# CSV con JSON
# --------------------------
def safe_load(val):
    try:
        return json.loads(val)
    except:
        if isinstance(val, str) and val.strip() != "":
            return [val]  # si es un string suelto, lo metemos en lista
        return []

def load_csv(path="closet.csv"):
    if Path(path).exists():
        df = pd.read_csv(path)
        if not df.empty:
            df["formalidad"] = df["formalidad"].apply(safe_load)
            df["clima"] = df["clima"].apply(safe_load)
        return df
    else:
        return pd.DataFrame(columns=["id","nombre","categoria","color","formalidad","clima","disponible","imagen"])

def save_csv(df, path="closet.csv"):
    df_copy = df.copy()
    df_copy["formalidad"] = df_copy["formalidad"].apply(json.dumps)
    df_copy["clima"] = df_copy["clima"].apply(json.dumps)
    df_copy.to_csv(path, index=False)

# --------------------------
# Funciones de Outfit
# --------------------------
def seleccionar_prendas(df):
    superior = df[df["categoria"]=="superior"]
    inferior = df[df["categoria"]=="inferior"]
    calzado  = df[df["categoria"]=="calzado"]
    if superior.empty or inferior.empty or calzado.empty:
        return None
    return {
        "Superior": superior.sample(1).iloc[0],
        "Inferior": inferior.sample(1).iloc[0],
        "Calzado": calzado.sample(1).iloc[0]
    }

def generar_outfit(df, formalidad, clima, debug=False):
    """
    Genera un outfit considerando formalidad y clima.
    Siempre devuelve un outfit si hay prendas disponibles.
    """
    filtrado = df[df["disponible"]==1]

    # Filtrar por formalidad y clima
    filtrado_fc = filtrado[
        filtrado["formalidad"].apply(lambda f: formalidad in f) &
        filtrado["clima"].apply(lambda c: clima in c or "todo" in c)
    ]

    if debug:
        st.write(f"Prendas filtradas por formalidad='{formalidad}' y clima='{clima}': {len(filtrado_fc)}")
        st.dataframe(filtrado_fc[["nombre","categoria","color","formalidad","clima","disponible"]])

    if filtrado_fc.empty:
        if debug:
            st.warning("No hay prendas que cumplan formalidad y clima")
        return None

    # Intentar hasta 20 veces encontrar un outfit armónico
    for _ in range(20):
        outfit = seleccionar_prendas(filtrado_fc)
        if outfit:
            colores = [prenda["color"].lower() for prenda in outfit.values()]
            if armonia_colores(colores):
                return outfit

    # Si no encuentra armonía, devuelve un outfit válido
    outfit = seleccionar_prendas(filtrado_fc)
    if outfit:
        st.warning("No se encontró un outfit armónico, mostrando el primero disponible 😅")
    return outfit

# --------------------------
# Interfaz con pestañas
# --------------------------
st.title("👕 Closet Automático con Armonía de Colores")

tabs = st.tabs(["Generar Outfit", "Agregar Prenda", "Lavandería"])

# -----------------------------------
# Pestaña 1: Generar Outfit
# -----------------------------------
with tabs[0]:
    df = load_csv()
    formalidad = st.selectbox("Elige formalidad", ["casual","formal"])
    clima = get_weather()
    st.write(f"🌦️ Clima detectado en {CITY}: **{clima}**")

    if "outfit_actual" not in st.session_state:
        st.session_state["outfit_actual"] = None

    if st.button("Generar Outfit") or st.session_state["outfit_actual"] is not None:
        if st.session_state["outfit_actual"] is None:
            st.session_state["outfit_actual"] = generar_outfit(df, formalidad, clima, debug=True)

        outfit = st.session_state["outfit_actual"]

        if outfit:
            st.success("Outfit recomendado:")
            cols = st.columns(len(outfit))
            for i, (categoria, prenda) in enumerate(outfit.items()):
                with cols[i]:
                    st.markdown(f"**{categoria}**")
                    st.write(prenda["nombre"])
                    img_path = Path(prenda["imagen"])
                    if img_path.exists():
                        st.image(img_path, use_container_width=True)
                    else:
                        st.warning("Imagen no encontrada")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Generar otro"):
                    st.session_state["outfit_actual"] = generar_outfit(df, formalidad, clima)
            with col2:
                if st.button("✅ Usar este outfit"):
                    ids = [int(p["id"]) for p in outfit.values()]
                    df.loc[df["id"].isin(ids), "disponible"] = 0  # marcar como en lavandería
                    save_csv(df)
                    st.success("Outfit usado y enviado a lavandería 👕🧺")
                    st.session_state["outfit_actual"] = None
        else:
            st.error("No se pudo generar un outfit armónico 😢")

# -----------------------------------
# Pestaña 2: Agregar Prenda
# -----------------------------------
with tabs[1]:
    st.header("🛍️ Agregar nueva prenda")
    nombre = st.text_input("Nombre de la prenda")
    categoria = st.selectbox("Categoría", ["superior", "inferior", "calzado"])
    color = st.text_input("Color (ej: rojo, azul, verde, negro, blanco...)")
    formalidad = st.multiselect("Formalidad", ["casual","formal"])
    clima = st.multiselect("Clima", ["calor","frio","templado","lluvia","todo"])
    imagen = st.file_uploader("Subir imagen", type=["jpg","png"])

    if st.button("Agregar prenda") and nombre and imagen and formalidad and clima and color:
        imagen_path = Path("imagenes") / imagen.name
        imagen_path.parent.mkdir(parents=True, exist_ok=True)
        with open(imagen_path, "wb") as f:
            f.write(imagen.getbuffer())

        df = load_csv()
        nuevo_id = df["id"].max()+1 if not df.empty else 1

        df = df.append({
            "id": nuevo_id,
            "nombre": nombre,
            "categoria": categoria,
            "color": color,
            "formalidad": formalidad,
            "clima": clima,
            "disponible": 1,
            "imagen": str(imagen_path)
        }, ignore_index=True)

        save_csv(df)

        st.success(f"Prenda '{nombre}' agregada ✅")
        st.image(imagen_path, use_container_width=True)

# -----------------------------------
# Pestaña 3: Lavandería
# -----------------------------------
with tabs[2]:
    st.header("🧺 Lavandería")
    df = load_csv()
    lavanderia = df[df["disponible"]==0]

    if lavanderia.empty:
        st.info("No hay prendas en la lavandería 🎉")
    else:
        for _, prenda in lavanderia.iterrows():
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f"**{prenda['nombre']}** ({prenda['categoria']})")
                img_path = Path(prenda["imagen"])
                if img_path.exists():
                    st.image(img_path, use_container_width=True)
            with col2:
                if st.button(f"✅ Disponible", key=f"lav_{prenda['id']}"):
                    df.loc[df["id"]==prenda["id"], "disponible"] = 1
                    save_csv(df)
                    st.experimental_rerun()
