# Dependabot Alert #2 Resolution Guide

**Date:** December 2025  
**Alert URL:** https://github.com/Fawl3r/Parlay-Gorilla-/security/dependabot/2

---

## Step 1: Identify the Vulnerability

1. Go to the alert on GitHub: https://github.com/Fawl3r/Parlay-Gorilla-/security/dependabot/2
2. Note the following information:
   - **Package name** (e.g., `httpx`, `numpy`, `requests`)
   - **Current version** (e.g., `0.24.1`, `1.26.3`)
   - **Severity** (Critical, High, Moderate, Low)
   - **Recommended fix version**
   - **CVE number** (if available)

## Step 2: Check for Automatic PR

Dependabot may have created a pull request automatically:

1. Go to **Pull requests** tab
2. Look for PRs from `dependabot[bot]`
3. PR title format: `Bump [package] from [old-version] to [new-version]`
4. Review and merge if safe

## Step 3: Manual Fix (If No PR)

### For Backend (Python/pip) Dependencies:

```bash
cd backend

# Update the specific package in requirements.txt
# Example: httpx==0.24.1 → httpx==0.27.0
# Edit requirements.txt manually or use:

pip install --upgrade [package-name]

# Update requirements.txt
pip freeze > requirements.txt

# Or update directly in requirements.txt:
# Change: httpx==0.24.1
# To: httpx==[recommended-version]
```

### For Frontend (npm) Dependencies:

```bash
cd frontend

# Update specific package
npm install [package-name]@[version]

# Or use npm audit fix (if safe)
npm audit fix
```

## Step 4: Common Critical Vulnerabilities

### Python Packages (Backend)

**httpx (0.24.1):**
- Check for CVE-2024-* vulnerabilities
- Update to latest: `httpx==0.27.0` or newer

**numpy (1.26.3):**
- Check for CVE-2024-* vulnerabilities
- Update to latest: `numpy==2.0.0` or newer (may have breaking changes)
- Or update to latest 1.x: `numpy==1.26.4` or newer

**Other common vulnerable packages:**
- `urllib3` - Update to latest
- `requests` - Update to latest
- `cryptography` - Update to latest
- `python-jose` - Update to latest

### npm Packages (Frontend)

**Common critical vulnerabilities:**
- `axios` - Update to latest
- `jsonwebtoken` - Update to latest
- `node-forge` - Update to latest
- `minimist` - Update to latest

## Step 5: Test After Update

```bash
# Backend
cd backend
python -m pytest tests/  # Run tests

# Frontend
cd frontend
npm run test:unit  # Run unit tests
npm run build      # Verify build works
```

## Step 6: Commit and Push

```bash
git add backend/requirements.txt  # or frontend/package.json
git commit -m "fix: update [package] to [version] to resolve CVE-XXXX-XXXX"
git push
```

## Step 7: Verify Resolution

1. Wait 5-10 minutes for GitHub to re-scan
2. Check Dependabot alerts: https://github.com/Fawl3r/Parlay-Gorilla-/security/dependabot
3. Alert should show as "Fixed" or "Dismissed"

---

## Quick Reference: Update Commands

### Backend
```bash
cd backend
pip install --upgrade [package-name]
pip freeze > requirements.txt
```

### Frontend
```bash
cd frontend
npm install [package-name]@[version]
```

---

## Need Help?

If you're unsure which package is affected:
1. Check the GitHub alert page for exact details
2. Run `npm audit` (frontend) or `pip-audit` (backend)
3. Look for packages marked as "critical" severity

