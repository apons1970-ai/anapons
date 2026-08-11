"""Turning a loaded :class:`~aula.model.Site` into static HTML.

Everything a student needs to *read* is in the HTML. The JavaScript only adds the
interaction: shuffling, checking answers, revealing help, remembering progress. A
lesson with scripts blocked is still a readable lesson.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt
from markupsafe import Markup

from .blocks import Segment
from .errors import Report
from .model import Leccion, Semestre, Site, lesson_id

TEMPLATES = Path(__file__).parent / "templates"
ASSETS = Path(__file__).parent / "assets"

_markdown = MarkdownIt("commonmark").enable(["table", "strikethrough"])


def render_site(site: Site, out: Path, report: Report) -> int:
    """Write the whole site. Returns the number of pages written."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["site"] = site
    env.globals["url"] = _url_builder(site)
    env.filters["markdown"] = _render_markdown
    env.filters["prose"] = _render_prose
    env.filters["respuestas"] = _gap_answers

    try:
        out.mkdir(parents=True, exist_ok=True)
        shutil.copytree(ASSETS, out / "assets", dirs_exist_ok=True)
    except OSError as exc:
        report.error(out, f"cannot write the site: {exc}")
        return 0

    pages = 0
    _write(out / "index.html", env.get_template("index.html").render(cursos=site.cursos), report)
    pages += 1

    for curso in site.cursos:
        page = env.get_template("curso.html").render(curso=curso)
        _write(out / curso.slug / "index.html", page, report)
        pages += 1

        for semestre in curso.semestres:
            page = env.get_template("semestre.html").render(
                curso=curso, semestre=semestre, grupos=_by_category(semestre)
            )
            _write(out / curso.slug / semestre.slug / "index.html", page, report)
            pages += 1

            for index, leccion in enumerate(semestre.lecciones):
                page = env.get_template("leccion.html").render(
                    curso=curso,
                    semestre=semestre,
                    leccion=leccion,
                    leccion_id=lesson_id(curso, semestre, leccion),
                    anterior=semestre.lecciones[index - 1] if index else None,
                    siguiente=(
                        semestre.lecciones[index + 1]
                        if index + 1 < len(semestre.lecciones)
                        else None
                    ),
                )
                _write(out / curso.slug / semestre.slug / leccion.slug / "index.html", page, report)
                pages += 1

    return pages


#: The order categories appear on a semester page, with their headings.
CATEGORIAS_EN_ORDEN = (
    ("vocabulario", "📚 Vocabulario"),
    ("gramatica", "✏️ Gramática"),
    ("microbloque", "🧩 Microbloques"),
)


def _by_category(semestre: Semestre) -> list[tuple[str, list[Leccion]]]:
    """Group a semester's lessons, keeping empty categories out."""
    grouped = []
    for categoria, heading in CATEGORIAS_EN_ORDEN:
        lecciones = [item for item in semestre.lecciones if item.categoria == categoria]
        if lecciones:
            grouped.append((heading, lecciones))
    return grouped


def _url_builder(site: Site):
    def url(*parts: str) -> str:
        return site.base_url + "".join(f"{part}/" for part in parts if part)

    return url


def _gap_answers(items: list[dict]) -> list[list[list[str]]]:
    """Accepted answers for a ``huecos`` activity: per sentence, per gap, in order."""
    return [
        [part["respuestas"] for part in item["partes"] if part["tipo"] == "hueco"] for item in items
    ]


def _render_markdown(text: str) -> Markup:
    return Markup(_markdown.render(text))


def _render_prose(segments: list[Segment]) -> Markup:
    """Render body segments, wrapping German ones so the toggle can hide them."""
    pieces = []
    for segment in segments:
        html = _markdown.render(segment.text)
        if segment.label == "de":
            pieces.append(f'<div class="de">{html}</div>')
        else:
            pieces.append(html)
    return Markup("".join(pieces))


def _write(path: Path, html: str, report: Report) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
    except OSError as exc:
        report.error(path, f"cannot write this page: {exc}")
