-- PrepTrack — Priority 1/2/3 feature additions
-- Run against your existing database:
--   mysql -u root -p preptrack < feature_schema.sql

USE preptrack;

-- Weekly goal + interview countdown live on the user record
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS weekly_goal INT NOT NULL DEFAULT 20,
    ADD COLUMN IF NOT EXISTS interview_date DATE NULL;
