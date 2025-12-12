-- ============================================================
-- Supabase Tables for Game Analytics Dashboard
-- ============================================================

-- 1. Research Reports Table (研究报告)
-- 存储 ODR 生成的深度研究报告
CREATE TABLE IF NOT EXISTS research_reports (
    id BIGSERIAL PRIMARY KEY,
    thread_id TEXT UNIQUE NOT NULL,          -- ODR thread ID
    title TEXT NOT NULL,                      -- 游戏标题 (e.g., "Call of Duty BO7")
    season TEXT,                              -- 赛季 (e.g., "Season 1", "2024")
    week_number INTEGER,                      -- 周数 (e.g., 47)
    week_start_date DATE,                     -- 周开始日期
    week_end_date DATE,                       -- 周结束日期
    report_content TEXT,                      -- 研究报告全文 (Markdown格式)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建索引以加速查询
CREATE INDEX IF NOT EXISTS idx_reports_title ON research_reports(title);
CREATE INDEX IF NOT EXISTS idx_reports_season_week ON research_reports(season, week_number);
CREATE INDEX IF NOT EXISTS idx_reports_dates ON research_reports(week_start_date, week_end_date);

-- 2. Anomalies Metadata Table (异常元数据)
-- 存储 Databricks 检测到的异常记录
CREATE TABLE IF NOT EXISTS anomalies (
    id BIGSERIAL PRIMARY KEY,
    thread_id TEXT,                           -- 关联的 ODR thread ID (可为空)
    title TEXT NOT NULL,                      -- 游戏标题
    season TEXT,                              -- 赛季
    week_number INTEGER,                      -- 周数
    week_start_date DATE,                     -- 周开始日期
    week_end_date DATE,                       -- 周结束日期
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 外键关联到研究报告 (可选)
    CONSTRAINT fk_report 
        FOREIGN KEY (thread_id) 
        REFERENCES research_reports(thread_id)
        ON DELETE SET NULL
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_anomalies_title ON anomalies(title);
CREATE INDEX IF NOT EXISTS idx_anomalies_season_week ON anomalies(season, week_number);
CREATE INDEX IF NOT EXISTS idx_anomalies_dates ON anomalies(week_start_date, week_end_date);

-- 3. Databricks Sync Table (Databricks 同步表)
-- 占位表，后续根据 Databricks 表结构定义
CREATE TABLE IF NOT EXISTS databricks_sync (
    id BIGSERIAL PRIMARY KEY,
    sync_date TIMESTAMPTZ DEFAULT NOW(),
    -- 其他字段后续添加
    raw_data JSONB                            -- 暂时用 JSONB 存储原始数据
);

-- ============================================================
-- Row Level Security (RLS) - 可选，用于多租户场景
-- ============================================================

-- 启用 RLS (如果需要)
-- ALTER TABLE research_reports ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE anomalies ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Helper Functions
-- ============================================================

-- 自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为 research_reports 添加触发器
DROP TRIGGER IF EXISTS update_research_reports_updated_at ON research_reports;
CREATE TRIGGER update_research_reports_updated_at
    BEFORE UPDATE ON research_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- Sample Data (测试用，可删除)
-- ============================================================

-- 插入示例研究报告
INSERT INTO research_reports (thread_id, title, season, week_number, week_start_date, week_end_date, report_content)
VALUES 
    ('thread_001', 'Call of Duty BO7', '2024', 47, '2024-11-18', '2024-11-24', 
     '# CoD BO7 Weekly Report\n\n## Summary\nPlayer sentiment analysis shows...\n\n## Key Findings\n- Revenue up 15%\n- Player retention stable'),
    ('thread_002', 'FIFA 25', '2024', 47, '2024-11-18', '2024-11-24',
     '# FIFA 25 Weekly Report\n\n## Summary\nNew season launch impact...')
ON CONFLICT (thread_id) DO NOTHING;

-- 插入示例异常记录
INSERT INTO anomalies (thread_id, title, season, week_number, week_start_date, week_end_date)
VALUES 
    ('thread_001', 'Call of Duty BO7', '2024', 47, '2024-11-18', '2024-11-24'),
    (NULL, 'Valorant', '2024', 47, '2024-11-18', '2024-11-24')
ON CONFLICT DO NOTHING;

-- ============================================================
-- Verification
-- ============================================================

-- 查看创建的表
-- SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

-- 查看表结构
-- \d research_reports
-- \d anomalies

