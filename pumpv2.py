import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import warnings
import shutil
warnings.filterwarnings(action='ignore')
import pandas as pd
import oopnet as on
import numpy as np
import math
import tempfile
import os




def read_catalogo_pump(col1):

    # 📁 Subir archivo Excel
    uploaded_file = st.sidebar.file_uploader("Selecciona el archivo Excel (.xlsx)", type=["xlsx"])

    # 🧩 Columnas requeridas
    columnas_requeridas = ['FABRICANTE', 'MODELO', 'POTENCIA (HP)', 'Q (l/min)', 'H (m)']

    if uploaded_file is not None:
        try:
            # 📖 Leer archivo Excel
            df = pd.read_excel(uploaded_file)

            # ✅ Validar columnas
            if all(col in df.columns for col in columnas_requeridas):
                df_filtrado = df[columnas_requeridas]
                with col1:
                    st.success("✅ Catálogo de Bombas cargado correctamente.")
                    st.markdown('<h3 style="color: blue;">🛒 Catalogo de Bombas </h3>', unsafe_allow_html=True)
                    st.dataframe(df_filtrado)  # Mostrar tabla para revisión
                return df_filtrado
            else:
                faltantes = [col for col in columnas_requeridas if col not in df.columns]
                with col1:
                    st.error(f"❌ El archivo no tiene el formato esperado. Faltan columnas: {faltantes}")
                return None
        except Exception as e:
            with col1:
                st.error(f"❌ Error al leer el archivo Excel: {e}")
            return None
    else:
        with col1:
            st.info("📎 Por favor sube tu Catalogo de Bombas...")
        return None

def verificar_descendente(lista):
    for i in range(len(lista) - 1):
        if lista[i] < lista[i + 1]:
            return False
    return True

def verificar_ascendente(lista):
    for i in range(len(lista) - 1):
        if lista[i] > lista[i + 1]:
            return False
    return True

# Para seguir depurando valores locos en el excel de las curvas
def depurar_lista(fila_depurada):
    fila_depurada2 = []
    for elemento in fila_depurada:
        elemento = elemento.strip()  # Eliminar espacios en blanco al principio y al final
        if ',' in elemento:  # Si el elemento tiene una coma
            if elemento.endswith(',') or elemento.endswith('-'):  # Si el elemento termina con una coma
                continue  # No agregar el elemento a la lista depurada
            else:
                fila_depurada2.append(elemento)  # Agregar el elemento a la lista depurada
        if elemento.count('.') == 1 and not any(p in elemento for p in ',;:!'):
            nuevo_elemento = elemento.replace('.', ',')
            fila_depurada2.append(nuevo_elemento )
    return fila_depurada2


def get_flow_and_head_values(fila):
        verificar_orden = 0
        # Recorrer las filas del DataFrame
        # Crear el string para comentario o descripcion
        coment =fila[0] + ' ' + str(fila[2]) + ' Hp'
        potencia_hp = (fila[2])
        # crear el id de la curva
        id_curve = str(fila[1]).replace(' ','')
        # eliminar nan
        fila_new=list(fila[3:-1].dropna())
        # Crear una nueva lista con los elementos convertidos en texto
        fila_new = [str(elemento) for elemento in fila_new]
##        if id_curve =='MOT1.5-2':
##            st.text('string')
##            st.text(fila_new)
##        if id_curve =='HAPPY10HP': st.text(fila_new)
        fila_new=depurar_lista(fila_new)
        fila_depurada=[]
        for elemento in fila_new:
            valores = str(elemento).split(',')
            if len(valores) == 2 and valores[0].replace('.', '', 1).isdigit() and valores[1].replace('.', '', 1).isdigit():
                fila_depurada.append(elemento)
##        if id_curve =='MOT1.5-2':
##            st.text('flltro mio')
##            st.text(fila_depurada)
##
##        if id_curve =='MOT1.5-2':
##            st.text('depurada')
##            st.text(fila_depurada)

        # extraer el caudal y la carga
        flow_values =[round(float(valor.split(',') [0])/60,2) for valor in fila_depurada];
        head_values =[round(float(valor.split(',') [1]),2)  for valor in fila_depurada]
        if verificar_descendente(head_values) and verificar_ascendente(flow_values):
            verificar_orden = 1
        else:
            verificar_orden = 0
        return flow_values , head_values,coment, id_curve,verificar_orden, potencia_hp

