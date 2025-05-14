-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS "spaces"
AUTHORIZATION postgres;

-- Table: spaces
CREATE TABLE IF NOT EXISTS spaces.spaces (
    id_space SERIAL PRIMARY KEY,
    id_parent_space INTEGER,    -- Reference to the parent space
    space_name TEXT NOT NULL UNIQUE,
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
    projection_name TEXT NOT NULL UNIQUE,
    projection_description TEXT,
    x_pos_in_parent_projection NUMERIC,  -- X coordinate relative to parent projection
    y_pos_in_parent_projection NUMERIC,  -- Y coordinate relative to parent projection
    projection_image BYTEA,
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
    image BYTEA NOT NULL,
    id_parent_space INTEGER NOT NULL,    -- Reference to the parent space
    CONSTRAINT fk_space_image
        FOREIGN KEY (id_parent_space)
        REFERENCES spaces.spaces(id_space)
        ON DELETE CASCADE
);

-- Table: items
CREATE TABLE spaces.items (
    id_item SERIAL PRIMARY KEY,
    item_name TEXT NOT NULL,
    item_description TEXT,
    id_parent_space INTEGER NOT NULL,
    CONSTRAINT fk_item_space
        FOREIGN KEY (id_parent_space)
        REFERENCES spaces.spaces(id_space)
        ON DELETE CASCADE
);


-- Table: items_projections
CREATE TABLE spaces.items_projections (
    id_item_projection SERIAL PRIMARY KEY,
    id_parent_item INTEGER NOT NULL,
    id_parent_projection INTEGER NOT NULL,
    x_pos_in_parent_projection NUMERIC,
    y_pos_in_parent_projection NUMERIC,
    CONSTRAINT fk_item
        FOREIGN KEY (id_parent_item)
        REFERENCES spaces.items(id_item)
        ON DELETE CASCADE,
    CONSTRAINT fk_projection
        FOREIGN KEY (id_parent_projection)
        REFERENCES spaces.projections(id_projection)
        ON DELETE CASCADE,
    CONSTRAINT uq_item_projection UNIQUE (id_parent_item, id_parent_projection)
);
