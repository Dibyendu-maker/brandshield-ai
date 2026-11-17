from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user, get_db
from backend.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from backend.database.models import Organization, User
from backend.schemas.auth import TokenResponse, UserLogin, UserOut, UserRegister

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )

    token = create_access_token(
        {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id,
        }
    )
    return TokenResponse(
        access_token=token, token_type="bearer", user=UserOut.model_validate(user)
    )


@router.post("/oauth-login", response_model=TokenResponse)
def oauth_login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    # OAuth2 standard form compatible endpoint
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token(
        {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id,
        }
    )
    return TokenResponse(
        access_token=token, token_type="bearer", user=UserOut.model_validate(user)
    )


@router.post("/register", response_model=UserOut)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Resolve organization
    org = None
    if user_in.organization_slug:
        org = (
            db.query(Organization)
            .filter(Organization.slug == user_in.organization_slug)
            .first()
        )
    if not org:
        org = db.query(Organization).first()
    if not org:
        org = Organization(name="Default Organization", slug="default")
        db.add(org)
        db.commit()
        db.refresh(org)

    new_user = User(
        organization_id=org.id,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role
        if user_in.role in ["admin", "creator", "reviewer"]
        else "creator",
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserOut.model_validate(new_user)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.get("/users", response_model=list[UserOut])
def list_org_users(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    # Tenant isolation: only return users from current organization
    users = (
        db.query(User)
        .filter(User.organization_id == current_user.organization_id)
        .all()
    )
    return [UserOut.model_validate(u) for u in users]
