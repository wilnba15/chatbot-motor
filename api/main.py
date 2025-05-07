
from fastapi import FastAPI, Request
from pydantic import BaseModel
import json

app = FastAPI()

# Cargar el flujo desde el JSON
with open("flujo_conversacional_motor.json", "r", encoding="utf-8") as f:
    flujo = json.load(f)

# Simulación de estado conversacional (en producción usar base de datos o redis)
estado_usuario = {}

class Mensaje(BaseModel):
    usuario_id: str
    mensaje: str

@app.post("/api/chat")
def responder_mensaje(msg: Mensaje):
    usuario_id = msg.usuario_id
    mensaje = msg.mensaje.strip().lower()

    # Estado inicial
    if usuario_id not in estado_usuario:
        estado_usuario[usuario_id] = "inicio"

    estado_actual = estado_usuario[usuario_id]
    nodo = flujo.get(estado_actual)

    if not nodo:
        return {"respuesta": "Lo siento, algo salió mal."}

    siguientes = nodo.get("siguientes", {})
    opciones = nodo.get("opciones", [])

    # Si hay opciones, verificar por número
    if opciones:
        for op in opciones:
            if mensaje == op["opcion"]:
                siguiente_estado = op["siguiente"]
                estado_usuario[usuario_id] = siguiente_estado
                return {"respuesta": flujo[siguiente_estado]["mensaje"]}

    # Si es texto libre (ej. "listo" o "menú")
    if mensaje in siguientes:
        siguiente_estado = siguientes[mensaje]
        estado_usuario[usuario_id] = siguiente_estado
        return {"respuesta": flujo[siguiente_estado]["mensaje"]}

    # Si no coincide, repetir nodo actual
    return {"respuesta": nodo["mensaje"]}
