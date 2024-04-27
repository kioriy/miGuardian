# -*- coding: utf-8 -*-
# @Author: Hugo Rafael Hernández Llamas
# @Date:   2024-04-22 19:12:46
# @Last Modified by:   Hugo Rafael Hernández Llamas
# @Last Modified time: 2024-04-25 22:33:16
from enum import Enum

class ESettings(Enum):
    no_check_in = "no_chek_in"
    update_check_in = "update_check_in"
    chat_id_admin = "chat_id_admin"
    clave = "clave"
    first_load = "first_load"
    num_row_last_register = "num_row_last_register"
    schedule = "schedule"
    school_name = "school_name"
    screen_status = "screen_status"
    spreadsheet_name_breakfast = "spreadsheet_name_breakfast"
    status_update_db = "status_update_db"
    type_display_command = "type_display_command"