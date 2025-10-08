# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-23 23:46:49
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2025-10-08 09:01:34

import requests

class TelegramNotifier:
    def __init__(self):
        self.token = "6061799324:AAEcfontKz7QXUKkPHmolU24encwXrZY9gs" 
        self.base_url = f"https://api.telegram.org/bot{self.token}/"

    def send_message(self, chat_id, message, image_path=None):
        """Metodo para enviar mensajes a un bot en telegram

        Args:
            chat_id ([str]]): [chat id del usuario]
            message ([str]): [mensaje personalizado para el usuario]

        Returns:
            [json]: [mensaje de retorno de la api telegram]
        """
        if image_path:
            # Si se proporciona una imagen, enviar la imagen junto con el mensaje
            url = self.base_url + "sendPhoto"
            files = {'photo': open(image_path, 'rb')}
            data = {
                'chat_id': chat_id,
                'caption': message,
                'parse_mode': 'MarkdownV2'  # Si el mensaje está en HTML; usa 'Markdown' si es el caso
            }
            response = requests.post(url, data=data, files=files)
        else:
            url = self.base_url + "sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'MarkdownV2'
            }
            response = requests.post(url, data=data)
            
        print(f"{response.json()}")
        return response.json()
    
    def send_video(self, chat_id, video_path, caption=""):
        """Método para subir un video a un bot en Telegram y obtener el file_id"""
        url = self.base_url + "sendDocument"
        files = {'video': open(video_path, 'rb')}
        data = {
            'chat_id': chat_id,
            'caption': caption,
            'parse_mode': 'MarkdownV2'
        }
        response = requests.post(url, data=data, files=files)
        result = response.json()
        print(f"{result}")
        if result['ok']:
            return result['result']['video']['file_id']
        else:
            return None

    def send_video_by_id(self, chat_id, file_id, caption=""):
        """Método para compartir un video ya subido usando file_id"""
        url = self.base_url + "sendVideo"
        data = {
            'chat_id': chat_id,
            'video': file_id,
            'caption': caption,
            'parse_mode': 'MarkdownV2'
        }
        response = requests.post(url, data=data)
        print(f"{response.json()}")
        return response.json()
