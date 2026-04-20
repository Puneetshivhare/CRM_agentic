"""
app/models/document.py — SQLAlchemy model for dim_documents.

Stores uploaded files (PDFs, CSVs, transcripts) and their extracted text.
The extracted_text field is the source for future RAG/vector indexing.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Document(Base):
    """dim_documents — stores uploaded files linked optionally to a company."""

    __tablename__ = "dim_documents"

    # ── Primary key ────────────────────────────────────────────────────────
    document_id: int = Column(Integer, primary_key=True, autoincrement=True)

    # ── Ownership ─────────────────────────────────────────────────────────
    user_id: int = Column(Integer, nullable=False, index=True)

    # ── File metadata ─────────────────────────────────────────────────────
    file_path: str = Column(String(500), nullable=False)
    file_name: str = Column(String(255), nullable=False)
    document_type: str = Column(
        String(50),
        nullable=False,
        index=True,
        comment="pdf | csv | email_transcript | call_transcript",
    )
    num_pages: Optional[int] = Column(Integer, nullable=True)
    file_size_bytes: Optional[int] = Column(Integer, nullable=True)

    # ── Extracted content (used for RAG later) ────────────────────────────
    extracted_text: Optional[str] = Column(Text, nullable=True)

    # ── Optional company association ──────────────────────────────────────
    associated_company_id: Optional[int] = Column(
        Integer,
        ForeignKey("dim_companies.company_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Timestamps ────────────────────────────────────────────────────────
    upload_date: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ─────────────────────────────────────────────────────
    company = relationship("Company", back_populates="documents", lazy="select")

    __table_args__ = (
        Index("idx_documents_user", "user_id"),
        Index("idx_documents_company", "associated_company_id"),
        Index("idx_documents_type", "document_type"),
    )

    def __repr__(self) -> str:
        return f"<Document id={self.document_id} name={self.file_name!r}>"
