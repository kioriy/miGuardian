# -*- coding: utf-8 
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-19 12:33:12
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2025-10-06 02:14:59
# @Last Modified time: 2025-10-06 01:09:33

from subprocess import call
from kivymd.app import MDApp
from kivy.clock import Clock
from functools import partial
from datetime import datetime
from datetime import timedelta
from kivy.utils import platform
from util.offline import Offline
from unicodedata import normalize
from util.datasync import DataSync
from util.datajson import DataJson
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from util.notification import TelegramNotifier
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivymd.uix.list import ThreeLineAvatarListItem, ImageLeftWidget
import database.miguardiandb as db 
import util.temppath as tp
import threading
import subprocess
import re
import glob
import os
#import service.megasync
#import database.fakedata

class MainScreen(Screen):
    def on_enter(self, *args):
        app = MDApp.get_running_app()
        Clock.schedule_once(partial(app.refocus_ti, 'main', 'barcode_input'))

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
        total_desayunos = len(self.ids.breakfast_student_list.children) + 1
        setting =  DataJson("settings", dict())
        
        if student:
            db.register_breakfast(student.id)
            self.load_breakfast_records() # Refrescar la lista cada vez que se añade un registro nuevo
            self.ids.barcode_input_store.text = ''
            Clock.schedule_once(partial(app.refocus_ti, 'store', 'barcode_input_store'))
            chat_id = student.chat_id#1323264228#student.chat_id
            #chat_id = 1323264228
            print(f"CHAT_ID:<<<<<<<{chat_id}>>>>>>>")
            current_time = datetime.now().strftime('%I:%M:%S %p')
            message = f"El alumno {student.nombre} {student.apellidos} registro un desayuno a las {current_time}"
            '''Mensaje para el padre de familia'''
            threading.Thread(target=app.notification.send_message, args=(chat_id, message,)).start()
            chat_id = setting.add_and_get_dict_value_if_not_exist('chat_id_admin', 0)#1323264228
            #chat_id = setting.add_and_get_dict_value_if_not_exist(1323264228, 0)#1323264228
            current_time = datetime.now().strftime('%d-%m-%Y %I:%M:%S %p')
            school_name = setting.add_and_get_dict_value_if_not_exist("school_name", "SN")
            message = f"{current_time} Total de desayunos: {total_desayunos} de {school_name}, Total al corte ${total_desayunos * 30}"
            '''Mensaje al administrador con el total del corte de caja de los desayunos'''
            threading.Thread(target=app.notification.send_message, args=(chat_id, message,)).start()
        else:
            self.ids.barcode_input_store.text = ''
            Clock.schedule_once(partial(app.refocus_ti, 'store', 'barcode_input_store'))
