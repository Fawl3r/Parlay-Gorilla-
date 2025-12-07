-- Usage Metrics SQL Queries
-- Run these queries directly with psql for CLI analytics

-- ============================================
-- Event Counts by Type
-- ============================================
-- All events in the last 7 days
SELECT 
    event_type,
    COUNT(*) AS count
FROM app_events
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY event_type
ORDER BY count DESC;

-- Events by day
SELECT 
    DATE(created_at) AS event_date,
    event_type,
    COUNT(*) AS count
FROM app_events
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at), event_type
ORDER BY event_date DESC, count DESC;

-- ============================================
-- Analysis Page Views
-- ============================================
-- Total analysis views in the last 30 days
SELECT COUNT(*) AS analysis_views
FROM app_events
WHERE event_type = 'view_analysis'
  AND created_at >= NOW() - INTERVAL '30 days';

-- Analysis views by sport
SELECT 
    metadata->>'sport' AS sport,
    COUNT(*) AS views
FROM app_events
WHERE event_type = 'view_analysis'
  AND created_at >= NOW() - INTERVAL '30 days'
  AND metadata->>'sport' IS NOT NULL
GROUP BY metadata->>'sport'
ORDER BY views DESC;

-- Top 20 most viewed matchups
SELECT 
    metadata->>'sport' AS sport,
    metadata->>'matchup' AS matchup,
    COUNT(*) AS views
FROM app_events
WHERE event_type = 'view_analysis'
  AND created_at >= NOW() - INTERVAL '7 days'
  AND metadata->>'matchup' IS NOT NULL
GROUP BY metadata->>'sport', metadata->>'matchup'
ORDER BY views DESC
LIMIT 20;

-- ============================================
-- Parlay Builder Usage
-- ============================================
-- Parlay builder sessions
SELECT COUNT(*) AS parlay_sessions
FROM app_events
WHERE event_type = 'build_parlay'
  AND created_at >= NOW() - INTERVAL '30 days';

-- Parlays by type (from parlay_events)
SELECT 
    parlay_type,
    COUNT(*) AS count,
    ROUND(AVG(legs_count), 2) AS avg_legs,
    MIN(legs_count) AS min_legs,
    MAX(legs_count) AS max_legs
FROM parlay_events
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY parlay_type
ORDER BY count DESC;

-- Parlay legs distribution
SELECT 
    legs_count,
    COUNT(*) AS count
FROM parlay_events
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY legs_count
ORDER BY legs_count;

-- ============================================
-- Feature Usage
-- ============================================
-- Upset Finder clicks
SELECT COUNT(*) AS upset_finder_clicks
FROM app_events
WHERE event_type = 'click_upset_finder'
  AND created_at >= NOW() - INTERVAL '30 days';

-- Feature usage breakdown
SELECT 
    event_type,
    COUNT(*) AS usage_count,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(DISTINCT session_id) AS unique_sessions
FROM app_events
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY event_type
ORDER BY usage_count DESC;

-- ============================================
-- Traffic & Referrers
-- ============================================
-- Top landing pages
SELECT 
    page_url,
    COUNT(*) AS views
FROM app_events
WHERE created_at >= NOW() - INTERVAL '7 days'
  AND page_url IS NOT NULL
GROUP BY page_url
ORDER BY views DESC
LIMIT 20;

-- Referrer breakdown
SELECT 
    CASE 
        WHEN referrer IS NULL OR referrer = '' THEN 'direct'
        WHEN referrer ILIKE '%google%' THEN 'google'
        WHEN referrer ILIKE '%facebook%' OR referrer ILIKE '%twitter%' THEN 'social'
        ELSE 'other'
    END AS referrer_type,
    COUNT(*) AS count
FROM app_events
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY referrer_type
ORDER BY count DESC;

-- ============================================
-- Session Analytics
-- ============================================
-- Unique sessions per day
SELECT 
    DATE(created_at) AS date,
    COUNT(DISTINCT session_id) AS unique_sessions
FROM app_events
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND session_id IS NOT NULL
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Average events per session
SELECT 
    ROUND(AVG(event_count), 2) AS avg_events_per_session
FROM (
    SELECT 
        session_id,
        COUNT(*) AS event_count
    FROM app_events
    WHERE created_at >= NOW() - INTERVAL '7 days'
      AND session_id IS NOT NULL
    GROUP BY session_id
) sessions;

