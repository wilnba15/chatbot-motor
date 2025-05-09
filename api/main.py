import os
import json
import gspread
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.oauth2 import service_account
from fastapi.responses import HTMLResponse

# === Autenticación con Google Sheets ===
credenciales_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if credenciales_json:
    info = json.loads(credenciales_json)
    creds = service_account.Credentials.from_service_account_info(info)
    client = gspread.authorize(creds)
    sheet = client.open("Asesorias Chatbot").worksheet("Asesorias Chatbot")
else:
    sheet = None

# === Configurar FastAPI ===
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

# === Flujo de conversación ===
estado_usuario = {}
datos_usuario = {}
espera_confirmacion = {}

flujos = {
    "inicio": "Hola, soy tu asistente virtual, ¿en qué te puedo ayudar hoy? 1. Conocer nuestros servicios 2. Agendar una asesoría gratuita",
    "servicios": "Ofrecemos asesoría especializada en tecnología, ventas y marketing.",
    "agendar_nombre": "¿Cuál es tu nombre completo?",
    "agendar_telefono": "¿Cuál es tu número de teléfono?",
    "agendar_correo": "¿Cuál es tu correo electrónico?",
    "agendar_especialidad": "¿Cuál es tu especialidad o giro?",
    "agendar_fecha": "¿Qué fecha y hora prefieres para la asesoría?",
}

@app.post("/api/chat")
async def responder_mensaje(mensaje: Mensaje):
    uid = "usuario1"  # identificador estático para pruebas
    texto = mensaje.mensaje.lower()

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>API activa</h1>"


    if uid not in estado_usuario:
        estado_usuario[uid] = "inicio"

    estado = estado_usuario[uid]

    # FLUJO
    if texto in ["1", "uno"] and estado == "inicio":
        return {"respuesta": flujos["servicios"]}

    elif texto in ["2", "dos"] and estado == "inicio":
        estado_usuario[uid] = "agendar_nombre"
        datos_usuario[uid] = {}
        return {"respuesta": flujos["agendar_nombre"]}

    elif estado == "agendar_nombre":
        datos_usuario[uid]["nombre"] = mensaje.mensaje
        estado_usuario[uid] = "agendar_telefono"
        return {"respuesta": flujos["agendar_telefono"]}

    elif estado == "agendar_telefono":
        datos_usuario[uid]["telefono"] = mensaje.mensaje
        estado_usuario[uid] = "agendar_correo"
        return {"respuesta": flujos["agendar_correo"]}

    elif estado == "agendar_correo":
        datos_usuario[uid]["correo"] = mensaje.mensaje
        estado_usuario[uid] = "agendar_especialidad"
        return {"respuesta": flujos["agendar_especialidad"]}

    elif estado == "agendar_especialidad":
        datos_usuario[uid]["especialidad"] = mensaje.mensaje
        estado_usuario[uid] = "agendar_fecha"
        return {"respuesta": flujos["agendar_fecha"]}

    elif estado == "agendar_fecha":
        datos_usuario[uid]["fecha"] = mensaje.mensaje

        if sheet:
            valores = list(datos_usuario[uid].values())
            sheet.append_row(valores)

        estado_usuario[uid] = "inicio"
        mensaje_menu = flujos["inicio"]
        return {"respuesta": "✅ ¡Gracias! Hemos registrado tu asesoría. Si deseas salir, escribe 'menú' o 'salir'.\n\n" + mensaje_menu}

    elif texto in ["menu", "salir"]:
        estado_usuario[uid] = "inicio"
        return {"respuesta": flujos["inicio"]}

    else:
        return {"respuesta": "Por favor, elige una opción del menú o escribe 'menú' para empezar."}
