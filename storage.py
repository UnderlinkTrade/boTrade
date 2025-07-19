import json
import os

ESTRUCTURA_INICIAL = {
    "jugadores": [],
    "compras": [],
    "cerrado": False
}

def cargar_sesion(ruta):
    if not os.path.exists(ruta):
        return ESTRUCTURA_INICIAL.copy()
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)

def guardar_sesion(ruta, estado):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=2, ensure_ascii=False)
