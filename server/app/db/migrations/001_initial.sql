-- Prison Roll Call Database Schema
-- Version: 001 Initial Schema
-- Created: January 2025

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Inmates table
CREATE TABLE IF NOT EXISTS inmates (
    id TEXT PRIMARY KEY,
    inmate_number TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    cell_block TEXT NOT NULL,
    cell_number TEXT NOT NULL,
    photo_uri TEXT,
    is_enrolled INTEGER DEFAULT 0,
    enrolled_at TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_inmates_block ON inmates(cell_block);
CREATE INDEX IF NOT EXISTS idx_inmates_enrolled ON inmates(is_enrolled);
CREATE INDEX IF NOT EXISTS idx_inmates_number ON inmates(inmate_number);

-- Face embeddings (separate table for security)
CREATE TABLE IF NOT EXISTS embeddings (
    inmate_id TEXT PRIMARY KEY REFERENCES inmates(id),
    embedding BLOB NOT NULL,
    model_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- Locations
CREATE TABLE IF NOT EXISTS locations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    parent_id TEXT REFERENCES locations(id),
    capacity INTEGER DEFAULT 1,
    floor INTEGER DEFAULT 0,
    building TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_locations_type ON locations(type);
CREATE INDEX IF NOT EXISTS idx_locations_building ON locations(building);

-- Roll calls
CREATE TABLE IF NOT EXISTS roll_calls (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    cancelled_reason TEXT,
    route TEXT NOT NULL,
    officer_id TEXT NOT NULL,
    notes TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_rollcalls_status ON roll_calls(status);
CREATE INDEX IF NOT EXISTS idx_rollcalls_scheduled ON roll_calls(scheduled_at);

-- Verifications
CREATE TABLE IF NOT EXISTS verifications (
    id TEXT PRIMARY KEY,
    roll_call_id TEXT NOT NULL REFERENCES roll_calls(id),
    inmate_id TEXT NOT NULL REFERENCES inmates(id),
    location_id TEXT NOT NULL REFERENCES locations(id),
    status TEXT NOT NULL,
    confidence REAL NOT NULL,
    photo_uri TEXT,
    timestamp TEXT NOT NULL,
    is_manual_override INTEGER DEFAULT 0,
    manual_override_reason TEXT,
    notes TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_verifications_rollcall ON verifications(roll_call_id);
CREATE INDEX IF NOT EXISTS idx_verifications_inmate ON verifications(inmate_id);
CREATE INDEX IF NOT EXISTS idx_verifications_timestamp ON verifications(timestamp);

-- Audit log
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    officer_id TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    details TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);

-- Policy
CREATE TABLE IF NOT EXISTS policy (
    id TEXT PRIMARY KEY DEFAULT 'default',
    verification_threshold REAL DEFAULT 0.75,
    enrollment_quality_threshold REAL DEFAULT 0.80,
    auto_accept_threshold REAL DEFAULT 0.92,
    manual_review_threshold REAL DEFAULT 0.60,
    low_light_adjustment REAL DEFAULT -0.05,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL
);

-- Insert default policy if it doesn't exist
INSERT OR IGNORE INTO policy (id, verification_threshold, enrollment_quality_threshold, 
                               auto_accept_threshold, manual_review_threshold, 
                               low_light_adjustment, updated_at, updated_by)
VALUES ('default', 0.75, 0.80, 0.92, 0.60, -0.05, datetime('now'), 'system');
