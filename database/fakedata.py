# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2023-08-20 22:49:20
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2023-08-24 03:06:32

from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from faker import Faker
import database.miguardiandb as db

Base = declarative_base()
DATABASE_URL = "sqlite:///./miguardian.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Definición del modelo ya está en miguardiandb, así que podemos omitirlo aquí

fake = Faker()

def insert_fake_students(n):
    # Asegurarse de que la base de datos y las tablas estén creadas
    db.setup_database()

    session = SessionLocal()
    for _ in range(n):
        # Generando datos ficticios
        codigo = fake.unique.random_number(digits=2)
        nombre = fake.first_name()
        apellido = fake.last_name()
        grado = fake.random_element(elements=('1ro', '2do', '3ro', '4to', '5to', '6to'))
        grupo = fake.random_element(elements=('A', 'B', 'C', 'D'))
        chat_id = fake.random_number(digits=10)
        
        # Creando y añadiendo el estudiante ficticio a la sesión
        student = db.Student(nombre=nombre, apellidos=apellido, grado=grado, grupo=grupo, codigo=codigo, chat_id=chat_id)
        session.add(student)
    
    # Haciendo commit de los cambios
    session.commit()
    session.close()
    print(f"{n} estudiantes ficticios añadidos.")


insert_fake_students(100)