# Epilog: The Self-Healing Runtime for AI Agents

> **Hackathon:** [Gemini 3.0 Hackathon](https://gemini3.devpost.com/)  
> **Tagline:** "Agents break. Epilog fixes them."  
> **Status:** Draft v1.0

---

## 1. Executive Summary

**Epilog** is an open-source "Flight Recorder" and "Auto-Surgeon" for Agentic workflows. Unlike traditional tracing tools (LangSmith) that only *show* you the logs, Epilog actively **intercepts** failures, uses **Gemini 1.5 Pro (Multimodal)** to diagnose root causes (analyzing both code and screenshots), and generates verified code patches.

We position Epilog not as a competitor to frameworks like GSD or Ralph, but as the essential **Telemetry & Repair Layer** that makes those high-performance loops reliable.

---

## 2. Core Architecture: The "Shadow Runtime"

The system consists of three distinct components:

### A. The Black Box (`epilog-sdk`)
A lightweight Python SDK that instruments the user's agent.
*   **Mechanism:** A `CallbackHandler` compatible with LangChain/LangGraph.
*   **Responsibility:** Streams "Events" (Tools, Thoughts, Outputs) and **Artifacts** (Screenshots, PDF downloads) to the Epilog Core.
*   **Key Feature:** It captures the *visual state* of the agent (e.g., screenshots of the browser) alongside the text logs.

### B. The Operating Room (`epilog-core`)
The backend brain powered by **Gemini 1.5 Pro**.
*   **Engine:** FastAPI + LangGraph.
*   **The "Doctor Squad":** A multi-agent system that wakes up only when a run fails.
    1.  **Triage Agent:** Scans the massive JSON trace (using Gemini's 2M context) to locate the drift.
    2.  **Visual Coroner:** Compares the agent's "Thought" vs. the "Screenshot" (e.g., *Agent said 'clicked login', but Screenshot shows a 404 error*).
    3.  **PatchSmith:** Reads the user's source code and generates a Git Patch to fix the logic.
    4.  **Simulant (Optional):** Spins up a sandbox (Docker/E2B) to verify the patch.

### C. The HUD (`epilog-web`)
A "SpaceX-style" Mission Control dashboard.
*   **Stack:** Next.js + React Flow + ShadCN UI.
*   **Key View:** A scrubbing timeline that visualizes the agent's execution graph, allowing "Time Travel" to any previous state.

---

## 3. Data Protocol: The Universal Trace Schema

We define a strict schema to allow swappable models later, though we optimize for Gemini 3 now.

```jsonc
// stored in events.jsonl
{
  "run_id": "uuid-550e8400",
  "step_index": 42,
  "timestamp": "2026-01-22T10:00:00Z",
  "event_type": "tool_end", 
  "agent_name": "CryptoResearcher",
  "payload": {
    "tool": "browser_screenshot",
    "args": {"url": "https://finance.yahoo.com"},
    "output": "<binary_image_ref>" 
  },
  "context": {
    "visual_snapshot": "/artifacts/run_550/step_42.png", // Crucial for Gemini Vision
    "memory_dump": "..." // The agent's STM at this moment
  },
  "error": null
}
```

---

## 4. Implementation Roadmap (Phases)

### Phase 1: The Foundation & "The Patient"
**Goal:** Create a broken agent and the ability to record it.
1.  **The "Patient" Agent:** Build a LangGraph agent that performs a visual task (e.g., "Go to this URL, screenshot the pricing table, and summarize it").
    *   *Sabotage:* Make it fail on specific UI layouts (simulating "flaky" web tools).
2.  **The Recorder SDK:** Implement `EpilogCallbackHandler`.
    *   Must save logs to a local `sqlite.db` or `jsonl` file.
    *   Must capture screenshots if the agent yields them.

### Phase 2: The HUD (Visualization)
**Goal:** See the failure clearly.
1.  **API:** Build a simple FastAPI endpoint `GET /runs/{id}` that returns the JSONL.
2.  **UI:** Build the Next.js frontend.
    *   Use **React Flow** to render the LangGraph nodes.
    *   Add a "Timeline Scrubber" at the bottom.
    *   **Success Criteria:** You can drag the slider and see the screenshot change from Step 1 to Step 10.

### Phase 3: The Doctor (Gemini Integration)
**Goal:** The "One-Click Fix."
1.  **The Diagnosis Node:**
    *   Ingest the *entire* trace (text + images) into Gemini 1.5 Pro.
    *   Prompt: *"Analyze this failure. Correlate the visual snapshot at Step X with the error at Step Y."*
2.  **The Patch Node:**
    *   Give Gemini read-access to the "Patient's" source code (`agent.py`).
    *   Prompt: *"Write a unified diff patch to handle this edge case."*
3.  **UI Integration:** Display the Diagnosis and the Code Diff side-by-side in the HUD.

### Phase 4: The Loop (Advanced/Optional)
**Goal:** Prove the fix works.
1.  **Integration with E2B (or local Docker):**
    *   Epilog spins up a container.
    *   Applies the patch.
    *   Re-runs the failing input.
    *   Reports: "Fix Verified: Passing."

---

## 5. Technology Stack

*   **LLM:** **Gemini 1.5 Pro** (Primary Reasoning & Vision), **Gemini Flash** (Fast Triage).
*   **Orchestration:** **LangGraph** (Python).
*   **Backend:** FastAPI, Python 3.11+.
*   **Frontend:** Next.js 14, React Flow, TailwindCSS, ShadCN/UI.
*   **Storage:** SQLite (MVP), Postgres (Production).
*   **Sandboxing:** E2B SDK (for executing fixes safely).

---

## 6. Competitive Advantage (The Pitch)

| Feature | Standard Debuggers (LangSmith) | **Epilog** |
| :--- | :--- | :--- |
| **Context** | Single Step | **Full History (1M+ Tokens)** |
| **Modality** | Text Only | **Multimodal (Screenshots/PDFs)** |
| **Action** | Passive Logging | **Active Auto-Fixing** |
| **Workflow** | Human reads logs | **AI writes patches** |

---

## 7. Hackathon Strategy Checklist

- [ ] **Leverage Long Context:** We must feed the *whole* log to Gemini, not chunks. This is a specific Gemini advantage.
- [ ] **Show, Don't Tell:** The demo must show a **Visual** failure (e.g., a website popup blocking the agent) that a text-only debugger would miss.
- [ ] **Open Source Ready:** The architecture uses standard interfaces (`CallbackHandler`), making it easy for others to adopt.