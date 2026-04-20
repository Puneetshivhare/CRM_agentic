"""
app/services/file_service.py — File processing service for PDFs and CSVs.

Responsibilities:
  - Extract text from PDF files (pypdf)
  - Parse CSV prospect lists
  - Validate and sanitize file contents
  - Chunk large documents for RAG processing
  - Return structured file metadata
"""

import logging
import csv
from io import StringIO, BytesIO
from typing import Optional, Dict, List, Any, Tuple

logger = logging.getLogger("agentic_crm")


class FileService:
    """Service for processing uploaded files (PDFs, CSVs)."""

    def __init__(self, max_file_size_mb: int = 50):
        """
        Initialize file service.

        Args:
            max_file_size_mb: Maximum allowed file size in MB
        """
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024

    def extract_pdf_text(self, file_bytes: bytes, file_name: str) -> Dict[str, Any]:
        """
        Extract text from PDF file.

        Args:
            file_bytes: Raw PDF content
            file_name: Original file name

        Returns:
            Dict with:
              - success: bool
              - text: Extracted text (first 50k chars)
              - num_pages: Number of pages
              - chunks: List of text chunks (for RAG)
              - error: Error message if failed
        """
        try:
            # Validate file size
            if len(file_bytes) > self.max_file_size_bytes:
                return {
                    "success": False,
                    "error": f"File exceeds {self.max_file_size_mb}MB limit",
                }

            # Import pypdf (lazy import to avoid hard dependency)
            try:
                from pypdf import PdfReader
            except ImportError:
                logger.error("pypdf not installed — install with: pip install pypdf")
                return {
                    "success": False,
                    "error": "PDF processing not available (pypdf not installed)",
                }

            # Parse PDF
            pdf_file = BytesIO(file_bytes)
            reader = PdfReader(pdf_file)
            num_pages = len(reader.pages)

            # Extract text from all pages
            full_text = ""
            for page_num, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if text:
                        full_text += f"\n--- Page {page_num + 1} ---\n{text}"
                except Exception as e:
                    logger.warning(
                        f"Failed to extract text from page {page_num + 1} of {file_name}: {e}"
                    )

            if not full_text.strip():
                return {
                    "success": False,
                    "error": "No text extracted from PDF (may be scanned/image-based)",
                }

            # Chunk the text (1000 char chunks with 100 char overlap)
            chunks = self._chunk_text(full_text, chunk_size=1000, overlap=100)

            logger.info(
                f"Extracted {num_pages} pages from {file_name}, "
                f"{len(full_text)} chars, {len(chunks)} chunks"
            )

            return {
                "success": True,
                "text": full_text[:50000],  # First 50k chars for metadata
                "num_pages": num_pages,
                "chunks": chunks,
                "total_chars": len(full_text),
            }

        except Exception as e:
            logger.error(f"Error extracting PDF text from {file_name}: {e}")
            return {
                "success": False,
                "error": f"PDF processing failed: {str(e)}",
            }

    def parse_csv_prospects(self, file_bytes: bytes, file_name: str) -> Dict[str, Any]:
        """
        Parse CSV file containing prospect data.

        Expected columns: first_name, last_name, email, title, company_name, etc.
        (Flexible — will extract whatever is present)

        Args:
            file_bytes: Raw CSV content
            file_name: Original file name

        Returns:
            Dict with:
              - success: bool
              - rows: List of dicts (CSV rows)
              - columns: Found column names
              - row_count: Number of rows
              - error: Error message if failed
        """
        try:
            # Validate file size
            if len(file_bytes) > self.max_file_size_bytes:
                return {
                    "success": False,
                    "error": f"File exceeds {self.max_file_size_mb}MB limit",
                }

            # Decode CSV
            try:
                csv_text = file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    csv_text = file_bytes.decode("latin-1")
                except:
                    return {
                        "success": False,
                        "error": "CSV file encoding not recognized (expected UTF-8 or Latin-1)",
                    }

            # Parse CSV
            csv_file = StringIO(csv_text)
            reader = csv.DictReader(csv_file)

            if not reader.fieldnames:
                return {
                    "success": False,
                    "error": "CSV has no headers",
                }

            rows = list(reader)
            if not rows:
                return {
                    "success": False,
                    "error": "CSV has no data rows",
                }

            logger.info(
                f"Parsed {len(rows)} rows from {file_name}, "
                f"columns: {', '.join(reader.fieldnames)}"
            )

            return {
                "success": True,
                "rows": rows,
                "columns": list(reader.fieldnames),
                "row_count": len(rows),
            }

        except Exception as e:
            logger.error(f"Error parsing CSV from {file_name}: {e}")
            return {
                "success": False,
                "error": f"CSV parsing failed: {str(e)}",
            }

    def process_file(
        self, file_bytes: bytes, file_name: str, file_type: str
    ) -> Dict[str, Any]:
        """
        Process file (PDF or CSV) and return extracted content.

        Args:
            file_bytes: Raw file content
            file_name: Original file name
            file_type: "pdf" or "csv"

        Returns:
            Dict with processed file data
        """
        if file_type.lower() == "pdf":
            return self.extract_pdf_text(file_bytes, file_name)
        elif file_type.lower() == "csv":
            return self.parse_csv_prospects(file_bytes, file_name)
        else:
            return {
                "success": False,
                "error": f"Unsupported file type: {file_type} (expected pdf or csv)",
            }

    def _chunk_text(
        self, text: str, chunk_size: int = 1000, overlap: int = 100
    ) -> List[str]:
        """
        Split text into overlapping chunks for RAG.

        Args:
            text: Full text to chunk
            chunk_size: Size of each chunk (characters)
            overlap: Overlap between chunks (characters)

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end])

            # Move start position (with overlap)
            start = end - overlap

            # Avoid infinite loop on last chunk
            if end == len(text):
                break

        return chunks

    def detect_file_type(self, file_name: str) -> Optional[str]:
        """
        Detect file type from filename extension.

        Args:
            file_name: Original file name

        Returns:
            "pdf", "csv", or None if unknown
        """
        name_lower = file_name.lower()
        if name_lower.endswith(".pdf"):
            return "pdf"
        elif name_lower.endswith(".csv"):
            return "csv"
        else:
            return None


# Module-level instance
file_service = FileService()
