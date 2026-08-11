"""Front matter splitting and metadata validation (spec sections 3 and 5)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from conftest import errors, has_message

from aula.errors import Report
from aula.frontmatter import check_choice, check_keys, check_types, parse_file


def write(tmp_path: Path, text: str, name: str = "actividad.md") -> Path:
    path = tmp_path / name
    path.write_text(dedent(text).lstrip("\n"), encoding="utf-8")
    return path


def test_splits_metadata_from_body(tmp_path: Path, report: Report):
    path = write(
        tmp_path,
        """
        +++
        titulo = "La casa"
        etiquetas = ["casa", "localizacion"]
        +++

        El cuerpo.
        """,
    )
    parsed = parse_file(path, report)

    assert parsed is not None
    assert parsed.meta == {"titulo": "La casa", "etiquetas": ["casa", "localizacion"]}
    assert parsed.body.strip() == "El cuerpo."
    assert parsed.body_line == 5
    assert not report.problems


def test_body_may_be_empty(tmp_path: Path, report: Report):
    parsed = parse_file(write(tmp_path, '+++\ntitulo = "x"\n+++\n'), report)

    assert parsed is not None
    assert parsed.body.strip() == ""
    assert not report.problems


def test_missing_opening_fence_is_reported(tmp_path: Path, report: Report):
    parsed = parse_file(write(tmp_path, 'titulo = "La casa"\n'), report)

    assert parsed is None
    assert has_message(report, "must start with a line containing only +++")
    assert errors(report)[0].line == 1


def test_unclosed_fence_is_reported(tmp_path: Path, report: Report):
    parsed = parse_file(write(tmp_path, '+++\ntitulo = "La casa"\n\nEl cuerpo.\n'), report)

    assert parsed is None
    assert has_message(report, "never closed")


def test_empty_file_is_reported(tmp_path: Path, report: Report):
    assert parse_file(write(tmp_path, ""), report) is None
    assert has_message(report, "empty")


def test_invalid_toml_reports_the_line(tmp_path: Path, report: Report):
    path = write(
        tmp_path,
        """
        +++
        titulo = "La casa"
        categoria = vocabulario
        +++
        """,
    )
    parsed = parse_file(path, report)

    assert parsed is None
    assert has_message(report, "not valid TOML")
    # The offending line is the third of the file, not the second of the metadata.
    assert errors(report)[0].line == 3


def test_unknown_key_suggests_the_right_one(tmp_path: Path, report: Report):
    parsed = parse_file(write(tmp_path, '+++\ntitolo = "La casa"\n+++\n'), report)
    check_keys(parsed, report, required=set(), optional={"titulo", "categoria"})

    assert has_message(report, 'unknown setting "titolo"')
    problem = errors(report)[0]
    assert problem.hint is not None and 'did you mean "titulo"' in problem.hint
    assert problem.line == 2


def test_unknown_key_without_a_close_match_lists_the_allowed_ones(tmp_path: Path, report: Report):
    parsed = parse_file(write(tmp_path, '+++\ncolor = "rojo"\n+++\n'), report)
    check_keys(parsed, report, required=set(), optional={"titulo", "categoria"})

    problem = errors(report)[0]
    assert problem.hint is not None and "allowed settings here" in problem.hint


def test_missing_required_key_is_reported(tmp_path: Path, report: Report):
    parsed = parse_file(write(tmp_path, '+++\ntitulo = "La casa"\n+++\n'), report)
    check_keys(parsed, report, required={"titulo", "categoria"}, optional=set())

    assert has_message(report, '"categoria" is required but missing')


def test_german_key_without_a_spanish_one_is_reported(tmp_path: Path, report: Report):
    parsed = parse_file(write(tmp_path, '+++\ntitulo_de = "Das Haus"\n+++\n'), report)
    check_keys(parsed, report, required=set(), optional={"titulo", "titulo_de"})

    assert has_message(report, '"titulo_de" has no "titulo" next to it')


def test_wrong_value_type_is_reported(tmp_path: Path, report: Report):
    parsed = parse_file(write(tmp_path, '+++\ntitulo = 3\nbarajar = "si"\n+++\n'), report)
    check_types(parsed, report, {"titulo": str, "barajar": bool})

    assert has_message(report, '"titulo" must be text in quotes')
    assert has_message(report, '"barajar" must be true or false')


def test_list_of_non_text_is_reported(tmp_path: Path, report: Report):
    parsed = parse_file(write(tmp_path, "+++\netiquetas = [1, 2]\n+++\n"), report)
    check_types(parsed, report, {"etiquetas": list})

    assert has_message(report, "must be a list of text values")


def test_choice_outside_the_allowed_set_is_reported(tmp_path: Path, report: Report):
    parsed = parse_file(write(tmp_path, '+++\nnivel = "dificil"\n+++\n'), report)
    value = check_choice(parsed, report, "nivel", {"basico", "repaso", "desafio"}, "basico")

    assert value == "basico"
    assert has_message(report, "not one of the allowed values")
    assert "desafio" in errors(report)[0].hint


def test_choice_falls_back_to_the_default_when_absent(tmp_path: Path, report: Report):
    parsed = parse_file(write(tmp_path, '+++\ntitulo = "x"\n+++\n'), report)

    assert check_choice(parsed, report, "nivel", {"basico"}, "basico") == "basico"
    assert not report.problems
