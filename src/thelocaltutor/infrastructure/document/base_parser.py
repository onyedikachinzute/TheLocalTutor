"""Abstract base for document parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ParsedPage:
    page_number: int
    text: str


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: str) -> list[ParsedPage]:
        """Return pages with extracted text from the document."""

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """Return True if this parser can handle the given file."""
