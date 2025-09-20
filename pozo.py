import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from fpdf import FPDF
import datetime





# Ruta de la imagen (asegúrate de que exista en tu sistema)
image_path = "HydroMapper/img/Esquema_pozo.png"

def generar_pdf_bomba(caudal, HB, potencia, imagen_path, nombre_archivo="reporte_bomba.pdf"):
    from fpdf import FPDF
    import datetime

    pdf = FPDF()
    pdf.add_page()

    # Título
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Reporte de Capacidad de Bomba", ln=True, align='C')

    # Fecha
    pdf.set_font("Arial", '', 12)
    fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(200, 10, f"Fecha: {fecha_actual}", ln=True, align='C')

    pdf.ln(10)

    # Datos
    pdf.set_font("Arial", '', 14)
    pdf.cell(200, 10, f"🔹 Caudal (lps): {caudal}", ln=True)
    pdf.cell(200, 10, f"🔹 HB (m): {HB}", ln=True)
    pdf.cell(200, 10, f"🔹 Potencia (HP): {potencia}", ln=True)

    pdf.ln(10)

    # Imagen
    try:
        pdf.image(imagen_path, x=30, w=150)
    except Exception as e:
        pdf.cell(200, 10, f"⚠️ Error al cargar imagen: {e}", ln=True)

    # Guardar PDF
    pdf.output(nombre_archivo)
    return nombre_archivo

#####################################################################3
def hazen_williams_loss(Q, C, D, L):
    """
    Calcula la pérdida de carga por fricción usando la ecuación de Hazen-Williams.

    Parámetros:
    Q -- Caudal (m³/s)
    C -- Coeficiente de Hazen-Williams
    D -- Diámetro interno de la tubería (m)
    L -- Longitud de la tubería (m)

    Retorna:
    hf -- Pérdida de carga (m)
    """
    if C <= 0 or D <= 0 or L <= 0 or Q < 0:
        raise ValueError("Todos los parámetros deben ser positivos y C, D, L mayores que cero.")

    hf = 10.67 * ((Q / (C * D**2.63))**1.852) * L
    return hf


def limpiar_campos():
    for key in [
        "diametro_vertical", "longitud_vertical", "sumergencia",
        "abatimiento", "presion_descarga", "eficiencia",
        "diametro_horizontal", "longitud_horizontal", "profundidad_freatica",
        "altura_descarga", "caudal", "C"
    ]:
        st.session_state[key] = ""


################################################

def ejecutar_pozo():

    col1, col2 = st.columns((5,7))

    with col1:

        with st.container(border=True):
            st.subheader("🔧 Parámetros del Pozo-Sistema")

            # Crear 4 columnas
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                diametro_vertical = st.text_input("Diámetro vertical (mm)", value="150", key="diametro_vertical")
                longitud_vertical = st.text_input("Longitud vertical (m)", value="12", key="longitud_vertical")
                sumergencia = st.text_input("Sumergencia (m)", value="3.5", key="sumergencia")

            with c2:
                abatimiento = st.text_input("Abatimiento (m)", value="5", key="abatimiento")
                presion_descarga = st.text_input("Presión de descarga (mca)", value="20", key="presion_descarga")
                eficiencia = st.text_input("Eficiencia (%)", value="60", key="eficiencia")

            with c3:
                diametro_horizontal = st.text_input("Diámetro horizontal (mm)", value="101", key="diametro_horizontal")
                longitud_horizontal = st.text_input("Longitud horizontal (m)", value="2000", key="longitud_horizontal")
                profundidad_freatica = st.text_input("Profundidad freática (m)", value="15", key="profundidad_freatica")

            with c4:
                altura_descarga = st.text_input("Altura de descarga (m)", value="10", key="altura_descarga")
                caudal = st.text_input("Caudal (lps)", value="5", key="caudal")
                C = st.text_input("C (Hazen-Williams)", value="130", key="C")



    ###################################3333333
        c11,c12 =  st.columns(2)

        with c11:
            if st.button("⭐ Calcular Bomba   ᯓ➤"):
                try:
                    # Convertir entradas a float
                    Q = float(caudal)
                    C = float(C)
                    Dv = float(diametro_vertical)
                    Lv = float(longitud_vertical)
                    Dh = float(diametro_horizontal)
                    Lh = float(longitud_horizontal)

                    # Nuevas conversiones
                    abat = float(abatimiento)
                    sumerg = float(sumergencia)
                    presion = float(presion_descarga)
                    altura = float(altura_descarga)
                    profundidad = float(profundidad_freatica)
                    eficiencia = float(eficiencia)

                    # Validar valores positivos
                    if any(val <= 0 for val in [Q, C, Dv, Lv, Dh, Lh, presion, altura, profundidad, eficiencia]) or abat < 0 or sumerg < 0:
                        st.warning("⚠️ Todos los valores deben ser numéricos y mayores que cero (excepto abatimiento y sumergencia que pueden ser cero).")
                    else:
                        hfv = hazen_williams_loss(Q / 1000, C, Dv / 1000, Lv)
                        hfh = hazen_williams_loss(Q / 1000, C, Dh / 1000, Lh)
                        Delta_H = abat + profundidad + altura
                        HB = round(Delta_H + hfv + hfh + presion,1)
                        Potencia = round(1000*HB*Q/(76*eficiencia*10))

