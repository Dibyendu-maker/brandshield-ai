import re

from backend.database.models import BrandFact
from backend.schemas.compliance import FindingItem


class FactualVerificationAnalyzer:
    """Verifies content statements against approved hardware/software specifications and policies."""

    @staticmethod
    def analyze(text: str, facts: list[BrandFact]) -> list[FindingItem]:
        findings: list[FindingItem] = []
        if not text or not facts:
            return findings

        # Group facts by key and product
        fact_dict = {}
        for f in facts:
            fact_dict[(f.product_name.lower(), f.fact_key.lower())] = f
            # Also store general key fallback
            fact_dict[f.fact_key.lower()] = f

        # 1. Battery Life Verification
        # Matches patterns like "24 hours of battery life", "24-hour battery", "battery life up to 24 hrs", "24 hours battery"
        battery_regex = re.compile(
            r"(\b(?:(?:up\s+to\s+)?(\d+)\s*(?:hours?|hrs?)\s+(?:of\s+)?battery(?:\s+life)?|battery(?:\s+life)?(?:\s+of)?\s+(?:up\s+to\s+)?(\d+)\s*(?:hours?|hrs?))\b)",
            re.IGNORECASE,
        )
        for match in battery_regex.finditer(text):
            full_match_str = match.group(1)
            # Find the number
            num_match = re.search(r"(\d+)", full_match_str)
            if not num_match:
                continue
            claimed_hours = int(num_match.group(1))

            # Retrieve approved battery fact
            approved_battery_fact = fact_dict.get("battery_life")
            if approved_battery_fact:
                approved_num_match = re.search(
                    r"(\d+)", approved_battery_fact.fact_value
                )
                approved_hours = (
                    int(approved_num_match.group(1)) if approved_num_match else None
                )

                if approved_hours and claimed_hours != approved_hours:
                    findings.append(
                        FindingItem(
                            category="factual",
                            severity="CRITICAL",
                            problematic_snippet=full_match_str,
                            explanation=(
                                f"Battery claim '{full_match_str}' conflicts with approved specification of {approved_battery_fact.fact_value}. "
                                f"Claiming {claimed_hours} hours creates severe regulatory liability under consumer truth-in-advertising laws."
                            ),
                            brand_guideline_ref="Product Specification Standards — Power & Battery",
                            approved_source_fact=f"{approved_battery_fact.fact_value} (Source: {approved_battery_fact.source_reference or 'Official Spec Sheet'})",
                            confidence=0.98,
                            recommended_correction=f"up to {approved_battery_fact.fact_value} of battery life",
                            requires_human_verification=False,
                            finding_status="open",
                        )
                    )

        # 2. Warranty Claim Verification
        # Matches patterns like "5-year warranty", "5 year warranty", "warranty of 5 years", "5 years warranty"
        warranty_regex = re.compile(
            r"(\b(?:(\d+)[- ]*(?:year|yr|years|yrs)\s+warranty|warranty\s+(?:of\s+)?(\d+)[- ]*(?:year|yr|years|yrs))\b)",
            re.IGNORECASE,
        )
        for match in warranty_regex.finditer(text):
            full_match_str = match.group(1)
            num_match = re.search(r"(\d+)", full_match_str)
            if not num_match:
                continue
            claimed_years = int(num_match.group(1))

            approved_warranty_fact = fact_dict.get("warranty_period")
            if approved_warranty_fact:
                approved_num_match = re.search(
                    r"(\d+)", approved_warranty_fact.fact_value
                )
                approved_years = (
                    int(approved_num_match.group(1)) if approved_num_match else None
                )

                if approved_years and claimed_years != approved_years:
                    findings.append(
                        FindingItem(
                            category="factual",
                            severity="CRITICAL",
                            problematic_snippet=full_match_str,
                            explanation=(
                                f"Warranty claim '{full_match_str}' contradicts approved warranty term ({approved_warranty_fact.fact_value}). "
                                f"Overstating warranty creates legally binding obligations that conflict with enterprise warranty reserves."
                            ),
                            brand_guideline_ref="Legal & Warranty Compliance Policy",
                            approved_source_fact=f"{approved_warranty_fact.fact_value} (Source: {approved_warranty_fact.source_reference or 'Warranty Policy'})",
                            confidence=0.98,
                            recommended_correction=f"{approved_warranty_fact.fact_value} warranty",
                            requires_human_verification=False,
                            finding_status="open",
                        )
                    )

        # 3. Pricing Verification
        # Matches patterns like "$999", "$1,499"
        price_regex = re.compile(r"(\$\s*[\d,]+(?:\.\d{2})?)", re.IGNORECASE)
        approved_price_fact = fact_dict.get("base_price")
        if approved_price_fact:
            approved_clean_price = approved_price_fact.fact_value.replace(
                " ", ""
            ).lower()
            for match in price_regex.finditer(text):
                claimed_price = match.group(1).replace(" ", "").lower()
                if (
                    claimed_price not in approved_clean_price
                    and approved_clean_price not in claimed_price
                ):
                    findings.append(
                        FindingItem(
                            category="factual",
                            severity="CRITICAL",
                            problematic_snippet=match.group(1),
                            explanation=f"Submitted price '{match.group(1)}' does not match the approved enterprise base price ({approved_price_fact.fact_value}).",
                            brand_guideline_ref="Enterprise Pricing Catalog & Revenue Governance",
                            approved_source_fact=f"{approved_price_fact.fact_value} (Source: {approved_price_fact.source_reference or 'Price Sheet'})",
                            confidence=0.95,
                            recommended_correction=approved_price_fact.fact_value,
                            requires_human_verification=True,
                            finding_status="open",
                        )
                    )

        return findings
