# JARVIS Universal Agent — Production Architecture

## Executive Summary

JARVIS is an autonomous digital worker that:
- **Operates** your computer (OS automation, browser control, application manipulation)
- **Thinks** with any LLM (online via OpenRouter/FreeeLLMAPI/etc, offline via Ollama/LM Studio)
- **Speaks** naturally with local voice (VoiceStudio + fallbacks)
- **Remembers** persistently via SQLite + semantic memory
- **Decides** with evidence-based confidence, asking when uncertain
- **Recovers** from failures with checkpointed state and alternative strategies
- **Proves** every consequential action with traceability and audit

**Design Principle:** Privacy-first, reliability-obsessed, vendor-agnostic, offline-capable, provenance-aware.

---

## 1. CORE ARCHITECTURE LAYERS

### 1.1 Brain Layer (LLM Abstraction)

```
┌─────────────────────────────────────────────────────────────────┐
│                      ARBITER (Brain Router)                      │
│  - Auto-detect connectivity (AUTO / LAND / SEA / OVERRIDE)      │
│  - Capability registry (vision, tool-use, token-limit, latency) │
│  - Best-bee-for-job routing (verified perf, not model size)     │
│  - Cost/latency tracking & configurable limits                  │
└──────────────────┬──────────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
   ┌────▼───┐ ┌───▼────┐ ┌───▼──────┐
   │ ONLINE │ │ OFFLINE│ │ FALLBACK │
   │ Models │ │ Models │ │ Chain    │
   └────┬───┘ └───┬────┘ └───┬──────┘
        │         │          │
   ┌────▼─────────▼──────────▼────┐
   │  Unified LLM Client           │
   │  (streaming, tool-use, vision)│
   └───────────────────────────────┘
```

**Online APIs (LAND mode):**
- OpenRouter (primary aggregator)
- FreeeLLMAPI
- OmniRoute
- Groq, Together.ai, Claude API (user choice)
- Custom endpoints (user-configured)

**Offline Models (SEA mode):**
- Ollama (local discovery & management)
- LM Studio (alternative local runner)
- Pre-pulled models stored locally

**Fallback Chain (AUTO mode):**
1. Try configured primary API
2. Fall back to secondary APIs by latency/reliability
3. Fall back to offline Ollama if online APIs fail
4. Degrade gracefully (text-only if vision unavailable, etc.)

**Capability Registry:**
- Maintains metadata for each model: vision, tool-use, context window, latency, cost/1M tokens
- Rejects models incapable of required task
- Routes by capability, not blind model name

**Cost & Privacy Tracking:**
- Track cumulative cloud API spend per mission
- Enforce configurable spend limits (e.g., max $10/mission)
- Alert before exceeding limits; never silently spend
- Route sensitive tasks to offline models only

---

### 1.2 Memory Layer

```
┌──────────────────────────────────────────┐
│    AUTHORITATIVE STATE (SQLite)          │
│  - Mission log & execution history       │
│  - Task checkpoints & resume state       │
│  - Action log with evidence (screenshots)│
│  - Audit trail (what happened, why)      │
└──────────────────────────────────────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
    ┌────▼─────────────┐         ┌────────▼────────┐
    │ SEMANTIC INDEX   │         │  SECRETS STORE  │
    │ (Vector/Chroma)  │         │  (OS Keyring)   │
    │ - Knowledge base │         │  - API keys     │
    │ - Doc summaries  │         │  - Passwords    │
    │ - SourceFinder   │         │  - Credentials  │
    │   provenance     │         │                 │
    └──────────────────┘         └─────────────────┘
```

**SQLite (Operational Truth):**
- Mission history with original intent, decomposition, status
- Checkpoint state (what's done, what's pending, resume point)
- Action evidence: screenshots, logs, output, errors
- Audit trail: who requested what, when, why, what was the outcome
- User-controlled archival/forgetting (not auto-deletion)

**Semantic/Vector Memory (Knowledge):**
- Indexed documents, research summaries, knowledge base
- SourceFinder-style provenance: always remember the source URL/file/timestamp
- Enables: "What did I learn about X?" and "Where did I find that?"
- Sits alongside SQLite, never replaces it

**Secrets Management:**
- API keys → OS credential manager (Windows: Data Protection API)
- Never in logs, env vars, or source code
- Accessible only via authenticated JARVIS session

