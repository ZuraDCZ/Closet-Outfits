import streamlit as st
import pandas as pd
import requests
from pathlib import Path
import os
import json
import random

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
    tonos = [color_wheel.get(c.lower(), None) for c in colores]
    if all(t is None for t in tonos):
        return True
    tonos = [t for t in tonos if t is not None]
    if len(tonos) <= 1:
        return True
    difs = []
    for i in range(len(tonos)):
        for j in range(i+1, len(tonos)):
            d = abs(tonos[i] - tonos[j])
            difs.append(min(d, 360-d))
    if all(d <= 30 for d in difs):
        return True
    if any(abs(d-180) <= 20 for d in difs):
        return True
    if len(tonos) == 3 and all(abs(d-120) <= 20 for d in difs):
        return True
    return False

# --------------------------
# CSV con parser flexible
# --------------------------
def safe_parse(value):
    if pd.isna(value):
        return []
    try:
        return json.loads(value)
    except:
        return [v.strip() for v in str(value).split(",") if v.strip()]

def load_csv(path="closet.csv"):
    if Path(path).exists():
        df = pd.read_csv(path)
        if "formalidad" in df.columns:
            df["formalidad"] = df["formalidad"].apply(safe_parse)
        if "clima" in df.columns:
            df["clima"] = df["clima"].apply(safe_parse)
        return df
    else:
        return pd.DataFrame(columns=["id","nombre","categoria","color","formalidad","clima","disponible","imagen"])

def save_csv(df, path="closet.csv"):
    df.to_csv(path, index=False)

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

def generar_outfit(df, formalidad, clima):
    filtrado = df[df["disponible"]==1]
    filtrado_fc = filtrado[
        filtrado["formalidad"].apply(lambda f: formalidad in f) &
        filtrado["clima"].apply(lambda c: clima in c or "todo" in c)
    ]
    for _ in range(20):
        outfit = seleccionar_prendas(filtrado_fc)
        if outfit:
            colores = [prenda["color"].lower() for prenda in outfit.values()]
            if armonia_colores(colores):
                return outfit
    return None

# --------------------------
# Interfaz
# --------------------------
st.title("👕 Closet Automático con Armonía de Colores y Lavandería")

tabs = st.tabs(["Generar Outfit", "Agregar Prenda", "Lavandería"])
df = load_csv()

# --------------------------
# Pestaña 1: Generar Outfit
# --------------------------
with tabs[0]:
    formalidad = st.selectbox("Elige formalidad", ["casual","formal"])
    clima = get_weather()
    st.write(f"🌦️ Clima detectado en {CITY}: **{clima}**")

    if "outfit_actual" not in st.session_state:
        st.session_state["outfit_actual"] = None

    # Botón único para generar outfit
    if st.button("🔄 Generar / Reemplazar Outfit", key="generar_outfit"):
        st.session_state["outfit_actual"] = generar_outfit(df, formalidad, clima)

    # Mostrar outfit actual
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

        # Botón de usar outfit con key único
        if st.button("✅ Usar este outfit", key="usar_outfit"):
            ids = [int(p["id"]) for p in outfit.values()]
            df.loc[df["id"].isin(ids), "disponible"] = 0
            save_csv(df)
            st.session_state["outfit_actual"] = None
            st.success("Outfit usado y enviado a lavandería 👕🧺")
    else:
        st.info("Presiona el botón para generar un outfit 😎")

# --------------------------
# Pestaña 2: Agregar Prenda
# --------------------------
with tabs[1]:
    st.header("🛍️ Agregar nueva prenda")
    nombre = st.text_input("Nombre de la prenda")
    categoria = st.selectbox("Categoría", ["superior","inferior","calzado"])
    color = st.text_input("Color (ej: rojo, azul, negro...)")
    formalidad = st.text_input("Formalidad (ej: casual, formal) separadas por coma")
    clima_input = st.text_input("Clima (ej: calor, frio, templado, lluvia) separadas por coma")
    imagen = st.text_input("Ruta de imagen (opcional)")

    if st.button("Agregar prenda"):
        nuevo_id = df["id"].max()+1 if not df.empty else 1
        nueva_prenda = {
            "id": nuevo_id,
            "nombre": nombre,
            "categoria": categoria,
            "color": color,
            "formalidad": [f.strip() for f in formalidad.split(",") if f.strip()],
            "clima": [c.strip() for c in clima_input.split(",") if c.strip()],
            "disponible": 1,
            "imagen": imagen
        }
        df = pd.concat([df, pd.DataFrame([nueva_prenda])], ignore_index=True)
        save_csv(df)
        st.success(f"{nombre} agregada al closet ✅")

# --------------------------
# Pestaña 3: Lavandería
# --------------------------
with tabs[2]:
    st.header("🧺 Lavandería")
    lav = df[df["disponible"]==0]
    if lav.empty:
        st.info("No hay prendas en la lavandería 🎉")
    else:
        for _, prenda in lav.iterrows():
            st.write(f"- {prenda['nombre']} ({prenda['categoria']})")
            img_path = Path(prenda["imagen"])
            if img_path.exists():
                st.image(img_path, use_container_width=True)
            if st.button(f"✅ Marcar como disponible", key=f"lav_{prenda['id']}"):
                df.loc[df["id"]==prenda["id"], "disponible"]=1
                save_csv(df)
                st.success(f"{prenda['nombre']} ahora está disponible")