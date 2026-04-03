"""
CodeArch — Autonomous Codebase Archaeologist
Multi-agent system using LangGraph + Ollama (100% local)
"""

import os
import json
from pathlib import Path
from typing import TypedDict, Annotated
import operator

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END


# ── State shared across all agents ──────────────────────────────────────────

class ArchState(TypedDict):
    repo_path: str
    file_tree: str
    file_contents: dict          # {filepath: content}
    explorer_notes: str
    analyst_notes: str
    skeptic_questions: str
    skeptic_answers: str
    final_report: str
    progress: Annotated[list, operator.add]  # streamed status messages


# ── LLM setup (Ollama, fully local) ─────────────────────────────────────────

def get_llm(model: str = "qwen2.5:7b", temperature: float = 0.2):
    return ChatOllama(model=model, temperature=temperature)

def get_coder_llm():
    return ChatOllama(model="deepseek-coder:latest", temperature=0.1)


# ── Tool: File reader ────────────────────────────────────────────────────────

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache"}
SKIP_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff",
             ".woff2", ".ttf", ".eot", ".pdf", ".zip", ".tar", ".gz",
             ".lock", ".min.js", ".min.css"}
MAX_FILE_BYTES = 8_000
MAX_FILES = 40


def build_file_tree(repo_path: str) -> tuple[str, dict]:
    """Walk the repo, return (tree_str, {path: content})"""
    root = Path(repo_path)
    tree_lines = []
    contents = {}
    file_count = 0

    def walk(path: Path, prefix: str = ""):
        nonlocal file_count
        try:
            items = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name))
        except PermissionError:
            return
        for item in items:
            if item.name.startswith(".") and item.name != ".env.example":
                continue
            if item.is_dir():
                if item.name in SKIP_DIRS:
                    continue
                tree_lines.append(f"{prefix}📁 {item.name}/")
                walk(item, prefix + "  ")
            else:
                if any(item.name.endswith(e) for e in SKIP_EXTS):
                    continue
                tree_lines.append(f"{prefix}📄 {item.name}")
                if file_count < MAX_FILES:
                    try:
                        text = item.read_text(errors="replace")
                        contents[str(item.relative_to(root))] = text[:MAX_FILE_BYTES]
                        file_count += 1
                    except Exception:
                        pass

    walk(root)
    return "\n".join(tree_lines), contents


# ── Agent nodes ──────────────────────────────────────────────────────────────

def explorer_agent(state: ArchState) -> dict:
    """Reads the codebase and maps its high-level structure."""
    llm = get_llm()
    tree = state["file_tree"]
    # Pick key files (README, entry points, config)
    priority_keys = ["README.md", "package.json", "pyproject.toml",
                     "setup.py", "main.py", "app.py", "index.js",
                     "index.ts", "Dockerfile", "docker-compose.yml"]
    sample_contents = ""
    for key in priority_keys:
        for path, content in state["file_contents"].items():
            if Path(path).name == key:
                sample_contents += f"\n\n### {path}\n{content[:2000]}"

    # Also add first 10 source files
    count = 0
    for path, content in state["file_contents"].items():
        if count >= 10:
            break
        if not any(Path(path).name == k for k in priority_keys):
            sample_contents += f"\n\n### {path}\n{content[:1500]}"
            count += 1

    messages = [
        SystemMessage(content="""You are an expert software architect.
Your job is to explore a codebase and produce clear, structured notes.
Be specific. Mention file names, function names, and patterns you see.
Format your response in clear sections."""),
        HumanMessage(content=f"""Explore this codebase and produce exploration notes.

FILE TREE:
{tree}

KEY FILE CONTENTS:
{sample_contents}

Produce notes covering:
1. **Project Purpose** — what does this project do?
2. **Tech Stack** — languages, frameworks, databases, tools
3. **Architecture Style** — monolith, microservices, MVC, etc.
4. **Entry Points** — where does execution begin?
5. **Key Modules** — most important files/folders and their roles
6. **External Dependencies** — APIs, databases, services it connects to
""")
    ]
    response = llm.invoke(messages)
    return {
        "explorer_notes": response.content,
        "progress": ["✅ Explorer agent: codebase mapped"]
    }


