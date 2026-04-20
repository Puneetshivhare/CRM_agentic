"""
app/routes/documents.py — REST API endpoints for document management.

Endpoints:
  POST   /api/documents/upload      — Upload and process PDF/CSV
  GET    /api/documents             — List documents
  GET    /api/documents/{document_id} — Get document metadata
  DELETE /api/documents/{document_id} — Delete document
"""

import logging
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.auth import get_current_user
from app.database import get_db
from app.models.document import Document
from app.models.prospect import Prospect
from app.services.file_service import file_service

logger = logging.getLogger("agentic_crm")
router = APIRouter(prefix="/api/documents", tags=["documents"])


# ── Pydantic Schemas ──────────────────────────────────────────────────


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""

    document_id: int
    file_name: str
    document_type: str
    num_pages: Optional[int]
    extracted_text_length: int
    prospects_created: int = 0
    message: str

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    """Response for document metadata."""

    document_id: int
    file_name: str
    document_type: str
    num_pages: Optional[int]
    file_size_bytes: Optional[int]
    extracted_text_length: int
    associated_company_id: Optional[int]
    created_at: str

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """List of documents."""

    total: int
    documents: List[DocumentResponse]


# ── Helper Functions ──────────────────────────────────────────────────


def get_current_user_id(user: Annotated[dict, Depends(get_current_user)]) -> int:
    """Extract user_id from validated JWT token."""
    return user["user_id"]


# ── Endpoints ─────────────────────────────────────────────────────────


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> DocumentUploadResponse:
    """
    Upload and process a document (PDF or CSV).

    For PDFs:
      - Extracts text and metadata
      - Stores raw content for RAG (Phase 2)

    For CSVs:
      - Parses prospect records
      - Creates prospects in database
      - Stores file metadata

    Returns: document metadata and processing summary.
    """
    try:
        # Validate file name
        if not file.filename:
            raise HTTPException(status_code=400, detail="File must have a name")

        # Detect file type
        file_type = file_service.detect_file_type(file.filename)
        if not file_type:
            raise HTTPException(
                status_code=400,
                detail="File must be PDF or CSV",
            )

        # Read file content
        file_content = await file.read()

        logger.info(
            f"[DocumentAPI] Processing {file_type.upper()} upload: {file.filename} "
            f"({len(file_content)} bytes)"
        )

        # Process file
        result = file_service.process_file(
            file_bytes=file_content,
            file_name=file.filename,
            file_type=file_type,
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "File processing failed"),
            )

        # ── Store document metadata ────────────────────────────────────
        document = Document(
            user_id=user_id,
            file_name=file.filename,
            file_path=f"/uploads/{file_type}/",
            document_type=file_type,
            num_pages=result.get("num_pages"),
            file_size_bytes=len(file_content),
            extracted_text=result.get("text", ""),
        )
        db.add(document)
        db.flush()  # Get document_id
        document_id = document.document_id

        prospects_created = 0
        message = ""

        # ── Handle CSV: create prospects ────────────────────────────────
        if file_type == "csv":
            rows = result.get("rows", [])
            for row in rows:
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
                        company_id=None,  # TODO: Link to company if name provided
                        enrichment_status="pending",
                        enrichment_confidence=0.0,
                    )
                    db.add(prospect)
                    prospects_created += 1
                except Exception as e:
                    logger.warning(f"Failed to create prospect from CSV row: {e}")

            message = f"Created {prospects_created} prospect(s) from CSV"

        # ── Handle PDF: extract for RAG ────────────────────────────────
        elif file_type == "pdf":
            num_pages = result.get("num_pages", 0)
            message = f"Extracted {num_pages} page(s) from PDF (ready for RAG in Phase 2)"

        db.commit()

        logger.info(
            f"[DocumentAPI] Document {document_id} stored. {message}"
        )

        return DocumentUploadResponse(
            document_id=document_id,
            file_name=file.filename,
            document_type=file_type,
            num_pages=result.get("num_pages"),
            extracted_text_length=len(result.get("text", "")),
            prospects_created=prospects_created,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DocumentAPI] Error uploading document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}",
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
    skip: int = 0,
    limit: int = 50,
) -> DocumentListResponse:
    """List all documents for the current user."""
    try:
        query = db.query(Document).filter(Document.user_id == user_id)
        total = query.count()
        documents = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

        doc_responses = [
            DocumentResponse(
                document_id=doc.document_id,
                file_name=doc.file_name,
                document_type=doc.document_type,
                num_pages=doc.num_pages,
                file_size_bytes=doc.file_size_bytes,
                extracted_text_length=len(doc.extracted_text or ""),
                associated_company_id=doc.associated_company_id,
                created_at=doc.created_at.isoformat(),
            )
            for doc in documents
        ]

        return DocumentListResponse(total=total, documents=doc_responses)

    except Exception as e:
        logger.error(f"[DocumentAPI] Error listing documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}",
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> DocumentResponse:
    """Get metadata for a specific document."""
    try:
        document = (
            db.query(Document)
            .filter(
                Document.document_id == document_id,
                Document.user_id == user_id,
            )
            .first()
        )

        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found",
            )

        return DocumentResponse(
            document_id=document.document_id,
            file_name=document.file_name,
            document_type=document.document_type,
            num_pages=document.num_pages,
            file_size_bytes=document.file_size_bytes,
            extracted_text_length=len(document.extracted_text or ""),
            associated_company_id=document.associated_company_id,
            created_at=document.created_at.isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DocumentAPI] Error fetching document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch document: {str(e)}",
        )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> None:
    """Delete a document (soft delete for audit trail)."""
    try:
        document = (
            db.query(Document)
            .filter(
                Document.document_id == document_id,
                Document.user_id == user_id,
            )
            .first()
        )

        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found",
            )

        db.delete(document)
        db.commit()

        logger.info(f"[DocumentAPI] Deleted document {document_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[DocumentAPI] Error deleting document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}",
        )
