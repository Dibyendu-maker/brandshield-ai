import re

from backend.schemas.compliance import FindingItem


class AccessibilityAnalyzer:
    """Evaluates text readability, WCAG 2.1 AA cognitive accessibility heuristics, and content clarity."""

    @staticmethod
    def _count_syllables(word: str) -> int:
        word = word.lower().strip(".:;?!")
        if len(word) <= 3:
            return 1
        word = re.sub(r"(?:[^laeiouy]|ed|es|e)$", "", word)
        word = re.sub(r"^y", "", word)
        syllables = len(re.findall(r"[aeiouy]{1,2}", word))
        return max(1, syllables)

    @classmethod
    def calculate_readability(cls, text: str) -> dict[str, float]:
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        words = re.findall(r"\b[A-Za-z0-9\'-]+\b", text)

        num_sentences = max(1, len(sentences))
        num_words = max(1, len(words))
        num_syllables = sum(cls._count_syllables(w) for w in words)

        # Flesch Reading Ease Formula: 206.835 - 1.015*(words/sentences) - 84.6*(syllables/words)
        asl = num_words / num_sentences
        asw = num_syllables / num_words
        flesch_score = round(206.835 - (1.015 * asl) - (84.6 * asw), 1)
        flesch_score = max(0.0, min(100.0, flesch_score))

        # Flesch-Kincaid Grade Level: 0.39*(words/sentences) + 11.8*(syllables/words) - 15.59
        grade_level = round(0.39 * asl + 11.8 * asw - 15.59, 1)

        return {
            "flesch_reading_ease": flesch_score,
            "grade_level": max(1.0, grade_level),
            "avg_sentence_length": round(asl, 1),
            "sentence_count": num_sentences,
            "word_count": num_words,
        }

    @classmethod
    def analyze(
        cls, text: str, has_image_without_alt: bool = False
    ) -> list[FindingItem]:
        findings: list[FindingItem] = []
        if not text:
            return findings

        # 1. Missing Alt-Text check
        if has_image_without_alt:
            findings.append(
                FindingItem(
                    category="accessibility",
                    severity="MEDIUM",
                    problematic_snippet="Image asset without accompanying descriptive alt text",
                    explanation="Non-text visual elements require descriptive alternative text for screen reader compatibility under WCAG 2.1 Guideline 1.1.1 (Non-text Content).",
                    brand_guideline_ref="WCAG 2.1 AA / Digital Accessibility Standard §1.1.1",
                    approved_source_fact="Enterprise Digital Accessibility Governance",
                    confidence=1.0,
                    recommended_correction="Provide descriptive alt text conveying the key product visual and context.",
                    requires_human_verification=False,
                    finding_status="open",
                )
            )

        # 2. All-caps shouting check
        all_caps_words = [
            w
            for w in re.findall(r"\b[A-Z]{4,}\b", text)
            if w
            not in ["HTML", "OLED", "RAM", "SSD", "USB", "CPU", "GPU", "HDMI", "NVME"]
        ]
        if len(all_caps_words) >= 3:
            findings.append(
                FindingItem(
                    category="accessibility",
                    severity="LOW",
                    problematic_snippet=" ".join(all_caps_words[:4]),
                    explanation="Consecutive all-capitalized words hinder readability for neurodivergent audiences and can cause screen readers to announce words as individual acronym letters.",
                    brand_guideline_ref="Editorial Accessibility Standard — Typography & Casing",
                    approved_source_fact="WCAG 2.1 Readable Text Heuristics",
                    confidence=0.90,
                    recommended_correction="Convert all-caps phrases to standard title or sentence case.",
                    requires_human_verification=False,
                    finding_status="open",
                )
            )

        # 3. Excessive sentence complexity (> 35 words per sentence)
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
        for s in sentences:
            words_in_s = s.split()
            if len(words_in_s) > 38:
                findings.append(
                    FindingItem(
                        category="accessibility",
                        severity="LOW",
                        problematic_snippet=s[:70] + "...",
                        explanation=f"Overly complex sentence ({len(words_in_s)} words). Plain language guidelines recommend breaking sentences over 30 words into smaller units to improve cognitive accessibility.",
                        brand_guideline_ref="WCAG 2.1 AA Guideline 3.1 (Understandable Content)",
                        approved_source_fact="Cognitive Accessibility & Plain Language Standards",
                        confidence=0.85,
                        recommended_correction="Divide long sentence into concise, direct statements.",
                        requires_human_verification=False,
                        finding_status="open",
                    )
                )

        return findings
