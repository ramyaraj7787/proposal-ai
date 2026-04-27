import sys
from pathlib import Path
from typing import Optional
import uuid

# Setup path so imports work correctly
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.config import get_settings
from graph.builder import build_proposal_graph
from schemas.state_schema import ProposalInput
from graph.state import ProposalState
from services.ppt.ppt_builder import build_proposal_ppt
from services.generation.chat_updater import update_proposal_via_chat
from services.ingestion.folder_watcher import start_folder_watcher
import shutil

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start the watchdog observer when the app starts
    observer = start_folder_watcher()
    yield
    # Stop the watchdog observer when the app shuts down
    if observer:
        observer.stop()
        observer.join()

app = FastAPI(title="AI Proposal Tool API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = ROOT_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

sessions: dict[str, dict] = {}
settings = get_settings()
graph = build_proposal_graph(settings)

@app.get("/")
async def serve_index():
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return {"message": "Frontend not found"}

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/api/upload")
async def upload_rfp(
    file: UploadFile = File(...),
    country: str = Form(...),
    sector: str = Form(...),
    domain: str = Form(...),
    client: str = Form(...),
    proposal_objective: str = Form(...),
    assistant_prompt: Optional[str] = Form("Emphasize business impact, delivery credibility, and differentiators.")
):
    try:
        session_id = str(uuid.uuid4())
        
        upload_dir = settings.output_dir / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = upload_dir / f"{session_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            f.write(await file.read())
            
        proposal_input = ProposalInput(
            rfp_path=str(file_path),
            country=country,
            sector=sector,
            domain=domain,
            client=client,
            proposal_objective=proposal_objective,
            assistant_prompt=assistant_prompt
        )
        
        initial_state = ProposalState(**proposal_input.model_dump())
        
        print(f"Starting pipeline for session {session_id}...")
        result = graph.invoke(initial_state)
        print(f"Pipeline finished for session {session_id}.")
        
        sessions[session_id] = {
            "state": result,
            "chat_history": [
                {"role": "assistant", "content": "I have generated the initial proposal. How would you like me to adjust it?"}
            ]
        }
        
        return {
            "session_id": session_id,
            "proposal_sections": result.get("proposal_sections", []),
            "ppt_output_path": result.get("ppt_output_path", "")
        }
    except Exception as e:
        print(f"Error in upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(request: ChatRequest):
    session = sessions.get(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    state = session["state"]
    chat_history = session["chat_history"]
    
    chat_history.append({"role": "user", "content": request.message})
    
    current_sections = state.get("proposal_sections", [])
    updated_sections, ai_message = update_proposal_via_chat(
        current_sections=current_sections,
        chat_history=chat_history,
        settings=settings
    )
    
    state["proposal_sections"] = updated_sections
    state["ppt_output_path"] = build_proposal_ppt(state, settings)
    
    chat_history.append({"role": "assistant", "content": ai_message})
    
    return {
        "proposal_sections": updated_sections,
        "chat_history": chat_history,
        "ppt_output_path": state["ppt_output_path"]
    }

@app.get("/api/download/{session_id}")
async def download_ppt(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    ppt_path = session["state"].get("ppt_output_path")
    if not ppt_path or not Path(ppt_path).exists():
        raise HTTPException(status_code=404, detail="PPT file not found")
        
    return FileResponse(
        path=ppt_path,
        filename=Path(ppt_path).name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

@app.post("/api/knowledge-base")
async def upload_knowledge_file(file: UploadFile = File(...)):
    """
    Endpoint for uploading a historical file to the knowledge base.
    The background folder_watcher will automatically pick it up and reindex!
    """
    try:
        raw_dir = ROOT_DIR / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        file_path = raw_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"message": f"File {file.filename} added to knowledge base! Re-indexing automatically triggered in background."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
