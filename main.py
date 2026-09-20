import time
from datetime import date
from agent import enviar_mensaje, obtener_estadisticas, extraer_datos_sesion
import db_manager 

def iniciar_app():
    print("💪 ¡Bienvenido a tu Terminal Fitness Coach!")
    print("""
    Comandos: 
        1. 'salir' para cerrar 
        2. '/registrar [texto]' para guardar una sesión : [ejercicio, sets, reps, peso, notas]
        \n
    """)
    
    # db_manager.descargar_bd_de_drive(servicio)
    tiempo_inicio = time.time()
    
    while True:
        usuario_input = input("Tú: ")

        # Comandos 
        ## 1. Condición de salida
        if usuario_input.lower() in ['salir', 'exit', 'quit']:
            # Calcular duración exacta
            tiempo_fin = time.time()
            duracion_segundos = tiempo_fin - tiempo_inicio
            minutos, segundos = divmod(int(duracion_segundos), 60)
            
            # Traer datos del modelo
            stats = obtener_estadisticas()
            
            # Imprimir el tablero de estado expandido
            print("\n" + "="*50)
            print("📊 REPORTE TÉCNICO DE LA SESIÓN")
            print("-" * 50)
            print("⚙️  CONFIGURACIÓN DEL AGENTE")
            print(f"    Modelo principal      : {stats['modelo_base']}")
            print(f"    Personalidad (System) : {stats['instrucciones_sistema']}")
            print(f"    MIME Type Chat        : {stats['mime_type_chat']}")
            print(f"    MIME Type Registro    : {stats['mime_type_extractor']}")
            print("-" * 50)
            print("📈 MÉTRICAS DE USO")
            print(f"    Tiempo activo         : {minutos}m {segundos}s")
            print(f"    Mensajes Totales      : {stats['total_mensajes']}")
            print(f"    Tus mensajes (User)   : {stats['interacciones_usuario']}")
            print(f"    Respuestas (Model)    : {stats['respuestas_coach']}")
            print(f"    Costo de Contexto     : {stats['tokens_memoria']} tokens en memoria")
            print("="*50)
            
            print("\nGuardando progreso y cerrando el gimnasio... ¡Hasta la próxima!")
            # db_manager.subir_bd_a_drive(servicio)
            break
            
        ## 2. Condición de registro de base de datos
        if usuario_input.lower().startswith("/registrar "):

            ### Extraer el texto después del comando y procesarlo
            texto_registro = usuario_input.replace("/registrar ", "")
            print("⏳ Analizando e insertando en la base de datos...")
            
            try:

                ### El LLM que extrae datos los extrae 
                datos = extraer_datos_sesion(texto_registro)

                ### Guarda el dia actual en formato YYYY-MM-DD
                hoy = date.today().strftime("%Y-%m-%d")
                
                # Por ahora usamos ejercicio_id=1 (El Deadlift de prueba que creaste antes)
                # En el futuro, buscaremos el ID real del ejercicio en la tabla Ejercicios
                db_manager.registrar_sesion(
                    ejercicio_id=1, 
                    fecha=hoy, 
                    sets_realizados=datos['sets'], 
                    reps_realizados=datos['reps'], 
                    peso_utilizado=datos['peso'], 
                    notas_sesion=datos['notas']
                )
                print(f"""
                - Guardado : {datos['sets']} sets de {datos['reps']} reps con {datos['peso']} en {datos['ejercicio']}.
                """)
            except Exception as e:
                print(f"❌ Error al guardar en SQLite: {e}")
            # continue # Vuelve al inicio del bucle sin enviar esto al chat normal

        ## 3. Chat normal (Tu código actual...)
        try:
            respuesta = enviar_mensaje(usuario_input)
            print(f"\n🤖 Coach: {respuesta}\n")
        
        except Exception as e:
            print(f"\n❌ Error de conexión: {e}\n")

if __name__ == '__main__':
    iniciar_app()