import streamlit as st
import pandas as pd
import ast
import random
import os

st.set_page_config(page_title="Closet Automático", page_icon="👕", layout="wide")

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
            return [x]
    return []

@st.cache_data
def load_csv():
    df = pd.read_csv("closet.csv")
    df["formalidad"] = df["formalidad"].apply(safe_list)
    df["clima"] = df["clima"].apply(safe_list)
    return df

def save_csv(df):
    df.to_csv("closet.csv", index=False)

def mostrar_prenda(row):
    st.image(row["imagen"], width=150)
    st.write(f"👕 {row['nombre']}")
    st.write(f"🎨 Color: {row['color']}")
    st.write(f"👔 Formalidad: {', '.join(row['formalidad'])}")
    st.write(f"☁️ Clima: {', '.join(row['clima'])}")

# ---------------------------
# App principal
# ---------------------------

st.title("👕 Closet Automático con Lavandería y Colores")

menu = st.sidebar.radio("Menú", ["Generar Outfit", "Agregar Prenda", "Lavandería"])

df = load_csv()

# ---------------------------
# Generar outfit
# ---------------------------
if menu == "Generar Outfit":
    st.header("✨ Generar Outfit")

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
            prenda_sup = superiores.sample(1).iloc[0]
            prenda_inf = inferiores.sample(1).iloc[0]
            prenda_calzado = calzado.sample(1).iloc[0]

            st.subheader("👕 Outfit generado:")
            cols = st.columns(3)
            with cols[0]:
                mostrar_prenda(prenda_sup)
            with cols[1]:
                mostrar_prenda(prenda_inf)
            with cols[2]:
                mostrar_prenda(prenda_calzado)

            if st.button("✅ Usar este outfit"):
                df.loc[df["id"] == prenda_sup["id"], "disponible"] = 0
                df.loc[df["id"] == prenda_inf["id"], "disponible"] = 0
                df.loc[df["id"] == prenda_calzado["id"], "disponible"] = 0
                save_csv(df)
                st.success("👕 Prendas enviadas a lavandería")

        else:
            st.error("😢 No hay prendas disponibles con esas condiciones")

# ---------------------------
# Agregar prenda
# ---------------------------
elif menu == "Agregar Prenda":
    st.header("➕ Agregar nueva prenda")

    with st.form("nueva_prenda"):
        nombre = st.text_input("Nombre de la prenda")
        categoria = st.selectbox("Categoría", ["superior", "inferior", "calzado"])
        color = st.text_input("Color")
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
elif menu == "Lavandería":
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