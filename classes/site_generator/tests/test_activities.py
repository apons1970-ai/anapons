"""The seven activity parsers (spec section 6)."""

from __future__ import annotations

import pytest
from conftest import errors, has_message

from aula.activities import ACTIVITY_TYPES, SHUFFLE_BY_DEFAULT


def test_the_type_set_is_closed_and_matches_the_spec():
    assert set(ACTIVITY_TYPES) == {
        "vocabulario",
        "opcion",
        "huecos",
        "pareja",
        "orden",
        "libre",
        "nota",
    }
    assert set(SHUFFLE_BY_DEFAULT) <= set(ACTIVITY_TYPES)


# --------------------------------------------------------------------------- opcion


def test_opcion_reads_questions_options_and_help(parse):
    body, report = parse(
        "opcion",
        """
        una lámpara

        - [x] HAY
        - [ ] ESTAR

        > „una" ist ein unbestimmter Artikel.

        la lámpara

        - [ ] HAY
        - [x] ESTAR
        """,
    )

    assert not report.problems
    assert len(body.items) == 2
    first = body.items[0]
    assert first["pregunta"] == "una lámpara"
    assert [option["texto"] for option in first["opciones"]] == ["HAY", "ESTAR"]
    assert [option["correcta"] for option in first["opciones"]] == [True, False]
    assert first["ayuda"].startswith("„una")
    assert body.items[1]["ayuda"] == ""


def test_opcion_accepts_more_than_one_correct_option(parse):
    body, report = parse(
        "opcion",
        """
        ¿Cuáles son lugares?

        - [x] la cocina
        - [x] el baño
        - [ ] la nevera
        """,
    )

    assert not report.problems
    assert sum(option["correcta"] for option in body.items[0]["opciones"]) == 2


def test_opcion_without_a_correct_option_is_reported(parse):
    _, report = parse(
        "opcion",
        """
        una lámpara

        - [ ] HAY
        - [ ] ESTAR
        """,
    )

    assert has_message(report, "has no correct option")
    assert "[x]" in errors(report)[0].hint


def test_opcion_with_a_single_option_is_reported(parse):
    _, report = parse("opcion", "una lámpara\n\n- [x] HAY\n")

    assert has_message(report, "needs at least two options")


def test_opcion_reports_a_badly_written_option_on_its_own_line(parse):
    _, report = parse(
        "opcion",
        """
        una lámpara

        - [x] HAY
        - ESTAR
        """,
    )

    assert has_message(report, "must start with [ ] or [x]")
    assert errors(report)[0].line == 8


def test_opcion_reports_options_with_no_question(parse):
    _, report = parse("opcion", "- [x] HAY\n- [ ] ESTAR\n")

    assert has_message(report, "do not belong to any question")


def test_opcion_reports_help_with_no_question(parse):
    _, report = parse("opcion", "> una explicación suelta\n")

    assert has_message(report, "does not belong to any question")


def test_opcion_with_an_empty_body_is_reported(parse):
    _, report = parse("opcion", "")

    assert has_message(report, "has no questions")


# --------------------------------------------------------------------------- huecos


def test_huecos_splits_text_and_gaps(parse):
    body, report = parse(
        "huecos",
        """
        Yo {estudio} español. (estudiar)
        > Ich lerne Spanisch.
        """,
    )

    assert not report.problems
    item = body.items[0]
    assert item["partes"] == [
        {"tipo": "texto", "texto": "Yo "},
        {"tipo": "hueco", "respuestas": ["estudio"]},
        {"tipo": "texto", "texto": " español. (estudiar)"},
    ]
    assert item["ayuda"] == "Ich lerne Spanisch."


def test_huecos_accepts_alternatives_in_order(parse):
    body, _ = parse("huecos", "Leo y Anna {comparten|se reparten} la habitación.")

    assert body.items[0]["partes"][1]["respuestas"] == ["comparten", "se reparten"]


