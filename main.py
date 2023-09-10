# -*- coding: utf-8 
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-19 12:33:12
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2023-09-10 14:43:21

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
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.list import ThreeLineAvatarListItem, ImageLeftWidget


#from util.datasync import DataSync
import database.miguardiandb as db 
import util.temppath as tp
import threading
import subprocess
import util.datasync
import re
from unicodedata import normalize
from functools import partial

#import service.megasync
#import database.fakedata

class MainScreen(Screen):
    pass

class StoreScreen(Screen):
    def on_enter(self, *args):
        list_items = len(self.ids.breakfast_student_list.children)
        app = MDApp.get_running_app()
        Clock.schedule_once(partial(app.refocus_ti, 'store', 'barcode_input_store'))
        
        if list_items == 0:
            self.load_breakfast_records()
        
    def load_breakfast_records(self):
        breakfast_records = db.get_today_breakfast_records()#db.get_breakfast_records()
        app = MDApp.get_running_app()
        self.ids.breakfast_student_list.clear_widgets()
        
        for record in breakfast_records:
            list_item = ThreeLineAvatarListItem(
                text= f"{record.nombre} {record.apellidos}" ,
                secondary_text=f"{record.grado} - {record.grupo}",
                tertiary_text=str(f"{record.date.strftime('%d-%m-%y')} {record.time}")
            )
            
            nnombre = app.normalize_s(record.nombre)
            napellidos = app.normalize_s(record.apellidos)
        
            avatar = ImageLeftWidget(source=f"fotos/{nnombre} {napellidos}.jpeg")
            list_item.add_widget(avatar)
            self.ids.breakfast_student_list.add_widget(list_item)
            
        
    def register_new_breakfast(self, codigo):
        student = db.get_student_by_code(codigo)
        app = MDApp.get_running_app()
        
        if student:
            db.register_breakfast(student.id)
            self.load_breakfast_records() # Refrescar la lista cada vez que se añade un registro nuevo
            self.ids.barcode_input_store.text = ''
            Clock.schedule_once(partial(app.refocus_ti, 'store', 'barcode_input_store'))
            

class MiGuardianApp(MDApp):
    def build(self):
        db.setup_database()# Inicializamos la base de datos al iniciar la app
        self.photos_path = tp.ensure_photos_dir_exists()
        #print(f">>>>>>>>>>{self.photos_path}<<<<<<<<<<<<<<<")
        self.event_logger = DataJson("eventRegister", {"no_student":[], "no_photo":[]})
        self.notification = TelegramNotifier()
        self.settings = DataJson("settings", dict())
        self.screen_status = self.settings.get_dict_value('screen_status', 'HDMI')
        #Clock.schedule_once(partial(self.refocus_ti('main', 'barcode_input')))
        
        self.sm = ScreenManager()
        
        main_screen = MainScreen(name="main")
        store_screen = StoreScreen(name="store")
        
        self.sm.add_widget(main_screen)
        self.sm.add_widget(store_screen)
        
        #Clock.schedule_once(partial(self.refocus_ti('main', 'barcode_input')))
        
        return self.sm#Builder.load_file('miguardian.kv')

    def on_start(self):
        Clock.schedule_once(partial(self.refocus_ti, 'main', 'barcode_input'))

    def show_student_info(self):
        main_screen = self.root.get_screen('main')
        
        barcode = main_screen.ids.barcode_input.text#self.root.ids.barcode_input.text
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
            
            main_screen.ids.student_photo.source = photo_path if file_exist else placeholder_path
            main_screen.ids.student_photo.size_hint:  (1, 1)
            main_screen.ids.student_info.text = (f"Nombre: {student.nombre} {student.apellidos}\n" 
                                            f"Grado: {student.grado}\n" 
                                            f"Grupo: {student.grupo}\n" 
                                            f"{status_photo}" )
            
            #agregar el registro de asistencia del alumno
            status = self.register_attendance(student)#Clock.schedule_once(lambda dt: self.async_run(self.register_attendance(student))) 
            
            if status == "entrada":
                main_screen.ids.status_message.text = "Registro de entrada exitoso"
                main_screen.ids.status_icon.icon = "door-open"
                main_screen.ids.status_icon.text_color = (0, 1, 0, 1)  # verde
            else:
                main_screen.ids.status_message.text = "Registro de salida exitoso"
                main_screen.ids.status_icon.icon = "door-closed"
                main_screen.ids.status_icon.text_color = (1, 0, 0, 1)  # rojo
        else:
            #Si el estudiante no se encuentra en la base de datos, registra el evento
            list_no_student = self.event_logger.data["no_student"]
            list_no_student.append(barcode)
            self.event_logger.add_dict("no_student", list_no_student)
            main_screen.ids.student_photo.source = placeholder_path   # Imagen por defecto
            main_screen.ids.student_info.text = "Estudiante no encontrado"
        
        # Reiniciar el valor del MDTextField
        main_screen.ids.barcode_input.text = ''
        # Mantener el foco en el MDTextField
        Clock.schedule_once(partial(self.refocus_ti, 'main', 'barcode_input'))

    def register_attendance(self, student: db.Student):
            #current_time = datetime.now().strftime('%H:%M:%S') # Obtener la hora actual
            chat_id = 1323264228 #student.chat_id#1323264228#student.chat_id
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
    
    def refocus_ti(self, screen_name, control_id, dt):
        screen = self.root.get_screen(screen_name)
        if screen:
            control = screen.ids.get(control_id)
            if control:
                control.focus = True
        
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
            
    def switch_form(self):
        if self.sm.current == "main":
            self.sm.current = "store"
        else:
            self.sm.current = "main"

MiGuardianApp().run()