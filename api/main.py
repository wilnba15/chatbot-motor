
from fastapi import FastAPI
from pydantic import BaseModel
import json
import csv
from datetime import datetime

app = FastAPI()

with open("flujo_conversacional_motor.json", "r", encoding="utf-8") as f:
    flujo = json.load(f)

estado_usuario = {}
datos_usuario = {}

formulario_campos = [
    ("form_nombre", "¿Cuál es tu nombre completo?"),
    ("form_telefono", "¿Cuál es tu número de teléfono?"),
    ("form_correo", "¿Cuál es tu correo electrónico?"),
    ("form_especialidad", "¿Cuál es tu especialidad o giro?"),
    ("form_fecha", "¿Qué fecha y hora prefieres para la asesoría?")
]

class Mensaje(BaseModel):
    usuario_id: str
    mensaje: str

def obtener_mensaje(nodo):
    return nodo.get("mensaje", "")

def guardar_csv(datos):
    with open("asesorias.csv", "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            datos.get("nombre", ""),
            datos.get("telefono", ""),
            datos.get("correo", ""),
            datos.get("especialidad", ""),
            datos.get("fecha", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ])

@app.post("/api/chat")
def responder_mensaje(msg: Mensaje):
    uid = msg.usuario_id
    texto = msg.mensaje.strip()

    # Palabras para reiniciar
    if texto.lower() in ["hola", "menú", "menu", "inicio", "empezar"]:
        estado_usuario[uid] = "inicio"
        return {"respuesta": obtener_mensaje(flujo["inicio"])}

    # Flujo normal si no está llenando formulario
    if uid not in estado_usuario:
        estado_usuario[uid] = "inicio"

    estado_actual = estado_usuario[uid]

    if estado_actual.startswith("form_"):
        # Guardar respuesta y pasar al siguiente campo
        idx = next((i for i, (k, _) in enumerate(formulario_campos) if k == estado_actual), None)
        if idx is not None:
            campo_key = formulario_campos[idx][0].replace("form_", "")
            datos_usuario.setdefault(uid, {})[campo_key] = texto

            if idx + 1 < len(formulario_campos):
                siguiente_estado, pregunta = formulario_campos[idx + 1]
                estado_usuario[uid] = siguiente_estado
                return {"respuesta": pregunta}
            else:
                # Guardar y finalizar
                guardar_csv(datos_usuario[uid])
                estado_usuario[uid] = "inicio"
                datos_usuario.pop(uid, None)
                return {"respuesta": "✅ ¡Gracias! Hemos registrado tu asesoría. Un asesor te contactará pronto. ¿Deseas hacer algo más?\nEscribe 'menú' para volver al inicio."}

    nodo = flujo.get(estado_actual)
    if not nodo:
        return {"respuesta": "❌ Algo salió mal. Intenta nuevamente."}

    siguientes = nodo.get("siguientes", {})
    opciones = nodo.get("opciones", [])

    if opciones:
        for op in opciones:
            if texto == op["opcion"]:
                siguiente_estado = op["siguiente"]
                estado_usuario[uid] = siguiente_estado
                if siguiente_estado == "agenda":
                    estado_usuario[uid] = formulario_campos[0][0]
                    return {"respuesta": formulario_campos[0][1]}
                return {"respuesta": obtener_mensaje(flujo[siguiente_estado])}
        return {"respuesta": "❌ Opción no válida. Por favor, selecciona una opción del menú."}

    if texto.lower() in siguientes:
        siguiente_estado = siguientes[texto.lower()]
        estado_usuario[uid] = siguiente_estado
        if siguiente_estado == "agenda":
            estado_usuario[uid] = formulario_campos[0][0]
            return {"respuesta": formulario_campos[0][1]}
        return {"respuesta": obtener_mensaje(flujo[siguiente_estado])}

    return {"respuesta": "❌ Opción no válida. Por favor, intenta de nuevo o escribe 'menú'."}
