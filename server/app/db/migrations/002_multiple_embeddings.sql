-- Migration 002: Support Multiple Embeddings Per Inmate
-- This migration allows storing multiple face embeddings per inmate
-- to improve recognition accuracy through averaging

-- Drop the old embeddings table
DROP TABLE IF EXISTS embeddings;

-- Create new embeddings table with support for multiple per inmate
CREATE TABLE embeddings (
    id TEXT PRIMARY KEY,
    inmate_id TEXT NOT NULL REFERENCES inmates(id),
    embedding BLOB NOT NULL,
    photo_path TEXT,
    quality REAL NOT NULL DEFAULT 1.0,
    model_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    
    -- Index for efficient lookup by inmate
    FOREIGN KEY (inmate_id) REFERENCES inmates(id) ON DELETE CASCADE
);

CREATE INDEX idx_embeddings_inmate ON embeddings(inmate_id);
CREATE INDEX idx_embeddings_created ON embeddings(created_at);
