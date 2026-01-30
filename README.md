# Epilog

**AI-powered debugger for AI agents.** Epilog doesn't just log what happened — it tells you WHY things failed. For browser agents, it captures screenshots to detect visual mismatches.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Why Epilog?

When AI agents fail, traditional tools show you logs. You see "element not found" but not *why*. Was the page different? Did the API change? Is the selector wrong?

**Epilog captures context and uses AI to diagnose the root cause.**

| Traditional Tools | Epilog |
|-------------------|--------|
| Shows logs | Diagnoses failures |
| "Figure it out" | "Here's what went wrong" |
| Text only | Screenshots + logs (for visual agents) |

### Core Value: AI Diagnosis

For **all agents** (API calls, MCP tools, code execution):
- Event traces capture what the agent did
- AI analyzes the sequence and identifies failure patterns
- Diagnosis explains the root cause, not just the symptom

### Enhanced for Visual Agents

For **browser/GUI agents**, Epilog adds:
- Screenshot capture at each step
- Visual mismatch detection (expected vs actual)
- "Agent tried selector X, but page shows Y"

## Features

- **Trace Capture** — Record agent events (tool calls, thoughts, outputs) via LangChain/LangGraph callback handler
- **Screenshot Artifacts** — Capture what visual agents actually see (optional, via Playwright)
- **Real-time Dashboard** — Monitor agent runs live with SSE streaming
- **AI Diagnosis** — Gemini analyzes failures using full context (traces + screenshots)
- **Visual Mismatch Detection** — Compare agent expectations vs visual reality
- **Patch Generation** — Auto-generate code fixes based on diagnosis

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone and configure
git clone https://github.com/Sai-Krishna99/Epilog.git
cd Epilog
cp .env.example .env  # Add your GOOGLE_API_KEY

# Start everything
docker-compose up -d

# Open dashboard
open http://localhost:3000
```

### Option 2: Local Development

**Prerequisites:**
- Python 3.11+
- PostgreSQL (or Docker)
- Node.js 20+
- Google API Key (for Gemini)

```bash
# Clone and install
git clone https://github.com/Sai-Krishna99/Epilog.git
cd Epilog
uv sync

# Start PostgreSQL
docker run -d --name epilog-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=epilog \
  -p 5432:5432 postgres:16

# Run migrations
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/epilog"
uv run alembic upgrade head

# Terminal 1: API
uv run uvicorn epilog.api.main:app --reload

# Terminal 2: Dashboard
cd epilog-web && npm install && npm run dev
```

### Run the Demos

```bash
# Before/After comparison - shows traditional debugging first
uv run python before_epilog_demo.py  # Traditional (no Epilog)
uv run python cookie_popup_demo.py   # With Epilog - see the difference!

# More failure scenarios
uv run python login_wall_demo.py     # LinkedIn auth wall
uv run python paywall_demo.py        # Medium subscription wall
uv run python real_demo_agent.py     # HN scraper wrong selector
```

1. Open http://localhost:3000
2. Select a session from the sidebar
3. Scrub to an event with a camera icon (has screenshot)
4. Click **DIAGNOSE** to see AI analysis

| Demo | Failure Type | What Screenshot Shows |
|------|-------------|----------------------|
| Cookie Popup | GDPR modal | Privacy consent covering page |
| Login Wall | Auth required | "Sign in to view" page |
| Paywall | Subscription | "Member-only story" block |
| HN Scraper | Wrong selector | Page looks fine, selector outdated |

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Your Agent    │────▶│   Epilog SDK    │────▶│   Epilog API    │
│ (LangChain/etc) │     │ (CallbackHandler)│     │   (FastAPI)     │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                        ┌─────────────────┐     ┌────────▼────────┐
                        │    Dashboard    │◀────│   PostgreSQL    │
                        │    (Next.js)    │ SSE │                 │
                        └────────┬────────┘     └─────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  Gemini Flash   │
                        │   (Diagnosis)   │
                        └─────────────────┘
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `GOOGLE_API_KEY` | Google AI API key for Gemini | Required for diagnosis |
| `EPILOG_DIAGNOSIS_MODEL` | Gemini model for analysis | `gemini-2.0-flash` |
| `NEXT_PUBLIC_API_URL` | API URL for frontend | `http://localhost:8000` |

## SDK Usage

```python
from epilog.sdk import EpilogCallbackHandler, ScreenshotCapture

# For any agent (no screenshots)
handler = EpilogCallbackHandler(
    api_base_url="http://localhost:8000",
    session_name="My Agent Run"
)

# For browser agents (with screenshots)
async with ScreenshotCapture(headless=True) as capture:
    handler = EpilogCallbackHandler(
        api_base_url="http://localhost:8000",
        session_name="Browser Agent",
        screenshot_capture=capture
    )

    # Use with LangChain
    chain.invoke({"input": "..."}, config={"callbacks": [handler]})

    # Or call methods directly
    await handler.on_tool_end_with_screenshot(
        output="Clicked button",
        run_id=run_id,
        url="https://example.com"
    )
```

## License

MIT License. See [LICENSE](LICENSE) for details.

---

**Agents break. Epilog explains why.**
