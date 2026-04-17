from app.core.types.common import ValuationLabel
from app.domains.valuation.service import ValuationService


def test_valuation_service_maps_peg_thresholds():
    service = ValuationService()

    assert service.label_from_peg(0.79) == ValuationLabel.UNDERVALUED
    assert service.label_from_peg(1.0) == ValuationLabel.FAIR
    assert service.label_from_peg(1.51) == ValuationLabel.OVERVALUED
    assert service.label_from_peg(None) is None

