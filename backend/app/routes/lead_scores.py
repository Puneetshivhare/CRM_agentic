"""
app/routes/lead_scores.py — Lead scoring and sales prioritization.

Endpoints:
  GET    /api/lead-scores              — List prospects by lead score
  GET    /api/lead-scores/{prospect_id} — Get lead score for prospect
  POST   /api/lead-scores/calculate    — Calculate/recalculate scores
  PUT    /api/lead-scores/{prospect_id} — Adjust manual score modifiers
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
from app.models.lead_score import LeadScore
from app.models.prospect import Prospect
from app.models.company import Company
from app.models.interaction import Interaction

logger = logging.getLogger("agentic_crm")
router = APIRouter(prefix="/api/lead-scores", tags=["lead_scores"])


# ── Pydantic Schemas ──────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    industry: float = 0.0
    company_size: float = 0.0
    funding_stage: float = 0.0
    emails_opened: int = 0
    links_clicked: int = 0
    replies: int = 0


class LeadScoreCreate(BaseModel):
    prospect_id: int = Field(..., gt=0)
    fit_score: Optional[float] = None
    engagement_score: Optional[float] = None
    propensity_score: Optional[float] = None


class LeadScoreUpdate(BaseModel):
    fit_score: Optional[float] = None
    engagement_score: Optional[float] = None
    propensity_score: Optional[float] = None


class LeadScoreResponse(BaseModel):
    score_id: int
    prospect_id: int
    company_id: Optional[int]
    fit_score: float
    engagement_score: float
    propensity_score: float
    total_score: float
    grade: str
    is_hot_lead: bool
    score_breakdown: Optional[dict]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PaginatedLeadScoresResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[LeadScoreResponse]


# ── Helper Functions ──────────────────────────────────────────────────

def get_current_user_id(user: Annotated[dict, Depends(get_current_user)]) -> int:
    """Extract user_id from validated JWT token."""
    return user["user_id"]


def calculate_fit_score(company: Optional[Company]) -> float:
    """Calculate company fit score (0-100) based on firmographics."""
    if not company:
        return 0.0

    fit = 0.0

    # Industry scoring (30 points)
    target_industries = ["B2B SaaS", "Enterprise Software", "FinTech", "MarTech"]
    if company.industry and company.industry in target_industries:
        fit += 30.0
    elif company.industry:
        fit += 15.0

    # Company size scoring (35 points)
    if company.headcount:
        if 50 <= company.headcount <= 5000:
            fit += 35.0
        elif 20 <= company.headcount < 50:
            fit += 25.0
        elif company.headcount > 5000:
            fit += 20.0
        else:
            fit += 10.0

    # Funding stage scoring (35 points)
    if company.funding_stage:
        stage_scores = {
            "Seed": 20.0,
            "Series A": 30.0,
            "Series B": 35.0,
            "Series C": 35.0,
            "Series D+": 32.0,
            "Public": 25.0,
        }
        fit += stage_scores.get(company.funding_stage, 10.0)

    return min(fit, 100.0)


def calculate_engagement_score(prospect_id: int, db: Session) -> float:
    """Calculate engagement score (0-100) from interaction history."""
    interactions = db.query(Interaction).filter(
        Interaction.prospect_id == prospect_id
    ).all()

    if not interactions:
        return 0.0

    engagement = 0.0
    opens = sum(1 for i in interactions if i.interaction_type == "email_opened")
    clicks = sum(1 for i in interactions if i.interaction_type == "link_clicked")
    replies = sum(1 for i in interactions if i.interaction_type == "reply")

    # Opens: 30 points (max 5 opens = 30)
    engagement += min(opens * 6.0, 30.0)
    # Clicks: 40 points (max 5 clicks = 40)
    engagement += min(clicks * 8.0, 40.0)
    # Replies: 30 points (each reply = 30)
    engagement += min(replies * 30.0, 30.0)

    return min(engagement, 100.0)


def calculate_propensity_score(fit: float, engagement: float) -> float:
    """Calculate propensity to convert (0-100) from fit and engagement."""
    return (fit * 0.6 + engagement * 0.4)


def calculate_total_score(fit: float, engagement: float, propensity: float) -> tuple[float, str]:
    """Calculate weighted total score and grade letter."""
    total = (fit * 0.35 + engagement * 0.25 + propensity * 0.4)
    total = min(total, 100.0)

    if total >= 90:
        grade = "A"
    elif total >= 80:
        grade = "B"
    elif total >= 70:
        grade = "C"
    elif total >= 60:
        grade = "D"
    else:
        grade = "F"

    return total, grade


# ── Endpoints ─────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedLeadScoresResponse)
async def list_lead_scores(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("total_score", regex="^(total_score|grade|fit_score|engagement_score)$"),
    min_score: float = Query(0.0, ge=0.0, le=100.0),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PaginatedLeadScoresResponse:
    """List prospects by lead score (highest first)."""
    query = db.query(LeadScore).filter(
        and_(
            LeadScore.user_id == user_id,
            LeadScore.total_score >= min_score
        )
    )

    total = query.count()

    # Sort by field
    if sort_by == "total_score":
        query = query.order_by(desc(LeadScore.total_score))
    elif sort_by == "fit_score":
        query = query.order_by(desc(LeadScore.fit_score))
    elif sort_by == "engagement_score":
        query = query.order_by(desc(LeadScore.engagement_score))
    elif sort_by == "grade":
        query = query.order_by(LeadScore.grade)

    scores = (
        query.offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedLeadScoresResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=[LeadScoreResponse.from_orm(s) for s in scores],
    )


@router.get("/{prospect_id}", response_model=LeadScoreResponse)
async def get_lead_score(
    prospect_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> LeadScoreResponse:
    """Get lead score for a prospect."""
    score = (
        db.query(LeadScore)
        .filter(
            and_(
                LeadScore.prospect_id == prospect_id,
                LeadScore.user_id == user_id,
            )
        )
        .first()
    )

    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead score not found",
        )

    return LeadScoreResponse.from_orm(score)


@router.post("/{prospect_id}/calculate", response_model=LeadScoreResponse)
async def calculate_lead_score(
    prospect_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> LeadScoreResponse:
    """Calculate or recalculate lead score for a prospect."""
    # Verify prospect belongs to user
    prospect = (
        db.query(Prospect)
        .filter(
            and_(
                Prospect.prospect_id == prospect_id,
                Prospect.user_id == user_id,
            )
        )
        .first()
    )

    if not prospect:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prospect not found",
        )

    # Get company (if linked)
    company = None
    if prospect.company_id:
        company = db.query(Company).filter(Company.company_id == prospect.company_id).first()

    # Calculate component scores
    fit_score = calculate_fit_score(company)
    engagement_score = calculate_engagement_score(prospect_id, db)
    propensity_score = calculate_propensity_score(fit_score, engagement_score)
    total_score, grade = calculate_total_score(fit_score, engagement_score, propensity_score)

    # Check if score exists
    score = (
        db.query(LeadScore)
        .filter(
            and_(
                LeadScore.prospect_id == prospect_id,
                LeadScore.user_id == user_id,
            )
        )
        .first()
    )

    score_breakdown = {
        "industry": round(fit_score * 0.3, 1) if company else 0,
        "company_size": round(fit_score * 0.35, 1) if company else 0,
        "funding_stage": round(fit_score * 0.35, 1) if company else 0,
        "emails_opened": len([i for i in (prospect.interactions or []) if getattr(i, 'interaction_type', None) == "email_opened"]),
    }

    if score:
        score.fit_score = fit_score
        score.engagement_score = engagement_score
        score.propensity_score = propensity_score
        score.total_score = total_score
        score.grade = grade
        score.is_hot_lead = total_score >= 80
        score.score_breakdown = score_breakdown
        score.updated_at = datetime.utcnow()
    else:
        score = LeadScore(
            prospect_id=prospect_id,
            company_id=prospect.company_id,
            user_id=user_id,
            fit_score=fit_score,
            engagement_score=engagement_score,
            propensity_score=propensity_score,
            total_score=total_score,
            grade=grade,
            is_hot_lead=total_score >= 80,
            score_breakdown=score_breakdown,
        )
        db.add(score)

    db.commit()
    db.refresh(score)

    logger.info(f"Calculated lead score for prospect {prospect_id}: {total_score:.1f} ({grade})")
    return LeadScoreResponse.from_orm(score)


@router.put("/{prospect_id}", response_model=LeadScoreResponse)
async def update_lead_score(
    prospect_id: int,
    request: LeadScoreUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> LeadScoreResponse:
    """Update/adjust component scores for a prospect."""
    score = (
        db.query(LeadScore)
        .filter(
            and_(
                LeadScore.prospect_id == prospect_id,
                LeadScore.user_id == user_id,
            )
        )
        .first()
    )

    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead score not found",
        )

    # Update components
    if request.fit_score is not None:
        score.fit_score = min(max(request.fit_score, 0.0), 100.0)
    if request.engagement_score is not None:
        score.engagement_score = min(max(request.engagement_score, 0.0), 100.0)
    if request.propensity_score is not None:
        score.propensity_score = min(max(request.propensity_score, 0.0), 100.0)

    # Recalculate total and grade
    total, grade = calculate_total_score(
        score.fit_score,
        score.engagement_score,
        score.propensity_score
    )
    score.total_score = total
    score.grade = grade
    score.is_hot_lead = total >= 80
    score.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(score)

    logger.info(f"Updated lead score for prospect {prospect_id}: {total:.1f} ({grade})")
    return LeadScoreResponse.from_orm(score)
