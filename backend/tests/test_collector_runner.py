from unittest.mock import Mock

import pytest

from app.collectors.base import CollectionResult
from app.services.collector_runner import run_collector


def test_runner_returns_collection_result():
    collector = Mock()
    collector.source_name = "test_source"

    expected = CollectionResult(
        source_name="test_source",
        solicitations=[],
        collected_at=__import__("datetime").datetime.now(),
    )

    collector.run.return_value = expected

    result = run_collector(collector)

    assert result is expected
    collector.run.assert_called_once()

def test_runner_propagates_errors():
    collector = Mock()
    collector.source_name = "test_source"
    collector.run.side_effect = RuntimeError("Collector failed")

    with pytest.raises(RuntimeError, match="Collector failed"):
        run_collector(collector)