import sqlite3
from typing import Optional

# Funciones de gestión de la base de datos SQLite
def get_connection() -> sqlite3.Connection:
    """
    Establece y retorna la conexión a la base de datos local SQLite.
    Si el archivo 'fitness_app.db' no existe en el directorio actual, SQLite lo creará automáticamente.
    """
    return sqlite3.connect('fitness_app.db')

def init_db() -> None:
    """
    Inicializa el esquema de la base de datos.
    Crea las 4 tablas relacionales principales (Usuarios, Rutinas, Ejercicios, Sesiones)
    si es que aún no existen en el archivo 'fitness_app.db'.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Tabla Usuarios
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        objetivo TEXT,
        porcentaje_grasa REAL,
        notas TEXT
    )
    ''')

    # 2. Tabla Rutinas (Se vincula al usuario)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Rutinas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        dia_numero INTEGER,
        grupo_muscular TEXT,
        FOREIGN KEY (usuario_id) REFERENCES Usuarios(id)
    )
    ''')

    # 3. Tabla Ejercicios (Se vincula a una rutina)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Ejercicios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rutina_id INTEGER,
        nombre TEXT,
        sets_obj INTEGER,
        reps_obj INTEGER,
        peso_obj REAL,
        notas_ejercicio TEXT,
        FOREIGN KEY (rutina_id) REFERENCES Rutinas(id)
    )
    ''')

    # 4. Tabla Sesiones (El historial diario, se vincula a un ejercicio)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Sesiones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ejercicio_id INTEGER,
        fecha DATE,
        sets_realizados INTEGER,
        reps_realizados INTEGER,
        peso_utilizado REAL,
        notas_sesion TEXT,
        FOREIGN KEY (ejercicio_id) REFERENCES Ejercicios(id)
    )
    ''')

    conn.commit()
    conn.close()
    print("Base de datos y tablas inicializadas correctamente.")

def insertar_usuario(objetivo: str, porcentaje_grasa: float, notas: str) -> int:
    """
    Inserta un nuevo usuario en la base de datos.
    
    Se utiliza: Típicamente solo una vez al configurar la aplicación por primera vez, 
    o cuando se desea registrar a una nueva persona.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO Usuarios (objetivo, porcentaje_grasa, notas)
        VALUES (?, ?, ?)
    ''', (objetivo, porcentaje_grasa, notas))
    
    usuario_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return usuario_id

def insertar_rutina(usuario_id: int, dia_numero: int, grupo_muscular: str) -> int:
    """
    Crea el contenedor de una rutina diaria para un usuario específico.
    
    Se utiliza: Cuando el agente (LLM) genera un plan nuevo. Por ejemplo, si el agente crea
    un plan de 3 días, llamará a esta función 3 veces (para los días 1, 2 y 3).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO Rutinas (usuario_id, dia_numero, grupo_muscular)
        VALUES (?, ?, ?)
    ''', (usuario_id, dia_numero, grupo_muscular))
    
    rutina_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return rutina_id

def insertar_ejercicio(rutina_id: int, nombre: str, sets_obj: int, reps_obj: int, peso_obj: float, notas_ejercicio: str = "") -> int:
    """
    Añade un ejercicio específico al plan de una rutina.
    
    Se utiliza: Inmediatamente después de usar 'insertar_rutina()'. El LLM iterará sobre 
    los ejercicios que generó para ese día y llamará a esta función por cada uno, asociándolos
    al 'rutina_id' correspondiente.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO Ejercicios (rutina_id, nombre, sets_obj, reps_obj, peso_obj, notas_ejercicio)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (rutina_id, nombre, sets_obj, reps_obj, peso_obj, notas_ejercicio))
    
    ejercicio_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return ejercicio_id

def registrar_sesion(ejercicio_id: int, fecha: str, sets_realizados: int, reps_realizados: int, peso_utilizado: float, notas_sesion: str = "") -> None:
    """
    Registra la ejecución real de un ejercicio en una fecha específica (El historial de entrenamiento).
    
    Se utiliza: Cada vez que termines un ejercicio en el gimnasio. Le dirás al agente:
    "Acabo de hacer 3 sets de 10 con 135lbs en Pendlay Rows". El agente buscará el ID de ese 
    ejercicio y usará esta función para guardar tu progreso real.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO Sesiones (ejercicio_id, fecha, sets_realizados, reps_realizados, peso_utilizado, notas_sesion)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (ejercicio_id, fecha, sets_realizados, reps_realizados, peso_utilizado, notas_sesion))
    
    conn.commit()
    conn.close()


# Funciones de integración con Google Drive para respaldar la base de datos

import sqlite3
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# Permiso para leer/escribir archivos creados por la app en Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def autenticar_drive():
    """Maneja el flujo OAuth2 de Google Drive y retorna el servicio."""
    creds = None
    # El archivo token.json almacena los tokens de acceso y actualización
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Si no hay credenciales válidas disponibles, pide al usuario iniciar sesión
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Guarda las credenciales para la próxima ejecución
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    # Construye y retorna el servicio de la API de Drive
    return build('drive', 'v3', credentials=creds)