**Privacy by Default:**
- Sensitive data (PII, financial, auth tokens) automatically redacted in logs
- User can mark missions/documents as private (offline-only processing)
- Clear audit of what data touched which APIs

---

### 1.3 Computer Control Layer

```
┌────────────────────────────────────────────────────────┐
│              ACTION EXECUTOR                           │
│  Priority: UIA/Accessibility → API → Keyboard/Mouse   │
│  Evidence: Screenshot on important actions & failures  │
└────────────────────────┬───────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼────┐     ┌────▼────┐    ┌────▼────┐
    │ UIA      │     │ Browser │    │ Generic  │
    │ Windows  │     │ CDP     │    │ GUI      │
    │ Apps     │     │ Chrome  │    │ (Mouse/  │
    │ (native) │     │         │    │ Keyboard)│
    └──────────┘     └─────────┘    └──────────┘
```

**UIA/Accessibility First (Windows UI Automation):**
- Query window hierarchies, buttons, text fields
- Read accessibility tree (no OCR needed for text)
- Inspect element properties, states, bounds
- Preferred: most reliable, fastest, requires no vision

**Application-Specific APIs:**
- Office COM API (Excel, Word, Outlook)
- Browser CDP (Chrome/Edge on port 9222)
- Git CLI, FFmpeg, system APIs
- Custom integrations for frequently-used apps

**Browser Automation (CDP):**
- Chrome DevTools Protocol for browser control
- JavaScript execution, DOM queries
- Screenshot + network inspection

**Fallback: Vision + OCR + Mouse/Keyboard:**
- When apps don't expose APIs
- Screenshot → OCR/layout analysis → coordinate inference
- Human-like cursor movement (or fastest-safe adaptive timing)
- Used when necessary, not by default

**Evidence & Traceability:**
- Screenshot on-demand (before important actions)
- Auto-capture on failure for debugging
- NOT continuous streaming (too expensive, unnecessary)
- All actions logged with timestamp, coordinates, app context
- Failed attempts preserved in audit for diagnosis

---

### 1.4 Voice Layer

```
┌───────────────────────────────────────────────────┐
│         VOICE PROVIDER ABSTRACTION                │
│  - VoiceStudio (local-first, if available)       │
│  - Windows SAPI fallback (system TTS/STT)        │
│  - Future: other providers (plug in at runtime)  │
└──────────────────┬────────────────────────────────┘
                   │
         ┌─────────┼─────────┐
         │         │         │
    ┌────▼──┐ ┌────▼───┐ ┌──▼─────┐
    │Speech │ │ Stream │ │Barge-in│
    │Recog  │ │Synthesis│ │Interrupt│
    │(STT)  │ │ (TTS)   │ │Support  │
    └───────┘ └────────┘ └─────────┘
```

**Input (Speech-to-Text):**
- Push-to-talk (initial mode): explicit activation
- Wake-word/always-listening (future mode)
- Confidence threshold: if <threshold, ask for clarification ("I didn't catch that. Can you repeat?")
- Streaming support (future: mid-sentence barge-in)

**Output (Text-to-Speech):**
- Multiple voice profiles (personas, tone, language)
- Voice cloning support (if VoiceStudio provides it)
- Streaming delivery (real-time playback)

**Provider Abstraction:**
- JARVIS doesn't know or care if it's VoiceStudio, SAPI, or Elevenlabs
- `VoiceProvider` interface: `transcribe()`, `synthesize()`, `set_voice()`
- Fallback chain: try primary provider, fall back to SAPI/system TTS

**Failure Modes:**
- Voice unavailable → drop to text mode (CLI/dashboard text only)
- Speech recognition fails → offer text input fallback
- No audio output → text output only
- System always remains functional

---

### 1.5 Mission Engine

```
┌──────────────────────────────────────────────────┐
│            MISSION PLANNER                       │
│  - Decompose user intent → task tree             │
│  - Resource-aware scheduling                     │
│  - Checkpoint boundaries (mission/task/subtask)  │
└──────────────────┬───────────────────────────────┘
                   │
         ┌─────────┴────────┐
         │                  │
    ┌────▼─────┐      ┌─────▼───┐
    │ EXECUTOR  │      │VERIFIER  │
    │ (Workers) │      │(Evidence)│
    └────┬──────┘      └────┬─────┘
         │                  │
    ┌────▼──────────────────▼─────┐
    │ CHECKPOINT STORE (SQLite)    │
    │ - Resumable state            │
    │ - Completed subtasks         │
    │ - Artifacts generated        │
    └──────────────────────────────┘
```

