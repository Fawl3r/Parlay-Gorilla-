-- Revenue Metrics SQL Queries
-- Run these queries directly with psql for CLI analytics

-- ============================================
-- Total Revenue
-- ============================================
-- Total revenue (all time)
SELECT 
    SUM(amount) AS total_revenue,
    COUNT(*) AS total_payments
FROM payments
WHERE status = 'paid';

-- Revenue in the last 30 days
SELECT 
    SUM(amount) AS revenue_30d,
    COUNT(*) AS payments_30d
FROM payments
WHERE status = 'paid'
  AND paid_at >= NOW() - INTERVAL '30 days';

-- ============================================
-- Revenue by Time Period
-- ============================================
-- Daily revenue for the last 30 days
SELECT 
    DATE(paid_at) AS date,
    SUM(amount) AS revenue,
    COUNT(*) AS payments
FROM payments
WHERE status = 'paid'
  AND paid_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(paid_at)
ORDER BY date DESC;

-- Weekly revenue for the last 12 weeks
SELECT 
    DATE_TRUNC('week', paid_at) AS week,
    SUM(amount) AS revenue,
    COUNT(*) AS payments
FROM payments
WHERE status = 'paid'
  AND paid_at >= NOW() - INTERVAL '12 weeks'
GROUP BY DATE_TRUNC('week', paid_at)
ORDER BY week DESC;

-- Monthly revenue for the last 12 months
SELECT 
    DATE_TRUNC('month', paid_at) AS month,
    SUM(amount) AS revenue,
    COUNT(*) AS payments
FROM payments
WHERE status = 'paid'
  AND paid_at >= NOW() - INTERVAL '12 months'
GROUP BY DATE_TRUNC('month', paid_at)
ORDER BY month DESC;

-- ============================================
-- Revenue by Plan
-- ============================================
SELECT 
    plan,
    SUM(amount) AS total_revenue,
    COUNT(*) AS payment_count,
    ROUND(AVG(amount), 2) AS avg_payment
FROM payments
WHERE status = 'paid'
GROUP BY plan
ORDER BY total_revenue DESC;

-- ============================================
-- Revenue by Provider
-- ============================================
SELECT 
    provider,
    SUM(amount) AS total_revenue,
    COUNT(*) AS payment_count
FROM payments
WHERE status = 'paid'
GROUP BY provider
ORDER BY total_revenue DESC;

-- ============================================
-- Subscription Metrics
-- ============================================
-- Active subscriptions
SELECT COUNT(*) AS active_subscriptions
FROM subscriptions
WHERE status = 'active';

-- Subscriptions by plan
SELECT 
    plan,
    status,
    COUNT(*) AS count
FROM subscriptions
GROUP BY plan, status
ORDER BY plan, status;

-- New subscriptions in the last 30 days
SELECT COUNT(*) AS new_subscriptions
FROM subscriptions
WHERE created_at >= NOW() - INTERVAL '30 days';

-- Churned subscriptions in the last 30 days
SELECT COUNT(*) AS churned_subscriptions
FROM subscriptions
WHERE cancelled_at >= NOW() - INTERVAL '30 days';

-- ============================================
-- Churn Analysis
-- ============================================
-- Churn rate (cancelled in last 30 days / active at start of period)
WITH period_start AS (
    SELECT COUNT(*) AS active_at_start
    FROM subscriptions
    WHERE created_at < NOW() - INTERVAL '30 days'
      AND (cancelled_at IS NULL OR cancelled_at >= NOW() - INTERVAL '30 days')
),
cancelled AS (
    SELECT COUNT(*) AS cancelled_count
    FROM subscriptions
    WHERE cancelled_at >= NOW() - INTERVAL '30 days'
)
SELECT 
    cancelled_count,
    active_at_start,
    ROUND(cancelled_count * 100.0 / NULLIF(active_at_start, 0), 2) AS churn_rate
FROM period_start, cancelled;

-- Cancellation reasons
SELECT 
    COALESCE(cancellation_reason, 'Not specified') AS reason,
    COUNT(*) AS count
FROM subscriptions
WHERE cancelled_at IS NOT NULL
GROUP BY cancellation_reason
ORDER BY count DESC;

-- ============================================
-- Payment Status Breakdown
-- ============================================
SELECT 
    status,
    COUNT(*) AS count,
    SUM(amount) AS total_amount
FROM payments
GROUP BY status
ORDER BY count DESC;

-- Failed payments in the last 30 days
SELECT 
    DATE(created_at) AS date,
    COUNT(*) AS failed_payments
FROM payments
WHERE status = 'failed'
  AND created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- ============================================
-- Customer LTV Approximation
-- ============================================
-- Average revenue per user
SELECT 
    ROUND(SUM(amount) / NULLIF(COUNT(DISTINCT user_id), 0), 2) AS avg_revenue_per_user
FROM payments
WHERE status = 'paid';

-- Average subscription length
SELECT 
    ROUND(AVG(EXTRACT(EPOCH FROM (COALESCE(cancelled_at, NOW()) - created_at)) / 86400), 2) AS avg_days
FROM subscriptions
WHERE status IN ('active', 'cancelled', 'expired');

