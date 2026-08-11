"""Splitting a content file into TOML front matter and body.

Every ``.md`` file under ``content/`` is::

    +++
    titulo = "..."
    +++

    body

See section 3 of the content format spec.
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from .errors import Report

FENCE = "+++"

# tomllib does not expose the position on every supported version, but its message
# reliably ends with "(at line 3, column 5)" or "(at end of document)".
_TOML_POSITION = re.compile(r"\(at line (\d+), column \d+\)\s*$")


@dataclass(frozen=True)
class ParsedFile:
    path: Path
    meta: dict
    body: str
    #: 1-based line number in the file of the first body line, for error messages.
    body_line: int


def parse_file(path: Path, report: Report) -> ParsedFile | None:
    """Read and split a content file. Returns ``None`` if it cannot be used at all."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        report.error(path, "this file is not valid UTF-8 text", hint="save it with UTF-8 encoding")
        return None
    except OSError as exc:
        report.error(path, f"cannot read this file: {exc.strerror or exc}")
        return None

    if text.startswith("﻿"):
        report.error(
            path,
            "the file starts with a byte order mark",
            line=1,
            hint="save it as UTF-8 without BOM",
        )
        text = text.lstrip("﻿")

    lines = text.splitlines()
    if not lines:
        report.error(path, "the file is empty", hint=f"it must start with a {FENCE} block")
        return None

    if lines[0].strip() != FENCE:
        report.error(
            path,
            f"the file must start with a line containing only {FENCE}",
            line=1,
            hint=f"add {FENCE} as the very first line, then the metadata, then {FENCE} again",
        )
        return None

    closing = next((i for i, line in enumerate(lines[1:], start=1) if line.strip() == FENCE), None)
    if closing is None:
        report.error(
            path,
            f"the {FENCE} block is never closed",
            line=1,
            hint=f"add a line containing only {FENCE} after the metadata",
        )
        return None

    meta_text = "\n".join(lines[1:closing])
    try:
        meta = tomllib.loads(meta_text)
    except tomllib.TOMLDecodeError as exc:
        message = str(exc)
        match = _TOML_POSITION.search(message)
        # +1 because the metadata starts on the line after the opening fence.
        line = int(match.group(1)) + 1 if match else 1
        report.error(
            path,
            f"the metadata is not valid TOML: {_TOML_POSITION.sub('', message).strip()}",
            line=line,
            hint='every value needs quotes around text, as in titulo = "La casa"',
        )
        return None

    body = "\n".join(lines[closing + 1 :])
    return ParsedFile(path=path, meta=meta, body=body, body_line=closing + 2)


def check_keys(
    parsed: ParsedFile,
    report: Report,
    *,
    required: set[str],
    optional: set[str],
) -> None:
    """Reject unknown keys, so that ``titolo`` fails loudly instead of vanishing."""
    known = required | optional
    for key in sorted(parsed.meta):
        if key in known:
            continue
        suggestion = _closest(key, known)
        report.error(
            parsed.path,
            f'unknown setting "{key}"',
            line=_meta_line(parsed, key),
            hint=(
                f'did you mean "{suggestion}"?'
                if suggestion
                else "allowed settings here: " + ", ".join(sorted(known))
            ),
        )

    for key in sorted(required - set(parsed.meta)):
        report.error(parsed.path, f'the setting "{key}" is required but missing', line=1)

    # A German variant with no Spanish original is always a mistake.
    for key in sorted(parsed.meta):
        if key.endswith("_de") and key[: -len("_de")] not in parsed.meta:
            base = key[: -len("_de")]
            report.error(
                parsed.path,
                f'"{key}" has no "{base}" next to it',
                line=_meta_line(parsed, key),
                hint=f'add "{base}" with the Spanish version, or remove "{key}"',
            )


def check_choice(
    parsed: ParsedFile, report: Report, key: str, allowed: set[str], default: str | None = None
) -> str | None:
    """Validate a key whose value must come from a fixed set."""
    value = parsed.meta.get(key, default)
    if value is None:
        return None
    if not isinstance(value, str) or value not in allowed:
        report.error(
            parsed.path,
            f'"{key}" is set to {value!r}, which is not one of the allowed values',
            line=_meta_line(parsed, key),
            hint="allowed: " + ", ".join(sorted(allowed)),
        )
        return default
    return value


def check_types(parsed: ParsedFile, report: Report, expected: dict[str, type]) -> None:
    """Validate the Python type of each present key."""
    names = {str: "text in quotes", bool: "true or false", list: "a list", int: "a number"}
    for key, kind in expected.items():
        if key not in parsed.meta:
            continue
        value = parsed.meta[key]
        # bool is a subclass of int; keep them distinct.
        if isinstance(value, kind) and not (kind is int and isinstance(value, bool)):
            if kind is list and not all(isinstance(item, str) for item in value):
                report.error(
                    parsed.path,
                    f'"{key}" must be a list of text values',
                    line=_meta_line(parsed, key),
                    hint=f'for example: {key} = ["casa", "localizacion"]',
                )
            continue
        report.error(
            parsed.path,
            f'"{key}" must be {names.get(kind, kind.__name__)}',
            line=_meta_line(parsed, key),
        )


def _meta_line(parsed: ParsedFile, key: str) -> int:
    """Best-effort line number of a key inside the front matter."""
    try:
        lines = parsed.path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return 1
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
    for number, line in enumerate(lines[: parsed.body_line], start=1):
        if pattern.match(line):
            return number
    return 1


def _closest(word: str, candidates: set[str]) -> str | None:
    """A typo suggestion, but only when it is close enough to be helpful."""
    import difflib

    matches = difflib.get_close_matches(word, sorted(candidates), n=1, cutoff=0.7)
    return matches[0] if matches else None
