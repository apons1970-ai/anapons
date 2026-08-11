"""Problems found in the content, and how they are shown to the author.

Every message names a file and, where possible, a line, and says what to do about
it. The author edits content on github.com and is not a programmer, so the wording
matters as much as the detection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class Problem:
    """One thing wrong with one file."""

    path: Path
    message: str
    line: int | None = None
    hint: str | None = None
    severity: Severity = "error"


@dataclass
class Report:
    """Collects problems during a load and formats them."""

    root: Path
    problems: list[Problem] = field(default_factory=list)

    def error(self, path: Path, message: str, line: int | None = None, hint: str | None = None):
        self.problems.append(Problem(path, message, line, hint, "error"))

    def warning(self, path: Path, message: str, line: int | None = None, hint: str | None = None):
        self.problems.append(Problem(path, message, line, hint, "warning"))

    def has_errors(self, strict: bool = False) -> bool:
        if strict:
            return bool(self.problems)
        return any(p.severity == "error" for p in self.problems)

    def _display_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def _sorted(self) -> list[Problem]:
        return sorted(self.problems, key=lambda p: (str(p.path), p.line or 0))

    def format_human(self, strict: bool = False) -> str:
        lines: list[str] = []
        for problem in self._sorted():
            where = self._display_path(problem.path)
            if problem.line is not None:
                where += f":{problem.line}"
            severity = "error" if strict else problem.severity
            lines.append(where)
            lines.append(f"  {severity}: {problem.message}")
            if problem.hint:
                for hint_line in problem.hint.splitlines():
                    lines.append(f"  {hint_line}")
            lines.append("")
        errors = sum(1 for p in self.problems if p.severity == "error")
        warnings = len(self.problems) - errors
        if self.problems:
            lines.append(f"{errors} error(s), {warnings} warning(s)")
        return "\n".join(lines)

    def format_github(self, strict: bool = False) -> str:
        """GitHub Actions annotations, so messages land on the line in the diff view."""
        lines: list[str] = []
        for problem in self._sorted():
            level = "error" if strict or problem.severity == "error" else "warning"
            location = f"file={self._display_path(problem.path)}"
            if problem.line is not None:
                location += f",line={problem.line}"
            body = problem.message
            if problem.hint:
                body += "\n" + problem.hint
            # Annotation payloads are single-line; newlines must be percent-encoded.
            body = body.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
            lines.append(f"::{level} {location}::{body}")
        return "\n".join(lines)
