import re

from backend.database.models import BrandGuideline
from backend.schemas.compliance import FindingItem


class ToneAnalyzer:
    """Evaluates tone, personality, hype intensity, and emotional consistency against approved voice."""

    HYPERBOLE_EXCLAMATIONS = re.compile(r"!{2,}")
    AGGRESSIVE_SALES_WORDS = [
        "blow your mind",
        "insane deal",
        "crazy fast",
        "unbelievable bargain",
        "act now or regret",
        "game changer",
        "revolutionary miracle",
    ]
    CASUAL_SLANG = ["gonna", "wanna", "kinda", "super dope", "no cap", "legit fire"]

    @classmethod
    def analyze(cls, text: str, guideline: BrandGuideline | None) -> list[FindingItem]:
        findings: list[FindingItem] = []
        if not text:
            return findings

        preferred_tone = (
            guideline.preferred_tone
            if guideline and guideline.preferred_tone
            else "Professional, approachable and trustworthy."
        )

        # 1. Excessive exclamation marks check
        exclamation_count = text.count("!")
        if exclamation_count >= 3 or cls.HYPERBOLE_EXCLAMATIONS.search(text):
            findings.append(
                FindingItem(
                    category="tone",
                    severity="MEDIUM",
                    problematic_snippet="Multiple exclamation points (!)",
                    explanation=(
                        f"Content uses excessive exclamation marks ({exclamation_count} occurrences). "
                        f"Brand voice emphasizes '{preferred_tone}'. Overly sensational punctuation diminishes corporate authority."
                    ),
                    brand_guideline_ref="Editorial Voice & Tone Manual — Punctuation & Emphasis",
                    approved_source_fact=f"Approved Brand Tone: '{preferred_tone}'",
                    confidence=0.88,
                    recommended_correction="Use confident, calm punctuation with single periods.",
                    requires_human_verification=False,
                    finding_status="open",
                )
            )

        # 2. Aggressive sales jargon / hype
        text_lower = text.lower()
        for phrase in cls.AGGRESSIVE_SALES_WORDS:
            if phrase in text_lower:
                findings.append(
                    FindingItem(
                        category="tone",
                        severity="MEDIUM",
                        problematic_snippet=phrase,
                        explanation=f"Overly aggressive sales jargon ('{phrase}') deviates from the approved tone ('{preferred_tone}').",
                        brand_guideline_ref="Editorial Voice & Tone Manual",
                        approved_source_fact=f"Brand Tone: '{preferred_tone}'",
                        confidence=0.90,
                        recommended_correction="Rephrase with measured, value-driven business prose.",
                        requires_human_verification=False,
                        finding_status="open",
                    )
                )

        # 3. Overly casual slang in enterprise copy
        for slang in cls.CASUAL_SLANG:
            if re.search(rf"\b{re.escape(slang)}\b", text_lower):
                findings.append(
                    FindingItem(
                        category="tone",
                        severity="LOW",
                        problematic_snippet=slang,
                        explanation=f"Informal colloquialism '{slang}' conflicts with enterprise brand positioning.",
                        brand_guideline_ref="Editorial Style Guide — Professional Register",
                        approved_source_fact=f"Approved Tone: '{preferred_tone}'",
                        confidence=0.95,
                        recommended_correction="Use formal enterprise phrasing.",
                        requires_human_verification=False,
                        finding_status="open",
                    )
                )

        return findings
