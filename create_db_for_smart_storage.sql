-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS "spaces"
AUTHORIZATION postgres;

-- Table: spaces
CREATE TABLE IF NOT EXISTS spaces.spaces (
    id_space SERIAL PRIMARY KEY,
    id_parent_space INTEGER,    -- Reference to the parent space
    space_name TEXT NOT NULL,
    space_description TEXT,
    CONSTRAINT fk_parent_space
        FOREIGN KEY (id_parent_space)
        REFERENCES spaces.spaces(id_space)
        ON DELETE SET NULL
);

-- Table: things
CREATE TABLE spaces.things (
    id_thing SERIAL PRIMARY KEY,
    thing_name TEXT NOT NULL,
    thing_description TEXT,
    id_parent_space INTEGER NOT NULL,
    CONSTRAINT fk_parent_space
        FOREIGN KEY (id_parent_space)
        REFERENCES spaces.spaces(id_space)
        ON DELETE CASCADE
);

-- Table: projections
CREATE TABLE IF NOT EXISTS spaces.projections (
    id_projection SERIAL PRIMARY KEY,
    id_parent_projection INTEGER,        -- Optional reference to another projection
    id_parent_space INTEGER,             -- Reference to the parent space
    id_parent_thing INTEGER,             -- Reference to the parent thing
    projection_name TEXT NOT NULL,
    projection_description TEXT,
    x_pos_in_parent_projection NUMERIC,  -- X coordinate relative to parent projection
    y_pos_in_parent_projection NUMERIC,  -- Y coordinate relative to parent projection
    z_pos NUMERIC, -- координата для правильного восстановления сцены
    projection_image BYTEA,
    projection_width NUMERIC,
    projection_height NUMERIC,
    CONSTRAINT fk_parent_projection
        FOREIGN KEY (id_parent_projection)
        REFERENCES spaces.projections(id_projection)
        ON DELETE SET NULL,
    CONSTRAINT fk_space_projection
        FOREIGN KEY (id_parent_space)
        REFERENCES spaces.spaces(id_space)
        ON DELETE CASCADE,
    CONSTRAINT fk_parent_thing
        FOREIGN KEY (id_parent_thing)
        REFERENCES spaces.things(id_thing)
        ON DELETE CASCADE,
    CONSTRAINT parent_space_or_thing_check CHECK (
        (id_parent_space IS NOT NULL AND id_parent_thing IS NULL)
        OR
        (id_parent_space IS NULL AND id_parent_thing IS NOT NULL)
    )
);

-- Table: images
CREATE TABLE IF NOT EXISTS spaces.images (
    id_image SERIAL PRIMARY KEY,
    id_parent_space INTEGER,    -- Ссылка на пространство (nullable)
    id_parent_thing INTEGER,    -- Ссылка на вещь (nullable)
    image BYTEA NOT NULL,
    image_name TEXT,
    CONSTRAINT fk_space_image
        FOREIGN KEY (id_parent_space)
        REFERENCES spaces.spaces(id_space)
        ON DELETE CASCADE,
    CONSTRAINT fk_thing_image
        FOREIGN KEY (id_parent_thing)
        REFERENCES spaces.things(id_thing)
        ON DELETE CASCADE,
    CONSTRAINT parent_space_or_thing_check CHECK (
        (id_parent_space IS NOT NULL AND id_parent_thing IS NULL)
        OR
        (id_parent_space IS NULL AND id_parent_thing IS NOT NULL)
    )
);