from typing import Literal

from pydantic import BaseModel, Field

SeverityLevel = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
FindingCategory = Literal[
    "tone", "terminology", "factual", "claim", "messaging", "visual", "accessibility"
]


class FindingItem(BaseModel):
    id: int | None = None
    category: FindingCategory
    severity: SeverityLevel
    problematic_snippet: str
    explanation: str
    brand_guideline_ref: str | None = None
    approved_source_fact: str | None = None
    confidence: float = Field(default=0.95, ge=0.0, le=1.0)
    recommended_correction: str
    requires_human_verification: bool = False
    finding_status: str = "open"


class ComplianceAnalysisRequest(BaseModel):
    title: str = "Submitted Draft"
    text: str | None = None
    image_path: str | None = None
    submission_id: int | None = None


class ComplianceAnalysisResponse(BaseModel):
    submission_id: int | None = None
    overall_score: float
    total_violations: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    category_breakdown: dict[str, int]
    findings: list[FindingItem]
    suggested_revision: str
    scoring_methodology: str = (
        "Compliance Score = max(0, 100 - (Critical x 25 + High x 15 + Medium x 5 + Low x 2)). "
        "Deductions reflect enterprise brand risk, factual exposure, and regulatory advertising standards."
    )
