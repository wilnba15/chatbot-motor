import os
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pyairtable import Table

# === Configuración Airtable ===
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Tasks"

if AIRTABLE_TOKEN and BASE_ID:
    airtable = Table(AIRTABLE_TOKEN, BASE_ID, TABLE_NAME)
else:
    airtable = None

# === Configuración FastAPI ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Estructura del mensaje ===
class Mensaje(BaseModel):
    mensaje: str

estado_usuario = {}
datos_usuario = {}

flujos = {
    "inicio": "Hola, soy tu asistente virtual, ¿en qué te puedo ayudar hoy? 1. Conocer nuestros servicios 2. Agendar una asesoría gratuita",
    "servicios": "Ofrecemos asesoría especializada en tecnología, ventas y marketing.",
    "agendar_nombre": "¿Cuál es tu nombre completo?",
    "agendar_telefono": "¿Cuál es tu número de teléfono?",
    "agendar_correo": "¿Cuál es tu correo electrónico?",
    "agendar_especialidad": "¿Cuál es tu especialidad o giro?",
    "agendar_fecha": "¿Qué fecha y hora prefieres para la asesoría?",
}

@app.post("/chat")
async def responder_mensaje(mensaje: Mensaje):
    uid = "usuario1"
    texto = mensaje.mensaje.lower()

    if uid not in estado_usuario:
        estado_usuario[uid] = "inicio"

    estado = estado_usuario[uid]

    if texto in ["1", "uno"] and estado == "inicio":
        return {"respuesta": flujos["servicios"]}

    elif texto in ["2", "dos"] and estado == "inicio":
        estado_usuario[uid] = "agendar_nombre"
        datos_usuario[uid] = {}
        return {"respuesta": flujos["agendar_nombre"]}

    elif estado == "agendar_nombre":
        datos_usuario[uid]["Nombre"] = mensaje.mensaje
        estado_usuario[uid] = "agendar_telefono"
        return {"respuesta": flujos["agendar_telefono"]}

    elif estado == "agendar_telefono":
        datos_usuario[uid]["Telefono"] = mensaje.mensaje
        estado_usuario[uid] = "agendar_correo"
        return {"respuesta": flujos["agendar_correo"]}

    elif estado == "agendar_correo":
        datos_usuario[uid]["Email"] = mensaje.mensaje
        estado_usuario[uid] = "agendar_especialidad"
        return {"respuesta": flujos["agendar_especialidad"]}

    elif estado == "agendar_especialidad":
        datos_usuario[uid]["Especialidad"] = mensaje.mensaje
        estado_usuario[uid] = "agendar_fecha"
        return {"respuesta": flujos["agendar_fecha"]}

    elif estado == "agendar_fecha":
        datos_usuario[uid]["Fecha y Hora"] = mensaje.mensaje
        if airtable:
            try:
                airtable.create(datos_usuario[uid])
            except Exception as e:
                print(f"❌ Error guardando en Airtable: {e}")
        estado_usuario[uid] = "inicio"
        return {
            "respuesta": "✅ ¡Gracias! Hemos registrado tu asesoría. Si deseas salir, escribe 'menú' o 'salir'.\n\n" + flujos["inicio"]
        }

    elif texto in ["menu", "salir"]:
        estado_usuario[uid] = "inicio"
        return {"respuesta": flujos["inicio"]}

    else:
        return {"respuesta": "Por favor, elige una opción del menú o escribe 'menú' para empezar."}
