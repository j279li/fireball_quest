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

-- 4) Characters (depends on users, game_systems, campaigns)
CREATE TABLE characters (
  id              BIGSERIAL PRIMARY KEY,

  user_id         BIGINT NOT NULL REFERENCES users(id),
  game_system_id  INT    NOT NULL REFERENCES game_systems(id),

  -- optional "home" campaign; character can exist without a campaign
  campaign_id     BIGINT REFERENCES campaigns(id),


