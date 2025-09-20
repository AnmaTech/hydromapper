import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import oopnet as on
import time
import os
from oopnet.elements.network_components import Reservoir
from oopnet.elements import Reservoir, Pump, Valve
import math
from matplotlib.collections import LineCollection
import pandas as pd



### 🌐 Configuración de la página
##st.set_page_config(
##    page_title="HyDroMapper",
##    page_icon="💧",
##    layout="wide"
##)

########## FUNCIONES################################33333

def extraer_nodos(network):
    report = network.run()
    coord_x = []
    coord_y = []
    cota=[]
    P = []
    dic_nodos = {}
    for junc in on.get_nodes(network):
        if isinstance(junc, Reservoir):
            coord_x.append(junc.xcoordinate)
            coord_y.append(junc.ycoordinate)
            cota.append(junc.elevation)
##            st.write(junc.elevation)
            P.append(junc.head)
            dic_nodos[junc.id] = (junc.xcoordinate, junc.ycoordinate)
        else:
            coord_x.append(junc.xcoordinate)
            coord_y.append(junc.ycoordinate)
            cota.append(junc.elevation)
            P.append(round(report.pressure[junc.id].mean()))
            dic_nodos[junc.id] = (junc.xcoordinate, junc.ycoordinate)
        conexiones = []
    for i in on.get_links(network):
        conexiones.append((i.startnode.id, i.endnode.id))
    return dic_nodos, conexiones, coord_x, coord_y, P, cota





# Funcion ## Hacer una Funcion para cambio de diametro en la red de manera automática desde Python hacia Epanet
def replace_diam (network, DIAM_NEW):
    for link,diam_new in zip(on.get_links(network),DIAM_NEW):
        link.diameter=diam_new
    network_new=network
    return network_new


def cargar_EPANET():
    # 📥 Widget para cargar archivo .inp de EPANET
    archivo_inp = st.sidebar.file_uploader("📂 Selecciona tu archivo EPANET (.inp)", type=["inp"])

    if archivo_inp is None:
        st.warning("⚠️ Por favor, selecciona un archivo .inp para continuar.")
        return None
    else:
        # Crear carpeta temporal si no existe
        os.makedirs("temp", exist_ok=True)

        # Ruta local donde se guardará el archivo
        ruta_local = os.path.join("temp", archivo_inp.name)

        # Guardar el archivo en disco
        with open(ruta_local, "wb") as f:
            f.write(archivo_inp.getbuffer())

        # Retornar la ruta para usarla en otras funciones
        return ruta_local


# 🔄 Función para calcular diámetros en mm
def calcular_diametros(network, velocidad):
    report = network.run()
    caudales = []
    diametros_mm = []
    for i in on.get_links(Network_orig):
        Q = (abs(round(report.flow[i.id].mean(),2)))/1000  # m³/s
        if Q == 0:
            D_mm = 50  # Valor mínimo por defecto
        else:
            D_m = math.sqrt((4 * Q) / (math.pi * velocidad))
            D_mm = round(D_m * 1000, 2)
        diametros_mm.append(D_mm)
    return diametros_mm



