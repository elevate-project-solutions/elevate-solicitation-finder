from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CollectedSolicitation:
    """
    Standardized representation of a solicitation retrieved 
    from an external procurement source.
    """

    source_record_id: str
    title: str

    agency_name: str | None = None
    solicitation_number: str | None = None
    source_url: str | None = None 
    due_at: datetime | None = None
    status: str | None = None

    raw_data: dict[str, Any] = field(default_factory=dict)

@dataclass
class CollectionResult:
    """
    Standardized result returned by a collectors.
    
    Contains the source identifier, collected records, 
    and the time the collection completed.
    """

    source_name: str
    solicitations: list[CollectedSolicitation]
    collected_at: datetime

    @property
    def total_collected(self) -> int:
        """Number of solicitation records collected."""
        return len(self.solicitations)

class BaseCollector(ABC):
    """
    Abstract base class for all procurement collectors.
    
    Every collector must provide:
    - A stable source name.
    - A collect() method returning solicitation records.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Returns the collector's unique source identifier."""
        raise NotImplementedError

    @abstractmethod
    def collect(self) -> list[CollectedSolicitation]:
        """
        Retrieves solicitations from the external source.
        
        Each returned record must be a CollectedSolicitation instance.
        """
        raise NotImplementedError

    def run(self) -> CollectionResult:
        """
        Executes the collector and package its results 
        into a standardized CollectionResult.
        """
        solicitations = self.collect()

        if not isinstance(solicitations, list):
            raise TypeError(
                "Collector collect() must return a list."
            )

        for solicitation in solicitations:
            if not isinstance(
                solicitation, CollectedSolicitation
            ):
                raise TypeError(
                    "Collector returned an invalid solicitation record."
                )

        return CollectionResult(
            source_name=self.source_name,
            solicitations=solicitations,
            collected_at=datetime.now().astimezone(),
        )