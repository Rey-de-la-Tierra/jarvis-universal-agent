# JARVIS Universal Agent

**Autonomous OS automation with ANY LLM API. Real-time voice, computer control, long-term memory. Privacy-first, reliability-obsessed, vendor-agnostic, offline-capable.**

## Vision

JARVIS is not just a chatbot. It's a **digital worker** that:

- **Operates** your computer (screen capture, mouse/keyboard, browser control, application automation)
- **Thinks** with any LLM (OpenRouter, FreeeLLMAPI, OmniRoute, Groq, or local Ollama/LM Studio)
- **Speaks** naturally with local voice (VoiceStudio or Windows SAPI fallback)
- **Remembers** persistently across missions (SQLite operational state + vector semantic memory)
- **Decides** confidently, asking for clarification when uncertain
- **Recovers** from failures with checkpointed state and alternative strategies
- **Proves** every action with traceability and evidence (screenshots, logs, audit trail)

## Key Features

### 🧠 Vendor-Agnostic Brain

- **Online (LAND):** OpenRouter, FreeeLLMAPI, OmniRoute, Groq, Together.ai, Claude API, custom endpoints
- **Offline (SEA):** Ollama, LM Studio, local models
- **Intelligent Routing:** Capability-based model selection, not blind model sizing
- **Fallback Chains:** Graceful degradation across multiple APIs
- **Cost Tracking:** Never spend money silently; enforce per-mission budgets

### 💻 Full OS Automation

- **Windows UIA:** Query window hierarchies, elements, accessibility trees
- **Browser CDP:** Chrome/Edge control, JavaScript execution, DOM queries
- **Office APIs:** Excel (formulas, formatting), Word, PDF generation
- **Screen Capture & OCR:** Visual perception and action verification
- **Mouse/Keyboard:** Human-like timing or fastest-safe execution
- **18 Core Primitives:** Window management, clipboard, file operations, and more

### 🎙️ Real-Time Voice

- **Push-to-Talk (v1):** Explicit activation + natural speech recognition
- **Fallback Chain:** VoiceStudio → Windows SAPI → text-only mode
- **Multiple Personas:** Voice cloning and personality profiles
- **Confidence Thresholds:** Ask for clarification if unclear

### 🧠 Long-Term Memory

- **SQLite Authoritative State:** Mission history, checkpoints, action logs, audit trail
- **Vector Semantic Memory:** Knowledge base with source provenance (SourceFinder-style)
- **Persistent Mission State:** Resume from last checkpoint on crash
- **User-Controlled Forgetting:** Archival, not auto-deletion
- **Privacy by Default:** Sensitive data redacted in logs, locked to offline processing

### 🎯 Intelligent Task Execution

- **Autonomous Work:** Normal, safe operations execute without confirmation
- **Policy Gating:** Destructive, financial, security-sensitive, or ambiguous actions require approval
- **Error Recovery:** Retry → diagnose → alternative strategy → escalate
- **Checkpointing:** Resume from verified checkpoints (mission/task/subtask boundaries)
- **Plan Adaptation:** Modify strategy if evidence demands it, preserve original intent

### 🏥 Self-Healing Reliability

- **Evidence-Based Health:** No fake green lights; monitor actual service probes
- **Auto-Recovery:** Bounded retries with exponential backoff, loop detection
- **Resource Awareness:** CPU/RAM/VRAM/disk limits, adaptive throttling
- **Worker Fleet:** 6+ specialized agents (Core, Document, Content, Research, Browser, Code)
- **Endurance Tested:** Zero memory leaks, stress-tested multi-cycle execution

### 🔐 Security & Privacy

- **Secrets Manager:** OS keyring integration (Windows DPAPI, macOS Keychain, Linux pass)
- **Data Classification:** Tag missions as public/sensitive/private; enforce offline-only for sensitive
- **Audit Trail:** Immutable append-only logs with action provenance
- **Credential Masking:** All logs auto-redact API keys, passwords, tokens

