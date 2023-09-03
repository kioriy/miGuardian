# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-23 23:46:49
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2023-08-24 21:50:03

import requests

class TelegramNotifier:
    def __init__(self):
        self.token = "6061799324:AAFgovrNp5ZKsl4LgojVWiGNL5tZ5BHx0fU" 
        self.base_url = f"https://api.telegram.org/bot{self.token}/"

    def send_message(self, chat_id, message):
        url = self.base_url + "sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message
        }
        response = requests.post(url, data=data)
        return response.json()
