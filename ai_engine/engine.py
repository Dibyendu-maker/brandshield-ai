from sqlalchemy.orm import Session

from ai_engine.analysis.accessibility import AccessibilityAnalyzer
from ai_engine.analysis.claims import PromotionalClaimAnalyzer
from ai_engine.analysis.facts import FactualVerificationAnalyzer
from ai_engine.analysis.messaging import MessagingAnalyzer
from ai_engine.analysis.terminology import TerminologyAnalyzer
from ai_engine.analysis.tone import ToneAnalyzer
from ai_engine.corrections.studio import CorrectionStudio
from ai_engine.retrieval.retriever import HybridRetriever
from ai_engine.vision.analyzer import VisualBrandAnalyzer
from backend.schemas.compliance import (
    ComplianceAnalysisResponse,
    FindingItem,
)


class ComplianceEngine:
    """Master orchestrator for BrandShield AI modular compliance audit."""

    @classmethod
    def audit_content(
        cls,
        text: str | None,
        image_path: str | None,
        org_id: int,
        db: Session,
        submission_id: int | None = None,
    ) -> ComplianceAnalysisResponse:
        retriever = HybridRetriever(db, org_id)
        ground_truth = retriever.retrieve_ground_truth_context(text or "")
        guideline = ground_truth["guideline"]
        facts = ground_truth["all_facts"]

        findings: list[FindingItem] = []

        # 1. Text Analyses
        if text and text.strip():
            # A. Terminology & Prohibited Phrases
            term_findings = TerminologyAnalyzer.analyze(text, guideline)
            findings.extend(term_findings)

            # B. Factual Verification (Battery, Warranty, Specs)
            fact_findings = FactualVerificationAnalyzer.analyze(text, facts)
            findings.extend(fact_findings)

            # C. Promotional Claims & Superlatives
            approved_claims = (
                json_loads_safe(guideline.approved_claims)
                if guideline and guideline.approved_claims
                else []
            )
            claim_findings = PromotionalClaimAnalyzer.analyze(text, approved_claims)
            findings.extend(claim_findings)

            # D. Tone & Voice Consistency
            tone_findings = ToneAnalyzer.analyze(text, guideline)
            findings.extend(tone_findings)

            # E. Messaging Alignment
            msg_findings = MessagingAnalyzer.analyze(text, guideline, facts)
            findings.extend(msg_findings)

            # F. Readability & Accessibility
            access_findings = AccessibilityAnalyzer.analyze(
                text, has_image_without_alt=bool(image_path and not text)
            )
            findings.extend(access_findings)

        # 2. Multimodal Visual Inspection
        if image_path:
            approved_palette = guideline.get_color_palette() if guideline else []
            brand_name = guideline.brand_name if guideline else "NovaTech"
            vision_result = VisualBrandAnalyzer.analyze_image(
                image_path, approved_palette, brand_name
            )
            findings.extend(vision_result["findings"])

        # Deduplicate findings if identical snippet and category
        unique_findings = []
        seen = set()
        for f in findings:
            key = (f.category, f.problematic_snippet.lower(), f.severity)
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)
        findings = unique_findings

        # 3. Severity Aggregation & Scoring
        critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
        high_count = sum(1 for f in findings if f.severity == "HIGH")
        medium_count = sum(1 for f in findings if f.severity == "MEDIUM")
        low_count = sum(1 for f in findings if f.severity == "LOW")
        total_violations = len(findings)

        # Explainable, weighted scoring formula
        score = 100.0 - (
            critical_count * 25.0
            + high_count * 15.0
            + medium_count * 5.0
            + low_count * 2.0
        )
        overall_score = max(0.0, min(100.0, round(score, 1)))

        # Category breakdown
        category_breakdown: dict[str, int] = {}
        for f in findings:
            category_breakdown[f.category] = category_breakdown.get(f.category, 0) + 1

        # 4. Generate Intent-Preserving Correction
        suggested_revision = ""
        if text and text.strip():
            suggested_revision = CorrectionStudio.generate_correction(
                text, findings, guideline, facts
            )

        return ComplianceAnalysisResponse(
            submission_id=submission_id,
            overall_score=overall_score,
            total_violations=total_violations,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            category_breakdown=category_breakdown,
            findings=findings,
            suggested_revision=suggested_revision,
        )


def json_loads_safe(val):
    import json

    try:
        return json.loads(val)
    except Exception:
        return []
