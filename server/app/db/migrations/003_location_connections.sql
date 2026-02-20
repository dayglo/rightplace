-- Migration 003: Add location connections table for pathfinding
-- This enables graph-based walking path calculation between locations

-- Add optional coordinates to locations table for map visualization
-- Note: ALTER TABLE ADD COLUMN is not idempotent in SQLite
-- This migration should only be run once on a fresh database
ALTER TABLE locations ADD COLUMN x_coord REAL;
ALTER TABLE locations ADD COLUMN y_coord REAL;

-- Create location_connections table
CREATE TABLE IF NOT EXISTS location_connections (
    id TEXT PRIMARY KEY,
    from_location_id TEXT NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    to_location_id TEXT NOT NULL REFERENCES locations(id) ON DELETE CASCADE,
    distance_meters INTEGER DEFAULT 10,
    travel_time_seconds INTEGER DEFAULT 15,
    connection_type TEXT DEFAULT 'corridor',  -- corridor, stairwell, walkway, gate
    is_bidirectional BOOLEAN DEFAULT TRUE,
    requires_escort BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for efficient pathfinding queries
CREATE INDEX IF NOT EXISTS idx_location_connections_from ON location_connections(from_location_id);
CREATE INDEX IF NOT EXISTS idx_location_connections_to ON location_connections(to_location_id);
CREATE INDEX IF NOT EXISTS idx_location_connections_bidirectional ON location_connections(is_bidirectional);

-- Create trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS update_location_connections_timestamp
AFTER UPDATE ON location_connections
FOR EACH ROW
BEGIN
    UPDATE location_connections SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
