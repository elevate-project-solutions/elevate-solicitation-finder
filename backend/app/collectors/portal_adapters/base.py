"""Common interface for procurement portal adapters"""

from abc import ABC, abstractmethod

from app.collectors.portal_adapters.models import (
    PortalInspection
)

class PortalAdapter(ABC):

    provider: str

    @abstractmethod
    def inspect(
        self,
        url: str,
        solicitation_number: str | None,
        solicitation_title: str | None,
    ) -> PortalInspection:
        """Inspects a procurement opportunity"""
        raise NotImplementedError