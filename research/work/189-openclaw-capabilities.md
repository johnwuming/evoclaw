# R-189: OpenClaw Multi-Agent Monitoring Capabilities

> **Date:** 2026-08-09  
> **Status:** Complete  
> **Researcher:** research-lead subagent  
> **Method:** Code reading, file exploration, README/docs analysis

---

## 1. OpenClaw CLI Monitoring Commands

**Source:** `/root/.local/share/pnpm/global/5/.pnpm/openclaw@2026.7.1-2/node_modules/openclaw/`  
**Version:** openclaw@2026.7.1-2  
**Binary entry:** `openclaw.mjs` → `dist/index.js`

### Complete CLI Command Reference (from `openclaw --help` extracted from package)

**Global Options:** `--container <name>`, `--dev`, `--log-level <silent|fatal|error|warn|info|debug|trace>`, `--no-color`, `--profile <name>`, `-V/--version`

**All 50+ Commands** (suffix `*` = has subcommands):

| Command | Category | Purpose |
|---------|----------|--------|
| `acp *` | Integration | Run an ACP bridge backed by the Gateway |
| `agent` | AI | Run an agent turn via the Gateway (use --local for embedded) |
| `agents *` | Agent Mgmt | Manage isolated agents (workspaces + auth + routing) |
| `approvals *` | Security | Manage exec approvals (gateway or node host) |
| `attach` | Integration | Attach Claude Code to a gateway session with scoped MCP tools |
| **`audit`** | **Observability** | **Inspect metadata-only agent run and tool action records** |
| `backup *` | Operations | Create and verify local backup archives |
| `capability *` | AI | Run provider capability commands (alias: infer) |
| `channels *` | Channel Mgmt | Manage connected chat channels and accounts |
| `chat` / `terminal` | UI | Open a local terminal UI (alias for tui --local) |
| `clawbot *` | Legacy | Legacy clawbot command aliases |
| `commitments *` | Task Mgmt | List and manage inferred follow-up commitments |
| `completion` | Shell | Generate shell completion script |
| `config *` | Config | Non-interactive config helpers (get/set/patch/unset/file/schema/validate) |
| `configure` | Config | Interactive configuration wizard |
| `crestodian` | Setup | Ring-zero setup and repair helper |
| **`cron *`** | **Scheduling** | **Manage cron jobs (via Gateway)** |
| `daemon *` | Service | Manage the Gateway service (launchd/systemd/schtasks) |
| `dashboard` | UI | Open the Control UI with your current token |
| `devices *` | Device Mgmt | Device pairing and auth tokens |
| `directory *` | Contacts | Lookup contact and group IDs |
| `dns *` | Network | DNS helpers for wide-area discovery (Tailscale + CoreDNS) |
| `docs` | Help | Search the live OpenClaw docs |
| **`doctor`** | **Health** | **Health checks + quick fixes for the gateway and channels** |
| `exec-approvals *` / `exec-policy *` | Security | Exec approval management |
| **`gateway *`** | **Core** | **Run, inspect, and query the WebSocket Gateway** |
| **`health`** | **Monitoring** | **Fetch health from the running gateway** |
| `hooks *` | Internals | Manage internal agent hooks |
| `infer *` | AI | Run provider-backed inference commands |
| **`logs`** | **Monitoring** | **Tail gateway file logs via RPC** |
| `mcp *` | Integration | Manage mcp.servers config and channel bridge |
| **`memory *`** | **State** | **Search, inspect, and reindex memory files** |
| `message *` | Messaging | Send, read, and manage messages and channel actions |
| `migrate *` | Import | Import state from another agent system |
| **`models *`** | **AI** | **Model discovery, scanning, and configuration** |
| `node *` | Node | Run and manage the headless node host service |
| **`nodes *`** | **Device** | **Manage gateway-owned nodes (pairing, status, invoke, media)** |
| `onboard` / `setup` | Setup | Guided setup for auth, models, Gateway, workspace, channels, skills |
| `pairing *` | Security | Secure DM pairing (approve inbound requests) |
| `plugins *` | Extension | Manage OpenClaw plugins and extensions |
| `promos *` | Offers | Discover and claim promotional model offers from ClawHub |
| `proxy *` | Debug | Run the OpenClaw debug proxy and inspect captured traffic |
| `qr` | Setup | Generate a mobile pairing QR code and setup code |
| `reset` | Operations | Reset local config/state (keeps the CLI installed) |
| **`sandbox *`** | **Security** | **Manage sandbox containers (Docker-based agent isolation)** |
| `secrets *` | Security | Secrets runtime controls |
| **`security *`** | **Security** | **Audit local config and state for security foot-guns** |
| **`sessions *`** | **Session** | **List stored conversation sessions** |
| `skills *` | Skills | List and inspect available skills |
| **`status`** | **Monitoring** | **Show channel health and recent session recipients** |
| **`system *`** | **System** | **System tools (events, heartbeat, presence)** |
| **`tasks *`** | **Task Mgmt** | **Inspect durable background tasks and TaskFlow state** |
| **`transcripts *`** | **Observability** | **Inspect stored transcripts** |
| `tui` | UI | Open a terminal UI connected to the Gateway |
| `uninstall` | Operations | Uninstall the gateway service + local data |
| `update *` | Operations | Update OpenClaw and inspect update channel status |
| `webhooks *` | Integration | Webhook helpers and integrations |
| `worktrees *` | Dev | Create, inspect, restore, and clean up managed worktrees |