def graficar_aduccion(dic_nodos, conexiones, coord_x, coord_y, P, cota, id_nodos, umbral,network):
    fig, ax = plt.subplots(figsize=(7.5, 3.1))
                        # 🟦 Embalses
    embalses = {}
    for node in on.get_nodes(network):
        if isinstance(node, Reservoir):
            embalses[node.id] = {
                'xcoordinate': node.coordinates[0],
                'ycoordinate': node.coordinates[1]
            }

    # 💪 Bombas
    bombas = []
    for link in on.get_links(network):
        if isinstance(link, Pump):
            bombas.append((link.startnode.id, link.endnode.id))

    # 🧩 Válvulas
    valvulas = []
    for link in on.get_links(network):
        if isinstance(link, Valve):
            valvulas.append((link.startnode.id, link.endnode.id))


    fig, ax = plt.subplots(figsize=(7.5, 3.1))

    # 🔗 Dibujar las conexiones diferenciadas
    for inicio, fin in conexiones:
        try:
            x_values = [dic_nodos[inicio][0], dic_nodos[fin][0]]
            y_values = [dic_nodos[inicio][1], dic_nodos[fin][1]]

            if bombas and (inicio, fin) in bombas or (fin, inicio) in bombas:
                ax.plot(x_values, y_values, color='blue', linewidth=3, label='Bomba')
            elif valvulas and (inicio, fin) in valvulas or (fin, inicio) in valvulas:
                ax.plot(x_values, y_values, color='green', linestyle='dotted', linewidth=2, label='Válvula')
            else:
                ax.plot(x_values, y_values, 'k-', linewidth=1)  # Línea negra normal
        except:
            pass

    # 🎨 Preparar colores personalizados
    P_array = np.array(P)
    colores = []

    cmap = plt.get_cmap('Blues')
    norm = plt.Normalize(vmin=min(P_array), vmax=max(P_array))

    for p in P_array:
        if p < umbral:
            colores.append('red')  # Presión baja
        else:
            colores.append(cmap(norm(p)))  # Escala azul

    # 🎯 Graficar los puntos con colores personalizados
    sc = ax.scatter(coord_x, coord_y, c=colores, s=100, alpha=0.8, edgecolors='black', linewidths=0.5)

    # 🟦 Dibujar embalses como rectángulos
    if embalses:
        for emb_id, coords in embalses.items():
            x, y = coords['xcoordinate'], coords['ycoordinate']
            ax.add_patch(plt.Rectangle((x - 0.5, y - 0.5), 1, 1, fill=True, color='cyan', edgecolor='black', label='Embalse'))
            ax.text(x, y, emb_id, fontsize=9, color='black', ha='center', va='center', zorder=5)

    # 🗺️ Barra de color
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Presión (mca)')

    # 🏷️ Etiquetas de nodos
    for x, y, etiqueta in zip(coord_x, coord_y, id_nodos):
        ax.text(x, y, str(etiqueta), fontsize=9, color='black', ha='center', va='center', zorder=4)

    # 🧼 Estética
    ax.yaxis.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    # Ajustar límites
    ax.autoscale()
    ax.set_aspect('equal')

    ax.set_title("Presiones en mca ", fontsize=14, color='Blue', fontweight='bold')

    return fig



##def graficar_aduccion(dic_nodos, conexiones, coord_x, coord_y, P, cota, id_nodos, umbral):
##    fig, ax = plt.subplots(figsize=(7.5, 3.1))
##
##    # 🔗 Dibujar las conexiones
##    for inicio, fin in conexiones:
##        try:
##            x_values = [dic_nodos[inicio][0], dic_nodos[fin][0]]
##            y_values = [dic_nodos[inicio][1], dic_nodos[fin][1]]
##            ax.plot(x_values, y_values, 'k-')  # Línea negra
##        except:
##            pass
##
##    # 🎨 Preparar colores personalizados
##    P_array = np.array(P)
##    colores = []
##
##    # Usar colormap azul para valores por encima del umbral
##    cmap = plt.get_cmap('Blues')
##    norm = plt.Normalize(vmin=min(P_array), vmax=max(P_array))
##
##    for p in P_array:
####        st.write(p)
##        if p < umbral:
##            colores.append('red')  # Presión baja
##        else:
##            colores.append(cmap(norm(p)))  # Escala azul
##
##    # 🎯 Graficar los puntos con colores personalizados
##    sc = ax.scatter(coord_x, coord_y, c=colores, s=100, alpha=0.8, edgecolors='black', linewidths=0.5)
##
##    # 🗺️ Barra de color solo para los valores en escala azul
##    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
##    sm.set_array([])  # Necesario para que funcione el colorbar
##    cbar = plt.colorbar(sm, ax=ax)
##    cbar.set_label('Presión (mca)')
##
##    # 🏷️ Agregar etiquetas a cada nodo
##    for x, y, etiqueta in zip(coord_x, coord_y, id_nodos):
##        ax.text(x, y, str(etiqueta), fontsize=9, color='black', ha='center', va='center', zorder=4)
##
##    # 🧼 Limpiar estética del gráfico
##    ax.yaxis.set_visible(False)
##    for spine in ax.spines.values():
##        spine.set_visible(False)
##
##    # 📌 Título
##    ax.set_title("Presiones en mca ", fontsize=14, color='Blue', fontweight='bold')
##
##    return fig



