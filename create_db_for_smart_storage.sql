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

-- Table: projections
CREATE TABLE IF NOT EXISTS spaces.projections (
    id_projection SERIAL PRIMARY KEY,
    id_parent_projection INTEGER,        -- Optional reference to another projection
    id_parent_space INTEGER NOT NULL,    -- Reference to the parent space
    projection_name TEXT NOT NULL,
    projection_description TEXT,
    x_pos_in_parent_projection NUMERIC,  -- X coordinate relative to parent projection
    y_pos_in_parent_projection NUMERIC,  -- Y coordinate relative to parent projection
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
        ON DELETE CASCADE
);

-- Table: images
CREATE TABLE IF NOT EXISTS spaces.images (
    id_image SERIAL PRIMARY KEY,
    id_parent_space INTEGER NOT NULL,    -- Reference to the parent space
    image BYTEA NOT NULL,
    image_name TEXT,
    CONSTRAINT fk_space_image
        FOREIGN KEY (id_parent_space)
        REFERENCES spaces.spaces(id_space)
        ON DELETE CASCADE
);

-- Table: things
CREATE TABLE spaces.things (
    id_thing SERIAL PRIMARY KEY,
    thing_name TEXT NOT NULL,
    thing_description TEXT,
    thing_image BYTEA,
    id_parent_space INTEGER NOT NULL,
    id_parent_projection INTEGER,
    x_pos_in_parent_projection NUMERIC,  -- X coordinate relative to parent projection
    y_pos_in_parent_projection NUMERIC,  -- Y coordinate relative to parent projection
    thing_projection_image BYTEA,
    thing_projection_width NUMERIC,
    thing_projection_height NUMERIC,
    CONSTRAINT fk_parent_space
        FOREIGN KEY (id_parent_space)
        REFERENCES spaces.spaces(id_space)
        ON DELETE CASCADE,
    CONSTRAINT fk_parent_projection
        FOREIGN KEY (id_parent_projection)
        REFERENCES spaces.projections(id_projection)
        ON DELETE CASCADE
);