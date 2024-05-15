# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2024-03-12 19:29:22
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2024-05-04 23:39:24
from util.notification import TelegramNotifier
from util.load_handler_logging import load_handler_logging
from util.datasync import DataSync
from util.datajson import DataJson
from datetime import datetime
from enums import ESettings

import database.miguardiandb as db
import logging
import schedule
import time

load_handler_logging()

def notification_no_check_in():
    logging.info("Iniciando la tarea diaria para verificar la asistencia de los alumnos...")#print("Iniciando la tarea diaria para verificar la asistencia de los alumnos...")
    # Inicializa la base de datos (asegúrate de que esto sea necesario y adecuado según tu configuración)
    db.setup_database()
    settings = DataJson("settings", dict())
    # Obtiene la lista de alumnos que no han marcado asistencia hoy
    db.get_noCheckIn_student()
    # Utiliza DataJson para cargar los datos del archivo JSON
    list_no_check_in_student = DataJson("estudiantes_sin_entrada", [])  # No necesitas agregar .json aquí, DataJson lo manejará
    # Ahora 'data' contendrá la lista de estudiantes
    list_student = list_no_check_in_student.load_data()
    # Divide la lista de alumnos en sub-listas de 30 elementos cada una
    sublistas_alumnos = [list_student[i:i + 30] for i in range(0, len(list_student), 30)]
    # Construye la lista de nombres, apellidos, grados y grupos de los estudiantes
    # Asegúrate de que cada 'alumno' en 'list_student' es un diccionario con las claves correctas
    for indice_sulista, sublista in enumerate(sublistas_alumnos):
        start_index = (indice_sulista * len(sublista)) if len(sublista) == 30 else ((indice_sulista) * 30 + len(sublista))
        alumnos_nombres = [f"{indice + 1}. {alumno['nombre']} {alumno['apellidos']}-{alumno['grado']}º{alumno['grupo']}\n" 
                            for indice, alumno in enumerate(sublista, start=start_index)]
        # Prepara el mensaje
        fecha_hoy = datetime.today().strftime('%Y-%m-%d')
        if alumnos_nombres:
            mensaje = f"Alumnos que no registraron entrada el {fecha_hoy}: \n" + "".join(alumnos_nombres)
        else:
            mensaje = f"Todos los alumnos han registrado entrada el {fecha_hoy}.\n"
        # Envía el mensaje a través de Telegram
        notifier = TelegramNotifier()
        chat_id = settings.data.setdefault(ESettings.chat_id_admin.name, 0)
        notifier.send_message(chat_id, mensaje )
        time.sleep(1)  # Pequeña pausa para evitar sobrecargar el servidor de Telegram
    
    reschedule(ESettings.no_check_in.name, notification_no_check_in)

def update_check_in():
    """_summary_
    Actuliza la reporte de todas las entradas y salidas en el documento de google sheets
    """
    logging.info("Iniciando la actividad para la actualización de los datos en la nube...")
    #Cargamos el archivo de configuración para obtener el nombre de la escuela
    settings = DataJson("settings", dict())
    #Creamos la instancia para de DataSync y acceder a los metodos de sincronizacion
    ds = DataSync()
    #Obtenemos los datos de la base de datos
    entries_exits_record = db.get_all_entries_and_exits()# get_entries_and_exits_by_date(date)
    #Verificamos que la consulta a la base de datos nos devuelva registros
    if len(entries_exits_record) > 0:
        ds.update_entries(settings.data["school_name"], entries_exits_record)
    #Volvemos a programar la tarea en el siguiente esquema valido. 
    reschedule(ESettings.update_check_in.name, update_check_in) 

def sync_photos():
    pass

def backrest_database():
    pass

def send_log():
    pass

def update_database():
    pass

def reschedule(event_schedule: str, task_fuction):
    """
    _summary_
    General el siguiente esquema valido para programa la siguiente tarea
    """
    at_time = get_valid_schedule(event_schedule)
    logging.info(f"el siguiente esquema valido es {at_time}")#print(f"el siguiente esquema valido es -------> {at_time}")
    schedule.every().day.at(at_time).do(task_fuction)
    
def get_valid_schedule(event_schedule: str):
    """
    _summary_
    devuelve un horario valido vigente
    del archivo de configuracion del esquema de eventos no_check_in
    
    Returns:
        _type_: str at_time
    """
    settings = DataJson("settings", dict())
    #si se realiza una actualizacion y el parametro no existe en el archivo de configuracion
    #setdefault creara la llave e inicializara con un valor asiginado
    time_schedule = settings.data.setdefault(ESettings.schedule.name, {ESettings.no_check_in.name : ["08:20"]})
    #Obtenemos el esquema de la estructura schedule del diccionario de eventos
    time_schedule = time_schedule[0][event_schedule]
    #normalizamos el esquema y formato de horas para mantener mejor coerencia en la comparación de tipos %H:%M
    time_schedule = [datetime.strptime(time, "%H:%M").time() for time in time_schedule]
    #Obtenemos el tiempo actual
    current_time = datetime.now()
    #Normalizamos el formato para coerencia de comparaciones %H:%M
    current_time = current_time.replace(second=0, microsecond=0).time()
    #Obtendremos el horario actual vigente del esquema, comparando la lista de esquemas con current_time
    at_time = [valid_time for valid_time in time_schedule if current_time < valid_time]
    
    if not at_time: 
        at_time.append(time_schedule[0])
    
    return at_time[0].strftime("%H:%M")

def main():
    #Actualiza el siguiente horario valido segun el esquema configurado para cada evento
    reschedule(ESettings.no_check_in.name, notification_no_check_in)
    reschedule(ESettings.update_check_in.name, update_check_in)
    # Bucle infinito para ejecutar las tareas programadas
    while True:
        schedule.run_pending()
        time.sleep(10)  # Espera un minuto antes de comprobar las tareas pendientes de nuevo
        ahora = datetime.now()
        #logging.info(f"I work ... {ahora.strftime('%I:%M:%S %p')}") #print(f"I work ... {ahora.strftime('%I:%M:%S %p')}")

if __name__ == "__main__":
    main()