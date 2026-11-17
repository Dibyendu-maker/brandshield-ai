import json
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database.session import Base


def utc_now():
    return datetime.now(UTC)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    users = relationship(
        "User", back_populates="organization", cascade="all, delete-orphan"
    )
    guidelines = relationship(
        "BrandGuideline", back_populates="organization", cascade="all, delete-orphan"
    )
    facts = relationship(
        "BrandFact", back_populates="organization", cascade="all, delete-orphan"
    )
    documents = relationship(
        "BrandDocument", back_populates="organization", cascade="all, delete-orphan"
    )
    submissions = relationship(
        "ContentSubmission", back_populates="organization", cascade="all, delete-orphan"
    )


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(
        String(50), default="creator", nullable=False
    )  # admin, creator, reviewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="users")
    submissions = relationship(
        "ContentSubmission",
        foreign_keys="ContentSubmission.creator_id",
        back_populates="creator",
    )
    assigned_submissions = relationship(
        "ContentSubmission",
        foreign_keys="ContentSubmission.assigned_reviewer_id",
        back_populates="reviewer",
    )


class BrandGuideline(Base):
    __tablename__ = "brand_guidelines"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(
        Integer, ForeignKey("organizations.id"), unique=True, nullable=False
    )
    brand_name = Column(String(255), nullable=False)
    brand_description = Column(Text, nullable=True)
    mission_values = Column(Text, nullable=True)
    preferred_tone = Column(
        Text, nullable=True
    )  # e.g., "Professional, approachable, trustworthy"
    prohibited_phrases = Column(Text, default="[]")  # JSON string array
    preferred_terminology = Column(
        Text, default="{}"
    )  # JSON mapping { "forbidden": "preferred" }
    logo_path = Column(String(512), nullable=True)
    color_palette = Column(
        Text, default="[]"
    )  # JSON array of HEX codes e.g. ["#0B132B", "#1C2541", "#5BC0BE"]
    typography_rules = Column(
        Text, default="{}"
    )  # JSON { "primary_font": "Inter", "heading_font": "Plus Jakarta Sans" }
    approved_claims = Column(
        Text, default="[]"
    )  # JSON array of pre-approved marketing claims
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="guidelines")

    def get_prohibited_phrases(self) -> list[str]:
        try:
            return (
                json.loads(self.prohibited_phrases) if self.prohibited_phrases else []
            )
        except Exception:
            return []

    def get_preferred_terminology(self) -> dict[str, str]:
        try:
            return (
                json.loads(self.preferred_terminology)
                if self.preferred_terminology
                else {}
            )
        except Exception:
            return {}

    def get_color_palette(self) -> list[str]:
        try:
            return json.loads(self.color_palette) if self.color_palette else []
        except Exception:
            return []


class BrandFact(Base):
    __tablename__ = "brand_facts"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    product_name = Column(
        String(255), index=True, nullable=False
    )  # e.g. "NovaBook Pro"
    category = Column(
        String(100), nullable=False
    )  # "specification", "pricing", "warranty", "claim"
    fact_key = Column(
        String(255), nullable=False
    )  # e.g. "battery_life", "warranty_period", "price"
    fact_value = Column(
        String(512), nullable=False
    )  # e.g. "12 hours", "1 year", "$1299"
    source_reference = Column(
        String(512), nullable=True
    )  # e.g. "Product Spec Sheet v2.1"
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="facts")


class BrandDocument(Base):
    __tablename__ = "brand_documents"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # "pdf", "docx", "txt", "md"
    file_path = Column(String(512), nullable=False)
    document_title = Column(String(255), nullable=True)
    chunk_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=utc_now)

    organization = relationship("Organization", back_populates="documents")


class ContentSubmission(Base):
    __tablename__ = "content_submissions"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False)
    content_type = Column(
        String(50), default="text"
    )  # "text", "document", "image", "multimodal"
    original_text = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=True)
    image_path = Column(String(512), nullable=True)
    current_status = Column(
        String(50), default="draft"
    )  # draft, submitted, under_review, changes_requested, resubmitted, approved, rejected
    compliance_score = Column(Float, default=100.0)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    organization = relationship("Organization", back_populates="submissions")
    creator = relationship(
        "User", foreign_keys=[creator_id], back_populates="submissions"
    )
    reviewer = relationship(
        "User",
        foreign_keys=[assigned_reviewer_id],
        back_populates="assigned_submissions",
    )
    findings = relationship(
        "ComplianceFinding", back_populates="submission", cascade="all, delete-orphan"
    )
    revisions = relationship(
        "ContentRevision",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="ContentRevision.revision_number.asc()",
    )
    comments = relationship(
        "ReviewComment",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="ReviewComment.created_at.asc()",
    )


class ComplianceFinding(Base):
    __tablename__ = "compliance_findings"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer, ForeignKey("content_submissions.id"), nullable=False
    )
    category = Column(
        String(50), nullable=False
    )  # "tone", "terminology", "factual", "claim", "messaging", "visual", "accessibility"
    severity = Column(String(20), nullable=False)  # "CRITICAL", "HIGH", "MEDIUM", "LOW"
    problematic_snippet = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    brand_guideline_ref = Column(String(512), nullable=True)
    approved_source_fact = Column(String(512), nullable=True)
    confidence = Column(Float, default=0.95)
    recommended_correction = Column(Text, nullable=False)
    requires_human_verification = Column(Boolean, default=False)
    finding_status = Column(
        String(20), default="open"
    )  # "open", "applied", "dismissed"
    created_at = Column(DateTime, default=utc_now)

    submission = relationship("ContentSubmission", back_populates="findings")


class ContentRevision(Base):
    __tablename__ = "content_revisions"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer, ForeignKey("content_submissions.id"), nullable=False
    )
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    revision_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    version_label = Column(
        String(50), default="User Edit"
    )  # "Original", "AI Suggested", "User Edit", "Final Approved"
    changes_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    submission = relationship("ContentSubmission", back_populates="revisions")
    author = relationship("User")


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(
        Integer, ForeignKey("content_submissions.id"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=False)
    status_transition = Column(
        String(50), nullable=True
    )  # e.g. "submitted -> under_review"
    created_at = Column(DateTime, default=utc_now)

    submission = relationship("ContentSubmission", back_populates="comments")
    user = relationship("User")
