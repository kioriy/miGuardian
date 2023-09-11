# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-22 22:31:42
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2023-09-11 02:15:07

import gspread
from gspread_dataframe import get_as_dataframe
from util.datajson import DataJson 
import database.miguardiandb as db  # Asumiendo que miguardiandb tiene las funciones necesarias para interacción con la BD.
import pandas as pd

class DataSync:

    __service_account = gspread.service_account()
    __sheet = __service_account.open("8020digital")

    def __init__(self):
        self.config_manager = DataJson("settings", dict())
        work_sheet_name = self.config_manager.data['school_name']
        self.__work_sheet_name = work_sheet_name
        self.__work_sheet = self.__sheet.worksheet(self.__work_sheet_name)
        #self.config_manager = DataJson("settings", dict())#{"first_load_completed": False, "total_records": 0})
        #self.config = self.config_manager.data
        #self.num_rows = self.__work_sheet.row_count()
        
    def sync(self):
        num_row_last_register = self.config_manager.get_dict_value('num_row_last_register', 0)
        num_rows = len(self.__work_sheet.get_all_values())
        first_load = self.config_manager.get_dict_value('first_load', False)
        if first_load and num_rows > num_row_last_register:
            print(">>>>>ACTUALIZACION DE DATOS<<<<<<<<<<")
            self.update_sync()
        elif not first_load:
            print(">>>>>CARGA INICIAL DE DATOS<<<<<<<<<<")
            self.initial_sync()
        
    def get_filtered_dataframe(self):
        """Obtiene un DataFrame filtrado con solo las columnas necesarias."""
        df = get_as_dataframe(self.__work_sheet, header=0)  # Considerando que la primera fila tiene los encabezados
        required_columns = db.student_column_name()
        return df[required_columns].dropna(how="all")

    def initial_sync(self):
        """Realiza la primera sincronización masiva."""
        df = self.get_filtered_dataframe()
        for _, record in df.iterrows():
            db.add_or_update_student(self.row_to_dict(record))
        
        num_rows = len(self.__work_sheet.get_all_values()) - 1
        self.config_manager.add_dict("num_row_last_register", num_rows) #self.__work_sheet.row_count)
        self.config_manager.add_dict("first_load", True)

    def update_sync(self):
        """Realiza una sincronización incremental desde la última fila sincronizada."""
        #total_rows = self.__work_sheet.row_count
        num_row_last_register = self.config_manager.get_dict_value("num_row_last_register", 0)
        num_rows = len(self.__work_sheet.get_all_values())
        new_records = []
        for i in range(num_row_last_register + 1, num_rows, 1):
            row_data = self.__work_sheet.row_values(i)
            new_records.append(self.row_to_dict(row_data))
        
        for record in new_records:
            db.add_or_update_student(record)  # Función hipotética que agrega o actualiza un registro.

        return self.__work_sheet.row_count

    def row_to_dict(self, row_data):
        """Convierte una fila de datos en un diccionario."""
        return {
        "nombre": row_data[0].lower().title(),
        "apellidos": row_data[1].lower().title(),
        "grado": str(int(float(row_data[2]))), #row_data[2],
        "grupo": row_data[3],
        "codigo": str(int(float(row_data[4]))),  # Convertir a float, luego a int y luego a str
        "chat_id": str(int(float(row_data[5])))  # Convertir a float, luego a int y luego a str
    }

# Código de ejecución
syncer = DataSync()

# Para la primera sincronización
syncer.sync()#syncer.initial_sync()

# Para sincronizaciones incrementales
#LAST_SYNCED_ROW = syncer.num_rows  # Puedes guardar este valor en un archivo o en la base de datos para persistencia entre ejecuciones.
#LAST_SYNCED_ROW = syncer.incremental_sync(LAST_SYNCED_ROW)
#FIRS_LOAD = True
