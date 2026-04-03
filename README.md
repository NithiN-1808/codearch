# 🏗️ CodeArch — Autonomous Codebase Archaeologist

> Drop a GitHub URL. Four AI agents collaborate autonomously to produce an elite onboarding intelligence report — **100% local, no API keys, no cloud.**

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-FF6B6B?style=for-the-badge)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-00C7B7?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</div>

---

## ✨ What is CodeArch?

Most developers waste their first week on a new codebase just figuring out *where things are*. CodeArch fixes that.

Paste any GitHub repo URL. Four specialized AI agents dig through the code autonomously — mapping structure, finding patterns, challenging assumptions, and writing a polished onboarding guide. All in minutes. All on your machine.

---

## 🤖 The Agent Pipeline

```
GitHub URL
    ↓
[Cloner]          — git clone --depth=1
    ↓
[🔭 Explorer]     — maps structure, tech stack, entry points
    ↓
[🔬 Analyst]      — finds patterns, tech debt, hidden conventions
    ↓
[🤔 Skeptic]      — challenges analysis, surfaces gaps & open questions
    ↓
[✍️  Writer]       — synthesises everything into a day-1 onboarding guide
    ↓
Intelligence Report (streamed live via SSE)
```

All agents share a **LangGraph state graph** — each node reads from and writes to the same typed state dict, enabling clean, deterministic data flow across the pipeline.

---

## 📋 Output: Intelligence Report

Each report covers:

- 🎯 **Project Overview** — what it does and why it exists
- 🏗️ **Architecture** — style, patterns, structure
- 🚀 **Day-1 Getting Started Guide** — exact steps to run it
- 📁 **Key Files & What They Do** — no more guessing
- ⚠️ **Gotchas & Traps** — the stuff that bites new engineers
- 💡 **Hidden Patterns & Conventions** — the unwritten rules
- 🔗 **External Dependencies** — APIs, DBs, services
- 📋 **Open Questions** — what's still unclear
- ✅ **Recommended Reading Order** — where to start

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Agent Orchestration | LangGraph |
| LLM Runtime | Ollama (local) |
| Models | qwen2.5:7b + deepseek-coder |
| Backend | FastAPI + SSE Streaming |
| Frontend | Vanilla JS + Marked.js |

---

## ⚡ Prerequisites

- Python 3.10+
- Git
- [Ollama](https://ollama.com) installed

---

## 🚀 Setup

### 1. Install Ollama

```bash
# macOS / Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows: https://ollama.com/download
```

### 2. Pull the models

```bash
ollama pull qwen2.5:7b
ollama pull deepseek-coder
```

### 3. Clone this repo

```bash
git clone https://github.com/YOUR_USERNAME/codearch.git
cd codearch
```

### 4. Set up Python environment

```bash
cd backend
python3 -m venv venv

# Activate
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 5. Start the backend

```bash
python server.py
# → Uvicorn running on http://0.0.0.0:8000
```

### 6. Serve the frontend

```bash
# New terminal
cd frontend
python3 -m http.server 3000
```

Open **http://localhost:3000** 🎉

---

## 💻 Usage

1. Paste any public GitHub repo URL
2. Click **Analyse →**
3. Watch the agents work in real time
4. Read your intelligence report

### Repos to try

```
https://github.com/tiangolo/fastapi
https://github.com/pallets/flask
https://github.com/django/django
https://github.com/expressjs/express
```

---

## 🔧 Troubleshooting

| Error | Fix |
|-------|-----|
| `Error connecting to API` | Make sure `python server.py` is running |
| `model not found` | Run `ollama pull qwen2.5:7b` |
| `not enough memory` | Close browser tabs and background apps, then restart Ollama |
| Agents are slow | Normal on CPU — GPU speeds this up significantly |

---

## 🧩 Extending CodeArch

- 🗺️ **Diagram Agent** — generate architecture diagrams with Mermaid.js
- 🔍 **Vector Search** — ChromaDB Q&A over the codebase post-report
- 🔀 **Diff Agent** — compare two repos or two commits
- 📄 **PDF Export** — download the report
- 🤖 **PR Bot** — GitHub Actions integration to run on every pull request

---

## 📁 Project Structure

```
codearch/
├── backend/
│   ├── agents.py          # LangGraph multi-agent pipeline
│   ├── server.py          # FastAPI server + SSE streaming
│   └── requirements.txt
└── frontend/
    └── index.html         # Vanilla JS UI
```

---

## 📜 License

MIT — free to use, modify, and distribute.

---

<div align="center">
  <b>Built with LangGraph · Ollama · FastAPI</b><br/>
  <i>No cloud. No API keys. Just local AI doing serious work.</i>
</div>
