# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2024-05-04 21:08:44
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2024-05-14 22:12:51
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        """_summary_
        Metodo que extiende de logging para poder dar formato al archivo log,
        devuelve un diccionario serilazado en json, para facilitar su procesamiento.
        Args:
            record (_type_): logging.Formatter
        Returns:
            _type_: _description_
        """
        log_record = {
            "time": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage()
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)