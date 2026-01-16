import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
import database_model


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # 👈 FILE, not memory

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    database_model.Base.metadata.create_all(bind=engine)
    yield
    database_model.Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db
