#!/usr/bin/env python3
"""
Supabase Database Setup Script
Creates tables and inserts fake data for RAG system
"""

import os
import json
from datetime import datetime, timedelta
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "http://4.155.228.61:8000")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UiLCJpYXQiOjE3NjM3NjkwNTEsImV4cCI6MjA3OTEyOTA1MX0.Lo5Uda5J4r2WvIO0tLG1fGGAf08r6sP5efw11sc-aW4")

# SQL statements for table creation
CREATE_TABLES_SQL = """
-- Enable pgvector extension (run this in Supabase Studio SQL Editor)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Table 1: report_origin (原始报告)
CREATE TABLE IF NOT EXISTS report_origin (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    season VARCHAR(50) NOT NULL,
    week INTEGER NOT NULL,
    report_content TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(title, season, week)
);

-- Table 2: report_deep_research (深度研究报告)
CREATE TABLE IF NOT EXISTS report_deep_research (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    season VARCHAR(50) NOT NULL,
    week INTEGER NOT NULL,
    report_content TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(title, season, week)
);

-- Table 3: metrics_data (指标数据)
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

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_metrics_lookup ON metrics_data(title, season, week_number);
CREATE INDEX IF NOT EXISTS idx_report_origin_lookup ON report_origin(title, season, week);
CREATE INDEX IF NOT EXISTS idx_report_deep_lookup ON report_deep_research(title, season, week);
"""

# Fake data for report_origin
FAKE_REPORT_ORIGIN = [
    {
        "title": "bo6_wz2",
        "season": "Season 3",
        "week": 1,
        "report_content": """# Weekly Anomaly Report - BO6 Warzone 2 Season 3 Week 1

## Executive Summary
This week marks the launch of Season 3 for BO6 Warzone 2, showing exceptional growth across all key metrics.

## Key Findings

### 1. BR Hours Surge (+410%)
- BR hours increased from 7.6M to 38.9M
- Primary driver: New map "Avalon" release
- Secondary driver: Double XP weekend event

### 2. Player Engagement
- Daily Active Users (DAU) up 156%
- Session length increased by 45 minutes on average
- Return player rate: 67% (vs 34% previous week)

### 3. Segment Analysis
- **BR Main Mode**: Contributed 71.5% of growth
- **Premium Players**: Contributed 67.3% of growth  
- **Dolphins (Mid-spenders)**: Contributed 67.1% of growth

### 4. Revenue Impact
- MTX revenue up 89%
- Battle Pass purchases exceeded projections by 234%

## Recommendations
1. Extend Double XP event by 3 days
2. Increase server capacity for EU region
3. Monitor premium player retention closely
"""
    },
    {
        "title": "bo6_wz2",
        "season": "Season 3",
        "week": 2,
        "report_content": """# Weekly Anomaly Report - BO6 Warzone 2 Season 3 Week 2

## Executive Summary
Week 2 shows stabilization after the Season 3 launch surge, with healthy retention metrics.

## Key Findings

### 1. BR Hours Normalization
- BR hours decreased from 38.9M to 32.1M (-17%)
- Expected post-launch correction
- Still 320% above Season 2 baseline

### 2. Retention Analysis
- Day 7 retention: 45% (excellent for post-launch)
- Churn rate among new players: 23%
- Premium player retention: 78%

### 3. Mode Popularity Shift
- Resurgence mode gaining traction (+45% WoW)
- BR Main maintaining dominance (62% of total playtime)
- Plunder mode declining (-12% WoW)

### 4. Technical Performance
- Server stability: 99.7% uptime
- Average ping reduced by 15ms after capacity upgrade
- Crash rate: 0.3% (industry leading)

## Action Items
1. Investigate Plunder mode decline
2. Plan mid-season content drop
3. Prepare for competitor launch next week
"""
    },
    {
        "title": "bo6_wz2",
        "season": "Season 2",
        "week": 8,
        "report_content": """# Weekly Anomaly Report - BO6 Warzone 2 Season 2 Week 8

## Executive Summary
Final week of Season 2 showing typical end-of-season behavior with players awaiting new content.

## Key Findings

### 1. Engagement Decline
- BR hours at 7.6M (lowest of season)
- Players "saving" playtime for Season 3
- Battle Pass completion rush observed

### 2. End-of-Season Patterns
- 45% of active players completed Battle Pass
- Store purchases down 34%
- LTM participation up 67% (final rewards)

### 3. Community Sentiment
- Positive anticipation for Season 3: 78%
- Concerns about meta staleness: 45%
- Requests for new map: 89%

## Season 2 Summary
- Total unique players: 45M
- Peak concurrent: 2.1M
- Average DAU: 8.2M
"""
    },
    {
        "title": "bo7_mp",
        "season": "Season 1",
        "week": 1,
        "report_content": """# Weekly Anomaly Report - BO7 Multiplayer Season 1 Week 1

## Executive Summary
Launch week for BO7 Multiplayer showing strong initial performance.

## Key Findings

### 1. Launch Metrics
- 12.5M unique players in first week
- Peak concurrent: 1.8M
- Average session: 2.3 hours

### 2. Mode Distribution
- Team Deathmatch: 34%
- Domination: 28%
- Search & Destroy: 18%
- Other modes: 20%

### 3. New Features Reception
- Omnimovement system: 82% positive
- New scorestreak system: 67% positive
- Map design: 74% positive

### 4. Technical Issues
- Matchmaking delays: resolved Day 3
- Spawn issues on 2 maps: hotfix deployed
- Overall stability: 98.9%

## Early Indicators
- Strong word-of-mouth
- Streamer engagement above expectations
- Competitive scene showing interest
"""
    }
]