class MiGuardianApp(MDApp):
    def build(self):
        Window.maximize()
        self.offline = Offline()
        self.title = "mi Guardian v1.11.3"
        #db.updatedb()
        #cleardb.setup_database()# Inicializamos la base de datos al iniciar la app
        self.photos_path = tp.ensure_photos_dir_exists()
        #print(f">>>>>>>>>>{self.photos_path}<<<<<<<<<<<<<<<")
        self.event_logger = DataJson("eventRegister", {"no_student":[], "no_photo":[]})
        self.notification = TelegramNotifier()
        self.settings = DataJson("settings", dict())
        self.screen_status = self.settings.add_and_get_dict_value_if_not_exist('screen_status', 'HDMI')
        #db.updatedb()
        self.sm = ScreenManager()
        
        main_screen = MainScreen(name="main")
        store_screen = StoreScreen(name="store")
        
        self.sm.add_widget(main_screen)
        self.sm.add_widget(store_screen)
        
        if self.offline.status:
            internet_status_icon = main_screen.ids.internet_status_icon
            internet_status_icon.icon = 'wifi-off'
            #internet_status_icon.text_color = (1, 0, 0, 1)
            internet_status_icon.opacity = 0
            internet_status_icon.disabled = True
            
            ds = DataSync()
            ds.sync()
            #self.generate_all_entries_exits_report()#self.generate_entries_exits_report()
        else:
            internet_status_icon = main_screen.ids.internet_status_icon
            internet_status_icon.icon = 'wifi-off'
            internet_status_icon.text_color = (1, 0, 0, 1)
            internet_status_icon.opacity = 1
            internet_status_icon.disabled = False
        
        return self.sm#Builder.load_file('miguardian.kv')

    def on_start(self):
        Clock.schedule_once(partial(self.refocus_ti, 'main', 'barcode_input'))

    def show_student_info(self):
        main_screen = self.root.get_screen('main')
        
        barcode = main_screen.ids.barcode_input.text#self.root.ids.barcode_input.text
        alumnos_tutores_id = '999'
        nombre_autorizado = "False"
        mensaje_pantalla = "Alumno no encontrado"
        
        if barcode.startswith('t'):
            alumnos_tutores_id = barcode[1:]
            student, autorizado = db.get_autorizado_and_student_by_code(alumnos_tutores_id)
            if autorizado:
                nombre_autorizado = autorizado.nombre
            else:
                mensaje_pantalla = "Autorizado no registrado... ACTUALIZANDO DATOS!!\nRegistrar acceso con la credencial de estudiante"
        else:
            student = db.get_student_by_code(barcode)

        placeholder_path = f"{self.photos_path}placeholder.jpeg"
        #self.screen_status = self.settings.data['screen_status']
        
        if student:
            # Genera la ruta de la foto dinámicamente y actualiza la interfaz
            nnombre = self.normalize_s(student.nombre)
            napellidos = self.normalize_s(student.apellidos)
            
            file_exist, photo_path = self.find_photo(nnombre, napellidos)
            #photo_path = f"{self.photos_path}{nnombre} {napellidos}.jpeg"
            #file_exist = tp.file_exist(photo_path)
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
            status = self.register_attendance(student, nombre_autorizado, alumnos_tutores_id)#Clock.schedule_once(lambda dt: self.async_run(self.register_attendance(student))) 
            
            if status == "entrada":
                main_screen.ids.status_message.text = "Registro de entrada exitoso"
                main_screen.ids.status_icon.icon = "door-open"
                main_screen.ids.status_icon.opacity = 1
                main_screen.ids.status_icon.disabled = False
                main_screen.ids.status_icon.text_color = (0, 1, 0, 1)  # verde
            else:
                main_screen.ids.status_message.text = "Registro de salida exitoso"
                main_screen.ids.status_icon.icon = "door-closed"
                main_screen.ids.status_icon.opacity = 1
                main_screen.ids.status_icon.disabled = False
                main_screen.ids.status_icon.text_color = (1, 0, 0, 1)  # rojo
        else:
            main_screen.ids.student_photo.source = placeholder_path   # Imagen por defecto
            main_screen.ids.student_info.text = f"{mensaje_pantalla}"#"Estudiante no encontrado"
            self.notification_student_not_found(barcode)
            
        # Reiniciar el valor del MDTextField
        main_screen.ids.barcode_input.text = ''
        # Mantener el foco en el MDTextField
        Clock.schedule_once(partial(self.refocus_ti, 'main', 'barcode_input'))
        
    def notification_student_not_found(self, barcode):
            current_time = datetime.now().strftime('%I:%M:%S %p')
            #status = db.register_record_es(student.id)
            school_name = self.settings.data["school_name"]
            message = f"No se encontró el registro para el alumno con id {barcode} {current_time} \- {school_name}"
            threading.Thread(target=self.notification.send_message, args=(1323264228, message,)).start()

    def register_attendance(self, student: db.Student, autorizado_nombre, alumnos_tutores_id):
            mensaje_autorizado = ""
            
            if autorizado_nombre != "False" and autorizado_nombre.lower() != "sa":
                mensaje_autorizado = f", por el autorizado {autorizado_nombre}"
                
            #current_time = datetime.now().strftime('%H:%M:%S') # Obtener la hora actual
            chat_id = student.chat_id#1323264228#student.chat_id
            #chat_id = 1323264228
            print(f"CHAT_ID:<<<<<<<{chat_id}>>>>>>>")
            current_time = datetime.now().strftime('%I:%M:%S %p')
            status = db.register_record_es(student.id, alumnos_tutores_id)
            message = f"El 👨‍🎓 alumno {student.nombre} {student.apellidos} registro su {status} a las ⏰ {current_time}{mensaje_autorizado}"
            threading.Thread(target=self.notification.send_message, args=(chat_id, message,)).start()
            #threading.Thread(target=self.notification.send_message, args=(1323264228, message,)).start()
            return status
    
    def normalize_s(self, s):
        
        s = s.strip()
        s = s.lower()
        
        # Normaliza la cadena a la forma NFD de Unicode
        s = normalize("NFD", s)
        
        #eliminar las ñ por las n
        s = re.sub(r"\u006e\u0303", "n", s, flags=re.I)
        
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
        type_display_command = self.settings.add_and_get_dict_value_if_not_exist("type_display_command", "./LCD35-show")
        
        try:
            subprocess.run(["sudo", f"{type_display_command}"], cwd="/home/kioriy/LCD-show/")
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
            
    def shutdown_raspberry(self):
        if not hasattr(self, 'shutdown_dialog'):
            self.shutdown_dialog = MDDialog(
                title='Confirmar apagar',
                text='Realmente quieres apagar el sistema miGuardian?',
                size_hint=(0.8, 1),
                elevation = 0,
                buttons=[
                    MDFlatButton(
                        text='CANCELAR',
                        on_release=self.close_shutdown_dialog
                    ),
                    MDFlatButton(
                        text='APAGAR',
                        on_release=self.perform_shutdown
                    )
                ]
            )
        self.shutdown_dialog.open()

    def close_report_dialog(self, *args):
        self.report_dialog.dismiss()
        Clock.schedule_once(partial(self.refocus_ti, 'main', 'barcode_input'))
        
    def close_resumen_dialog(self, *args):
        self.shutdown_dialog.dismiss()

    def perform_shutdown(self, *args):
        # Aquí es donde realmente apagas la Raspberry
        if platform == 'linux' or platform == 'linux2':  # Puede requerir más comprobaciones según tu configuración
            call("sudo shutdown -h now", shell=True)
        self.close_shutdown_dialog()
        
    def generate_breakfast_report(self):
        ds = DataSync()
        # Obtiene los registros de desayuno de la base de datos
        breakfast_records = db.get_all_breakfast_records()

        # Actualiza la hoja de cálculo de Google Sheets
        if len(breakfast_records) > 0:
            ds.update_breakfast(self.settings.data["spreadsheet_name_breakfast"], breakfast_records)
            
            self.dialog = MDDialog(title='Actualización corte de caja',
                                text='Datos actualizados')
            self.dialog.open()

        # Agregar aquí cualquier otra lógica necesaria después de actualizar Google Sheets
        
    def generate_entries_exits_report(self):
        ds = DataSync()
        
        date = datetime.today().date() - timedelta(days=1)
        
        entries_exits_record = db.get_entries_and_exits_by_date(date)
        
        if len(entries_exits_record) > 0:
            ds.update_entries(self.settings.data["school_name"], entries_exits_record)
            
    def generate_all_entries_exits_report(self):
        #Creamos la instancia para de DataSync y acceder a los metodos de sincronizacion
        ds = DataSync()
        #Obtenemos los datos de la base de datos
        entries_exits_record = db.get_all_entries_and_exits()# get_entries_and_exits_by_date(date)
        #Verificamos que la consulta a la base de datos nos devuelva registros
        if len(entries_exits_record) > 0:
            ds.update_entries(self.settings.data["school_name"], entries_exits_record)
        
        self.show_dialog_resumen_report(len(entries_exits_record))
        
        Clock.schedule_once(partial(self.refocus_ti, 'main', 'barcode_input'))
            
    def find_photo(self, nnombre, napellidos):
        # Genera el patrón para buscar cualquier extensión de imagen
        pattern = f"{self.photos_path}{nnombre.strip()} {napellidos.strip()}.*"
        
        # Busca cualquier archivo que coincida con el patrón
        photo_files = glob.glob(pattern)

        # Si se encuentra un archivo, devuelve True y la ruta; de lo contrario, False y None
        if photo_files:
            return True, photo_files[0]  # Devuelve True y el archivo encontrado
        else:
            return False, None  # Devuelve False si no se encuentra ningún archivo

    def show_dialog_resumen_report(self, total_registros):
        if not hasattr(self, 'report_dialog'):
            self.report_dialog = MDDialog(
                title='Resumen reporte',
                text=f'El reporte se genero con {total_registros} registros',
                size_hint=(0.8, 1),
                elevation = 0,
                buttons=[
                    MDFlatButton(
                        text='ACEPTAR',
                        on_release=self.close_report_dialog
                    ),
                ]
            )#commit
            
        self.report_dialog.open()
    
MiGuardianApp().run()
