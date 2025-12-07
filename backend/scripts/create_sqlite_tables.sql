-- SQLite-compatible table creation for badges, user_badges, and verification_tokens
-- Run this if using SQLite instead of PostgreSQL

-- Add columns to users table (if they don't exist)
-- Note: SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS directly
-- You may need to check if columns exist first

-- Add email_verified column
-- ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0;
-- Add profile_completed column  
-- ALTER TABLE users ADD COLUMN profile_completed INTEGER DEFAULT 0;
-- Add bio column
-- ALTER TABLE users ADD COLUMN bio TEXT;
-- Add timezone column
-- ALTER TABLE users ADD COLUMN timezone VARCHAR(50);

-- Create badges table
CREATE TABLE IF NOT EXISTS badges (
    id TEXT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(100),
    requirement_type VARCHAR(50) NOT NULL,
    requirement_value INTEGER NOT NULL DEFAULT 1,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active VARCHAR(1) NOT NULL DEFAULT '1',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_badge_slug ON badges(slug);
CREATE INDEX IF NOT EXISTS idx_badge_requirement_type ON badges(requirement_type);
CREATE INDEX IF NOT EXISTS idx_badge_display_order ON badges(display_order);

-- Create user_badges table
CREATE TABLE IF NOT EXISTS user_badges (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    badge_id TEXT NOT NULL,
    unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (badge_id) REFERENCES badges(id) ON DELETE CASCADE,
    UNIQUE(user_id, badge_id)
);

CREATE INDEX IF NOT EXISTS idx_user_badge_user ON user_badges(user_id);
CREATE INDEX IF NOT EXISTS idx_user_badge_badge ON user_badges(badge_id);
CREATE INDEX IF NOT EXISTS idx_user_badge_unlocked ON user_badges(unlocked_at);

-- Create verification_tokens table
CREATE TABLE IF NOT EXISTS verification_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    token_hash VARCHAR(64) NOT NULL,
    token_type VARCHAR(20) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_verification_token_hash ON verification_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_verification_token_expires ON verification_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_verification_token_user_type ON verification_tokens(user_id, token_type);
CREATE INDEX IF NOT EXISTS idx_verification_token_type ON verification_tokens(token_type);

