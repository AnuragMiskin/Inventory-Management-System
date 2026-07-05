import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure repo root is on sys.path so `import main` works when running `pytest`
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import main as app_module
import models as models_module
from database import get_db


@pytest.fixture(scope="session")
def sqlite_database_url(tmp_path_factory):
    # file-based sqlite to avoid cross-thread issues
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    return f"sqlite:///{db_path}"


@pytest.fixture(scope="session")
def engine(sqlite_database_url):
    engine = create_engine(sqlite_database_url, connect_args={"check_same_thread": False})
    models_module.Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def db_session(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        # clean between tests
        db.query(models_module.Product).delete()
        db.commit()
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session, engine):
    # The app's endpoints depend on `get_db_checked`, which first calls `db_is_up()`
    # using the *real* DATABASE engine. In tests we must bypass that check.
    def override_get_db_checked():
        return db_session

    # Also override `get_db` just in case anything falls through to it.
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app_module.app.dependency_overrides[app_module.get_db_checked] = override_get_db_checked
    app_module.app.dependency_overrides[get_db] = override_get_db

    return TestClient(app_module.app)