# Fake data for report_deep_research
FAKE_REPORT_DEEP_RESEARCH = [
    {
        "title": "bo6_wz2",
        "season": "Season 3",
        "week": 1,
        "report_content": """# Deep Research Report: Season 3 Launch Analysis

## Research Question
What factors contributed to the 410% increase in BR hours during Season 3 Week 1?

## Methodology
- Analyzed 2.3M player sessions
- Conducted sentiment analysis on 150K social media posts
- Compared with historical launch data from 5 previous seasons

## Detailed Findings

### 1. Content Impact Analysis

#### New Map "Avalon"
The introduction of the Avalon map was the primary driver of engagement:
- 78% of sessions included Avalon
- Average time on Avalon: 45 minutes (vs 28 min on other maps)
- Map-specific challenges drove 34% more completions

#### Weapon Balance Changes
- SMG meta shift attracted aggressive playstyle players
- Sniper buffs brought back 12% of lapsed players
- AR nerfs initially controversial but accepted within 48 hours

### 2. Marketing & Events Synergy

#### Double XP Weekend
- Timing aligned perfectly with launch
- 67% of players specifically returned for XP event
- Social media mentions: 2.3M (450% above baseline)

#### Streamer Partnerships
- Top 50 streamers averaged 45K concurrent viewers
- Twitch category peaked at #1 for 72 hours
- YouTube content creation up 234%

### 3. Competitive Landscape

#### Competitor Analysis
- Main competitor had server issues during our launch
- No major releases from other BR titles
- Market share gain estimated at 8%

### 4. Player Segment Deep Dive

#### Premium Players (67.3% contribution)
- Immediate Battle Pass purchases: 89%
- Store bundle purchases: 3.2 per player average
- Engagement hours: 12.4 (vs 4.2 for F2P)

#### Dolphins (67.1% contribution)
- Conversion from F2P: 23%
- Average spend: $24
- Highest growth segment

#### Whales (19.6% contribution)
- Lower proportional contribution but highest absolute spend
- Bundle completion rate: 67%
- Early adopter of all cosmetics

## Conclusions

The 410% growth was driven by:
1. **Content Quality** (45% attribution) - Avalon map exceeded expectations
2. **Event Timing** (30% attribution) - Double XP perfectly timed
3. **Marketing** (15% attribution) - Streamer partnerships effective
4. **Market Conditions** (10% attribution) - Competitor struggles

## Recommendations

1. **Extend Success**
   - Keep Avalon in featured rotation for 2 more weeks
   - Plan mid-season map update

2. **Capitalize on Momentum**
   - Launch premium bundle targeting Dolphins
   - Announce esports tournament

3. **Risk Mitigation**
   - Prepare contingency for competitor response
   - Monitor server capacity for sustained load
"""
    },
    {
        "title": "bo6_wz2",
        "season": "Season 3",
        "week": 2,
        "report_content": """# Deep Research Report: Post-Launch Retention Analysis

## Research Question
How well is Season 3 retaining the launch week surge, and what predicts long-term engagement?

## Key Metrics

### Retention Funnel
- Day 1 → Day 7: 45% retention
- Day 7 → Day 14: 72% retention (projected)
- Compared to Season 2 launch: +12% improvement

### Cohort Analysis
| Cohort | D1 Retention | D7 Retention | Projected LTV |
|--------|--------------|--------------|---------------|
| New Players | 34% | 28% | $12 |
| Returning (1-3 months) | 67% | 52% | $45 |
| Returning (3+ months) | 78% | 65% | $67 |
| Never Churned | 89% | 82% | $120 |

### Engagement Predictors
Machine learning model identified top predictors of 30-day retention:
1. **First session length** (>45 min = 3x more likely to retain)
2. **Social play** (squad games = 2.5x retention)
3. **Battle Pass purchase** (2.2x retention)
4. **Achievement unlocks** (>5 in week 1 = 1.8x retention)

## Recommendations
1. Implement "first session optimization" - guide new players to 45+ min sessions
2. Push squad invites during peak hours
3. Offer Battle Pass discount to Day 3 non-purchasers
"""
    }
]

