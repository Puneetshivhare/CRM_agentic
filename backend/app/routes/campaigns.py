"""
app/routes/campaigns.py — Email campaign and sequence management.

Endpoints:
  GET    /api/campaigns              — List campaigns
  GET    /api/campaigns/{id}         — Get single campaign
  POST   /api/campaigns              — Create campaign
  PUT    /api/campaigns/{id}         — Update campaign
  DELETE /api/campaigns/{id}         — Delete campaign
  POST   /api/campaigns/{id}/enroll  — Enroll prospects in campaign
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.auth import get_current_user
from app.database import get_db
from app.models.campaign import Campaign
from app.models.prospect import Prospect

logger = logging.getLogger("agentic_crm")
router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


# ── Pydantic Schemas ──────────────────────────────────────────────────

class SequenceStep(BaseModel):
    day: int = Field(..., ge=0, description="Days after enrollment to send")
    subject: str = Field(..., max_length=255)
    body: str


class CampaignBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    sequence_steps: list[SequenceStep]
    target_criteria: Optional[dict] = None
    is_active: bool = True


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sequence_steps: Optional[list[SequenceStep]] = None
    target_criteria: Optional[dict] = None
    is_active: Optional[bool] = None


class CampaignResponse(CampaignBase):
    campaign_id: int
    user_id: int
    enrolled_count: int
    opened_count: int
    clicked_count: int
    replied_count: int
    conversion_rate: float
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PaginatedCampaignsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[CampaignResponse]


class EnrollRequest(BaseModel):
    prospect_ids: list[int] = Field(..., min_items=1)


class EnrollResponse(BaseModel):
    enrolled: int
    status: str


# ── Helper Functions ──────────────────────────────────────────────────

def get_current_user_id(user: Annotated[dict, Depends(get_current_user)]) -> int:
    """Extract user_id from validated JWT token."""
    return user["user_id"]


# ── Endpoints ─────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedCampaignsResponse)
async def list_campaigns(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PaginatedCampaignsResponse:
    """List campaigns for the current user."""
    query = db.query(Campaign).filter(Campaign.user_id == user_id)

    total = query.count()
    campaigns = (
        query.order_by(desc(Campaign.created_at))
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedCampaignsResponse(
        total=total,
        page=page,
        per_page=per_page,
        items=[CampaignResponse.from_orm(c) for c in campaigns],
    )


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> CampaignResponse:
    """Get a single campaign."""
    campaign = (
        db.query(Campaign)
        .filter(and_(Campaign.campaign_id == campaign_id, Campaign.user_id == user_id))
        .first()
    )

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    return CampaignResponse.from_orm(campaign)


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    request: CampaignCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> CampaignResponse:
    """Create a new email campaign."""
    campaign = Campaign(
        user_id=user_id,
        name=request.name,
        description=request.description,
        sequence_steps=[s.dict() for s in request.sequence_steps],
        target_criteria=request.target_criteria,
        is_active=request.is_active,
    )

    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    logger.info(f"Created campaign {campaign.campaign_id} for user {user_id}")
    return CampaignResponse.from_orm(campaign)


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    request: CampaignUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> CampaignResponse:
    """Update a campaign."""
    campaign = (
        db.query(Campaign)
        .filter(and_(Campaign.campaign_id == campaign_id, Campaign.user_id == user_id))
        .first()
    )

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if request.name is not None:
        campaign.name = request.name
    if request.description is not None:
        campaign.description = request.description
    if request.sequence_steps is not None:
        campaign.sequence_steps = [s.dict() for s in request.sequence_steps]
    if request.target_criteria is not None:
        campaign.target_criteria = request.target_criteria
    if request.is_active is not None:
        campaign.is_active = request.is_active

    db.commit()
    db.refresh(campaign)

    logger.info(f"Updated campaign {campaign_id} for user {user_id}")
    return CampaignResponse.from_orm(campaign)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> None:
    """Delete a campaign."""
    campaign = (
        db.query(Campaign)
        .filter(and_(Campaign.campaign_id == campaign_id, Campaign.user_id == user_id))
        .first()
    )

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    db.delete(campaign)
    db.commit()

    logger.info(f"Deleted campaign {campaign_id} for user {user_id}")


@router.post("/{campaign_id}/enroll", response_model=EnrollResponse)
async def enroll_prospects(
    campaign_id: int,
    request: EnrollRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    """Enroll prospects in a campaign (multi-touch email sequence)."""
    campaign = (
        db.query(Campaign)
        .filter(and_(Campaign.campaign_id == campaign_id, Campaign.user_id == user_id))
        .first()
    )

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    # Verify prospects belong to user
    prospects = (
        db.query(Prospect)
        .filter(
            and_(
                Prospect.prospect_id.in_(request.prospect_ids),
                Prospect.user_id == user_id,
            )
        )
        .all()
    )

    if len(prospects) != len(request.prospect_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some prospects not found or don't belong to you",
        )

    # In production, would create CampaignEnrollment records
    campaign.enrolled_count += len(prospects)
    db.commit()

    logger.info(f"Enrolled {len(prospects)} prospects in campaign {campaign_id}")

    return {"enrolled": len(prospects), "status": "success"}