def insert_curve(id_curve,coment ,flow_values,head_values, temp_file):
    file=temp_file.name
    network = on.Network.read(file)
    curve=on.Curve(id_curve,comment=None, tag=None, xvalues=flow_values,
                       yvalues=head_values)
    on.add_curve(network=network, curve=on.Curve(id_curve,comment=None, tag=None,
                    xvalues=flow_values , yvalues=head_values))
    return curve, network

def replace_Pump(network, link,curve):
    on.remove_pump(network=network, id=link.id)
    on.add_pump( network=network , pump = on.Pump( id=link.id, comment=None, tag=None,  status='OPEN',
                                                  startnode=on.get_node(network, link.startnode.id),
                                                  endnode=on.get_node(network, link.endnode.id), power=None,
                                                  head=curve, speed=1.0, pattern=None, setting=None))
    return network

# Filtrar solo los junction eliminando el embalse para no obtener presiones cero
def filter_series_by_index(series, index_list):
    if isinstance(series, pd.Series) and isinstance(index_list, list):
        filtered_series = series[series.index.isin(index_list)]
        return filtered_series
    else:
        print("Los parámetros no son del tipo esperado.")


def positive_pressure (report, network):
    verificar_presiones_pos =0
    # obtener solo los elelentos que son nodos no embalses
    solo_nodos =[junc.id for junc in on.get_junctions(network)]
    # eliminar nodos de embalses
    nodos_validos = filter_series_by_index(report.pressure, solo_nodos)
    todos_positivos = all( nodos_validos> 0)
    if todos_positivos:
        verificar_presiones_pos =1
    else:
        verificar_presiones_pos =0
    return verificar_presiones_pos

def filter_pmin_pmax(report, pmin, pmax, network):
        verificar_pmin_max=0
        # obtener solo los elelentos que son nodos no embalses
        solo_nodos =[junc.id for junc in on.get_junctions(network)]
        # eliminar nodos de embalses
        nodos_validos = filter_series_by_index(report.pressure, solo_nodos)
        if (nodos_validos >= pmin).all() and (nodos_validos <= pmax).all():
            verificar_pmin_max=1
        else:
            verificar_pmin_max=0
        return verificar_pmin_max

def fill_dataframe(df, series,coment, id_curve, potencia_hp, objeto1):
    # Crear una lista
    nueva_lista = [coment, id_curve, potencia_hp, objeto1 ]
    # Crear un diccionario con las etiquetas y los valores de la nueva lista
    nuevos_datos = {'Fabricante': nueva_lista[0], 'Modelo': nueva_lista[1], 'Potencia Hp': nueva_lista[2], 'Network':nueva_lista[3]}
    # Crear una nueva serie con los datos existentes y los nuevos datos
    nuevos_datos_serie = pd.Series(nuevos_datos)
    series_new = pd.concat([nuevos_datos_serie, series])
    #print(series_new )
    if isinstance(df, pd.DataFrame) and isinstance(series, pd.Series):
        df = pd.concat([df, series_new.to_frame().T], ignore_index=True)
    else:
        print("Los parámetros no son del tipo esperado.")
    return df


def graficar_resultados(df_pressure_sorted, sub_choice, col3):
        # Crear gráfica con matplotlib la red
        df_selected = df_pressure_sorted[df_pressure_sorted['Fabricante']==sub_choice]
        report = df_selected ['Network'][0].run()
        p = report.pressure
        f = report.flow
        v = report.velocity
        fig1 = df_selected ['Network'][0].plot(nodes=p, links=f)
        with col3:
            st.pyplot(fig1)
##        # Aqui van presiones y velocidades
##        fig2, (ax1, ax2) = plt.subplots(1, 2)
##        # Graficar en el primer subplot
##        ax1.bar(p.keys(), p.values, color ='maroon', width = 0.4)
##        ax1.set_title('Presiones en Nodos')
##        ax1.set_xlabel('Nodos')
##        ax1.set_ylabel('Presion (m)')
##        # Graficar en el segundo subplot
##        ax2.bar(v.keys(), v.values, color ='red', width = 0.4)
##        ax2.set_title('Velocidades m/s')
##        ax2.set_xlabel('Tuberías')
##        st.pyplot(fig2)