def test_huecos_accepts_several_gaps_on_one_line(parse):
    body, report = parse("huecos", "En la pared {hay} tres fotos y {están} bien.")

    assert not report.problems
    gaps = [part for part in body.items[0]["partes"] if part["tipo"] == "hueco"]
    assert [gap["respuestas"] for gap in gaps] == [["hay"], ["están"]]


def test_huecos_help_attaches_to_the_sentence_above_it(parse):
    body, _ = parse(
        "huecos",
        """
        Yo {estudio} español.
        Tú {lees} mucho.
        > Du liest viel.
        """,
    )

    assert body.items[0]["ayuda"] == ""
    assert body.items[1]["ayuda"] == "Du liest viel."


def test_huecos_escaped_braces_stay_literal(parse):
    body, report = parse("huecos", r"Se escribe \{así\} y {aquí} no.")

    assert not report.problems
    texts = [part["texto"] for part in body.items[0]["partes"] if part["tipo"] == "texto"]
    assert "{así}" in "".join(texts)


def test_huecos_reports_an_unclosed_gap(parse):
    _, report = parse("huecos", "Yo {estudio español.")

    assert has_message(report, "never closed")


def test_a_broken_gap_is_reported_once_not_twice(parse):
    _, report = parse("huecos", "Yo {estudio español.\nTú {lees} mucho.")

    # Without the guard this line also trips the "has no gap" check.
    assert len(errors(report)) == 1


def test_huecos_reports_a_stray_closing_brace(parse):
    _, report = parse("huecos", "Yo estudio} español.")

    assert has_message(report, "closing brace with no opening one")


def test_huecos_reports_an_empty_gap(parse):
    _, report = parse("huecos", "Yo {} español.")

    assert has_message(report, "this gap is empty")


def test_huecos_reports_a_sentence_with_no_gap(parse):
    _, report = parse("huecos", "Yo estudio español.")

    assert has_message(report, "has no gap")


# --------------------------------------------------------------------------- pareja


def test_pareja_reads_pairs(parse):
    body, report = parse(
        "pareja",
        """
        - encima de = debajo de
        - delante de = detrás de
        """,
    )

    assert not report.problems
    assert [(pair["izquierda"], pair["derecha"]) for pair in body.items] == [
        ("encima de", "debajo de"),
        ("delante de", "detrás de"),
    ]


def test_pareja_accepts_lines_without_a_list_marker(parse):
    body, report = parse("pareja", "encima de = debajo de\ndelante de = detrás de")

    assert not report.problems
    assert len(body.items) == 2


def test_pareja_reports_a_line_that_is_not_a_pair(parse):
    _, report = parse("pareja", "- encima de = debajo de\n- delante de")

    assert has_message(report, "is not a pair")


def test_pareja_reports_a_repeated_left_hand_side(parse):
    _, report = parse(
        "pareja",
        """
        - encima de = debajo de
        - Encima de = arriba de
        """,
    )

    assert has_message(report, "appears on the left twice")


def test_pareja_needs_at_least_two_pairs(parse):
    _, report = parse("pareja", "- encima de = debajo de")

    assert has_message(report, "at least two pairs")


# --------------------------------------------------------------------------- orden


def test_orden_splits_a_sentence_into_pieces(parse):
    body, report = parse("orden", "En mi habitación hay tres fotos.")

    assert not report.problems
    assert body.items[0]["piezas"] == ["En", "mi", "habitación", "hay", "tres", "fotos."]


def test_orden_keeps_bracketed_chunks_together(parse):
    body, _ = parse("orden", "La cama está [al lado de] la ventana.")

    assert "al lado de" in body.items[0]["piezas"]
    assert "lado" not in body.items[0]["piezas"]


def test_orden_attaches_help_to_the_sentence(parse):
    body, _ = parse(
        "orden",
        """
        La cama está cerca.
        > Das Bett steht in der Nähe.
        """,
    )

    assert body.items[0]["ayuda"] == "Das Bett steht in der Nähe."


