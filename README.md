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

- **Trace Capture** — Record agent execution events (tool calls, thoughts, outputs) via LangChain/LangGraph callback handler
- **Screenshot Recording** — Capture visual state alongside text logs
- **Timeline Dashboard** — Scrub through execution history and see screenshots at each step
- **Multimodal Diagnosis** — Gemini analyzes failures by comparing what the agent "thought" vs what the screenshot "shows"
- **Patch Generation** — Get unified diff patches to fix the root cause

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (or Docker)
- Node.js 18+ (for dashboard)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/epilog.git
cd epilog

# Install Python dependencies
uv sync  # or: pip install -e .

# Start PostgreSQL (if using Docker)
docker run --name epilog-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=epilog \
  -p 5432:5432 -d postgres:16

# Run database migrations
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/epilog"
uv run alembic upgrade head

# Start the API server
uv run uvicorn epilog.api.main:app --reload
```

The API is now running at `http://localhost:8000`. Check `http://localhost:8000/docs` for the OpenAPI documentation.

### Instrument Your Agent

```python
from langchain_core.callbacks import BaseCallbackHandler
from epilog.sdk import EpilogCallbackHandler

# Create the callback handler
epilog = EpilogCallbackHandler(
    api_url="http://localhost:8000",
    session_name="my-agent-run"
)

# Use with LangChain/LangGraph
agent.invoke({"input": "your task"}, config={"callbacks": [epilog]})

# Epilog automatically captures:
# - Tool calls and outputs
# - LLM thoughts and responses
# - Screenshots (when using browser tools)
# - Errors and stack traces
```

### View Traces

Open the dashboard at `http://localhost:3000` to:
- Browse trace sessions
- Scrub through the execution timeline
- View screenshots at each step
- Trigger AI diagnosis on failures

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

**Components:**

- **epilog-sdk** — Lightweight callback handler that streams events and screenshots
- **epilog-api** — FastAPI backend for trace ingestion and storage
- **epilog-web** — Next.js dashboard with timeline visualization
- **diagnosis** — Gemini-powered failure analysis and patch generation

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `GEMINI_API_KEY` | Google AI API key for diagnosis | Required for diagnosis |

### SDK Options

```python
EpilogCallbackHandler(
    api_url="http://localhost:8000",  # Epilog API endpoint
    session_name="my-session",         # Optional session name
    capture_screenshots=True,          # Enable screenshot capture
    async_mode=True,                   # Non-blocking event dispatch
)
```

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy epilog/
```

## Roadmap

- [x] Trace ingestion API
- [x] PostgreSQL storage with async SQLAlchemy
- [ ] SDK callback handler for LangChain/LangGraph
- [ ] Screenshot capture integration
- [ ] Timeline dashboard
- [ ] Gemini multimodal diagnosis
- [ ] Patch generation

## Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on the process for submitting pull requests.

## License

MIT License. See [LICENSE](LICENSE) for details.

---

**Agents break. Epilog fixes them.**
