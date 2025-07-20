import uuid
from datetime import datetime
from io import StringIO

def agregar_jugador(estado, nombre, anfitrion=False):
    if any(j["nombre"] == nombre for j in estado["jugadores"]):
        return
    estado["jugadores"].append({
        "nombre": nombre,
        "anfitrion": anfitrion
    })

def registrar_compra(estado, jugador, monto, metodo, user_id):
    estado["compras"].append({
        "id": str(uuid.uuid4()),
        "jugador": jugador,
        "monto": monto,
        "metodo": metodo,
        "user_id": user_id,
        "validado": False,
        "validador": None,
        "timestamp": datetime.now().isoformat()
    })

def validar_compra(estado, id_compra, validador, validador_id):
    for compra in estado["compras"]:
        if compra["id"] == id_compra and not compra["validado"]:
            if compra.get("user_id") == validador_id:
                raise ValueError("No puedes validar tu propia compra.")
            compra["validado"] = True
            compra["validador"] = validador
            compra["validador_id"] = validador_id
            compra["validado_ts"] = datetime.now().isoformat()
            break

def calcular_balance(estado):
    resumen = {}
    for jugador in estado["jugadores"]:
        nombre = jugador["nombre"]
        resumen[nombre] = {"efectivo": 0, "transferencia": 0, "total": 0}

    for compra in estado["compras"]:
        if compra["validado"]:
            resumen[compra["jugador"]][compra["metodo"].lower()] += compra["monto"]

    for valores in resumen.values():
        valores["total"] = valores["efectivo"] + valores["transferencia"]

    resumen_final = [{"Jugador": k, **v} for k, v in resumen.items()]
    return resumen_final

def cerrar_sesion(estado):
    estado["cerrado"] = True
    estado["cerrado_ts"] = datetime.now().isoformat()
    
def generar_cuadratura_final(estado):
    resumen = []
    resumen.append("🃏 RESUMEN FINAL DE LA PARTIDA\n")
    resumen.append(f"Fecha de cierre: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    resumen.append("Jugadores:\n")

    resumen.append("Nombre        | Comprado | Salida | Resultado | Liquidación")
    resumen.append("--------------|----------|--------|-----------|------------------------------")

    resultados = calcular_resultado_final(estado)

    for j in resultados:
        resumen.append(f"{j['Jugador']:<14} ${j['total']:>7,}   {str(j['fichas_salida']):>6}   {str(j['resultado']):>9}   {j['deuda']}")

    resumen.append("\nGracias por jugar. ¡Nos vemos en la próxima! 🤑")

    return "\n".join(resumen)

def registrar_retiro(estado, jugador, fichas_salida, preferencia):
    if "retiros" not in estado:
        estado["retiros"] = []
    estado["retiros"].append({
        "jugador": jugador,
        "fichas_salida": fichas_salida,
        "preferencia": preferencia,
        "timestamp": datetime.now().isoformat()
    })

def calcular_resultado_final(estado):
    balance = calcular_balance(estado)
    salidas = {r["jugador"]: r for r in estado.get("retiros", [])}

    for jugador in balance:
        nombre = jugador["Jugador"]
        retiro = salidas.get(nombre)

        if retiro:
            fichas_salida = retiro.get("fichas_salida", 0)
            preferencia = retiro.get("preferencia", "No informado")
            fichas_compradas = jugador["total"]
            resultado = fichas_salida - fichas_compradas

            jugador["fichas_salida"] = fichas_salida
            jugador["preferencia"] = preferencia
            jugador["resultado"] = resultado

            if resultado > 0:
                jugador["deuda"] = f"Debe recibir ${resultado:,} vía {preferencia}"
            elif resultado < 0:
                jugador["deuda"] = f"Debe devolver ${-resultado:,}"
            else:
                jugador["deuda"] = "Saldo exacto"
        else:
            jugador["fichas_salida"] = "N/A"
            jugador["preferencia"] = "N/A"
            jugador["resultado"] = "N/A"
            jugador["deuda"] = "No se ha retirado"

    return balance

def eliminar_jugador(estado, nombre_jugador):
    # Elimina al jugador de la lista
    estado["jugadores"] = [j for j in estado["jugadores"] if j["nombre"] != nombre_jugador]
    # Elimina cualquier compra asociada
    estado["compras"] = [c for c in estado["compras"] if c["jugador"] != nombre_jugador]
    # Elimina cualquier retiro asociado
    estado["retiros"] = [r for r in estado.get("retiros", []) if r["jugador"] != nombre_jugador]

