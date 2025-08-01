from uuid import uuid4
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import HTTPException
from typing import Optional

# http://localhost:8000/docs

# Create a FastAPI instance
app = FastAPI()

sessions = {}

# Pydantic model for validating resume submission
class ResumeSubmission(BaseModel):
    latex_code: str
    job_url: str

# Defind what the suggesttions are
class Suggestion(BaseModel):
    id: str
    section: str
    original_text: str
    suggested_text: str
    reason: Optional[str] = None
    status: str = "pending"

@app.post("/submit_resume")
def submit_resume(submission: ResumeSubmission):
    session_id = f"session_{len(sessions) + 1}"
    sessions[session_id] = {
        "latex_code": submission.latex_code,
        "job_url": submission.job_url,
        "status": "submitted",
        "suggestions": [] # where the suggestions are stored
    }
    return {"session_id": session_id}

@app.get("/session/{session_id}")
def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]

@app.post("/session/{session_id}/status")
def update_status(session_id: str, status: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    sessions[session_id]["status"] = status
    return {"session_id": session_id, "new_status": status}

@app.post("/session/{session_id}/add_suggestion")
def add_suggestion(session_id: str, suggestion: Suggestion):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    # Generate a unique id for the suggestion
    suggestion_with_id = suggestion.dict()
    suggestion_with_id['id'] = str(uuid4())
    sessions[session_id]["suggestions"].append(suggestion_with_id)
    return {"message": "Suggestion added", "suggestion": suggestion_with_id}

# Apporve and Reject Suggestions - need to convert to integer, have a session_id
@app.post("/session/{session_id}/approve_suggestion/{suggestion_id}")
def approve_suggestion(session_id: str, suggestion_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    for suggestion in sessions[session_id]["suggestions"]:
        if suggestion["id"] == suggestion_id:
            suggestion["status"] = "approved"
            return {"message": "Suggestion approved", "suggestion": suggestion}
    raise HTTPException(status_code=404, detail="Suggestion not found")

@app.post("/session/{session_id}/reject_suggestion/{suggestion_id}")
def reject_suggestion(session_id: str, suggestion_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    for suggestion in sessions[session_id]["suggestions"]:
        if suggestion["id"] == suggestion_id:
            suggestion["status"] = "rejected"
            return {"message": "Suggestion rejected", "suggestion": suggestion}
    return {'error': 'Suggestion not found'}

# Get the final latex code
@app.get("/session/{session_id}/final_resume")
def get_final_resume(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = sessions[session_id]
    latex_code = session['latex_code']
    # Apply all approved suggestions
    for suggestion in session['suggestions']:
        if suggestion['status'] == 'approved':
            latex_code = latex_code.replace(suggestion['original_text'], suggestion['suggested_text'])
    return {
        'original_latex': session['latex_code'],
        'final_latex': latex_code,
        'approved_suggestions': [s for s in session['suggestions'] if s['status'] == 'approved']
    }