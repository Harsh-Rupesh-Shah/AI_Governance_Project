import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
import logging

from app.schemas.api_models import GovernanceRequest, GovernanceResponse, AuditLogResponse
from app.api.deps import get_current_user, get_db, get_threads_collection
from app.graph.workflow import app as workflow_app

router = APIRouter()
logger = logging.getLogger(__name__)

def get_active_thread(username: str):
    threads_col = get_threads_collection()
    # Find a thread that is marked as 'clarifying'
    thread = threads_col.find_one({"username": username, "status": "clarifying"})
    if thread:
        return thread["thread_id"], thread["request_text"]
    return None, None

def set_active_thread(username: str, thread_id: str, status: str, request_text: str):
    threads_col = get_threads_collection()
    threads_col.update_one(
        {"username": username, "thread_id": thread_id},
        {"$set": {"status": status, "request_text": request_text, "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )

@router.post("/request", response_model=GovernanceResponse)
def submit_request(req: GovernanceRequest, current_user: dict = Depends(get_current_user)):
    username = current_user["username"]
    user_input = req.request_text
    
    # 1. Check for active Clarify thread
    active_thread_id, prev_text = get_active_thread(username)
    
    if active_thread_id:
        thread_id = active_thread_id
        # Append the new input to the history
        current_request_text = f"{prev_text}\n\nUser Clarification: {user_input}"
    else:
        thread_id = str(uuid.uuid4())
        current_request_text = user_input
        
    initial_state = {
        "request_id": thread_id,
        "user_id": username,
        "request_text": current_request_text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        # Run graph
        for event in workflow_app.stream(initial_state, config=config, stream_mode="updates"):
            pass # Exhaust stream
            
        final_snapshot = workflow_app.get_state(config)
        final_state = final_snapshot.values
        
    except Exception as e:
        logger.error(f"Error during workflow execution: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during AI evaluation")

    decision = final_state.get('decision', 'N/A')
    reason = final_state.get('decision_reason', 'N/A')
    risk_score = final_state.get('risk_score')
    audit_id = final_state.get('audit_id')
    
    # 2. Update Thread Status based on Decision
    if decision == "CLARIFY":
        set_active_thread(username, thread_id, "clarifying", current_request_text)
    else:
        # Close thread
        set_active_thread(username, thread_id, "closed", current_request_text)
        
    return GovernanceResponse(
        decision=decision,
        decision_reason=reason,
        risk_score=risk_score,
        audit_id=audit_id,
        thread_id=thread_id
    )

@router.get("/audit", response_model=list[AuditLogResponse])
def get_audit_logs(current_user: dict = Depends(get_current_user)):
    # Only admins or Finance Ops should see all audits. 
    # For now, let's just return all for demo purposes.
    db = get_db()
    
    # LangGraph Store MongoDB uses 'namespace' array and puts data in 'value'
    logs = list(db["memories"].find({"namespace": ["audit", "trails"]}).sort("updated_at", -1).limit(50))
    
    response = []
    for log in logs:
        # The actual data we saved is inside the 'value' field of the store document
        audit_data = log.get("value", {})
        if audit_data:
            response.append(AuditLogResponse(**audit_data))
        
    return response
