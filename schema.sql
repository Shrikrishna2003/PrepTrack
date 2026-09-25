-- PrepTrack database schema
-- Run: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS preptrack CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE preptrack;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    weekly_goal INT NOT NULL DEFAULT 20,
    interview_date DATE NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

INSERT IGNORE INTO companies (name) VALUES ('TCS'), ('Infosys'), ('Atidan'), ('Other');

CREATE TABLE IF NOT EXISTS problems (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    company_id INT NOT NULL,
    topic VARCHAR(100),
    difficulty ENUM('Easy', 'Medium', 'Hard') NOT NULL DEFAULT 'Medium',
    platform VARCHAR(100),
    problem_link VARCHAR(500),
    status ENUM('Solved', 'Attempted', 'Revisit') NOT NULL DEFAULT 'Solved',
    solved_date DATE NOT NULL,
    time_taken_min INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    problem_id INT,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE SET NULL
);

CREATE INDEX idx_problems_user_date ON problems(user_id, solved_date);
CREATE INDEX idx_problems_user_company ON problems(user_id, company_id);
CREATE INDEX idx_notes_user ON notes(user_id);
