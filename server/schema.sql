-- 1) Users (no dependencies)
CREATE TABLE users (
  id           BIGSERIAL PRIMARY KEY,
  email        TEXT NOT NULL UNIQUE,
  username     TEXT NOT NULL UNIQUE,
  display_name TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2) Game systems (no dependencies)
CREATE TABLE game_systems (
  id   SERIAL PRIMARY KEY,
  key  TEXT UNIQUE NOT NULL,  -- e.g. 'dnd5e', 'pathfinder2e'
  name TEXT NOT NULL          -- e.g. 'D&D 5th Edition'
);

-- 3) Campaigns (depends on users, game_systems)
CREATE TABLE campaigns (
  id             BIGSERIAL PRIMARY KEY,
  owner_user_id  BIGINT NOT NULL REFERENCES users(id),
  game_system_id INT    NOT NULL REFERENCES game_systems(id),
  description TEXT NOT NULL DEFAULT '',
  name           TEXT NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 4) Sessions (depends on campaigns)
CREATE TABLE sessions (
  id           BIGSERIAL PRIMARY KEY,
  campaign_id  BIGINT NOT NULL REFERENCES campaigns(id),
  description TEXT NOT NULL DEFAULT '',
  name         TEXT NOT NULL,
  scheduled_at TIMESTAMPTZ,
  started_at   TIMESTAMPTZ,
  ended_at     TIMESTAMPTZ,

  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5) Characters (depends on users, game_systems, campaigns)
CREATE TABLE characters (
  id              BIGSERIAL PRIMARY KEY,

  user_id         BIGINT NOT NULL REFERENCES users(id),
  game_system_id  INT    NOT NULL REFERENCES game_systems(id),

  -- optional "home" campaign; character can exist without a campaign
  campaign_id     BIGINT REFERENCES campaigns(id),

  name            TEXT NOT NULL,
  class_name      TEXT,
  race            TEXT,
  level           INT,

  stats           JSONB NOT NULL DEFAULT '{}'::jsonb,

  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- prevent same user having two chars with same name for the same system
  UNIQUE (user_id, game_system_id, name)
);

-- 6) Campaign memberships (depends on campaigns, users)
CREATE TABLE campaign_memberships (
  id           BIGSERIAL PRIMARY KEY,
  campaign_id  BIGINT NOT NULL REFERENCES campaigns(id),
  user_id      BIGINT NOT NULL REFERENCES users(id),

  role         TEXT NOT NULL,  -- 'DM', 'PLAYER'
  joined_at    TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (campaign_id, user_id)
);

-- 7) Session characters (depends on sessions, users, characters)
CREATE TABLE session_characters (
  id           BIGSERIAL PRIMARY KEY,
  session_id   BIGINT NOT NULL REFERENCES sessions(id),
  user_id      BIGINT NOT NULL REFERENCES users(id),
  character_id BIGINT NOT NULL REFERENCES characters(id),

  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE (session_id, user_id),
  UNIQUE (session_id, character_id)
);

-- 8) Messages (depends on sessions, users, characters)
CREATE TABLE messages (
  id           BIGSERIAL PRIMARY KEY,
  session_id   BIGINT NOT NULL REFERENCES sessions(id),
  user_id      BIGINT NOT NULL REFERENCES users(id),
  character_id BIGINT REFERENCES characters(id),
  msg_type     TEXT NOT NULL DEFAULT 'chat',  -- 'CHAT', 'ROLL', 'NOTE', etc.
  content      TEXT NOT NULL,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

  metadata     JSONB NOT NULL DEFAULT '{}'::jsonb
);

-- 9) Notes (depends on users, campaigns, sessions)
CREATE TABLE notes (
  id           BIGSERIAL PRIMARY KEY,
  user_id      BIGINT NOT NULL REFERENCES users(id),
  campaign_id  BIGINT REFERENCES campaigns(id),
  session_id   BIGINT REFERENCES sessions(id),

  title        TEXT,
  content      TEXT NOT NULL,

  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 10) Local auth credentials (depends on users)
CREATE TABLE auth_local_credentials (
  user_id             BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  password_hash       TEXT NOT NULL,
  password_updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