### Monitoring-Relevant Commands (Key for Multi-Agent Monitoring)

| Command | Purpose |
|---------|--------|
| `openclaw status` | Show channel health and recent session recipients |
| `openclaw health` | Fetch health from the running gateway |
| `openclaw doctor` | Health checks + quick fixes for the gateway and channels |
| `openclaw logs` | Tail gateway file logs via RPC |
| **`openclaw system events`** | **System event monitoring** |
| **`openclaw system heartbeat`** | **Heartbeat monitoring (native CLI support!)** |
| **`openclaw system presence`** | **Presence monitoring** |
| `openclaw sessions list` / `--json` | List stored conversation sessions |
| `openclaw tasks` | Inspect durable background tasks and TaskFlow state |
| `openclaw audit` | Inspect agent run and tool action records |
| `openclaw transcripts` | Inspect stored transcripts |
| `openclaw agents list` | List configured agents |
| `openclaw cron list` | List cron jobs |
| `openclaw models status` | Show model/provider auth health |
| `openclaw channels status` | See connected messaging accounts and login state |

### Chat Commands (in-session)

`/status`, `/new`, `/reset`, `/compact`, `/think <level>`, `/verbose on|off`, `/trace on|off`, `/usage off|tokens|full`, `/restart`, `/activation mention|always`

### Session/Agent Tools (available to agents)

- `sessions_list` — List sessions with filters (kind, label, agentId, search, activity, archived)
- `sessions_history` — Fetch history for a session
- `sessions_send` — Send a message to a session
- `sessions_spawn` — Spawn sub-agents or ACP sessions
- `subagents` — List active/recent subagents for current session

### Key Architectural Concepts

- **Gateway:** Single control plane for sessions, channels, tools, and events
- **Multi-agent routing:** Inbound channels/accounts/peers routed to isolated agents
- **Session model:** Each agent has isolated sessions; `updatedAt` timestamp refreshes on every token
- **Sandboxing:** Non-main sessions can run in Docker/SSH/OpenShell sandboxes
- **Config location:** `~/.openclaw/openclaw.json` (not `config.yaml` — this instance has no config file at standard paths)

---

## 2. Agent Dashboard Project

**Location:** `/root/.openclaw/workspace/tools/agent-dashboard/`  
**Version:** 4.0.0  
**Stack:** Express + `node:sqlite` (Node 22 built-in), single-file server (~5000+ lines)  
**Port:** 8055  
**Description:** "Agent Dashboard V4 — Task Center (Express + node:sqlite, no native deps)"

