# aula

The static site generator for the Spanish lessons in [`../content/`](../content/).

It reads a tree of Markdown files with TOML front matter, validates them, and
writes a static site. The format is defined in
[`../docs/devel/content-format-spec.md`](../docs/devel/content-format-spec.md);
that document is the source of truth, and this package implements it.

## Using it

```sh
uv run aula check --content ../content              # validate, print what is wrong
uv run aula check --content ../content --strict     # warnings count as errors, as in CI
uv run aula build --content ../content --out ../site
```

`--format github` turns the messages into GitHub Actions annotations, so they land
on the offending line in the diff view. `--borradores` includes content marked
`estado = "borrador"`.

## Layout

| Module | What it does |
|---|---|
| `errors.py` | `Problem` and `Report`: how mistakes are collected and phrased |
| `frontmatter.py` | Splits `+++` TOML front matter; validates keys, types and choices |
| `blocks.py` | Scans a body into `:::` containers and runs of paragraphs, lists, quotes and headings |
| `activities.py` | One parser per activity type. The set is closed |
| `model.py` | The content tree: `Site`, `Curso`, `Semestre`, `Leccion`, `Actividad` |
| `loader.py` | Walks `content/`, validating as it goes |
| `cli.py` | `aula check` and `aula build` |

Loading and validating are a single pass, and a bad file never stops the walk: the
author should see every mistake in one run, not one per commit.

## Working on it

```sh
uv run pytest
uv run ruff check . && uv run ruff format .
```

Adding an activity type means, in order: amend the spec, add a parser in
`activities.py` with its errors, add tests, then add a renderer and a checker.
