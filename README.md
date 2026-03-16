# AzureStackPlugin

A multi-agent software delivery workflow for Azure Python projects. Provides 13 single-responsibility agents, 53 Azure SDK skills, and a continual-learning hook system — all orchestrated through a structured pipeline that covers feature delivery, bugfixes, refactoring, and security audits.

---

## Agents

13 agents, each with a single responsibility. The **Orchestrator** is the sole entry point — all requests are classified and routed from there.

| Agent | Role |
|---|---|
| `orchestrator` | Classifies requests, spawns agents, manages barriers, escalates blockers |
| `brainstorm` | Gathers requirements via Q&A with the user (feature-full path only) |
| `architecture` | Designs technical architecture from `brainstorm-report.md` |
| `planner` | Decomposes architecture into sprints; verifies each sprint after completion |
| `tdd-suite` | Writes failing pytest tests before implementation (red phase) |
| `implement` | Sole code author — writes production code to pass tests |
| `code-reviewer` | Reviews code quality, logic, and structure (per sprint, parallel) |
| `security` | Per-sprint security check — injection, secrets, auth, CVEs (parallel) |
| `debug` | Traces bugs to root cause, writes failing repro tests |
| `refactor-planner` | Plans behavior-preserving refactors in small, reversible sprints |
| `regression-tester` | Verifies no behavior change after each refactor sprint |
| `security-auditor` | Full security audit across SAST, secrets, dependencies, threat model |
| `reflection` | Records learnings and patterns after each committed sprint |

---

## Workflows

```
feature-full   Brainstorm → Architecture → Planner → [TDD] → Implement → [Review ∥ Security] → Reflection
feature-lite   Planner → Implement → [Review ∥ Security] → Reflection
bugfix         Debug → Planner → Implement → [Review ∥ Security] → Reflection
refactor       Refactor Planner → Implement → [Review ∥ Regression] → Reflection
security       Security Auditor (SAST ∥ Secrets ∥ Dependencies ∥ Threat Model) → consolidated report
hotfix         Implement → [Review ∥ SAST ∥ Secrets]
```

| Workflow | When |
|---|---|
| `feature-full` | > 2 modules, new external service, security implication, or > 3 days |
| `feature-lite` | Feature request not meeting `feature-full` criteria |
| `bugfix` | Incorrect behavior, reproducible |
| `refactor` | Structural change, no behavior change |
| `security` | Full or partial codebase audit |
| `hotfix` | Emergency patch, 1–2 files |

---

## Skills

53 Azure SDK skills loaded on-demand by the Implement Agent. Each skill provides correct SDK patterns, auth idioms, and error handling for its service.

| Category | Skills |
|---|---|
| **AI / Foundry** | `azure-openai`, `azure-ai-projects`, `agent-framework-azure-ai`, `container-agents-azure-ai`, `azure-ai-ml`, `azure-foundry-evaluations` |
| **Cognitive Services** | `azure-ai-search`, `azure-ai-textanalytics`, `azure-ai-document-intelligence`, `azure-ai-vision-imageanalysis`, `azure-ai-face`, `azure-ai-transcription`, `azure-speech-stt-rest`, `azure-ai-voicelive`, `azure-ai-translation-text`, `azure-ai-translation-document`, `azure-ai-contentsafety`, `azure-ai-contentunderstanding`, `azure-ai-video-indexer` |
| **Storage / Data** | `azure-blob-storage`, `azure-datalake`, `azure-file-shares`, `azure-queue-storage`, `azure-data-tables`, `azure-cosmos`, `azure-cosmos-mongodb`, `azure-sql`, `azure-postgres-flexible`, `azure-redis` |
| **Messaging** | `azure-service-bus`, `azure-event-hubs`, `azure-event-grid`, `azure-notification-hubs` |
| **Compute** | `azure-functions`, `azure-container-apps`, `azure-aks`, `azure-containerregistry` |
| **Security / Config** | `azure-identity`, `azure-keyvault`, `azure-appconfiguration` |
| **Networking** | `azure-apim`, `azure-communication-services`, `azure-digital-twins` |
| **Observability** | `azure-application-insights`, `azure-monitor-query`, `azure-monitor-ingestion`, `azure-devops-sdk` |
| **Infrastructure** | `azure-architecture-patterns`, `azure-bicep`, `azure-terraform` |
| **Python** | `fastapi-crud`, `pydantic-models` |
| **Plugin** | `find-azure-skills`, `continual-learning` |

---

## Python Tooling

This plugin uses [uv](https://docs.astral.sh/uv/) for Python package management and test execution.

Install dependencies:
```bash
uv add <package>
```

Run tests:
```bash
uv run pytest
```

---

## Continual Learning

A hook system persists cross-session knowledge to SQLite:

- **Global** (`~/.copilot/learnings.db`) — patterns across all projects
- **Local** (`.copilot-memory/learnings.db`) — patterns specific to this repo

Hooks fire at `sessionStart` (loads prior knowledge), `postToolUse` (logs outcomes), and `sessionEnd` (analyzes patterns, compacts data).

Install by copying the hook into your project:
```bash
cp -r hooks/continual-learning .github/hooks/
```

---

## License

MIT — see [LICENSE](LICENSE).