import json
import psycopg2
from typing import List
from PyQt6.QtWidgets import QMessageBox
#import space


def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)


def db_connect(config):
    return psycopg2.connect(**config)


# def load_all_spaces() -> List[space.Space]:
#     query = """
#         SELECT id_space, space_name, space_description, id_parent_space
#         FROM spaces.spaces
#         ORDER BY space_name
#     """
#     conn = None
#     spaces = []
#     try:
#         config = load_config()
#         conn = db_connect(config)
#         with conn:
#             with conn.cursor() as cur:
#                 cur.execute(query)
#                 results = cur.fetchall()
#                 for row in results:
#                     space = space.Space(
#                         name=row[1],
#                         description=row[2],
#                         id_space=row[0],
#                         id_parent_space=row[3]
#                     )
#                     spaces.append(space)
#     except psycopg2.Error as e:
#         QMessageBox.critical(None, "Ошибка при загрузке пространств", str(e))
#     finally:
#         if conn:
#             conn.close()
#     return spaces
#
#
# l = load_all_spaces()
# print(l)


""" В рамках одного пространства развертки имеют уникальное имя.
 Нужно найти все развертки пространства, потом найти для каждой развертки все её подразвертки (подпространства), 
 у которых она родительская развертка (id_parent_projection).
 При этом в MainWidget хранить словарь {развертка_1: [[подразвертка_1, x, y], [подразвертка_2, x, y]], 
                                        развертка_2: [[подразвертка_1, x, y], [подразвертка_2, x, y]] ... } """