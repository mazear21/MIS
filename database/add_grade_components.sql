-- =============================================
-- Add Grade Components Table
-- Migration: Add flexible grading rubric system
-- Date: 2026-02-14
-- =============================================

-- Create grade_components table
CREATE TABLE IF NOT EXISTS grade_components (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    component_type VARCHAR(50) NOT NULL CHECK (component_type IN ('homework', 'quiz', 'report', 'project', 'exam', 'midterm', 'final', 'lab', 'activity', 'practical')),
    component_name VARCHAR(100) NOT NULL,
    max_score DECIMAL(5,2) NOT NULL CHECK (max_score > 0),
    weight_percentage DECIMAL(5,2) NOT NULL CHECK (weight_percentage >= 0 AND weight_percentage <= 100),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_grade_components_subject ON grade_components(subject_id);

-- Verify table creation
SELECT 'Grade components table created successfully!' as status;
