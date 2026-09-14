-- Migration to add authentication and RLS

-- Add user_id to compliance_reports
ALTER TABLE compliance_reports
ADD COLUMN user_id UUID REFERENCES auth.users(id);

-- Enable RLS on compliance_reports
ALTER TABLE compliance_reports ENABLE ROW LEVEL SECURITY;

-- Policies for compliance_reports
CREATE POLICY "Users can insert their own reports"
ON compliance_reports FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own reports"
ON compliance_reports FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own reports"
ON compliance_reports FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Create table audit_verdict_cache if it doesn't exist, to apply RLS properly
CREATE TABLE IF NOT EXISTS audit_verdict_cache (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    -- other columns ...
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add user_id to audit_verdict_cache if it exists and doesn't have it
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='audit_verdict_cache' AND column_name='user_id') THEN
        ALTER TABLE audit_verdict_cache ADD COLUMN user_id UUID REFERENCES auth.users(id);
    END IF;
END $$;

-- Enable RLS on audit_verdict_cache
ALTER TABLE audit_verdict_cache ENABLE ROW LEVEL SECURITY;

-- Policies for audit_verdict_cache
CREATE POLICY "Users can insert their own verdict cache"
ON audit_verdict_cache FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view their own verdict cache"
ON audit_verdict_cache FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own verdict cache"
ON audit_verdict_cache FOR UPDATE
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- Explicitly allow public read access for reference tables just in case RLS is enabled on them
-- ALTER TABLE compliance_requirements ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "Public read for compliance_requirements" ON compliance_requirements FOR SELECT USING (true);
