"""Parsers for the seven activity types.

The set is closed (spec section 6): adding a type means editing the spec, adding a
parser here, and adding a renderer and a checker. Content can never invent one.

Each parser takes the body of an activity file and returns a plain dict, ready to
hand to a template or serialise as JSON. Anything wrong goes to the report with a
line number; a parser always returns something, so one broken activity does not
stop the rest of the build.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .blocks import Block, Segment, parse_blocks, split_containers, split_pair, unescape
from .errors import Report

ACTIVITY_TYPES = ("vocabulario", "opcion", "huecos", "pareja", "orden", "libre", "nota")

#: Types whose bodies are prose, parsed as language segments rather than blocks.
PROSE_TYPES = frozenset({"libre", "nota"})

#: Per type, whether options/items are shuffled unless the author says otherwise.
SHUFFLE_BY_DEFAULT = {"opcion": True, "pareja": True, "orden": True}

_OPTION = re.compile(r"^\[([ xX])\]\s*(.*)$")


@dataclass
class Body:
    """The parsed body of one activity."""

    items: list[dict]
    #: Prose segments, for the types whose body is Markdown.
    prose: list[Segment]


def parse_body(tipo: str, body: str, first_line: int, path: Path, report: Report) -> Body:
    segments = split_containers(body, first_line, path, report)

    if tipo in PROSE_TYPES:
        return _PROSE_PARSERS[tipo](segments, path, report)

    # Structured types are line-oriented; a ::: container in one is a mistake.
    for segment in segments:
        if segment.label:
            report.error(
                path,
                f'a "::: {segment.label}" block cannot be used in a "{tipo}" activity',
                line=segment.line,
                hint=f"only libre and nota activities use ::: blocks; this one is {tipo}",
            )
    text = "\n\n".join(segment.text for segment in segments if not segment.label)
    start = next((segment.line for segment in segments if not segment.label), first_line)
    blocks = parse_blocks(text, start) if segments else []
    return Body(items=_STRUCTURED_PARSERS[tipo](blocks, path, report), prose=[])


# --------------------------------------------------------------------------- opcion


def _parse_opcion(blocks: list[Block], path: Path, report: Report) -> list[dict]:
    """Paragraph = the question, ``- [ ]`` list = the options, ``>`` = the help."""
    questions: list[dict] = []
    for block in blocks:
        if block.kind == "paragraph":
            for index, line in enumerate(block.lines):
                questions.append(
                    {"pregunta": line, "opciones": [], "ayuda": "", "linea": block.line_of(index)}
                )
        elif block.kind == "list":
            if not questions:
                report.error(
                    path,
                    "these options do not belong to any question",
                    line=block.line,
                    hint="write the question on a line above the options",
                )
                continue
            for index, line in enumerate(block.lines):
                match = _OPTION.match(line)
                if not match:
                    report.error(
                        path,
                        "every option must start with [ ] or [x]",
                        line=block.line_of(index),
                        hint=f"write it as:\n      - [ ] {line}",
                    )
                    continue
                questions[-1]["opciones"].append(
                    {"texto": unescape(match.group(2)).strip(), "correcta": match.group(1) != " "}
                )
        elif block.kind == "quote":
            if not questions:
                report.error(
                    path,
                    "this help text does not belong to any question",
                    line=block.line,
                    hint="the > lines go after the options of a question",
                )
                continue
            questions[-1]["ayuda"] = " ".join(block.lines)
        else:
            report.error(
                path,
                f"a {block.kind} cannot be used in an opcion activity",
                line=block.line,
                hint="an opcion activity is: a question, then its [ ] options, then optional >",
            )

    for question in questions:
        line = question["linea"]
        options = question["opciones"]
        if len(options) < 2:
            report.error(
                path,
                f'the question "{_short(question["pregunta"])}" needs at least two options',
                line=line,
                hint="list them underneath as:\n      - [x] correct one\n      - [ ] another one",
            )
        elif not any(option["correcta"] for option in options):
            report.error(
                path,
                f'the question "{_short(question["pregunta"])}" has no correct option',
                line=line,
                hint="mark the right one by changing its [ ] to [x]",
            )
    if not questions:
        report.error(path, "this opcion activity has no questions", line=1)
    return questions


# --------------------------------------------------------------------------- huecos


def _parse_huecos(blocks: list[Block], path: Path, report: Report) -> list[dict]:
    """One sentence per line, ``{respuesta}`` marks a gap, ``>`` gives the help."""
    items: list[dict] = []
    for block in blocks:
        if block.kind in ("paragraph", "list"):
            for index, line in enumerate(block.lines):
                number = block.line_of(index)
                partes = _parse_gaps(line, path, number, report)
                if partes is None:
                    # Already reported; do not pile a second message on the same line.
                    continue
                if not any(part["tipo"] == "hueco" for part in partes):
                    report.error(
                        path,
                        f'the sentence "{_short(line)}" has no gap',
                        line=number,
                        hint="put the answer in braces, as in: Yo {estudio} español.",
                    )
                    continue
                items.append({"partes": partes, "ayuda": "", "linea": number})
        elif block.kind == "quote":
            if not items:
                report.error(
                    path,
                    "this help text does not belong to any sentence",
                    line=block.line,
                    hint="the > line goes after the sentence it translates",
                )
                continue
            items[-1]["ayuda"] = " ".join(block.lines)
        else:
            report.error(
                path,
                f"a {block.kind} cannot be used in a huecos activity",
                line=block.line,
                hint="write one sentence per line, with the answers in braces",
            )
    if not items:
        report.error(path, "this huecos activity has no sentences", line=1)
    return items


def _parse_gaps(line: str, path: Path, number: int, report: Report) -> list[dict] | None:
    """Scan one line into literal text and ``{a|b}`` gaps. ``None`` if the line is broken."""
    partes: list[dict] = []
    buffer: list[str] = []
    index = 0

    def flush_text() -> None:
        if buffer:
            partes.append({"tipo": "texto", "texto": "".join(buffer)})
            buffer.clear()

    while index < len(line):
        char = line[index]
        if char == "\\" and index + 1 < len(line):
            buffer.append(line[index + 1])
            index += 2
            continue
        if char == "}":
            report.error(
                path,
                "there is a closing brace with no opening one",
                line=number,
                hint=r"to write a literal brace use \}",
            )
            return None
        if char != "{":
            buffer.append(char)
            index += 1
            continue

        end = _find_closing_brace(line, index)
        if end is None:
            report.error(
                path,
                "a gap is opened with { but never closed",
                line=number,
                hint="close it with }, as in: Yo {estudio} español.",
            )
            return None

        flush_text()
        answers = [
            unescape(answer).strip() for answer in _split_alternatives(line[index + 1 : end])
        ]
        answers = [answer for answer in answers if answer]
        if not answers:
            report.error(
                path,
                "this gap is empty",
                line=number,
                hint="write the expected answer inside the braces, as in {estudio}",
            )
        else:
            partes.append({"tipo": "hueco", "respuestas": answers})
        index = end + 1

    flush_text()
    return partes


def _find_closing_brace(line: str, start: int) -> int | None:
    index = start + 1
    while index < len(line):
        if line[index] == "\\":
            index += 2
            continue
        if line[index] == "}":
            return index
        index += 1
    return None


def _split_alternatives(inner: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    index = 0
    while index < len(inner):
        if inner[index] == "\\" and index + 1 < len(inner):
            current.append(inner[index : index + 2])
            index += 2
            continue
        if inner[index] == "|":
            parts.append("".join(current))
            current = []
            index += 1
            continue
        current.append(inner[index])
        index += 1
    parts.append("".join(current))
    return parts


# --------------------------------------------------------------------------- pareja


def _parse_pareja(blocks: list[Block], path: Path, report: Report) -> list[dict]:
    """One pair per line: ``izquierda = derecha``."""
    pairs: list[dict] = []
    for block in blocks:
        if block.kind not in ("list", "paragraph"):
            report.error(
                path,
                f"a {block.kind} cannot be used in a pareja activity",
                line=block.line,
                hint="write one pair per line, as: - encima de = debajo de",
            )
            continue
        for index, line in enumerate(block.lines):
            number = block.line_of(index)
            pair = split_pair(line)
            if pair is None:
                report.error(
                    path,
                    f'the line "{_short(line)}" is not a pair',
                    line=number,
                    hint="separate the two halves with a space, an equals sign and a space:\n"
                    "      - encima de = debajo de",
                )
                continue
            izquierda, derecha = pair
            if not izquierda or not derecha:
                report.error(path, "both halves of a pair must have text", line=number)
                continue
            pairs.append({"izquierda": izquierda, "derecha": derecha, "linea": number})

    seen: dict[str, int] = {}
    for pair in pairs:
        key = pair["izquierda"].casefold()
        if key in seen:
            report.error(
                path,
                f'"{pair["izquierda"]}" appears on the left twice',
                line=pair["linea"],
                hint=f"it is already used on line {seen[key]}; the left column must be unique",
            )
        seen.setdefault(key, pair["linea"])

    if len(pairs) < 2:
        report.error(
            path,
            "a pareja activity needs at least two pairs",
            line=1,
            hint="with only one pair there is nothing to match",
        )
    return pairs


# --------------------------------------------------------------------------- orden


def _parse_orden(blocks: list[Block], path: Path, report: Report) -> list[dict]:
    """One correct sentence per line; ``[...]`` keeps words together as one token."""
    items: list[dict] = []
    for block in blocks:
        if block.kind in ("paragraph", "list"):
            for index, line in enumerate(block.lines):
                number = block.line_of(index)
                tokens = _tokenise(line, path, number, report)
                if tokens is None:
                    continue
                if len(tokens) < 3:
                    report.error(
                        path,
                        f'the sentence "{_short(line)}" has too few parts to order',
                        line=number,
                        hint="it needs at least three words or [grouped] chunks",
                    )
                    continue
                items.append({"piezas": tokens, "ayuda": "", "linea": number})
        elif block.kind == "quote":
            if not items:
                report.error(
                    path,
                    "this help text does not belong to any sentence",
                    line=block.line,
                    hint="the > line goes after the sentence it translates",
                )
                continue
            items[-1]["ayuda"] = " ".join(block.lines)
        else:
            report.error(
                path,
                f"a {block.kind} cannot be used in an orden activity",
                line=block.line,
                hint="write one correct sentence per line",
            )
    if not items:
        report.error(path, "this orden activity has no sentences", line=1)
    return items


def _tokenise(line: str, path: Path, number: int, report: Report) -> list[str] | None:
    tokens: list[str] = []
    current: list[str] = []
    index = 0

    def flush() -> None:
        if current:
            tokens.append("".join(current))
            current.clear()

    while index < len(line):
        char = line[index]
        if char == "\\" and index + 1 < len(line):
            current.append(line[index + 1])
            index += 2
            continue
        if char == "[":
            end = line.find("]", index)
            if end == -1:
                report.error(
                    path,
                    "a group is opened with [ but never closed",
                    line=number,
                    hint="close it with ], as in: [al lado de]",
                )
                return None
            flush()
            chunk = unescape(line[index + 1 : end]).strip()
            if chunk:
                tokens.append(chunk)
            index = end + 1
            continue
        if char.isspace():
            flush()
            index += 1
            continue
        current.append(char)
        index += 1

    flush()
    return tokens


# ---------------------------------------------------------------------- vocabulario


def _parse_vocabulario(blocks: list[Block], path: Path, report: Report) -> list[dict]:
    """``##`` headings make groups; ``español = Deutsch`` lines are the entries."""
    groups: list[dict] = [{"titulo": "", "entradas": [], "linea": 1}]
    for block in blocks:
        if block.kind == "heading":
            groups.append({"titulo": block.lines[0], "entradas": [], "linea": block.line})
        elif block.kind in ("paragraph", "list"):
            for index, line in enumerate(block.lines):
                pair = split_pair(line)
                if pair is None:
                    groups[-1]["entradas"].append(
                        {"es": unescape(line).strip(), "de": "", "linea": block.line_of(index)}
                    )
                    continue
                español, aleman = pair
                if not español:
                    report.error(
                        path,
                        "this entry has no Spanish word",
                        line=block.line_of(index),
                        hint="write it as: la cocina = die Küche",
                    )
                    continue
                groups[-1]["entradas"].append(
                    {"es": español, "de": aleman, "linea": block.line_of(index)}
                )
        else:
            report.error(
                path,
                f"a {block.kind} cannot be used in a vocabulario activity",
                line=block.line,
                hint="use ## for a group and one entry per line",
            )

    groups = [group for group in groups if group["entradas"] or group["titulo"]]
    for group in groups:
        if not group["entradas"]:
            report.warning(
                path,
                f'the group "{group["titulo"]}" has no words in it',
                line=group["linea"],
            )
    if not any(group["entradas"] for group in groups):
        report.error(
            path,
            "this vocabulario activity has no words",
            line=1,
            hint="add lines like: la cocina = die Küche",
        )
    return groups


