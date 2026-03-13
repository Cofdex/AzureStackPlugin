# GitHub Copilot Instructions — AzureStackPlugin

## Hard rules

- **Never run `git commit --no-verify`** — hooks exist for a reason. If a hook fails, fix the root cause.
- **Never commit without explicit user confirmation.** Always show the full `git diff --staged` and the proposed commit message, then wait for the user to say "yes" or "commit" before running `git commit`. No exceptions.
- **Always use `uv` for Python** — no `pip`, `pip3`, `virtualenv`, or `python -m venv`. Use `uv` for everything: installs, venvs, running scripts.

---

## Repository overview

This is a **GitHub Copilot CLI plugin** — a collection of agents, skills, and hooks that extend Copilot with a multi-agent software delivery workflow for Azure Python projects.

```
agents/     ← .agent.md files — 13 single-responsibility agents
skills/     ← .skill bundles — Azure SDK code-gen skills + utility skills
hooks/      ← lifecycle hooks (continual-learning: sessionStart / postToolUse / sessionEnd)
docs/       ← workflow outputs and learning artifacts (written by agents at runtime)
plugin.json ← plugin manifest
settings.json
```

The **Orchestrator** is the sole entry point for all agent workflows. Every user request routes through `agents/orchestrator.agent.md` first — never spawn agents directly.

---

## Agent authoring

### File format

Every agent file is a `.agent.md` with YAML frontmatter followed by markdown:

```yaml
---
name: <agent-name>
description: <one-paragraph triggering description>
model: claude-opus-4.6 | claude-sonnet-4.6 | claude-haiku-4.5
tools: ["read", "edit", "execute", "agent", "microsoft-learn/*", "Context7/*", ...]
---

You are the <role>. ...

## Workflows: <comma-separated list>
## Role
...
```

### Model assignments
| Model | Used for |
|---|---|
| `claude-opus-4.6` | orchestrator, planner, architecture, security-auditor |
| `claude-sonnet-4.6` | brainstorm, implement, refactor-planner, code-reviewer, debug, tdd-suite, security |
| `claude-haiku-4.5` | regression-tester, reflection |

### Required sections (in order)
Every agent must have:
1. Frontmatter (`name`, `description`, `model`, `tools`)
2. Persona line — "You are the …"
3. `## Workflows:` — which workflows trigger this agent
4. `## Role` — what it does
5. `## MCP and skill auto-selection` — when to load which MCP server or skill
6. `## File output` — exact paths and markdown templates for every file the agent writes

### Workflow participation tags
Use exactly these strings in `## Workflows:`:
- `feature-full`, `feature-lite`, `bugfix`, `refactor`, `security`, `hotfix`

---

## Skill authoring

### Structure
```
skills/<skill-name>/
├── SKILL.md          ← frontmatter (name, description) + instructions
├── references/       ← large reference files loaded on demand
├── evals/evals.json  ← test cases
└── <name>.skill      ← packaged bundle (generated, do not edit)
```

### Packaging
```bash
python -m scripts.package_skill skills/<skill-name>
```

### SKILL.md frontmatter
```yaml
---
name: <skill-name>
description: >
  <triggering description — be specific about when to use this skill>
---
```

The `description` is the primary trigger mechanism — make it concrete, not generic.

### find-azure-skills
`skills/find-azure-skills/` maps task descriptions → correct Azure SDK skill names. It reads `references/skills-catalog.md` (52 skills). When an agent needs to identify which Azure SDK skill to load, it calls `find-azure-skills` via the `agent` tool. The result populates the `SDK skills to load:` line in `handoff.md`.

---

## Hook authoring

Hooks live in `hooks/<name>/` and are installed by copying to `.github/hooks/`:

```bash
cp -r hooks/continual-learning .github/hooks/
```

A hook directory requires:
- `hooks.json` — declares which lifecycle events to bind and the bash command to run
- The script itself (e.g., `learn.sh`)

Lifecycle events: `sessionStart`, `postToolUse`, `sessionEnd`

---

## Workflow output paths (runtime, not committed)

Agents write all outputs under `docs/workflows/<workflow-id>/`. The ID format is:
```
<type>-<short-slug>-<3-digit-counter>
# e.g. feature-translation-001, bugfix-auth-crash-001
```

ADR hierarchy:
- **Workflow ADR**: `docs/workflows/<workflow-id>/adr/<slug>.md` — scoped to one workflow
- **Global ADR**: `docs/learning/adr/<slug>.md` — promoted by Reflection Agent only when the same decision recurs in ≥ 2 distinct workflow IDs

---

## Python (for skill scripts and hooks)

- **Python version**: 3.12
- **Package manager**: `uv` exclusively

```bash
# Create venv
uv venv --python 3.12

# Install dependencies
uv pip install <package>

# Run a script
uv run python script.py

# Add to a project
uv add <package>
```

- Azure auth: always use `DefaultAzureCredential` from `azure-identity`
- Type hints required on all function signatures
- `azure-identity` is always a dependency alongside any Azure SDK skill

---

## Continual learning memory

Agents read and write two memory locations:
- `.copilot-memory/conventions.md` — human-readable project conventions (version-controlled)
- `.copilot-memory/learnings.db` — SQLite, local scope
- `~/.copilot/learnings.db` — SQLite, global scope

SQL schema for inserting a learning:
```sql
INSERT INTO learnings (scope, category, content, source)
VALUES ('local', 'mistake', '<what to avoid>', 'agent');
-- categories: pattern | mistake | preference | tool_insight
```

The Reflection Agent is the primary writer. Security Agent and Code Reviewer agents also append to `.copilot-memory/conventions.md` when they detect recurring patterns.

---

## Parallel execution model

Agents in a parallel group each write `last_heartbeat` to `project-state.md` every 5 minutes. The Orchestrator monitors heartbeats and restarts agents stale > 15 minutes. Escalate to the user if an agent crashes twice in the same sprint.

Parallel groups:
- `review-gate` (feature/bugfix): Code Reviewer + Security Agent
- `validation-gate` (refactor): Code Reviewer + Regression Tester
- `audit-scans` (security): SAST + Secrets + Dependency + Threat Modeler