# Fake metrics data
FAKE_METRICS_DATA = [
    # Week 1 - Overall
    {
        "week_end_date": "2025-04-02",
        "week_start_date": "2025-03-27",
        "week_number": 1,
        "title": "bo6_wz2",
        "season": "Season 3",
        "metric_category": "engagement",
        "metric_name": "br_hours",
        "data_type": "overall",
        "is_topline_metric": True,
        "segment_level": 0,
        "segment_combo": None,
        "contribution_value": 0,
        "contribution_type": "neutral",
        "value_current": 38892636.49,
        "value_previous": 7630645.28,
        "value_delta": 31261991.21,
        "current_active_players": 17091206,
        "share_of_delta": 0,
        "is_top_contributor": False,
        "z_score": 0,
        "is_outlier": False,
        "comparison_mode": "cross_season",
        "monitored_title": "bo6_wz2",
        "monitored_season": "Season 3",
        "compare_title": "bo6_wz2",
        "compare_season": "Season 2",
        "base_entity": "Season 3",
        "compare_entity": "Season 2"
    },
    # Week 1 - Segment: BR Main
    {
        "week_end_date": "2025-04-02",
        "week_start_date": "2025-03-27",
        "week_number": 1,
        "title": "bo6_wz2",
        "season": "Season 3",
        "metric_category": "engagement",
        "metric_name": "br_hours",
        "data_type": "segment",
        "is_topline_metric": False,
        "segment_level": 1,
        "segment_combo": "mode_main=BR Main",
        "contribution_value": 0.7147048602711944,
        "contribution_type": "positive",
        "contribution_rank_positive": 1,
        "contribution_rank_overall": 1,
        "value_current": 27471824.61,
        "value_previous": 5128727.55,
        "value_delta": 22343097.06,
        "current_active_players": 5311090,
        "share_of_delta": 0.7147048602711944,
        "is_top_contributor": True,
        "z_score": 3.2,
        "is_outlier": True,
        "outlier_type": "positive_outlier",
        "comparison_mode": "cross_season",
        "monitored_title": "bo6_wz2",
        "monitored_season": "Season 3",
        "compare_title": "bo6_wz2",
        "compare_season": "Season 2",
        "base_entity": "Season 3",
        "compare_entity": "Season 2"
    },
    # Week 1 - Segment: Premium
    {
        "week_end_date": "2025-04-02",
        "week_start_date": "2025-03-27",
        "week_number": 1,
        "title": "bo6_wz2",
        "season": "Season 3",
        "metric_category": "engagement",
        "metric_name": "br_hours",
        "data_type": "segment",
        "is_topline_metric": False,
        "segment_level": 1,
        "segment_combo": "premium_label=Premium",
        "contribution_value": 0.6728473531418597,
        "contribution_type": "positive",
        "contribution_rank_positive": 2,
        "contribution_rank_overall": 2,
        "value_current": 23907797.69,
        "value_previous": 2873249.65,
        "value_delta": 21034548.04,
        "current_active_players": 11481145,
        "share_of_delta": 0.6728473531418597,
        "is_top_contributor": False,
        "z_score": 2.8,
        "is_outlier": True,
        "outlier_type": "positive_outlier",
        "comparison_mode": "cross_season",
        "monitored_title": "bo6_wz2",
        "monitored_season": "Season 3",
        "compare_title": "bo6_wz2",
        "compare_season": "Season 2",
        "base_entity": "Season 3",
        "compare_entity": "Season 2"
    },
    # Week 1 - Segment: Dolphins
    {
        "week_end_date": "2025-04-02",
        "week_start_date": "2025-03-27",
        "week_number": 1,
        "title": "bo6_wz2",
        "season": "Season 3",
        "metric_category": "engagement",
        "metric_name": "br_hours",
        "data_type": "segment",
        "is_topline_metric": False,
        "segment_level": 1,
        "segment_combo": "spending_segment=Dolphins",
        "contribution_value": 0.6713720857640262,
        "contribution_type": "positive",
        "contribution_rank_positive": 3,
        "contribution_rank_overall": 3,
        "value_current": 26539001.74,
        "value_previous": 5550573.49,
        "value_delta": 20988428.24,
        "current_active_players": 6836480,
        "share_of_delta": 0.6713720857640262,
        "is_top_contributor": False,
        "z_score": 2.7,
        "is_outlier": True,
        "outlier_type": "positive_outlier",
        "comparison_mode": "cross_season",
        "monitored_title": "bo6_wz2",
        "monitored_season": "Season 3",
        "compare_title": "bo6_wz2",
        "compare_season": "Season 2",
        "base_entity": "Season 3",
        "compare_entity": "Season 2"
    },
    # Week 1 - Segment: F2P
    {
        "week_end_date": "2025-04-02",
        "week_start_date": "2025-03-27",
        "week_number": 1,
        "title": "bo6_wz2",
        "season": "Season 3",
        "metric_category": "engagement",
        "metric_name": "br_hours",
        "data_type": "segment",
        "is_topline_metric": False,
        "segment_level": 1,
        "segment_combo": "premium_label=F2P",
        "contribution_value": 0.3271526468581403,
        "contribution_type": "positive",
        "contribution_rank_positive": 4,
        "contribution_rank_overall": 4,
        "value_current": 14984838.80,
        "value_previous": 4757395.63,
        "value_delta": 10227443.17,
        "current_active_players": 5610061,
        "share_of_delta": 0.3271526468581403,
        "is_top_contributor": False,
        "z_score": 1.2,
        "is_outlier": False,
        "comparison_mode": "cross_season",
        "monitored_title": "bo6_wz2",
        "monitored_season": "Season 3",
        "compare_title": "bo6_wz2",
        "compare_season": "Season 2",
        "base_entity": "Season 3",
        "compare_entity": "Season 2"
    },
    # Week 1 - Segment: Whales
    {
        "week_end_date": "2025-04-02",
        "week_start_date": "2025-03-27",
        "week_number": 1,
        "title": "bo6_wz2",
        "season": "Season 3",
        "metric_category": "engagement",
        "metric_name": "br_hours",
        "data_type": "segment",
        "is_topline_metric": False,
        "segment_level": 1,
        "segment_combo": "spending_segment=Whales",
        "contribution_value": 0.1964749336344091,
        "contribution_type": "positive",
        "contribution_rank_positive": 5,
        "contribution_rank_overall": 5,
        "value_current": 7138484.54,
        "value_previous": 996286.89,
        "value_delta": 6142197.65,
        "current_active_players": 1538213,
        "share_of_delta": 0.1964749336344091,
        "is_top_contributor": False,
        "z_score": 0.8,
        "is_outlier": False,
        "comparison_mode": "cross_season",
        "monitored_title": "bo6_wz2",
        "monitored_season": "Season 3",
        "compare_title": "bo6_wz2",
        "compare_season": "Season 2",
        "base_entity": "Season 3",
        "compare_entity": "Season 2"
    },
    # Week 1 - DAU metric
    {
        "week_end_date": "2025-04-02",
        "week_start_date": "2025-03-27",
        "week_number": 1,
        "title": "bo6_wz2",
        "season": "Season 3",
        "metric_category": "engagement",
        "metric_name": "dau",
        "data_type": "overall",
        "is_topline_metric": True,
        "segment_level": 0,
        "segment_combo": None,
        "contribution_value": 0,
        "contribution_type": "neutral",
        "value_current": 8234567,
        "value_previous": 3215678,
        "value_delta": 5018889,
        "current_active_players": 17091206,
        "share_of_delta": 0,
        "is_top_contributor": False,
        "z_score": 2.5,
        "is_outlier": True,
        "outlier_type": "positive_outlier",
        "comparison_mode": "cross_season",
        "monitored_title": "bo6_wz2",
        "monitored_season": "Season 3",
        "compare_title": "bo6_wz2",
        "compare_season": "Season 2",
        "base_entity": "Season 3",
        "compare_entity": "Season 2"
    },
    # Week 2 - Overall
    {
        "week_end_date": "2025-04-09",
        "week_start_date": "2025-04-03",
        "week_number": 2,
        "title": "bo6_wz2",
        "season": "Season 3",
        "metric_category": "engagement",
        "metric_name": "br_hours",
        "data_type": "overall",
        "is_topline_metric": True,
        "segment_level": 0,
        "segment_combo": None,
        "contribution_value": 0,
        "contribution_type": "neutral",
        "value_current": 32145678.90,
        "value_previous": 38892636.49,
        "value_delta": -6746957.59,
        "current_active_players": 15234567,
        "share_of_delta": 0,
        "is_top_contributor": False,
        "z_score": -1.2,
        "is_outlier": False,
        "comparison_mode": "week_over_week",
        "monitored_title": "bo6_wz2",
        "monitored_season": "Season 3",
        "compare_title": "bo6_wz2",
        "compare_season": "Season 3",
        "base_entity": "Week 2",
        "compare_entity": "Week 1"
    },
    # Week 2 - Resurgence growing
    {
        "week_end_date": "2025-04-09",
        "week_start_date": "2025-04-03",
        "week_number": 2,
        "title": "bo6_wz2",
        "season": "Season 3",
        "metric_category": "engagement",
        "metric_name": "br_hours",
        "data_type": "segment",
        "is_topline_metric": False,
        "segment_level": 1,
        "segment_combo": "mode_main=Resurgence",
        "contribution_value": 0.45,
        "contribution_type": "positive",
        "contribution_rank_positive": 1,
        "contribution_rank_overall": 1,
        "value_current": 9876543.21,
        "value_previous": 6812345.67,
        "value_delta": 3064197.54,
        "current_active_players": 4521890,
        "share_of_delta": 0.45,
        "is_top_contributor": True,
        "z_score": 2.1,
        "is_outlier": True,
        "outlier_type": "positive_outlier",
        "comparison_mode": "week_over_week",
        "monitored_title": "bo6_wz2",
        "monitored_season": "Season 3",
        "compare_title": "bo6_wz2",
        "compare_season": "Season 3",
        "base_entity": "Week 2",
        "compare_entity": "Week 1"
    },
    # BO7 MP data
    {
        "week_end_date": "2025-04-02",
        "week_start_date": "2025-03-27",
        "week_number": 1,
        "title": "bo7_mp",
        "season": "Season 1",
        "metric_category": "engagement",
        "metric_name": "mp_hours",
        "data_type": "overall",
        "is_topline_metric": True,
        "segment_level": 0,
        "segment_combo": None,
        "contribution_value": 0,
        "contribution_type": "neutral",
        "value_current": 28750000,
        "value_previous": 0,
        "value_delta": 28750000,
        "current_active_players": 12500000,
        "share_of_delta": 1.0,
        "is_top_contributor": True,
        "z_score": 0,
        "is_outlier": False,
        "comparison_mode": "launch",
        "monitored_title": "bo7_mp",
        "monitored_season": "Season 1",
        "base_entity": "Season 1",
        "compare_entity": "Launch"
    }
]


