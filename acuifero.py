import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy.interpolate import griddata
from datetime import datetime
import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import folium
from folium.raster_layers import ImageOverlay
from streamlit_folium import st_folium
import os
from scipy.spatial import ConvexHull






# 📂 Ruta del archivo
excel_path = r"C://Users//Gateway//Desktop//Tabla Pozos.xlsx"



def guardar_raster_como_png(zi, xi, yi, output_path='raster.png'):
    plt.figure(figsize=(8, 6))
    plt.imshow(zi, extent=[xi.min(), xi.max(), yi.min(), yi.max()],
               origin='lower', cmap='viridis', alpha=0.5)
    plt.axis('off')
    plt.savefig(output_path, bbox_inches='tight', pad_inches=0, transparent=True)
    plt.close()


# 📥 Cargar y validar datos
def cargar_datos(df):
##    df = pd.read_excel(path)
    if df.shape[1] < 6:
        st.warning("⚠️ La tabla debe tener al menos 6 columnas en el orden especificado.")
        return None
    errores = []
    if not isinstance(df.iloc[0, 0], str):
        errores.append("La primera columna debe ser el ID del pozo (texto).")
    # ✅ Validar fecha en múltiples formatos
    fecha_valida = False
    fecha_raw = str(df.iloc[0, 1])
    formatos_fecha = [
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S,%f",
        "%Y-%m-%d %H:%M:%S"
    ]
    for fmt in formatos_fecha:
        try:
            datetime.strptime(fecha_raw, fmt)
            fecha_valida = True
            break
        except:
            continue
    if not fecha_valida:
        errores.append("La segunda columna debe ser una fecha válida (DD/MM/YYYY, ISO 8601 o YYYY-MM-DD HH:MM:SS).")
    for i in [2, 3, 4, 5]:
        try:
            float(df.iloc[0, i])
        except:
            errores.append(f"La columna {i+1} debe ser numérica.")

    if errores:
        for e in errores:
            st.warning("⚠️ " + e)
        return None
    df.columns = ['Pozo', 'Fecha', 'X', 'Y', 'Nivel Estático', df.columns[-1]]
    return df

# 📊 Interpolación para contornos y raster
def generar_malla(df, columna, resolucion=100):
##    st.write(df)
    xi = np.linspace(df['X'].min(), df['X'].max(), resolucion)
    yi = np.linspace(df['Y'].min(), df['Y'].max(), resolucion)
    xi, yi = np.meshgrid(xi, yi)
    zi = griddata((df['X'], df['Y']), df[columna], (xi, yi), method='cubic')
    return xi, yi, zi

def ejecutar_todo(df):
    df = cargar_datos(df)
