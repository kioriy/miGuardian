# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-22 22:31:42
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2024-10-17 00:20:53

import gspread
from gspread_dataframe import get_as_dataframe
import gspread_dataframe as gd
from util.datajson import DataJson 
import database.miguardiandb as db  # Asumiendo que miguardiandb tiene las funciones necesarias para interacción con la BD.
import pandas as pd
from datetime import datetime, time, date, timedelta
from enums import ESettings as property

class DataSync:

    #__service_account = gspread.service_account()
    #__sheet = __service_account.open("8020digital")
    
    def __init__(self):
        self.__service_account = gspread.service_account()
        self.__sheet = self.__service_account.open("8020digital")
        self.config_manager = DataJson("settings", dict())
        work_sheet_name = self.config_manager.data[property.school_name.name]
        self.__work_sheet_name = work_sheet_name
        self.__work_sheet = self.__sheet.worksheet(self.__work_sheet_name)
        
    def sync(self):
        num_row_last_register = self.config_manager.add_and_get_dict_value_if_not_exist(property.num_row_last_register_student.name, 0)
        num_rows = len(self.__work_sheet.get_all_values())
        first_load = self.config_manager.add_and_get_dict_value_if_not_exist(property.first_load.name, False)
        load_tutores = self.config_manager.add_and_get_dict_value_if_not_exist(property.load_autorizados.name, False)
        load_alumnos_tutor = self.config_manager.add_and_get_dict_value_if_not_exist(property.load_alumnos_tutor.name, False)
        
        if first_load and num_rows > num_row_last_register:
            print(">>>>>ACTUALIZACION DE DATOS<<<<<<<<<<")
            self.update_sync()
        elif not first_load:
            print(">>>>>CARGA INICIAL DE DATOS<<<<<<<<<<")
            self.initial_sync()
        
        if load_tutores:    
            self.sync_autorizados()
        if load_alumnos_tutor:
            self.sync_alumnos_autorizados()
        
    def get_filtered_dataframe(self):
        """Obtiene un DataFrame filtrado con solo las columnas necesarias."""
        df = get_as_dataframe(self.__work_sheet, header=0) #Considerando que la primera fila tiene los encabezados
        required_columns = db.student_column_name()
        return df[required_columns].dropna(how="all")

    def initial_sync(self):
        """Realiza la primera sincronización masiva."""
        df = self.get_filtered_dataframe()
        for _, record in df.iterrows():
            db.add_or_update_student(self.row_to_dict(record))
        
        num_rows = len(self.__work_sheet.get_all_values())
        self.config_manager.add_dict(property.num_row_last_register_student.name, num_rows-1)
        self.config_manager.add_dict(property.first_load.name, True)

    def update_sync(self):
        """Realiza una sincronización incremental desde la última fila sincronizada."""
        num_row_last_register = self.config_manager.add_and_get_dict_value_if_not_exist(property.num_row_last_register_student.name, 0)
        new_row_last_register = 0

        df = self.get_filtered_dataframe()

        for indice, record in df.iterrows():
            if indice >= num_row_last_register:
                db.add_or_update_student(self.row_to_dict(record))
                new_row_last_register = indice

        self.config_manager.add_dict(property.num_row_last_register_student.name, new_row_last_register)

    def sync_autorizados(self):
        """Sincroniza los datos de autorizados desde Google Sheets."""
        worksheet_autorizados = self.__sheet.worksheet(f"{self.__work_sheet_name} Autorizados")
        df_autorizados = get_as_dataframe(worksheet_autorizados, header=0)
        df_autorizados = df_autorizados.dropna(how="all")
        start_index = self.config_manager.add_and_get_dict_value_if_not_exist(property.num_row_last_register_autorizados.name, False)

        for _, record in df_autorizados.iloc[start_index:].iterrows():
            autorizado_data = {
                "codigo": str(int(float(record["codigo"]))),
                "nombre": record["nombre"].lower().title(),
                "telefono": str(record["telefono"]),
                "chat_id": str(int(float(record["chat_id"])))
            }
            db.add_or_update_autorizado(autorizado_data)
        
        start_index = df_autorizados.shape[0]
        self.config_manager.add_dict(property.num_row_last_register_autorizados.name, start_index)

    def sync_alumnos_autorizados(self):
        """Sincroniza las relaciones alumno-tutor desde Google Sheets."""
        worksheet_alumnos_autorizados = self.__sheet.worksheet(f"{self.__work_sheet_name} Alumnos Autorizados")
        df_alumnos_autorizados = get_as_dataframe(worksheet_alumnos_autorizados, header=0)
        df_alumnos_autorizados = df_alumnos_autorizados.dropna(how="all")
        start_index = self.config_manager.add_and_get_dict_value_if_not_exist(property.num_row_last_register_alumnos_tutor.name, False)

        for _, record in df_alumnos_autorizados.iloc[start_index:].iterrows():
            codigo = str(int(float(record["codigo"])))
            student_id = str(int(float(record["student_id"])))
            autorizado_id = str(int(float(record["autorizado_id"])))
            
            #student_id = db.get_student_id_by_code(codigo_alumno)
            #autorizado_id = db.get_autorizado_id_by_telefono(telefono_autorizado)
            
            if student_id and autorizado_id:
                alumno_tutor_data = {
                    "codigo": codigo,
                    "student_id": student_id,
                    "autorizado_id": autorizado_id
                }
                db.add_or_update_alumno_tutor(alumno_tutor_data)
        
        start_index = df_alumnos_autorizados.shape[0]
        self.config_manager.add_dict(property.num_row_last_register_alumnos_tutor.name, start_index)
    
    def row_to_dict(self, row_data):
        """Convierte una fila de datos en un diccionario."""
        print(f"=============={row_data[0]}==================")
        return {
            "nombre": row_data[0].lower().title(),
            "apellidos": row_data[1].lower().title(),
            "grado": str(int(float(row_data[2]))), #row_data[2],
            "grupo": row_data[3],
            "codigo": str(int(float(row_data[4]))),  # Convertir a float, luego a int y luego a str
            "chat_id": str(int(float(row_data[5]))),  # Convertir a float, luego a int y luego a str
            "turno": row_data[6].lower()
        }

    def update_breakfast(self, spread_sheet_name:str, breakfast_records):
        service_account = gspread.service_account()
        sheet_breakfast = service_account.open(spread_sheet_name)
        worksheet_name = f"{datetime.today().strftime('%d-%m-%y')} - {self.config_manager.data['school_name']}" 
        
        try:
            work_sheet = sheet_breakfast.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            sheet_breakfast.add_worksheet(title=worksheet_name, rows=1000, cols=10)
            work_sheet = sheet_breakfast.worksheet(worksheet_name)
        # end try
        df = pd.DataFrame(breakfast_records, columns=["Nombre", "Apellidos", "Grado", "Grupo", "Fecha", "Hora"])
        
        gd.set_with_dataframe(work_sheet, df)
        
    def update_entries(self, spread_sheet_name:str, entries_exits_record):
        service_account = gspread.service_account()
        sheet_entry_and_exit = service_account.open(f"Registros entradas y salidas - {spread_sheet_name}")
        #date = datetime.today().strftime('%d-%m-%y')
        worksheet_name = f"{self.config_manager.data['school_name']}" 
        #Verificamos que la hoja de calculo exista, si no la cremos y luego realizamos la exportacion
        try:
            work_sheet = sheet_entry_and_exit.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            sheet_entry_and_exit.add_worksheet(title=worksheet_name, rows=1000, cols=10)
            work_sheet = sheet_entry_and_exit.worksheet(worksheet_name)
        # end try
        #Generamos el dataFrame desde los datos de la consulta de entradas y salidas
        df = pd.DataFrame(entries_exits_record, columns=["Nombre","Apellidos","Grado","Grupo","Hora entrada","Hora salida","Fecha"])
        
        gd.set_with_dataframe(work_sheet, df)

# Código de ejecución
#syncer = DataSync()

# Para la primera sincronización
#syncer.sync()#syncer.initial_sync()

# Para sincronizaciones incrementales
#LAST_SYNCED_ROW = syncer.num_rows  # Puedes guardar este valor en un archivo o en la base de datos para persistencia entre ejecuciones.
#LAST_SYNCED_ROW = syncer.incremental_sync(LAST_SYNCED_ROW)
#FIRS_LOAD = True
