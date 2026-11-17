import json
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ai_engine.embeddings.vector_store import vector_store
from ai_engine.ingestion.extractor import DocumentExtractor
from backend.api.deps import get_current_user, get_db, require_roles
from backend.core.config import settings
from backend.database.models import BrandDocument, BrandFact, BrandGuideline, User
from backend.schemas.brand import (
    BrandDocumentOut,
    BrandFactCreate,
    BrandFactOut,
    BrandGuidelineOut,
    BrandGuidelineUpdate,
)

router = APIRouter(prefix="/brand", tags=["Brand Knowledge"])


@router.get("/guidelines", response_model=BrandGuidelineOut)
def get_guidelines(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    guideline = (
        db.query(BrandGuideline)
        .filter(BrandGuideline.organization_id == current_user.organization_id)
        .first()
    )
    if not guideline:
        # Create empty default guideline if not existing
        guideline = BrandGuideline(
            organization_id=current_user.organization_id,
            brand_name="NovaTech",
            preferred_tone="Professional, approachable and trustworthy.",
        )
        db.add(guideline)
        db.commit()
        db.refresh(guideline)

    return BrandGuidelineOut(
        id=guideline.id,
        organization_id=guideline.organization_id,
        brand_name=guideline.brand_name,
        brand_description=guideline.brand_description,
        mission_values=guideline.mission_values,
        preferred_tone=guideline.preferred_tone,
        prohibited_phrases=guideline.get_prohibited_phrases(),
        preferred_terminology=guideline.get_preferred_terminology(),
        color_palette=guideline.get_color_palette(),
        typography_rules=json.loads(guideline.typography_rules)
        if guideline.typography_rules
        else {},
        approved_claims=json.loads(guideline.approved_claims)
        if guideline.approved_claims
        else [],
        logo_path=guideline.logo_path,
        created_at=guideline.created_at,
        updated_at=guideline.updated_at,
    )


@router.put("/guidelines", response_model=BrandGuidelineOut)
def update_guidelines(
    data: BrandGuidelineUpdate,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    guideline = (
        db.query(BrandGuideline)
        .filter(BrandGuideline.organization_id == current_user.organization_id)
        .first()
    )
    if not guideline:
        guideline = BrandGuideline(
            organization_id=current_user.organization_id, brand_name="NovaTech"
        )
        db.add(guideline)

    if data.brand_name is not None:
        guideline.brand_name = data.brand_name
    if data.brand_description is not None:
        guideline.brand_description = data.brand_description
    if data.mission_values is not None:
        guideline.mission_values = data.mission_values
    if data.preferred_tone is not None:
        guideline.preferred_tone = data.preferred_tone
    if data.prohibited_phrases is not None:
        guideline.prohibited_phrases = json.dumps(data.prohibited_phrases)
    if data.preferred_terminology is not None:
        guideline.preferred_terminology = json.dumps(data.preferred_terminology)
    if data.color_palette is not None:
        guideline.color_palette = json.dumps(data.color_palette)
    if data.typography_rules is not None:
        guideline.typography_rules = json.dumps(data.typography_rules)
    if data.approved_claims is not None:
        guideline.approved_claims = json.dumps(data.approved_claims)

    db.commit()
    db.refresh(guideline)

    return BrandGuidelineOut(
        id=guideline.id,
        organization_id=guideline.organization_id,
        brand_name=guideline.brand_name,
        brand_description=guideline.brand_description,
        mission_values=guideline.mission_values,
        preferred_tone=guideline.preferred_tone,
        prohibited_phrases=guideline.get_prohibited_phrases(),
        preferred_terminology=guideline.get_preferred_terminology(),
        color_palette=guideline.get_color_palette(),
        typography_rules=json.loads(guideline.typography_rules)
        if guideline.typography_rules
        else {},
        approved_claims=json.loads(guideline.approved_claims)
        if guideline.approved_claims
        else [],
        logo_path=guideline.logo_path,
        created_at=guideline.created_at,
        updated_at=guideline.updated_at,
    )


@router.post("/guidelines/upload", response_model=BrandDocumentOut)
async def upload_guideline_document(
    file: UploadFile = File(...),
    document_title: str = Form(None),
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".docx", ".txt", ".md"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported guideline document format '{ext}'. Supported formats: PDF, DOCX, TXT, MD",
        )

    # Save to disk
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    save_path = Path(settings.UPLOAD_DIR) / unique_name
    content_bytes = await file.read()

    with open(save_path, "wb") as f:
        f.write(content_bytes)

    # Extract text & sections
    try:
        extracted = DocumentExtractor.extract_from_file(str(save_path))
        text = extracted["text"]
        chunks = DocumentExtractor.chunk_text(text, chunk_size=500, overlap=50)

        # Chunk & embed into ChromaDB vector store
        if chunks:
            chunk_ids = [f"doc_{unique_name}_chunk_{i}" for i in range(len(chunks))]
            metadatas = [
                {
                    "org_id": current_user.organization_id,
                    "doc_name": file.filename,
                    "doc_id": unique_name,
                    "chunk_index": i,
                }
                for i in range(len(chunks))
            ]

            vector_store.add_documents(
                org_id=current_user.organization_id,
                documents=chunks,
                metadatas=metadatas,
                ids=chunk_ids,
            )

        # Record in database
        doc_entry = BrandDocument(
            organization_id=current_user.organization_id,
            filename=file.filename,
            file_type=ext.lstrip("."),
            file_path=str(save_path),
            document_title=document_title or file.filename,
            chunk_count=len(chunks),
        )
        db.add(doc_entry)
        db.commit()
        db.refresh(doc_entry)

        return BrandDocumentOut.model_validate(doc_entry)
    except Exception as e:
        if save_path.exists():
            save_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process and index document: {e!s}",
        )


@router.get("/documents", response_model=list[BrandDocumentOut])
def list_documents(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    docs = (
        db.query(BrandDocument)
        .filter(BrandDocument.organization_id == current_user.organization_id)
        .all()
    )
    return [BrandDocumentOut.model_validate(d) for d in docs]


@router.get("/facts", response_model=list[BrandFactOut])
def list_brand_facts(
    product_name: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(BrandFact).filter(
        BrandFact.organization_id == current_user.organization_id
    )
    if product_name:
        query = query.filter(BrandFact.product_name.ilike(f"%{product_name}%"))
    facts = query.all()
    return [BrandFactOut.model_validate(f) for f in facts]


@router.post("/facts", response_model=BrandFactOut)
def create_brand_fact(
    fact_in: BrandFactCreate,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    new_fact = BrandFact(
        organization_id=current_user.organization_id,
        product_name=fact_in.product_name,
        category=fact_in.category,
        fact_key=fact_in.fact_key,
        fact_value=fact_in.fact_value,
        source_reference=fact_in.source_reference,
        notes=fact_in.notes,
    )
    db.add(new_fact)
    db.commit()
    db.refresh(new_fact)
    return BrandFactOut.model_validate(new_fact)


@router.delete("/facts/{fact_id}")
def delete_brand_fact(
    fact_id: int,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    fact = (
        db.query(BrandFact)
        .filter(
            BrandFact.id == fact_id,
            BrandFact.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not fact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Brand fact not found"
        )
    db.delete(fact)
    db.commit()
    return {"message": "Brand fact deleted successfully"}
