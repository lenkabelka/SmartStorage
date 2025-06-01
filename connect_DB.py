import json
import psycopg2


def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)


def db_connect(config):
    return psycopg2.connect(**config)


""" В рамках одного пространства развертки имеют уникальное имя.
 Нужно найти все развертки пространства, потом найти для каждой развертки все её подразвертки (подпространства), 
 у которых она родительская развертка (id_parent_projection).
 При этом в MainWidget хранить словарь {развертка_1: [[подразвертка_1, x, y], [подразвертка_2, x, y]], 
                                        развертка_2: [[подразвертка_1, x, y], [подразвертка_2, x, y]] ... } """