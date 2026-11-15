-- Migration 004: Add designation (job role) column to submissions table
-- Run this against your existing nd_audit database if the table already exists.

ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS designation VARCHAR(255);
