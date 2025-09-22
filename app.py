import streamlit as st
import pandas as pd
import ast
import requests
import random

st.set_page_config(page_title="Closet Automático", page_icon="👕", layout="wide")

API_KEY = "TU_API_KEY"  # <-- pon aquí tu clave de OpenWeatherMap
CITY = "Mexico City"

# ---------------------------
# Funciones auxiliares
# ---------------------------

def safe_list(x):
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except:
            return [s.strip() for s in x.split(",")]
    return []

@st.cache_data
def load_csv():
    df = pd.read_csv("closet.csv")
    df["formalidad"] = df["formalidad"].apply(safe_list)
    df["clima"] = df["clima"].apply(safe_list)
    return df

def save_csv(df):
    df.to_csv("closet.csv", index=False)

def get_weather():
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=es"
        r = requests.get(url).json()
        temp = r["main"]["temp"]
        if temp >= 26:
            return "calor"
        elif 18 <= temp < 26:
            return "templado"
        else:
            return "frio"
    except:
        return None

def mostrar_prenda(row):
    st.image(row["imagen"], width=150)
    st.write(f"👕 {row['nombre']}")
    st.write(f"🎨 Color: {row['color']}")
    st.write(f"👔 Formalidad: {', '.join(row['formalidad'])}")
    st.write(f"☁️ Clima: {', '.join(row['clima'])}")

# ---------------------------
# Colores (ángulos aproximados en rueda HSV)
# ---------------------------
color_wheel = {
    "rojo": 0,
    "naranja": 30,
    "amarillo": 60,
    "verde": 120,
    "azul": 240,
    "morado": 270,
    "rosa": 300,
    "blanco": None,
    "negro": None,
    "gris": None
}

def colores_combinan(c1, c2):
    if c1 not in color_wheel or c2 not in color_wheel:
        return True  # colores neutros o desconocidos combinan con todo
    h1, h2 = color_wheel[c1], color_wheel[c2]
    if h1 is None or h2 is None:
        return True
    diff = abs(h1 - h2)
    diff = min(diff, 360 - diff)
    return diff in [0, 30, 60, 180]  # monocromático, análogo o complementario

# ---------------------------
# App principal
# ---------------------------

st.title("👕 Closet Automático con Colores + Clima + Lavandería")

tab1, tab2, tab3 = st.tabs(["Generar Outfit", "Agregar Prenda", "Lavandería"])

df = load_csv()

# ---------------------------
# Generar outfit
# ---------------------------
with tab1:
    st.header("✨ Generar Outfit")

    clima_auto = get_weather()
    if clima_auto:
        st.info(f"☀️ Clima detectado: {clima_auto}")
        clima_seleccionado = clima_auto
    else:
        clima_seleccionado = st.selectbox("Selecciona el clima:", ["calor", "templado", "frio"])

    formalidad_seleccionada = st.selectbox("Selecciona formalidad:", ["casual", "formal"])

    if st.button("🎲 Generar Outfit"):
        disponibles = df[df["disponible"] == 1]

        superiores = disponibles[(disponibles["categoria"] == "superior") &
                                 (disponibles["clima"].apply(lambda x: clima_seleccionado in x)) &
                                 (disponibles["formalidad"].apply(lambda x: formalidad_seleccionada in x))]

        inferiores = disponibles[(disponibles["categoria"] == "inferior") &
                                 (disponibles["clima"].apply(lambda x: clima_seleccionado in x)) &
                                 (disponibles["formalidad"].apply(lambda x: formalidad_seleccionada in x))]

        calzado = disponibles[(disponibles["categoria"] == "calzado") &
                              (disponibles["clima"].apply(lambda x: clima_seleccionado in x)) &
                              (disponibles["formalidad"].apply(lambda x: formalidad_seleccionada in x))]

        if not superiores.empty and not inferiores.empty and not calzado.empty:
            outfit = None
            for _ in range(20):  # intentamos varias combinaciones
                prenda_sup = superiores.sample(1).iloc[0]
                prenda_inf = inferiores.sample(1).iloc[0]
                if colores_combinan(prenda_sup["color"], prenda_inf["color"]):
                    prenda_calzado = calzado.sample(1).iloc[0]
                    outfit = (prenda_sup, prenda_inf, prenda_calzado)
                    break

            if outfit:
                st.subheader("👕 Outfit generado:")
                cols = st.columns(3)
                for i, prenda in enumerate(outfit):
                    with cols[i]:
                        mostrar_prenda(prenda)

                if st.button("✅ Usar este outfit"):
                    for prenda in outfit:
                        df.loc[df["id"] == prenda["id"], "disponible"] = 0
                    save_csv(df)
                    st.success("👕 Prendas enviadas a lavandería")
            else:
                st.error("😢 No se encontró combinación de colores adecuada")
        else:
            st.error("😢 No hay prendas disponibles con esas condiciones")

# ---------------------------
# Agregar prenda
# ---------------------------
with tab2:
    st.header("➕ Agregar nueva prenda")

    with st.form("nueva_prenda"):
        nombre = st.text_input("Nombre de la prenda")
        categoria = st.selectbox("Categoría", ["superior", "inferior", "calzado"])
        color = st.text_input("Color (ej: rojo, azul, negro)")
        formalidad = st.multiselect("Formalidad", ["casual", "formal"])
        clima = st.multiselect("Clima", ["calor", "templado", "frio"])
        imagen = st.text_input("Ruta de la imagen (ej: imagenes/camisa_blanca.jpeg)")
        submit = st.form_submit_button("Agregar")

        if submit:
            new_id = df["id"].max() + 1 if not df.empty else 1
            nueva_fila = {
                "id": new_id,
                "nombre": nombre,
                "categoria": categoria,
                "color": color,
                "formalidad": formalidad,
                "clima": clima,
                "disponible": 1,
                "imagen": imagen
            }
            df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
            save_csv(df)
            st.success(f"Prenda {nombre} agregada con éxito ✅")

# ---------------------------
# Lavandería
# ---------------------------
with tab3:
    st.header("🧺 Lavandería")

    lav = df[df["disponible"] == 0]

    if lav.empty:
        st.info("👌 No hay prendas en lavandería")
    else:
        for _, row in lav.iterrows():
            with st.expander(row["nombre"]):
                mostrar_prenda(row)

        if st.button("♻️ Vaciar lavandería (marcar como disponible)"):
            df["disponible"] = 1
            save_csv(df)
            st.success("Todas las prendas están disponibles nuevamente ✅")