def analyst_agent(state: ArchState) -> dict:
    """Finds patterns, tech debt, and onboarding insights."""
    llm = get_coder_llm()

    # Sample more files for deep analysis
    deep_sample = ""
    count = 0
    for path, content in state["file_contents"].items():
        if count >= 20:
            break
        deep_sample += f"\n\n### {path}\n{content[:1200]}"
        count += 1

    messages = [
        SystemMessage(content="""You are a senior engineer doing a deep code review.
You identify architectural patterns, potential issues, and hidden complexity.
Be brutally honest but constructive. Use specific examples from the code."""),
        HumanMessage(content=f"""Based on the exploration notes and code, perform deep analysis.

EXPLORATION NOTES:
{state['explorer_notes']}

CODE SAMPLES:
{deep_sample}

Analyse and report on:
1. **Design Patterns** — what patterns are used (factory, observer, repository, etc.)?
2. **Tech Debt** — what is messy, inconsistent, or likely to cause bugs?
3. **Undocumented Assumptions** — implicit rules a new dev must know
4. **Onboarding Traps** — things that will confuse a new engineer
5. **Strengths** — what is done well that should be preserved
6. **Recommended Entry Points** — best files to start reading for understanding
""")
    ]
    response = llm.invoke(messages)
    return {
        "analyst_notes": response.content,
        "progress": ["✅ Analyst agent: deep analysis complete"]
    }


def skeptic_agent(state: ArchState) -> dict:
    """Challenges the analysis and digs into open questions."""
    llm = get_llm(temperature=0.4)

    messages = [
        SystemMessage(content="""You are a skeptical senior architect.
Your job is to challenge previous analysis, find gaps, and ask probing questions.
Then answer those questions using the available information.
Be specific and thorough."""),
        HumanMessage(content=f"""Review this analysis and identify what's missing or unclear.

EXPLORER NOTES:
{state['explorer_notes']}

ANALYST NOTES:
{state['analyst_notes']}

1. List 5 probing questions a new engineer would still have after reading the analysis.
2. Answer each question as best you can from the available information.
3. Flag any assumptions in the analysis that might be wrong.
4. Identify any critical areas of the codebase NOT yet covered.
""")
    ]
    response = llm.invoke(messages)
    return {
        "skeptic_questions": response.content,
        "progress": ["✅ Skeptic agent: gaps identified and challenged"]
    }


def writer_agent(state: ArchState) -> dict:
    """Synthesises all agent outputs into a final onboarding report."""
    llm = get_llm(temperature=0.3)

    messages = [
        SystemMessage(content="""You are a technical writer creating an elite onboarding document.
Write in clear, direct prose. Use markdown formatting.
The reader is a new engineer joining the team on day 1.
Make it actionable — they should know exactly what to read first and what to avoid."""),
        HumanMessage(content=f"""Create a comprehensive onboarding intelligence report.

EXPLORATION NOTES:
{state['explorer_notes']}

ANALYSIS NOTES:
{state['analyst_notes']}

SKEPTIC REVIEW:
{state['skeptic_questions']}

Write a complete "Codebase Intelligence Report" with these sections:
# Codebase Intelligence Report

## 🎯 Project Overview
## 🏗️ Architecture
## 🚀 Getting Started (day 1 guide)
## 📁 Key Files & What They Do
## ⚠️ Watch Out For (traps & gotchas)
## 💡 Hidden Patterns & Conventions
## 🔗 External Dependencies
## 📋 Open Questions
## ✅ Recommended Reading Order

Be specific. Use file names. Be the guide you wished you had on day 1.
""")
    ]
    response = llm.invoke(messages)
    return {
        "final_report": response.content,
        "progress": ["✅ Writer agent: report complete"]
    }


# ── Build the LangGraph ──────────────────────────────────────────────────────

def build_graph():
    graph = StateGraph(ArchState)

    graph.add_node("explorer", explorer_agent)
    graph.add_node("analyst", analyst_agent)
    graph.add_node("skeptic", skeptic_agent)
    graph.add_node("writer", writer_agent)

    graph.set_entry_point("explorer")
    graph.add_edge("explorer", "analyst")
    graph.add_edge("analyst", "skeptic")
    graph.add_edge("skeptic", "writer")
    graph.add_edge("writer", END)

    return graph.compile()


# ── Convenience runner ────────────────────────────────────────────────────────

def run_codearch(repo_path: str) -> dict:
    """Run the full multi-agent pipeline on a local repo path."""
    print(f"🔍 Scanning repo: {repo_path}")
    file_tree, file_contents = build_file_tree(repo_path)

    initial_state: ArchState = {
        "repo_path": repo_path,
        "file_tree": file_tree,
        "file_contents": file_contents,
        "explorer_notes": "",
        "analyst_notes": "",
        "skeptic_questions": "",
        "skeptic_answers": "",
        "final_report": "",
        "progress": [f"🗂️ Scanned {len(file_contents)} files"],
    }

    graph = build_graph()
    print("🤖 Running agents...")
    result = graph.invoke(initial_state)

    for msg in result["progress"]:
        print(msg)

    return result


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    result = run_codearch(path)
    print("\n" + "=" * 60)
    print(result["final_report"])