import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
from datetime import date

# Cargar credenciales
load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Definir la personalidad y rol del modelo
instrucciones_sistema = (
    "Eres un coach de fitness experto, directo y motivador. "
    "Tu objetivo es ayudar al usuario a crear rutinas y mejorar su técnica en ejercicios en el GYM. "
    "Responde de forma concisa y conversacional."
)

# Inicializar el modelo con las instrucciones
modelo = genai.GenerativeModel(
    'gemini-3.6-flash',
    system_instruction=instrucciones_sistema
)

# Iniciar un chat que recordará el contexto de los mensajes anteriores
chat = modelo.start_chat(history=[])

def enviar_mensaje(mensaje: str) -> str:
    """Envía el mensaje del usuario al modelo y retorna la respuesta."""
    respuesta = chat.send_message(mensaje)
    return respuesta.text

def obtener_estadisticas():
    """Extrae métricas detalladas de uso, configuración y memoria de los modelos."""
    # Desglosar los mensajes del historial
    total_mensajes = len(chat.history)
    mensajes_usuario = sum(1 for msg in chat.history if msg.role == "user")
    mensajes_coach = sum(1 for msg in chat.history if msg.role == "model")
    
    # Contar los tokens acumulados en la memoria a corto plazo
    tokens_totales = modelo.count_tokens(chat.history).total_tokens if total_mensajes > 0 else 0
    
    # Extraer el MIME type del modelo JSON (si está configurado)
    mime_json = "Desconocido"
    if hasattr(modelo_json, '_generation_config') and 'response_mime_type' in modelo_json._generation_config:
        mime_json = modelo_json._generation_config['response_mime_type']

    return {
        "modelo_base": modelo.model_name,
        "instrucciones_sistema": "Activas" if modelo._system_instruction else "Inactivas",
        "total_mensajes": total_mensajes,
        "interacciones_usuario": mensajes_usuario,
        "respuestas_coach": mensajes_coach,
        "tokens_memoria": tokens_totales,
        "mime_type_chat": "text/plain (Texto Libre)",
        "mime_type_extractor": mime_json
    }
# Creamos un segundo modelo configurado EXCLUSIVAMENTE para devolver JSON
modelo_json = genai.GenerativeModel(
    'gemini-3.6-flash',
    generation_config={"response_mime_type": "application/json"}
)

def extraer_datos_sesion(texto_usuario):
    """Fuerza a Gemini a convertir lenguaje natural en un diccionario estructurado."""
    prompt = f"""
    Eres un extractor de datos. Analiza el mensaje del usuario y devuelve ÚNICAMENTE 
    un JSON con esta estructura exacta. Si falta un dato numérico, usa 0.
    {{"ejercicio": "nombre del ejercicio", "sets": numero, "reps": numero, "peso": numero, "notas": "observaciones"}}
    
    Mensaje del usuario: "{texto_usuario}"
    """
    respuesta = modelo_json.generate_content(prompt)
    
    # Convertimos el texto JSON que devuelve Gemini a un diccionario de Python
    return json.loads(respuesta.text)

if __name__ == "__main__":

    texto_usuario = input("Introduce tu registro de sesión (ejercicio, sets, reps, peso, notas): ")
    json_extract = extraer_datos_sesion(texto_usuario)
    print("Datos extraídos en formato JSON:", json_extract)