## Funciones de Subida y Descarga de la base de datos a Google Drive
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# Especifica la carpeta de Google Drive donde se almacenará la base de datos
CARPETA_ID = '1mxj-F74p7VfdWkV62jKPTvs3en9XVx7Z'
# DEBUG
print(f"DEBUG: Carpeta de Drive configurada con ID: {CARPETA_ID}")

def subir_bd_a_drive(servicio_drive):
    nombre_archivo = 'fitness_app.db'
    print("Sincronizando base de datos con Google Drive...")
    
    # Busca si el archivo ya existe en la carpeta de Drive
    respuesta = servicio_drive.files().list(
        q=f"name='{nombre_archivo}' and '{CARPETA_ID}' in parents",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    archivos = respuesta.get('files', [])

    # Preparamos el archivo local para subirlo (mimetype genérico de base de datos)
    media = MediaFileUpload(nombre_archivo, mimetype='application/x-sqlite3', resumable=True)

    if archivos:
        # El archivo existe, lo ACTUALIZAMOS
        archivo_id = archivos[0].get('id')
        servicio_drive.files().update(
            fileId=archivo_id,
            media_body=media
        ).execute()
        print(f"✅ Base de datos actualizada en Drive exitosamente.")
    else:
        # El archivo NO existe, lo CREAMOS por primera vez dentro de la carpeta especificada
        metadatos = {
            'name': nombre_archivo,
            'parents': [CARPETA_ID]
        }
        servicio_drive.files().create(
            body=metadatos,
            media_body=media,
            fields='id'
        ).execute()
        print(f"✅ Base de datos subida a la carpeta de Drive por primera vez.")

def descargar_bd_de_drive(servicio_drive):
    nombre_archivo = 'fitness_app.db'
    print("Comprobando base de datos en Google Drive...")
    
    # 1. Buscar el archivo en Drive solo dentro de la carpeta especificada
    respuesta = servicio_drive.files().list(
        q=f"name='{nombre_archivo}' and '{CARPETA_ID}' in parents",
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    archivos = respuesta.get('files', [])
    
    if not archivos:
        print("ℹ️ No se encontró la base de datos en Drive. Se trabajará localmente.")
        return False

    # 2. Si existe, procedemos a descargarlo
    archivo_id = archivos[0].get('id')
    solicitud = servicio_drive.files().get_media(fileId=archivo_id)
    
    with open(nombre_archivo, 'wb') as f:
        descargador = MediaIoBaseDownload(f, solicitud)
        completado = False
        while not completado:
            estado, completado = descargador.next_chunk()
            
    print("✅ Base de datos descargada exitosamente desde Drive.")
    return True


if __name__ == '__main__':

    # ======================================================================================================
    # Prueba de integración con Google Drive Descarga de la base de datos
    # ======================================================================================================

    # 1. Autenticar Google Drive y obtener el servicio
    servicio = autenticar_drive()

    # 2. Descargar la base de datos desde Drive (si existe)
    descargar_bd_de_drive(servicio)


    # ======================================================================================================
    # Añadir un registro de prueba a la base de datos local para verificar que todo funciona correctamente
    # ======================================================================================================
    init_db()
    
    # Prueba de inserción
    objetivo = input("Ingrese su objetivo (pérdida de grasa, ganancia muscular, mantenimiento): ")
    porcentaje_grasa = float(input("Ingrese su porcentaje de grasa corporal actual (ej. 20.5): "))
    notas = input("Ingrese cualquier nota adicional sobre su estado físico o preferencias: ")


    mi_id = insertar_usuario(objetivo=objetivo, porcentaje_grasa=porcentaje_grasa, notas=notas)
    rutina_dia_1_id = insertar_rutina(usuario_id=mi_id, dia_numero=1, grupo_muscular="Espalda y Pierna")
    
    ejercicio_1_id = insertar_ejercicio(
        rutina_id=rutina_dia_1_id, 
        nombre="Stiff Legged Deadlifts", 
        sets_obj=3, reps_obj=10, peso_obj=135.0, 
        notas_ejercicio="Mantener la espalda recta"
    )
    
    registrar_sesion(
        ejercicio_id=ejercicio_1_id, 
        fecha="2026-09-16", 
        sets_realizados=3, reps_realizados=8, peso_utilizado=135.0, 
        notas_sesion="Me costó trabajo el último set"
    )
    print("Datos insertados correctamente.")

    # ======================================================================================================
    # Prueba de integración con Google Drive Subida de la base de datos
    # ======================================================================================================

    # 1. Subir nuestro archivo recién creado/modificado a la nube
    subir_bd_a_drive(servicio)