##    df = pd.read_excel(archivo)

    if df is not None:
        col1, col2 = st.columns([1.2, 1])

        with col1:
            with st.container(border = True):
                st.subheader("Nivel Estático (Isopiezas)")

                        # Genera la malla
                xi, yi, zi = generar_malla(df, 'Nivel Estático')
                # Crea figura base con el raster
                fig1 = px.imshow(
                    zi,
                    origin='lower',
                    labels={'x': 'Longitud', 'y': 'Latitud', 'color': 'Nivel Estático'},
                    x=np.linspace(df['X'].min(), df['X'].max(), zi.shape[1]),
                    y=np.linspace(df['Y'].min(), df['Y'].max(), zi.shape[0]),
                )
                # Agrega las curvas de nivel (isopiezas)
                fig1.add_trace(go.Contour(
                    z=zi,
                    x=np.linspace(df['X'].min(), df['X'].max(), zi.shape[1]),
                    y=np.linspace(df['Y'].min(), df['Y'].max(), zi.shape[0]),
                    contours=dict(
                        coloring='none',  # Solo líneas, sin relleno
                        showlabels=True,  # Mostrar etiquetas de nivel
                        labelfont=dict(size=18, color='black')
                    ),
                    line=dict(width=2, color='black'),
                    showscale=False  # Oculta la barra de color del contorno
                ))
                # Agrega los puntos originales como scatter
                fig1.add_trace(go.Scatter(
                    x=df['X'],
                    y=df['Y'],
                    mode='markers+text',
                    marker=dict(color='white', size=18, line=dict(width=2, color='black')),

                ))
                # Trazar las etiquetas como texto en las mismas coordenadas
                fig1.add_trace(go.Scatter(
                    x=df['X'],
                    y=df['Y'],
                    mode='text',
                    text=df.iloc[:, 0],  # Etiquetas desde la primera columna
                    textposition='top center',
                    textfont=dict(color='black', size=24),
                    showlegend=False  # No mostrar en la leyenda
                ))
                # Ajusta diseño
                fig1.update_layout(height=680, mapbox_style="open-street-map")
                # Muestra el gráfico
                st.plotly_chart(fig1, use_container_width=True)



        with col2:
            with st.container(border=True):
                st.subheader('Mapa de ' + df.columns[-1])

                # Genera la malla
                xi2, yi2, zi2 = generar_malla(df, df.columns[-1])

                fig2 = px.imshow(
                    zi2,
                    origin='lower',
                    labels={'x': 'Longitud', 'y': 'Latitud', 'color': df.columns[-1]},
                    x=np.linspace(df['X'].min(), df['X'].max(), zi2.shape[1]),
                    y=np.linspace(df['Y'].min(), df['Y'].max(), zi2.shape[0]),
                    color_continuous_scale=px.colors.sequential.Plasma[::-1]  # 🔄 Invertido
                )
                # Agrega las curvas de nivel (isopiezas)
                fig2.add_trace(go.Contour(
                    z=zi2,
                    x=np.linspace(df['X'].min(), df['X'].max(), zi2.shape[1]),
                    y=np.linspace(df['Y'].min(), df['Y'].max(), zi2.shape[0]),
                    contours=dict(
                        coloring='none',         # Solo líneas, sin relleno
                        showlabels=True,         # Mostrar etiquetas de nivel
                        labelfont=dict(size=20, color='white')
                    ),
                    line=dict(width=2, color='black'),
                    showscale=False             # Oculta la barra de color del contorno
                ))

                # Ajusta diseño
                fig2.update_layout(height=680, mapbox_style="open-street-map")

                # Muestra el gráfico
                st.plotly_chart(fig2, use_container_width=True)



    # Centrar mapa
    centro = [df['Y'].mean(), df['X'].mean()]
    m = folium.Map(location=centro, zoom_start=13, tiles=None)

    # Fondo satelital
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Esri Satellite',
        overlay=False,
        control=True
    ).add_to(m)

    # Guardar imagen raster
    guardar_raster_como_png(zi2, xi, yi)

    # Superponer imagen raster
    ImageOverlay(
        name='Nivel Estático',
        image='raster.png',
        bounds=[[df['Y'].min(), df['X'].min()], [df['Y'].max(), df['X'].max()]],
        opacity=8,
        interactive=True,
        cross_origin=False
    ).add_to(m)

    # Añadir puntos con popups
    for _, row in df.iterrows():
        folium.Marker(
            location=[row['Y'], row['X']],
            popup=f"<b>{row['Pozo']}</b>",
            icon=folium.Icon(color='blue', icon='info-sign')
        ).add_to(m)

    # Mostrar mapa en Streamlit
    with st.container(border=True):
        st.subheader("🌐 Mapa Satelital con Raster de "+ df.columns[-1])
        st_data = st_folium(m, width=1200, height=600)


def cargar_Excel():
    # 📥 Widget para cargar archivo Excel
    archivo_excel = st.sidebar.file_uploader("📂 Selecciona tu archivo Excel", type=["xlsx"])
    if archivo_excel is None:
        st.warning("⚠️ Por favor, selecciona un archivo Excel para continuar.")
        return None
    else:
        ruta_local = os.path.join("temp", archivo_excel.name)
        os.makedirs("temp", exist_ok=True)
        with open(ruta_local, "wb") as f:
            f.write(archivo_excel.getbuffer())
        df = pd.read_excel(ruta_local)
        ejecutar_todo(df)