# Función para buscar bomba
def buscar_bomba(df, temp_file,presion_minima, presion_maxima,col3):
    # Leer red
    file=temp_file.name
    network = on.Network.read(file)
    report = network.run()

##    # Ruta del archivo transformado
##    ruta_excel = "C://Users//Gateway//Desktop//Efra//python_epanet//BD_pump_transformado.xlsx"
##
##    # Leer el archivo
##    df = pd.read_excel(ruta_excel)
##    st.write(df)


    # Caclulo principal
    # Definir presiones maximas y minimas
    pmin = presion_minima
    pmax = presion_maxima

    # Data Frame que contien la soluciones validas
    df_pressure=pd.DataFrame()
    diccionario_network = {}

    # Definir el dataframe para guardar escenarios de bombas factibles
    for link in on.get_links(network):
        if (isinstance(link,on.elements.network_components.Pump)): # filtering PRV valves types only

##            # reemplzar curva por curva
##            for indice, fila in df_curve1.iterrows():
##                # Extraer valores de la curva caracteristica
##                flow_values , head_values, coment, id_curve,verificar_orden, potencia_hp = get_flow_and_head_values(fila)

##                # Función8 para verificar si la curva es lógica (H desciende cuando Q aumenta)
##            def verificar_orden(q_list, h_list):
##                return all(h_list[i] >= h_list[i+1] for i in range(len(h_list)-1)) and all(q_list[i] <= q_list[i+1] for i in range(len(q_list)-1))

            # Agrupar por modelo
##            st.write(df.columns)
            modelos = df.groupby(['FABRICANTE', 'MODELO', 'POTENCIA (HP)'])
            # Verifica si hay grupos
            if modelos.ngroups == 0:
                st.write("No hay grupos disponibles.")


##            st.write(type(modelos))

            # Recorrer cada modelo
            for (fabricante, modelo, potencia_hp), grupo in modelos:
##                st.write(grupo, fabricante, modelo, potencia_hp)
                flow_values = [round(q / 60, 3) for q in grupo['Q (l/min)'].tolist()]  # Convertir a L/s
##                st.write(flow_values)
                head_values = grupo['H (m)'].tolist()
##                st.write(head_values)
                coment = f"{fabricante} {potencia_hp} Hp"
                id_curve = str(modelo).replace(" ", "").replace("-", "_")
##                verificar_orden = verificar_orden(flow_values, head_values)

                curve, network = insert_curve(id_curve,coment ,flow_values,head_values, temp_file)
                # reemplazar la bomba
                network = replace_Pump(network, link,curve)
                # Verificar solo `presiones positivas y que esten en el rango
                verificar_presiones_pos = positive_pressure (report, network)

                if verificar_presiones_pos==1:
##                    st.write(verificar_presiones_pos)
                    verificar_pmin_max      = filter_pmin_pmax(report, pmin, pmax, network)
##                    verificar_pmin_max=1
                    # Filtra las presiones que esten por debajo de pmax y arriba de pmin
                    if verificar_pmin_max ==1  :
                        #filtrar por Q max simulado vs Q max bomba
                        factor_Qmax =1.15
                        try:
                            if max(flow_values)*factor_Qmax > report.flow[link.id]:
                                # Agregar objetos al diccionario e ir guardando redes que son solucion
                                objeto1 = network
                                diccionario_network[coment] = objeto1

                                df_pressure = fill_dataframe(df_pressure, report.pressure,coment, id_curve, potencia_hp, objeto1)
                        except:
                            st.text(' xx La Curva de la Bomba ' + id_curve + ' No fue evaluada')


                    #except :
##                        st.text(id_curve)
##                        pass
    df_curve1= df
    if (len(df_pressure))>0:

        st.text(' ✅ Se revisaron :' + str(len(df_curve1)) + ' Bombas¡¡ 🤓')
        st.text(' ✅ Un Total de  :' + str(len(df_pressure)) + ' cumplen con las restricciones¡¡ 🤓')

        # Tabla de presiones ordenadas
        df_pressure_sorted = df_pressure.sort_values(by='Potencia Hp', ascending=True).reset_index(drop=True)
##        df_pressure_sorted.Network[0].write(path + 'network_PUMP_new.inp')
##        st.text(' ✅ Se creo un fichero de epanet usando la Bomba ' + str(df_pressure_sorted.Fabricante[0]) + ' 🤓')
        #· Recalcular diametros economicos usando la primera bomba
        report = df_pressure_sorted.Network[0].run()