### Dashboard API Endpoints

#### Project Management
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/projects` | GET | List projects (with task counts) |
| `/api/projects/:id` | GET | Project detail with tasks |
| `/api/projects` | POST | Create project |
| `/api/projects/:id` | PUT | Update project |
| `/api/projects/:id` | DELETE | Delete (only cancelled/archived) |
| `/api/projects/:id/review` | POST | Approve/reject project |
| `/api/projects/:id/open` | POST | Open project dir in VS Code |
| `/api/projects/:id/docs` | GET | Scan .md files in project |

#### Task Management
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/tasks` | GET | List tasks (filter by project/status/type) |
| `/api/tasks/:id` | GET | Task detail with events |
| `/api/tasks` | POST | Create task (auto R-number for research) |
| `/api/tasks/:id` | PUT | Update task (state transitions) |
| `/api/tasks/:id/dispatch` | POST | Submit to dispatch queue |
| `/api/tasks/:id/retry` | POST | Retry failed task |
| `/api/tasks/:id/pause` | POST | Pause task |
| `/api/tasks/:id` | DELETE | Delete task |

#### Agent & Monitoring (Key for Multi-Agent Monitoring)
| Route | Method | Purpose |
|-------|--------|---------|
| **`/api/agents`** | GET | **Real agent status from OpenClaw CLI** — queries `openclaw sessions --json` |
| **`/api/stats`** | GET | **Dashboard statistics** — aggregate task/project counts |
| **`/api/dispatch-status`** | GET | **Team blocking/pending status** — serial control |
| `/api/reports` | GET | List research reports |
| `/api/reports/:id` | GET | Read report content |

#### Quota/Resource Monitoring
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/zai-quota` | GET | 智谱 GLM Coding Plan quota |
| `/api/zai-quota/refresh` | POST | Force refresh 智谱 quota |
| `/api/volc-quota` | GET | 火山引擎 Agent Plan quota |
| `/api/volc-quota/refresh` | POST | Force refresh 火山 quota |
| `/api/deepseek-quota` | GET | DeepSeek balance |
| **`/api/hp-stats`** | GET | **HP-800G1 compute node stats** (hardware monitoring) |

#### Internal Endpoints
| Route | Method | Purpose |
|-------|--------|---------|
| `/internal/dispatch` | POST | Trigger spawn cycle (auth required) |
| `/internal/review` | POST | Submit review decision (auth required) |

### Database Schema (SQLite)

```
projects:     id, name, slug, status, description, repo_path, deployed_url
tasks:        id, project_id, title, type, status, priority, expected_output,
              assigned_agent, spawn_config, dispatched_at, completed_at,
              parent_task_id, retry_count, max_retries, completion_summary,
              review_summary, spawn_error, agent_session_key, task_prompt
