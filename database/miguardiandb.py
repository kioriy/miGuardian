# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-19 22:41:55
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2023-08-28 00:23:54
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Time, Date, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import NoSuchTableError
from datetime import datetime, time, date

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
    # Relación con la tabla attendance
    attendances = relationship("Attendance", back_populates="student")

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

setup_database()
