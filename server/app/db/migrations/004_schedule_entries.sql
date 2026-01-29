-- Prison Roll Call Database Schema
-- Version: 004 Schedule Entries
-- Created: January 2025
-- Description: Adds schedule_entries table for prisoner timetables/regimes

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Schedule entries (prisoner timetables)
CREATE TABLE IF NOT EXISTS schedule_entries (
    id TEXT PRIMARY KEY,
    inmate_id TEXT NOT NULL REFERENCES inmates(id) ON DELETE CASCADE,
    location_id TEXT NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    day_of_week INTEGER NOT NULL CHECK(day_of_week >= 0 AND day_of_week <= 6),
    start_time TEXT NOT NULL,  -- Format: "HH:MM"
    end_time TEXT NOT NULL,    -- Format: "HH:MM"
    activity_type TEXT NOT NULL,
    is_recurring INTEGER DEFAULT 1,
    effective_date TEXT,  -- For one-off appointments (ISO 8601 date)
    source TEXT DEFAULT 'manual',  -- 'manual', 'sync', 'generated'
    source_id TEXT,  -- External system ID for sync
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_schedule_inmate ON schedule_entries(inmate_id);
CREATE INDEX IF NOT EXISTS idx_schedule_location ON schedule_entries(location_id);
CREATE INDEX IF NOT EXISTS idx_schedule_day_time ON schedule_entries(day_of_week, start_time);
CREATE INDEX IF NOT EXISTS idx_schedule_source ON schedule_entries(source, source_id);
CREATE INDEX IF NOT EXISTS idx_schedule_activity ON schedule_entries(activity_type);
CREATE INDEX IF NOT EXISTS idx_schedule_effective ON schedule_entries(effective_date);
