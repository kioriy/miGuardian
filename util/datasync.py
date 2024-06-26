# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-22 22:31:42
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2024-04-30 19:50:07

import gspread
from gspread_dataframe import get_as_dataframe
import gspread_dataframe as gd
from util.datajson import DataJson 
import database.miguardiandb as db  # Asumiendo que miguardiandb tiene las funciones necesarias para interacción con la BD.
import pandas as pd
from datetime import datetime, time, date, timedelta

class DataSync:

    #__service_account = gspread.service_account()
    #__sheet = __service_account.open("8020digital")
    
    def __init__(self):
        self.__service_account = gspread.service_account()
        self.__sheet = self.__service_account.open("8020digital")
        self.config_manager = DataJson("settings", dict())
        work_sheet_name = self.config_manager.data['school_name']
        self.__work_sheet_name = work_sheet_name
        self.__work_sheet = self.__sheet.worksheet(self.__work_sheet_name)
        
    def sync(self):
        num_row_last_register = self.config_manager.add_and_get_dict_value_if_not_exist('num_row_last_register', 0)
        num_rows = len(self.__work_sheet.get_all_values())
        first_load = self.config_manager.add_and_get_dict_value_if_not_exist('first_load', False)
        if first_load and num_rows > num_row_last_register:
            print(">>>>>ACTUALIZACION DE DATOS<<<<<<<<<<")
            self.update_sync()
        elif not first_load:
            print(">>>>>CARGA INICIAL DE DATOS<<<<<<<<<<")
            self.initial_sync()
        
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
        self.config_manager.add_dict("num_row_last_register", num_rows-1)
        self.config_manager.add_dict("first_load", True)

    def update_sync(self):
        """Realiza una sincronización incremental desde la última fila sincronizada."""
        num_row_last_register = self.config_manager.add_and_get_dict_value_if_not_exist("num_row_last_register", 0)
        new_row_last_register = 0

        df = self.get_filtered_dataframe()

        for indice, record in df.iterrows():
            if indice >= num_row_last_register:
                db.add_or_update_student(self.row_to_dict(record))
                new_row_last_register = indice

        self.config_manager.add_dict("num_row_last_register", new_row_last_register)

    def row_to_dict(self, row_data):
        """Convierte una fila de datos en un diccionario."""
        print(f"=============={row_data[0]}==================")
        return {
        "nombre": row_data[0].lower().title(),
        "apellidos": row_data[1].lower().title(),
        "grado": str(int(float(row_data[2]))), #row_data[2],
        "grupo": row_data[3],
        "codigo": str(int(float(row_data[4]))),  # Convertir a float, luego a int y luego a str
        "chat_id": str(int(float(row_data[5])))  # Convertir a float, luego a int y luego a str
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
