"""Walking the content tree (spec section 2) and the cross-file checks."""

from __future__ import annotations

from pathlib import Path

from conftest import (
    ACTIVIDAD,
    CURSO_INDEX,
    LECCION_INDEX,
    SEMESTRE_INDEX,
    SITE_TOML,
    errors,
    has_message,
    warnings,
    write_tree,
)

from aula.errors import Report
from aula.loader import load_site
from aula.model import lesson_id

LESSON = "6G/01-primer-semestre-a/01-la-casa"


def test_loads_a_well_formed_tree(good_site: Path, report: Report):
    site = load_site(good_site, report)

    assert not report.problems
    assert site is not None
    assert site.titulo == "Clases de español"
    assert [curso.codigo for curso in site.cursos] == ["6G"]

    curso, semestre, leccion = next(site.walk())
    assert (curso.slug, semestre.slug, leccion.slug) == ("6g", "primer-semestre-a", "la-casa")
    assert leccion.categoria == "vocabulario"
    assert [actividad.slug for actividad in leccion.actividades] == ["contrarios"]
    assert leccion.actividades[0].tipo == "opcion"


def test_lesson_bodies_are_kept_as_prose(good_site: Path, report: Report):
    site = load_site(good_site, report)
    _, _, leccion = next(site.walk())

    assert leccion.prose[0].text.startswith("Con **HAY**")


def test_lesson_id_is_the_slug_path(good_site: Path, report: Report):
    site = load_site(good_site, report)

    assert lesson_id(*next(site.walk())) == "6g/primer-semestre-a/la-casa"


def test_base_url_is_normalised(tmp_path: Path, report: Report):
    content = write_tree(
        tmp_path / "content",
        {
            "site.toml": SITE_TOML.replace('"/classes/"', '"classes"'),
            "6G/_indice.md": CURSO_INDEX,
            "6G/01-primer-semestre-a/_indice.md": SEMESTRE_INDEX,
            "6G/01-primer-semestre-a/01-la-casa/_indice.md": LECCION_INDEX,
            f"{LESSON}/01-contrarios.md": ACTIVIDAD,
        },
    )
    site = load_site(content, report)

    assert site.base_url == "/classes/"


def test_activities_follow_the_numeric_prefix_not_the_alphabet(good_site: Path, report: Report):
    write_tree(
        good_site,
        {
            f"{LESSON}/02-zeta.md": ACTIVIDAD,
            f"{LESSON}/10-alfa.md": ACTIVIDAD,
            f"{LESSON}/03-beta.md": ACTIVIDAD,
        },
    )
    site = load_site(good_site, report)
    _, _, leccion = next(site.walk())

    assert [actividad.slug for actividad in leccion.actividades] == [
        "contrarios",
        "zeta",
        "beta",
        "alfa",
    ]


def test_unprefixed_names_sort_after_prefixed_ones(good_site: Path, report: Report):
    write_tree(good_site, {f"{LESSON}/aparte.md": ACTIVIDAD, f"{LESSON}/09-nueve.md": ACTIVIDAD})
    site = load_site(good_site, report)
    _, _, leccion = next(site.walk())

    assert [actividad.slug for actividad in leccion.actividades][-1] == "aparte"


def test_repeated_prefix_is_reported(good_site: Path, report: Report):
    write_tree(good_site, {f"{LESSON}/01-otra.md": ACTIVIDAD})
    load_site(good_site, report)

    assert has_message(report, "is already used by")


def test_name_with_accents_or_capitals_is_reported(good_site: Path, report: Report):
    write_tree(good_site, {f"{LESSON}/02-La-Casá.md": ACTIVIDAD})
    load_site(good_site, report)

    assert has_message(report, "is not a valid name")
    assert "no accents" in errors(report)[0].hint


def test_missing_index_is_reported(good_site: Path, report: Report):
    (good_site / LESSON / "_indice.md").unlink()
    load_site(good_site, report)

    assert has_message(report, "has no _indice.md")


def test_missing_site_config_is_reported(tmp_path: Path, report: Report):
    content = write_tree(tmp_path / "content", {"6G/_indice.md": CURSO_INDEX})

    assert load_site(content, report) is None
    assert has_message(report, "there is no site.toml")


def test_course_listed_without_a_folder_is_reported(good_site: Path, report: Report):
    (good_site / "site.toml").write_text(
        SITE_TOML.replace('["6G"]', '["6G", "7G"]'), encoding="utf-8"
    )
    load_site(good_site, report)

    assert has_message(report, 'cursos lists "7G", but there is no folder')


