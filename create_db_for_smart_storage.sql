-- Создание схемы
CREATE SCHEMA IF NOT EXISTS "spaces"
AUTHORIZATION postgres;

-- Table: users
CREATE TABLE IF NOT EXISTS spaces.users (
    id_user SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role VARCHAR(10) NOT NULL DEFAULT 'user'
        CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS spaces.spaces (
    id_space SERIAL PRIMARY KEY,
    id_parent_space INTEGER,    -- Reference to the parent space
    space_name TEXT NOT NULL,
    space_description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_parent_space
        FOREIGN KEY (id_parent_space)
        REFERENCES spaces.spaces(id_space)
        ON DELETE SET NULL
);

-- Table: things
CREATE TABLE IF NOT EXISTS spaces.things (
    id_thing SERIAL PRIMARY KEY,
    thing_name TEXT NOT NULL,
    thing_description TEXT,
    id_parent_space INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_parent_space
        FOREIGN KEY (id_parent_space)
        REFERENCES spaces.spaces(id_space)
        ON DELETE CASCADE
);

-- Table: projections
CREATE TABLE IF NOT EXISTS spaces.projections (
    id_projection SERIAL PRIMARY KEY,
    id_parent_projection INTEGER,
    id_parent_space INTEGER,
    id_parent_thing INTEGER,
    projection_name TEXT NOT NULL,
    projection_description TEXT,
    x_pos_in_parent_projection NUMERIC,
    y_pos_in_parent_projection NUMERIC,
    z_pos NUMERIC,
    projection_image BYTEA,
    projection_width NUMERIC,
    projection_height NUMERIC,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
    id_parent_space INTEGER,
    id_parent_thing INTEGER,
    image BYTEA NOT NULL,
    image_name TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
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
    id_user INTEGER NOT NULL REFERENCES spaces.users(id_user) ON DELETE CASCADE,
    id_space INTEGER NOT NULL REFERENCES spaces.spaces(id_space) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL CHECK (role IN ('editor', 'viewer')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_user, id_space)
);