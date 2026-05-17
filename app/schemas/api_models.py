from pydantic import BaseModel, Field
from typing import Optional, List, Any

# Auth Schemas
class UserRegister(BaseModel):
    username: str
    password: str
    role: Optional[str] = "employee" # employee or admin

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Governance Request Schemas
class GovernanceRequest(BaseModel):
    request_text: str

class GovernanceResponse(BaseModel):
    decision: str
    decision_reason: str
    risk_score: Optional[float] = None
    audit_id: Optional[str] = None
    thread_id: Optional[str] = None

# Audit Log Response Schema
class AuditLogResponse(BaseModel):
    audit_id: str
    created_at: str
    request_text: str
    action_type: Optional[str] = None
    refund_amount: Optional[float] = None
    customer_id: Optional[str] = None
    risk_score: Optional[float] = None
    decision: str
    decision_reason: str
    assigned_reviewer: Optional[str] = None

    class Config:
        extra = "allow"