def test_orden_reports_a_sentence_that_is_too_short(parse):
    _, report = parse("orden", "Hay pan.")

    assert has_message(report, "too few parts to order")


def test_orden_reports_an_unclosed_group(parse):
    _, report = parse("orden", "La cama está [al lado de la ventana.")

    assert has_message(report, "never closed")


# ---------------------------------------------------------------------- vocabulario


def test_vocabulario_groups_entries_under_headings(parse):
    body, report = parse(
        "vocabulario",
        """
        ## Lugares

        la cocina = die Küche
        el baño = das Badezimmer

        ## Localización

        encima de = auf / über
        """,
    )

    assert not report.problems
    assert [group["titulo"] for group in body.items] == ["Lugares", "Localización"]
    assert body.items[0]["entradas"][1] == {
        "es": "el baño",
        "de": "das Badezimmer",
        "linea": 8,
    }


def test_vocabulario_allows_entries_before_any_heading(parse):
    body, report = parse("vocabulario", "la cocina = die Küche")

    assert not report.problems
    assert body.items[0]["titulo"] == ""
    assert len(body.items[0]["entradas"]) == 1


def test_vocabulario_allows_an_entry_with_no_translation(parse):
    body, report = parse("vocabulario", "la cocina")

    assert not report.problems
    assert body.items[0]["entradas"][0] == {"es": "la cocina", "de": "", "linea": 5}


def test_vocabulario_warns_about_an_empty_group(parse):
    _, report = parse("vocabulario", "## Lugares\n\n## Objetos\n\nla nevera = der Kühlschrank")

    assert has_message(report, 'the group "Lugares" has no words in it')
    assert report.problems[0].severity == "warning"


def test_vocabulario_with_no_entries_is_reported(parse):
    _, report = parse("vocabulario", "## Lugares")

    assert has_message(report, "has no words")


# ----------------------------------------------------------------------- libre, nota


def test_libre_keeps_the_prompt_and_the_model_apart(parse):
    body, report = parse(
        "libre",
        """
        Piensa en tu habitación.

        ::: modelo
        En la habitación hay una cama.
        :::
        """,
    )

    assert not report.problems
    assert [segment.label for segment in body.prose] == ["", "modelo"]
    assert body.prose[1].text == "En la habitación hay una cama."


def test_libre_reports_a_second_model(parse):
    _, report = parse(
        "libre",
        """
        ::: modelo
        uno
        :::

        ::: modelo
        dos
        :::
        """,
    )

    assert has_message(report, "more than one ::: modelo block")


def test_libre_rejects_a_german_container(parse):
    _, report = parse("libre", "::: de\nText\n:::")

    assert has_message(report, "cannot be used in a libre activity")


def test_nota_keeps_german_blocks(parse):
    body, report = parse(
        "nota",
        """
        **¿Qué hay? → HAY**

        ::: de
        Frage nach der Existenz → HAY.
        :::
        """,
    )

    assert not report.problems
    assert [segment.label for segment in body.prose] == ["", "de"]


def test_nota_rejects_a_model_container(parse):
    _, report = parse("nota", "::: modelo\ntexto\n:::")

    assert has_message(report, "cannot be used in a nota activity")


def test_empty_nota_is_reported(parse):
    _, report = parse("nota", "")

    assert has_message(report, "is empty")


# ------------------------------------------------------------------------- shared


@pytest.mark.parametrize("tipo", ["opcion", "huecos", "pareja", "orden", "vocabulario"])
def test_structured_types_reject_containers(tipo, parse):
    _, report = parse(tipo, "::: de\nText\n:::")

    assert has_message(report, "cannot be used in a")


def test_line_numbers_are_relative_to_the_whole_file(parse):
    _, report = parse(
        "huecos",
        """
        Yo {estudio} español.
        Tú lees mucho.
        """,
    )

    # +++ / tipo / +++ / blank, then the body: the bad line is the sixth.
    assert errors(report)[0].line == 6
