import streamlit as st
import pandas as pd
import random
import requests
from pathlib import Path

# --------------------------
# CONFIGURACIÓN
# --------------------------
API_KEY = "bb36a253a616b556fc1726ef28255ce7"  # Regístrate gratis en https://openweathermap.org/api
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
    filtrado = df[(df["disponible"] == 1) & 
                  (df["formalidad"] == formalidad) & 
                  (df["clima"].isin([clima, "todo"]))]

    superior = filtrado[filtrado["categoria"] == "superior"]
    inferior = filtrado[filtrado["categoria"] == "inferior"]
    calzado  = filtrado[filtrado["categoria"] == "calzado"]

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
st.title("👕 Outfit Automático con Fotos")

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
