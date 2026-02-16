-- Update grade_components table to use new component types
-- Add 'seminar', change 'lab' to 'lab_report', remove 'practical'

-- First, update existing 'lab' entries to 'lab_report'
UPDATE grade_components SET component_type = 'lab_report' WHERE component_type = 'lab';

-- Update existing 'practical' entries to 'lab_report' (if any exist)
UPDATE grade_components SET component_type = 'lab_report' WHERE component_type = 'practical';

-- Drop the old constraint
ALTER TABLE grade_components DROP CONSTRAINT IF EXISTS grade_components_component_type_check;

-- Add the new constraint with updated types
ALTER TABLE grade_components ADD CONSTRAINT grade_components_component_type_check 
    CHECK (component_type IN ('homework', 'quiz', 'report', 'project', 'exam', 'midterm', 'final', 'lab_report', 'activity', 'seminar'));
