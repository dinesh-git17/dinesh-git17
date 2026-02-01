---
name: synchronizing-portfolio-state
description: Fetches live data from linked repositories to keep the portfolio project list accurate.
version: 1.0.0
allowed-tools: [bash, git, gh]
---

# 1. Purpose

To ensure the "Projects" section of `README.md` reflects reality, not hallucination, by validating project descriptions and topics against the actual linked repositories.

# 2. Activation Conditions

- **Trigger:** User asks to "update projects," "add [Repo Name]," or "sync portfolio."
- **Trigger:** Scheduled audit of project links.

# 3. Scope

- **Read:** Remote GitHub repository metadata (description, topics, stars).
- **Write:** "Projects" section of `README.md`.

# 4. Inputs

- List of repository URLs mentioned in `README.md`.
- `gh` CLI (GitHub CLI) installed in the environment.

# 5. Behavioral Rules

- **Single Source of Truth:** The repository's _actual_ GitHub description overrides any manual text in the README _unless_ the user provides a specific manual override.
- **Format:** `**[Name](URL)** description.`
- **Verification:** Before adding a project, check if the URL returns 404.
- **Topic Sync:** If the repo has GitHub Topics (e.g., `data-engineering`, `python`), consider adding them as context in the description.

# 6. Enforcement Logic

1.  **Extract URLs:** Parse `README.md` for `github.com/dinesh-git17/*`.
2.  **Fetch Metadata:** Execute `gh repo view <url> --json description,topics`.
3.  **Diff:** Compare fetched description with README text.
4.  **Update:** If significantly different, propose an update to match the repo's "About" section.

# 7. Forbidden Actions

- **Dead Links:** Adding a project without verifying the URL exists.
- **Private Repos:** Exposing private repository details without explicit "Public" verification.
- **Fabrication:** Inventing features for a project that are not listed in its topics or description.

# 8. Failure Conditions

- **API Failure:** If `gh` CLI fails or is unauthenticated, abort the sync and report the error.
- **Mismatch:** If the repo does not belong to `dinesh-git17` (prevent accidental promotion of random repos).

# 9. Examples

- _Action:_ User says "Add my Claude Home repo."
- _Execution:_ Claude runs `gh repo view dinesh-git17/claudehome`, gets description "Explores architectural persistence...", and formats the Markdown entry automatically.
