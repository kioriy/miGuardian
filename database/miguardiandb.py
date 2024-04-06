# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-19 22:41:55
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2024-04-05 19:02:56
#from sqlalchemy.exc import NoSuchTableError
from datetime import datetime, time, date, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Time, Date, Table, MetaData
from util.datajson import DataJson
import json
import os
import shutil

#from util.datajson import DataJson

Base = declarative_base()

# Definición de la tabla Student
class Student(Base):
    __tablename__ = 'student'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    grado = Column(String, nullable=False)
    grupo = Column(String, nullable=False)
    codigo = Column(String, unique=True, index=True, nullable=False)
    chat_id = Column(String)
    turno = Column(String, nullable=False)
    # Relación con la tabla attendance
    attendances = relationship("Attendance", back_populates="student")
    breakfasts = relationship("Breakfast", back_populates="student")
    
    def serialize(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellidos": self.apellidos,
            "grado": self.grado,
            "grupo": self.grupo,
            "codigo": self.codigo,
            "chat_id": self.chat_id
        }

class Breakfast(Base):
    __tablename__ = 'breakfast'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=datetime.today().date())
    time = Column(Time,)
    
    student_id = Column(Integer, ForeignKey('student.id'))
    student = relationship("Student", back_populates="breakfasts")
    
    def serialize(self):
        return {
            "id": self.id,
            "date": self.date,
            "time": self.time
        }

# Definición de la tabla Attendance
class Attendance(Base):
    __tablename__ = 'attendance'

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=datetime.today().date())
    entry_time = Column(Time,)
    exit_time = Column(Time, default=time(0,0))
    student_id = Column(Integer, ForeignKey('student.id'))
    
    # Relación con la tabla student
    student = relationship("Student", back_populates="attendances")
    
    def serialize(self):
        return {
            "id": self.id,
            "date": self.date,
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "student_id": self.student_id
        }

# Configuración de la base de datos (usando SQLite local)
DATABASE_URL = "sqlite:///./miguardian.db"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
metadata = MetaData()

def setup_database():
    Base.metadata.create_all(bind=engine)

def student_column_name():
    return [column.name for column in Student.__table__.columns if column.name != 'id']#return [column.name for column in Student.__table__.columns]
    '''
    try:
        student_table = Table('student', metadata, autoload=True, autoload_with=engine)
        column_names = [Column.name for column in student_table.columns]
        return column_names
    except NoSuchTableError:
        print("Error: La tabla 'student' no existe en la base de datos.")
        return []
    except Exception as e:
        print(f"Error al obtener los nombres de columna: {e}")
        return []
        '''

def add_student(student_data):
    db_session = SessionLocal()
    student = Student(**student_data)
    db_session.add(student)
    db_session.commit()
    db_session.close()

def updatedb():
    db_session = SessionLocal()
    settings = DataJson("settings", dict())
    settings.add_and_get_dict_value_if_not_exist("status_update_db", True)
    
    if settings['status_update_db']:
        today = datetime.now().strftime("%Y-%m-%d")
        name_folder_backup = f"respaldo_{today}"
        os.makedirs(name_folder_backup, exist_ok=True)
        
        #Mover una copia de la base de datos
        shutil.copy('miguardian.db', f"{name_folder_backup}/miguardian_{today}.db")
        
        #realizar respaldo de las tablas de la base de datos
        json_student_backup = DataJson(f"{name_folder_backup}/student_backup", dict())
        students_backup = db_session.query(Student).all()
        students_backup = list(map(lambda x: x.serialize(), students_backup))
        json_student_backup.data = students_backup
        json_student_backup.write_data()
    
    db_session.close()
    
def add_or_update_student(student_data: dict):
    """
    Añade o actualiza un estudiante en la base de datos.
    
    :param student_data: Diccionario que contiene la información del estudiante.
    """
    db_session = SessionLocal()

    existing_student = db_session.query(Student).filter_by(codigo=student_data['codigo']).first()

    # Si el estudiante existe, actualizamos sus datos
    try: #sqlite3.IntegrityError 
        if existing_student:
            for key, value in student_data.items():
                setattr(existing_student, key, value)
        # Si no existe, lo añadimos a la base de datos
        else:
            new_student = Student(**student_data)
            db_session.add(new_student)
            
        db_session.commit()
        db_session.close()
    except Exception as e:
        raise e
    # end try
    

def get_student_by_code(codigo):
    db_session = SessionLocal()
    student = db_session.query(Student).filter(Student.codigo == codigo).first()
    db_session.close()
    return student

def update_student_by_code(codigo, student_data):
    db_session = SessionLocal()
    student = db_session.query(Student).filter(Student.codigo == codigo).first()
    for key, value in student_data.items():
        setattr(student, key, value)
    db_session.commit()
    db_session.close()

def delete_student_by_code(codigo):
    db_session = SessionLocal()
    student = db_session.query(Student).filter(Student.codigo == codigo).first()
    db_session.delete(student)
    db_session.commit()
    db_session.close()

def get_current_time_without_microseconds():
    now = datetime.now()
    return time(now.hour, now.minute, now.second)

def register_record_es(student_id):
    db_session = SessionLocal()

    # Fecha actual
    today = datetime.today().date()

    # Busca si ya existe un registro para el estudiante en el día actual
    attendance = db_session.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.date == today
    ).first()

    current_time = get_current_time_without_microseconds()
    
    status: str

    if not attendance:
        # Registra la entrada
        new_attendance = Attendance(entry_time=current_time, student_id=student_id)
        db_session.add(new_attendance)
        status = "entrada"
    else:
        # Registra la salida
        attendance.exit_time = current_time
        status = "salida"

    db_session.commit()
    db_session.close()
    
    return status

