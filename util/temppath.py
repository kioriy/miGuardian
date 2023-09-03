# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-20 22:31:21
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2023-08-28 02:37:14

import os
import tempfile

def file_exist(file_path):
    return os.path.exists(file_path)

def ensure_photos_dir_exists():
    """Asegura que la carpeta 'fotos' exista en el directorio temporal."""
    temp_dir = tempfile.gettempdir()
    photos_dir = os.path.join(temp_dir, "fotos")
    os.makedirs(photos_dir, exist_ok=True)
    return os.path.join(photos_dir, "")

#ensure_photos_dir_exists()
# Ejemplo de uso:
#relative_path = generate_temp_path(".png")
#print(relative_path)
