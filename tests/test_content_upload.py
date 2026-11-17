import io
from pathlib import Path

from backend.core.config import settings


def _get_auth_headers(client):
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "creator@novatech.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_valid_document_upload_txt(client):
    """Test valid .txt document upload and text extraction."""
    headers = _get_auth_headers(client)
    file_content = b"This is a verified brand guideline document for testing."
    files = {"file": ("guidelines.txt", io.BytesIO(file_content), "text/plain")}
    data = {"title": "Q4 Brand Brief", "content_type": "document"}

    res = client.post(
        "/api/v1/content/submit", data=data, files=files, headers=headers
    )
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["title"] == "Q4 Brand Brief"
    assert "verified brand guideline document" in res_data["original_text"]
    assert res_data["file_path"] is not None
    assert Path(res_data["file_path"]).exists()

    # Clean up created file
    Path(res_data["file_path"]).unlink(missing_ok=True)


def test_valid_document_upload_md(client):
    """Test valid .md document upload."""
    headers = _get_auth_headers(client)
    file_content = b"# Product Overview\nNovaBook Pro specifications."
    files = {"file": ("overview.md", io.BytesIO(file_content), "text/markdown")}
    data = {"title": "Markdown Overview", "content_type": "document"}

    res = client.post(
        "/api/v1/content/submit", data=data, files=files, headers=headers
    )
    assert res.status_code == 200
    res_data = res.json()
    assert "NovaBook Pro specifications" in res_data["original_text"]

    Path(res_data["file_path"]).unlink(missing_ok=True)


def test_valid_image_upload_png(client):
    """Test valid .png image upload."""
    headers = _get_auth_headers(client)
    # Minimal 1x1 transparent PNG bytes
    tiny_png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {"file": ("brand_logo.png", io.BytesIO(tiny_png), "image/png")}
    data = {"title": "NovaTech Logo", "content_type": "image"}

    res = client.post(
        "/api/v1/content/submit", data=data, files=files, headers=headers
    )
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["image_path"] is not None
    assert Path(res_data["image_path"]).exists()

    Path(res_data["image_path"]).unlink(missing_ok=True)


def test_unsupported_file_type_rejected(client):
    """Test rejection of unsupported file extensions (e.g. .exe, .sh, .bat)."""
    headers = _get_auth_headers(client)
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00"
    files = {
        "file": (
            "payload.exe",
            io.BytesIO(fake_exe),
            "application/x-msdownload",
        )
    }
    data = {"title": "Executable File", "content_type": "document"}

    res = client.post(
        "/api/v1/content/submit", data=data, files=files, headers=headers
    )
    assert res.status_code == 400
    assert "Unsupported file format '.exe'" in res.json()["detail"]


def test_empty_file_upload_rejected(client):
    """Test rejection of zero-byte file uploads."""
    headers = _get_auth_headers(client)
    files = {"file": ("empty.txt", io.BytesIO(b""), "text/plain")}
    data = {"title": "Empty File Submission", "content_type": "document"}

    res = client.post(
        "/api/v1/content/submit", data=data, files=files, headers=headers
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_empty_submission_rejected(client):
    """Test rejection when neither text nor file/image is supplied."""
    headers = _get_auth_headers(client)
    data = {"title": "No Content Submission", "original_text": "   "}

    res = client.post("/api/v1/content/submit", data=data, headers=headers)
    assert res.status_code == 400
    assert "must include non-empty text" in res.json()["detail"]


def test_path_traversal_filename_sanitized(client):
    """Test that path traversal attempts in filename are sanitized and confined to UPLOAD_DIR."""
    headers = _get_auth_headers(client)
    traversal_name = "../../../traversal_test.txt"
    files = {"file": (traversal_name, io.BytesIO(b"Safe content"), "text/plain")}
    data = {"title": "Traversal Attempt", "content_type": "document"}

    res = client.post(
        "/api/v1/content/submit", data=data, files=files, headers=headers
    )
    assert res.status_code == 200
    saved_path = Path(res.json()["file_path"])
    # Ensure saved path is strictly inside UPLOAD_DIR
    upload_dir = Path(settings.UPLOAD_DIR).resolve()
    assert upload_dir in saved_path.resolve().parents
    assert ".." not in saved_path.name

    saved_path.unlink(missing_ok=True)


def test_oversized_file_rejected_if_exceeds_configured_limit(
    client, monkeypatch
):
    """Test that file exceeding settings.MAX_UPLOAD_SIZE_MB is rejected with HTTP 413."""
    headers = _get_auth_headers(client)
    # Temporarily set max size to 1MB for testing
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)
    oversized_data = b"X" * (1024 * 1024 + 100)  # ~1.0001 MB
    files = {
        "file": ("large_doc.txt", io.BytesIO(oversized_data), "text/plain")
    }
    data = {"title": "Oversized File", "content_type": "document"}

    res = client.post(
        "/api/v1/content/submit", data=data, files=files, headers=headers
    )
    assert res.status_code == 413
    assert "exceeds the configured maximum limit" in res.json()["detail"]
