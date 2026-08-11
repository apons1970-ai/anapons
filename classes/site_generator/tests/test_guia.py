"""The author guide must stay true to what the generator actually accepts.

The guide is what Ana copies from. An example in it that no longer validates is a
worse bug than a broken test, because she has no way to tell it is our fault. This
extracts every complete activity example from the guide and runs it through the
real loader.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from aula.errors import Report
from aula.loader import load_site

GUIA = Path(__file__).resolve().parents[2] / "docs" / "como-escribir-las-lecciones.md"


def ejemplos() -> list[tuple[str, str]]:
    """Every fenced block in the guide that is a complete activity file."""
    encontrados = []
    for bloque in re.findall(r"```markdown\n(.*?)```", GUIA.read_text(encoding="utf-8"), re.DOTALL):
        if not bloque.startswith("+++"):
            continue
        tipo = re.search(r'tipo = "(\w+)"', bloque)
        # The cheat sheet has a skeleton with `tipo = "..."`, which is not an example.
        if tipo and tipo.group(1) != "...":
            encontrados.append((tipo.group(1), bloque))
    return encontrados


def test_the_guide_exists_and_shows_every_type():
    tipos = {tipo for tipo, _ in ejemplos()}

    assert tipos == {"vocabulario", "opcion", "huecos", "pareja", "orden", "libre", "nota"}


@pytest.mark.parametrize("indice", range(len(ejemplos())))
def test_every_example_in_the_guide_validates(indice: int, tmp_path: Path):
    tipo, bloque = ejemplos()[indice]
    contenido = tmp_path / "content"
    leccion = contenido / "6G/01-bloque/01-leccion"
    leccion.mkdir(parents=True)

    (contenido / "site.toml").write_text(
        'version = 1\ntitulo = "Prueba"\nbase_url = "/"\ncursos = ["6G"]\n', encoding="utf-8"
    )
    (contenido / "6G/_indice.md").write_text('+++\ntitulo = "Clase 6G"\n+++\n', encoding="utf-8")
    (contenido / "6G/01-bloque/_indice.md").write_text(
        '+++\ntitulo = "Bloque"\n+++\n', encoding="utf-8"
    )
    (leccion / "_indice.md").write_text(
        '+++\ntitulo = "Leccion"\ncategoria = "gramatica"\n+++\n', encoding="utf-8"
    )
    (leccion / "01-ejemplo.md").write_text(bloque, encoding="utf-8")

    report = Report(root=contenido)
    load_site(contenido, report)
    problemas = [
        f"{p.path.name}:{p.line} {p.message}" for p in report.problems if p.severity == "error"
    ]

    assert not problemas, f"the {tipo} example in the guide does not validate: {problemas}"
