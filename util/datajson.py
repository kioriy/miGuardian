# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-07-23 01:16:34
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2024-04-22 20:37:31
import json
import os
import numpy as np
#import pandas as pd

class DataJson:
    def __init__(self, file_name, any_data):
        """_summary_
            Crea la instancia de un archivo json
            se envía como parámetro el nombre del archivo
        Args:
            file_name (_str_): _description_ nombre del archivo
        """
        self.file_name = file_name
        self.create_file_if_not_exist()
        self.file_is_empty = self.file_is_empty()
        if not self.file_is_empty:
            self.data = self.load_data()
        else:
            self.data = any_data

    def add(self, new_data):
        self.data.append(new_data)
        self.write_data()

    def add_dict(self, key, value):
        self.data[f"{key}"] = value
        self.write_data()
        
    def add_and_get_dict_value_if_not_exist(self, key: str, value_if_key_not_exist):
        value = self.data.get(key, value_if_key_not_exist)
        if value == value_if_key_not_exist:
            self.add_dict(key, value)
        return value
    
    def load_data(self):
        with open(f"{self.file_name}.json") as j:
            return json.load(j)
        
    def write_data(self):
        #self.data = self.data.to_json(orient="values")
        with open(f"{self.file_name}.json", "w") as j:
            json.dump(self.data, j, indent=4, sort_keys=True)

    def exist_key(self, id: str):
        return id in self.data #True if len(list(filter(lambda x: x["id"]==id, self.data))) > 0 else False
    
    def get_index(self, value: str)-> int:
        return np.where(self.data == value) #self.data.index[f'{id}']s

    def create_file_if_not_exist(self):
        if not os.path.isfile(f"{self.file_name}.json"):
            open(f"{self.file_name}.json", "x")
            
    def file_is_empty(self)-> bool:
        return False if os.stat(f"{self.file_name}.json").st_size != 0 else True

    
