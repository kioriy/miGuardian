# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2024-03-12 19:29:22
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2024-06-02 22:38:25
from util.notification import TelegramNotifier
from util.load_handler_logging import load_handler_logging
from util.datasync import DataSync
from util.datajson import DataJson
from datetime import datetime
from enums import ESettings

import database.miguardiandb as db
import pandas as pd
import logging
import schedule
import time

load_handler_logging()

def notification_no_check_in():
    logging.info("Iniciando la tarea diaria para verificar la asistencia de los alumnos...")
    # Inicializa la base de datos
    db.setup_database()
    #inicializamos el archivo de configuracion
    settings = DataJson("settings", dict())
    #obtenemos la fecha actual
    fecha_hoy = datetime.today().strftime('%Y-%m-%d')
    #Inicializamos la lista de mensajes
    list_alumnos_nombres = []
    #Obtiene la lista de alumnos que no han marcado asistencia hoy
    df = pd.dataframe(db.get_noCheckIn_student())
    #Obteenemos el tamaño del dataframe
    tamaño_df = len(df)
    #Inicializamos la variable de mensaje del alumno
    alumnos_nombres = ""
    #Inicializamos el contador para cada ronda de mensajes si la catindad de alumnos es mayor a 30
    ronda_mensajes = 1

    if tamaño_df > 1:
        #recorre todo el data frame
        for index, alumno in df.iterrows():
            #generamos el mensaje de cada alumno tomando los datos de cada iteracion del data frame
            alumnos_nombres += f"{index + 1}. {alumno['nombre']} {alumno['apellidos']}-{alumno['grado']}º{alumno['grupo']}\n"
            #El index se va a dividir entre treinta cuando el residuo sean un valor 0 va a guardar otra ronda de mensajes
            ronda_mensajes = (index + 1) % 30
            #Concatena el encabezado de mensaje e idexa un nuevo bloque de 30 mensajes            
            if ronda_mensajes == 0 or (index + 1) == tamaño_df:
                mensaje = f"Alumnos que no registraron entrada el {fecha_hoy}: \n" + "".join(alumnos_nombres)
                list_alumnos_nombres.append(mensaje)
    else:
        mensaje = f"Todos los alumnos han registrado entrada el {fecha_hoy}.\n"
        list_alumnos_nombres.append(mensaje)
    
    for mensaje in list_alumnos_nombres:
        # Envía el mensaje a través de Telegram
        notifier = TelegramNotifier()
        chat_id = settings.data.setdefault(ESettings.chat_id_admin.name, 0)
        notifier.send_message(chat_id, mensaje )
        time.sleep(1)  #Pequeña pausa para evitar sobrecargar al servidor de Telegram
    
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
        #ahora = datetime.now()
        #logging.info(f"I work ... {ahora.strftime('%I:%M:%S %p')}") #print(f"I work ... {ahora.strftime('%I:%M:%S %p')}")

if __name__ == "__main__":
    main()