# ----------------------------------------------------------------------- prose types


def _parse_libre(segments: list[Segment], path: Path, report: Report) -> Body:
    """Prompt in Markdown, with an optional ``::: modelo`` answer."""
    modelos = [segment for segment in segments if segment.label == "modelo"]
    for extra in modelos[1:]:
        report.error(
            path,
            "there is more than one ::: modelo block",
            line=extra.line,
            hint="keep a single model answer per activity",
        )
    for segment in segments:
        if segment.label and segment.label != "modelo":
            report.error(
                path,
                f'"::: {segment.label}" cannot be used in a libre activity',
                line=segment.line,
                hint="a libre activity only takes a ::: modelo block",
            )
    return Body(items=[], prose=segments)


def _parse_nota(segments: list[Segment], path: Path, report: Report) -> Body:
    """Free Markdown, optionally with ``::: de`` blocks."""
    for segment in segments:
        if segment.label and segment.label != "de":
            report.error(
                path,
                f'"::: {segment.label}" cannot be used in a nota activity',
                line=segment.line,
                hint="a nota only takes ::: de blocks",
            )
    if not segments:
        report.error(path, "this nota activity is empty", line=1)
    return Body(items=[], prose=segments)


_STRUCTURED_PARSERS = {
    "opcion": _parse_opcion,
    "huecos": _parse_huecos,
    "pareja": _parse_pareja,
    "orden": _parse_orden,
    "vocabulario": _parse_vocabulario,
}

_PROSE_PARSERS = {
    "libre": _parse_libre,
    "nota": _parse_nota,
}


def _short(text: str, limit: int = 40) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"
