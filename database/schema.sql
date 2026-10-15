-- ============================================================
-- Career Assistance System - Database Schema
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    raw_text TEXT,
    extracted_skills TEXT,        -- JSON array
    extracted_education TEXT,     -- JSON array
    extracted_experience TEXT,    -- JSON array
    extracted_projects TEXT,      -- JSON array
    extracted_certifications TEXT,-- JSON array
    contact_info TEXT,            -- JSON object
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS job_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT,
    required_skills TEXT,         -- JSON array
    description TEXT,
    avg_salary TEXT,
    experience_level TEXT
);

CREATE TABLE IF NOT EXISTS job_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    resume_id INTEGER NOT NULL,
    job_role_id INTEGER NOT NULL,
    match_percentage REAL,
    missing_skills TEXT,          -- JSON array
    recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (resume_id) REFERENCES resumes(id),
    FOREIGN KEY (job_role_id) REFERENCES job_roles(id)
);

CREATE TABLE IF NOT EXISTS interview_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    job_role TEXT NOT NULL,
    questions TEXT,               -- JSON array
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    overall_score REAL,
    status TEXT DEFAULT 'in_progress',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS interview_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    score REAL,
    feedback TEXT,
    relevance_score REAL,
    clarity_score REAL,
    technical_score REAL,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES interview_sessions(id)
);

CREATE TABLE IF NOT EXISTS skill_gap_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    resume_id INTEGER NOT NULL,
    target_job_role TEXT NOT NULL,
    user_skills TEXT,             -- JSON array
    required_skills TEXT,         -- JSON array
    missing_skills TEXT,          -- JSON array
    learning_roadmap TEXT,        -- JSON object
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (resume_id) REFERENCES resumes(id)
);
