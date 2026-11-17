import json

from backend.core.security import get_password_hash
from backend.database.models import BrandFact, BrandGuideline, Organization, User
from backend.database.session import Base, SessionLocal, engine


def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if NovaTech organization exists
        org = db.query(Organization).filter(Organization.slug == "novatech").first()
        if not org:
            org = Organization(name="NovaTech Global", slug="novatech")
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"[InitDB] Created organization: {org.name} (ID: {org.id})")

        # Seed Users
        users_to_seed = [
            ("admin@novatech.com", "NovaTech Admin", "admin"),
            ("creator@novatech.com", "Alex Content Creator", "creator"),
            ("reviewer@novatech.com", "Sarah Brand Reviewer", "reviewer"),
        ]

        for email, full_name, role in users_to_seed:
            existing_user = db.query(User).filter(User.email == email).first()
            if not existing_user:
                new_user = User(
                    organization_id=org.id,
                    email=email,
                    hashed_password=get_password_hash("Password123!"),
                    full_name=full_name,
                    role=role,
                    is_active=True,
                )
                db.add(new_user)
                db.commit()
                print(f"[InitDB] Created user: {email} ({role})")

        # Seed Brand Guidelines for NovaTech
        existing_guideline = (
            db.query(BrandGuideline)
            .filter(BrandGuideline.organization_id == org.id)
            .first()
        )
        if not existing_guideline:
            guideline = BrandGuideline(
                organization_id=org.id,
                brand_name="NovaTech",
                brand_description="NovaTech is a next-generation enterprise technology provider delivering high-reliability hardware and AI productivity tools.",
                mission_values="Empowering global teams with trusted, cutting-edge AI productivity hardware and software solutions.",
                preferred_tone="Professional, approachable and trustworthy.",
                prohibited_phrases=json.dumps(
                    [
                        "Guaranteed success",
                        "100% guaranteed",
                        "world's number one",
                        "number one in the industry",
                        "best product in the world",
                        "best laptop in the world",
                        "unbeatable performance",
                        "zero flaws",
                    ]
                ),
                preferred_terminology=json.dumps(
                    {
                        "guaranteed success": "proven productivity gains",
                        "world's number one": "leading enterprise",
                        "best in the world": "top-tier",
                        "unlimited battery": "extended battery life",
                        "foolproof": "resilient and intuitive",
                    }
                ),
                color_palette=json.dumps(
                    ["#0B132B", "#1C2541", "#3A506B", "#5BC0BE", "#6FFFE9"]
                ),
                typography_rules=json.dumps(
                    {
                        "primary_font": "Inter",
                        "heading_font": "Plus Jakarta Sans",
                        "body_weight": "400",
                        "heading_weight": "700",
                    }
                ),
                approved_claims=json.dumps(
                    [
                        "AI-powered productivity laptop for modern enterprises.",
                        "Up to 12 hours of enterprise battery life.",
                        "Backed by an industry-standard 1-year limited hardware warranty.",
                        "Designed for hybrid workforces and secure data environments.",
                    ]
                ),
            )
            db.add(guideline)
            db.commit()
            print("[InitDB] Seeded NovaTech Brand Guidelines.")

        # Seed Brand Facts
        existing_facts = (
            db.query(BrandFact).filter(BrandFact.organization_id == org.id).count()
        )
        if existing_facts == 0:
            facts = [
                BrandFact(
                    organization_id=org.id,
                    product_name="NovaBook Pro",
                    category="specification",
                    fact_key="battery_life",
                    fact_value="12 hours",
                    source_reference="NovaBook Pro Official Hardware Spec Sheet 2026, Section 3.2",
                    notes="Verified under standard enterprise productivity benchmark test.",
                ),
                BrandFact(
                    organization_id=org.id,
                    product_name="NovaBook Pro",
                    category="warranty",
                    fact_key="warranty_period",
                    fact_value="1 year",
                    source_reference="NovaTech Global Warranty Policy & Terms 2026, Section 1",
                    notes="Standard limited hardware manufacturer warranty.",
                ),
                BrandFact(
                    organization_id=org.id,
                    product_name="NovaBook Pro",
                    category="pricing",
                    fact_key="base_price",
                    fact_value="$1,299 USD",
                    source_reference="NovaTech Enterprise Q4 Hardware Catalog",
                    notes="MSRP for baseline configuration (16GB RAM, 512GB SSD).",
                ),
                BrandFact(
                    organization_id=org.id,
                    product_name="NovaBook Pro",
                    category="claim",
                    fact_key="core_positioning",
                    fact_value="AI-powered productivity",
                    source_reference="NovaTech Product Marketing Brand Book 2026",
                    notes="Mandatory product category descriptor.",
                ),
                BrandFact(
                    organization_id=org.id,
                    product_name="NovaBook Pro",
                    category="specification",
                    fact_key="display",
                    fact_value="14.2-inch Liquid Retina OLED, 120Hz",
                    source_reference="NovaBook Pro Spec Sheet 2026, Section 2",
                    notes="Factory calibrated display.",
                ),
            ]
            db.add_all(facts)
            db.commit()
            print(f"[InitDB] Seeded {len(facts)} Brand Facts for NovaBook Pro.")

    finally:
        db.close()


if __name__ == "__main__":
    init_db()