def graficar_aduccion_psi(dic_nodos, conexiones, coord_x, coord_y, P_mca, cota,id_nodos, umbral):
    umbral = umbral *(1/0.703085)
    # Convertir presiones de mca a psi
    P_psi = [p * (1/0.703085) for p in P_mca]
    P = P_psi
    fig, ax = plt.subplots(figsize=(7.5, 3.1))
    # 🔗 Dibujar las conexiones
    for inicio, fin in conexiones:
        try:
            x_values = [dic_nodos[inicio][0], dic_nodos[fin][0]]
            y_values = [dic_nodos[inicio][1], dic_nodos[fin][1]]
            ax.plot(x_values, y_values, 'k-')  # Línea negra
        except:
            pass
    # 🎨 Preparar colores personalizados
    P_array = np.array(P)
    colores = []
    # Usar colormap azul para valores por encima del umbral
    cmap = plt.get_cmap('Blues')
    norm = plt.Normalize(vmin=min(P_array), vmax=max(P_array))
    for p in P_array:
        if p < umbral:
            colores.append('red')  # Presión baja
        else:
            colores.append(cmap(norm(p)))  # Escala azul

    # 🎯 Graficar los puntos con colores personalizados
    sc = ax.scatter(coord_x, coord_y, c=colores, s=100, alpha=0.8, edgecolors='black', linewidths=0.5)

    # 🗺️ Barra de color solo para los valores en escala azul
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Necesario para que funcione el colorbar
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Presión (psi)')

    # 🏷️ Agregar etiquetas a cada nodo
    for x, y, etiqueta in zip(coord_x, coord_y, id_nodos):
        ax.text(x, y, str(etiqueta), fontsize=9, color='black', ha='center', va='center', zorder=4)

    # 🧼 Limpiar estética del gráfico
    ax.yaxis.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

        # 📌 Título
    ax.set_title("Presiones en psi ", fontsize=14, color='Blue', fontweight='bold')
    return fig




def graficar_aduccion_por_caudal(dic_nodos, conexiones, coord_x, coord_y, Q):
    fig, ax = plt.subplots(figsize=(7.5, 3.1))

    # 🧩 Preparar segmentos de líneas (tuberías)
    segmentos = []
    for (inicio, fin) in conexiones:
        try:
            x_values = [dic_nodos[inicio][0], dic_nodos[fin][0]]
            y_values = [dic_nodos[inicio][1], dic_nodos[fin][1]]
            segmentos.append([(x_values[0], y_values[0]), (x_values[1], y_values[1])])
        except:
            pass

    # 🎨 Crear colección de líneas con color basado en Q
    Q_array = np.array(Q)
    lineas = LineCollection(segmentos, cmap='plasma', linewidths=2, array=Q_array)
    ax.add_collection(lineas)

    # 📍 Graficar nodos como puntos negros
    ax.scatter(coord_x, coord_y, color='black', s=30, zorder=3)

    # 🗺️ Barra de color para los caudales
    cbar = plt.colorbar(lineas, ax=ax)
    cbar.set_label('Caudal (lps)')

    # 🧼 Limpiar estética del gráfico
    ax.yaxis.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Ajustar límites
    ax.autoscale()
    ax.set_aspect('equal')
    ax.set_title("Caudales en lps", fontsize=14, color='green', fontweight='bold', loc='center')

    return fig



def graficar_aduccion_por_diametro(dic_nodos, conexiones, coord_x, coord_y, DIAM):
    fig, ax = plt.subplots(figsize=(7.5, 3.1))

    # 🧩 Preparar segmentos de líneas (tuberías)
    segmentos = []
    for (inicio, fin) in conexiones:
        try:
            x_values = [dic_nodos[inicio][0], dic_nodos[fin][0]]
            y_values = [dic_nodos[inicio][1], dic_nodos[fin][1]]
            segmentos.append([(x_values[0], y_values[0]), (x_values[1], y_values[1])])
        except:
            pass

    # 🎨 Crear colección de líneas con color basado en DIAM
    diam_array = np.array(DIAM)
    lineas = LineCollection(segmentos, cmap='viridis', linewidths=2, array=diam_array)
    ax.add_collection(lineas)
    # 📍 Graficar nodos como puntos negros
    ax.scatter(coord_x, coord_y, color='black', s=30, zorder=3)
    # 🗺️ Barra de color para los diámetros
    cbar = plt.colorbar(lineas, ax=ax)
    cbar.set_label('Diámetro (mm)')
    # 🧼 Limpiar estética del gráfico
    ax.yaxis.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    # Ajustar límites
    ax.autoscale()
    ax.set_aspect('equal')
    ax.set_title("Diámetro (mm)", fontsize=14, color='red', fontweight='bold', loc='center')
    return fig


