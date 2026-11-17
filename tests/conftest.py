import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.deps import get_db
from backend.database.session import Base

# Ensure offline environment for tests
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

# Use SQLite with StaticPool so in-memory connection is shared across all calls in test process
test_engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def isolate_test_environment():
    """Isolate tests from external networks, cloud LLMs, and heavy ML downloads."""
    from backend.core.config import settings

    orig_gemini_key = settings.GEMINI_API_KEY
    settings.GEMINI_API_KEY = ""

    from ai_engine.embeddings.vector_store import vector_store

    orig_emb_avail = vector_store._embedding_available
    vector_store._embedding_available = False

    yield

    settings.GEMINI_API_KEY = orig_gemini_key
    vector_store._embedding_available = orig_emb_avail


@pytest.fixture(scope="session")
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    # Temporarily bind test_engine for init_db
    import backend.database.init_db as idb

    orig_engine = idb.engine
    orig_session = idb.SessionLocal
    idb.engine = test_engine
    idb.SessionLocal = TestingSessionLocal
    idb.init_db()
    yield
    idb.engine = orig_engine
    idb.SessionLocal = orig_session


@pytest.fixture
def db_session(setup_test_db):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(setup_test_db):
    from backend.main import app

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
