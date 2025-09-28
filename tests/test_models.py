from __future__ import annotations

from intellioptics.models import Detector


def test_detector_labels_are_independent() -> None:
    first = Detector(id="det-1", name="First")
    second = Detector(id="det-2", name="Second")

    first.labels.append("alpha")

    assert first.labels is not second.labels
    assert first.labels == ["alpha"]
    assert second.labels == []
