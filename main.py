import streamlit as st
from datetime import datetime
import uuid
import os
import json
import hashlib

from utils.storage import guardar_sesion, cargar_sesion
from utils.logic import (
    agregar_jugador, registrar_compra, validar_compra,
    calcular_balance, cerrar_sesion, generar_cuadratura_final,
    registrar_retiro, calcular_resultado_final, eliminar_jugador
)

# Configuración inicial
st.set_page_config(page_title="Caja Póker", layout="wide")
st.title("🃏 Gestión de Caja - Partida de Póker")

# 🔐 Inicio de sesión del jugador
if "user_id" not in st.session_state:
    st.sidebar.header("🎩 Ingreso del jugador")
    with st.sidebar.form("login_form"):
        nombre_usuario = st.text_input("Tu nombre")
        correo_usuario = st.text_input("Tu correo")
        submit_login = st.form_submit_button("Ingresar")
        if submit_login and nombre_usuario and correo_usuario:
            hash_input = (nombre_usuario.strip().lower() + correo_usuario.strip().lower()).encode()
            st.session_state["user_id"] = hashlib.sha256(hash_input).hexdigest()
            st.session_state["nombre_usuario"] = nombre_usuario
            st.session_state["correo_usuario"] = correo_usuario

            # Registrar automáticamente al jugador si no existe
            SESSIONS_DIR = "data"
            os.makedirs(SESSIONS_DIR, exist_ok=True)
            sesion_actual = datetime.now().strftime("%Y-%m-%d")
            ruta_sesion = os.path.join(SESSIONS_DIR, f"{sesion_actual}.json")
            estado = cargar_sesion(ruta_sesion)
            nombres_actuales = [j["nombre"] for j in estado["jugadores"]]
            if nombre_usuario not in nombres_actuales:
                agregar_jugador(estado, nombre_usuario, anfitrion=False)
                guardar_sesion(ruta_sesion, estado)
            st.rerun()

if "user_id" in st.session_state:
    st.sidebar.success(f"🎮 Jugador activo: {st.session_state['nombre_usuario']}")

    # Botón para nueva partida con contraseña
    with st.sidebar.expander("🌟 Nueva partida"):
        nueva_partida_password = st.text_input("Contraseña para reiniciar partida", type="password")
        if st.button("Reiniciar partida"):
            if nueva_partida_password == "poker":
                SESSIONS_DIR = "data"
                for archivo in os.listdir(SESSIONS_DIR):
                    os.remove(os.path.join(SESSIONS_DIR, archivo))
                st.session_state.clear()
                st.rerun()
            else:
                st.error("Contraseña incorrecta para nueva partida")

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
            st.rerun()

    for jugador in estado["jugadores"]:
        col1, col2, col3 = st.columns([4, 2, 1])
        col1.markdown(f"**{jugador['nombre']}**")
        col2.markdown("Anfitrión" if jugador["anfitrion"] else "")
        if col3.button("❌", key=f"eliminar_{jugador['nombre']}"):
            eliminar_jugador(estado, jugador["nombre"])
            guardar_sesion(ruta_sesion, estado)
            st.rerun()

    # B. Registro de compras
    st.header("💵 Declarar compra de fichas")
    with st.form("declarar_compra"):
        jugador = st.selectbox("Jugador", [j["nombre"] for j in estado["jugadores"]])
        monto = st.number_input("Monto", min_value=1000, step=1000)
        metodo = st.selectbox("Método de pago", ["Efectivo", "Transferencia"])
        submit_compra = st.form_submit_button("Declarar compra")
        if submit_compra:
            registrar_compra(estado, jugador, monto, metodo, st.session_state["user_id"])
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
                try:
                    validar_compra(estado, compra["id"], validador, st.session_state["user_id"])
                    guardar_sesion(ruta_sesion, estado)
                    st.success(f"Compra validada por {validador}")
                except ValueError as e:
                    st.warning(str(e))

    # Registro de validaciones realizadas
    st.subheader("🧾 Registro de validaciones")
    validaciones = [c for c in estado["compras"] if c["validado"]]
    if validaciones:
        st.table([
            {
                "Jugador": v["jugador"],
                "Monto": v["monto"],
                "Método": v["metodo"],
                "Validador": v["validador"]
            } for v in validaciones
        ])

    # D. Estado actual
    st.header("📊 Estado de la partida")
    st.table(calcular_balance(estado))

    # 📈 Resultado final por jugador (post retiro)
    st.header("📈 Resultados de retiro")
    resultado_final = calcular_resultado_final(estado)

    total_comprado = sum(r["total"] for r in resultado_final)
    total_retirado = sum(r["fichas_salida"] for r in resultado_final if isinstance(r["fichas_salida"], (int, float)))

    if total_retirado > total_comprado:
        st.error(f"❌ Inconsistencia: se han retirado {total_retirado:,} fichas pero solo se compraron {total_comprado:,}.")

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

    # E. Retiro de jugadores
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

    # F. Cierre de sesión
    st.header("🔒 Cierre de sesión")

    if not estado["cerrado"]:
        jugadores_sin_retiro_valido = [
            j["nombre"] for j in estado["jugadores"]
            if not any(r["jugador"] == j["nombre"] and r.get("fichas_salida", 0) > 0 for r in estado.get("retiros", []))
        ]

        if jugadores_sin_retiro_valido:
            st.error(f"❌ No puedes cerrar la sesión. Faltan fichas finales de: {', '.join(jugadores_sin_retiro_valido)}")
        else:
            if "confirmar_cierre" not in st.session_state:
                st.session_state["confirmar_cierre"] = False

            if not st.session_state["confirmar_cierre"]:
                if st.button("Cerrar sesión definitivamente"):
                    st.session_state["confirmar_cierre"] = True
                    st.warning("⚠️ ¿Estás seguro que deseas cerrar la sesión? Haz clic nuevamente para confirmar.")
            else:
                if st.button("Confirmar cierre"):
                    cerrar_sesion(estado)
                    guardar_sesion(ruta_sesion, estado)
                    resumen_final = generar_cuadratura_final(estado)
                    st.success("✅ Sesión cerrada. Se calcularon los pagos correspondientes.")
                    st.code(resumen_final, language="text")
                    st.download_button("📄 Descargar resumen final", data=resumen_final, file_name=f"resumen_{sesion_actual}.txt")
    else:
        st.warning("La sesión está cerrada.")
        st.download_button("📄 Descargar resumen final", data=generar_cuadratura_final(estado), file_name=f"resumen_{sesion_actual}.txt")
