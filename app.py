import streamlit as st
import pandas as pd
import requests
from pathlib import Path
import os

st.set_page_config(page_title="Closet Automático", layout="wide")

# --------------------------
# Configuración API clima
# --------------------------
API_KEY = os.environ.get("OPENWEATHER_API_KEY")  # usa variable de entorno
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
    # Intento 1: formalidad + clima
    filtrado_fc = filtrado[(filtrado["formalidad"]==formalidad) &
                           (filtrado["clima"].isin([clima,"todo"]))]
    outfit = seleccionar_prendas(filtrado_fc)
    if outfit:
        return outfit
    # Intento 2: solo formalidad
    filtrado_f = filtrado[filtrado["formalidad"]==formalidad]
    outfit = seleccionar_prendas(filtrado_f)
    if outfit:
        return outfit
    # Intento 3: cualquier disponible
    outfit = seleccionar_prendas(filtrado)
    if outfit:
        return outfit
    return None

# --------------------------
# Interfaz con pestañas
# --------------------------
st.title("👕 Closet Automático")

tabs = st.tabs(["Generar Outfit", "Agregar Prenda"])

# -----------------------------------
# Pestaña 1: Generar Outfit
# -----------------------------------
with tabs[0]:
    df = pd.read_csv("closet.csv") if Path("closet.csv").exists() else pd.DataFrame(columns=["id","nombre","categoria","color","formalidad","clima","disponible","imagen"])
    
    formalidad = st.selectbox("Elige formalidad", ["casual","formal"])
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
                    img_path = Path(prenda["imagen"])
                    if img_path.exists():
                        st.image(img_path, use_container_width=True)
                    else:
                        st.warning("Imagen no encontrada")
        else:
            st.error("No se pudo generar un outfit 😢")

# -----------------------------------
# Pestaña 2: Agregar Prenda
# -----------------------------------
with tabs[1]:
    st.header("🛍️ Agregar nueva prenda")
    nombre = st.text_input("Nombre de la prenda")
    categoria = st.selectbox("Categoría", ["superior", "inferior", "calzado"])
    color = st.text_input("Color")
    formalidad = st.selectbox("Formalidad", ["casual","formal"])
    clima = st.selectbox("Clima", ["calor","frio","templado","lluvia","todo"])
    imagen = st.file_uploader("Subir imagen", type=["jpg","png"])
    
    if st.button("Agregar prenda") and nombre and imagen:
        imagen_path = Path("imagenes") / imagen.name
        imagen_path.parent.mkdir(parents=True, exist_ok=True)
        with open(imagen_path, "wb") as f:
            f.write(imagen.getbuffer())
        
        csv_path = Path("closet.csv")
        if csv_path.exists():
            df = pd.read_csv(csv_path)
        else:
            df = pd.DataFrame(columns=["id","nombre","categoria","color","formalidad","clima","disponible","imagen"])
        
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
        df.to_csv(csv_path, index=False)
        
        st.success(f"Prenda '{nombre}' agregada ✅")
        st.image(imagen_path, use_container_width=True)