##        recalcular_diam_econom(report)

        # Filtrar solo las columnas deseadas
        columnas_deseadas = ['Fabricante', 'Modelo', 'Potencia Hp']  # Lista de columnas deseadas
        df_pressure_filtrado = df_pressure_sorted .filter(columnas_deseadas)
##        st.subheader(' ')
        # Subheader en color azul
        st.markdown('<h3 style="color: blue;">🔎 Bombas seleccionadas:</h3>', unsafe_allow_html=True)
##        st.table(df_pressure_filtrado)
        # 🔘 Mostrar cada bomba como toggle
        return df_pressure_filtrado


##
##        # desplegar bombas seleccionadas
##        st.subheader(' ')
##        # Subtítulo de menor tamaño
##        st.write('<h3 style="font-size: 14px;color: blue;">Ver Gráficas y resultados</h3>', unsafe_allow_html=True)
##        lista_pump = list(df_pressure_filtrado['Fabricante'])
##        sub_choice       =  st.selectbox('Modelo', lista_pump, 0)
##        # Crear una figura vacía al inicio
##        graficar_resultados(df_pressure_sorted, sub_choice,col3)
    else:
        st.text(' ')
        st.text(' 🤓 Se revisaron :' + str(len(df_curve1)) + ' Bombas¡¡')
        st.text(' ⚠️ Ninguna Bomba de la Base de datos es adecuada para el sistema¡¡¡ 😩 ')

# Recalcular diametros con la Bomba seleccionada
def recalcular_diam_econom(report):
    #p = report.pressure
    f = report.flow; Diam_econ =[ round(1000*((4*(abs(q/1000)/velocidad_economica)/math.pi)**.5),2) for q in f.values]
    # Leer el fichero Excel y crear el dataframe
    full_path = path+ 'diam.xlsx'
    df = pd.read_excel(full_path)
    interno_mm = df['interno  mm'].tolist()
    # Definir la función para comparar los valores y crear la nueva lista
    diam_nuevos_comerciales = comparar_diametros(interno_mm, Diam_econ)
    # Asignar diametros comerciales y recalcular red



# Comparar diam
def comparar_diametros(interno_mm, diam_calc):
    diam_com = []
    for valor in diam_calc:
        valor_superior = float('inf')
        for diametro in interno_mm:
            if diametro >= valor and diametro < valor_superior:
                valor_superior = diametro
        diam_com.append(valor_superior)
    return diam_com

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

def run():
    col1,col2,col3= st.columns((3.2,3.2,8))
    with col1:
        presion_minima = st.slider(label='🕙 Presion minima (m)', min_value= 0,  max_value=50,   step=5,    value=0)
    with col2:
        presion_maxima = st.slider(label='🕤 Presion maxima (m)', min_value= 50, max_value=1000, step=50,   value=350)


    # 📤 Botón para cargar archivo EPANET
    uploaded_file = st.sidebar.file_uploader("Cargar archivo EPANET (.inp)", type=['inp'])

    if uploaded_file is not None:
        # 🗂️ Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".inp") as temp_file:
            temp_file.write(uploaded_file.getvalue())
            path_file = temp_file.name
        with col1:
            st.success("✅ Archivo EPANET cargado correctamente.")
        # Aquí puedes continuar con la lectura del archivo usando OOPNET o WNTR
    else:
        with col1:
            st.warning("⚠️Por favor, sube tu archivo EPANET en la barra lateral ")

    # Boton para cargar Tabla de curvas comerciales
    df_pump=read_catalogo_pump(col1)




    # Botón para buscar bomba
    st.subheader(' ')
    with col2:
        if st.button('🏃 Buscar Bomba en Catálogos disponibles ->> '):
            df_pressure_filtrado = buscar_bomba(df_pump, temp_file,presion_minima, presion_maxima,col3)
            try:
                for index, row in df_pressure_filtrado.iterrows():
                    bomba_id = f"{row['Fabricante']} - {row['Potencia Hp']} HP"
                    if st.toggle(f"🔽 {bomba_id}", key=index):
                        st.info(f"📌 Modelo disponible: {row['Modelo']}")
            except:
                pass









