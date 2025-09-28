from intellioptics.models import (
    Condition,
    Detector,
    ImageQuery,
    ModeEnum,
    Rule,
    SnoozeTimeUnitEnum,
)


def test_detector_accepts_metadata() -> None:
    detector = Detector(
        id="det-1",
        name="Camera",
        query="Is the light on?",
        mode=ModeEnum.BINARY,
        metadata={"team": "qa"},
    )

    assert detector.metadata == {"team": "qa"}


def test_detector_defaults_match_documentation() -> None:
    detector = Detector(
        id="det-2",
        name="Door Monitor",
        query="Is the door open?",
        mode=ModeEnum.BINARY,
        group_name="default",
    )

    assert detector.confidence_threshold == 0.9
    assert detector.patience_time == 30.0


def test_image_query_defaults_match_documentation() -> None:
    query = ImageQuery(id="iq-1")

    assert query.confidence_threshold == 0.9
    assert query.patience_time == 30.0
    assert query.done_processing is False


def test_rule_defaults_match_documentation() -> None:
    condition = Condition(verb="CHANGED_TO", parameters={"label": "YES"})
    rule = Rule(
        id=1,
        detector_id="det-1",
        detector_name="Door Detector",
        name="Door Alert",
        condition=condition,
    )

    assert rule.snooze_time_unit == SnoozeTimeUnitEnum.DAYS
    assert rule.snooze_time_value == 0
