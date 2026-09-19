import sqlite3
from typing import Optional

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


if __name__ == '__main__':
    # Bloque de prueba
    init_db()
    
    # Prueba de inserción
    mi_id = insertar_usuario(objetivo="Hipertrofia", porcentaje_grasa=15.0, notas="Evitar lesiones de rodilla")
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
    print("Prueba completada: Datos insertados correctamente.")