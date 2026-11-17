from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ai_engine.engine import ComplianceEngine
from backend.api.deps import get_current_user, get_db
from backend.database.models import ComplianceFinding, ContentSubmission, User
from backend.schemas.compliance import (
    ComplianceAnalysisRequest,
    ComplianceAnalysisResponse,
)

router = APIRouter(prefix="/compliance", tags=["AI Compliance Engine"])


@router.post("/audit/{submission_id}", response_model=ComplianceAnalysisResponse)
def audit_submission(
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

    # Get the latest revision content or original text
    latest_revision = submission.revisions[-1] if submission.revisions else None
    content_to_check = (
        latest_revision.content if latest_revision else submission.original_text
    )

    # Run compliance engine
    result = ComplianceEngine.audit_content(
        text=content_to_check,
        image_path=submission.image_path,
        org_id=current_user.organization_id,
        db=db,
        submission_id=submission.id,
    )

    # Persist findings to database (clear previous open findings for this submission)
    db.query(ComplianceFinding).filter(
        ComplianceFinding.submission_id == submission.id
    ).delete()

    for item in result.findings:
        finding = ComplianceFinding(
            submission_id=submission.id,
            category=item.category,
            severity=item.severity,
            problematic_snippet=item.problematic_snippet,
            explanation=item.explanation,
            brand_guideline_ref=item.brand_guideline_ref,
            approved_source_fact=item.approved_source_fact,
            confidence=item.confidence,
            recommended_correction=item.recommended_correction,
            requires_human_verification=item.requires_human_verification,
            finding_status="open",
        )
        db.add(finding)

    # Update submission score
    submission.compliance_score = result.overall_score
    submission.summary = (
        f"Compliance Audit: {result.total_violations} issue(s) detected. "
        f"Critical: {result.critical_count}, High: {result.high_count}, "
        f"Medium: {result.medium_count}, Low: {result.low_count}."
    )
    db.commit()

    return result


@router.post("/check-adhoc", response_model=ComplianceAnalysisResponse)
def audit_adhoc(
    req: ComplianceAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ad-hoc compliance check for quick live validation before formal submission."""
    return ComplianceEngine.audit_content(
        text=req.text,
        image_path=req.image_path,
        org_id=current_user.organization_id,
        db=db,
    )


@router.put("/finding/{finding_id}/status")
def update_finding_status(
    finding_id: int,
    new_status: str,  # open, applied, dismissed
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    finding = (
        db.query(ComplianceFinding)
        .join(ContentSubmission)
        .filter(
            ComplianceFinding.id == finding_id,
            ContentSubmission.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not finding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found"
        )

    finding.finding_status = new_status
    db.commit()
    return {"message": f"Finding status updated to {new_status}"}
