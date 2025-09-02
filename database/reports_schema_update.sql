-- Database Schema Updates for Report Management
-- Add these to your existing schema for better report handling

-- Create reports table to store report files in database
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID REFERENCES analysis_sessions(id) ON DELETE CASCADE,
    ticker VARCHAR(10) NOT NULL,
    company_name VARCHAR(255),
    report_type VARCHAR(10) NOT NULL, -- 'pdf' or 'latex'
    filename VARCHAR(255) NOT NULL,
    file_content BYTEA NOT NULL, -- Store the actual file content
    file_size BIGINT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '5 days')
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_session_id ON reports(session_id);
CREATE INDEX IF NOT EXISTS idx_reports_ticker ON reports(ticker);
CREATE INDEX IF NOT EXISTS idx_reports_expires_at ON reports(expires_at);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at);

-- Update analysis_results table to reference reports table
ALTER TABLE analysis_results 
ADD COLUMN IF NOT EXISTS report_id UUID REFERENCES reports(id) ON DELETE SET NULL;

-- Create function to cleanup expired reports
CREATE OR REPLACE FUNCTION cleanup_expired_reports()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM reports WHERE expires_at < CURRENT_TIMESTAMP;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to cleanup reports older than specified days
CREATE OR REPLACE FUNCTION cleanup_old_reports(days_threshold INTEGER DEFAULT 5)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM reports WHERE created_at < (CURRENT_TIMESTAMP - INTERVAL '1 day' * days_threshold);
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create view for user report history
CREATE OR REPLACE VIEW user_report_history AS
SELECT 
    r.id as report_id,
    r.user_id,
    r.ticker,
    r.company_name,
    r.report_type,
    r.filename,
    r.file_size,
    r.created_at,
    r.expires_at,
    s.analysis_status,
    ar.overall_score,
    ar.recommendation_action,
    ar.model_used
FROM reports r
LEFT JOIN analysis_sessions s ON r.session_id = s.id
LEFT JOIN analysis_results ar ON s.id = ar.session_id
ORDER BY r.created_at DESC;

-- Comment: To run cleanup manually, use:
-- SELECT cleanup_expired_reports();
-- SELECT cleanup_old_reports(5);
