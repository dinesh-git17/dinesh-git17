---
name: governing-readme-structure
description: strictly enforces HTML structure, badge styles, and asset paths in the README.
version: 1.0.0
---

# 1. Purpose

To maintain the visual integrity of the profile by locking down specific HTML alignment hacks and badge styling rules that GitHub Flavored Markdown (GFM) requires for this specific layout.

# 2. Activation Conditions

- **Trigger:** Any modification to `README.md`.
- **Trigger:** Adding new tools/technologies to the "Tech Stack" section.

# 3. Scope

- **File:** `README.md` only.
- **Regions:** Header `<div align="center">`, Badge images, Footer.

# 4. Inputs

- `README.md` AST (Abstract Syntax Tree) or text content.
- List of requested technology additions (e.g., "Add Snowflake").

# 5. Behavioral Rules

- **Badge Standardization:**
  - **Socials (Header):** Must use `style=for-the-badge`. Color must be official hex. Logo color: white.
  - **Tech Stack (Body):** Must use `style=flat-square`. Logo color: white (default) or black (if low contrast).
- **Asset Handling:**
  - Images MUST use relative paths (e.g., `banner.png`) where possible.
  - External images MUST use HTTPS.
  - All `<img>` tags MUST have an `alt` attribute.
- **Alignment:**
  - Header and Footer MUST be wrapped in `<div align="center">` ... `</div>`.
  - Do NOT use `<center>` tags (deprecated).

# 6. Enforcement Logic

1.  **Parser:** Read the `README.md`.
2.  **Validator:**
    - If `style=plastic` or `style=social` is found -> **REJECT**.
    - If `banner.png` is referenced as an absolute URL -> **REJECT**.
    - If `` is missing -> **CRITICAL FAILURE**.

# 7. Forbidden Actions

- **Style Mixing:** Using different badge styles in the same section.
- **Marker Deletion:** Removing or modifying the `` comments.
- **Absolute Local Paths:** Linking to `C:/Users/...` or full GitHub raw URLs for files that exist in the repo.

# 8. Failure Conditions

- **Integrity Breach:** If automation markers are lost.
- **Style Clash:** If the user requests a style that violates the `flat-square` standard (Claude must refuse and explain the standard).