def test_unlisted_folder_only_warns(good_site: Path, report: Report):
    write_tree(good_site, {"7G/_indice.md": CURSO_INDEX})
    load_site(good_site, report)

    assert not errors(report)
    assert has_message(report, "is not listed in cursos")


def test_unsupported_content_version_is_reported(good_site: Path, report: Report):
    (good_site / "site.toml").write_text(
        SITE_TOML.replace("version = 1", "version = 2"), encoding="utf-8"
    )
    load_site(good_site, report)

    assert has_message(report, "the site generator understands version 1")


def test_drafts_are_left_out_unless_asked_for(good_site: Path, report: Report):
    write_tree(
        good_site,
        {f"{LESSON}/_indice.md": LECCION_INDEX.replace("+++\n\n", 'estado = "borrador"\n+++\n\n')},
    )

    site = load_site(good_site, report)
    assert list(site.walk()) == []

    included = load_site(good_site, Report(root=good_site), include_drafts=True)
    assert len(list(included.walk())) == 1


def test_draft_activity_is_left_out(good_site: Path, report: Report):
    write_tree(
        good_site,
        {f"{LESSON}/02-borrador.md": ACTIVIDAD.replace("+++\n\n", 'estado = "borrador"\n+++\n\n')},
    )
    site = load_site(good_site, report)
    _, _, leccion = next(site.walk())

    assert [actividad.slug for actividad in leccion.actividades] == ["contrarios"]


def test_lesson_with_no_activities_only_warns(good_site: Path, report: Report):
    (good_site / LESSON / "01-contrarios.md").unlink()
    load_site(good_site, report)

    assert not errors(report)
    assert has_message(report, "has no published activities")


def test_stray_files_and_folders_are_ignored_with_a_warning(good_site: Path, report: Report):
    write_tree(good_site, {f"{LESSON}/notas.txt": "algo", "6G/leeme.md": "algo"})
    load_site(good_site, report)

    assert not errors(report)
    assert has_message(report, "only .md files are used here")
    assert has_message(report, "expected a folder here but found a file")


def test_dot_files_are_ignored_silently(good_site: Path, report: Report):
    write_tree(good_site, {f"{LESSON}/.DS_Store": ""})
    load_site(good_site, report)

    assert not report.problems


def test_shuffle_defaults_come_from_the_type(good_site: Path, report: Report):
    write_tree(
        good_site,
        {f"{LESSON}/02-palabras.md": '+++\ntipo = "vocabulario"\ntitulo = "x"\n+++\n\nla cocina\n'},
    )
    site = load_site(good_site, report)
    _, _, leccion = next(site.walk())
    barajar = {actividad.tipo: actividad.barajar for actividad in leccion.actividades}

    assert barajar == {"opcion": True, "vocabulario": False}


def test_explicit_shuffle_setting_wins(good_site: Path, report: Report):
    write_tree(
        good_site,
        {f"{LESSON}/01-contrarios.md": ACTIVIDAD.replace("+++\n\n", "barajar = false\n+++\n\n")},
    )
    site = load_site(good_site, report)
    _, _, leccion = next(site.walk())

    assert leccion.actividades[0].barajar is False


def test_unknown_activity_type_is_reported(good_site: Path, report: Report):
    write_tree(good_site, {f"{LESSON}/02-raro.md": '+++\ntipo = "crucigrama"\ntitulo = "x"\n+++\n'})
    load_site(good_site, report)

    assert has_message(report, "not one of the allowed values")
    assert "vocabulario" in errors(report)[0].hint


def test_one_broken_file_does_not_hide_the_next(good_site: Path, report: Report):
    write_tree(
        good_site,
        {
            f"{LESSON}/02-uno.md": '+++\ntipo = "opcion"\ntitulo = "a"\n+++\n\npregunta\n\n- [ ] a\n- [ ] b\n',
            f"{LESSON}/03-dos.md": '+++\ntipo = "pareja"\ntitulo = "b"\n+++\n\n- solo una linea\n',
        },
    )
    load_site(good_site, report)
    reported = {problem.path.name for problem in errors(report)}

    assert reported == {"02-uno.md", "03-dos.md"}


def test_warnings_alone_do_not_count_as_errors(good_site: Path, report: Report):
    write_tree(good_site, {"7G/_indice.md": CURSO_INDEX})
    load_site(good_site, report)

    assert warnings(report)
    assert not report.has_errors()
    assert report.has_errors(strict=True)
