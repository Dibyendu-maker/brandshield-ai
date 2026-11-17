from typing import Any

from sqlalchemy.orm import Session

from ai_engine.embeddings.vector_store import vector_store
from backend.database.models import BrandFact, BrandGuideline


class HybridRetriever:
    """Combines deterministic relational brand truth with semantic vector retrieval."""

    def __init__(self, db: Session, org_id: int):
        self.db = db
        self.org_id = org_id

    def get_guideline(self) -> BrandGuideline | None:
        return (
            self.db.query(BrandGuideline)
            .filter(BrandGuideline.organization_id == self.org_id)
            .first()
        )

    def get_all_facts(self) -> list[BrandFact]:
        return (
            self.db.query(BrandFact)
            .filter(BrandFact.organization_id == self.org_id)
            .all()
        )

    def get_facts_for_product(self, product_name: str) -> list[BrandFact]:
        # Case-insensitive substring match
        return (
            self.db.query(BrandFact)
            .filter(
                BrandFact.organization_id == self.org_id,
                BrandFact.product_name.ilike(f"%{product_name}%"),
            )
            .all()
        )

    def search_semantic_guidelines(
        self, query: str, top_k: int = 3
    ) -> list[dict[str, Any]]:
        return vector_store.search_similar(self.org_id, query, n_results=top_k)

    def retrieve_ground_truth_context(self, text: str) -> dict[str, Any]:
        """Assembles comprehensive ground truth evidence relevant to the submitted text."""
        guideline = self.get_guideline()
        all_facts = self.get_all_facts()
        semantic_matches = self.search_semantic_guidelines(text, top_k=3)

        # Match facts mentioned in text
        relevant_facts = []
        text_lower = text.lower()
        for fact in all_facts:
            # Check if product name or fact key/concept appears
            if (
                fact.product_name.lower() in text_lower
                or fact.fact_key.lower().replace("_", " ") in text_lower
                or "battery" in text_lower
                and "battery" in fact.fact_key.lower()
                or "warranty" in text_lower
                and "warranty" in fact.fact_key.lower()
                or "price" in text_lower
                and ("price" in fact.fact_key.lower() or "$" in fact.fact_value)
            ):
                relevant_facts.append(fact)

        # Fallback to all facts if none specifically matched
        if not relevant_facts:
            relevant_facts = all_facts

        return {
            "guideline": guideline,
            "matched_facts": relevant_facts,
            "all_facts": all_facts,
            "semantic_excerpts": semantic_matches,
        }
