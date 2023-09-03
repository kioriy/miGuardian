# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-28 01:25:49
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2023-09-03 02:54:55
from mega import Mega
import util.temppath as tp
import os

class PhotoSync:

    def __init__(self, email: str, password: str):
        self.mega = Mega()
        self.m = self.mega.login(email, password)
        #self.temp_folder = tp.ensure_photos_dir_exists()

    def download_photos(self, file_name: str):
        """
        Descarga todas las fotos de una carpeta remota de Mega a una carpeta temporal.
        
        :param remote_folder: El nombre de la carpeta remota en Mega.
        """
        self.temp_folder = tp.ensure_photos_dir_exists()
        #folder = self.m.get_files_in_node("https://mega.nz/folder/QYcQgZJS#rMDSWyzWM8I12rkDoiID-A")#('Albert Einstein')
        #folder_import = self.m.get_files_in_node('QVVzEApA')
        file = self.m.find('aaron ruben montero flores.jpeg')
        #sub_folder = self.m.find('Albert Einstein', folder_import[0]['h']) #folder_import = self.m.get_files_in_node('QVVzEApA')
        #print(f"Import url >>>>>> {folder_import}")
        #folder = self.m.find('EJ1FhbSS', folder_import[0])
        #print(f"Find sesiones fotografias >>>>> {folder}")
        #folder_ei = self.m.find('Albert Einstein')
        
        #print(f"Carpeta albert einstin >>>>> {folder_ei}")
        #folder_url = self.m.find('https://mega.nz/folder/AUtyGQ4D#qlHZBHySqhJ_wO_uOOGy4w')
        #print(folder_url)
        # Obtener el3 ID de la carpeta
        #folder_id = 'EJ1FhbSS'#folder[1]['h']
        #folder_id = list_data['h']
        # Obtener el contenido de la carpeta
        #folder_content = self.m.get_files_in_node(folder_id)
        
        #if folder is not None:
            # Iterar sobre los archivos en la carpeta y descargarlos
            
        
        try:
            self.m.download(file, self.temp_folder, )
        except KeyError as e:
            print(f"Clave no encontrada: {e}")
'''
        for file_id, file_data in folder_content.items():
            try:
                if 't' in file_data and file_data['t'] == 0:
                    print(f"Descargando archivo: {file_data['a']}")
                    self.m.download(file, self.temp_folder, )
            except KeyError as e:
                print(f"Clave no encontrada: {e}")
        #else:
        #    print("La carpeta 'Albert Einstein' no se encuentra en Mega.")
'''

'''
    def sync_photos(self):
        """
        Sincroniza las fotos descargadas a una carpeta local.
        """
        local_folder = tp.temp_path()  # Obteniendo la carpeta temporal del sistema
        for filename in os.listdir(self.temp_folder):
            local_path = os.path.join(local_folder, filename)
            temp_path = os.path.join(self.temp_folder, filename)
            os.rename(temp_path, local_path)
'''

# Uso
email = "kioriy@hotmail.com"
password = "yagamiKY*17"
remote_folder = "Sesion fotografica/Albert Einstein"#"https://mega.nz/fm/EJ1FhbSS"


photo_sync = PhotoSync(email, password)
#folder = photo_sync.m.find("Albert Einstein")
#print(folder)
photo_sync.download_photos(remote_folder)
#photo_sync.sync_photos()