def test_connection():
    """Test Supabase connection"""
    print("🔍 Testing Supabase connection...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"✅ Connected to Supabase at {SUPABASE_URL}")
        return supabase
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None


def print_sql_for_manual_execution():
    """Print SQL statements for manual execution in Supabase Studio"""
    print("\n" + "="*80)
    print("📋 SQL STATEMENTS FOR MANUAL EXECUTION")
    print("="*80)
    print("\nPlease run the following SQL in Supabase Studio SQL Editor:")
    print("\n" + "-"*80)
    print(CREATE_TABLES_SQL)
    print("-"*80)


def insert_fake_data(supabase: Client):
    """Insert fake data into tables"""
    print("\n📝 Inserting fake data...")
    
    # Insert report_origin
    print("\n  → Inserting report_origin...")
    for report in FAKE_REPORT_ORIGIN:
        try:
            result = supabase.table("report_origin").upsert(report).execute()
            print(f"    ✅ Inserted: {report['title']} - {report['season']} Week {report['week']}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Insert report_deep_research
    print("\n  → Inserting report_deep_research...")
    for report in FAKE_REPORT_DEEP_RESEARCH:
        try:
            result = supabase.table("report_deep_research").upsert(report).execute()
            print(f"    ✅ Inserted: {report['title']} - {report['season']} Week {report['week']}")
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Insert metrics_data
    print("\n  → Inserting metrics_data...")
    for metric in FAKE_METRICS_DATA:
        try:
            result = supabase.table("metrics_data").insert(metric).execute()
            print(f"    ✅ Inserted: {metric['metric_name']} - {metric.get('segment_combo', 'overall')}")
        except Exception as e:
            print(f"    ❌ Error: {e}")


def verify_data(supabase: Client):
    """Verify inserted data"""
    print("\n🔍 Verifying data...")
    
    try:
        # Check report_origin
        result = supabase.table("report_origin").select("*").execute()
        print(f"\n  report_origin: {len(result.data)} records")
        for r in result.data:
            print(f"    - {r['title']} / {r['season']} / Week {r['week']}")
        
        # Check report_deep_research
        result = supabase.table("report_deep_research").select("*").execute()
        print(f"\n  report_deep_research: {len(result.data)} records")
        for r in result.data:
            print(f"    - {r['title']} / {r['season']} / Week {r['week']}")
        
        # Check metrics_data
        result = supabase.table("metrics_data").select("*").execute()
        print(f"\n  metrics_data: {len(result.data)} records")
        
        # Get unique combinations
        combos = set()
        for r in result.data:
            combos.add(f"{r['title']} / {r['season']} / Week {r['week_number']}")
        for c in sorted(combos):
            print(f"    - {c}")
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        print("   Tables may not exist yet. Please run the SQL manually first.")


def main():
    print("="*80)
    print("🚀 SUPABASE DATABASE SETUP")
    print("="*80)
    
    # Test connection
    supabase = test_connection()
    
    if not supabase:
        print("\n⚠️ Cannot connect to Supabase.")
        print_sql_for_manual_execution()
        return
    
    # Print SQL for table creation
    print_sql_for_manual_execution()
    
    # Ask user to confirm tables are created
    print("\n" + "="*80)
    print("⏳ NEXT STEPS:")
    print("="*80)
    print("""
1. Open Supabase Studio at: http://4.155.228.61:3000
2. Go to SQL Editor
3. Run the SQL statements above to create tables
4. Then run this script again with --insert flag to add fake data

Or run: python setup_supabase.py --insert
    """)
    
    import sys
    if "--insert" in sys.argv:
        insert_fake_data(supabase)
        verify_data(supabase)
    elif "--verify" in sys.argv:
        verify_data(supabase)


if __name__ == "__main__":
    main()

