import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from backend.core.config import settings
from backend.schemas.compliance import FindingItem


class VisualBrandAnalyzer:
    """Multimodal brand compliance: Combines deterministic color/contrast metrics with Gemini Vision."""

    @staticmethod
    def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
        hex_clean = hex_str.lstrip("#")
        if len(hex_clean) == 3:
            hex_clean = "".join([c * 2 for c in hex_clean])
        return tuple(int(hex_clean[i : i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
        return f"#{int(rgb[0]):02x}{int(rgb[1]):02x}{int(rgb[2]):02x}".upper()

    @staticmethod
    def calculate_relative_luminance(rgb: tuple[int, int, int]) -> float:
        """Calculates WCAG 2.1 relative luminance for an sRGB color."""
        srgb = [c / 255.0 for c in rgb]
        linear = [
            c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    @classmethod
    def calculate_contrast_ratio(
        cls, color1: tuple[int, int, int], color2: tuple[int, int, int]
    ) -> float:
        """Calculates WCAG 2.1 contrast ratio between two colors."""
        l1 = cls.calculate_relative_luminance(color1)
        l2 = cls.calculate_relative_luminance(color2)
        brightest = max(l1, l2)
        darkest = min(l1, l2)
        ratio = (brightest + 0.05) / (darkest + 0.05)
        return round(ratio, 2)

    @classmethod
    def extract_dominant_colors(
        cls, image_path: str, k: int = 5
    ) -> list[dict[str, Any]]:
        """Uses K-Means clustering in OpenCV to objectively extract dominant colors and their percentages."""
        img = cv2.imread(image_path)
        if img is None:
            return []
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Resize for fast, consistent processing
        img_small = cv2.resize(img_rgb, (150, 150), interpolation=cv2.INTER_AREA)
        pixels = img_small.reshape((-1, 3)).astype(np.float32)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(
            pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
        )

        counts = np.bincount(labels.flatten())
        total_pixels = len(labels)

        dominant = []
        for i, center in enumerate(centers):
            rgb = tuple(int(round(c)) for c in center)
            percentage = round((counts[i] / total_pixels) * 100, 1)
            dominant.append(
                {"hex": cls.rgb_to_hex(rgb), "rgb": rgb, "percentage": percentage}
            )

        # Sort descending by prevalence
        dominant.sort(key=lambda x: x["percentage"], reverse=True)
        return dominant

    @classmethod
    def color_distance(
        cls, rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]
    ) -> float:
        """Euclidean distance in RGB color space."""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))

    @classmethod
    def analyze_image(
        cls, image_path: str, approved_palette: list[str], brand_name: str = "NovaTech"
    ) -> dict[str, Any]:
        """Runs multimodal visual brand inspection."""
        path = Path(image_path)
        if not path.exists():
            return {
                "error": "Image file not found",
                "findings": [],
                "dominant_colors": [],
            }

        dominant_colors = cls.extract_dominant_colors(image_path, k=5)
        findings: list[FindingItem] = []

        # 1. Deterministic Color Palette Compliance
        approved_rgbs = (
            [cls.hex_to_rgb(h) for h in approved_palette] if approved_palette else []
        )
        palette_match_score = 100.0

        if approved_rgbs and dominant_colors:
            unapproved_colors = []
            for item in dominant_colors:
                # Find minimum distance to any approved color
                min_dist = min(
                    cls.color_distance(item["rgb"], app_rgb)
                    for app_rgb in approved_rgbs
                )
                # Distance threshold > 80 indicates noticeable deviation
                if min_dist > 80.0 and item["percentage"] > 10.0:
                    unapproved_colors.append((item["hex"], item["percentage"]))

            if unapproved_colors:
                unapproved_str = ", ".join(
                    [f"{h} ({p}%)" for h, p in unapproved_colors]
                )
                findings.append(
                    FindingItem(
                        category="visual",
                        severity="HIGH",
                        problematic_snippet=f"Unapproved dominant color(s): {unapproved_str}",
                        explanation=(
                            f"Image uses dominant colors that deviate significantly from the approved brand palette "
                            f"({', '.join(approved_palette[:5])}). Objective color-space distance exceeds brand tolerance."
                        ),
                        brand_guideline_ref="Visual Brand Identity — Approved Color System",
                        approved_source_fact=f"Approved Palette: {', '.join(approved_palette)}",
                        confidence=0.96,
                        recommended_correction=f"Adjust artwork color grading to align with approved primary hues: {', '.join(approved_palette[:3])}.",
                        requires_human_verification=False,
                        finding_status="open",
                    )
                )

        # 2. Deterministic WCAG Color Contrast Evaluation
        if len(dominant_colors) >= 2:
            top_dark = min(
                dominant_colors[:3],
                key=lambda x: cls.calculate_relative_luminance(x["rgb"]),
            )
            top_bright = max(
                dominant_colors[:3],
                key=lambda x: cls.calculate_relative_luminance(x["rgb"]),
            )
            contrast = cls.calculate_contrast_ratio(top_dark["rgb"], top_bright["rgb"])

            if contrast < 4.5:
                findings.append(
                    FindingItem(
                        category="accessibility",
                        severity="MEDIUM",
                        problematic_snippet=f"Color contrast ratio: {contrast}:1 between {top_dark['hex']} and {top_bright['hex']}",
                        explanation=(
                            f"Primary visual contrast ratio ({contrast}:1) falls below WCAG 2.1 Level AA requirement (4.5:1 for standard text, 3.0:1 for large graphical elements). "
                            "May fail digital accessibility standards for low-vision users."
                        ),
                        brand_guideline_ref="WCAG 2.1 AA §1.4.3 (Minimum Contrast)",
                        approved_source_fact="Enterprise Digital Accessibility Guidelines",
                        confidence=0.99,
                        recommended_correction="Increase contrast between background and overlaid textual/graphical elements to at least 4.5:1.",
                        requires_human_verification=False,
                        finding_status="open",
                    )
                )

        # 3. Contextual Visual Inspection via Gemini Vision (if configured)
        gemini_result = cls._run_gemini_vision(image_path, brand_name, approved_palette)
        if gemini_result and "findings" in gemini_result:
            findings.extend(gemini_result["findings"])

        return {
            "dominant_colors": dominant_colors,
            "findings": findings,
            "gemini_analysis": gemini_result.get(
                "narrative", "Deterministic visual inspection completed."
            ),
        }

    @classmethod
    def _run_gemini_vision(
        cls, image_path: str, brand_name: str, approved_palette: list[str]
    ) -> dict[str, Any]:
        """Calls Gemini Vision API if key is available; otherwise gracefully returns structured observation."""
        if not settings.GEMINI_API_KEY:
            return {
                "narrative": "Standard deterministic visual compliance checks completed (Gemini API key not configured)."
            }

        try:
            from google import genai

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            prompt = (
                f"You are BrandShield AI Visual Compliance Inspector. Analyze this marketing image for the brand '{brand_name}'. "
                f"Approved brand color palette: {', '.join(approved_palette)}. "
                "Evaluate:\n"
                "1. Logo presence, clear space, and distortion.\n"
                "2. Overall visual tone and composition.\n"
                "3. Any unauthorized visual artifacts or inappropriate imagery.\n"
                "Keep response concise and professional."
            )

            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[
                    genai.types.Part.from_bytes(
                        data=image_bytes, mime_type="image/jpeg"
                    ),
                    prompt,
                ],
            )
            narrative = (
                response.text
                if response and response.text
                else "Visual inspection completed."
            )
            return {"narrative": narrative}
        except Exception as e:
            return {
                "narrative": f"Gemini Vision contextual inspection unavailable ({e!s}). Deterministic inspection applied."
            }
