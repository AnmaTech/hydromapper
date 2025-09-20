import streamlit as st
from PIL import Image
import acuifero as Acui
import pozo as pozo
import epanet_diseno as epanet_diseno
import epanet_operacion as epanet_ope
import pumpv2 as pump
import Embalse as embalse
import os
#os.environ["PATH"] += os.pathsep + os.path.expanduser("~/.local/bin")

# 🌐 Configuración de la página
st.set_page_config(
    page_title="HyDroMapper",
    page_icon="💧",
    layout="wide"
)

# 📌 Cargar logo en la barra lateral
with st.sidebar:
    #logo = Image.open("img/logoAnma.jpg")
    logo = Image.open("img/logoAnma.jpg")
    st.image(logo)

    usuario = st.text_input("Usuario")
    contraseña = st.text_input("Contraseña", type="password")

    opcion = st.radio("Seleccione", ["💧 Bomba - Pozos", "🌎 Acuíferos", "🧊 Embalse", "✍🏻 Diseño - redes","⚡ Operación - redes",
                    "🔎Selección-Bombas","❌ Salir"])



#####################################################################3
# 🚀 Pantalla principal según opción
if opcion == "💧 Bomba - Pozos":
    st.title("💧 Bomba - Pozos")
    pozo.ejecutar_pozo()

elif opcion == "🌎 Acuíferos":
    st.title("🌎 Acuíferos")
    Acui.cargar_Excel()

elif opcion == "✍🏻 Diseño - redes":
    st.title("✍🏻 Diseño de redes")
    epanet_diseno.run()

elif opcion == "⚡ Operación - redes":
    st.title("⚡ Operación de redes")
    epanet_ope.run()
elif opcion == "🔎Selección-Bombas":
    st.title("🔎Selección-Bombas")
    pump.run()

elif opcion == "🧊 Embalse":
    st.title("🧊 Embalse")
    embalse.run()


elif opcion == "❌ Salir":
    st.title("👋 Hasta pronto")

    st.markdown("Gracias por usar la aplicación. Puedes cerrar la pestaña o volver al menú lateral.")



