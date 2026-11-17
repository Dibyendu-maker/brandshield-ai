from ai_engine.engine import ComplianceEngine
from backend.database.models import BrandGuideline


def test_novatech_demonstration_scenario(db_session):
    """Verifies all 5 canonical findings and the expected suggestion for NovaTech."""
    # Retrieve NovaTech organization
    guideline = db_session.query(BrandGuideline).first()
    assert guideline is not None, "NovaTech guidelines must be seeded"
    org_id = guideline.organization_id

    # Canonical flawed marketing copy
    test_ad = (
        "Introducing NovaBook Pro! The world's number one laptop with 24 hours of "
        "battery life and a 5-year warranty. Guaranteed success for every user!"
    )

    result = ComplianceEngine.audit_content(
        text=test_ad, image_path=None, org_id=org_id, db=db_session
    )

    # 1. Total violations & scoring check
    assert result.total_violations >= 4, (
        f"Expected at least 4 violations, got {result.total_violations}"
    )
    assert result.overall_score < 70, (
        f"Expected score penalized, got {result.overall_score}"
    )

    categories = [f.category for f in result.findings]
    snippets = [f.problematic_snippet.lower() for f in result.findings]

    # 2. Check Factual Contradictions: Battery Life & Warranty
    assert "factual" in categories, "Must detect factual contradictions"
    battery_finding = next(
        (
            f
            for f in result.findings
            if f.category == "factual" and "battery" in f.problematic_snippet.lower()
        ),
        None,
    )
    assert battery_finding is not None, (
        "Must detect 24 hours battery life contradiction"
    )
    assert battery_finding.severity == "CRITICAL"
    assert "12 hours" in battery_finding.approved_source_fact

    warranty_finding = next(
        (
            f
            for f in result.findings
            if f.category == "factual" and "warranty" in f.problematic_snippet.lower()
        ),
        None,
    )
    assert warranty_finding is not None, "Must detect 5-year warranty contradiction"
    assert warranty_finding.severity == "CRITICAL"
    assert "1 year" in warranty_finding.approved_source_fact

    # 3. Check Prohibited Terminology
    assert "terminology" in categories, "Must detect terminology violation"
    term_finding = next(
        (
            f
            for f in result.findings
            if "guaranteed success" in f.problematic_snippet.lower()
        ),
        None,
    )
    assert term_finding is not None, "Must detect 'Guaranteed success'"

    # 4. Check Superiority Claim
    claim_finding = next(
        (f for f in result.findings if "number one" in f.problematic_snippet.lower()),
        None,
    )
    assert claim_finding is not None, "Must detect 'world's number one' claim"

    # 5. Check Suggested Revision
    suggested = result.suggested_revision
    print("\n--- TEST SUGGESTED REVISION ---")
    print(suggested)
    print("--------------------------------\n")

    assert "NovaBook Pro" in suggested
    assert "12 hours" in suggested, "Must correct battery life to 12 hours"
    assert "1-year" in suggested or "1 year" in suggested, (
        "Must correct warranty to 1 year"
    )
    assert "Guaranteed success" not in suggested, "Must eliminate prohibited phrase"
    assert "AI-powered productivity" in suggested or "productivity" in suggested
