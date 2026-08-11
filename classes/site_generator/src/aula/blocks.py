"""Turning an activity or lesson body into something structured.

Two passes, described in sections 4 and 6.1 of the spec:

``split_containers``
    Pulls out ``::: de`` / ``::: modelo`` fenced sections, keeping the Markdown
    inside them untouched. Used for prose (lesson bodies, ``nota``, ``libre``).

``parse_blocks``
    Groups the remaining lines into runs of paragraphs, lists, quotes and
    headings. Blank lines separate runs but are otherwise insignificant, so the
    author can space things out or not. Used for the structured activity types.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .errors import Report

CONTAINER_FENCE = re.compile(r"^:::\s*(\S*)\s*$")
_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_ITEM = re.compile(r"^[-*]\s+(.*)$")
_QUOTE = re.compile(r"^>\s?(.*)$")

#: Container labels the format knows about. Anything else is a typo.
KNOWN_LABELS = {"de", "modelo"}


@dataclass(frozen=True)
class Segment:
    """A stretch of body text, either plain or inside a ``::: label`` container."""

    label: str  # "" for plain prose
    text: str
    line: int  # 1-based line of the first text line


@dataclass(frozen=True)
class Block:
    kind: str  # paragraph | list | quote | heading
    lines: list[str]  # content, with list/quote/heading markers stripped
    line: int  # 1-based line of the first line

    def line_of(self, index: int) -> int:
        return self.line + index


def split_containers(body: str, first_line: int, path: Path, report: Report) -> list[Segment]:
    """Split a body into plain stretches and ``:::`` containers. Containers do not nest."""
    segments: list[Segment] = []
    buffer: list[str] = []
    buffer_line = first_line
    label = ""
    open_line: int | None = None

    def flush(at_line: int) -> None:
        nonlocal buffer, buffer_line
        # Skip leading blank lines so the recorded line number is the first real one.
        lead = 0
        while lead < len(buffer) and not buffer[lead].strip():
            lead += 1
        if lead < len(buffer):
            segments.append(Segment(label, "\n".join(buffer[lead:]).rstrip(), buffer_line + lead))
        buffer = []
        buffer_line = at_line

    for offset, line in enumerate(body.splitlines()):
        number = first_line + offset
        match = CONTAINER_FENCE.match(line.strip())
        if not match:
            buffer.append(line)
            continue

        fence_label = match.group(1)
        if open_line is None:
            if not fence_label:
                report.error(
                    path,
                    "this ::: closes a block that was never opened",
                    line=number,
                    hint="to open one write ::: de and close it with :::",
                )
                continue
            if fence_label not in KNOWN_LABELS:
                report.error(
                    path,
                    f'"::: {fence_label}" is not a kind of block the site knows',
                    line=number,
                    hint="allowed: " + ", ".join(f"::: {name}" for name in sorted(KNOWN_LABELS)),
                )
            flush(number + 1)
            label = fence_label
            open_line = number
        else:
            if fence_label:
                report.error(
                    path,
                    f'"::: {fence_label}" starts inside another ::: block',
                    line=number,
                    hint=f"close the block opened on line {open_line} first, with :::",
                )
                continue
            flush(number + 1)
            label = ""
            open_line = None

    if open_line is not None:
        report.error(
            path,
            "this ::: block is never closed",
            line=open_line,
            hint="add a line containing only ::: where it should end",
        )
    flush(first_line)
    return segments


def parse_blocks(text: str, first_line: int) -> list[Block]:
    """Group lines into runs of the same kind."""
    blocks: list[Block] = []
    kind = ""
    lines: list[str] = []
    start = first_line

    def flush() -> None:
        nonlocal kind, lines
        if lines:
            blocks.append(Block(kind, lines, start))
        kind, lines = "", []

    for offset, raw in enumerate(text.splitlines()):
        number = first_line + offset
        if not raw.strip():
            flush()
            continue

        stripped = raw.strip()
        if match := _HEADING.match(stripped):
            this_kind, content = "heading", match.group(2).strip()
        elif match := _LIST_ITEM.match(stripped):
            this_kind, content = "list", match.group(1).strip()
        elif match := _QUOTE.match(stripped):
            this_kind, content = "quote", match.group(1).strip()
        else:
            this_kind, content = "paragraph", stripped

        # Headings are always their own block, so two in a row do not merge.
        if this_kind != kind or this_kind == "heading":
            flush()
            kind, start = this_kind, number
        lines.append(content)

    flush()
    return blocks


def unescape(text: str) -> str:
    r"""Turn ``\{`` into ``{`` and so on, for the characters the syntax reserves."""
    return re.sub(r"\\([{}\[\]=|])", r"\1", text)


def split_pair(text: str) -> tuple[str, str] | None:
    """Split ``izquierda = derecha`` on the first unescaped ``' = '``."""
    start = 0
    while (found := text.find(" = ", start)) != -1:
        if found > 0 and text[found - 1] == "\\":
            start = found + 1
            continue
        return unescape(text[:found]).strip(), unescape(text[found + 3 :]).strip()
    return None
