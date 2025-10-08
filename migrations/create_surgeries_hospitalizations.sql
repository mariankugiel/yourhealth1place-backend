-- Migration to create surgeries and hospitalizations table
-- This is for the history tab, not health record types

-- Create enum for procedure types
CREATE TYPE procedure_type AS ENUM ('surgery', 'hospitalization');

-- Create enum for recovery status
CREATE TYPE recovery_status AS ENUM ('full_recovery', 'partial_recovery', 'no_recovery');

-- Create surgeries and hospitalizations table
CREATE TABLE surgeries_hospitalizations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    procedure_type procedure_type NOT NULL,
    name VARCHAR(255) NOT NULL,
    procedure_date DATE NOT NULL,
    reason VARCHAR(500),
    treatment VARCHAR(500),
    body_area VARCHAR(100),
    recovery_status recovery_status NOT NULL DEFAULT 'full_recovery',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id)
);

-- Create indexes for better performance
CREATE INDEX idx_surgeries_hospitalizations_user_id ON surgeries_hospitalizations(user_id);
CREATE INDEX idx_surgeries_hospitalizations_procedure_type ON surgeries_hospitalizations(procedure_type);
CREATE INDEX idx_surgeries_hospitalizations_procedure_date ON surgeries_hospitalizations(procedure_date);
CREATE INDEX idx_surgeries_hospitalizations_recovery_status ON surgeries_hospitalizations(recovery_status);

-- Add comments for documentation
COMMENT ON TABLE surgeries_hospitalizations IS 'Stores surgical procedures and hospitalizations for history tab';
COMMENT ON COLUMN surgeries_hospitalizations.procedure_type IS 'Type of procedure: surgery or hospitalization';
COMMENT ON COLUMN surgeries_hospitalizations.name IS 'Name of the surgery or hospitalization';
COMMENT ON COLUMN surgeries_hospitalizations.procedure_date IS 'Date when the procedure occurred';
COMMENT ON COLUMN surgeries_hospitalizations.reason IS 'Reason for the procedure';
COMMENT ON COLUMN surgeries_hospitalizations.treatment IS 'Treatment received';
COMMENT ON COLUMN surgeries_hospitalizations.body_area IS 'Body area affected';
COMMENT ON COLUMN surgeries_hospitalizations.recovery_status IS 'Current recovery status';
COMMENT ON COLUMN surgeries_hospitalizations.notes IS 'Additional notes about the procedure';
