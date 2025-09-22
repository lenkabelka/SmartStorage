-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS "spaces"
AUTHORIZATION postgres;

-- Table: users
CREATE TABLE IF NOT EXISTS spaces.users (
    id_user SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(10) NOT NULL CHECK (role IN ('admin', 'creator', 'viewer'))
);

-- Table: spaces
CREATE TABLE IF NOT EXISTS spaces.spaces (
    id_space SERIAL PRIMARY KEY,
    id_parent_space INTEGER,                -- Reference to the parent space
    creator_id INTEGER,                      -- Reference to the user who created the space
    space_name TEXT NOT NULL,
    space_description TEXT,
    CONSTRAINT fk_parent_space
        FOREIGN KEY (id_parent_space)
        REFERENCES spaces.spaces(id_space)
        ON DELETE SET NULL,
    CONSTRAINT fk_creator
        FOREIGN KEY (creator_id)
        REFERENCES spaces.users(id_user)
        ON DELETE SET NULL
);

-- Table: things
CREATE TABLE IF NOT EXISTS spaces.things (
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
    z_pos NUMERIC,                       -- Z coordinate for scene restoration
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
    id_parent_space INTEGER,    -- Reference to a space (nullable)
    id_parent_thing INTEGER,    -- Reference to a thing (nullable)
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

-- Table: user_access
CREATE TABLE IF NOT EXISTS spaces.user_access (
    id_user INTEGER NOT NULL,
    id_space INTEGER NOT NULL,
    can_edit BOOLEAN DEFAULT FALSE,
    can_view BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (id_user, id_space),
    CONSTRAINT fk_user_access_user
        FOREIGN KEY (id_user)
        REFERENCES spaces.users(id_user)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_access_space
        FOREIGN KEY (id_space)
        REFERENCES spaces.spaces(id_space)
        ON DELETE CASCADE
);