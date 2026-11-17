from pathlib import Path

from ai_engine.vision.analyzer import VisualBrandAnalyzer


def test_compliant_image_colors():
    logo_path = Path("sample_data/novatech_logo_compliant.png")
    assert logo_path.exists()

    approved_palette = ["#0B132B", "#1C2541", "#3A506B", "#5BC0BE", "#6FFFE9"]
    result = VisualBrandAnalyzer.analyze_image(
        str(logo_path), approved_palette, "NovaTech"
    )

    assert len(result["dominant_colors"]) > 0
    # Primary dominant color should be dark navy #0B132B
    top_color = result["dominant_colors"][0]
    assert (
        top_color["hex"] in ["#0B132B", "#0C132B"]
        or VisualBrandAnalyzer.color_distance(top_color["rgb"], (11, 19, 43)) < 15.0
    )


def test_unapproved_image_flags_violations():
    bad_img_path = Path("sample_data/unapproved_promo_banner.png")
    assert bad_img_path.exists()

    approved_palette = ["#0B132B", "#1C2541", "#3A506B", "#5BC0BE", "#6FFFE9"]
    result = VisualBrandAnalyzer.analyze_image(
        str(bad_img_path), approved_palette, "NovaTech"
    )

    # Should detect unapproved red color
    findings = result["findings"]
    categories = [f.category for f in findings]
    assert "visual" in categories, "Must flag unapproved red dominant color"
