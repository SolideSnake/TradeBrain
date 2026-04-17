from __future__ import annotations

from app.core.types.common import ValuationLabel


class ValuationService:
    def __init__(
        self,
        undervalued_threshold: float = 0.8,
        overvalued_threshold: float = 1.5,
    ) -> None:
        self.undervalued_threshold = undervalued_threshold
        self.overvalued_threshold = overvalued_threshold

    def label_from_peg(self, peg_ratio: float | None) -> ValuationLabel | None:
        if peg_ratio is None or peg_ratio <= 0:
            return None
        if peg_ratio < self.undervalued_threshold:
            return ValuationLabel.UNDERVALUED
        if peg_ratio > self.overvalued_threshold:
            return ValuationLabel.OVERVALUED
        return ValuationLabel.FAIR
