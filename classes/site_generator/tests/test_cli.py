"""The command line surface (spec section 7)."""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import ACTIVIDAD, write_tree

from aula.cli import main

LESSON = "6G/01-primer-semestre-a/01-la-casa"


def test_check_passes_on_a_good_tree(good_site: Path, capsys):
    assert main(["check", "--content", str(good_site)]) == 0
    assert "all good" in capsys.readouterr().out


def test_check_counts_what_it_found(good_site: Path, capsys):
    main(["check", "--content", str(good_site)])

    assert "1 courses, 1 lessons, 1 activities" in capsys.readouterr().out


def test_check_fails_on_a_broken_activity(good_site: Path, capsys):
    write_tree(good_site, {f"{LESSON}/01-contrarios.md": ACTIVIDAD.replace("[x]", "[ ]")})

    assert main(["check", "--content", str(good_site)]) == 1
    assert "has no correct option" in capsys.readouterr().err


def test_messages_name_the_file_relative_to_the_content_folder(good_site: Path, capsys):
    write_tree(good_site, {f"{LESSON}/01-contrarios.md": ACTIVIDAD.replace("[x]", "[ ]")})
    main(["check", "--content", str(good_site)])

    assert f"content/{LESSON}/01-contrarios.md:" in capsys.readouterr().err


def test_warnings_alone_pass_but_fail_under_strict(good_site: Path):
    write_tree(good_site, {"7G/_indice.md": '+++\ntitulo = "Clase 7G"\n+++\n'})

    assert main(["check", "--content", str(good_site)]) == 0
    assert main(["check", "--content", str(good_site), "--strict"]) == 1


def test_github_format_emits_annotations(good_site: Path, capsys):
    write_tree(good_site, {f"{LESSON}/01-contrarios.md": ACTIVIDAD.replace("[x]", "[ ]")})
    main(["check", "--content", str(good_site), "--format", "github"])

    err = capsys.readouterr().err
    assert err.startswith("::error file=")
    assert f"file=content/{LESSON}/01-contrarios.md,line=" in err
    # Annotations are one per line; the hint must be percent-encoded onto it.
    assert "%0A" in err
    assert all(line.startswith("::") for line in err.splitlines())


def test_github_format_marks_warnings_as_errors_under_strict(good_site: Path, capsys):
    write_tree(good_site, {"7G/_indice.md": '+++\ntitulo = "Clase 7G"\n+++\n'})

    main(["check", "--content", str(good_site), "--format", "github"])
    assert capsys.readouterr().err.startswith("::warning ")

    main(["check", "--content", str(good_site), "--format", "github", "--strict"])
    assert capsys.readouterr().err.startswith("::error ")


def test_drafts_can_be_included(good_site: Path, capsys):
    write_tree(
        good_site,
        {f"{LESSON}/02-borrador.md": ACTIVIDAD.replace("+++\n\n", 'estado = "borrador"\n+++\n\n')},
    )

    main(["check", "--content", str(good_site)])
    assert "1 activities" in capsys.readouterr().out

    main(["check", "--content", str(good_site), "--borradores"])
    assert "2 activities" in capsys.readouterr().out


def test_missing_content_directory_is_reported(tmp_path: Path, capsys):
    assert main(["check", "--content", str(tmp_path / "nope")]) == 2
    assert "there is no content directory" in capsys.readouterr().err


def test_a_command_is_required(capsys):
    with pytest.raises(SystemExit):
        main([])
