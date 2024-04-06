# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2024-03-12 19:29:22
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2024-03-14 20:29:35

from util.notification import TelegramNotifier
from util.datajson import DataJson
from datetime import datetime

import database.miguardiandb as db
import schedule
import time

def tarea_diaria():
    print("Iniciando la tarea diaria para verificar la asistencia de los alumnos...")
    
    # Inicializa la base de datos (asegúrate de que esto sea necesario y adecuado según tu configuración)
    db.setup_database()
    settings = DataJson("settings", dict())
    #list_no_check_in_student = DataJson("estudiantes_sin_entrada.json", [])
    
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
        chat_id = settings.add_and_get_dict_value_if_not_exist('chat_id_admin', 0)
        notifier.send_message(chat_id, mensaje )
        time.sleep(1)  # Pequeña pausa para evitar sobrecargar el servidor de Telegram

def main():
    # Programa la tarea para que se ejecute todos los días a la hora especificada.
    settings = DataJson("settings", dict())
    time_schedule = settings.add_and_get_dict_value_if_not_exist("schedule", ["08:20"])
    current_time = datetime.now().strftime("%H:%M")
    at_time = [valid_time for valid_time in time_schedule if datetime.strptime(current_time, "%H:%M").time() < datetime.strptime(valid_time, "%H:%M").time()]
    
    schedule.every().day.at(at_time).do(tarea_diaria)

    # Bucle infinito para ejecutar las tareas programadas
    while True:
        schedule.run_pending()
        time.sleep(10)  # Espera un minuto antes de comprobar las tareas pendientes de nuevo

if __name__ == "__main__":
    main()