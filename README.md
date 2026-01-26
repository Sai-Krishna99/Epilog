# Epilog

**Flight recorder and auto-surgeon for AI agents.** Capture execution traces with screenshots, diagnose failures with multimodal AI, and generate code patches automatically.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Why Epilog?

When AI agents fail, traditional debuggers show you text logs. But agents operating in visual environments (browsers, GUIs, documents) fail for *visual* reasons that text logs miss entirely.

**Epilog captures what your agent *saw*, not just what it *said*.**

| Traditional Debuggers | Epilog |
|----------------------|--------|
| Text logs only | Screenshots + logs |
| Manual log reading | AI-powered diagnosis |
| "Figure it out yourself" | Generated code patches |

## Features

- **Trace Capture** — Record agent execution events (tool calls, thoughts, outputs) via LangChain/LangGraph callback handler.
- **Visual Artifacts** — High-resolution screenshot recording alongside every agent action.
- **Pro-Grade Dashboard** — Monochrome, minimalist UI with a frame-by-frame timeline scrubber.
- **Multimodal Diagnosis** — Gemini 3.0 analyzes failures by comparing agent "thoughts" vs "visual reality".
- **Auto-Surgeon** — Automatic generation of Unified Diff patches based on AI failure analysis.
- **Local Times** — All logs and dashboards render in your browser-local timezone.

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL (or Docker)
- Node.js 18+ (for dashboard)
- Gemini API Key (Vertex AI or standard)

### 2. Installation

```bash
# Clone and install
git clone https://github.com/Sai-Krishna99/Epilog.git
cd Epilog
uv sync
```

### 3. Start the Platform

```bash
# Terminal 1: Backend
uv run uvicorn epilog.api.main:app --reload

# Terminal 2: Dashboard
cd epilog-web
npm run dev
```

### 4. Run the Multimodal Demo

We've provided a "broken" patient agent demo to show Epilog in action.

```bash
# Terminal 3: Demo
uv run python patient_agent.py
```

Go to `http://localhost:3000`, select the **"Patient Agent Demo"** session, and click **DIAGNOSE** on the error event to see the Auto-Surgeon fix the code.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Your Agent    │────▶│   Epilog SDK    │────▶│   Epilog API    │
│  (LangGraph)    │     │ (CallbackHandler)│     │   (FastAPI)     │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                        ┌─────────────────┐     ┌────────▼────────┐
                        │    Dashboard    │◀────│   PostgreSQL    │
                        │    (Next.js)    │     │                 │
                        └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  Gemini Vision  │
                        │   (Diagnosis)   │
                        └─────────────────┘
```

## Configuration

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `GEMINI_API_KEY` | Google AI API key |
| `EPILOG_DIAGNOSIS_MODEL` | Gemini model for analysis (Default: `gemini-3-flash-preview`) |

## Roadmap

- [x] Trace ingestion API
- [x] PostgreSQL storage with async SQLAlchemy
- [x] SDK callback handler for LangChain/LangGraph
- [x] Visual artifact capture (generic & playwright)
- [x] Timeline dashboard
- [x] Gemini multimodal diagnosis
- [x] Patch generation

## License

MIT License. See [LICENSE](LICENSE) for details.

---

**Agents break. Epilog fixes them.**