task_events:  task_id, event, detail, ts
agent_status: agent_id, role, status, current_task_id, token_usage
counters:     auto-increment IDs (task-0001, proj-0001)
```

### Agent Tab UI Component

The frontend is a **single-page app embedded in server.js** (no separate React/Vue build).  
6 tabs via bottom navigation:

1. **项目 (Projects)** — Project cards with expand/collapse
2. **任务 (Tasks)** — Kanban board (pending/running/review/done/failed)
3. **用量 (Usage)** — 智谱/火山/DeepSeek quota progress bars + HP-800G1 stats
4. **Agents** — Team-grouped agent cards (research/dev/ops)
5. **研究报告 (Reports)** — Report list with detail viewer + TOC
6. **量化 (Quant)** — Backtest nav curve (SVG), factor table, evolution timeline

**UI Features:** Dark/light theme, glassmorphism, pull-to-refresh, FAB, mobile keyboard adaptation, font size control, Apple HIG-style design.

### Spawn Architecture (R-126)

- **Dev tasks** → `spawnAgentViaCLI()` using `openclaw cron add --agent claude`
- **Research/Quant tasks** → `spawnAgentViaGateway()` using gateway HTTP API `/tools/invoke`
- **Team serial control:** Each team (research/dev/quant/ops) max 1 running task
- **Spawn failures:** 3 consecutive failures → `failed_final` status

---

## 3. dispatch.js — Timeout Detection Mechanism

**Location:** `/root/.openclaw/workspace/tools/agent-dashboard/dispatch.js`  
**Schedule:** Every 2 minutes via system crontab (`node dispatch.js`)

### 4-Step Pipeline

#### Step 1: `processCompletions()`
- Reads `.task-completions.jsonl`
- Validates deliverables exist
- Marks completed tasks as `pending_review`

#### Step 2: `detectEndedSessions()` — **KEY TIMEOUT MECHANISM**
- Queries all `running` tasks
- For each task with `agent_session_key`, fetches session data via `openclaw sessions --json`
- **Core logic:** If `now - session.updatedAt > graceMinutes` → session has ended
  - Running sessions refresh `updatedAt` on every token
  - When `updatedAt` freezes, the session is considered terminated
- **Team grace periods:**
  - research: **30 minutes**
  - dev: **30 minutes**
  - quant: **30 minutes**
  - ops: **5 minutes**
- **Decision matrix:**
  - Session ended + deliverable ready → `pending_review`
  - Session ended + deliverable missing → `failed`
  - Session not found within 24h → considered lost → same logic
  - No session_key + elapsed > 3× max grace → timeout

#### Step 3: `retryFailed()`
- Auto-retries `failed` tasks if `retry_count < max_retries`
- Returns them to `pending` status

#### Step 4: `processPendingReview()`
- Triggers `POST /internal/dispatch` on server.js
- Spawns next pending tasks

### Key Design Insight
The timeout detection relies on **`updatedAt` freezing** as a reliable signal of session termination. The principle: "running sessions refresh `updatedAt` on every token" — so a frozen timestamp means the session stopped generating output.

---

## 4. Heartbeat, Cron, and Session Management Mechanisms

### 4.1 Heartbeat System

**Concept:** Periodic polling mechanism for proactive agent behavior.

- **HEARTBEAT.md** — Optional checklist file agents can edit; not present on this instance
- **Trigger:** Configured heartbeat prompt (typically every ~30 min)
- **Response:** Agent can do proactive work (check emails, calendar, weather) or return `HEARTBEAT_OK`
- **Heartbeat vs Cron distinction:**
  - **Heartbeat:** Batch checks, needs conversational context, timing can drift
  - **Cron:** Exact timing, task isolation, different model/thinking level, one-shot reminders
- **State tracking:** `memory/heartbeat-state.json` with `lastChecks` timestamps

### 4.2 Cron System

**CLI:** `openclaw cron add --agent <name>`  
**Skill:** `lightclaw-cron` (LightClawBot scheduled reminders)  
**Use cases:**
- One-time reminders ("remind me in 20 minutes")
- Recurring schedules ("9:00 AM every Monday")
- Isolated task execution outside main session
- Agent spawning (`openclaw cron add --agent claude` — used by dashboard)

**Runtime module:** `cron-store-runtime` (in plugin-sdk exports)

### 4.3 Session Management

**CLI:** `openclaw sessions --json`, `openclaw sessions list`  
**Agent tools:** `sessions_list`, `sessions_history`, `sessions_send`, `sessions_spawn`

**Session types:**
- Main session (direct chat with human)
- Sub-agent sessions (`sessions_spawn` with `runtime: "subagent"`)
- ACP harness sessions (`sessions_spawn` with `runtime: "acp"` for Claude Code, Cursor, etc.)
- Detached sessions (via TaskFlow)

**Session lifecycle:**
- `updatedAt` timestamp refreshes on every token generated
- Sessions can be listed, inspected, and their history fetched
- Sub-agents auto-announce completion to parent sessions (push-based, not polling)
- Session depth limits apply (this instance: depth 2/4)

### 4.4 TaskFlow (Durable Multi-Step Jobs)

**Skill:** `taskflow`  
**Purpose:** Coordinate multi-step detached tasks as one durable job  
**Key features:**
- Owner session context preserved
- State persistence between steps (`stateJson`)
- Revision tracking for conflict-safe mutations
- Wait/resume/cancel lifecycle
- Linked child tasks

**Lifecycle:**
1. `createManaged(...)` → 2. `runTask(...)` → 3. `setWaiting(...)` → 4. `resume(...)` → 5. `finish(...)/fail(...)`

### 4.5 Sub-Agent Architecture

**Spawning:** `sessions_spawn` creates child sessions  
**Auto-announce:** Completions are push-based (arrive as user messages to parent)  
**Depth limits:** Configured max depth (this instance: 4)  
**Capabilities:** Sub-agents may have restricted capabilities (this instance: `capabilities=none` — no shell exec)

---

## 5. Configuration Files Found

| Path | Status |
|------|--------|
| `~/.openclaw/openclaw.json` | **NOT FOUND** (expected main config) |
| `~/.openclaw/config.yaml` | NOT FOUND |
| `~/.openclaw/config.json` | NOT FOUND |
| `~/.openclaw/gateway.yaml` | NOT FOUND |
| `~/.openclaw/HEARTBEAT.md` | NOT FOUND |
| `~/.openclaw/cron.json` | NOT FOUND |
| `~/.openclaw/schedules.json` | NOT FOUND |
| `~/.openclaw/timers.json` | NOT FOUND |
| `~/.openclaw/workspace-research/MEMORY.md` | NOT FOUND |
| `~/.openclaw/workspace-research/AGENTS.md` | ✅ Exists (loaded in project context) |
| `~/.openclaw/workspace-research/TOOLS.md` | ✅ Exists (loaded in project context) |

---

## 6. OpenClaw Package Structure

**Installed at:** `/root/.local/share/pnpm/global/5/.pnpm/openclaw@2026.7.1-2/node_modules/openclaw/`  
**Key directories:**
- `dist/` — Compiled JavaScript (main distribution)
- `dist/plugin-sdk/` — Plugin SDK with runtime modules
- `dist/extensions/` — Channel/provider extensions (discord, slack, whatsapp, qqbot, etc.)
- `skills/` — Bundled skills (taskflow, tmux, weather, cron, healthcheck, etc.)
- `docs/` — Documentation
- `src/agents/templates/` — Agent template files

**Key plugin-sdk modules relevant to monitoring:**
- `cron-store-runtime` — Cron job storage/management
- `config-runtime` — Configuration access
- `runtime` — Core runtime access
- `health` — Health check module
- `runtime-doctor` — Runtime diagnostics
- `session` related modules — Session management

---

## 7. Summary: Existing Multi-Agent Monitoring Capabilities

### What Already Exists
1. **Dashboard server** (`/api/agents`) queries OpenClaw CLI for real-time agent status
2. **dispatch.js** runs every 2 min, detects timed-out sessions via `updatedAt` freezing
3. **30-minute inactivity timeout** for research/dev/quant teams (5 min for ops)
4. **Task state machine:** pending → running → pending_review → done / failed
5. **Auto-retry** with configurable `max_retries`
6. **Team serial control:** Max 1 running task per team
7. **Quota monitoring:** 智谱/火山/DeepSeek API quotas
8. **Hardware monitoring:** HP-800G1 stats via `/api/hp-stats`
9. **OpenClaw native:** `sessions_list`, `sessions_history`, `subagents` tools
10. **Session `updatedAt`** as liveness signal (refreshes on every token)

### Gaps / Opportunities
- No `openclaw.json` config found at standard path (may be elsewhere)
- No HEARTBEAT.md or MEMORY.md configured
- Dashboard is a custom project, not part of OpenClaw core
- dispatch.js timeout detection (30 min) is coarse-grained
- No real-time WebSocket push for agent status changes (dashboard polls)
- Sub-agents in this environment have `capabilities=none` (no shell exec)
