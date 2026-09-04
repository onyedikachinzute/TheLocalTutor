"""Application-specific exceptions."""


class TutorError(Exception):
    """Base exception for all application errors."""


class DocumentProcessingError(TutorError):
    """Raised when a document cannot be parsed or processed."""


class UnsupportedFormatError(DocumentProcessingError):
    """Raised for file formats not supported by any parser."""


class AIServiceError(TutorError):
    """Raised when the AI provider cannot fulfil a request."""


class AIConnectionError(AIServiceError):
    """Raised when the AI service (Ollama) is unreachable."""


class AIParseError(AIServiceError):
    """Raised when the AI response cannot be parsed into questions."""


class DatabaseError(TutorError):
    """Raised on unrecoverable database errors."""


class ValidationError(TutorError):
    """Raised when data fails domain validation."""
