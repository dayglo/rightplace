-- Migration 005: Add home_cell_id to inmates
-- Links each prisoner to their assigned cell (location)
-- Created: January 2026

-- Add home_cell_id column
ALTER TABLE inmates ADD COLUMN home_cell_id TEXT REFERENCES locations(id);

-- Index for efficient lookups (who lives in this cell?)
CREATE INDEX IF NOT EXISTS idx_inmates_home_cell ON inmates(home_cell_id);