# Funciones relacionadas con la tabla Breakfast
def register_breakfast(student_id):
    db_session = SessionLocal()
    
    current_time = get_current_time_without_microseconds()

    new_breakfast = Breakfast(time=current_time, student_id=student_id)
    db_session.add(new_breakfast)
    
    db_session.commit()
    db_session.close()

def get_breakfast_records():
    db_session = SessionLocal()

    results = db_session.query(
        Student.nombre, 
        Student.apellidos, 
        Student.grado, 
        Student.grupo, 
        Breakfast.date,
        Breakfast.time
    ).join(Breakfast, Student.id == Breakfast.student_id).all()

    db_session.close()
    return results

def get_today_breakfast_records():
    db_session = SessionLocal()
    
    # Fecha actual
    today = datetime.today().date()
    #start_date = datetime(year=2024, month=1, day=1)
    #end_date = datetime(year=2024, month=1, day=15)
    
    # Obtener la fecha actual
    
    #fecha_actual = datetime.now()

    # Obtener el primer día del mes actual
    #primer_dia_mes = fecha_actual.replace(day=1)

    # Obtener la fecha actual más 15 días
    #fecha_15_dias = primer_dia_mes + timedelta(days=15)

    # Calcular la fecha de inicio y la fecha de fin para el rango
    #start_date = primer_dia_mes
    #end_date = fecha_15_dias

    # Verificar si los primeros 15 días ya han pasado
    #if fecha_actual.day > 15:
        # Si ya pasaron, ajusta las fechas para los 15 días siguientes
        #start_date = fecha_actual.replace(day=16)
        #end_date = fecha_actual + timedelta(days=30)

    # Busca registros de desayunos del día actual
    today_records = db_session.query(
        Student.nombre, 
        Student.apellidos, 
        Student.grado, 
        Student.grupo, 
        Breakfast.date,
        Breakfast.time
        ).join(
            Student, 
            Breakfast.student_id == Student.id
            ).filter(
                Breakfast.date == today#start_date, end_date)
                ).order_by(Breakfast.date.desc(), Breakfast.time.desc()).all()
    
    db_session.close()
    
    return today_records

def get_all_breakfast_records():
    db_session = SessionLocal()
    
    # Obtener la fecha actual
    fecha_actual = datetime.now()

    # Obtener el primer día del mes actual
    primer_dia_mes = fecha_actual.replace(day=1)

    # Obtener la fecha actual más 15 días
    fecha_15_dias = primer_dia_mes + timedelta(days=15)

    # Calcular la fecha de inicio y la fecha de fin para el rango
    start_date = primer_dia_mes
    end_date = fecha_15_dias

    # Verificar si los primeros 15 días ya han pasado
    if fecha_actual.day > 15:
        # Si ya pasaron, ajusta las fechas para los 15 días siguientes
        start_date = fecha_actual.replace(day=16)
        end_date = fecha_actual + timedelta(days=30)

    # Busca registros de desayunos del día actual
    today_records = db_session.query(
        Student.nombre, 
        Student.apellidos, 
        Student.grado, 
        Student.grupo, 
        Breakfast.date,
        Breakfast.time
        ).join(
            Student, 
            Breakfast.student_id == Student.id
            ).filter(
                Breakfast.date.between(start_date, end_date)
                ).order_by(Breakfast.date.desc(), Breakfast.time.desc()).all()
    
    db_session.close()
    
    return today_records

def get_entries_and_exits_by_date(target_date: date):
    db_session = SessionLocal()
    
    entries_and_exits = db_session.query(
        Student.nombre,
        Student.apellidos,
        Attendance.entry_time,
        Attendance.exit_time,
        Attendance.date
    ).join(
        Attendance,
        Student.id == Attendance.student_id
    ).filter(
        Attendance.date == target_date
    ).all()

    return entries_and_exits

def get_all_entries_and_exits():
    db_session = SessionLocal()
    
    entries_and_exits = db_session.query(
        Student.nombre,
        Student.apellidos,
        Attendance.entry_time,
        Attendance.exit_time,
        Attendance.date
    ).join(
        Attendance,
        Student.id == Attendance.student_id
    ).order_by(Attendance.date.desc()).all()

    return entries_and_exits

def get_noCheckIn_student():
    db_session = SessionLocal()
    hoy = datetime.today().date()
    #manager_no_checkin_student = DataJson("estudiantes_sin_entrada.json", [])

    # Consulta todos los estudiantes
    todos_los_estudiantes = db_session.query(Student).all()
    # Consulta los registros de asistencia para hoy
    asistencias_hoy = db_session.query(Attendance).filter(Attendance.date == hoy).all()

    # Crear un conjunto de ID de estudiantes con asistencias registradas hoy
    ids_con_asistencia = {asistencia.student_id for asistencia in asistencias_hoy}

    # Filtrar estudiantes sin asistencias hoy
    estudiantes_sin_entrada = [est for est in todos_los_estudiantes if est.id not in ids_con_asistencia]

    #manager_no_checkin_student.data = estudiantes_sin_entrada
    #manager_no_checkin_student.write_data()
    # Crear una lista para almacenar los datos de los estudiantes
    estudiantes_sin_entrada_datos = [{
        'nombre': est.nombre,
        'apellidos': est.apellidos,
        'grado': est.grado,
        'grupo': est.grupo
    } for est in estudiantes_sin_entrada]

    # Escribir los datos en un archivo JSON
    with open('estudiantes_sin_entrada.json', 'w') as archivo_json:
        json.dump(estudiantes_sin_entrada_datos, archivo_json, indent=4, ensure_ascii=False)

    db_session.close()
    #return estudiantes_sin_entrada

setup_database()
