---
name: auditing-workflow-security
description: Enforces OSSF Scorecard standards and security best practices for GitHub Actions workflows.
version: 1.0.0
---

# 1. Purpose

To prevent supply chain attacks and credential leaks by enforcing strict security rules on `.github/workflows/*.yml` files before they are committed.

# 2. Activation Conditions

- **Trigger:** Any modification to files in `.github/workflows/`.
- **Trigger:** Creation of new workflow files.

# 3. Scope

- **Files:** `*.yml` / `*.yaml` inside `.github/`.
- **Concepts:** permissions, secrets, action versions, script injection.

# 4. Inputs

- Content of the workflow file being edited.

# 5. Behavioral Rules

- **Least Privilege:** All workflows MUST specify `permissions:`. If the workflow only reads code, use `permissions: read-all` or `contents: read`.
- **Pinning:** 3rd-party Actions (e.g., `actions/checkout`) SHOULD be pinned by SHA (e.g., `@a5ac7...`) for maximum security, or at minimum by major version (`@v4`).
- **Script Safety:** Inline scripts using `${{ ... }}` values MUST use intermediate environment variables to prevent script injection.

# 6. Enforcement Logic

1.  **Scan:** Check for `permissions:`. If missing -> **BLOCK**.
2.  **Scan:** Check for `secrets.GITHUB_TOKEN` usage. Ensure it's not passed to untrusted scripts.
3.  **Scan:** Check for `curl | bash` patterns. If found -> **WARN** or **BLOCK**.

# 7. Forbidden Actions

- **All-Access Pass:** Leaving `permissions` undefined (defaults to read/write in older repos).
- **Hardcoded Secrets:** Committing plaintext API keys or credentials.
- **Writable Workflows:** Allowing `workflow_dispatch` on a workflow that writes to the repo without branch protection checks.

# 8. Failure Conditions

- **Security Risk:** Finding `permissions: write-all`.
- **Injection Risk:** Finding `run: echo "${{ github.event.issue.title }}"` (direct interpolation).
- **Remediation:** Claude must refuse to commit and instead output the corrected, secure YAML.

# 9. Examples

- _Bad:_ `run: echo "Hello ${{ inputs.name }}"`
- _Good:_
  ```yaml
  env:
    NAME: ${{ inputs.name }}
  run: echo "Hello $NAME"
  ```
