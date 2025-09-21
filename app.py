import streamlit as st
import pandas as pd
import random
import json
import os

# -------------------------------
# Función para cargar CSV con parser flexible
# -------------------------------
def safe_parse(value):
    if pd.isna(value):
        return []
    try:
        return json.loads(value)  # intenta cargar como JSON
    except:
        return [v.strip() for v in str(value).split(",") if v.strip()]  # fallback: separar por coma

def load_csv():
    if os.path.exists("closet.csv"):
        df = pd.read_csv("closet.csv")
        if "formalidad" in df.columns:
            df["formalidad"] = df["formalidad"].apply(safe_parse)
        if "clima" in df.columns:
            df["clima"] = df["clima"].apply(safe_parse)
        return df
    else:
        return pd.DataFrame(columns=["id","nombre","tipo","color","formalidad","clima","estado","imagen"])

def save_csv(df):
    df.to_csv("closet.csv", index=False)

# -------------------------------
# App
# -------------------------------
st.title("👕 Closet Automático con Armonía de Colores")

menu = st.sidebar.radio("Menú", ["Generar Outfit", "Agregar Prenda", "Lavandería"])

df = load_csv()

# -------------------------------
# Generar Outfit
# -------------------------------
if menu == "Generar Outfit":
    st.header("Generar Outfit")

    if df.empty:
        st.warning("No tienes prendas en tu closet todavía.")
    else:
        # Solo prendas disponibles
        disponibles = df[df["estado"] == "disponible"]

        if disponibles.empty:
            st.warning("Todas tus prendas están en lavandería 😅")
        else:
            # Elegir al azar
            outfit = disponibles.sample(min(2, len(disponibles)))  # mínimo 2 piezas
            st.write("### Outfit sugerido:")
            for _, row in outfit.iterrows():
                st.write(f"- {row['nombre']} ({row['color']})")
                if pd.notna(row["imagen"]) and os.path.exists(row["imagen"]):
                    st.image(row["imagen"], use_container_width=True)

            # Botones de acción
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Generar otro outfit"):
                    st.experimental_rerun()
            with col2:
                if st.button("✅ Usar este outfit (mandar a lavandería)"):
                    df.loc[outfit.index, "estado"] = "lavandería"
                    save_csv(df)
                    st.success("Las prendas se mandaron a lavandería.")

# -------------------------------
# Agregar Prenda
# -------------------------------
elif menu == "Agregar Prenda":
    st.header("Agregar nueva prenda")

    with st.form("nueva_prenda"):
        nombre = st.text_input("Nombre")
        tipo = st.text_input("Tipo (camisa, pantalón, etc.)")
        color = st.text_input("Color")
        formalidad = st.text_input("Formalidad (ej: casual, formal, sport) separadas por coma")
        clima = st.text_input("Clima (ej: frío, calor, templado) separadas por coma")
        imagen = st.text_input("Ruta de imagen (opcional)")
        submit = st.form_submit_button("Agregar")

    if submit:
        nueva_prenda = {
            "id": len(df) + 1,
            "nombre": nombre,
            "tipo": tipo,
            "color": color,
            "formalidad": [f.strip() for f in formalidad.split(",") if f.strip()],
            "clima": [c.strip() for c in clima.split(",") if c.strip()],
            "estado": "disponible",
            "imagen": imagen
        }
        df = pd.concat([df, pd.DataFrame([nueva_prenda])], ignore_index=True)
        save_csv(df)
        st.success(f"{nombre} agregada al closet ✅")

# -------------------------------
# Lavandería
# -------------------------------
elif menu == "Lavandería":
    st.header("👕 Prendas en Lavandería")

    lav = df[df["estado"] == "lavandería"]
    if lav.empty:
        st.info("No tienes prendas en la lavandería 🎉")
    else:
        st.table(lav[["nombre","tipo","color"]])
        if st.button("🔄 Vaciar lavandería (marcar como disponible)"):
            df.loc[df["estado"] == "lavandería", "estado"] = "disponible"
            save_csv(df)
            st.success("Todas las prendas están disponibles otra vez ✅")