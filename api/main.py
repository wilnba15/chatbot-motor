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
else:
    client = gspread.service_account(filename="credenciales.json")

sheet = client.open("Asesorias Chatbot").worksheet("Hoja 1")

# === Inicializar FastAPI ===
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Flujo conversacional ===
flujos = {
    "inicio": {
        "respuesta": "Hola, soy tu asistente virtual, ¿en qué te puedo ayudar hoy?\n1. Conocer nuestros servicios\n2. Agendar una asesoría gratuita\n3. Ver promociones y precios\n4. Descargar contenidos útiles\n5. Hablar con un asesor humano"
    },
    "registro_nombre": {"pregunta": "¿Cuál es tu nombre completo?"},
    "registro_telefono": {"pregunta": "¿Cuál es tu número de teléfono?"},
    "registro_correo": {"pregunta": "¿Cuál es tu correo electrónico?"},
    "registro_especialidad": {"pregunta": "¿Cuál es tu especialidad o giro?"},
    "registro_fecha": {"pregunta": "¿Qué fecha y hora prefieres para la asesoría?"}
}

estado_usuario = {}
datos_usuario = {}

class Mensaje(BaseModel):
    uid: str
    texto: str

@app.post("/api/chat")
async def responder_mensaje(mensaje: Mensaje):
    uid = mensaje.uid
    texto = mensaje.texto.strip().lower()

    if texto in ["hola", "menú", "menu"] or uid not in estado_usuario:
        estado_usuario[uid] = "inicio"
        return {"respuesta": flujos["inicio"]["respuesta"]}

    estado_actual = estado_usuario.get(uid, "inicio")

    if estado_actual == "inicio":
        if texto == "2":
            estado_usuario[uid] = "registro_nombre"
            datos_usuario[uid] = {}
            return {"respuesta": flujos["registro_nombre"]["pregunta"]}
        else:
            return {"respuesta": flujos["inicio"]["respuesta"]}

    elif estado_actual == "registro_nombre":
        datos_usuario[uid]["nombre"] = texto
        estado_usuario[uid] = "registro_telefono"
        return {"respuesta": flujos["registro_telefono"]["pregunta"]}

    elif estado_actual == "registro_telefono":
        datos_usuario[uid]["telefono"] = texto
        estado_usuario[uid] = "registro_correo"
        return {"respuesta": flujos["registro_correo"]["pregunta"]}

    elif estado_actual == "registro_correo":
        datos_usuario[uid]["correo"] = texto
        estado_usuario[uid] = "registro_especialidad"
        return {"respuesta": flujos["registro_especialidad"]["pregunta"]}

    elif estado_actual == "registro_especialidad":
        datos_usuario[uid]["especialidad"] = texto
        estado_usuario[uid] = "registro_fecha"
        return {"respuesta": flujos["registro_fecha"]["pregunta"]}

    elif estado_actual == "registro_fecha":
        datos_usuario[uid]["fecha"] = texto
        data = datos_usuario.pop(uid, {})

        sheet.append_row([
            data.get("nombre", ""),
            data.get("telefono", ""),
            data.get("correo", ""),
            data.get("especialidad", ""),
            data.get("fecha", "")
        ])

        estado_usuario[uid] = "inicio"
        mensaje_menu = flujos["inicio"]["respuesta"]
        return {"respuesta": "✅ ¡Gracias! Hemos registrado tu asesoría. Si deseas salir, escribe 'menú' o 'salir'.\n\n" + mensaje_menu}

    return {"respuesta": "Disculpa, no entendí tu mensaje. Por favor escribe 'menú' para ver las opciones."}

@app.get("/", response_class=HTMLResponse)
def home():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())