**Decomposition:**
- User mission → high-level task breakdown
- Estimate resource/time budgets
- Bounded depth (max levels, loop limits, timeout per subtask)
- Ambiguous tasks → ask for clarification before proceeding

**Execution Policy:**
- **Autonomous work:** normal, safe operations (research, document creation, etc.)
- **Confirmation required:** destructive (delete/rm), financial (payment/purchase), security-altering (permissions), genuinely ambiguous
- Policy is user-configurable per mission type

**Error Handling:**
1. Immediate failure → retry with backoff (configurable max retries)
2. Persistent failure → diagnose (log evidence, analyze error)
3. Retry alternative strategy (different approach, different tool)
4. Escalate to alternative worker/bee
5. Report honestly to user with evidence

**Checkpointing:**
- Resume from last verified checkpoint on crash
- Boundaries: mission start, task completion, subtask completion
- Checkpoint includes: completed artifact hashes, next pending task ID
- On resume, verify completed work before proceeding

**Modification Policy:**
- JARVIS may adapt its plan if evidence demands it
- Must preserve original mission intent
- Document changes in audit trail

---

### 1.6 Worker/Agent Architecture (HiveVerse)

```
┌─────────────────────────────────────┐
│    COMMANDER (Mission Executive)    │
│    - Dispatch tasks to workers      │
│    - Coordinate multi-worker flows  │
│    - Escalate failures              │
└────────────────────┬────────────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼────┐     ┌─────▼──┐       ┌────▼────┐
│Core Bee │     │Content │       │Research │
│(Generic)│     │Bee     │       │Bee      │
│ Control │     │(GPTzuu)│       │(Analysis)
│Executor │     │        │       │         │
└────┬────┘     └────┬───┘       └────┬────┘
     │               │               │
     └───────┬───────┴───────┬───────┘
             │               │
         ┌───▼────┐      ┌───▼────┐
         │Document │      │Browser/│
         │Bee      │      │Network │
         │(Office) │      │Bee     │
         └─────────┘      └────────┘
```

**Commander:**
- Receives mission from user
- Parses intent, creates task DAG
- Dispatches to appropriate workers
- Monitors progress, handles escalation
- Reports completion/failure

**Workers (Bees):**
Each specialized for a domain:
- **Core Bee:** Generic computer control, system operations
- **Document Bee:** Excel, Word, PDF creation/manipulation
- **Content Bee:** GPTzuu video production, media automation
- **Research Bee:** Web search, data aggregation, synthesis
- **Browser Bee:** Web interaction, form filling, data scraping
- **Code Bee:** Git, code review, script execution (future)
- **Email Bee:** Email/calendar management (future)

**Worker Protocol:**
- Each worker is stateless (state in SQLite)
- Receives task, executes, returns result + evidence
- Can fail and be retried, or escalated to different worker
- Reports resource usage for health tracking

**Extensibility:**
- New workers pluggable at runtime
- Worker discovery via registry
- Custom workers for domain-specific tasks

---

### 1.7 Health & Reliability Layer

```
┌──────────────────────────────────────┐
│      WATCHDOG (Health Monitor)       │
│  - Evidence-based system state       │
│  - Auto-restart with loop detection  │
│  - Resource-aware throttling         │
└──────────────────┬───────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼───┐      ┌───▼──┐      ┌───▼──┐
│Service │      │Deps  │      │Resrcs│
│Monitor │      │Health│      │Limits│
│        │      │      │      │      │
└────────┘      └──────┘      └──────┘
```

**Service Monitoring:**
- Ollama availability & responsiveness
- Mission engine status
- Worker health (are they responsive?)
- Database (SQLite) accessibility
- Browser/CDP connectivity
- Voice service status
- Network connectivity

