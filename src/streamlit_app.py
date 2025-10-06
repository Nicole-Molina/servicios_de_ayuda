import streamlit as st
import pandas as pd
from unidecode import unidecode

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Servicios de ayuda y comisarías", layout="wide")

st.title("🧭 Buscador de Servicios y Comisarías")

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    # Directorio base: la carpeta donde está streamlit_app.py
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Carpeta donde están los archivos de datos
    ASSETS_DIR = os.path.join(BASE_DIR, '..', 'assets')

    # Cargar establecimientos consolidados
    est_file = os.path.join(ASSETS_DIR, 'establecimientos_consolidados.xlsx')
    establecimientos = pd.read_excel(est_file)

    # Cargar comisarías
    com_file = os.path.join(ASSETS_DIR, 'comisarias.xlsx')
    comisarias = pd.read_excel(com_file)

    # Cargar ubigeos
    ubigeos_file = os.path.join(ASSETS_DIR, 'ubigeos.xlsx')
    ubigeos = pd.read_excel(ubigeos_file)

    # Opcional: asegurarse de que los textos estén en mayúscula y sin tildes
    for df in [establecimientos, comisarias, ubigeos]:
        df.columns = [unidecode(col.upper()) for col in df.columns]
        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].apply(lambda x: unidecode(str(x).upper()) if pd.notnull(x) else x)

    return establecimientos, comisarias, ubigeos

# --- NORMALIZACIÓN ---
for df in [establecimientos, comisarias, ubigeos]:
    df.columns = df.columns.str.upper()
    for col in ["DEPARTAMENTO", "PROVINCIA", "DISTRITO"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

# --- PANEL DE FILTROS ---
st.sidebar.header("🔎 Filtros")

# Filtro de departamento
departamentos = sorted(ubigeos["DEPARTAMENTO"].dropna().unique())
departamento_sel = st.sidebar.selectbox("Departamento", ["(Todos)"] + departamentos)

# Filtro de provincia dependiente
if departamento_sel != "(Todos)":
    provincias = sorted(ubigeos.loc[ubigeos["DEPARTAMENTO"] == departamento_sel, "PROVINCIA"].dropna().unique())
else:
    provincias = sorted(ubigeos["PROVINCIA"].dropna().unique())

provincia_sel = st.sidebar.selectbox("Provincia", ["(Todos)"] + provincias)

# Filtro de distrito dependiente
if provincia_sel != "(Todos)":
    distritos = sorted(ubigeos.loc[
        (ubigeos["DEPARTAMENTO"] == departamento_sel) & 
        (ubigeos["PROVINCIA"] == provincia_sel), 
        "DISTRITO"
    ].dropna().unique())
else:
    distritos = sorted(ubigeos["DISTRITO"].dropna().unique())

distrito_sel = st.sidebar.selectbox("Distrito", ["(Todos)"] + distritos)

# --- FUNCIÓN PARA FILTRAR ---
def filtrar_datos(df):
    if departamento_sel != "(Todos)":
        df = df[df["DEPARTAMENTO"] == departamento_sel]
    if provincia_sel != "(Todos)":
        df = df[df["PROVINCIA"] == provincia_sel]
    if distrito_sel != "(Todos)":
        df = df[df["DISTRITO"] == distrito_sel]
    return df

establecimientos_filtrado = filtrar_datos(establecimientos)
comisarias_filtrado = filtrar_datos(comisarias)

# --- RESULTADOS ---
st.subheader("🏥 Servicios de ayuda disponibles")
st.dataframe(establecimientos_filtrado, use_container_width=True)

st.download_button(
    label="⬇️ Descargar servicios filtrados (Excel)",
    data=establecimientos_filtrado.to_csv(index=False).encode('utf-8'),
    file_name="servicios_filtrados.csv",
    mime="text/csv"
)

st.subheader("👮 Comisarías disponibles")
st.dataframe(comisarias_filtrado, use_container_width=True)

st.download_button(
    label="⬇️ Descargar comisarías filtradas (Excel)",
    data=comisarias_filtrado.to_csv(index=False).encode('utf-8'),
    file_name="comisarias_filtradas.csv",
    mime="text/csv"
)

# --- RESUMEN ---
st.markdown("---")
st.markdown(f"**Resultados:** {len(establecimientos_filtrado)} servicios y {len(comisarias_filtrado)} comisarías mostradas.")
