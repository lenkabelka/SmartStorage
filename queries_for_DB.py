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
def insert_space(space_name, space_description):
    query = """
        INSERT INTO spaces.spaces (id_parent_space, space_name, space_description)
        VALUES (%s, %s, %s)
        RETURNING id_space;
    """
    values = (None, space_name, space_description)

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
def insert_projection_of_space(id_parent_space, projection_name, projection_description, projection_image):
    query = """
            INSERT INTO spaces.projections (id_parent_projection, id_parent_space, projection_name, 
            projection_description, x_pos_in_parent_projection, y_pos_in_parent_projection, projection_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_projection;
        """
    image_bytes = utils.pixmap_to_bytes(projection_image.pixmap())
    values = (None, id_parent_space, projection_name, projection_description, None, None, psycopg2.Binary(image_bytes))

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
def insert_projection_of_subspace(id_parent_projection, id_parent_space, projection_name, projection_description, projection_image):
    query = """
            INSERT INTO spaces.projections (id_parent_projection, id_parent_space, projection_name, 
            projection_description, x_pos_in_parent_projection, y_pos_in_parent_projection, projection_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_projection;
        """
    image_bytes = utils.pixmap_to_bytes(projection_image.pixmap())
    values = (id_parent_projection, id_parent_space, projection_name, projection_description, None, None, psycopg2.Binary(image_bytes))

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



def insert_image(image, parent_id):
    query = """
        INSERT INTO spaces.images (image, id_projection)
        VALUES (%s, %s)
    """
    values = (image, parent_id)

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