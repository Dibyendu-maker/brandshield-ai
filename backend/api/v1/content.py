import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ai_engine.ingestion.extractor import DocumentExtractor
from backend.api.deps import get_current_user, get_db
from backend.core.config import settings
from backend.database.models import (
    ContentRevision,
    ContentSubmission,
    User,
)
from backend.schemas.compliance import FindingItem
from backend.schemas.submission import (
    ContentRevisionOut,
    ContentSubmissionOut,
    ReviewCommentOut,
)

router = APIRouter(prefix="/content", tags=["Content Ingestion"])

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".markdown"}
ALL_SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_DOCUMENT_EXTENSIONS


@router.post("/submit", response_model=ContentSubmissionOut)
async def submit_content(
    title: str = Form(...),
    content_type: str = Form("text"),  # text, document, image, multimodal
    original_text: str | None = Form(None),
    file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    saved_file_path = None
    saved_image_path = None
    extracted_text = (original_text or "").strip()

    if file and file.filename:
        # 1. Sanitize filename and validate extension before disk write
        raw_name = Path(file.filename).name
        ext = Path(raw_name).suffix.lower()

        if ext not in ALL_SUPPORTED_EXTENSIONS:
            supported_list = ", ".join(
                sorted([e.lstrip(".").upper() for e in ALL_SUPPORTED_EXTENSIONS])
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format '{ext}'. Supported formats: {supported_list}",
            )

        content_bytes = await file.read()

        # 2. Check for empty file upload
        if len(content_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes).",
            )

        # 3. Enforce existing configured upload limit (settings.MAX_UPLOAD_SIZE_MB)
        if (
            getattr(settings, "MAX_UPLOAD_SIZE_MB", None)
            and settings.MAX_UPLOAD_SIZE_MB > 0
        ):
            max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
            if len(content_bytes) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds the configured maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                )

        # 4. Secure sanitized unique filename
        safe_stem = re.sub(r"[^\w\.-]", "_", Path(raw_name).stem)
        unique_name = f"content_{uuid.uuid4().hex}_{safe_stem}{ext}"
        save_path = Path(settings.UPLOAD_DIR) / unique_name

        try:
            with open(save_path, "wb") as f:
                f.write(content_bytes)

            if ext in SUPPORTED_IMAGE_EXTENSIONS:
                saved_image_path = str(save_path)
                content_type = "multimodal" if extracted_text else "image"
            elif ext in SUPPORTED_DOCUMENT_EXTENSIONS:
                saved_file_path = str(save_path)
                content_type = "multimodal" if saved_image_path else "document"
                try:
                    doc_info = DocumentExtractor.extract_from_file(str(save_path))
                    if not extracted_text:
                        extracted_text = doc_info.get("text", "").strip()
                except Exception as e:
                    if save_path.exists():
                        save_path.unlink()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Error extracting content from uploaded document: {e!s}",
                    )
        except HTTPException:
            raise
        except Exception as e:
            if save_path.exists():
                save_path.unlink()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process uploaded file: {e!s}",
            )

    if not extracted_text and not saved_image_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Content submission must include non-empty text, a document, or an image.",
        )

    submission = ContentSubmission(
        organization_id=current_user.organization_id,
        creator_id=current_user.id,
        title=title,
        content_type=content_type,
        original_text=extracted_text,
        file_path=saved_file_path,
        image_path=saved_image_path,
        current_status="draft",
        compliance_score=100.0,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    # Automatically create Revision 1 (Original)
    initial_revision = ContentRevision(
        submission_id=submission.id,
        author_id=current_user.id,
        revision_number=1,
        content=extracted_text,
        version_label="Original",
        changes_summary="Initial content ingestion.",
    )
    db.add(initial_revision)
    db.commit()

    return _format_submission_out(submission)


@router.get("/{submission_id}", response_model=ContentSubmissionOut)
def get_submission(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    submission = (
        db.query(ContentSubmission)
        .filter(
            ContentSubmission.id == submission_id,
            ContentSubmission.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
        )
    return _format_submission_out(submission)


@router.get("/", response_model=list[ContentSubmissionOut])
def list_submissions(
    status_filter: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ContentSubmission).filter(
        ContentSubmission.organization_id == current_user.organization_id
    )
    if status_filter:
        query = query.filter(ContentSubmission.current_status == status_filter)
    # If creator role, optionally see their own or all org submissions
    submissions = query.order_by(ContentSubmission.created_at.desc()).all()
    return [_format_submission_out(s) for s in submissions]


def _format_submission_out(s: ContentSubmission) -> ContentSubmissionOut:
    findings = [
        FindingItem(
            id=f.id,
            category=f.category,
            severity=f.severity,
            problematic_snippet=f.problematic_snippet,
            explanation=f.explanation,
            brand_guideline_ref=f.brand_guideline_ref,
            approved_source_fact=f.approved_source_fact,
            confidence=f.confidence,
            recommended_correction=f.recommended_correction,
            requires_human_verification=f.requires_human_verification,
            finding_status=f.finding_status,
        )
        for f in s.findings
    ]

    revisions = [
        ContentRevisionOut(
            id=r.id,
            submission_id=r.submission_id,
            author_id=r.author_id,
            revision_number=r.revision_number,
            content=r.content,
            version_label=r.version_label,
            changes_summary=r.changes_summary,
            created_at=r.created_at,
        )
        for r in s.revisions
    ]

    comments = [
        ReviewCommentOut(
            id=c.id,
            submission_id=c.submission_id,
            user_id=c.user_id,
            user_name=c.user.full_name if c.user else "Reviewer",
            comment=c.comment,
            status_transition=c.status_transition,
            created_at=c.created_at,
        )
        for c in s.comments
    ]

    return ContentSubmissionOut(
        id=s.id,
        organization_id=s.organization_id,
        creator_id=s.creator_id,
        creator_name=s.creator.full_name if s.creator else "Creator",
        assigned_reviewer_id=s.assigned_reviewer_id,
        reviewer_name=s.reviewer.full_name if s.reviewer else None,
        title=s.title,
        content_type=s.content_type,
        original_text=s.original_text,
        file_path=s.file_path,
        image_path=s.image_path,
        current_status=s.current_status,
        compliance_score=s.compliance_score,
        summary=s.summary,
        created_at=s.created_at,
        updated_at=s.updated_at,
        findings=findings,
        revisions=revisions,
        comments=comments,
    )
