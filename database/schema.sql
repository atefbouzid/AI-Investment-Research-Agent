-- Optimized PostgreSQL Database Schema for Investment Research Platform
-- Simplified for maximum efficiency with only essential tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for authentication and user management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Reports table - consolidated to store all analysis data and files
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Stock Information
    ticker VARCHAR(10) NOT NULL,
    company_name VARCHAR(255),
    
    -- Analysis Results (consolidated from analysis_results table)
    overall_score DECIMAL(5,2),
    recommendation_action VARCHAR(20), -- BUY, SELL, HOLD
    recommendation_confidence DECIMAL(5,2),
    model_used VARCHAR(100),
    analysis_data JSONB, -- Complete analysis data in JSON format
    
    -- File Storage
    filename VARCHAR(255) NOT NULL,
    file_content_pdf BYTEA, -- PDF file content
    file_content_latex TEXT, -- LaTeX source content
    file_size BIGINT,
    
    -- Status and Timestamps
    analysis_status VARCHAR(20) DEFAULT 'completed', -- completed, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    error_message TEXT
);

-- Create indexes for better performance
CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_ticker ON reports(ticker);
CREATE INDEX idx_reports_created_at ON reports(created_at);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at on users table
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


