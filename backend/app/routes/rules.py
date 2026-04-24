"""Minimal automation rule endpoints for the current frontend."""

import logging
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.rule import Rule
from app.models.rule_execution import RuleExecution
from app.utils.logger import trace_logic

logger = logging.getLogger("agentic_crm")
router = APIRouter(prefix="/api/rules", tags=["rules"])


class ActionConfig(BaseModel):
    action_type: str
    action_params: dict = Field(default_factory=dict)


class RuleBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    trigger_event: str
    conditions: dict = Field(default_factory=dict)
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


class RuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: int
    user_id: int
    name: str
    description: Optional[str]
    trigger_event: str
    conditions: dict
    actions: list[ActionConfig]
    is_active: bool
    execution_count: int
    last_executed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class PaginatedRulesResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[RuleResponse]


class RuleExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    created_at: datetime


class PaginatedExecutionsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[RuleExecutionResponse]


def get_current_user_id(user: Annotated[dict, Depends(get_current_user)]) -> int:
    return user["user_id"]


def _extract_rule_definition(rule: Rule) -> dict:
    return dict(rule.rule_definition or {})


def _build_rule_response(db: Session, rule: Rule) -> RuleResponse:
    rule_definition = _extract_rule_definition(rule)
    last_execution = (
        db.query(RuleExecution)
        .filter(RuleExecution.rule_id == rule.rule_id)
        .order_by(desc(RuleExecution.created_at))
        .first()
    )

    return RuleResponse(
        rule_id=rule.rule_id,
        user_id=rule.user_id,
        name=rule.rule_name,
        description=rule.description,
        trigger_event=rule_definition.get("trigger_event", ""),
        conditions=rule_definition.get("conditions", {}),
        actions=rule_definition.get("actions", []),
        is_active=rule.is_active,
        execution_count=rule.execution_count,
        last_executed_at=last_execution.created_at if last_execution else None,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.get("", response_model=PaginatedRulesResponse)
async def list_rules(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PaginatedRulesResponse:
    trace_logic(logger, "rules.list.request", user_id=user_id, page=page, per_page=per_page, is_active=is_active)
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
        items=[_build_rule_response(db, rule) for rule in rules],
    )


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> RuleResponse:
    rule = (
        db.query(Rule)
        .filter(and_(Rule.rule_id == rule_id, Rule.user_id == user_id))
        .first()
    )
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")
    return _build_rule_response(db, rule)


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    request: RuleCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> RuleResponse:
    rule = Rule(
        user_id=user_id,
        rule_name=request.name,
        rule_type="workflow",
        rule_definition={
            "trigger_event": request.trigger_event,
            "conditions": request.conditions,
            "actions": [action.model_dump() for action in request.actions],
        },
        description=request.description,
        is_active=request.is_active,
    )

    db.add(rule)
    db.commit()
    db.refresh(rule)
    logger.info("Created rule %s for user %s", rule.rule_id, user_id)
    trace_logic(logger, "rules.create.success", user_id=user_id, rule_id=rule.rule_id, name=rule.rule_name)
    return _build_rule_response(db, rule)


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    request: RuleUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> RuleResponse:
    rule = (
        db.query(Rule)
        .filter(and_(Rule.rule_id == rule_id, Rule.user_id == user_id))
        .first()
    )
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    if request.name is not None:
        rule.rule_name = request.name
    if request.description is not None:
        rule.description = request.description
    if request.is_active is not None:
        rule.is_active = request.is_active

    rule_definition = _extract_rule_definition(rule)
    if request.trigger_event is not None:
        rule_definition["trigger_event"] = request.trigger_event
    if request.conditions is not None:
        rule_definition["conditions"] = request.conditions
    if request.actions is not None:
        rule_definition["actions"] = [action.model_dump() for action in request.actions]
    rule.rule_definition = rule_definition

    db.commit()
    db.refresh(rule)
    logger.info("Updated rule %s for user %s", rule.rule_id, user_id)
    trace_logic(logger, "rules.update.success", user_id=user_id, rule_id=rule.rule_id, name=rule.rule_name)
    return _build_rule_response(db, rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> None:
    rule = (
        db.query(Rule)
        .filter(and_(Rule.rule_id == rule_id, Rule.user_id == user_id))
        .first()
    )
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rule not found")

    db.delete(rule)
    db.commit()
    logger.info("Deleted rule %s for user %s", rule_id, user_id)
    trace_logic(logger, "rules.delete.success", user_id=user_id, rule_id=rule_id)


@router.get("/{rule_id}/executions", response_model=PaginatedExecutionsResponse)
async def get_rule_executions(
    rule_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PaginatedExecutionsResponse:
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
        items=[RuleExecutionResponse.model_validate(execution) for execution in executions],
    )
