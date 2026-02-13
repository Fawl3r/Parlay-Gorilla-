# Parlay Gorilla — Build Checklist

Use this checklist for every build/PR. No CI automation yet; document and follow manually.

## Always

- [ ] **PG_FeatureBuilder**
- [ ] **F3_CodeGuardian**
- [ ] **F3_TestSentinel**

## If touching parlay logic

- [ ] **PG_PicksEngine**
- [ ] **PG_ExplainabilityGuard**
- [ ] **PG_ConfidenceEngineer**
- [ ] **PG_PayoutRiskGuard**

## If touching APIs or data

- [ ] **PG_APIQuotaNinja**
- [ ] **PG_AnomalyDetector**

## If touching paywalls or billing

- [ ] **PG_RevenueSentinel**
- [ ] **PG_ComplianceShield**

## Before merge

- [ ] **F3_InfraWatch**
- [ ] **Safety Mode snapshot must be GREEN**

## Safety gate rule

- **No merge if Safety Mode ≠ GREEN.**
- Exceptions require a documented admin override per **INCIDENT_RUNBOOK.md** (e.g. acknowledged RED override with ticket/incident ID and timeline to fix).
