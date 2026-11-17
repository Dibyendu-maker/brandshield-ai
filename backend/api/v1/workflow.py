from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ai_engine.corrections.studio import CorrectionStudio
from backend.api.deps import get_current_user, get_db, require_roles
from backend.api.v1.content import _format_submission_out
from backend.database.models import (
    ContentRevision,
    ContentSubmission,
    ReviewComment,
    User,
)
from backend.schemas.submission import (
    ContentRevisionCreate,
    ContentRevisionOut,
    ContentSubmissionOut,
    ReviewCommentCreate,
    ReviewCommentOut,
    StatusChangeRequest,
)

router = APIRouter(prefix="/workflow", tags=["Human Review & Workflow"])

VALID_STATUSES = [
    "draft",
    "submitted",
    "under_review",
    "changes_requested",
    "resubmitted",
    "approved",
    "rejected",
]


@router.post("/{submission_id}/status", response_model=ContentSubmissionOut)
def update_status(
    submission_id: int,
    req: StatusChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if req.new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{req.new_status}'. Allowed: {VALID_STATUSES}",
        )

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

    # Role permissions check
    # Only reviewer or admin can approve or reject
    if req.new_status in ["approved", "rejected"]:
        if current_user.role not in ["reviewer", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only designated Brand Reviewers or Administrators can approve or reject submissions.",
            )

    old_status = submission.current_status
    submission.current_status = req.new_status

    # Record transition comment
    comment_text = (
        req.comment or f"Status changed from {old_status} to {req.new_status}."
    )
    comment = ReviewComment(
        submission_id=submission.id,
        user_id=current_user.id,
        comment=comment_text,
        status_transition=f"{old_status} -> {req.new_status}",
    )
    db.add(comment)
    db.commit()
    db.refresh(submission)

    return _format_submission_out(submission)


@router.post("/{submission_id}/assign-reviewer")
def assign_reviewer(
    submission_id: int,
    reviewer_id: int,
    current_user: User = Depends(require_roles(["admin", "reviewer"])),
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

    reviewer = (
        db.query(User)
        .filter(
            User.id == reviewer_id, User.organization_id == current_user.organization_id
        )
        .first()
    )
    if not reviewer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reviewer user not found"
        )

    submission.assigned_reviewer_id = reviewer.id
    if submission.current_status == "submitted":
        submission.current_status = "under_review"

    db.commit()
    return {"message": f"Assigned to reviewer {reviewer.full_name}"}


@router.post("/{submission_id}/comment", response_model=ReviewCommentOut)
def add_comment(
    submission_id: int,
    comment_in: ReviewCommentCreate,
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

    comment = ReviewComment(
        submission_id=submission.id,
        user_id=current_user.id,
        comment=comment_in.comment,
        status_transition=comment_in.status_transition,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return ReviewCommentOut(
        id=comment.id,
        submission_id=comment.submission_id,
        user_id=comment.user_id,
        user_name=current_user.full_name,
        comment=comment.comment,
        status_transition=comment.status_transition,
        created_at=comment.created_at,
    )


@router.post("/{submission_id}/revision", response_model=ContentRevisionOut)
def save_revision(
    submission_id: int,
    rev_in: ContentRevisionCreate,
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

    next_rev_num = len(submission.revisions) + 1
    new_rev = ContentRevision(
        submission_id=submission.id,
        author_id=current_user.id,
        revision_number=next_rev_num,
        content=rev_in.content,
        version_label=rev_in.version_label or f"Revision {next_rev_num}",
        changes_summary=rev_in.changes_summary or "Updated content.",
    )
    db.add(new_rev)

    # If changes were requested, update status to resubmitted
    if submission.current_status == "changes_requested":
        submission.current_status = "resubmitted"

    db.commit()
    db.refresh(new_rev)

    return ContentRevisionOut(
        id=new_rev.id,
        submission_id=new_rev.submission_id,
        author_id=new_rev.author_id,
        revision_number=new_rev.revision_number,
        content=new_rev.content,
        version_label=new_rev.version_label,
        changes_summary=new_rev.changes_summary,
        created_at=new_rev.created_at,
    )


@router.get("/{submission_id}/diff")
def get_revision_diff(
    submission_id: int,
    rev1: int | None = None,
    rev2: int | None = None,
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

    revisions = {r.revision_number: r.content for r in submission.revisions}

    # If no revision numbers given, compare Rev 1 (Original) with latest revision
    text1 = revisions.get(rev1, submission.original_text or "")
    text2 = revisions.get(
        rev2,
        list(revisions.values())[-1] if revisions else submission.original_text or "",
    )

    diff_chunks = CorrectionStudio.compute_diff(text1, text2)
    return {
        "submission_id": submission_id,
        "base_text": text1,
        "comparison_text": text2,
        "diff_chunks": diff_chunks,
    }
