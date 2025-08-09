from abc import ABC, abstractmethod
from typing import List
from app.models.source_item import SourceItem


class DataSource(ABC):
    @abstractmethod
    async def fetch(self, limit: int = 50) -> List[SourceItem]:
        raise NotImplementedError