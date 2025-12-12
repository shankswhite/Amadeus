# Supabase 数据库设置指南

## 📋 概述

本指南帮助你在 Supabase 中创建 RAG 系统所需的表并插入测试数据。

## 🔧 方法 1: 通过 SSH 到 Supabase VM 执行

### Step 1: SSH 到 Supabase VM

```bash
ssh <your-user>@4.155.228.61
```

### Step 2: 进入 PostgreSQL 容器

```bash
# 查找 postgres 容器
docker ps | grep postgres

# 进入容器 (假设容器名是 supabase-db 或类似)
docker exec -it supabase-db-1 psql -U postgres -d postgres
```

### Step 3: 执行 SQL 脚本

复制 `create_tables.sql` 的内容并在 psql 中执行：

```sql
-- 粘贴 create_tables.sql 的内容
```

然后复制 `insert_fake_data.sql` 的内容：

```sql
-- 粘贴 insert_fake_data.sql 的内容
```

### Step 4: 验证数据

```sql
SELECT 'report_origin' as table_name, COUNT(*) FROM report_origin
UNION ALL SELECT 'report_deep_research', COUNT(*) FROM report_deep_research
UNION ALL SELECT 'metrics_data', COUNT(*) FROM metrics_data;
```

---

## 🔧 方法 2: 使用 Supabase Studio (如果可访问)

### Step 1: 开放端口 3000

在 Azure Portal 或 VM 防火墙中开放端口 3000。

### Step 2: 访问 Studio

```
http://4.155.228.61:3000
```

### Step 3: 执行 SQL

1. 进入 **SQL Editor**
2. 粘贴 `create_tables.sql` 内容
3. 点击 **Run**
4. 粘贴 `insert_fake_data.sql` 内容
5. 点击 **Run**

---

## 🔧 方法 3: 开放 PostgreSQL 端口后本地执行

### Step 1: 开放端口 5432

在 Azure Portal 添加入站规则允许 5432 端口。

### Step 2: 本地执行 SQL

```bash
# 执行建表
psql -h 4.155.228.61 -p 5432 -U postgres -d postgres -f backend/create_tables.sql

# 执行数据插入
psql -h 4.155.228.61 -p 5432 -U postgres -d postgres -f backend/insert_fake_data.sql
```

---

## ✅ 验证成功

执行以下查询确认数据已插入：

```sql
-- 检查表数量
SELECT 'report_origin' as table_name, COUNT(*) FROM report_origin
UNION ALL SELECT 'report_deep_research', COUNT(*) FROM report_deep_research  
UNION ALL SELECT 'metrics_data', COUNT(*) FROM metrics_data;

-- 预期结果:
-- report_origin: 4
-- report_deep_research: 2
-- metrics_data: 12
```

```sql
-- 检查数据内容
SELECT title, season, week FROM report_origin ORDER BY title, season, week;

-- 预期结果:
-- bo6_wz2 | Season 2 | 8
-- bo6_wz2 | Season 3 | 1
-- bo6_wz2 | Season 3 | 2
-- bo7_mp  | Season 1 | 1
```

---

## 📁 文件位置

- `backend/create_tables.sql` - 创建表的 SQL
- `backend/insert_fake_data.sql` - 插入测试数据的 SQL
- `backend/setup_supabase.py` - Python 设置脚本 (可选)

---

## 🗄️ 数据库结构

### 表 1: `report_origin`
| 字段 | 类型 | 说明 |
|------|------|------|
| title | VARCHAR(100) | 游戏标题 (e.g., bo6_wz2) |
| season | VARCHAR(50) | 赛季 (e.g., Season 3) |
| week | INTEGER | 周数 |
| report_content | TEXT | 原始报告内容 |

### 表 2: `report_deep_research`
| 字段 | 类型 | 说明 |
|------|------|------|
| title | VARCHAR(100) | 游戏标题 |
| season | VARCHAR(50) | 赛季 |
| week | INTEGER | 周数 |
| report_content | TEXT | 深度研究报告内容 |

### 表 3: `metrics_data`
| 字段 | 类型 | 说明 |
|------|------|------|
| title | VARCHAR(100) | 游戏标题 |
| season | VARCHAR(50) | 赛季 |
| week_number | INTEGER | 周数 |
| metric_name | VARCHAR(100) | 指标名称 |
| segment_combo | VARCHAR(200) | 分段组合 |
| value_current | DECIMAL | 当前值 |
| value_previous | DECIMAL | 前值 |
| value_delta | DECIMAL | 变化量 |
| contribution_value | DECIMAL | 贡献度 |
| is_outlier | BOOLEAN | 是否异常 |
| ... | ... | 其他字段 |

---

## 🔑 测试数据说明

### Fake 报告数据
- **bo6_wz2 Season 3 Week 1**: Season 3 发布首周，BR hours 增长 410%
- **bo6_wz2 Season 3 Week 2**: Season 3 第二周，留存分析
- **bo6_wz2 Season 2 Week 8**: Season 2 最后一周
- **bo7_mp Season 1 Week 1**: BO7 多人模式发布首周

### Fake 指标数据
- 包含 overall 和 segment 级别数据
- 涵盖 br_hours, dau, mp_hours 等指标
- 包含 BR Main, Premium, Dolphins, F2P, Whales 等分段

---

## 📞 下一步

数据库设置完成后，请告诉我，我将继续：

1. **Phase 2**: 创建 LangGraph RAG 服务
2. **Phase 3**: 更新前端界面

