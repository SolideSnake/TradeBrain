from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domains.target_portfolio.errors import DuplicateTargetPositionSymbolError
from app.domains.target_portfolio.models import TargetPosition
from app.domains.target_portfolio.schemas import TargetPositionCreate, TargetPositionUpdate


class TargetPositionRepository:
    def list(self, db: Session) -> list[TargetPosition]:
        query = select(TargetPosition).order_by(
            TargetPosition.target_value_usd.desc(),
            TargetPosition.symbol.asc(),
        )
        return list(db.scalars(query))

    def get(self, db: Session, position_id: int) -> TargetPosition | None:
        return db.get(TargetPosition, position_id)

    def create(self, db: Session, payload: TargetPositionCreate) -> TargetPosition:
        position = TargetPosition(**payload.model_dump())
        db.add(position)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise DuplicateTargetPositionSymbolError(payload.symbol) from exc
        db.refresh(position)
        return position

    def update(
        self,
        db: Session,
        position: TargetPosition,
        payload: TargetPositionUpdate,
    ) -> TargetPosition:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(position, field, value)
        db.add(position)
        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            raise DuplicateTargetPositionSymbolError(payload.symbol or position.symbol) from exc
        db.refresh(position)
        return position

    def delete(self, db: Session, position: TargetPosition) -> None:
        db.delete(position)
        db.commit()

