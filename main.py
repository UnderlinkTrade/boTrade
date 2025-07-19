import streamlit as st
from datetime import datetime
import uuid
import os
import json

from utils.storage import guardar_sesion, cargar_sesion
from utils.logic import (
    agregar_jugador, registrar_compra, validar_compra,
    calcular_balance, cerrar_sesion, generar_cuadratura_final,
    registrar_retiro, calcular_resultado_final
)

# Configuración inicial
st.set_page_config(page_title="Caja Póker", layout="wide")
st.title("🃏 Gestión de Caja - Partida de Póker")

# Selección o creación de sesión
SESSIONS_DIR = "data"
os.makedirs(SESSIONS_DIR, exist_ok=True)
sesion_actual = st.sidebar.text_input("Nombre de la sesión", value=datetime.now().strftime("%Y-%m-%d"))

ruta_sesion = os.path.join(SESSIONS_DIR, f"{sesion_actual}.json")
estado = cargar_sesion(ruta_sesion)

# ──────────────── PANELES PRINCIPALES ────────────────

# A. Registro de jugadores
st.header("👥 Jugadores")
with st.form("agregar_jugador"):
    nombre = st.text_input("Nombre del jugador")
    anfitrion = st.checkbox("¿Es anfitrión?")
    submit_jugador = st.form_submit_button("Agregar")
    if submit_jugador:
        agregar_jugador(estado, nombre.strip(), anfitrion)
        guardar_sesion(ruta_sesion, estado)

st.write("Jugadores registrados:")
st.table([{"Nombre": j["nombre"], "Anfitrión": j["anfitrion"]} for j in estado["jugadores"]])

# B. Registro de compras
st.header("💵 Declarar compra de fichas")
with st.form("declarar_compra"):
    jugador = st.selectbox("Jugador", [j["nombre"] for j in estado["jugadores"]])
    monto = st.number_input("Monto", min_value=1000, step=1000)
    metodo = st.selectbox("Método de pago", ["Efectivo", "Transferencia"])
    submit_compra = st.form_submit_button("Declarar compra")
    if submit_compra:
        registrar_compra(estado, jugador, monto, metodo)
        guardar_sesion(ruta_sesion, estado)

# C. Validar compras pendientes
st.header("✅ Validar compras")
compras_pendientes = [c for c in estado["compras"] if not c["validado"]]
for compra in compras_pendientes:
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        st.write(f'{compra["jugador"]} → {compra["monto"]} CLP vía {compra["metodo"]}')
    with col2:
        validador = st.selectbox(f"Validador para {compra['id']}", [j["nombre"] for j in estado["jugadores"] if j["nombre"] != compra["jugador"]], key=compra["id"])
    with col3:
        if st.button("Validar", key="validar_" + compra["id"]):
            validar_compra(estado, compra["id"], validador)
            guardar_sesion(ruta_sesion, estado)
            st.success("Compra validada")

# D. Estado actual
st.header("📊 Estado de la partida")
st.table(calcular_balance(estado))


# 📈 Resultado final por jugador (post retiro)
st.header("📈 Resultados de retiro")
resultado_final = calcular_resultado_final(estado)
st.table([
    {
        "Jugador": j["Jugador"],
        "Fichas compradas": j["total"],
        "Fichas salida": j["fichas_salida"],
        "Preferencia": j["preferencia"],
        "Resultado neto": j["resultado"],
        "Liquidación": j["deuda"]
    }
    for j in resultado_final
])


st.header("🏁 Retiro de jugadores")
with st.form("retiro_jugador"):
    jugador_retiro = st.selectbox("Jugador que se retira", [j["nombre"] for j in estado["jugadores"]])
    fichas_salida = st.number_input("Cantidad de fichas con las que se retira", min_value=0, step=1000)
    preferencia = st.selectbox("¿Cómo prefiere recibir?", ["Efectivo", "Transferencia"])
    submit_retiro = st.form_submit_button("Registrar retiro")
    if submit_retiro:

        registrar_retiro(estado, jugador_retiro, fichas_salida, preferencia)
        guardar_sesion(ruta_sesion, estado)
        st.success(f"{jugador_retiro} retirado con {fichas_salida} fichas.")

# E. Cierre de sesión
# E. Cierre de sesión
st.header("🔒 Cierre de sesión")

if not estado["cerrado"]:
    jugadores_sin_retiro = [
        j["nombre"]
        for j in estado["jugadores"]
        if j["nombre"] not in [r["jugador"] for r in estado.get("retiros", [])]
    ]

    if jugadores_sin_retiro:
        st.error(f"❌ No puedes cerrar la sesión. Faltan retiros de: {', '.join(jugadores_sin_retiro)}")
    else:
        if "confirmar_cierre" not in st.session_state:
            st.session_state["confirmar_cierre"] = False

        if not st.session_state["confirmar_cierre"]:
            if st.button("Cerrar sesión definitivamente"):
                st.session_state["confirmar_cierre"] = True
                st.warning("¿Estás seguro que deseas cerrar la sesión? Haz clic nuevamente para confirmar.")
        else:
            if st.button("Confirmar cierre"):
                cerrar_sesion(estado)
                guardar_sesion(ruta_sesion, estado)
                resumen_final = generar_cuadratura_final(estado)
                st.success("✅ Sesión cerrada. Se calcularon los pagos correspondientes.")
                st.code(resumen_final, language="text")
                st.download_button("📄 Descargar resumen final",
                                   data=resumen_final,
                                   file_name=f"resumen_{sesion_actual}.txt")

else:
    st.warning("La sesión está cerrada.")
    st.download_button("📄 Descargar resumen final",
                       data=generar_cuadratura_final(estado),
                       file_name=f"resumen_{sesion_actual}.txt")


