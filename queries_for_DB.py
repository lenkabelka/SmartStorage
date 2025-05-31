import json
import psycopg2
import image_utils as utils


def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)


def db_connect(config):
    return psycopg2.connect(**config)


# id_space
# id_parent_space
# space_name
# space_description
def insert_space(space_name, space_description, id_space=None):
    insert_query = """
        INSERT INTO spaces.spaces (id_parent_space, space_name, space_description)
        VALUES (%s, %s, %s)
        RETURNING id_space;
    """
    insert_values = (None, space_name, space_description)

    conn = None
    try:
        config = load_config()
        conn = db_connect(config)
        with conn:
            with conn.cursor() as cur:
                cur.execute(insert_query, insert_values)
                print("saved_DB")
                inserted_id = cur.fetchone()[0]
                return inserted_id
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("Error by insert:", e)
        return None
    finally:
        if conn:
            conn.close()


# id_space
# id_parent_space
# space_name
# space_description
def update_space(id_space, space_name, space_description):

    update_query = """ 
        UPDATE spaces.spaces
        SET space_name = %s, space_description = %s
        WHERE id_space = %s
    """

    update_values = (space_name, space_description, id_space)

    conn = None
    try:
        config = load_config()
        conn = db_connect(config)
        with conn:
            with conn.cursor() as cur:
                cur.execute(update_query, update_values)
                print("saved_DB")
                inserted_id = cur.fetchone()[0]
                return inserted_id
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("Error by insert:", e)
        return None
    finally:
        if conn:
            conn.close()


# id_space
# id_parent_space
# space_name
# space_description
def delete_space(id_space):

    delete_query = """
        DELETE FROM spaces.spaces
        WHERE id_space = %s
    """

    delete_values = (id_space,)

    conn = None
    try:
        config = load_config()
        conn = db_connect(config)
        with conn:
            with conn.cursor() as cur:
                cur.execute(delete_query, delete_values)
                print("saved_DB")
                inserted_id = cur.fetchone()[0]
                return inserted_id
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("Error by insert:", e)
        return None
    finally:
        if conn:
            conn.close()


# id_projection
# id_parent_projection
# id_parent_space
# projection_name
# projection_description
# x_pos_in_parent_projection
# y_pos_in_parent_projection
# projection_image
# projection_width
# projection_height
def insert_projection_of_space(id_parent_space,
                               projection_name,
                               projection_description,
                               projection_image,
                               projection_width,
                               projection_height):

    query = """
            INSERT INTO spaces.projections (
            id_parent_projection, 
            id_parent_space, 
            projection_name, 
            projection_description, 
            x_pos_in_parent_projection, 
            y_pos_in_parent_projection, 
            projection_image, 
            projection_width, 
            projection_height
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_projection;
        """

    image_bytes = utils.pixmap_to_bytes(projection_image)
    values = (None, id_parent_space, projection_name, projection_description, None, None, psycopg2.Binary(image_bytes), projection_width, projection_height)

    conn = None
    try:
        config = load_config()
        conn = db_connect(config)
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                print("saved_DB")
                inserted_id = cur.fetchone()[0]
                return inserted_id
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("Error by insert:", e)
        return None
    finally:
        if conn:
            conn.close()


# id_space
# id_parent_space
# space_name
# space_description
def insert_subspace(id_parent_space, space_name, space_description):
    query = """
        INSERT INTO spaces.spaces (id_parent_space, space_name, space_description)
        VALUES (%s, %s, %s)
        RETURNING id_space;
    """
    values = (id_parent_space, space_name, space_description)

    conn = None
    try:
        config = load_config()
        conn = db_connect(config)
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                print("saved_DB")
                inserted_id = cur.fetchone()[0]
                return inserted_id
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("Error by insert:", e)
        return None
    finally:
        if conn:
            conn.close()


# id_projection
# id_parent_projection
# id_parent_space
# projection_name
# projection_description
# x_pos_in_parent_projection
# y_pos_in_parent_projection
# projection_image
# projection_width
# projection_height
def insert_projection_of_subspace(id_parent_projection,
                                  id_parent_space,
                                  projection_name,
                                  projection_description,
                                  x_pos_in_parent_projection,
                                  y_pos_in_parent_projection,
                                  projection_image,
                                  projection_width,
                                  projection_height):
    query = """
            INSERT INTO spaces.projections (
            id_parent_projection, 
            id_parent_space, 
            projection_name, 
            projection_description, 
            x_pos_in_parent_projection, 
            y_pos_in_parent_projection, 
            projection_image,
            projection_width,
            projection_height
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_projection;
        """
    image_bytes = utils.pixmap_to_bytes(projection_image)
    values = (id_parent_projection,
              id_parent_space,
              projection_name,
              projection_description,
              x_pos_in_parent_projection,
              y_pos_in_parent_projection,
              psycopg2.Binary(image_bytes),
              projection_width,
              projection_height)

    conn = None
    try:
        config = load_config()
        conn = db_connect(config)
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                print("saved_DB")
                inserted_id = cur.fetchone()[0]
                return inserted_id
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("Error by insert:", e)
        return None
    finally:
        if conn:
            conn.close()



def insert_image(id_parent_space, image, image_name=None):

    query = """
        INSERT INTO spaces.images (id_parent_space, image, image_name)
        VALUES (%s, %s, %s)
    """
    values = (id_parent_space, image, image_name)

    conn = None
    try:
        config = load_config()
        conn = db_connect(config)
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, values)
                print("saved_DB")
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("Error by insert:", e)
    finally:
        if conn:
            conn.close()


def get_all_space_names():
    query = "SELECT space_name FROM spaces.spaces"

    conn = None
    try:
        config = load_config()
        conn = db_connect(config)
        with conn:
            with conn.cursor() as cur:
                cur.execute(query)
                results = cur.fetchall()
                # Список строк: [('Name1',), ('Name2',)] → можно преобразовать в список имен
                return [row[0] for row in results]
    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        print("Error by select:", e)
        return []
    finally:
        if conn:
            conn.close()



""" В рамках одного пространства развертки имеют уникальное имя.
 Нужно найти все развертки пространства, потом найти для каждой развертки все её подразвертки (подпространства), 
 у которых она родительская развертка (id_parent_projection).
 При этом в MainWidget хранить словарь {развертка_1: [[подразвертка_1, x, y], [подразвертка_2, x, y]], 
                                        развертка_2: [[подразвертка_1, x, y], [подразвертка_2, x, y]] ... } """