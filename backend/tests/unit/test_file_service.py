from app.services.file_service import FileService


def test_detect_file_type_case_insensitive():
    service = FileService()

    assert service.detect_file_type("report.PDF") == "pdf"
    assert service.detect_file_type("contacts.CsV") == "csv"
    assert service.detect_file_type("archive.zip") is None


def test_parse_csv_prospects_success():
    service = FileService()
    csv_bytes = (
        b"first_name,last_name,email,title\n"
        b"Sarah,Chen,sarah@example.com,VP Engineering\n"
        b"James,Wilson,james@example.com,CTO\n"
    )

    result = service.parse_csv_prospects(csv_bytes, "prospects.csv")

    assert result["success"] is True
    assert result["row_count"] == 2
    assert result["columns"] == ["first_name", "last_name", "email", "title"]


def test_parse_csv_prospects_rejects_empty_rows():
    service = FileService()
    csv_bytes = b"first_name,last_name,email\n"

    result = service.parse_csv_prospects(csv_bytes, "empty.csv")

    assert result["success"] is False
    assert result["error"] == "CSV has no data rows"


def test_parse_csv_prospects_supports_latin1_fallback():
    service = FileService()
    latin1_csv = "first_name,last_name\nJos\xe9,Garc\xeda\n".encode("latin-1")

    result = service.parse_csv_prospects(latin1_csv, "latin1.csv")

    assert result["success"] is True
    assert result["row_count"] == 1


def test_parse_csv_prospects_enforces_file_size_limit():
    service = FileService(max_file_size_mb=1)
    oversized_content = b"a" * (service.max_file_size_bytes + 1)

    result = service.parse_csv_prospects(oversized_content, "too_big.csv")

    assert result["success"] is False
    assert "exceeds 1MB limit" in result["error"]


def test_process_file_rejects_unsupported_file_type():
    service = FileService()

    result = service.process_file(b"dummy", "image.png", "png")

    assert result["success"] is False
    assert "Unsupported file type" in result["error"]


def test_chunk_text_creates_overlapping_chunks():
    service = FileService()
    text = "ABCDEFGHIJ" * 200

    chunks = service._chunk_text(text, chunk_size=120, overlap=20)

    assert len(chunks) > 1
    assert chunks[0][-20:] == chunks[1][:20]
