-- ============================================================================
-- SUPABASE DATABASE SETUP - RAG SYSTEM TABLES
-- ============================================================================
-- Run this SQL in Supabase Studio SQL Editor or via psql
-- ============================================================================

-- Enable pgvector extension (for future embedding support)
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- Table 1: report_origin (原始报告)
-- ============================================================================
CREATE TABLE IF NOT EXISTS report_origin (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    season VARCHAR(50) NOT NULL,
    week INTEGER NOT NULL,
    report_content TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(title, season, week)
);

-- Enable RLS but allow all for now
ALTER TABLE report_origin ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for report_origin" ON report_origin FOR ALL USING (true);

-- ============================================================================
-- Table 2: report_deep_research (深度研究报告)
-- ============================================================================
CREATE TABLE IF NOT EXISTS report_deep_research (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    season VARCHAR(50) NOT NULL,
    week INTEGER NOT NULL,
    report_content TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(title, season, week)
);

ALTER TABLE report_deep_research ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for report_deep_research" ON report_deep_research FOR ALL USING (true);

-- ============================================================================
-- Table 3: metrics_data (指标数据)
-- ============================================================================
CREATE TABLE IF NOT EXISTS metrics_data (
    id SERIAL PRIMARY KEY,
    week_end_date DATE,
    week_start_date DATE,
    week_number INTEGER,
    title VARCHAR(100),
    season VARCHAR(50),
    season_start_date DATE,
    season_end_date DATE,
    metric_category VARCHAR(50),
    metric_name VARCHAR(100),
    data_type VARCHAR(50),
    is_topline_metric BOOLEAN DEFAULT FALSE,
    segment_level INTEGER,
    segment_combo VARCHAR(200),
    contribution_value DECIMAL(18,6),
    contribution_type VARCHAR(20),
    contribution_rank_positive INTEGER,
    contribution_rank_negative INTEGER,
    contribution_rank_overall INTEGER,
    value_current DECIMAL(18,4),
    value_previous DECIMAL(18,4),
    value_delta DECIMAL(18,4),
    current_active_players BIGINT,
    share_of_delta DECIMAL(18,6),
    is_top_contributor BOOLEAN DEFAULT FALSE,
    z_score DECIMAL(10,4),
    is_outlier BOOLEAN DEFAULT FALSE,
    outlier_type VARCHAR(50),
    comparison_mode VARCHAR(50),
    monitored_title VARCHAR(100),
    monitored_season VARCHAR(50),
    compare_title VARCHAR(100),
    compare_season VARCHAR(50),
    base_entity VARCHAR(100),
    compare_entity VARCHAR(100)
);

ALTER TABLE metrics_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for metrics_data" ON metrics_data FOR ALL USING (true);

-- ============================================================================
-- Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_metrics_lookup ON metrics_data(title, season, week_number);
CREATE INDEX IF NOT EXISTS idx_report_origin_lookup ON report_origin(title, season, week);
CREATE INDEX IF NOT EXISTS idx_report_deep_lookup ON report_deep_research(title, season, week);

-- ============================================================================
-- Verify tables created
-- ============================================================================
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

