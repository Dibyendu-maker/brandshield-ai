import re

from backend.schemas.compliance import FindingItem


class PromotionalClaimAnalyzer:
    """Detects, classifies, and audits promotional claims, superlatives, and absolute promises."""

    SUPERIORITY_PATTERNS = [
        (
            r"\b(?:world'?s\s+(?:number\s+(?:one|1)|#1)|number\s+one\s+in\s+the\s+world)\b",
            "world's number one",
            "Unsupported superiority claim",
        ),
        (
            r"\b(?:best\s+(?:laptop|product|computer|software|tool)\s+in\s+the\s+world)\b",
            "best in the world",
            "Unsubstantiated global superlative",
        ),
        (
            r"\b(?:number\s+(?:one|1)\s+in\s+the\s+industry)\b",
            "number one in the industry",
            "Unverified industry ranking claim",
        ),
        (
            r"\b(?:unbeatable\s+performance|unmatched\s+in\s+the\s+market)\b",
            "unbeatable performance",
            "Unsubstantiated competitive claim",
        ),
    ]

    GUARANTEE_PATTERNS = [
        (
            r"\b(?:guaranteed\s+success(?:\s+for\s+every\s+user)?)\b",
            "guaranteed success",
            "Absolute outcome guarantee",
        ),
        (
            r"\b(?:100%\s+guaranteed(?:\s+results)?)\b",
            "100% guaranteed",
            "Absolute percentage guarantee",
        ),
        (
            r"\b(?:zero\s+risk|zero\s+flaws|impossible\s+to\s+fail)\b",
            "zero risk",
            "Absolute risk disclaimer violation",
        ),
    ]

    SCIENTIFIC_PATTERNS = [
        (
            r"\b(?:scientifically\s+proven|clinically\s+tested\s+and\s+proven)\b",
            "scientifically proven",
            "Empirical proof claim requiring certified third-party audit",
        ),
    ]

    @classmethod
    def analyze(
        cls, text: str, approved_claims: list[str] | None = None
    ) -> list[FindingItem]:
        findings: list[FindingItem] = []
        if not text:
            return findings

        approved_list = [c.lower() for c in (approved_claims or [])]

        # 1. Superiority claims
        for pattern_str, label, desc in cls.SUPERIORITY_PATTERNS:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            for match in pattern.finditer(text):
                snippet = match.group(0)
                # Check if this exact claim is in approved claims
                is_approved = any(snippet.lower() in ac for ac in approved_list)
                if not is_approved:
                    findings.append(
                        FindingItem(
                            category="claim",
                            severity="HIGH",
                            problematic_snippet=snippet,
                            explanation=(
                                f"Identified {desc.lower()} ('{snippet}'). "
                                "Advertising regulatory bodies (FTC/ASA) require substantiating independent market research data before making #1 or best-in-world claims."
                            ),
                            brand_guideline_ref="Marketing Integrity Code — Superlative & Comparative Claims",
                            approved_source_fact="No verified independent market research citation found in Brand Knowledge",
                            confidence=0.92,
                            recommended_correction="Replace superlative ranking with a verifiable functional value proposition (e.g. 'high-performance enterprise laptop').",
                            requires_human_verification=True,
                            finding_status="open",
                        )
                    )

        # 2. Absolute Guarantees
        for pattern_str, label, desc in cls.GUARANTEE_PATTERNS:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            for match in pattern.finditer(text):
                snippet = match.group(0)
                findings.append(
                    FindingItem(
                        category="claim",
                        severity="CRITICAL",
                        problematic_snippet=snippet,
                        explanation=(
                            f"Detected {desc.lower()} ('{snippet}'). "
                            "Brand compliance prohibits absolute warranties of user success, as individual operational outcomes depend on external customer variables."
                        ),
                        brand_guideline_ref="Legal & Risk Governance — Warranties & Guarantees",
                        approved_source_fact="Organizational Legal Risk Policy: No Absolute Outcome Guarantees",
                        confidence=0.96,
                        recommended_correction="engineered for exceptional productivity and reliability",
                        requires_human_verification=False,
                        finding_status="open",
                    )
                )

        # 3. Scientific proof claims
        for pattern_str, label, desc in cls.SCIENTIFIC_PATTERNS:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            for match in pattern.finditer(text):
                snippet = match.group(0)
                findings.append(
                    FindingItem(
                        category="claim",
                        severity="HIGH",
                        problematic_snippet=snippet,
                        explanation=f"Detected scientific validation claim ('{snippet}'). Requires documented lab test whitepaper citation.",
                        brand_guideline_ref="Scientific & Technical Evidence Standards",
                        approved_source_fact="Approved Technical Whitepapers",
                        confidence=0.90,
                        recommended_correction="rigorously tested under enterprise workloads",
                        requires_human_verification=True,
                        finding_status="open",
                    )
                )

        return findings
