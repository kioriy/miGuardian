# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2024-12-07 21:11:18
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2025-01-29 22:38:59
import sys
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton
from PySide6.QtCore import QFile, QIODevice


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.load_ui()  # Cargar el archivo .ui
        self.window.show()  # Mostrar la ventana principal

    def load_ui(self):
        # Ruta del archivo .ui
        ui_file_name = "../miGuardian/interfaces/mainwindows.ui"
        ui_file = QFile(ui_file_name)

        # Intentar abrir el archivo .ui
        if not ui_file.open(QIODevice.ReadOnly):
            print(f"Cannot open {ui_file_name}: {ui_file.errorString()}")
            sys.exit(-1)
        
        # Crear un cargador para archivos .ui
        loader = QUiLoader()

        # Cargar el archivo .ui en la ventana principal
        self.window = loader.load(ui_file, self)
        ui_file.close()

        # Verificar si la carga fue exitosa
        if not self.window:
            print(loader.errorString())
            sys.exit(-1)

        #acceder a los widgets generados en qt desinger
        btn = self.window.btn_iniciar_sesion
        if btn:
            btn.setText("Acceso desde atributo")
        '''btn = self.window.findChild(QPushButton, "btn_iniciar_sesion")
        if btn:
            print("si btn")
            btn.setText("XXXXXXXXX")'''
        # Ajustar el diseño de la ventana
        self.setCentralWidget(self.window)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec())
