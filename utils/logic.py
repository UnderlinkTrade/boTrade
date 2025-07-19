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

def registrar_compra(estado, jugador, monto, metodo):
    estado["compras"].append({
        "id": str(uuid.uuid4()),
        "jugador": jugador,
        "monto": monto,
        "metodo": metodo,
        "validado": False,
        "validador": None,
        "timestamp": datetime.now().isoformat()
    })

def validar_compra(estado, id_compra, validador):
    for compra in estado["compras"]:
        if compra["id"] == id_compra and not compra["validado"]:
            compra["validado"] = True
            compra["validador"] = validador
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
    buffer = StringIO()
    buffer.write("Resumen de caja - Partida de Póker\n")
    buffer.write(f"Fecha: {estado.get('cerrado_ts', 'N/A')}\n\n")

    balance = calcular_balance(estado)
    total_efectivo = sum(x["efectivo"] for x in balance)
    total_transferencia = sum(x["transferencia"] for x in balance)
    total = total_efectivo + total_transferencia

    buffer.write(f"Total en efectivo recaudado: ${total_efectivo:,} CLP\n")
    buffer.write(f"Total en fichas (valor jugado): ${total:,} CLP\n\n")

    buffer.write("Detalle por jugador:\n")
    for b in balance:
        buffer.write(f"{b['Jugador']}: Efectivo ${b['efectivo']:,}, "
                     f"Transferencia ${b['transferencia']:,}, Total ${b['total']:,}\n")

    buffer.write("\nCompras validadas:\n")
    for c in estado["compras"]:
        if c["validado"]:
            buffer.write(f"{c['jugador']} → ${c['monto']:,} vía {c['metodo']} "
                         f"(validado por {c['validador']})\n")

    buffer.write("\nGracias por jugar 🤝\n")
    return buffer.getvalue()

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
        fichas_salida = salidas.get(nombre, {}).get("fichas_salida")
        if fichas_salida is not None:
            jugador["fichas_salida"] = fichas_salida
            jugador["resultado"] = fichas_salida - jugador["total"]
        else:
            jugador["fichas_salida"] = "N/A"
            jugador["resultado"] = "N/A"
    return balance

