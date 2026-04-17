from app.core.types.common import ValuationLabel
from app.domains.state.service import StateService


def test_state_service_detects_label_transition():
    service = StateService()

    first_state, _ = service.evaluate(
        symbol="AAPL",
        current_label=ValuationLabel.FAIR,
        existing_state=None,
    )
    assert first_state.current_label == ValuationLabel.FAIR
    assert first_state.previous_label is None
    assert first_state.has_changed is False

    existing = type(
        "ExistingState",
        (),
        {
            "current_label": ValuationLabel.FAIR,
            "previous_label": None,
            "changed_at": None,
        },
    )()
    next_state, _ = service.evaluate(
        symbol="AAPL",
        current_label=ValuationLabel.OVERVALUED,
        existing_state=existing,
    )
    assert next_state.current_label == ValuationLabel.OVERVALUED
    assert next_state.previous_label == ValuationLabel.FAIR
    assert next_state.has_changed is True
    assert next_state.changed_at is not None

