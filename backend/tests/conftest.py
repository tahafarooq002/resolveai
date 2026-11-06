import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# 1. Use an in-memory SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Patch the global engine/session in your app's database module BEFORE importing app/main
import app.core.database as db_mod
db_mod.engine = engine
db_mod.SessionLocal = TestingSessionLocal

from app.main import app
from app.core.database import Base
from app.core.dependencies import get_db

# 3. Explicitly import all models so Base.metadata recognizes them
from app.models.user import User
from app.models.organization import Organization
from app.models.ticket import SupportTicket, TicketMessage, AIClassification, GeneratedResponse
from app.models.document import KnowledgeDocument

@pytest.fixture(scope="function", autouse=True)
def db_tables():
    # Create all tables in SQLite memory before each test
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables after the test
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_tables):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c