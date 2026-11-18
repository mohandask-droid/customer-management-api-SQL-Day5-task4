import os

# set env BEFORE importing the app
os.environ["API_KEY"] = "test-key"
os.environ["WEBHOOK_SECRET"] = "test-secret"

import hashlib, hmac
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src import database
from src.database import Base, get_db
from src.main import app

TEST_DB_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(bind=test_engine, autoflush=False)


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)   # clean DB after every test


@pytest.fixture()
def client(db_session, monkeypatch):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # background task must also write to the test DB
    monkeypatch.setattr(database, "SessionLocal", TestSession)
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def auth():
    return {"X-API-Key": "test-key"}


@pytest.fixture()
def sign():
    def _sign(body: bytes, secret: str = "test-secret") -> str:
        return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return _sign