def run_plot_presiones(Network,pmin):
    id_nodos = [junc.id for junc in on.get_nodes(Network)]
    # Correr red y extraer dato para la Grafic
    dic_nodos, conexiones , coord_x, coord_y, P, cota = extraer_nodos(Network )
    # Graficar las tuberías
    fig = graficar_aduccion (dic_nodos, conexiones, coord_x, coord_y,P, cota,id_nodos, pmin,Network)
    # Mostrar la gráfica en Streamlit
    st.pyplot(fig)

def run_plot_presiones_psi(Network,pmin):
    id_nodos = [junc.id for junc in on.get_nodes(Network)]
    # Correr red y extraer dato para la Grafic
    dic_nodos, conexiones , coord_x, coord_y, P, cota = extraer_nodos(Network )
    # Graficar las tuberías
    fig = graficar_aduccion_psi(dic_nodos, conexiones, coord_x, coord_y, P, cota,id_nodos, pmin)
    # Mostrar la gráfica en Streamlit
    st.pyplot(fig)


def run_plot_Q(Network_new):
    report = Network_new.run()
    caudales = []
    diametros_mm = []
    for i in on.get_links(Network_new):
        Q = (abs(round(report.flow[i.id].mean(),2)))  # m³/s
        caudales.append(Q)
    # Correr red y extraer dato para la Grafic
    dic_nodos, conexiones , coord_x, coord_y, P, cota = extraer_nodos(Network_new )
    fig =graficar_aduccion_por_caudal(dic_nodos, conexiones, coord_x, coord_y, caudales )
    st.pyplot(fig)


def run_plot_D(Network_new):
    # Correr red y extraer dato para la Grafic
    dic_nodos, conexiones , coord_x, coord_y, P, cota = extraer_nodos(Network_new )
    fig = graficar_aduccion_por_diametro(dic_nodos, conexiones, coord_x, coord_y, DIAM_NEW)
    st.pyplot(fig)


def run_tabla_resultados (id, valor, col1, col2):
    df = pd.DataFrame()
    df[col1]=id ;     df[col2]=valor
    with st.expander("🔍 Ver Tabla de " + col2 ):
        st.table(df)

def run_tabla_resultados2 (id, valor, valor3 ,col1, col2, col3):
    df = pd.DataFrame()
    df[col1]=id ;     df[col2]=valor ; df[col3]=valor3
    with st.expander("🔍 Ver Tabla de " + col2 ):
        st.table(df)

def aproximar_diametros_comerciales(diametros_mm):
    # Lista de diámetros comerciales en pulgadas (½" a 200")
    diam_comerciales_pulg = [
        0.5, 0.75, 1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10, 12,
        14, 16, 18, 20, 24, 30, 36, 42, 48, 54, 60, 72, 84, 96,
        108, 120, 144, 160, 180, 200
    ]

    resultado = []
    for d_mm in diametros_mm:
        d_pulg = d_mm / 25.4  # Convertir a pulgadas
        # Buscar el primer diámetro comercial mayor o igual
        comercial = next((dc for dc in diam_comerciales_pulg if dc >= d_pulg), diam_comerciales_pulg[-1])
        resultado.append(comercial)

    return resultado



def replace(network,cota_embalse, id):
    for junc in on.get_nodes(network):
        if isinstance(junc, Reservoir) and id== junc.id:
            junc.head=float(cota_embalse)
##            st.write(junc)

def extraer_embalses(network):
    dic_embalse = {}
    for junc in on.get_nodes(network):
        if isinstance(junc, Reservoir):
            dic_embalse[junc.id] = {
                'xcoordinate': junc.xcoordinate,
                'ycoordinate': junc.ycoordinate,
                'head': junc.head
            }
    return dic_embalse


##################################################################################


####path_file= cargar_EPANET()
##path_file='C://Users//Gateway//Desktop//simple1.inp'
##Network_orig          =  on.Network.read(path_file)
##cantidad_tubos        =  len (on.get_links(Network_orig))
##if (cantidad_tubos)>0:
##    # ✅ Mostrar ruta como confirmación
##    st.success(f"✅ Red cargada correctamente")
##    run_plot_presiones(Network_orig)

