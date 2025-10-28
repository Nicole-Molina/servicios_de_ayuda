import streamlit as st
import pandas as pd
from unidecode import unidecode
import io

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Servicios de ayuda y comisarías", layout="wide")

st.title("🔍 Buscador de servicios de ayuda y comisarías")

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    establecimientos = pd.read_excel('./assets/establecimientos_consolidados.xlsx')
    comisarias = pd.read_excel('./assets/comisarias.xlsx')
    ubigeos = pd.read_excel('./assets/ubigeos_peru.xlsx')
    return establecimientos, comisarias, ubigeos

# --- BOTÓN PARA LIMPIAR CACHÉ Y RECARGAR ---
st.sidebar.button("🔄 Refrescar datos", on_click=lambda: st.cache_data.clear())

# Llamamos a la función y guardamos los DataFrames
establecimientos, comisarias, ubigeos = cargar_datos()

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
st.subheader("♀️ Servicios de ayuda disponibles")
st.dataframe(establecimientos_filtrado, use_container_width=True)

output_servicios = io.BytesIO()
with pd.ExcelWriter(output_servicios, engine="openpyxl") as writer:
    establecimientos_filtrado.to_excel(writer, index=False, sheet_name="Servicios de ayuda")
output_servicios.seek(0)

st.download_button(
    label="⬇️ Descargar servicios filtrados (Excel)",
    data=output_servicios,
    file_name="servicios_filtrados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.subheader("👮 Comisarías disponibles")
st.dataframe(comisarias_filtrado, use_container_width=True)

output_comisarias = io.BytesIO()
with pd.ExcelWriter(output_comisarias, engine="openpyxl") as writer:
    comisarias_filtrado.to_excel(writer, index=False, sheet_name="Comisarías")
output_comisarias.seek(0)

st.download_button(
    label="⬇️ Descargar comisarías filtradas (Excel)",
    data=output_comisarias,
    file_name="comisarias_filtradas.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# --- DESCARGA CONSOLIDADA ---
st.subheader("📦 Descarga completa")

# Copias de los filtrados
servicios_out = establecimientos_filtrado.copy()
comisarias_out = comisarias_filtrado.copy()

# En comisarías: crear la columna ESTABLECIMIENTO a partir de COMISARIA
comisarias_out["ESTABLECIMIENTO"] = comisarias_out["COMISARIA"]

# Asignar tipo
servicios_out["TIPO"] = "SERVICIO DE AYUDA"
comisarias_out["TIPO"] = "COMISARIA"

# Unir ambas bases
consolidado = pd.concat([servicios_out, comisarias_out], ignore_index=True)

# Eliminar columnas
consolidado = consolidado.drop(columns=["CATEGORIA"])
consolidado = consolidado.drop(columns=["COMISARIA"])

# Asegurar que todos los NaN (si quedaran) estén cubiertos
consolidado.fillna("NO DISPONIBLE", inplace=True)

# Ordenamos base consolidada
columnas = ["TIPO"] + [col for col in consolidado.columns if col != "TIPO"]
consolidado = consolidado[columnas]

# Botón de descarga consolidado
output = io.BytesIO()
with pd.ExcelWriter(output, engine="openpyxl") as writer:
    consolidado.to_excel(writer, index=False, sheet_name="Resultados")
output.seek(0)

st.download_button(
    label="⬇️ Descargar todos los resultados filtrados (Excel)",
    data=output,
    file_name="servicios_y_comisarias_filtrados.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.subheader("🌐 Canales digitales")

st.markdown("""
    Estos son algunos canales digitales donde puedes acceder a servicios de apoyo o realizar denuncias en línea:

    - **Línea 100:** Marcar 100 desde tu celular o teléfono fijo — Atención gratuita 24 horas para personas que experimenten o conozcan casos de violencia.  
    - **Central única de denuncias:** Marcar 1818 desde tu celular o teléfono fijo — Canal de consulta y/o denuncia abierto a casos de violencia.  
    - **Chat 100:** https://chat100.warminan.gob.pe/ — Chat gratuito 24 horas para orientación gratuita respecto de prevención y ayuda en situaciones de violencia.    

    📱 Puedes acceder a ellos desde tu celular o computadora en cualquier momento.
    """)


# --- RESUMEN ---
st.markdown("---")
st.markdown(f"**Resultados:** {len(establecimientos_filtrado)} servicios y {len(comisarias_filtrado)} comisarías mostradas.")