##                        # Generar el PDF con la imagen incluida
##                        archivo_pdf = generar_pdf_bomba(Q, HB, Potencia, image_path)

                        # Mostrar resultados
                        with col1:


                            with st.container(border=True):
                                st.markdown(f"""
                                ### ✅ Capacidad de La Bomba

                                <span style='font-size:26px'>
                                🔹 Caudal (lps): <span style='color:red'>{caudal}</span>
                                🔹 HB (m): <span style='color:red'>{HB}</span>
                                🔹 Potencia (HP): <span style='color:red'>{Potencia}</span>
                                </span>
                                """, unsafe_allow_html=True)

                except ValueError as e:
                    st.error("❌ Por favor, ingresa valores numéricos válidos en todos los campos.")




        with c12:
            limpiar_campo = st.button("Reset")#,on_click=limpiar_campos())




    # Mostrar la imagen
    with col2:
        with st.container(border = True  ):
            st.image(image_path ,use_container_width = True)



    with col1:

        st.subheader("🔎 Evaluar una Bomba")

        with st.expander("🔍 Evaluar una Bomba"):


            # Contenedor para ingresar los tres pares H-Q
            with st.container(border=True):
                h_values = []
                q_values = []
                for i in range(1, 4):
                    c1, c2 = st.columns(2)
                    with c1:
                        h = st.text_input(f"H{i} (m)", key=f"h{i}")
                    with c2:
                        q = st.text_input(f"Q{i} (lps)", key=f"q{i}")

                    # Validación de entrada
                    if h and q:
                        try:
                            h_val = float(h)
                            q_val = float(q)
                            h_values.append(h_val)
                            q_values.append(q_val)
                        except ValueError:
                            st.error(f"Par {i}: H y Q deben ser valores numéricos.")

            # Botón para construir la curva
            if st.button("✨ Calcular Punto de Operación"):
                if len(h_values) < 3 or len(q_values) < 3:
                    st.warning("Debe ingresar al menos tres pares válidos.")
                else:
                    # Validación de comportamiento físico
                    q_array = np.array(q_values)
                    h_array = np.array(h_values)

                    q_increasing = np.all(np.diff(q_array) > 0)
                    h_decreasing_with_q = np.all(np.diff(h_array) < 0)

                    h_increasing = np.all(np.diff(h_array) > 0)
                    q_decreasing_with_h = np.all(np.diff(q_array) < 0)

                    if not (h_decreasing_with_q or q_decreasing_with_h):
                        st.warning("La curva no cumple con el comportamiento esperado: H debe disminuir con Q o Q debe disminuir con H.")
                    else:
                        # Ajuste polinómico de segundo grado: H = A - BQ - CQ²
                        coeffs = np.polyfit(q_array, h_array, 2)
                        A, B, C = coeffs

                        # Generar puntos para la curva ajustada
                        q_fit = np.linspace(min(q_array), max(q_array), 100)
                        h_fit = np.polyval(coeffs, q_fit)

                        # Mostrar coeficientes
                        st.success(f"Curva ajustada: H = {A:.2f} - {abs(B):.2f}Q - {abs(C):.2f}Q²")

                        # Graficar
                        fig, ax = plt.subplots()
                        ax.plot(q_array, h_array, 'ro', label='Datos ingresados')
                        ax.plot(q_fit, h_fit, 'b-', label='Curva ajustada')
                        ax.set_xlabel("Q (lps)")
                        ax.set_ylabel("H (m)")
                        ax.set_title("Curva Característica")
                        ax.legend()
                        ax.grid(True)
                        st.pyplot(fig)

                    # Parámetros del sistema (deben estar definidos antes)
                try:
                    abat = float(abatimiento)
                    sumerg = float(sumergencia)
                    presion = float(presion_descarga)
                    altura = float(altura_descarga)
                    profundidad = float(profundidad_freatica)
                    Q_test = np.linspace(min(q_array), max(q_array), 100) / 1000  # m³/s
                    C_hw = float(C)
                    Dv_m = float(diametro_vertical) / 1000
                    Lv_m = float(longitud_vertical)
                    Dh_m = float(diametro_horizontal) / 1000
                    Lh_m = float(longitud_horizontal)
                    Delta_H = abat + profundidad + altura
                    presion_m = presion

                    # Calcular pérdidas por fricción
                    hf_v = np.array([hazen_williams_loss(q, C_hw, Dv_m, Lv_m) for q in Q_test])
                    hf_h = np.array([hazen_williams_loss(q, C_hw, Dh_m, Lh_m) for q in Q_test])
                    H_sistema = Delta_H + hf_v + hf_h + presion_m

                    # Calcular curva característica
                    H_bomba = np.polyval(coeffs, Q_test * 1000)  # volver a lps

                    # Buscar punto de intersección
                    diff = np.abs(H_bomba - H_sistema)
                    idx = np.argmin(diff)
                    Q_operacion = Q_test[idx] * 1000  # lps
                    H_operacion = H_bomba[idx]

                    # Graficar ambas curvas
                    fig2, ax2 = plt.subplots()
                    ax2.plot(Q_test * 1000, H_bomba, 'b-', label='Curva Característica')
                    ax2.plot(Q_test * 1000, H_sistema, 'g--', label='Curva del Sistema')
                    ax2.plot(Q_operacion, H_operacion, 'ro', label=f'Punto de operación\nQ={Q_operacion:.2f} lps, H={H_operacion:.2f} m')
                    ax2.set_xlabel("Q (lps)")
                    ax2.set_ylabel("H (m)")
                    ax2.set_title("Intersección: Curva de Bomba vs. Curva del Sistema")
                    ax2.legend()
                    ax2.grid(True)
                    st.pyplot(fig2)

                    st.success(f"🔧 Punto de operación encontrado: Q = {Q_operacion:.2f} lps, H = {H_operacion:.2f} m")

                except Exception as e:
                    st.error(f"❌ Error al calcular la curva del sistema: {e}")