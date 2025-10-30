from fastapi import Depends
from sqlalchemy.orm import Session

from ..application.services import ApplicationService
from ..infrastructure.database import SessionLocal
from ..infrastructure.repositories.sql_genealogy_repository import (
    SQLGenealogyRepository,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_app_service(db: Session = Depends(get_db)) -> ApplicationService:
    repo = SQLGenealogyRepository(db)
    return ApplicationService(repo)
