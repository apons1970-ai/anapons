"""Walking ``content/`` and turning it into a :class:`~aula.model.Site`.

Loading and validating are the same pass: anything that cannot be turned into a
sound model is reported with a file and a line, and the walk carries on so that one
bad file does not hide the next ten.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from .activities import ACTIVITY_TYPES, SHUFFLE_BY_DEFAULT, parse_body
from .blocks import Segment, split_containers
from .errors import Report
from .frontmatter import ParsedFile, check_choice, check_keys, check_types, parse_file
from .model import CATEGORIAS, ESTADOS, NIVELES, Actividad, Curso, Leccion, Semestre, Site

INDEX_NAME = "_indice.md"
SITE_CONFIG = "site.toml"
SUPPORTED_VERSION = 1

#: Directory and file names: an optional numeric prefix, then lowercase and hyphens.
NAME = re.compile(r"^(?:(\d+)-)?([a-z0-9]+(?:-[a-z0-9]+)*)$")

SITE_REQUIRED = {"version", "titulo", "base_url", "cursos"}
SITE_OPTIONAL = {"titulo_de"}
SECTION_REQUIRED = {"titulo"}
SECTION_OPTIONAL = {"titulo_de", "estado"}
LECCION_REQUIRED = {"titulo", "categoria"}
LECCION_OPTIONAL = {"titulo_de", "icono", "etiquetas", "estado"}
ACTIVIDAD_REQUIRED = {"tipo", "titulo"}
ACTIVIDAD_OPTIONAL = {
    "titulo_de",
    "instruccion",
    "instruccion_de",
    "nivel",
    "barajar",
    "etiquetas",
    "estado",
}


def load_site(content: Path, report: Report, *, include_drafts: bool = False) -> Site | None:
    """Load and validate the whole content tree."""
    config_path = content / SITE_CONFIG
    if not config_path.is_file():
        report.error(content, f"there is no {SITE_CONFIG} in the content folder")
        return None

    parsed = _parse_toml_config(config_path, report)
    if parsed is None:
        return None
    check_keys(parsed, report, required=SITE_REQUIRED, optional=SITE_OPTIONAL)
    check_types(
        parsed,
        report,
        {"version": int, "titulo": str, "titulo_de": str, "base_url": str, "cursos": list},
    )

    version = parsed.meta.get("version")
    if isinstance(version, int) and version != SUPPORTED_VERSION:
        report.error(
            config_path,
            f"this content is version {version}, but the site generator understands "
            f"version {SUPPORTED_VERSION}",
            hint="update the generator, or change version in site.toml",
        )

    site = Site(
        version=SUPPORTED_VERSION,
        titulo=str(parsed.meta.get("titulo", "")),
        titulo_de=str(parsed.meta.get("titulo_de", "")),
        base_url=_normalise_base_url(str(parsed.meta.get("base_url", "/"))),
        path=content,
    )

    listed = [name for name in parsed.meta.get("cursos", []) if isinstance(name, str)]
    for name in listed:
        directory = content / name
        if not directory.is_dir():
            report.error(
                config_path,
                f'cursos lists "{name}", but there is no folder with that name',
                hint=f"create the folder {name}/ or remove it from the list",
            )
            continue
        curso = _load_curso(directory, name, report, include_drafts)
        if curso is not None:
            site.cursos.append(curso)

    for directory in sorted(path for path in content.iterdir() if path.is_dir()):
        if directory.name not in listed:
            report.warning(
                config_path,
                f'the folder "{directory.name}" is not listed in cursos, so it is not published',
                hint=f'add "{directory.name}" to the cursos list to publish it',
            )
    return site


def _load_curso(directory: Path, codigo: str, report: Report, include_drafts: bool) -> Curso | None:
    parsed = _load_index(directory, report)
    if parsed is None:
        return None
    check_keys(parsed, report, required=SECTION_REQUIRED, optional=SECTION_OPTIONAL)
    check_types(parsed, report, {"titulo": str, "titulo_de": str, "estado": str})
    estado = check_choice(parsed, report, "estado", ESTADOS, "publicado")
    if estado == "borrador" and not include_drafts:
        report.warning(parsed.path, f'the course "{codigo}" is a draft, so it is not published')
        return None

    curso = Curso(
        slug=codigo.lower(),
        codigo=codigo,
        path=directory,
        titulo=str(parsed.meta.get("titulo", codigo)),
        titulo_de=str(parsed.meta.get("titulo_de", "")),
        estado=estado or "publicado",
        prose=_prose(parsed, report),
    )
    for child, slug in _ordered_children(directory, report, want_dirs=True):
        semestre = _load_semestre(child, slug, report, include_drafts)
        if semestre is not None:
            curso.semestres.append(semestre)
    if not curso.semestres:
        report.warning(directory, f'the course "{codigo}" has no published semesters in it')
    return curso


def _load_semestre(
    directory: Path, slug: str, report: Report, include_drafts: bool
) -> Semestre | None:
    parsed = _load_index(directory, report)
    if parsed is None:
        return None
    check_keys(parsed, report, required=SECTION_REQUIRED, optional=SECTION_OPTIONAL)
    check_types(parsed, report, {"titulo": str, "titulo_de": str, "estado": str})
    estado = check_choice(parsed, report, "estado", ESTADOS, "publicado")
    if estado == "borrador" and not include_drafts:
        return None

    semestre = Semestre(
        slug=slug,
        path=directory,
        titulo=str(parsed.meta.get("titulo", slug)),
        titulo_de=str(parsed.meta.get("titulo_de", "")),
        estado=estado or "publicado",
        prose=_prose(parsed, report),
    )
    for child, child_slug in _ordered_children(directory, report, want_dirs=True):
        leccion = _load_leccion(child, child_slug, report, include_drafts)
        if leccion is not None:
            semestre.lecciones.append(leccion)
    return semestre


def _load_leccion(
    directory: Path, slug: str, report: Report, include_drafts: bool
) -> Leccion | None:
    parsed = _load_index(directory, report)
    if parsed is None:
        return None
    check_keys(parsed, report, required=LECCION_REQUIRED, optional=LECCION_OPTIONAL)
    check_types(
        parsed,
        report,
        {
            "titulo": str,
            "titulo_de": str,
            "categoria": str,
            "icono": str,
            "etiquetas": list,
            "estado": str,
        },
    )
    estado = check_choice(parsed, report, "estado", ESTADOS, "publicado")
    if estado == "borrador" and not include_drafts:
        return None

    leccion = Leccion(
        slug=slug,
        path=directory,
        titulo=str(parsed.meta.get("titulo", slug)),
        titulo_de=str(parsed.meta.get("titulo_de", "")),
        categoria=check_choice(parsed, report, "categoria", CATEGORIAS) or "gramatica",
        icono=str(parsed.meta.get("icono", "")),
        etiquetas=list(parsed.meta.get("etiquetas", [])),
        estado=estado or "publicado",
        prose=_prose(parsed, report),
    )
    for child, child_slug in _ordered_children(directory, report, want_dirs=False):
        actividad = _load_actividad(child, child_slug, report, include_drafts)
        if actividad is not None:
            leccion.actividades.append(actividad)
    if not leccion.actividades:
        report.warning(
            directory,
            f'the lesson "{leccion.titulo}" has no published activities in it',
            hint="add an activity file next to _indice.md",
        )
    return leccion


def _load_actividad(
    path: Path, slug: str, report: Report, include_drafts: bool
) -> Actividad | None:
    parsed = parse_file(path, report)
    if parsed is None:
        return None
    check_keys(parsed, report, required=ACTIVIDAD_REQUIRED, optional=ACTIVIDAD_OPTIONAL)
    check_types(
        parsed,
        report,
        {
            "tipo": str,
            "titulo": str,
            "titulo_de": str,
            "instruccion": str,
            "instruccion_de": str,
            "nivel": str,
            "barajar": bool,
            "etiquetas": list,
            "estado": str,
        },
    )
    estado = check_choice(parsed, report, "estado", ESTADOS, "publicado")
    if estado == "borrador" and not include_drafts:
        return None

    tipo = check_choice(parsed, report, "tipo", set(ACTIVITY_TYPES))
    if tipo is None:
        # Without a usable type there is no way to read the body.
        return None

    body = parse_body(tipo, parsed.body, parsed.body_line, path, report)
    return Actividad(
        slug=slug,
        path=path,
        tipo=tipo,
        titulo=str(parsed.meta.get("titulo", slug)),
        titulo_de=str(parsed.meta.get("titulo_de", "")),
        instruccion=str(parsed.meta.get("instruccion", "")),
        instruccion_de=str(parsed.meta.get("instruccion_de", "")),
        nivel=check_choice(parsed, report, "nivel", NIVELES, "basico") or "basico",
        barajar=bool(parsed.meta.get("barajar", SHUFFLE_BY_DEFAULT.get(tipo, False))),
        etiquetas=list(parsed.meta.get("etiquetas", [])),
        estado=estado or "publicado",
        body=body,
    )


def _load_index(directory: Path, report: Report) -> ParsedFile | None:
    path = directory / INDEX_NAME
    if not path.is_file():
        report.error(
            directory,
            f"this folder has no {INDEX_NAME}",
            hint=f"every folder needs a {INDEX_NAME} describing it",
        )
        return None
    return parse_file(path, report)


def _prose(parsed: ParsedFile, report: Report) -> list[Segment]:
    """The Markdown body of an ``_indice.md``, split into language segments."""
    segments = split_containers(parsed.body, parsed.body_line, parsed.path, report)
    for segment in segments:
        if segment.label and segment.label != "de":
            report.error(
                parsed.path,
                f'"::: {segment.label}" cannot be used here',
                line=segment.line,
                hint="only ::: de blocks are allowed in an explanation",
            )
    return segments


def _ordered_children(
    directory: Path, report: Report, *, want_dirs: bool
) -> list[tuple[Path, str]]:
    """Children in ``01-`` prefix order, validating their names on the way."""
    children: list[tuple[int | None, str, Path, str]] = []
    prefixes: dict[str, Path] = {}

    for path in sorted(directory.iterdir()):
        if path.name.startswith(".") or path.name == INDEX_NAME:
            continue
        if path.is_dir() != want_dirs:
            kind = "folder" if want_dirs else "file"
            other = "file" if want_dirs else "folder"
            report.warning(
                path,
                f"expected a {kind} here but found a {other}, so it is ignored",
            )
            continue
        if not want_dirs and path.suffix != ".md":
            report.warning(path, "only .md files are used here, so this one is ignored")
            continue

        stem = path.stem if not want_dirs else path.name
        match = NAME.match(stem)
        if match is None:
            report.error(
                path,
                f'"{stem}" is not a valid name',
                hint="use lowercase letters, numbers and hyphens only, with no accents:\n"
                "      01-la-casa",
            )
            continue

        prefix, slug = match.group(1), match.group(2)
        if prefix is not None:
            if prefix in prefixes:
                report.error(
                    path,
                    f'the number {prefix} is already used by "{prefixes[prefix].name}"',
                    hint="give each one a different number so the order is unambiguous",
                )
            prefixes.setdefault(prefix, path)
        # Unprefixed names sort after every prefixed one.
        children.append((int(prefix) if prefix is not None else None, slug, path, slug))

    children.sort(key=lambda item: (item[0] is None, item[0] or 0, item[1]))
    return [(path, slug) for _, _, path, slug in children]


def _parse_toml_config(path: Path, report: Report) -> ParsedFile | None:
    """``site.toml`` is plain TOML, with no front matter fences."""
    try:
        text = path.read_text(encoding="utf-8")
        meta = tomllib.loads(text)
    except (OSError, UnicodeDecodeError) as exc:
        report.error(path, f"cannot read this file: {exc}")
        return None
    except tomllib.TOMLDecodeError as exc:
        report.error(path, f"this file is not valid TOML: {exc}")
        return None
    return ParsedFile(path=path, meta=meta, body="", body_line=len(text.splitlines()) + 1)


def _normalise_base_url(url: str) -> str:
    if not url.startswith("/"):
        url = "/" + url
    if not url.endswith("/"):
        url += "/"
    return url
