# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-10-15 02:25:18
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2023-10-15 14:06:35
import socket

class Offline():
    
    def __init__(self):
        self.status = self.check_internet_connection()
    
    def check_internet_connection(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(3)
        try:
            s.connect(("www.google.com", 80))
        except (socket.gaierror, socket.timeout):
            print("Sin conexión a internet")
            return False
        else:
            print("Con conexión a internet")
            s.close()
            return True

        # Si se produce una excepción, se asume que no hay conexión a Internet
        #return False

#Offline()