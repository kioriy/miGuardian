# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2024-05-04 22:54:49
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2024-06-02 22:40:16
from util.JsonFormatter import JsonFormatter
import logging

def load_handler_logging():
    """
    Crea el encabezado del archivo app.log
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('app.log', 'w')
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)