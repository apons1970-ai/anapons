"""Body scanning: ``:::`` containers, block runs, and the shared little helpers."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from conftest import has_message

from aula.blocks import parse_blocks, split_containers, split_pair, unescape
from aula.errors import Report

PATH = Path("actividad.md")


def containers(text: str, report: Report, first_line: int = 1):
    return split_containers(dedent(text).strip("\n"), first_line, PATH, report)


def test_blocks_group_runs_of_the_same_kind():
    blocks = parse_blocks("una lámpara\n\n- [x] HAY\n- [ ] ESTAR\n\n> porque sí\n", 1)

    assert [block.kind for block in blocks] == ["paragraph", "list", "quote"]
    assert blocks[1].lines == ["[x] HAY", "[ ] ESTAR"]
    assert blocks[2].lines == ["porque sí"]


def test_blocks_record_line_numbers_including_the_offset():
    blocks = parse_blocks("primera\nsegunda\n\n- tercera\n", 10)

    assert blocks[0].line == 10
    assert blocks[0].line_of(1) == 11
    assert blocks[1].line == 13


def test_blank_lines_are_insignificant_apart_from_separating_runs():
    packed = parse_blocks("uno\n- a\n- b\n> ayuda\n", 1)
    spaced = parse_blocks("uno\n\n- a\n- b\n\n> ayuda\n", 1)

    assert [block.kind for block in packed] == [block.kind for block in spaced]
    assert [block.lines for block in packed] == [block.lines for block in spaced]


def test_each_heading_is_its_own_block():
    blocks = parse_blocks("## Lugares\n## Objetos\nla nevera\n", 1)

    assert [block.kind for block in blocks] == ["heading", "heading", "paragraph"]
    assert blocks[0].lines == ["Lugares"]


def test_containers_are_split_out_and_labelled(report: Report):
    segments = containers(
        """
        Con HAY hablamos de cosas indeterminadas.

        ::: de
        Mit HAY spricht man über unbestimmte Dinge.
        :::

        Y seguimos en español.
        """,
        report,
    )

    assert [segment.label for segment in segments] == ["", "de", ""]
    assert segments[1].text == "Mit HAY spricht man über unbestimmte Dinge."
    assert not report.problems


def test_container_line_numbers_point_at_the_first_real_line(report: Report):
    segments = containers("uno\n\n::: de\n\neins\n:::\n", report, first_line=5)

    assert segments[0].line == 5
    assert segments[1].line == 9


def test_unclosed_container_is_reported(report: Report):
    containers("::: de\neins\n", report)

    assert has_message(report, "never closed")


def test_nested_container_is_reported(report: Report):
    containers("::: de\n::: modelo\ntext\n:::\n:::\n", report)

    assert has_message(report, "starts inside another")


def test_stray_closing_fence_is_reported(report: Report):
    containers("texto\n:::\n", report)

    assert has_message(report, "closes a block that was never opened")


def test_unknown_container_label_is_reported(report: Report):
    containers("::: aleman\ntext\n:::\n", report)

    assert has_message(report, "is not a kind of block the site knows")


def test_split_pair_uses_the_first_separator():
    assert split_pair("la cocina = die Küche") == ("la cocina", "die Küche")
    assert split_pair("entre ... y ... = zwischen ... und ...") == (
        "entre ... y ...",
        "zwischen ... und ...",
    )
    assert split_pair("a = b = c") == ("a", "b = c")


def test_split_pair_returns_none_without_a_separator():
    assert split_pair("la cocina") is None
    assert split_pair("2+2=4") is None


def test_escaped_separator_stays_literal():
    assert split_pair(r"2 \= dos = zwei") == ("2 = dos", "zwei")


def test_unescape_only_touches_reserved_characters():
    assert unescape(r"\{a\}") == "{a}"
    assert unescape(r"C:\ruta") == r"C:\ruta"
