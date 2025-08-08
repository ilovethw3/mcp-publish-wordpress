from sqlmodel import Session, create_engine, SQLModel
from mcp.core.config import settings

engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session