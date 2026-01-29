-- Prison Roll Call Database Schema
-- Version: 006 Audit Enhancements
-- Created: January 2025

-- Add tracking columns to audit_log
ALTER TABLE audit_log ADD COLUMN ip_address TEXT;
ALTER TABLE audit_log ADD COLUMN user_agent TEXT;

-- Create index for user queries (officer_id is the user_id)
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(officer_id);

-- Create compound index for entity lookups
CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_log(entity_type, entity_id);
