"""Model registry + agent config routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import select

from db.models import AgentConfig, Model
from db.session import get_session
from server.api.auth import require_auth
from server.api.main import app


class ModelCreate(BaseModel):
    model_id: str = Field(...)
    display_name: str | None = None
    location: str = Field(default="external")  # local | external
    tier: str = Field(default="small")  # small | middle | large
    cost_per_1m_tokens: float = 0.0


class ModelOut(BaseModel):
    id: str
    model_id: str
    display_name: str | None
    location: str
    tier: str
    cost_per_1m_tokens: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True



class AgentConfigUpdate(BaseModel):
    agent_name: str = Field(...)
    model_id: str
    temperature: float = 0.0
    max_tokens: int = 4096


@app.get("/api/v1/models", response_model=list[ModelOut])
def list_models(tier: str | None = None, _auth: str = Depends(require_auth)):
    session = get_session()
    try:
        q = select(Model).where(Model.is_active)
        if tier:
            q = q.where(Model.tier == tier)
        models = session.exec(q.order_by(Model.model_id)).all()
        return [ModelOut.model_validate(m) for m in models]
    finally:
        session.close()


@app.post("/api/v1/models", response_model=ModelOut, status_code=201)
def register_model(body: ModelCreate, _auth: str = Depends(require_auth)):
    session = get_session()
    try:
        m = Model(
            model_id=body.model_id,
            display_name=body.display_name,
            location=body.location,
            tier=body.tier,
            cost_per_1m_tokens=body.cost_per_1m_tokens,
        )
        session.add(m)
        session.commit()
        session.refresh(m)
        return ModelOut.model_validate(m)
    finally:
        session.close()
def remove_model(model_id: str, _auth: str = Depends(require_auth)):
    session = get_session()
    try:
        m = session.get(Model, model_id)
        if not m:
            raise HTTPException(404, "Not found")
        m.is_active = False
        session.add(m)
        session.commit()
    finally:
        session.close()


