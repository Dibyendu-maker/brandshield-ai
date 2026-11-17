from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.schemas.compliance import FindingItem


class ContentSubmissionCreate(BaseModel):
    title: str
    content_type: str = "text"  # text, document, image, multimodal
    original_text: str | None = None


class ContentSubmissionUpdate(BaseModel):
    title: str | None = None
    original_text: str | None = None
    assigned_reviewer_id: int | None = None


class ContentRevisionCreate(BaseModel):
    content: str
    version_label: str = "User Edit"
    changes_summary: str | None = None


class ContentRevisionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_id: int
    author_id: int
    revision_number: int
    content: str
    version_label: str
    changes_summary: str | None = None
    created_at: datetime


class ReviewCommentCreate(BaseModel):
    comment: str
    status_transition: str | None = None


class ReviewCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    submission_id: int
    user_id: int
    user_name: str | None = None
    comment: str
    status_transition: str | None = None
    created_at: datetime


class StatusChangeRequest(BaseModel):
    new_status: str  # draft, submitted, under_review, changes_requested, resubmitted, approved, rejected
    comment: str | None = None


class ContentSubmissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    creator_id: int
    creator_name: str | None = None
    assigned_reviewer_id: int | None = None
    reviewer_name: str | None = None
    title: str
    content_type: str
    original_text: str | None = None
    file_path: str | None = None
    image_path: str | None = None
    current_status: str
    compliance_score: float
    summary: str | None = None
    created_at: datetime
    updated_at: datetime
    findings: list[FindingItem] = []
    revisions: list[ContentRevisionOut] = []
    comments: list[ReviewCommentOut] = []
