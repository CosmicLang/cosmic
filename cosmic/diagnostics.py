"""Structured diagnostic system for the Cosmic compiler.

Modeled after Kof4j's Diagnostic.java + DiagnosticCollector.java.
Every compiler error/warning carries a severity, location, message, and code.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"
    INFO = "info"


@dataclass(frozen=True)
class Diagnostic:
    severity: Severity
    file: str
    line: int
    column: int
    length: int
    message: str
    code: str

    def format(self) -> str:
        loc = f"{self.file}:{self.line}:{self.column}" if self.file else f"{self.line}:{self.column}"
        code_suffix = f" [{self.code}]" if self.code else ""
        return f"{loc}: {self.severity.value}: {self.message}{code_suffix}"

    @staticmethod
    def error(file: str, line: int, column: int, length: int, message: str, code: str) -> Diagnostic:
        return Diagnostic(Severity.ERROR, file, line, column, length, message, code)

    @staticmethod
    def warning(file: str, line: int, column: int, length: int, message: str, code: str) -> Diagnostic:
        return Diagnostic(Severity.WARNING, file, line, column, length, message, code)

    @staticmethod
    def note(file: str, line: int, column: int, length: int, message: str, code: str) -> Diagnostic:
        return Diagnostic(Severity.NOTE, file, line, column, length, message, code)

    @staticmethod
    def info(file: str, line: int, column: int, length: int, message: str, code: str) -> Diagnostic:
        return Diagnostic(Severity.INFO, file, line, column, length, message, code)


@dataclass
class DiagnosticCollector:
    _diagnostics: list[Diagnostic] = field(default_factory=list)

    def report(self, d: Diagnostic) -> None:
        self._diagnostics.append(d)

    def error(self, file: str, line: int, column: int, length: int, message: str, code: str) -> None:
        self.report(Diagnostic.error(file, line, column, length, message, code))

    def warning(self, file: str, line: int, column: int, length: int, message: str, code: str) -> None:
        self.report(Diagnostic.warning(file, line, column, length, message, code))

    def note(self, file: str, line: int, column: int, length: int, message: str, code: str) -> None:
        self.report(Diagnostic.note(file, line, column, length, message, code))

    def info(self, file: str, line: int, column: int, length: int, message: str, code: str) -> None:
        self.report(Diagnostic.info(file, line, column, length, message, code))

    @property
    def diagnostics(self) -> list[Diagnostic]:
        return list(self._diagnostics)

    def has_errors(self) -> bool:
        return any(d.severity == Severity.ERROR for d in self._diagnostics)

    def error_count(self) -> int:
        return sum(1 for d in self._diagnostics if d.severity == Severity.ERROR)

    def warning_count(self) -> int:
        return sum(1 for d in self._diagnostics if d.severity == Severity.WARNING)

    def format_all(self) -> str:
        return "\n".join(d.format() for d in self._diagnostics)

    def clear(self) -> None:
        self._diagnostics.clear()
