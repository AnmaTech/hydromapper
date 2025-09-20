import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import oopnet as on
import time
import os
from oopnet.elements.network_components import Reservoir
from oopnet.elements.network_components import Valve
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


def get_Q (Network_new):
    for i in on.get_links(Network_new):
        Qi = (abs(round(report.flow[i.id].mean(),2)))
        Q.append(Qi)
    return Q


def extraer_valvulas(network):
    report = network.run()
    valvulas_dict = {}
    for link in on.get_links(network):
        tipo = None
        if isinstance(link, on.elements.network_components.PRV):
            tipo = 'PRV'
        elif isinstance(link, on.elements.network_components.FCV):
            tipo = 'FCV'
        elif isinstance(link, on.elements.network_components.PBV):
            tipo = 'PBV'
        elif isinstance(link, on.elements.network_components.TCV):
            tipo = 'TCV'
        elif isinstance(link, on.elements.network_components.PSV):
            tipo = 'PSV'
        elif isinstance(link, on.elements.network_components.GPV):
            tipo = 'GPV'
        if tipo:
            valvulas_dict[link.id] = {
                'type': tipo,
                'id': link.id,
                'diameter': float(getattr(link, 'diameter', 0.0)),
                'start_node': getattr(link.startnode, 'id', None),
                'end_node': getattr(link.endnode, 'id', None),
                'start_coordinates': {
                    'x': getattr(link.startnode, 'xcoordinate', None),
                    'y': getattr(link.startnode, 'ycoordinate', None)
                },
                'end_coordinates': {
                    'x': getattr(link.endnode, 'xcoordinate', None),
                    'y': getattr(link.endnode, 'ycoordinate', None)
                },
                'maximum_pressure': float(getattr(link, 'maximum_pressure', 0.0)),
                'status': getattr(link, 'status', None)           }
    return valvulas_dict


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


def graficar_aduccion(dic_nodos, conexiones, coord_x, coord_y, P, cota, id_nodos, umbral):
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
##            st.write(p)
            colores.append('red')  # Presión baja
        else:
            colores.append(cmap(norm(p)))  # Escala azul

    # 🎯 Graficar los puntos con colores personalizados
    sc = ax.scatter(coord_x, coord_y, c=colores, s=100, alpha=0.8, edgecolors='black', linewidths=0.5)

    # 🗺️ Barra de color solo para los valores en escala azul
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])  # Necesario para que funcione el colorbar
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label('Presión (mca)')

    # 🏷️ Agregar etiquetas a cada nodo
    for x, y, etiqueta in zip(coord_x, coord_y, id_nodos):
        ax.text(x, y, str(etiqueta), fontsize=9, color='yellow', ha='center', va='center', zorder=4)

    # 🧼 Limpiar estética del gráfico
    ax.yaxis.set_visible(False)
    for spine in ax.spines.values():
        spine.set_visible(False)

    # 📌 Título
    ax.set_title("Presiones en mca ", fontsize=14, color='Blue', fontweight='bold')

    return fig



def graficar_aduccion_psi(dic_nodos, conexiones, coord_x, coord_y, P_mca, cota,id_nodos, umbral):
    umbral = umbral *0.0142233
    # Convertir presiones de mca a psi
    P_psi = [p * 0.0142233 for p in P_mca]
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
    fig = graficar_aduccion (dic_nodos, conexiones, coord_x, coord_y,P, cota,id_nodos, pmin)
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
    with st.expander("🔍 Ver Tabla de " + col2):
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




def change_status_valve(link, diameter,status,network ):
    on.remove_valve(network=network, id=link.id)
    # add new GPV valve
##    on.add_valve(network=network, valve=on.GPV(id=link.id+'_GPV', comment=None, tag=None, status=status,
##                        diameter=diameter, minorloss=0.0,
##                        startnode=on.get_node(network, link.startnode.id),
##                        headloss_curve=curve_GPV, endnode=on.get_node(network, link.endnode.id)))




##################################################################################


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

                # Ejecutamos la función para obtener el diccionario
                dic_valve = extraer_valvulas(Network_orig)

                # Extraer Diametros
                DIAM_NEW = [link.diameter for link in on.get_links(Network_orig)]


                #############################################################################333
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
                        Control de Válvulas 🔧
                    </h1>
                    """, unsafe_allow_html=True)


                    # 🎚️ Slider con estilo personalizado
                    with st.container():
                        # Diccionario para guardar el estado de cada válvula
                        estado_valvulas = {}

                        # Iteramos sobre cada válvula en el diccionario
                        for valve_id, props in dic_valve.items():
                            tipo = props.get('type', 'Unknown')
                            nombre_valvula = f"{tipo} - {valve_id}"

                            # Creamos el switch (pestillo) para encender/apagar
                            estado = st.toggle(f"{nombre_valvula}", value=(props.get('status') == 'OPEN'))

                            # Guardamos el estado en un diccionario
                            estado_valvulas[valve_id] = 'OPEN' if estado else 'CLOSED'

                        st.subheader('Presión mínima (mca)')
                        pmin = st.slider(" Presión mínima (mca)", min_value=1, max_value=50, step=5)


                def actualizar_estado_valvulas(network, estado_valvulas):
                    """
                    Asigna el estado ('OPEN' o 'CLOSED') a cada válvula en la red
                    según el diccionario estado_valvulas.
                    """
                    for link in on.get_links(network):
                        if link.id in estado_valvulas:
                            nuevo_estado = estado_valvulas[link.id]
                            link.status = nuevo_estado


                actualizar_estado_valvulas(Network_orig, estado_valvulas)


                # 📊 Mostrar gráficas en dos columnas
                with c2:
                    col1, col2 = st.columns(2)

                    with col1:
                        run_plot_presiones(Network_orig,pmin)
                        dic_nodos, conexiones , coord_x, coord_y, P, cota = extraer_nodos(Network_orig)
                        run_tabla_resultados ([node.id for node in on.get_nodes(Network_orig)], P, 'Nodo', 'P (mca)')

                ##        run_plot_D(Network_orig)
                ##        run_tabla_resultados ([link.id for link in on.get_links(Network_orig)], DIAM_NEW, 'Tuberia', 'D(mmm)')

                    with col2:
                        run_plot_presiones_psi(Network_orig,pmin)
                        run_tabla_resultados([node.id for node in on.get_nodes(Network_orig)], [round(p * 0.0142233, 2) for p in P], 'Nodo', 'P (psi)')

                        run_plot_Q(Network_orig)
                        run_tabla_resultados ([link.id for link in on.get_links(Network_orig)],[abs(round(report.flow[i.id].mean(), 2))  for i in on.get_links(Network_orig)],  'Tuberia', 'Q(lps)')
            else:
                        st.warning("⚠️ La red fue cargada pero no contiene tubos.")
    except Exception as e:
        st.error(f"❌ Error al cargar la red: {e}")