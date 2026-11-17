from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db
from backend.database.models import (
    ComplianceFinding,
    ContentSubmission,
    User,
)

router = APIRouter(prefix="/analytics", tags=["Governance Analytics"])


@router.get("/dashboard")
def get_governance_analytics(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    org_id = current_user.organization_id

    # 1. Total Submissions & Status Counts
    submissions = (
        db.query(ContentSubmission)
        .filter(ContentSubmission.organization_id == org_id)
        .all()
    )
    total_submissions = len(submissions)

    status_counts = Counter(s.current_status for s in submissions)
    approved_count = status_counts.get("approved", 0)
    rejected_count = status_counts.get("rejected", 0)
    pending_count = total_submissions - (approved_count + rejected_count)

    # Approval vs Rejection Rate
    decided_count = approved_count + rejected_count
    approval_rate = (
        round((approved_count / decided_count * 100), 1) if decided_count > 0 else 0.0
    )
    rejection_rate = (
        round((rejected_count / decided_count * 100), 1) if decided_count > 0 else 0.0
    )

    # 2. Average Compliance Score
    avg_score = 0.0
    if total_submissions > 0:
        scores = [
            s.compliance_score for s in submissions if s.compliance_score is not None
        ]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 100.0

    # 3. Violations by Category & Priority
    findings = (
        db.query(ComplianceFinding)
        .join(ContentSubmission)
        .filter(ContentSubmission.organization_id == org_id)
        .all()
    )

    category_counts = Counter(f.category for f in findings)
    severity_counts = Counter(f.severity for f in findings)

    # 4. Repeated Terminology Mistakes
    terminology_findings = [
        f.problematic_snippet.lower() for f in findings if f.category == "terminology"
    ]
    repeated_terminology = [
        {"term": term, "count": count}
        for term, count in Counter(terminology_findings).most_common(5)
    ]

    # 5. Frequently Incorrect Claims & Facts
    fact_claim_findings = [
        f"{f.problematic_snippet} ({f.category})"
        for f in findings
        if f.category in ["factual", "claim"]
    ]
    frequent_claims = [
        {"claim": item, "count": count}
        for item, count in Counter(fact_claim_findings).most_common(5)
    ]

    # 6. Common Tone Violations
    tone_findings = [f.problematic_snippet for f in findings if f.category == "tone"]
    common_tone_issues = [
        {"issue": item, "count": count}
        for item, count in Counter(tone_findings).most_common(5)
    ]

    # 7. Submissions requiring multiple revisions
    multi_revision_count = 0
    for s in submissions:
        if len(s.revisions) > 2:
            multi_revision_count += 1

    # 8. Unclear Guideline Refinement Recommendations
    # Synthesizes policy recommendations when recurring violations exceed threshold
    policy_recommendations = []
    if category_counts.get("factual", 0) > 0:
        policy_recommendations.append(
            {
                "category": "Product Specifications",
                "observation": f"Detected {category_counts.get('factual')} specification conflicts (e.g. battery life, warranty).",
                "action": "Publish a 1-page Quick Reference Card for marketing creators detailing official hardware specs.",
            }
        )
    if category_counts.get("claim", 0) > 0:
        policy_recommendations.append(
            {
                "category": "Comparative Advertising",
                "observation": f"Detected {category_counts.get('claim')} superlative/guarantee claims requiring verification.",
                "action": "Clarify substantiation policy for #1 rankings in Brand Guidelines Section 4.",
            }
        )
    if category_counts.get("terminology", 0) > 0:
        policy_recommendations.append(
            {
                "category": "Approved Vocabulary",
                "observation": f"Identified {category_counts.get('terminology')} non-approved terminology instances.",
                "action": "Distribute automated terminology linter rules to agency partners.",
            }
        )

    return {
        "total_submissions": total_submissions,
        "average_compliance_score": avg_score,
        "approval_rate": approval_rate,
        "rejection_rate": rejection_rate,
        "status_distribution": dict(status_counts),
        "violations_by_category": dict(category_counts),
        "violations_by_severity": dict(severity_counts),
        "top_repeated_terminology": repeated_terminology,
        "frequent_incorrect_claims": frequent_claims,
        "common_tone_violations": common_tone_issues,
        "multi_revision_submissions": multi_revision_count,
        "policy_recommendations": policy_recommendations,
    }
