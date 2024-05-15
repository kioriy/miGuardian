# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2024-05-04 22:54:49
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2024-05-04 22:58:07
from util.JsonFormatter import JsonFormatter
import logging

def load_handler_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler('app.log', 'w')
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)