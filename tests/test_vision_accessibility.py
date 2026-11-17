from ai_engine.analysis.accessibility import AccessibilityAnalyzer
from ai_engine.vision.analyzer import VisualBrandAnalyzer


def test_readability_metrics():
    text = (
        "Introducing NovaBook Pro, an enterprise laptop offering up to 12 hours of "
        "battery life and backed by a 1-year warranty."
    )
    metrics = AccessibilityAnalyzer.calculate_readability(text)
    assert "flesch_reading_ease" in metrics
    assert metrics["flesch_reading_ease"] > 0
    assert metrics["grade_level"] > 0


def test_wcag_contrast_ratio():
    # White #FFFFFF and Black #000000 -> 21:1
    white_rgb = (255, 255, 255)
    black_rgb = (0, 0, 0)
    contrast = VisualBrandAnalyzer.calculate_contrast_ratio(white_rgb, black_rgb)
    assert contrast == 21.0

    # Low contrast: Dark navy #0B132B and Dark slate #1C2541
    navy_rgb = VisualBrandAnalyzer.hex_to_rgb("#0B132B")
    slate_rgb = VisualBrandAnalyzer.hex_to_rgb("#1C2541")
    low_contrast = VisualBrandAnalyzer.calculate_contrast_ratio(navy_rgb, slate_rgb)
    assert low_contrast < 3.0, f"Expected low contrast, got {low_contrast}"


def test_color_distance():
    c1 = (10, 20, 30)
    c2 = (10, 20, 30)
    assert VisualBrandAnalyzer.color_distance(c1, c2) == 0.0

    c3 = (255, 255, 255)
    assert VisualBrandAnalyzer.color_distance(c1, c3) > 100.0
