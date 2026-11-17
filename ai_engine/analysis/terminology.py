import re

from backend.database.models import BrandGuideline
from backend.schemas.compliance import FindingItem


class TerminologyAnalyzer:
    """Deterministic validation for prohibited phrases, preferred terminology, and brand naming."""

    @staticmethod
    def analyze(text: str, guideline: BrandGuideline | None) -> list[FindingItem]:
        findings: list[FindingItem] = []
        if not text or not guideline:
            return findings

        # 1. Prohibited phrases check
        prohibited = guideline.get_prohibited_phrases()
        for phrase in prohibited:
            if not phrase:
                continue
            # Word boundary regex with case-insensitive search
            pattern = re.compile(rf"\b{re.escape(phrase)}\b", re.IGNORECASE)
            matches = list(pattern.finditer(text))
            for match in matches:
                exact_snippet = match.group(0)
                findings.append(
                    FindingItem(
                        category="terminology",
                        severity="HIGH",
                        problematic_snippet=exact_snippet,
                        explanation=f"'{exact_snippet}' is explicitly listed in brand guidelines as a prohibited phrase due to regulatory, reputational, or unsubstantiated marketing risk.",
                        brand_guideline_ref="Brand Guidelines — Prohibited Phrases & Terms",
                        approved_source_fact="Organizational Prohibited Terminology Registry",
                        confidence=1.0,
                        recommended_correction="Remove or replace with an approved, factual descriptor.",
                        requires_human_verification=False,
                        finding_status="open",
                    )
                )

        # 2. Preferred terminology mappings
        preferred_map = guideline.get_preferred_terminology()
        for deprecated, approved in preferred_map.items():
            pattern = re.compile(rf"\b{re.escape(deprecated)}\b", re.IGNORECASE)
            for match in pattern.finditer(text):
                exact_snippet = match.group(0)
                # Avoid duplicate if already flagged as prohibited
                if any(
                    f.problematic_snippet.lower() == exact_snippet.lower()
                    and f.category == "terminology"
                    for f in findings
                ):
                    continue
                findings.append(
                    FindingItem(
                        category="terminology",
                        severity="MEDIUM",
                        problematic_snippet=exact_snippet,
                        explanation=f"Brand style requires using '{approved}' instead of the non-standard term '{exact_snippet}'.",
                        brand_guideline_ref="Brand Guidelines — Preferred Brand Vocabulary",
                        approved_source_fact=f"Approved Term: '{approved}'",
                        confidence=1.0,
                        recommended_correction=approved,
                        requires_human_verification=False,
                        finding_status="open",
                    )
                )

        # 3. Product Naming & Capitalization Validation
        brand_name = guideline.brand_name
        if brand_name:
            # Check incorrect capitalization like "novatech" instead of "NovaTech"
            pattern_brand = re.compile(rf"\b{re.escape(brand_name)}\b", re.IGNORECASE)
            for match in pattern_brand.finditer(text):
                exact_snippet = match.group(0)
                if exact_snippet != brand_name:
                    findings.append(
                        FindingItem(
                            category="terminology",
                            severity="LOW",
                            problematic_snippet=exact_snippet,
                            explanation=f"Incorrect brand name capitalization. Expected '{brand_name}', found '{exact_snippet}'.",
                            brand_guideline_ref="Brand Identity Guide — Trademark & Capitalization",
                            approved_source_fact=f"Official Brand Trademark: '{brand_name}'",
                            confidence=1.0,
                            recommended_correction=brand_name,
                            requires_human_verification=False,
                            finding_status="open",
                        )
                    )

        return findings
