"""
app/routes/rules.py — Automation rules and workflow triggers.

Endpoints:
  GET    /api/rules                    — List rules
  GET    /api/rules/{id}               — Get single rule
  POST   /api/rules                    — Create rule
  PUT    /api/rules/{id}               — Update rule
  DELETE /api/rules/{id}               — Delete rule
  GET    /api/rules/{id}/executions    — Get rule execution history
"""

import logging
from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.auth import get_current_user
from app.database import get_db
from app.models.rule import Rule
from app.models.rule_execution import RuleExecution

logger = logging.getLogger("agentic_crm")
router = APIRouter(prefix="/api/rules", tags=["rules"])


# ── Pydantic Schemas ──────────────────────────────────────────────────

class ActionConfig(BaseModel):
    action_type: str = Field(..., description="send_email, create_task, update_lead_score, etc.")
    action_params: dict = Field(default_factory=dict)


class RuleBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    trigger_event: str = Field(..., description="enrichment_complete, lead_score_high, email_opened, etc.")
    conditions: dict = Field(default_factory=dict, description="Conditional logic: {field: operator: value}")
    actions: list[ActionConfig]
    is_active: bool = True


class RuleCreate(RuleBase):
    pass


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_event: Optional[str] = None
    conditions: Optional[dict] = None
    actions: Optional[list[ActionConfig]] = None
    is_active: Optional[bool] = None


class RuleResponse(RuleBase):
    rule_id: int
    user_id: int
    execution_count: int
    last_executed_at: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PaginatedRulesResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[RuleResponse]


class RuleExecutionResponse(BaseModel):
    execution_id: int
    rule_id: int
    user_id: int
    prospect_id: Optional[int]
    company_id: Optional[int]
    trigger_event: str
    triggered: bool
    action_taken: Optional[str]
    result: str
    error_message: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class PaginatedExecutionsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[RuleExecutionResponse]


# ── Helper Functions ──────────────────────────────────────────────────

def get_current_user_id(user: Annotated[dict, Depends(get_current_user)]) -> int:
    """Extract user_id from validated JWT token."""
    return user["user_id"]


def evaluate_conditions(conditions: dict, context: dict) -> bool:
    """Evaluate rule conditions against context (prospect/company data)."""
    if not conditions:
        return True

    for field, criteria in conditions.items():
        value = context.get(field)
        if value is None:
            return False

        # Simple operator support: eq, ne, gt, gte, lt, lte, in, contains
        if isinstance(criteria, dict):
            for op, expected in criteria.items():
                if op == "eq" and value != expected:
                    return False
                elif op == "ne" and value == expected:
                    return False
                elif op == "gt" and not (value > expected):
                    return False
                elif op == "gte" and not (value >= expected):
                    return False
                elif op == "lt" and not (value < expected):
                    return False
                elif op == "lte" and not (value <= expected):
                    return False
                elif op == "in" and value not in expected:
                    return False
                elif op == "contains" and expected not in str(value):
                    return False

    return True


# ── Endpoints ─────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedRulesResponse)
async def list_rules(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PaginatedRulesResponse:
    """List automation rules for the current user."""
    query = db.query(Rule).filter(Rule.user_id == user_id)

    if is_active is not None:
        query = query.filter(Rule.is_active == is_active)

    total = query.count()
    rules = (
        query.order_by(desc(Rule.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedRulesResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=[RuleResponse.from_orm(r) for r in rules],
    )


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> RuleResponse:
    """Get a single rule."""
    rule = (
        db.query(Rule)
        .filter(and_(Rule.rule_id == rule_id, Rule.user_id == user_id))
        .first()
    )

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    return RuleResponse.from_orm(rule)


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    request: RuleCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> RuleResponse:
    """Create a new automation rule."""
    rule = Rule(
        user_id=user_id,
        name=request.name,
        description=request.description,
        trigger_event=request.trigger_event,
        conditions=request.conditions,
        actions=[a.dict() for a in request.actions],
        is_active=request.is_active,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)

    logger.info(f"Created rule {rule.rule_id} for user {user_id}")
    return RuleResponse.from_orm(rule)


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    request: RuleUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> RuleResponse:
    """Update a rule."""
    rule = (
        db.query(Rule)
        .filter(and_(Rule.rule_id == rule_id, Rule.user_id == user_id))
        .first()
    )

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    if request.name is not None:
        rule.name = request.name
    if request.description is not None:
        rule.description = request.description
    if request.trigger_event is not None:
        rule.trigger_event = request.trigger_event
    if request.conditions is not None:
        rule.conditions = request.conditions
    if request.actions is not None:
        rule.actions = [a.dict() for a in request.actions]
    if request.is_active is not None:
        rule.is_active = request.is_active

    db.commit()
    db.refresh(rule)

    logger.info(f"Updated rule {rule_id} for user {user_id}")
    return RuleResponse.from_orm(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> None:
    """Delete a rule."""
    rule = (
        db.query(Rule)
        .filter(and_(Rule.rule_id == rule_id, Rule.user_id == user_id))
        .first()
    )

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    db.delete(rule)
    db.commit()

    logger.info(f"Deleted rule {rule_id} for user {user_id}")


@router.get("/{rule_id}/executions", response_model=PaginatedExecutionsResponse)
async def get_rule_executions(
    rule_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PaginatedExecutionsResponse:
    """Get execution history for a rule."""
    # Verify rule belongs to user
    rule = (
        db.query(Rule)
        .filter(and_(Rule.rule_id == rule_id, Rule.user_id == user_id))
        .first()
    )

    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    query = db.query(RuleExecution).filter(RuleExecution.rule_id == rule_id)
    total = query.count()

    executions = (
        query.order_by(desc(RuleExecution.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedExecutionsResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=[RuleExecutionResponse.from_orm(e) for e in executions],
    )
