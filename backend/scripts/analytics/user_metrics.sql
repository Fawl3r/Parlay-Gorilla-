-- User Metrics SQL Queries
-- Run these queries directly with psql for CLI analytics

-- ============================================
-- Total Users
-- ============================================
-- Total registered users
SELECT COUNT(*) AS total_users FROM users;

-- Users by plan
SELECT 
    plan,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM users), 2) AS percentage
FROM users
GROUP BY plan
ORDER BY count DESC;

-- Users by role
SELECT 
    role,
    COUNT(*) AS count
FROM users
GROUP BY role
ORDER BY count DESC;

-- ============================================
-- Active Users (DAU/WAU/MAU)
-- ============================================
-- Daily Active Users (last 24 hours)
SELECT COUNT(DISTINCT id) AS dau
FROM users
WHERE last_login >= NOW() - INTERVAL '24 hours';

-- Weekly Active Users (last 7 days)
SELECT COUNT(DISTINCT id) AS wau
FROM users
WHERE last_login >= NOW() - INTERVAL '7 days';

-- Monthly Active Users (last 30 days)
SELECT COUNT(DISTINCT id) AS mau
FROM users
WHERE last_login >= NOW() - INTERVAL '30 days';

-- ============================================
-- Signups Over Time
-- ============================================
-- Daily signups for the last 30 days
SELECT 
    DATE(created_at) AS signup_date,
    COUNT(*) AS signups
FROM users
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY signup_date DESC;

-- Weekly signups for the last 12 weeks
SELECT 
    DATE_TRUNC('week', created_at) AS week,
    COUNT(*) AS signups
FROM users
WHERE created_at >= NOW() - INTERVAL '12 weeks'
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week DESC;

-- Monthly signups for the last 12 months
SELECT 
    DATE_TRUNC('month', created_at) AS month,
    COUNT(*) AS signups
FROM users
WHERE created_at >= NOW() - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month DESC;

-- ============================================
-- User Retention
-- ============================================
-- Users who signed up and logged in again (simple retention)
SELECT 
    COUNT(*) FILTER (WHERE last_login > created_at + INTERVAL '1 day') AS returned_users,
    COUNT(*) AS total_users,
    ROUND(
        COUNT(*) FILTER (WHERE last_login > created_at + INTERVAL '1 day') * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS return_rate
FROM users
WHERE created_at >= NOW() - INTERVAL '30 days';

-- ============================================
-- Active vs Inactive Users
-- ============================================
SELECT 
    is_active,
    COUNT(*) AS count
FROM users
GROUP BY is_active;

-- Users inactive for more than 30 days
SELECT COUNT(*) AS inactive_30_days
FROM users
WHERE is_active = true
  AND (last_login IS NULL OR last_login < NOW() - INTERVAL '30 days');

-- ============================================
-- Premium Conversion
-- ============================================
-- Conversion rate from free to paid
SELECT 
    COUNT(*) FILTER (WHERE plan IN ('standard', 'elite')) AS paid_users,
    COUNT(*) AS total_users,
    ROUND(
        COUNT(*) FILTER (WHERE plan IN ('standard', 'elite')) * 100.0 / NULLIF(COUNT(*), 0),
        2
    ) AS conversion_rate
FROM users;

-- New paid users in the last 30 days (from subscriptions)
SELECT COUNT(*) AS new_paid_users
FROM subscriptions
WHERE created_at >= NOW() - INTERVAL '30 days'
  AND status = 'active';