**Auto-Recovery:**
- Restart failed services with bounded retries
- Exponential backoff (don't restart-bomb failed services)
- Loop detection (if restarting >N times in window, declare dead, escalate)
- Prefer restart over degradation, but log what happened

**Resource Tracking:**
- CPU, RAM, VRAM (GPU), disk usage
- Don't launch 27B model if VRAM at 80%
- Don't spawn 10 parallel workers if RAM is constrained
- Throttle/queue work as needed
- Warn when approaching limits

**Evidence-Based Status:**
- No fake green lights
- System state derived from actual probes:
  - Ping services
  - Query resource usage
  - Check disk/network connectivity
  - Measure actual latency/throughput
- Status = measured fact, not assumption

---

## 2. OPERATIONAL MODES (AUTO / LAND / SEA)

### 2.1 AUTO (Default Intelligent Mode)

- System auto-detects online/offline availability
- Routes missions to best available backend
- Falls back gracefully on any failure
- Mixes online APIs (for speed/capability) with offline (for privacy/cost)
- User can override per-mission

**Decision Tree:**
```
User Mission
    │
    ├─ Requires cloud capability (vision, specific model)?
    │   └─→ Yes: try LAND, fall back to SEA if fail
    │   └─→ No: prefer SEA (privacy), try LAND if offline capability insufficient
    │
    ├─ Sensitive data / privacy-critical?
    │   └─→ Yes: force SEA (offline only)
    │   └─→ No: AUTO decides
    │
    ├─ Internet available?
    │   └─→ Yes: try LAND, fall back to SEA
    │   └─→ No: use SEA
    │
    └─ Cost budget exceeded?
        └─→ Yes: switch to SEA or cheaper LAND option
```

### 2.2 LAND (Cloud-First Mode)

- Primary routing to online APIs (OpenRouter, etc.)
- Falls back to offline only on failure
- Intended for tasks requiring:
  - Specific high-capability models
  - Real-time data (web search, live market data)
  - Capability offline models lack

### 2.3 SEA (Offline-First Mode)

- All work done locally (Ollama, local tools)
- No internet required
- No cloud costs
- Full privacy
- Degraded capability (smaller local models)
- Useful for: sensitive work, disconnected environments, cost-conscious operations

### 2.4 OVERRIDE (Per-Mission)

```yaml
mission:
  intent: "Research AI safety and draft white paper"
  mode: "AUTO"  # or "LAND" or "SEA" for this specific mission
  
  api_config:
    primary: "openrouter"
    fallback_chain: ["ollama", "lm_studio"]
    cost_limit: "$5.00"
    privacy_level: "normal"  # or "high" (forces offline)
```

---

## 3. USER INTERFACE

### 3.1 CLI (Command Line)

```bash
# Health & telemetry
python -m jarvis doctor                    # System health check
python -m jarvis telemetry                 # Real-time resource usage

# Configuration
python -m jarvis config list               # Show current config
python -m jarvis config set api.primary openrouter
python -m jarvis secret add openrouter.key YOUR_KEY  # Store in OS keyring

# Mission dispatch
python -m jarvis mission "task description" --mode AUTO --budget 5.00
python -m jarvis mission file://tasks.txt                 # Load from file

# Voice control (when enabled)
python -m jarvis voice --listen            # Push-to-talk mode
python -m jarvis voice --wake-word "hey jarvis"  # Always-listening mode

# System management
python -m jarvis profile list              # Show profiles (AUTO, LAND, SEA, custom)
python -m jarvis profile set production    # Switch profile
python -m jarvis logs --recent 50          # Tail recent actions
python -m jarvis audit mission-id-123      # Inspect mission evidence
```

### 3.2 Web Dashboard

Real-time browser UI (localhost:8080):
- **Mission Status:** Current mission, progress, subtasks, completion %
- **Real-time Stream:** Action log, evidence (screenshots), worker activity
- **System Health:** Service status, resource usage, network connectivity
- **Model/API Status:** Which models active, latency, cost accumulation
- **Archive:** Past missions, searchable history, replay evidence

### 3.3 Voice Interface

- Push-to-talk: "Listen" command, speak, system responds
- Wake-word (future): "Hey JARVIS..." to start interaction
- Barge-in (future): Interrupt mid-response
- Natural conversation flow with memory (recalls context from previous missions)

### 3.4 Configuration Management

**Files:**
```
~/.jarvis/
  ├── config.yaml          # Main settings
  ├── profiles.yaml        # Profiles (AUTO/LAND/SEA/custom)
  ├── models.yaml          # Model registry
  └── logging.yaml         # Log levels/verbosity
```

**User-Editable:**
- YAML configurations can be edited directly
- Changes take effect on next mission (or `jarvis reload`)
- Schema validation prevents invalid configs

**JARVIS-Managed:**
- JARVIS can suggest config changes: "I recommend enabling GPU caching"
- User approves/denies from CLI or dashboard
- Never auto-modify without confirmation

---

## 4. INTEGRATION POINTS

### 4.1 Day-One Integrations

- **LLM APIs:** OpenRouter, FreeeLLMAPI, OmniRoute, Ollama, LM Studio
- **Browser:** Chrome/Edge CDP (port 9222)
- **Office:** Excel (openpyxl), Word (python-docx), PDF (pypdf, reportlab)
- **OS:** Windows UIA, keyboard/mouse (pyautogui)
- **Voice:** VoiceStudio abstraction + SAPI fallback
- **Media:** FFmpeg (video processing, frame extraction)
- **Code:** Git CLI, Python execution
- **Database:** SQLite (state), Chroma/local vector DB (semantics)

### 4.2 Plugin/Worker Architecture

Workers are Python modules exposing:
```python
class CustomWorker:
    async def execute(self, task: Task, context: Context) -> Result:
        # task contains input data, original intent, checkpoint state
        # context provides access to LLM, memory, other workers
        return Result(status="success", output=..., evidence=...)
```

**Discovery:**
```bash
python -m jarvis workers list               # Show registered workers
python -m jarvis workers load ./my_worker.py  # Load custom worker
```

### 4.3 Extensibility Examples

- **Custom Tool:** Add a worker that interfaces with internal JIRA/Salesforce API
- **Domain Specific:** Specialized worker for financial analysis, medical research, etc.
- **External Scripts:** Worker that invokes arbitrary shell scripts, returns output

---

## 5. SECURITY & PRIVACY

### 5.1 Secrets Management

- API keys → OS credential store (Windows DPAPI)
- Never logged or exposed in prompts
- Accessible only via authenticated JARVIS session
- Audit: log which secret was accessed, not its value

### 5.2 Data Classification

- **Public:** Can use cloud APIs
- **Sensitive:** Offline-only (force SEA mode)
- **Private:** Additional encryption at rest
- User tags missions/documents with classification
- Enforcement: refuse to send classified data to cloud APIs

### 5.3 Audit Trail

- Immutable append-only log (SQLite WAL mode)
- Every action: who (user), what (action), when (timestamp), why (intent), how (tool/model), result (status + evidence)
- Screenshot evidence for visual actions (signed with timestamp)
- Failed attempts preserved (valuable for diagnosis, not auto-deleted)

---

## 6. TESTING & VALIDATION

### 6.1 Unit Tests

Individual components:
- LLM client (mocked & real APIs)
- Memory layer (SQLite operations)
- Action executor (UIA, browser CDP)
- Voice provider
- Config parsing
- Plan decomposition

### 6.2 Integration Tests

Real services:
- Actual Ollama instance
- Actual Chrome instance with CDP
- Actual Windows applications (Office, Notepad, etc.)
- Actual filesystem operations
- Actual FFmpeg processing
- API rate limits & fallback chains

### 6.3 Real-World Qualification Missions

Actual executable missions:
1. **Document Creation:** Research a topic → fetch data → create Excel with formulas → generate PDF report
2. **Browser Automation:** Log into website → scrape table → validate data → screenshot evidence
3. **Content Production:** Plan video script → generate frames → combine with audio → output MP4
4. **System Administration:** Inventory installed software → check updates → generate audit report

Success = actual artifacts generated, zero manual intervention, full evidence captured.

---

## 7. DEPLOYMENT TARGETS

### Primary

- **Windows 11 (Dell Precision 5690):** Full-featured, native performance

### Secondary

- **Linux (server mode):** Headless operation for continuous research/monitoring
- **Docker:** Isolated services (future)

### Not Supported

- macOS (until enough demand/capability verified)
- Mobile (out of scope)

---

## 8. FILE STRUCTURE

```
jarvis-universal-agent/
├── jarvis/
│   ├── __main__.py              # CLI entry point
│   ├── core/
│   │   ├── config.py            # Configuration management
│   │   ├── logger.py            # Audit-trail logging
│   │   ├── secrets.py           # OS keyring integration
│   │   └── state.py             # Global state manager
│   │
│   ├── brain/
│   │   ├── arbiter.py           # LLM router & capability detection
│   │   ├── model_client.py      # Unified LLM client
│   │   ├── model_registry.py    # Model metadata & capabilities
│   │   └── tool_registry.py     # Tool/function definitions
│   │
│   ├── memory/
│   │   ├── sqlite_store.py      # SQLite operational state
│   │   ├── checkpoint.py        # Mission/task checkpointing
│   │   ├── semantic_store.py    # Vector DB integration
│   │   └── provenance.py        # SourceFinder-style tracking
│   │
│   ├── control/
│   │   ├── actions.py           # Action executor (18 primitives)
│   │   ├── computer.py          # Screen capture, OCR, UIA
│   │   ├── browser.py           # CDP automation
│   │   └── executor.py          # Unified action runner
│   │
│   ├── voice/
│   │   ├── provider.py          # Abstract voice provider
│   │   ├── voicestudio.py       # VoiceStudio integration
│   │   ├── sapi.py              # Windows SAPI fallback
│   │   ├── transcription.py     # Speech-to-text
│   │   └── synthesis.py         # Text-to-speech
│   │
│   ├── mission/
│   │   ├── engine.py            # Mission executor
│   │   ├── planner.py           # Task decomposition
│   │   ├── commander.py         # Worker coordination
│   │   └── modes.py             # AUTO/LAND/SEA logic
│   │
│   ├── workers/
│   │   ├── base_worker.py       # Worker interface
│   │   ├── core_worker.py       # Generic executor
│   │   ├── document_worker.py   # Excel/Word/PDF
│   │   ├── content_worker.py    # GPTzuu content pipeline
│   │   ├── research_worker.py   # Web research & synthesis
│   │   └── registry.py          # Worker discovery
│   │
│   ├── health/
│   │   ├── watchdog.py          # Service monitor
│   │   ├── verifier.py          # Evidence-based validation
│   │   └── telemetry.py         # Resource tracking
│   │
│   ├── api/
│   │   ├── openrouter.py        # OpenRouter client
│   │   ├── freellm.py           # FreeeLLMAPI client
│   │   ├── omniroute.py         # OmniRoute client
│   │   ├── ollama_client.py     # Ollama integration
│   │   ├── lmstudio_client.py   # LM Studio integration
│   │   └── base_client.py       # Base API client
│   │
│   └── cli/
│       ├── commands.py          # Command handlers
│       ├── formatter.py         # Output formatting
│       └── repl.py              # Interactive shell
│
├── tests/
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_memory.py
│   │   ├── test_actions.py
│   │   ├── test_brain.py
│   │   └── ...
│   │
│   ├── integration/
│   │   ├── test_ollama.py       # Real Ollama instance
│   │   ├── test_browser.py      # Real Chrome/CDP
│   │   ├── test_office.py       # Real Office apps
│   │   ├── test_filesystem.py   # Real file operations
│   │   └── ...
│   │
│   └── qualification/
│       ├── mission_research.py        # Real qualification mission
│       ├── mission_document.py
│       ├── mission_content.py
│       └── mission_browser.py
│
├── config/
│   ├── config.yaml
│   ├── profiles.yaml
│   ├── models.yaml
│   └── logging.yaml
│
├── docs/
│   ├── ARCHITECTURE.md (this file)
│   ├── API_GUIDE.md
│   ├── VOICE_INTEGRATION.md
│   ├── WORKER_DEVELOPMENT.md
│   └── DEPLOYMENT.md
│
├── README.md
├── requirements.txt
└── setup.py
```

---

## 9. NEXT STEPS

1. **Inspect VoiceStudio:** Determine actual API/capabilities before full voice integration
2. **Lock API credentials:** Set up OpenRouter, FreeeLLMAPI account & API keys
3. **Bootstrap Ollama:** Pre-download candidate models for SEA mode
4. **Begin Unit Tests:** Core components (config, memory, LLM client)
5. **Integration Testing:** Real Ollama, real browser, real Office apps
6. **Qualification Missions:** Execute actual document creation, research, content production
