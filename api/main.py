from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from pyairtable import Api

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Mensaje(BaseModel):
    mensaje: str

# === Configuración Airtable ===
AIRTABLE_TOKEN = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME")
airtable_client = Api(AIRTABLE_TOKEN).base(AIRTABLE_BASE_ID)

# === Diccionario para manejar el estado ===
estado_usuario = {}

def reset_estado(usuario_id):
    estado_usuario[usuario_id] = {
        "paso": "inicio",
        "datos": {}
    }

@app.post("/api/chat")
async def responder(mensaje: Mensaje):
    user_id = "cliente_unico"  # puede ser una IP, ID o email si quieres multicliente
    texto = mensaje.mensaje.strip().lower()

    if user_id not in estado_usuario:
        reset_estado(user_id)

    paso_actual = estado_usuario[user_id]["paso"]
    datos = estado_usuario[user_id]["datos"]

    if texto in ["hola", "menu", "salir"]:
        reset_estado(user_id)
        return {"respuesta": "Hola, soy tu asistente virtual. ¿En qué te puedo ayudar hoy?\n1. Conocer nuestros servicios\n2. Agendar una asesoría gratuita"}

    if paso_actual == "inicio":
        if texto == "1":
            return {"respuesta": "Ofrecemos asesorías en marketing digital, diseño web e inteligencia artificial. \u00a1Cuéntame cómo puedo ayudarte!"}
        elif texto == "2":
            estado_usuario[user_id]["paso"] = "nombre"
            return {"respuesta": "¡Perfecto! Para agendar, por favor dime tu nombre completo."}
        else:
            return {"respuesta": "Por favor escribe '1' o '2' para continuar."}

    elif paso_actual == "nombre":
        datos["Nombre"] = mensaje.mensaje.strip()
        estado_usuario[user_id]["paso"] = "telefono"
        return {"respuesta": "¡Gracias! Ahora dime tu número de teléfono."}

    elif paso_actual == "telefono":
        datos["Telefono"] = mensaje.mensaje.strip()
        estado_usuario[user_id]["paso"] = "email"
        return {"respuesta": "Ahora necesito tu correo electrónico."}

    elif paso_actual == "email":
        datos["Email"] = mensaje.mensaje.strip()
        estado_usuario[user_id]["paso"] = "especialidad"
        return {"respuesta": "¿Cuál es tu especialidad o el tema para la asesoría?"}

    elif paso_actual == "especialidad":
        datos["Especialidad"] = mensaje.mensaje.strip()
        estado_usuario[user_id]["paso"] = "fecha"
        return {"respuesta": "¡Muy bien! Finalmente, dime la fecha y hora para agendar (ej. 15/05/2025 11:00)"}

    elif paso_actual == "fecha":
        datos["Fecha y Hora"] = mensaje.mensaje.strip()

        # Intentamos guardar en Airtable
        try:
            airtable_client.table(AIRTABLE_TABLE_NAME).create(datos)
            respuesta = "\u2705 ¡Gracias! Hemos registrado tu asesoría. Escribe 'menu' para volver o 'salir' para terminar."
        except Exception as e:
            respuesta = f"Hubo un error al registrar los datos: {str(e)}"

        reset_estado(user_id)
        return {"respuesta": respuesta}

    return {"respuesta": "No entendí tu mensaje. Escribe 'menu' para ver opciones."}
