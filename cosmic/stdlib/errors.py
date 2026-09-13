"""Cosmic Standard Library — errors module."""
from __future__ import annotations
import traceback
from typing import Any


class CosmicError(Exception):
    """Base class for all Cosmic runtime errors."""
    def __init__(self, message: str = '', line: int = 0, column: int = 0, filename: str = ''):
        self.line = line
        self.column = column
        self.filename = filename
        super().__init__(message)

    def __str__(self) -> str:
        msg = super().__str__()
        if self.filename and self.line:
            return f"{self.filename}:{self.line}:{self.column}: {type(self).__name__}: {msg}"
        if self.line:
            return f"Line {self.line}, Column {self.column}: {type(self).__name__}: {msg}"
        return f"{type(self).__name__}: {msg}"

    def format_traceback(self) -> str:
        return traceback.format_exc() or str(self)


class TypeError_(CosmicError):
    """Raised when a value has the wrong type."""
    def __init__(self, message: str = '', expected: str = '', got: str = '', **kwargs: Any):
        if expected and got:
            message = f"Expected {expected}, got {got}"
        super().__init__(message, **kwargs)


class ValueError_(CosmicError):
    """Raised when a value is invalid."""
    pass


class IndexError_(CosmicError):
    """Raised when an index is out of range."""
    def __init__(self, message: str = '', index: int = 0, size: int = 0, **kwargs: Any):
        if not message and size:
            message = f"Index {index} out of range (size: {size})"
        super().__init__(message, **kwargs)


class KeyError_(CosmicError):
    """Raised when a dictionary key is not found."""
    def __init__(self, message: str = '', key: Any = None, **kwargs: Any):
        if not message and key is not None:
            message = f"Key not found: {key!r}"
        super().__init__(message, **kwargs)


class FileNotFoundError_(CosmicError):
    """Raised when a file cannot be found."""
    def __init__(self, message: str = '', path: str = '', **kwargs: Any):
        if not message and path:
            message = f"File not found: {path}"
        super().__init__(message, **kwargs)


class PermissionError_(CosmicError):
    """Raised when a permission check fails."""
    def __init__(self, message: str = '', path: str = '', **kwargs: Any):
        if not message and path:
            message = f"Permission denied: {path}"
        super().__init__(message, **kwargs)


class TimeoutError_(CosmicError):
    """Raised when an operation times out."""
    def __init__(self, message: str = '', timeout: float = 0, **kwargs: Any):
        if not message and timeout:
            message = f"Operation timed out after {timeout}s"
        super().__init__(message, **kwargs)


class NotImplementedError_(CosmicError):
    """Raised when a feature is not yet implemented."""
    def __init__(self, message: str = '', feature: str = '', **kwargs: Any):
        if not message and feature:
            message = f"Not implemented: {feature}"
        super().__init__(message, **kwargs)


class AssertionError_(CosmicError):
    """Raised when an assertion fails."""
    pass


class ImportError_(CosmicError):
    """Raised when a module cannot be imported."""
    def __init__(self, message: str = '', module: str = '', **kwargs: Any):
        if not message and module:
            message = f"Cannot import module: {module}"
        super().__init__(message, **kwargs)


class RecursionError_(CosmicError):
    """Raised when the recursion limit is exceeded."""
    def __init__(self, message: str = '', limit: int = 0, **kwargs: Any):
        if not message and limit:
            message = f"Maximum recursion depth exceeded (limit: {limit})"
        super().__init__(message, **kwargs)


class OverflowError_(CosmicError):
    """Raised when a numeric value overflows."""
    pass


class DivisionByZeroError(CosmicError):
    """Raised when dividing by zero."""
    def __init__(self, message: str = '', **kwargs: Any):
        if not message:
            message = "Division by zero"
        super().__init__(message, **kwargs)


class NullReferenceError(CosmicError):
    """Raised when accessing a property or method on null."""
    def __init__(self, message: str = '', variable: str = '', **kwargs: Any):
        if not message and variable:
            message = f"Null reference: {variable}"
        elif not message:
            message = "Null reference"
        super().__init__(message, **kwargs)


class MatchError(CosmicError):
    """Raised when no match case handles the value."""
    def __init__(self, message: str = '', **kwargs: Any):
        if not message:
            message = "No matching case in match expression"
        super().__init__(message, **kwargs)


class InternalError(CosmicError):
    """Raised on internal compiler errors."""
    def __init__(self, message: str = '', **kwargs: Any):
        super().__init__(message or "Internal compiler error", **kwargs)


def format_error(error: Exception) -> str:
    if isinstance(error, CosmicError):
        return str(error)
    return f"{type(error).__name__}: {error}"


def format_error_with_traceback(error: Exception) -> str:
    if isinstance(error, CosmicError):
        tb = error.format_traceback()
        return f"{tb}\n{error}" if tb else str(error)
    return traceback.format_exc() or f"{type(error).__name__}: {error}"
