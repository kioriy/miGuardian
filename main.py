# -*- coding: utf-8 
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-19 12:33:12
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2023-09-05 21:01:12

#from kivy.support import install_twisted_reactor
#install_twisted_reactor()

from kivymd.app import MDApp
from kivymd.uix.screen import Screen
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.lang import Builder
from kivy.clock import Clock
from datetime import datetime
from util.datajson import DataJson
from util.notification import TelegramNotifier


#from util.datasync import DataSync
import database.miguardiandb as db 
import util.temppath as tp
import threading
import subprocess
import util.datasync
import re
from unicodedata import normalize
#import service.megasync
#import database.fakedata

class MiGuardianApp(MDApp):
    def build(self):
        db.setup_database()# Inicializamos la base de datos al iniciar la app
        self.photos_path = tp.ensure_photos_dir_exists()
        #print(f">>>>>>>>>>{self.photos_path}<<<<<<<<<<<<<<<")
        self.event_logger = DataJson("eventRegister", {"no_student":[], "no_photo":[]})
        self.notification = TelegramNotifier()
        self.settings = DataJson("settings", dict())
        self.screen_status = self.settings.data['screen_status']
        Clock.schedule_once(self.refocus_ti)
        return Builder.load_file('miguardian.kv')

    def show_student_info(self):
        barcode = self.root.ids.barcode_input.text
        student = db.get_student_by_code(barcode)
        placeholder_path = f"{self.photos_path}placeholder.jpeg"
        #self.screen_status = self.settings.data['screen_status']
        
        if student:
            # Genera la ruta de la foto dinámicamente y actualiza la interfaz
            nnombre = self.normalize_s(student.nombre)
            napellidos = self.normalize_s(student.apellidos)
            
            photo_path = f"{self.photos_path}{nnombre} {napellidos}.jpeg"
            file_exist = tp.file_exist(photo_path)
            status_photo = "" #if file_exist else "FOTOGRAFÍA DEL ALUMNO NO ENCONTRADA"
            
            if not file_exist:
                #Si no existe la foto, registra el evento
                list_no_photo = self.event_logger.data["no_photo"]
                list_no_photo.append(barcode)
                self.event_logger.add_dict("no_photo", list_no_photo)
                status_photo = "SIN FOTOGRAFÍA DEL ALUMNO"
            
            self.root.ids.student_photo.source = photo_path if file_exist else placeholder_path
            self.root.ids.student_photo.size_hint:  (1, 1)
            self.root.ids.student_info.text = (f"Nombre: {student.nombre} {student.apellidos}\n" 
                                            f"Grado: {student.grado}\n" 
                                            f"Grupo: {student.grupo}\n" 
                                            f"{status_photo}" )
            
            #agregar el registro de asistencia del alumno
            status = self.register_attendance(student)#Clock.schedule_once(lambda dt: self.async_run(self.register_attendance(student))) 
            
            if status == "entrada":
                self.root.ids.status_message.text = "Registro de entrada exitoso"
                self.root.ids.status_icon.icon = "door-open"
                self.root.ids.status_icon.text_color = (0, 1, 0, 1)  # verde
            else:
                self.root.ids.status_message.text = "Registro de salida exitoso"
                self.root.ids.status_icon.icon = "door-closed"
                self.root.ids.status_icon.text_color = (1, 0, 0, 1)  # rojo
        else:
            #Si el estudiante no se encuentra en la base de datos, registra el evento
            list_no_student = self.event_logger.data["no_student"]
            list_no_student.append(barcode)
            self.event_logger.add_dict("no_student", list_no_student)
            self.root.ids.student_photo.source = placeholder_path   # Imagen por defecto
            self.root.ids.student_info.text = "Estudiante no encontrado"
        
        # Reiniciar el valor del MDTextField
        self.root.ids.barcode_input.text = ''
        # Mantener el foco en el MDTextField
        Clock.schedule_once(self.refocus_ti)

    def register_attendance(self, student: db.Student):
            #current_time = datetime.now().strftime('%H:%M:%S') # Obtener la hora actual
            chat_id = student.chat_id#1323264228#student.chat_id
            print(f"CHAT_ID:<<<<<<<{chat_id}>>>>>>>")
            current_time = datetime.now().strftime('%I:%M:%S %p')
            status = db.register_record_es(student.id)
            message = f"El alumno {student.nombre} {student.apellidos} registro su {status} a las {current_time}"
            threading.Thread(target=self.notification.send_message, args=(chat_id, message,)).start()
            #self.notification.send_message(chat_id, message)
            return status
    
    def normalize_s(self, s):
        
        s = s.strip()
        s = s.lower()
        # -> NFD y eliminar diacríticos
        s = re.sub(
            r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+", r"\1", 
            normalize( "NFD", s), 0, re.I
            )

        # -> NFC
        s = normalize( 'NFC', s)
        
        return s
    
    def refocus_ti(self, *args):
        self.root.ids.barcode_input.focus = True
        
    def switch_screen(self):
        if self.screen_status == "HDMI":
            self.screen_status = "GPIO"
            self.switch_to_gpio()
            self.dialog = MDDialog(title='Confirma cambio de pantalla',
                                text='Confirma en 10 segundos',
                                buttons=[MDFlatButton(text='Revertir',
                                                        on_release=self.dialog_close_revert),
                                            MDFlatButton(text='Aceptar', 
                                                        on_release=self.dialog_close_accept)])
            self.dialog.open()
            self.counter = 10
            Clock.schedule_interval(self.update_dialog_text, 1)
            self.settings.data['screen_status'] = 'GPIO'
            self.settings.write_data()

        else:
            # Verifica la conexión HDMI
            try:
                subprocess.check_call('tvservice -n', shell=True)
                self.screen_status = "HDMI"
                self.switch_to_hdmi()
                self.settings.data['screen_status'] = 'HDMI'
                self.settings.write_data()
            except subprocess.CalledProcessError:
                print("No hay pantalla HDMI conectada.")

    def update_dialog_text(self, dt):
        self.counter -= 1
        self.dialog.text = f'Confirma en {self.counter} segundos'
        if self.counter <= 0:
            Clock.unschedule(self.update_dialog_text)
            self.dialog.dismiss()
            self.revert_to_hdmi()

    def dialog_close_revert(self, obj):
        Clock.unschedule(self.update_dialog_text)
        self.dialog.dismiss()
        self.revert_to_hdmi()
        
    def dialog_close_accept(self, obj):
        Clock.unschedule(self.update_dialog_text)
        self.dialog.dismiss()

    def switch_to_gpio(self):
        try:
            subprocess.run(["sudo", "./MHS35-show"], cwd="/home/kioriy/LCD-show/")
        except Exception as e:
            print(f"Ocurrió un error al cambiar a la pantalla GPIO: {e}")#subprocess.run(['cd LCD-show/ && sudo ./MHS35-show'], shell=True)

    def switch_to_hdmi(self):
        try:
            subprocess.run(["sudo", "./LCD-hdmi"], cwd="/home/kioriy/LCD-show/")
        except Exception as e:
            print(f"Ocurrió un error al cambiar a la pantalla HDMI: {e}")#subprocess.run(['cd LCD-show/ && sudo ./LCD-hdmi'], shell=True)

    def revert_to_hdmi(self):
        if self.screen_status == "GPIO":
            self.screen_status = "HDMI"
            self.switch_to_hdmi()
            self.settings.data['screen_status'] = 'HDMI'
            self.settings.write_data()

MiGuardianApp().run()