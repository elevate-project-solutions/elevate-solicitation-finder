from datetime import datetime

import pytest

from app.collectors.base import (
    BaseCollector,
    CollectedSolicitation,
    CollectionResult,
)


class FakeCollector(BaseCollector):
    """Test collector that does not make network requests."""

    @property
    def source_name(self) -> str:
        return "test_source"

    def collect(self) -> list[CollectedSolicitation]:
        return [
            CollectedSolicitation(
                source_record_id="TEST-001",
                title="Roof Replacement",
                agency_name="Test Agency",
                solicitation_number="RFP-001",
                status="Posted",
                raw_data={"example": True},
            )
        ]

def test_collected_solicitation_fields():
    solicitation = CollectedSolicitation(
        source_record_id="123",
        title="Concrete Repairs",
    )

    assert solicitation.source_record_id == "123"
    assert solicitation.title == "Concrete Repairs"
    assert solicitation.agency_name is None
    assert solicitation.raw_data == {}

def test_collected_soliciation_raw_data_is_independent ():
    first = CollectedSolicitation(
        source_record_id="1",
        title="First",
    )

    second = CollectedSolicitation(
        source_record_id="2",
        title="Second",
    )

    first.raw_data["example"] = True

    assert second.raw_data == {}

def test_collector_cannot_be_instantiated_directly():
    with pytest.raises(TypeError):
        BaseCollector()

def test_collector_requires_implementation():
    class IncompleteCollector(BaseCollector):
        pass

    with pytest.raises(TypeError):
        IncompleteCollector()

def test_collector_returns_standardized_results():
    collector = FakeCollector()

    result = collector.run()

    assert isinstance(result, CollectionResult)
    assert result.source_name == "test_source"
    assert result.total_collected == 1
    assert len(result.solicitations) == 1
    assert isinstance(result.collected_at, datetime)

def test_collector_preserves_solicitation_data():
    collector = FakeCollector()

    result = collector.run()
    solicitation = result.solicitations[0]

    assert solicitation.source_record_id == "TEST-001"
    assert solicitation.title == "Roof Replacement"
    assert solicitation.agency_name == "Test Agency"
    assert solicitation.solicitation_number == "RFP-001"
    assert solicitation.status == "Posted"
    assert solicitation.raw_data == {"example": True}

def test_collector_supports_empty_results():
    class EmptyCollector(BaseCollector):

        @property
        def source_name(self) -> str:
            return "empty_source"

        def collect(self) -> list[CollectedSolicitation]:
            return []

    result = EmptyCollector().run()

    assert result.source_name == "empty_source"
    assert result.total_collected == 0
    assert result.solicitations == []

def test_collector_rejects_invalid_result_type():
    class InvalidCollector(BaseCollector):

        @property
        def source_name(self) -> str:
            return "invalid_source"

        def collect(self) -> list[CollectedSolicitation]:
            return "not a list"

    with pytest.raises(TypeError):
        InvalidCollector().run()

def test_collector_rejects_invalid_records():
    class InvalidRecordCollector(BaseCollector):

        @property
        def source_name(self) -> str:
            return "invalid_records"

        def collect(self) -> list[CollectedSolicitation]:
            return [{"title": "Invalid Record"}]

    with pytest.raises(TypeError):
        InvalidRecordCollector().run()