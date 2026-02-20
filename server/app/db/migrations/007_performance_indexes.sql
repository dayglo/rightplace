-- Prison Roll Call Database Schema
-- Version: 007 Performance Indexes
-- Created: February 2025
-- Purpose: Add missing indexes to optimize treemap query performance

-- Add parent_id index for fast hierarchy traversal
-- Critical for _build_location_subtree which queries children by parent_id (4,912 times!)
CREATE INDEX IF NOT EXISTS idx_locations_parent_id ON locations(parent_id);

-- Add location_id index for verification lookups
-- Used in nested loops to find verifications by location
CREATE INDEX IF NOT EXISTS idx_verifications_location ON verifications(location_id);

-- Add composite index for optimal verification lookups
-- Covers the common query pattern: WHERE roll_call_id = ? AND location_id = ? AND inmate_id = ?
CREATE INDEX IF NOT EXISTS idx_verifications_rollcall_location_inmate
ON verifications(roll_call_id, location_id, inmate_id);
