-- Migration to add new fields to ADR table
-- Run this SQL script to update the existing ADR table structure

-- Add new columns to the adrs table
ALTER TABLE adrs 
ADD COLUMN status VARCHAR(50) DEFAULT 'proposed' NOT NULL,
ADD COLUMN context TEXT,
ADD COLUMN decision TEXT,
ADD COLUMN consequences TEXT,
ADD COLUMN alternatives TEXT,
ADD COLUMN author VARCHAR(255),
ADD COLUMN tags JSON;

-- Update existing records to have default status
UPDATE adrs SET status = 'proposed' WHERE status IS NULL;

-- Make content nullable for backward compatibility
ALTER TABLE adrs MODIFY COLUMN content TEXT NULL;

-- Add index on status for better query performance
CREATE INDEX idx_adrs_status ON adrs(status);

-- Add index on author for better query performance
CREATE INDEX idx_adrs_author ON adrs(author);