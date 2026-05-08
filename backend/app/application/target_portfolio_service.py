from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlite.target_position_repository import TargetPositionRepository
from app.domains.target_portfolio.models import TargetPosition
from app.domains.target_portfolio.schemas import (
    TargetPositionCreate,
    TargetPositionRead,
    TargetPositionUpdate,
)


class TargetPortfolioService:
    def __init__(self, repository: TargetPositionRepository | None = None) -> None:
        self.repository = repository or TargetPositionRepository()

    def list_positions(self, db: Session) -> list[TargetPositionRead]:
        return [
            TargetPositionRead.model_validate(position, from_attributes=True)
            for position in self.repository.list(db)
        ]

    def create_position(self, db: Session, payload: TargetPositionCreate) -> TargetPositionRead:
        position = self.repository.create(db, payload)
        return TargetPositionRead.model_validate(position, from_attributes=True)

    def update_position(
        self,
        db: Session,
        position_id: int,
        payload: TargetPositionUpdate,
    ) -> TargetPositionRead | None:
        position = self.repository.get(db, position_id)
        if position is None:
            return None
        updated = self.repository.update(db, position, payload)
        return TargetPositionRead.model_validate(updated, from_attributes=True)

    def delete_position(self, db: Session, position_id: int) -> bool:
        position = self.repository.get(db, position_id)
        if position is None:
            return False
        self.repository.delete(db, position)
        return True

