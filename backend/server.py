"""
FastAPI server for CodeArch
Provides REST + SSE streaming endpoints
"""

import os
import json
import asyncio
import tempfile
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents import build_graph, build_file_tree, ArchState

app = FastAPI(title="CodeArch API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyseRequest(BaseModel):
    repo_url: str       # GitHub URL or local path
    use_local: bool = False


def clone_repo(repo_url: str, target_dir: str) -> str:
    """Clone a GitHub repo and return the local path."""
    try:
        result = subprocess.run(
            ["git", "clone", "--depth=1", repo_url, target_dir],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        return target_dir
    except subprocess.TimeoutExpired:
        raise RuntimeError("Git clone timed out (>60s). Try a smaller repo.")


@app.get("/health")
def health():
    return {"status": "ok", "service": "codearch"}


@app.post("/analyse/stream")
async def analyse_stream(req: AnalyseRequest):
    """
    Streams agent progress via Server-Sent Events (SSE).
    Each event is a JSON object: {type, data}
    Types: progress | result | error | done
    """

    async def event_generator():
        tmp_dir = None
        try:
            # Step 1: get the repo
            if req.use_local:
                repo_path = req.repo_url
                if not Path(repo_path).exists():
                    yield f"data: {json.dumps({'type':'error','data':'Local path not found'})}\n\n"
                    return
            else:
                yield f"data: {json.dumps({'type':'progress','data':'⏬ Cloning repository...'})}\n\n"
                await asyncio.sleep(0.1)
                tmp_dir = tempfile.mkdtemp(prefix="codearch_")
                try:
                    loop = asyncio.get_event_loop()
                    repo_path = await loop.run_in_executor(
                        None, clone_repo, req.repo_url, tmp_dir
                    )
                except RuntimeError as e:
                    yield f"data: {json.dumps({'type':'error','data':str(e)})}\n\n"
                    return

            # Step 2: scan files
            yield f"data: {json.dumps({'type':'progress','data':'📂 Scanning files...'})}\n\n"
            await asyncio.sleep(0.1)
            loop = asyncio.get_event_loop()
            file_tree, file_contents = await loop.run_in_executor(
                None, build_file_tree, repo_path
            )

            file_count = len(file_contents)
            yield f"data: {json.dumps({'type':'progress','data':f'✅ Found {file_count} files to analyse'})}\n\n"
            await asyncio.sleep(0.1)

            # Step 3: build initial state
            initial_state: ArchState = {
                "repo_path": repo_path,
                "file_tree": file_tree,
                "file_contents": file_contents,
                "explorer_notes": "",
                "analyst_notes": "",
                "skeptic_questions": "",
                "skeptic_answers": "",
                "final_report": "",
                "progress": [],
            }

            # Step 4: stream agent progress
            agent_labels = {
                "explorer": "🔭 Explorer agent: mapping structure...",
                "analyst":  "🔬 Analyst agent: finding patterns & debt...",
                "skeptic":  "🤔 Skeptic agent: challenging assumptions...",
                "writer":   "✍️  Writer agent: composing report...",
            }

            graph = build_graph()

            result = None
            for node_name, label in agent_labels.items():
                yield f"data: {json.dumps({'type':'progress','data':label})}\n\n"
                await asyncio.sleep(0.1)

            # Run full graph in executor (LangGraph is sync)
            result = await loop.run_in_executor(None, graph.invoke, initial_state)

            # Send progress messages from agents
            for msg in result.get("progress", []):
                yield f"data: {json.dumps({'type':'progress','data':msg})}\n\n"
                await asyncio.sleep(0.05)

            # Send the final report
            report = result.get("final_report", "No report generated.")
            yield f"data: {json.dumps({'type':'result','data':report})}\n\n"
            yield f"data: {json.dumps({'type':'done','data':'Analysis complete'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type':'error','data':str(e)})}\n\n"
        finally:
            # Cleanup temp dir
            if tmp_dir and Path(tmp_dir).exists():
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)