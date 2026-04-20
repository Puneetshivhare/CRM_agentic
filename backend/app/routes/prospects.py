"""
app/routes/prospects.py — REST API endpoints for prospect management.

Endpoints:
  GET    /api/prospects              — List prospects with filters/pagination
  GET    /api/prospects/{id}         — Get single prospect
  POST   /api/prospects              — Create prospect
  PUT    /api/prospects/{id}         — Update prospect
  DELETE /api/prospects/{id}         — Delete prospect
  POST   /api/prospects/bulk-import  — Import from CSV
"""

import csv
import logging
from io import StringIO
from typing import Optional

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.prospect import Prospect
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger("agentic_crm")
router = APIRouter(prefix="/api/prospects", tags=["prospects"])


# ── Pydantic Schemas ──────────────────────────────────────────────────────

class ProspectBase(BaseModel):
    """Base prospect schema with common fields."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    location: Optional[str] = Field(None, max_length=255)
    linkedin_url: Optional[str] = Field(None, max_length=500)
    website_url: Optional[str] = Field(None, max_length=500)
    company_id: Optional[int] = None


class ProspectCreate(ProspectBase):
    """Schema for creating a prospect."""
    pass


class ProspectUpdate(BaseModel):
    """Schema for updating a prospect (all fields optional)."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    website_url: Optional[str] = None
    company_id: Optional[int] = None
    enrichment_status: Optional[str] = None
    enrichment_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class ProspectResponse(ProspectBase):
    """Schema for returning prospect data."""
    prospect_id: int
    user_id: int
    enrichment_status: str
    enrichment_confidence: float
    last_contacted_at: Optional[str] = None
    email_opens: int
    email_clicks: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PaginatedProspectsResponse(BaseModel):
    """Paginated response wrapper."""
    total: int
    page: int
    per_page: int
    items: list[ProspectResponse]


# ── Helper Functions ──────────────────────────────────────────────────────

def get_current_user_id(user: Annotated[dict, Depends(get_current_user)]) -> int:
    """Extract user_id from validated JWT token."""
    return user["user_id"]


# ── Endpoints ─────────────────────────────────────────────────────────────

@router.get("", response_model=PaginatedProspectsResponse)
async def list_prospects(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    search: Optional[str] = Query(None, description="Search by name, email, or company"),
    enrichment_status: Optional[str] = Query(None, description="Filter by status: pending|enriching|enriched|failed"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> PaginatedProspectsResponse:
    """List prospects with optional filtering and pagination."""
    try:
        query = db.query(Prospect).filter(Prospect.user_id == user_id)

        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    Prospect.first_name.ilike(f"%{search}%"),
                    Prospect.last_name.ilike(f"%{search}%"),
                    Prospect.email.ilike(f"%{search}%"),
                )
            )

        # Apply status filter
        if enrichment_status:
            query = query.filter(Prospect.enrichment_status == enrichment_status)

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        offset = (page - 1) * per_page
        prospects = query.order_by(desc(Prospect.created_at)).offset(offset).limit(per_page).all()

        return PaginatedProspectsResponse(
            total=total,
            page=page,
            per_page=per_page,
            items=prospects,
        )
    except Exception as e:
        logger.error(f"Error listing prospects: {e}")
        raise HTTPException(status_code=500, detail="Failed to list prospects")


@router.get("/{prospect_id}", response_model=ProspectResponse)
async def get_prospect(
    prospect_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ProspectResponse:
    """Get a single prospect by ID."""
    prospect = (
        db.query(Prospect)
        .filter(and_(Prospect.prospect_id == prospect_id, Prospect.user_id == user_id))
        .first()
    )
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return prospect


@router.post("", response_model=ProspectResponse, status_code=status.HTTP_201_CREATED)
async def create_prospect(
    prospect: ProspectCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ProspectResponse:
    """Create a new prospect."""
    try:
        db_prospect = Prospect(
            user_id=user_id,
            email=prospect.email,
            first_name=prospect.first_name,
            last_name=prospect.last_name,
            title=prospect.title,
            phone=prospect.phone,
            location=prospect.location,
            linkedin_url=prospect.linkedin_url,
            website_url=prospect.website_url,
            company_id=prospect.company_id,
            enrichment_status="pending",
            enrichment_confidence=0.0,
        )
        db.add(db_prospect)
        db.commit()
        db.refresh(db_prospect)
        logger.info(f"Created prospect {db_prospect.prospect_id} for user {user_id}")
        return db_prospect
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating prospect: {e}")
        raise HTTPException(status_code=500, detail="Failed to create prospect")


@router.put("/{prospect_id}", response_model=ProspectResponse)
async def update_prospect(
    prospect_id: int,
    prospect_update: ProspectUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ProspectResponse:
    """Update an existing prospect."""
    try:
        db_prospect = (
            db.query(Prospect)
            .filter(and_(Prospect.prospect_id == prospect_id, Prospect.user_id == user_id))
            .first()
        )
        if not db_prospect:
            raise HTTPException(status_code=404, detail="Prospect not found")

        # Update only provided fields
        update_data = prospect_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_prospect, field, value)

        db.commit()
        db.refresh(db_prospect)
        logger.info(f"Updated prospect {prospect_id} for user {user_id}")
        return db_prospect
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating prospect: {e}")
        raise HTTPException(status_code=500, detail="Failed to update prospect")


@router.delete("/{prospect_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prospect(
    prospect_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> None:
    """Delete a prospect."""
    try:
        db_prospect = (
            db.query(Prospect)
            .filter(and_(Prospect.prospect_id == prospect_id, Prospect.user_id == user_id))
            .first()
        )
        if not db_prospect:
            raise HTTPException(status_code=404, detail="Prospect not found")

        db.delete(db_prospect)
        db.commit()
        logger.info(f"Deleted prospect {prospect_id} for user {user_id}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting prospect: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete prospect")


@router.post("/bulk-import")
async def bulk_import_prospects(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> dict:
    """Import prospects from CSV file."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        contents = await file.read()
        csv_text = contents.decode("utf-8")
        csv_reader = csv.DictReader(StringIO(csv_text))

        created_count = 0
        errors = []

        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
            try:
                prospect = Prospect(
                    user_id=user_id,
                    email=row.get("email") or None,
                    first_name=row.get("first_name") or None,
                    last_name=row.get("last_name") or None,
                    title=row.get("title") or None,
                    phone=row.get("phone") or None,
                    location=row.get("location") or None,
                    linkedin_url=row.get("linkedin_url") or None,
                    website_url=row.get("website_url") or None,
                    company_id=int(row.get("company_id")) if row.get("company_id") else None,
                    enrichment_status="pending",
                    enrichment_confidence=0.0,
                )
                db.add(prospect)
                created_count += 1
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})

        db.commit()
        logger.info(f"Bulk imported {created_count} prospects for user {user_id}")

        return {
            "status": "success",
            "created": created_count,
            "errors": errors if errors else None,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error during bulk import: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to import CSV: {str(e)}")
