# GitHub Actions workflow IDE warnings

In VS Code (and similar editors), the GitHub Actions extension may show **"Context access might be invalid"** for expressions like `${{ secrets.ORACLE_HOST }}` or `${{ vars.BACKEND_URL }}` in `.github/workflows/*.yml`.

These are **false positives**. The extension only knows about built-in contexts (`github`, `env`, `secrets.GITHUB_TOKEN`). Your repo’s custom **Secrets and variables** (configured under **Settings → Secrets and variables → Actions**) are valid at runtime; the linter just can’t see them.

- **Action:** None required. The workflows run correctly in GitHub.
- **To hide the warnings:** You can treat workflow files as plain YAML in VS Code (loses Actions IntelliSense):
  ```json
  "files.associations": {
    ".github/workflows/*.yml": "yaml"
  }
  ```
  Use only if the warnings are too noisy.

See: [vscode-github-actions #222](https://github.com/github/vscode-github-actions/issues/222).
