from ai_engine.analysis.facts import FactualVerificationAnalyzer
from backend.database.models import BrandFact


def test_pricing_verification_without_warranty_fact():
    """Regression test: verifies pricing contradiction when no warranty fact exists in facts list.
    Previously failed with UnboundLocalError: local variable 'approved_fact' referenced before assignment.
    """
    facts = [
        BrandFact(
            product_name="NovaBook Pro",
            fact_key="base_price",
            fact_value="$1,299 USD",
            source_reference="Enterprise Hardware Catalog",
        )
    ]
    # Copy mentions wrong price, zero mention of warranty or battery
    text = "Get the latest NovaBook Pro starting at an unbelievable price of $799!"

    findings = FactualVerificationAnalyzer.analyze(text, facts)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.category == "factual"
    assert finding.severity == "CRITICAL"
    assert finding.problematic_snippet == "$799"
    assert "$1,299 USD" in finding.explanation
    assert "$1,299 USD" in finding.approved_source_fact
    assert finding.recommended_correction == "$1,299 USD"


def test_pricing_verification_with_matching_warranty_fact():
    """Regression test: verifies pricing explanation does not erroneously display warranty fact value
    when both warranty and pricing facts are present.
    """
    facts = [
        BrandFact(
            product_name="NovaBook Pro",
            fact_key="warranty_period",
            fact_value="1 year",
            source_reference="Warranty Policy",
        ),
        BrandFact(
            product_name="NovaBook Pro",
            fact_key="base_price",
            fact_value="$1,299 USD",
            source_reference="Price Sheet",
        ),
    ]
    # Warranty is compliant (1-year), but price is incorrect ($899)
    text = "NovaBook Pro includes a 1-year warranty and is available today for $899!"

    findings = FactualVerificationAnalyzer.analyze(text, facts)

    # Only pricing should be flagged
    assert len(findings) == 1
    finding = findings[0]
    assert finding.category == "factual"
    assert finding.problematic_snippet == "$899"
    # Explanation must state the approved base price, not the warranty term
    assert "$1,299 USD" in finding.explanation
    assert "1 year" not in finding.explanation


def test_warranty_verification_missing_approved_facts():
    """Regression test: warranty statement in text when no approved warranty fact is registered."""
    # Facts list has no warranty fact registered
    facts = [
        BrandFact(
            product_name="NovaBook Pro",
            fact_key="battery_life",
            fact_value="12 hours",
            source_reference="Spec Sheet",
        )
    ]
    text = "NovaBook Pro comes with a 3-year warranty."

    findings = FactualVerificationAnalyzer.analyze(text, facts)

    # Should not raise exception and should produce no ungrounded findings
    assert len(findings) == 0


def test_normal_successful_fact_verification():
    """Verifies that 100% compliant specifications pass with zero violations."""
    facts = [
        BrandFact(
            product_name="NovaBook Pro",
            fact_key="battery_life",
            fact_value="12 hours",
            source_reference="Hardware Spec 2026",
        ),
        BrandFact(
            product_name="NovaBook Pro",
            fact_key="warranty_period",
            fact_value="1 year",
            source_reference="Warranty Policy 2026",
        ),
        BrandFact(
            product_name="NovaBook Pro",
            fact_key="base_price",
            fact_value="$1,299 USD",
            source_reference="Catalog 2026",
        ),
    ]
    # Fully compliant copy
    text = (
        "NovaBook Pro delivers up to 12 hours of battery life and is backed by a "
        "1-year warranty, starting at $1,299 USD."
    )

    findings = FactualVerificationAnalyzer.analyze(text, facts)
    assert len(findings) == 0, f"Expected 0 violations for compliant copy, got {len(findings)}"


def test_factual_violations_battery_and_warranty():
    """Verifies that conflicting battery and warranty claims are both detected with CRITICAL severity."""
    facts = [
        BrandFact(
            product_name="NovaBook Pro",
            fact_key="battery_life",
            fact_value="12 hours",
            source_reference="Hardware Spec",
        ),
        BrandFact(
            product_name="NovaBook Pro",
            fact_key="warranty_period",
            fact_value="1 year",
            source_reference="Warranty Terms",
        ),
    ]
    text = "NovaBook Pro features 24 hours of battery life and a 5-year warranty."

    findings = FactualVerificationAnalyzer.analyze(text, facts)
    assert len(findings) == 2
    snippets = [f.problematic_snippet for f in findings]
    assert any("24 hours" in s for s in snippets)
    assert any("5-year warranty" in s for s in snippets)
    assert all(f.severity == "CRITICAL" for f in findings)
