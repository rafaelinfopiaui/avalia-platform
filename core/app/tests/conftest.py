import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_avalia.db")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("AI_ENGINE_URL", "http://localhost:9999")  # porta inexistente, força falha controlada

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.db import Base
import app.main as main_module
from app import db as db_module
from app.models import User, Role
from app.security import hash_password


@pytest.fixture()
def test_engine(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(test_engine):
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture()
def client(test_engine, monkeypatch):
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    main_module.app.dependency_overrides[db_module.get_db] = override_get_db
    monkeypatch.setattr(main_module, "SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("app.services.correction.SessionLocal", TestingSessionLocal, raising=False)

    with TestClient(main_module.app) as c:
        yield c
    main_module.app.dependency_overrides.clear()


@pytest.fixture()
def professor_token(client, test_engine):
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
    session = TestingSessionLocal()
    user = User(email="professor@example.com", password_hash=hash_password("Senha123!"), role=Role.PROFESSOR)
    session.add(user)
    session.commit()
    session.close()

    resp = client.post("/v1/auth/login", json={"email": "professor@example.com", "password": "Senha123!"})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]