def run():
    path_file= cargar_EPANET()
    # 🧭 Verificar que el archivo existe
     # 🛑 Verificar si se obtuvo una ruta válida
    if path_file is None:
        st.error("❌ No se seleccionó ningún archivo o la ruta es inválida.")
        return

    # ✅ Verificar que el archivo existe
    if not os.path.isfile(path_file):
        st.error(f"❌ El archivo no existe en la ruta: {path_file}")
        return

    try:
            # 📥 Intentar cargar la red
            Network_orig = on.Network.read(path_file)

            # 🔗 Verificar cantidad de tubos
            cantidad_tubos = len(on.get_links(Network_orig))

            if cantidad_tubos > 0:
                st.success(f"✅ Red cargada correctamente desde: {path_file}")

                # 📂 Cargar red original
##                path_file = 'C://Users//Gateway//Desktop//simple1.inp'
                ##path_file = 'C://Users//Gateway//Desktop//Santiago_cloro.inp'
                Network_orig = on.Network.read(path_file)
                report      = Network_orig.run()

                dic_embalse = (extraer_embalses(Network_orig))

                # 🎨 Estilo personalizado para el slider
                st.markdown("""
                    <style>
                    .custom-slider .stSlider label {
                        font-size: 25px !important;
                        color: #0072B5 !important;
                        font-weight: bold;
                    }
                    </style>
                """, unsafe_allow_html=True)

                # 🧱 Columnas para layout
                c1, c2 = st.columns((2.5, 12))

                with c1:
                    st.markdown("""
                    <h1 style='color: #0072B5; font-size: 36px; font-weight: bold;'>
                        Embalse
                    </h1>
                    """, unsafe_allow_html=True)
                    # 🎚️ Slider con estilo personalizado
                    # Diccionario para almacenar los valores seleccionados por el usuario
                    valores_embalses = {}

                    for embalse_id, propiedades in dic_embalse.items():
                        with st.container():
                            st.subheader(f'{embalse_id}')
                            cota = st.slider(
                                f"Carga del Embalse {embalse_id} (msnm)",
                                min_value=0,
                                max_value=100,
                                value=int(propiedades["head"]),
                                step=1
                            )
                            valores_embalses[embalse_id] = cota
                    st.subheader('Presión mínima (mca)')
                    pmin = st.slider(" Presión mínima (mca)", min_value=1, max_value=50, step=5)

                 # Se ereemplzana los valores de otas de empbalses
                for embalse_id, cota_embalse in valores_embalses.items():
                    replace(Network_orig, cota_embalse, embalse_id)

                # 📊 Mostrar gráficas en dos columnas
                with c2:
                    col1, col2 = st.columns(2)

                    with col1:
                        run_plot_presiones(Network_orig,pmin)
                        dic_nodos, conexiones , coord_x, coord_y, P, cota = extraer_nodos(Network_orig)
                        run_tabla_resultados2 ([node.id for node in on.get_nodes(Network_orig)], P, [round(p * (1/0.703085), 2) for p in P], 'Nodo', 'P (mca)','P (psi)')

                    with col2:
                        run_plot_Q(Network_orig)
                        report =Network_orig.run()
                        run_tabla_resultados(    [link.id for link in on.get_links(Network_orig)],  [int(abs(report.flow[i.id].mean())) for i in on.get_links(Network_orig)],
                            'Tuberia',
                            'Q(lps)'
                        )


            else:
                        st.warning("⚠️ La red fue cargada pero no contiene tubos.")
    except Exception as e:
        st.error(f"❌ Error al cargar la red: {e}")







##
##
##
### 📂 Cargar red original
##path_file = 'C://Users//Gateway//Desktop//simple1.inp'
####path_file = 'C://Users//Gateway//Desktop//Santiago_cloro.inp'
##path_file = 'C://Users//Gateway//Desktop//HidroLago//Proyectos de Ing//EB_TULE_new.inp'
##Network_orig = on.Network.read(path_file)
##


##        run_plot_presiones_psi(Network_orig,pmin)
##        run_tabla_resultados([node.id for node in on.get_nodes(Network_orig)], [round(p * (1/0.703085), 2) for p in P], 'Nodo', 'P (psi)')


#