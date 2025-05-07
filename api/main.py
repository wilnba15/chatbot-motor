
from fastapi import FastAPI, Request
from pydantic import BaseModel
import json

app = FastAPI()

# Cargar flujo desde JSON
with open("flujo_conversacional_motor.json", "r", encoding="utf-8") as f:
    flujo = json.load(f)

estado_usuario = {}

class Mensaje(BaseModel):
    usuario_id: str
    mensaje: str

# Función auxiliar para devolver mensaje de un nodo
def obtener_mensaje(nodo):
    if "mensaje" in nodo and "opciones" in nodo:
        texto_opciones = "\n".join([f"{op['opcion']}. {op['texto']}" for op in nodo["opciones"]])
        return f"{nodo['mensaje']}\n{texto_opciones}"
    return nodo.get("mensaje", "")

@app.post("/api/chat")
def responder_mensaje(msg: Mensaje):
    usuario_id = msg.usuario_id
    mensaje = msg.mensaje.strip().lower()

    if usuario_id not in estado_usuario:
        estado_usuario[usuario_id] = "inicio"

    estado_actual = estado_usuario[usuario_id]
    nodo = flujo.get(estado_actual)

    if not nodo:
        return {"respuesta": "❌ Algo salió mal. Intenta nuevamente."}

    siguientes = nodo.get("siguientes", {})
    opciones = nodo.get("opciones", [])

    # Manejo de opciones numéricas
    if opciones:
        for op in opciones:
            if mensaje == op["opcion"]:
                siguiente_estado = op["siguiente"]
                estado_usuario[usuario_id] = siguiente_estado
                return {"respuesta": obtener_mensaje(flujo[siguiente_estado])}
        return {"respuesta": "❌ Opción no válida. Por favor, selecciona una opción del menú."}

    # Manejo de respuestas libres
    if mensaje in siguientes:
        siguiente_estado = siguientes[mensaje]
        estado_usuario[usuario_id] = siguiente_estado
        return {"respuesta": obtener_mensaje(flujo[siguiente_estado])}

    # Si no se reconoce entrada
    return {"respuesta": "❌ Opción no válida. Por favor, intenta de nuevo o escribe 'menú'."}
