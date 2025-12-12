-- ============================================================================
-- INSERT FAKE DATA FOR RAG SYSTEM
-- ============================================================================
-- Run this AFTER create_tables.sql
-- ============================================================================

-- ============================================================================
-- Insert report_origin (原始报告)
-- ============================================================================
INSERT INTO report_origin (title, season, week, report_content) VALUES
('bo6_wz2', 'Season 3', 1, '# Weekly Anomaly Report - BO6 Warzone 2 Season 3 Week 1

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
3. Monitor premium player retention closely'),

('bo6_wz2', 'Season 3', 2, '# Weekly Anomaly Report - BO6 Warzone 2 Season 3 Week 2

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
3. Prepare for competitor launch next week'),

('bo6_wz2', 'Season 2', 8, '# Weekly Anomaly Report - BO6 Warzone 2 Season 2 Week 8

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
- Average DAU: 8.2M'),

('bo7_mp', 'Season 1', 1, '# Weekly Anomaly Report - BO7 Multiplayer Season 1 Week 1

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
- Competitive scene showing interest')
ON CONFLICT (title, season, week) DO UPDATE SET report_content = EXCLUDED.report_content;

-- ============================================================================
-- Insert report_deep_research (深度研究报告)
-- ============================================================================
INSERT INTO report_deep_research (title, season, week, report_content) VALUES
('bo6_wz2', 'Season 3', 1, '# Deep Research Report: Season 3 Launch Analysis

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
   - Monitor server capacity for sustained load'),

('bo6_wz2', 'Season 3', 2, '# Deep Research Report: Post-Launch Retention Analysis

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
3. Offer Battle Pass discount to Day 3 non-purchasers')
ON CONFLICT (title, season, week) DO UPDATE SET report_content = EXCLUDED.report_content;

-- ============================================================================
-- Insert metrics_data (指标数据)
-- ============================================================================
INSERT INTO metrics_data (week_end_date, week_start_date, week_number, title, season, metric_category, metric_name, data_type, is_topline_metric, segment_level, segment_combo, contribution_value, contribution_type, contribution_rank_positive, contribution_rank_overall, value_current, value_previous, value_delta, current_active_players, share_of_delta, is_top_contributor, z_score, is_outlier, outlier_type, comparison_mode, monitored_title, monitored_season, compare_title, compare_season, base_entity, compare_entity) VALUES

-- Week 1 - Overall BR Hours
('2025-04-02', '2025-03-27', 1, 'bo6_wz2', 'Season 3', 'engagement', 'br_hours', 'overall', TRUE, 0, NULL, 0, 'neutral', NULL, 0, 38892636.49, 7630645.28, 31261991.21, 17091206, 0, FALSE, 0, FALSE, NULL, 'cross_season', 'bo6_wz2', 'Season 3', 'bo6_wz2', 'Season 2', 'Season 3', 'Season 2'),

-- Week 1 - Segment: BR Main
('2025-04-02', '2025-03-27', 1, 'bo6_wz2', 'Season 3', 'engagement', 'br_hours', 'segment', FALSE, 1, 'mode_main=BR Main', 0.7147048602711944, 'positive', 1, 1, 27471824.61, 5128727.55, 22343097.06, 5311090, 0.7147048602711944, TRUE, 3.2, TRUE, 'positive_outlier', 'cross_season', 'bo6_wz2', 'Season 3', 'bo6_wz2', 'Season 2', 'Season 3', 'Season 2'),

-- Week 1 - Segment: Premium
('2025-04-02', '2025-03-27', 1, 'bo6_wz2', 'Season 3', 'engagement', 'br_hours', 'segment', FALSE, 1, 'premium_label=Premium', 0.6728473531418597, 'positive', 2, 2, 23907797.69, 2873249.65, 21034548.04, 11481145, 0.6728473531418597, FALSE, 2.8, TRUE, 'positive_outlier', 'cross_season', 'bo6_wz2', 'Season 3', 'bo6_wz2', 'Season 2', 'Season 3', 'Season 2'),

-- Week 1 - Segment: Dolphins
('2025-04-02', '2025-03-27', 1, 'bo6_wz2', 'Season 3', 'engagement', 'br_hours', 'segment', FALSE, 1, 'spending_segment=Dolphins', 0.6713720857640262, 'positive', 3, 3, 26539001.74, 5550573.49, 20988428.24, 6836480, 0.6713720857640262, FALSE, 2.7, TRUE, 'positive_outlier', 'cross_season', 'bo6_wz2', 'Season 3', 'bo6_wz2', 'Season 2', 'Season 3', 'Season 2'),

-- Week 1 - Segment: F2P
('2025-04-02', '2025-03-27', 1, 'bo6_wz2', 'Season 3', 'engagement', 'br_hours', 'segment', FALSE, 1, 'premium_label=F2P', 0.3271526468581403, 'positive', 4, 4, 14984838.80, 4757395.63, 10227443.17, 5610061, 0.3271526468581403, FALSE, 1.2, FALSE, NULL, 'cross_season', 'bo6_wz2', 'Season 3', 'bo6_wz2', 'Season 2', 'Season 3', 'Season 2'),

-- Week 1 - Segment: Whales
('2025-04-02', '2025-03-27', 1, 'bo6_wz2', 'Season 3', 'engagement', 'br_hours', 'segment', FALSE, 1, 'spending_segment=Whales', 0.1964749336344091, 'positive', 5, 5, 7138484.54, 996286.89, 6142197.65, 1538213, 0.1964749336344091, FALSE, 0.8, FALSE, NULL, 'cross_season', 'bo6_wz2', 'Season 3', 'bo6_wz2', 'Season 2', 'Season 3', 'Season 2'),

-- Week 1 - DAU metric
('2025-04-02', '2025-03-27', 1, 'bo6_wz2', 'Season 3', 'engagement', 'dau', 'overall', TRUE, 0, NULL, 0, 'neutral', NULL, 0, 8234567, 3215678, 5018889, 17091206, 0, FALSE, 2.5, TRUE, 'positive_outlier', 'cross_season', 'bo6_wz2', 'Season 3', 'bo6_wz2', 'Season 2', 'Season 3', 'Season 2'),

-- Week 2 - Overall
('2025-04-09', '2025-04-03', 2, 'bo6_wz2', 'Season 3', 'engagement', 'br_hours', 'overall', TRUE, 0, NULL, 0, 'neutral', NULL, 0, 32145678.90, 38892636.49, -6746957.59, 15234567, 0, FALSE, -1.2, FALSE, NULL, 'week_over_week', 'bo6_wz2', 'Season 3', 'bo6_wz2', 'Season 3', 'Week 2', 'Week 1'),

-- Week 2 - Resurgence growing
('2025-04-09', '2025-04-03', 2, 'bo6_wz2', 'Season 3', 'engagement', 'br_hours', 'segment', FALSE, 1, 'mode_main=Resurgence', 0.45, 'positive', 1, 1, 9876543.21, 6812345.67, 3064197.54, 4521890, 0.45, TRUE, 2.1, TRUE, 'positive_outlier', 'week_over_week', 'bo6_wz2', 'Season 3', 'bo6_wz2', 'Season 3', 'Week 2', 'Week 1'),

-- Week 2 - DAU
('2025-04-09', '2025-04-03', 2, 'bo6_wz2', 'Season 3', 'engagement', 'dau', 'overall', TRUE, 0, NULL, 0, 'neutral', NULL, 0, 7123456, 8234567, -1111111, 15234567, 0, FALSE, -0.8, FALSE, NULL, 'week_over_week', 'bo6_wz2', 'Season 3', 'bo6_wz2', 'Season 3', 'Week 2', 'Week 1'),

-- BO7 MP data
('2025-04-02', '2025-03-27', 1, 'bo7_mp', 'Season 1', 'engagement', 'mp_hours', 'overall', TRUE, 0, NULL, 0, 'neutral', NULL, 0, 28750000, 0, 28750000, 12500000, 1.0, TRUE, 0, FALSE, NULL, 'launch', 'bo7_mp', 'Season 1', NULL, NULL, 'Season 1', 'Launch');

-- ============================================================================
-- Verify data inserted
-- ============================================================================
SELECT 'report_origin' as table_name, COUNT(*) as count FROM report_origin
UNION ALL
SELECT 'report_deep_research', COUNT(*) FROM report_deep_research
UNION ALL
SELECT 'metrics_data', COUNT(*) FROM metrics_data;

-- Show sample data
SELECT title, season, week, LENGTH(report_content) as content_length FROM report_origin;
SELECT title, season, week_number, metric_name, segment_combo, value_current, value_delta, is_outlier FROM metrics_data LIMIT 10;

