import streamlit as st
import pandas as pd
import ast
import os
import requests
import random

st.set_page_config(page_title="Closet Automático", page_icon="👕")

# -------------------------
# FUNCIONES AUXILIARES
# -------------------------
def safe_list(x):
    """Convierte un string tipo '["casual","formal"]' en lista Python real."""
    if isinstance(x, list):
        return x
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except:
            return [s.strip() for s in x.split(",")]
    return []

def load_csv():
    df = pd.read_csv("closet.csv")
    if "disponible" not in df.columns:
        df["disponible"] = 1
    df["formalidad"] = df["formalidad"].apply(safe_list)
    df["clima"] = df["clima"].apply(safe_list)
    return df

def save_csv(df):
    df.to_csv("closet.csv", index=False)

def get_weather():
    """Obtiene clima desde OpenWeatherMap"""
    API_KEY = os.getenv("OPENWEATHER_KEY")
    CITY = os.getenv("CITY", "Mexico City")

    if not API_KEY:
        return None, None  # sin API configurada

    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=es"
    try:
        r = requests.get(url).json()
        temp = r["main"]["temp"]
        desc = r["weather"][0]["description"]

        # Clasificación simplificada
        if temp < 15:
            clima = "frio"
        elif temp > 28:
            clima = "calor"
        else:
            clima = "templado"
        return clima, f"{desc}, {temp}°C"
    except:
        return None, None

# -------------------------
# APP
# -------------------------
st.title("👕 Closet Automático con Clima Real")

df = load_csv()

tab1, tab2, tab3 = st.tabs(["✨ Generar Outfit", "➕ Agregar Prenda", "🧺 Lavandería"])

# -------------------------
# TAB 1: Generar Outfit
# -------------------------
with tab1:
    st.subheader("Generar Outfit")

    clima, clima_txt = get_weather()
    if clima:
        st.success(f"Clima detectado: {clima_txt} → {clima}")
    else:
        clima = st.selectbox("Selecciona clima manualmente:", ["frio", "templado", "calor"])
    
    formalidad = st.selectbox("Selecciona formalidad:", ["casual", "formal", "deportivo"])

    # Filtrar prendas disponibles
    prendas_filtradas = df[
        (df["disponible"] == 1) &
        (df["clima"].apply(lambda c: clima in c)) &
        (df["formalidad"].apply(lambda f: formalidad in f))
    ]

    st.write("Debug - Prendas encontradas:", len(prendas_filtradas))

    if st.button("Generar Outfit"):
        if prendas_filtradas.empty:
            st.error("😢 No hay prendas disponibles con esas condiciones")
        else:
            seleccionadas = prendas_filtradas.sample(min(2, len(prendas_filtradas)))
            for _, row in seleccionadas.iterrows():
                st.image(row["imagen"], width=150, caption=row["nombre"])
            # Botón para mandar a lavandería
            if st.button("Usar este outfit (mandar a lavandería)"):
                df.loc[seleccionadas.index, "disponible"] = 0
                save_csv(df)
                st.success("✅ Prendas enviadas a lavandería")

# -------------------------
# TAB 2: Agregar Prenda
# -------------------------
with tab2:
    st.subheader("Agregar nueva prenda")

    nombre = st.text_input("Nombre de la prenda")
    imagen = st.text_input("URL de imagen")
    formalidad = st.multiselect("Formalidad", ["casual", "formal", "deportivo"])
    clima = st.multiselect("Clima", ["frio", "templado", "calor"])

    if st.button("Guardar prenda"):
        nueva = {
            "nombre": nombre,
            "imagen": imagen,
            "formalidad": formalidad,
            "clima": clima,
            "disponible": 1
        }
        df = pd.concat([df, pd.DataFrame([nueva])], ignore_index=True)
        save_csv(df)
        st.success("👕 Prenda agregada correctamente")

# -------------------------
# TAB 3: Lavandería
# -------------------------
with tab3:
    st.subheader("🧺 Prendas en Lavandería")
    lav = df[df["disponible"] == 0]

    if lav.empty:
        st.info("No hay prendas en lavandería")
    else:
        for _, row in lav.iterrows():
            st.image(row["imagen"], width=120, caption=row["nombre"])
        if st.button("Vaciar lavandería (hacer disponibles todas)"):
            df["disponible"] = 1
            save_csv(df)
            st.success("Todas las prendas están de nuevo disponibles")