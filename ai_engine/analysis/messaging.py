from backend.database.models import BrandFact, BrandGuideline
from backend.schemas.compliance import FindingItem


class MessagingAnalyzer:
    """Verifies alignment with core brand positioning, value pillars, and campaign messaging."""

    @staticmethod
    def analyze(
        text: str, guideline: BrandGuideline | None, facts: list[BrandFact]
    ) -> list[FindingItem]:
        findings: list[FindingItem] = []
        if not text:
            return findings

        # Check required positioning pillar for NovaBook Pro
        # E.g. "AI-powered productivity"
        positioning_fact = next(
            (f for f in facts if f.fact_key == "core_positioning"), None
        )
        if positioning_fact:
            req_keyword = (
                positioning_fact.fact_value.lower()
            )  # "ai-powered productivity"
            # If text discusses laptop / notebook but omits core positioning
            if any(
                term in text.lower()
                for term in ["laptop", "notebook", "computer", "device", "novabook"]
            ):
                if req_keyword not in text.lower() and "ai-powered" not in text.lower():
                    findings.append(
                        FindingItem(
                            category="messaging",
                            severity="MEDIUM",
                            problematic_snippet="Missing mandatory brand positioning pillar",
                            explanation=(
                                f"Content introduces product without referencing the mandated core positioning descriptor: "
                                f"'{positioning_fact.fact_value}'."
                            ),
                            brand_guideline_ref="Brand Strategy & Campaign Architecture 2026",
                            approved_source_fact=f"{positioning_fact.fact_value} (Source: {positioning_fact.source_reference})",
                            confidence=0.90,
                            recommended_correction=f"Include the descriptor '{positioning_fact.fact_value}' in the product introduction.",
                            requires_human_verification=False,
                            finding_status="open",
                        )
                    )

        return findings
