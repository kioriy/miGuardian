# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2024-03-14 20:55:23
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2024-03-15 00:47:26

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = "sqlite:///./miguardian.db"
engine = create_engine(DATABASE_URL)

# Intenta agregar la columna nueva
try:
    with engine.connect() as conn:
        conn.execute("ALTER TABLE student ADD COLUMN turno VARCHAR;")
        print("Columna 'turno' añadida exitosamente.")
except SQLAlchemyError as e:
    print(f"Error al añadir la columna 'turno': {e}")