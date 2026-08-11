"""Shared helpers for the test suite."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from aula.activities import Body, parse_body
from aula.errors import Report


@pytest.fixture
def report(tmp_path: Path) -> Report:
    return Report(root=tmp_path)


@pytest.fixture
def parse(tmp_path: Path, report: Report):
    """Parse an activity body of a given type, returning the body and the report."""

    def _parse(tipo: str, body: str) -> tuple[Body, Report]:
        path = tmp_path / "actividad.md"
        text = dedent(body).strip("\n")
        path.write_text(f'+++\ntipo = "{tipo}"\n+++\n\n{text}\n', encoding="utf-8")
        # Line 1 is +++, 2 is tipo, 3 is +++, 4 is blank, so the body starts on 5.
        return parse_body(tipo, "\n" + text, 4, path, report), report

    return _parse


def messages(report: Report) -> list[str]:
    return [problem.message for problem in report.problems]


def errors(report: Report) -> list:
    return [problem for problem in report.problems if problem.severity == "error"]


def warnings(report: Report) -> list:
    return [problem for problem in report.problems if problem.severity == "warning"]


def has_message(report: Report, fragment: str) -> bool:
    return any(fragment in problem.message for problem in report.problems)


def write_tree(root: Path, files: dict[str, str]) -> Path:
    """Create a content tree from a mapping of relative path to file text."""
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(text).lstrip("\n"), encoding="utf-8")
    return root


SITE_TOML = """
version = 1
titulo = "Clases de español"
base_url = "/classes/"
cursos = ["6G"]
"""

CURSO_INDEX = """
+++
titulo = "Clase 6G"
+++
"""

SEMESTRE_INDEX = """
+++
titulo = "Primer semestre A"
+++
"""

LECCION_INDEX = """
+++
titulo = "La casa y la localización"
categoria = "vocabulario"
+++

Con **HAY** hablamos de cosas indeterminadas.
"""

ACTIVIDAD = """
+++
tipo = "opcion"
titulo = "Contrarios"
+++

encima de

- [x] debajo de
- [ ] al lado de
"""


@pytest.fixture
def good_site(tmp_path: Path) -> Path:
    """A minimal but complete and valid content tree."""
    content = tmp_path / "content"
    write_tree(
        content,
        {
            "site.toml": SITE_TOML,
            "6G/_indice.md": CURSO_INDEX,
            "6G/01-primer-semestre-a/_indice.md": SEMESTRE_INDEX,
            "6G/01-primer-semestre-a/01-la-casa/_indice.md": LECCION_INDEX,
            "6G/01-primer-semestre-a/01-la-casa/01-contrarios.md": ACTIVIDAD,
        },
    )
    return content
