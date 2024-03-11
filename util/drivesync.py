# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-12-03 20:49:09
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2023-12-03 23:14:34
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

# Autenticación y creación del cliente de Google Drive
gauth = GoogleAuth()
gauth.LoadCredentialsFile("credentials.json")
if gauth.credentials is None:
    gauth.LocalWebserverAuth()
elif gauth.access_token_expired:
    gauth.Refresh()
else:
    gauth.Authorize()
gauth.SaveCredentialsFile("credentials.json")

drive = GoogleDrive(gauth)

# Subir archivo
def upload():
    file1 = drive.CreateFile({'title': 'Hello.txt'})  # Crear un archivo de Google Drive
    file1.SetContentString('Hello World!')  # Establecer contenido del archivo
    file1.Upload()  # Subir el archivo
    print('Archivo subido, ID: %s' % file1.get('id'))

# Bajar archivo
def download():
    file_id = 'Hello.txt'
    file2 = drive.CreateFile({'id': file_id})
    file2.GetContentFile('destination_filename.txt')  # Descargar archivo como 'destination_filename.txt'

download()#upload()