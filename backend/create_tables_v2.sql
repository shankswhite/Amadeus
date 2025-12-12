-- ============================================================================
-- SUPABASE DATABASE SETUP - RAG SYSTEM TABLES (V2 - Correct Architecture)
-- ============================================================================
-- 报告内容存 Object Storage，数据库只存元数据和向量
-- ============================================================================

-- Enable pgvector extension for RAG
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- Table 1: report_origin (原始报告 - 元数据)
-- ============================================================================
-- 实际报告内容存储在 Object Storage: reports/origin/{title}_{season}_{week}.md
CREATE TABLE IF NOT EXISTS report_origin (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    season VARCHAR(50) NOT NULL,
    week INTEGER NOT NULL,
    
    -- Object Storage 路径
    storage_path VARCHAR(500),           -- e.g., "reports/origin/bo6_wz2_season3_week1.md"
    
    -- 用于 RAG 的向量嵌入 (OpenAI text-embedding-3-small: 1536 dimensions)
    embedding VECTOR(1536),
    
    -- 报告摘要 (用于快速展示，不存全文)
    summary VARCHAR(500),
    
    -- 元数据
    content_length INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(title, season, week)
);

-- ============================================================================
-- Table 2: report_deep_research (深度研究报告 - 元数据)
-- ============================================================================
-- 实际报告内容存储在 Object Storage: reports/deep_research/{title}_{season}_{week}.md
CREATE TABLE IF NOT EXISTS report_deep_research (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    season VARCHAR(50) NOT NULL,
    week INTEGER NOT NULL,
    
    -- Object Storage 路径
    storage_path VARCHAR(500),
    
    -- 用于 RAG 的向量嵌入
    embedding VECTOR(1536),
    
    -- 报告摘要
    summary VARCHAR(500),
    
    -- 元数据
    content_length INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(title, season, week)
);

-- ============================================================================
-- Table 3: metrics_data (指标数据 - 纯结构化，适合关系型)
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

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================
ALTER TABLE report_origin ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_deep_research ENABLE ROW LEVEL SECURITY;
ALTER TABLE metrics_data ENABLE ROW LEVEL SECURITY;

-- 允许 service_role 完全访问
CREATE POLICY "Service role full access on report_origin" 
    ON report_origin FOR ALL 
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on report_deep_research" 
    ON report_deep_research FOR ALL 
    USING (auth.role() = 'service_role');

CREATE POLICY "Service role full access on metrics_data" 
    ON metrics_data FOR ALL 
    USING (auth.role() = 'service_role');

-- 允许 authenticated 用户读取
CREATE POLICY "Authenticated read on report_origin" 
    ON report_origin FOR SELECT 
    USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated read on report_deep_research" 
    ON report_deep_research FOR SELECT 
    USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated read on metrics_data" 
    ON metrics_data FOR SELECT 
    USING (auth.role() = 'authenticated');

-- ============================================================================
-- Indexes
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_metrics_lookup ON metrics_data(title, season, week_number);
CREATE INDEX IF NOT EXISTS idx_metrics_outlier ON metrics_data(title, season, week_number, is_outlier);
CREATE INDEX IF NOT EXISTS idx_report_origin_lookup ON report_origin(title, season, week);
CREATE INDEX IF NOT EXISTS idx_report_deep_lookup ON report_deep_research(title, season, week);

-- 向量索引 (用于 RAG 相似度搜索)
CREATE INDEX IF NOT EXISTS idx_report_origin_embedding ON report_origin 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_report_deep_embedding ON report_deep_research 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================================================
-- Storage Buckets (需要在 Supabase Studio 或 API 中创建)
-- ============================================================================
-- 运行以下命令创建 storage bucket:
-- INSERT INTO storage.buckets (id, name, public) VALUES ('reports', 'reports', false);

-- ============================================================================
-- Verify
-- ============================================================================
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

