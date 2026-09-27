-- PrepTrack Feature Additions
-- Run on Railway MySQL

USE railway;

ALTER TABLE users
    ADD COLUMN weekly_goal INT NOT NULL DEFAULT 20,
    ADD COLUMN daily_goal INT NOT NULL DEFAULT 3;