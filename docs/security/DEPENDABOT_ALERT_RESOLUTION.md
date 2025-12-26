# Dependabot Alert Resolution Guide

**Date:** December 2025

---

## How to Resolve Dependabot Security Alerts

### Step 1: View the Alert

1. Go to your repository on GitHub
2. Navigate to: **Security** → **Dependabot alerts**
3. Click on the specific alert (e.g., Alert #1)
4. Review the vulnerability details:
   - **Package name** and version
   - **Severity** (Critical, High, Moderate, Low)
   - **Vulnerability description**
   - **Affected versions**
   - **Recommended fix**

### Step 2: Check for Automatic PR

Dependabot may have automatically created a pull request to fix the vulnerability:

1. Go to **Pull requests** tab
2. Look for PRs from `dependabot[bot]`
3. PR title format: `Bump [package] from [old-version] to [new-version]`
4. Review the PR:
   - Check if the update is safe
   - Review changelog if available
   - Run tests locally if needed
5. Merge the PR if approved

### Step 3: Manual Resolution (If No PR)

If Dependabot didn't create a PR, fix manually:

#### For Frontend (npm) Dependencies:

```bash
cd frontend

# Check what needs updating
npm audit

# Auto-fix (safe updates only)
npm audit fix

# Or update specific package
npm install [package-name]@latest

# Verify fix
npm audit
```

#### For Backend (pip) Dependencies:

```bash
cd backend

# Check vulnerabilities (requires pip-audit)
pip install pip-audit
pip-audit

# Update specific package
pip install --upgrade [package-name]

# Update requirements.txt
pip freeze > requirements.txt
```

### Step 4: Dismiss Alert (If False Positive)

If the alert is not applicable:

1. Open the alert on GitHub
2. Click **Dismiss alert**
3. Select reason:
   - **Vulnerable code is not actually used**
   - **Won't fix** (with explanation)
   - **Tolerable risk** (with explanation)
4. Add optional comment
5. Click **Dismiss alert**

### Step 5: Verify Resolution

1. After updating, verify the alert is resolved:
   - Alert status should change to "Dismissed" or "Fixed"
   - Run `npm audit` or `pip-audit` to confirm
2. Commit and push changes
3. Dependabot will automatically detect the fix

---

## Common Dependabot Alert Types

### 1. **npm Package Vulnerabilities**
- Usually in `frontend/package.json`
- Fix: Update package version
- Command: `npm install [package]@[version]`

### 2. **pip Package Vulnerabilities**
- Usually in `backend/requirements.txt`
- Fix: Update package version
- Command: `pip install --upgrade [package]`

### 3. **GitHub Actions Vulnerabilities**
- Usually in `.github/workflows/*.yml`
- Fix: Update action version
- Example: `actions/checkout@v3` → `actions/checkout@v4`

---

## Best Practices

### ✅ Do:
- Review Dependabot PRs promptly
- Test updates in development first
- Keep dependencies up to date
- Review changelogs for breaking changes
- Use `npm audit fix` for safe updates

### ❌ Don't:
- Ignore critical/high severity alerts
- Merge PRs without reviewing
- Dismiss alerts without reason
- Update without testing

---

## Alert Severity Levels

- **Critical:** Immediate action required
- **High:** Fix as soon as possible
- **Moderate:** Fix when convenient
- **Low:** Consider fixing

---

## Troubleshooting

### Alert Not Resolving After Update

1. Clear npm/pip cache:
   ```bash
   npm cache clean --force
   pip cache purge
   ```

2. Delete lock files and reinstall:
   ```bash
   rm package-lock.json
   npm install
   ```

3. Force Dependabot to re-scan:
   - Go to Security → Dependabot alerts
   - Click "Refresh" or wait for next scan

### Dependabot Not Creating PRs

1. Check Dependabot configuration:
   - Verify `.github/dependabot.yml` exists
   - Check if package ecosystem is supported
   - Verify directory paths are correct

2. Check repository settings:
   - Settings → Security → Dependabot
   - Ensure "Version updates" is enabled

---

## Related Files

- `.github/dependabot.yml` - Dependabot configuration
- `frontend/package.json` - Frontend dependencies
- `backend/requirements.txt` - Backend dependencies
- `.github/workflows/ci.yml` - CI/CD pipeline (may contain action vulnerabilities)

---

## References

- [GitHub Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [npm audit Documentation](https://docs.npmjs.com/cli/v8/commands/npm-audit)
- [pip-audit Documentation](https://pypi.org/project/pip-audit/)

