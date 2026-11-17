from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class BrandGuidelineBase(BaseModel):
    brand_name: str
    brand_description: str | None = None
    mission_values: str | None = None
    preferred_tone: str | None = None
    prohibited_phrases: list[str] = []
    preferred_terminology: dict[str, str] = {}
    color_palette: list[str] = []
    typography_rules: dict[str, Any] = {}
    approved_claims: list[str] = []


class BrandGuidelineCreate(BrandGuidelineBase):
    pass


class BrandGuidelineUpdate(BaseModel):
    brand_name: str | None = None
    brand_description: str | None = None
    mission_values: str | None = None
    preferred_tone: str | None = None
    prohibited_phrases: list[str] | None = None
    preferred_terminology: dict[str, str] | None = None
    color_palette: list[str] | None = None
    typography_rules: dict[str, Any] | None = None
    approved_claims: list[str] | None = None


class BrandGuidelineOut(BrandGuidelineBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    logo_path: str | None = None
    created_at: datetime
    updated_at: datetime


class BrandFactBase(BaseModel):
    product_name: str
    category: str  # specification, pricing, warranty, claim
    fact_key: str
    fact_value: str
    source_reference: str | None = None
    notes: str | None = None


class BrandFactCreate(BrandFactBase):
    pass


class BrandFactOut(BrandFactBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime


class BrandDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    filename: str
    file_type: str
    document_title: str | None = None
    chunk_count: int
    uploaded_at: datetime
