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
uv run aula serve --content ../content       # preview at localhost:8000, rebuilds on save
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
| `render.py` | Templating, Markdown and the write-out of every page |
| `templates/` | Jinja templates: page layouts and one per activity type |
| `assets/` | `aula.css` and `aula.js`, copied into the site as they are |
| `cli.py` | `aula check`, `aula build` and `aula serve` |

Loading and validating are a single pass, and a bad file never stops the walk: the
author should see every mistake in one run, not one per commit.

## Working on it

```sh
uv run pytest
uv run ruff check . && uv run ruff format .
```

Adding an activity type means, in order: amend the spec, add a parser in
`activities.py` with its errors, add a template under `templates/actividades/`,
add its behaviour to `preparadores` in `aula.js`, and add tests for each.

The HTML is complete without JavaScript: a lesson with scripts blocked is still
readable. Everything in `aula.js` is an addition on top — shuffling, checking,
revealing the German help, remembering progress in `localStorage`.