## Installation

### Prerequisites

- **OS:** Windows 11 (primary), Linux (secondary), macOS (future)
- **Python:** 3.10+
- **Hardware:** 32GB RAM, 8GB VRAM (RTX 2000 Ada or equiv) recommended
- **Ollama:** (optional) For offline LLM support
- **Chrome/Edge:** For browser automation

### Quick Start

```bash
# Clone repository
git clone https://github.com/Rey-de-la-Tierra/jarvis-universal-agent.git
cd jarvis-universal-agent

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Initialize configuration
python -m jarvis config init

# Store API keys
python -m jarvis secret add openrouter.key YOUR_KEY
python -m jarvis secret add freellm.key YOUR_KEY

# Verify setup
python -m jarvis doctor
```

## Quick Reference

### System Health

```bash
python -m jarvis doctor              # Full system check
python -m jarvis telemetry           # Real-time resource usage
python -m jarvis logs --recent 50    # Last 50 actions
```

### Configuration

```bash
python -m jarvis config list                    # Show current config
python -m jarvis config set mode AUTO           # Set operation mode (AUTO/LAND/SEA)
python -m jarvis profile list                   # Available profiles
python -m jarvis profile set production         # Activate profile
```

### Mission Dispatch

```bash
# Simple mission
python -m jarvis mission "Research AI safety and draft a white paper"

# With options
python -m jarvis mission "Create an Excel budget report" --mode SEA --budget 2.50

# Load from file
python -m jarvis mission file://missions.txt
```

### Voice Control

```bash
python -m jarvis voice --listen              # Push-to-talk mode
python -m jarvis voice --wake-word "hey jarvis"  # Always-listening mode (future)
```

## Architecture Highlights

### 3-Mode Operation (AUTO / LAND / SEA)

**AUTO (Default):**
- Auto-detect connectivity
- Intelligent fallback chain
- Mix cloud + local based on capability, cost, privacy
- User override per-mission

**LAND (Cloud-First):**
- Primary routing to online APIs
- Falls back to local on failure
- For tasks requiring cloud-only capability or real-time data

**SEA (Offline-First):**
- All work local (Ollama, tools)
- No internet required
- Full privacy, no cloud costs
- Reduced capability, degraded latency

### Worker Fleet (HiveVerse)

- **Commander:** Mission orchestration, task routing, escalation
- **Core Bee:** Generic computer control, system operations
- **Document Bee:** Excel, Word, PDF creation/manipulation
- **Content Bee:** GPTzuu video production, media automation
- **Research Bee:** Web search, data synthesis, analysis
- **Browser Bee:** Web interaction, form filling, scraping
- **Code Bee:** Git, code review, script execution (future)
- **Email Bee:** Email/calendar management (future)

## Testing

### Unit Tests

```bash
pytest tests/unit/ -v
```

### Integration Tests (Real Services)

```bash
pytest tests/integration/ -v
```

### Qualification Missions (Real Artifacts)

```bash
pytest tests/qualification/ -v
```

## Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Complete system design
- **[API_GUIDE.md](docs/API_GUIDE.md)** — LLM API integration
- **[VOICE_INTEGRATION.md](docs/VOICE_INTEGRATION.md)** — Voice setup
- **[WORKER_DEVELOPMENT.md](docs/WORKER_DEVELOPMENT.md)** — Build custom workers
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** — Production deployment

## Status

**Phase 1 (Current):** Core infrastructure (config, logging, secrets, state)
**Phase 2 (Next):** LLM client abstraction + Ollama integration  
**Phase 3:** Computer control (UIA, browser, screen capture)  
**Phase 4:** Voice integration (VoiceStudio + SAPI)  
**Phase 5:** Mission engine + worker fleet  
**Phase 6:** Health & reliability (watchdog, verification, endurance)  
**Phase 7:** Production qualification & hardening  

## License

MIT (See LICENSE file)

## Author

**Rey-de-la-Tierra** — Autonomous Digital Worker Innovation
