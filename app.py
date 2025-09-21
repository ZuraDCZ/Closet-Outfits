import streamlit as st
import pandas as pd
import random
import requests
import os
from pathlib import Path

# --------------------------
# CONFIGURACIÓN
# --------------------------
API_KEY = os.environ.get("OPENWEATHER_API_KEY")  # Regístrate gratis en https://openweathermap.org/api
if not API_KEY:
    import streamlit as st
    st.error("No se ha configurado la API Key. Por favor, agrega OPENWEATHER_API_KEY en Streamlit Cloud.")
    st.stop()
CITY = "Mexico City"  # Cambia por tu ciudad

# --------------------------
# FUNCIÓN: obtener clima
# --------------------------
def get_weather():
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=es"
    r = requests.get(url).json()
    
    if "main" not in r:  # si hay error
        st.warning(f"No se pudo obtener el clima: {r.get('message', 'Error desconocido')}")
        return "todo"  # usar valor por defecto
    
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

# --------------------------
# FUNCIÓN: generar outfit
# --------------------------
def generar_outfit(df, formalidad, clima):
    # 1️⃣ Filtrar por disponibilidad y formalidad
    filtrado = df[df["disponible"] == 1]
    
    # Intento 1: formalidad + clima
    filtrado_fc = filtrado[(filtrado["formalidad"] == formalidad) & 
                           (filtrado["clima"].isin([clima, "todo"]))]
    outfit = seleccionar_prendas(filtrado_fc)
    if outfit:
        return outfit
    
    # Intento 2: solo formalidad
    filtrado_f = filtrado[filtrado["formalidad"] == formalidad]
    outfit = seleccionar_prendas(filtrado_f)
    if outfit:
        return outfit
    
    # Intento 3: cualquier prenda disponible
    outfit = seleccionar_prendas(filtrado)
    if outfit:
        return outfit
    
    # Si nada funciona, devolver None
    return None

# Función auxiliar para seleccionar superior, inferior y calzado
def seleccionar_prendas(df):
    superior = df[df["categoria"] == "superior"]
    inferior = df[df["categoria"] == "inferior"]
    calzado  = df[df["categoria"] == "calzado"]

    if superior.empty or inferior.empty or calzado.empty:
        return None

    return {
        "Superior": superior.sample(1).iloc[0],
        "Inferior": inferior.sample(1).iloc[0],
        "Calzado": calzado.sample(1).iloc[0]
    }

# --------------------------
# INTERFAZ STREAMLIT
# --------------------------
st.title("👕 Outfit Automático con Fotos - DEV Diego Calderón")

df = pd.read_csv("closet.csv")

formalidad = st.selectbox("Elige formalidad", df["formalidad"].unique())

clima = get_weather()
st.write(f"🌦️ Clima detectado en {CITY}: **{clima}**")

if st.button("Generar Outfit"):
    outfit = generar_outfit(df, formalidad, clima)
    if outfit:
        st.success("Outfit recomendado:")
        cols = st.columns(len(outfit))
        for i, (categoria, prenda) in enumerate(outfit.items()):
            with cols[i]:
                st.markdown(f"**{categoria}**")
                st.write(prenda["nombre"])
                img_path = prenda["imagen"]
                if Path(img_path).exists() or img_path.startswith("http"):
                    st.image(img_path, use_column_width=True)
                else:
                    st.warning("Imagen no encontrada")
    else:
        st.error("No se encontró outfit con esas condiciones 😢")
