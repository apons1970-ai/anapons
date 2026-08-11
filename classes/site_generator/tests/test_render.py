"""Rendering the loaded site to static HTML (spec section 8)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from conftest import ACTIVIDAD, LECCION_INDEX, write_tree

from aula.errors import Report
from aula.loader import load_site
from aula.render import render_site

LESSON = "6G/01-primer-semestre-a/01-la-casa"
PAGE = "6g/primer-semestre-a/la-casa/index.html"


@pytest.fixture
def built(good_site: Path, tmp_path: Path):
    """Build the fixture site and give back the output directory."""

    def _build(extra: dict[str, str] | None = None) -> Path:
        if extra:
            write_tree(good_site, extra)
        report = Report(root=good_site)
        site = load_site(good_site, report)
        out = tmp_path / "site"
        render_site(site, out, report)
        assert not [problem for problem in report.problems if problem.severity == "error"]
        return out

    return _build


def read(out: Path, relative: str) -> str:
    return (out / relative).read_text(encoding="utf-8")


def test_writes_a_page_per_level(built):
    out = built()

    assert (out / "index.html").is_file()
    assert (out / "6g/index.html").is_file()
    assert (out / "6g/primer-semestre-a/index.html").is_file()
    assert (out / PAGE).is_file()


def test_copies_the_assets(built):
    out = built()

    assert (out / "assets/aula.css").is_file()
    assert (out / "assets/aula.js").is_file()


def test_links_use_the_base_url(built):
    out = built()

    assert 'href="/classes/6g/"' in read(out, "index.html")
    assert 'href="/classes/assets/aula.css"' in read(out, PAGE)


def test_lesson_page_carries_the_stable_identifier(built):
    out = built()

    assert 'data-leccion="6g/primer-semestre-a/la-casa"' in read(out, PAGE)
    assert 'data-id="6g/primer-semestre-a/la-casa/contrarios"' in read(out, PAGE)


def test_lesson_prose_is_rendered_as_markdown(built):
    out = built()

    assert "<strong>HAY</strong>" in read(out, PAGE)


def test_german_prose_is_wrapped_so_it_can_be_hidden(built):
    out = built({f"{LESSON}/_indice.md": LECCION_INDEX + "\n::: de\nAuf Deutsch erklärt.\n:::\n"})

    assert '<div class="de">' in read(out, PAGE)
    assert "Auf Deutsch erklärt." in read(out, PAGE)


def test_content_is_escaped_not_injected(built):
    out = built(
        {
            f"{LESSON}/02-riesgo.md": (
                '+++\ntipo = "opcion"\ntitulo = "<script>alert(1)</script>"\n+++\n\n'
                "¿Y esto?\n\n- [x] a\n- [ ] b\n"
            )
        }
    )
    page = read(out, PAGE)

    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_huecos_answers_are_emitted_in_document_order(built):
    out = built(
        {
            f"{LESSON}/02-completa.md": (
                '+++\ntipo = "huecos"\ntitulo = "Completa"\n+++\n\n'
                "En mi habitación {hay} una cama.\n"
                "La cama {está|se encuentra} {aquí}.\n"
            )
        }
    )
    payload = re.search(
        r'<script type="application/json" class="respuestas">(.*?)</script>', read(out, PAGE)
    )

    assert json.loads(payload.group(1)) == [
        [["hay"]],
        [["está", "se encuentra"], ["aquí"]],
    ]


def test_multi_answer_questions_are_marked(built):
    out = built(
        {
            f"{LESSON}/02-varias.md": (
                '+++\ntipo = "opcion"\ntitulo = "Varias"\n+++\n\n'
                "¿Cuáles son lugares?\n\n- [x] la cocina\n- [x] el baño\n- [ ] la nevera\n"
            )
        }
    )

    assert 'data-varias="si"' in read(out, PAGE)


def test_shuffle_setting_reaches_the_markup(built):
    out = built()

    assert 'data-barajar="si"' in read(out, PAGE)


def test_pairs_share_an_index_across_the_two_columns(built):
    out = built(
        {
            f"{LESSON}/02-parejas.md": (
                '+++\ntipo = "pareja"\ntitulo = "Contrarios"\n+++\n\n'
                "- encima de = debajo de\n- delante de = detrás de\n"
            )
        }
    )
    page = read(out, PAGE)
    columna = re.search(r'<ul class="columna derecha">(.*?)</ul>', page, re.DOTALL).group(1)

    assert 'data-par="0"' in columna
    assert "debajo de" in columna


def test_libre_keeps_the_model_hidden(built):
    out = built(
        {
            f"{LESSON}/02-escribe.md": (
                '+++\ntipo = "libre"\ntitulo = "Escribe"\n+++\n\n'
                "Piensa en tu casa.\n\n::: modelo\nHay una cama.\n:::\n"
            )
        }
    )
    page = read(out, PAGE)

    assert '<div class="modelo" hidden>' in page
    assert "Hay una cama." in page


def test_semester_page_groups_lessons_by_category(built):
    out = built(
        {
            "6G/01-primer-semestre-a/02-el-presente/_indice.md": (
                '+++\ntitulo = "El presente"\ncategoria = "gramatica"\n+++\n'
            ),
            "6G/01-primer-semestre-a/02-el-presente/01-verbos.md": ACTIVIDAD,
        }
    )
    page = read(out, "6g/primer-semestre-a/index.html")

    assert "📚 Vocabulario" in page
    assert "✏️ Gramática" in page
    assert "🧩 Microbloques" not in page


def test_lessons_link_to_each_other_in_order(built):
    out = built(
        {
            "6G/01-primer-semestre-a/02-el-presente/_indice.md": (
                '+++\ntitulo = "El presente"\ncategoria = "gramatica"\n+++\n'
            ),
            "6G/01-primer-semestre-a/02-el-presente/01-verbos.md": ACTIVIDAD,
        }
    )

    assert 'class="siguiente" href="/classes/6g/primer-semestre-a/el-presente/"' in read(out, PAGE)
    assert 'class="anterior" href="/classes/6g/primer-semestre-a/la-casa/"' in read(
        out, "6g/primer-semestre-a/el-presente/index.html"
    )


def test_every_activity_type_renders(built):
    out = built(
        {
            f"{LESSON}/02-vocabulario.md": '+++\ntipo = "vocabulario"\ntitulo = "V"\n+++\n\nla cocina = die Küche\n',
            f"{LESSON}/03-huecos.md": '+++\ntipo = "huecos"\ntitulo = "H"\n+++\n\nYo {estudio} español.\n',
            f"{LESSON}/04-pareja.md": '+++\ntipo = "pareja"\ntitulo = "P"\n+++\n\n- a = b\n- c = d\n',
            f"{LESSON}/05-orden.md": '+++\ntipo = "orden"\ntitulo = "O"\n+++\n\nLa cama está aquí.\n',
            f"{LESSON}/06-libre.md": '+++\ntipo = "libre"\ntitulo = "L"\n+++\n\nEscribe.\n',
            f"{LESSON}/07-nota.md": '+++\ntipo = "nota"\ntitulo = "N"\n+++\n\nRecuerda esto.\n',
        }
    )
    page = read(out, PAGE)

    for tipo in ["opcion", "vocabulario", "huecos", "pareja", "orden", "libre", "nota"]:
        assert f'data-tipo="{tipo}"' in page, tipo


def test_a_lesson_is_readable_without_javascript(built):
    """Everything needed to read the lesson is in the HTML, not built by script."""
    out = built()
    page = read(out, PAGE)

    assert "encima de" in page
    assert "debajo de" in page


def test_the_inline_script_and_the_runtime_agree_on_the_storage_key():
    """The pre-paint script in base.html reads a key aula.js writes. They must match.

    They live in different files, so nothing but this test keeps them in step; when
    they drifted, the language choice silently stopped surviving a reload.
    """
    from aula.render import ASSETS, TEMPLATES

    plantilla = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    runtime = (ASSETS / "aula.js").read_text(encoding="utf-8")
    prefijo = re.search(r'var CLAVE = "(.*?)";', runtime).group(1)

    assert f'localStorage.getItem("{prefijo}aleman")' in plantilla
