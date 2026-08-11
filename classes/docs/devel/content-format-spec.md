# Content format specification — v1

Status: draft for review
Audience: developers of the `aula` site generator

This document defines the on-disk content format that the generator consumes: the directory
structure, the metadata fields, and the markdown-like syntax for activities.

It is a **developer** document, written in English. All the *keys and values the author writes*
are in Spanish, because the author is a Spanish teacher and must be able to read her own files.
A separate author-facing guide (in Spanish, with German examples) will be derived from this once
the format is settled.

## 1. Principles

1. **Content is data, never code.** No file in `content/` is executable. A malformed file
   produces a build error naming the file, the line and the problem. It can never produce a
   broken page.
2. **Every content file is valid Markdown and renders legibly on github.com.** The author edits
   in the GitHub web UI; the diff and the preview must both be readable. This constrains the
   activity syntax to things Markdown already renders (lists, blockquotes, headings).
3. **Presentation lives in templates, never in content.** No HTML, no CSS class names in
   `content/`.
4. **One mechanism per job.** Ordering is filename prefixes and nothing else. Language is the
   `_de` suffix and nothing else.
5. **The activity type set is closed and versioned.** Adding a type is a deliberate change to
   this spec plus a parser, a renderer and a checker. Content never invents a type.

## 2. Directory structure

```
classes/
  content/
    site.toml
    6G/
      _indice.md
      01-primer-semestre-a/
        _indice.md
        01-la-casa/
          _indice.md
          01-contrarios.md
          02-donde-esta-el-gato.md
          03-hay-estar.md
        02-el-presente/
          _indice.md
          01-ar-er-ir.md
      02-primer-semestre-b/
        _indice.md
    7G/
      _indice.md
  site/                 # build output, git-ignored
  site_generator/       # the `aula` package
  docs/
```

Exactly three nesting levels below `content/`, fixed:

| Level | Directory | Meaning | Example |
|---|---|---|---|
| 1 | `6G/` | **curso** — a class group | Clase 6G |
| 2 | `01-primer-semestre-a/` | **semestre** — a block of the year | Primer semestre A |
| 3 | `01-la-casa/` | **leccion** — one topic | La casa y la localización |

Inside a lesson directory there is no further nesting: every `.md` file other than `_indice.md`
is one **actividad**.

### 2.1 Reserved filenames

- `_indice.md` — describes the directory it lives in. Required at every level. Its body is the
  page's own prose (course intro, semester intro, grammar explanation).
- `site.toml` — global configuration, only at the root of `content/`.

Everything else in a lesson directory is an activity. Files starting with `.` are ignored.

### 2.2 Naming rules

- Directory and file names: lowercase ASCII letters, digits and hyphens only. **No accents, no
  ñ, no spaces, no uppercase** — except course directories, which are the class codes as written
  (`6G`, `7R`).
- Ordering comes from a numeric prefix: `01-`, `02-`, … Prefixes are stripped from the URL, so
  **renumbering never breaks a link**. Two files may not share a prefix within a directory.
  Names without a prefix sort after all prefixed ones, alphabetically.
- Course ordering is not by prefix; it is the explicit `cursos` list in `site.toml`. That list
  is also the whitelist: a course directory not listed is not built.

### 2.3 URLs

The slug of a directory is its name with the numeric prefix removed. Course slugs are lowercased.

```
content/6G/01-primer-semestre-a/01-la-casa/  ->  /6g/primer-semestre-a/la-casa/
```

Activities do not get their own URL; they are rendered into the lesson page in prefix order,
each with an anchor `#<activity-slug>` (`03-hay-estar.md` → `#hay-estar`).

The stable identifier used for progress storage in `localStorage` is the full slug path,
e.g. `6g/primer-semestre-a/la-casa/hay-estar`. It must not change when content is edited.

## 3. File format

Every `.md` file is TOML front matter delimited by `+++`, followed by a body.

```markdown
+++
tipo = "opcion"
titulo = "¿Dónde está el gato?"
+++

encima de

- [x] debajo de
- [ ] al lado de
```

Rules:

- The opening `+++` must be the first line of the file. No BOM, no leading blank lines.
- Front matter is TOML (`tomllib`). It is required, even if empty.
- Files are UTF-8, LF line endings.
- The body may be empty for types that do not need one.

`site.toml` is plain TOML with no body.

## 4. Bilingual content

Spanish is the target language; German is the students' language. There are exactly two
mechanisms, and no others:

**Short strings in front matter** — a `_de` suffixed sibling key:

```toml
titulo = "La casa y la localización"
titulo_de = "Das Haus und die Ortsangaben"
instruccion = "Elige la relación espacial correcta."
instruccion_de = "Wähle die passende Ortsangabe."
```

The German variant is always optional. If absent, only the Spanish is shown.

**Prose in bodies** — a fenced container:

```markdown
Con **HAY** hablamos de cosas indeterminadas.

::: de
Mit **HAY** spricht man über unbestimmte Dinge.
:::
```

`::: de` … `:::` marks a German-language block. The template renders it behind a language
toggle. Any Markdown is allowed inside. Containers do not nest.

**Per-item help inside activities** uses `>` blockquotes — see §6.

## 5. Metadata reference

### 5.1 `site.toml`

| Key | Type | Req. | Meaning |
|---|---|---|---|
| `version` | int | yes | Content format version. Must be `1`. |
| `titulo` | string | yes | Site title. |
| `titulo_de` | string | no | German site title. |
| `base_url` | string | yes | Path prefix on the host, e.g. `"/Proyecto-Aula/"`. |
| `cursos` | array of string | yes | Course directories to build, in display order. |

```toml
version = 1
titulo = "Clases de español paso a paso"
titulo_de = "Spanisch Schritt für Schritt"
base_url = "/Proyecto-Aula/"
cursos = ["6G", "7G", "5G", "6R", "7R"]
```

### 5.2 `_indice.md` — course level

| Key | Type | Req. | Meaning |
|---|---|---|---|
| `titulo` | string | yes | e.g. `"Clase 6G"`. |
| `titulo_de` | string | no | |
| `estado` | string | no | `"publicado"` (default) or `"borrador"`. |

### 5.3 `_indice.md` — semester level

Same as course level. Body is an optional intro shown above the lesson grid.

### 5.4 `_indice.md` — lesson level

| Key | Type | Req. | Meaning |
|---|---|---|---|
| `titulo` | string | yes | |
| `titulo_de` | string | no | |
| `categoria` | string | yes | `"vocabulario"`, `"gramatica"` or `"microbloque"`. Groups lessons on the semester page. |
| `icono` | string | no | A single emoji. |
| `etiquetas` | array of string | no | Free tags, lowercase-hyphen. Used for the future activity bank. |
| `estado` | string | no | `"publicado"` (default) or `"borrador"`. |

The body is the lesson explanation: Markdown, possibly with `::: de` blocks. It is rendered
above the activities.

### 5.5 Activity files

| Key | Type | Req. | Meaning |
|---|---|---|---|
| `tipo` | string | yes | One of the seven types in §6. |
| `titulo` | string | yes | |
| `titulo_de` | string | no | |
| `instruccion` | string | no | Shown under the title. |
| `instruccion_de` | string | no | |
| `nivel` | string | no | `"basico"` (default), `"repaso"` or `"desafio"`. |
| `barajar` | bool | no | Shuffle items/options. Default depends on type — see §6. |
| `etiquetas` | array of string | no | |
| `estado` | string | no | `"publicado"` (default) or `"borrador"`. |

### 5.6 `estado`

`estado = "borrador"` excludes the item from the build, along with everything below it. The
generator lists what it skipped. `aula build --borradores` includes drafts, watermarked, for
local preview. This gives the author a safe way to leave work in progress on `main`.

## 6. Activity types

The closed set for v1 is seven types. Shared conventions first.

### 6.1 Shared conventions

**Blocks.** An activity body is parsed as a sequence of *blocks*, where a block is a maximal run
of consecutive lines of the same kind: `paragraph`, `list` (lines starting with `-`),
`quote` (lines starting with `>`), `heading` (lines starting with `#`), `container`
(`:::` fenced). Blank lines separate blocks but are otherwise insignificant, so the author may
space things out or not.

**`>` is always "the help".** A blockquote attached to an item is the explanation or translation
revealed *after* the student answers. In practice it is written in German. This is the single
meaning of `>` across every type.

**Accents.** Comparison of typed answers is case-insensitive and whitespace-trimmed, but
**accent-sensitive**. An answer that is correct except for accents is not marked wrong: it gets a
distinct "casi — revisa los acentos" state. The author therefore writes `{está}` and never needs
to list `esta` as an alternative.

**Shuffling.** Where an activity has a fixed set of options, they are shuffled per page load
unless `barajar = false`. Default is `barajar = true` for `opcion`, `pareja` and `orden`;
set it to `false` when the order carries meaning (e.g. options `-AR` / `-ER` / `-IR`).

**Escaping.** `\{`, `\}`, `\[`, `\]` and `\=` are literals wherever those characters are
significant.

---

### 6.2 `opcion` — multiple choice

A question is a paragraph, followed by a list whose items begin `- [ ]` or `- [x]`, optionally
followed by a `>` help block. `[x]` marks a correct option. More than one `[x]` turns the
question into a multi-select (checkboxes instead of radios).

```markdown
+++
tipo = "opcion"
titulo = "Busca la pista"
instruccion = "Elige HAY o ESTAR."
instruccion_de = "Wähle HAY oder ESTAR."
barajar = false
+++

una lámpara

- [x] HAY
- [ ] ESTAR

> „una" ist ein unbestimmter Artikel → HAY.

la lámpara

- [ ] HAY
- [x] ESTAR

> „la" ist ein bestimmter Artikel → ESTAR.
```

Parsed as: `[{prompt, options: [{text, correct}], help}]`.

Errors: a question with no options; a question with no `[x]`; a list item that is neither
`[ ]` nor `[x]`; a `>` block with no preceding question.

---

### 6.3 `huecos` — gap fill

One item per line. `{...}` is a gap. `|` separates genuinely different acceptable answers (not
accent variants — see §6.1). An optional `>` line gives the German translation. Several gaps per
line are allowed. Parenthesised hints are just literal text.

```markdown
+++
tipo = "huecos"
titulo = "Ahora conjuga"
instruccion = "Completa con la forma correcta."
instruccion_de = "Ergänze mit der richtigen Form."
+++

Yo {estudio} español. (estudiar)
> Ich lerne Spanisch.

Mi hermana {lee} mucho. (leer)
> Meine Schwester liest viel.

Leo y Anna {comparten|se reparten} la habitación. (compartir)
```

The first alternative in a gap is the canonical answer, shown when the student asks to see the
solution. Input width is sized from the canonical answer's length.

Parsed as: `[{segments: [text|gap], answers: [[str]], help}]`.

Errors: unclosed `{`; an empty gap `{}`; a line with no gap; a `>` line with no preceding item.

---

### 6.4 `pareja` — matching

One pair per line, `left = right`, split on the **first** ` = ` (space-equals-space), so `=`
may appear inside either side. Written as a list for GitHub readability. The right column is
shuffled for the student; `barajar = false` turns matching into a simple ordered review.

```markdown
+++
tipo = "pareja"
titulo = "Contrarios"
instruccion = "Relaciona las parejas."
instruccion_de = "Ordne die Gegensätze zu."
+++

- encima de = debajo de
- delante de = detrás de
- dentro de = fuera de
```

Errors: a line with no ` = `; duplicate left-hand sides; fewer than two pairs.

---

### 6.5 `orden` — word order

One sentence per line, written correctly. The generator splits it into tokens on whitespace and
shuffles them. `[...]` keeps a chunk together as one token.

```markdown
+++
tipo = "orden"
titulo = "Ordena la frase"
instruccion = "Coloca las palabras en el orden correcto."
instruccion_de = "Bringe die Wörter in die richtige Reihenfolge."
+++

La cama está [al lado de] la ventana.
> Das Bett steht neben dem Fenster.

En mi habitación hay tres fotos.
```

Trailing punctuation stays attached to its token. A sentence of fewer than three tokens is an
error (nothing to order).

---

### 6.6 `vocabulario` — word list

Presentational, not interactive in v1, but structured so it can later feed flashcards. `##`
headings create groups; `es = de` lines are entries; the German side may be omitted. Splitting
is on the first ` = `, as in `pareja`.

```markdown
+++
tipo = "vocabulario"
titulo = "La casa"
instruccion = "Busca relaciones entre las palabras."
instruccion_de = "Finde Verbindungen zwischen den Wörtern."
+++

## Lugares

la cocina = die Küche
el baño = das Badezimmer

## Localización

encima de = auf / über
debajo de = unter
entre ... y ... = zwischen ... und ...
```

Entries before the first `##` go into an unnamed group. Errors: no entries.

---

### 6.7 `libre` — open writing

The body is the prompt, as Markdown. A `::: modelo` container holds a model answer, hidden
behind a button. Nothing is checked.

```markdown
+++
tipo = "libre"
titulo = "Describe tú"
instruccion = "Escribe al menos cuatro frases: dos con HAY y dos con ESTAR."
instruccion_de = "Schreibe mindestens vier Sätze."
+++

Piensa en tu habitación.

::: modelo
En la habitación hay una cama. Hay muchos libros.
La cama está junto a la ventana. Los libros están en la estantería.
:::
```

What the student types is kept in `localStorage` so it survives a refresh. At most one
`::: modelo` container.

---

### 6.8 `nota` — interstitial explanation

Plain Markdown rendered between activities, for the explain-practise-explain rhythm. `::: de`
allowed. `titulo` is optional for this type only.

```markdown
+++
tipo = "nota"
titulo = "Recuerda"
+++

**¿Qué hay? → HAY** · **¿Dónde está/están? → ESTAR**

::: de
Frage nach der Existenz → HAY. Frage nach dem Ort → ESTAR.
:::
```

## 7. Validation

`aula check` runs validation without building; `aula build` runs it first and refuses to emit
anything if it fails. Every message carries `path:line` and says what to do.

```
aula check --content DIR [--strict] [--format human|github]
aula build --content DIR --out DIR [--borradores] [--base-url URL]
aula serve --content DIR [--port N]      # local preview, watches and rebuilds
```

`--format github` emits `::error file=…,line=…::` annotations so that CI attaches each message
to the offending line in the GitHub diff view. `--base-url` overrides `site.toml`; `aula serve`
implies `--base-url /`.

The generator must detect, at minimum:

- **Structure** — missing `_indice.md`; nesting deeper or shallower than three levels; a course
  in `cursos` with no directory; a course directory not in `cursos` (warning); duplicate numeric
  prefixes; names with accents, spaces or uppercase.
- **Front matter** — missing or malformed `+++`; TOML syntax errors; unknown keys (error, not
  ignored — catches typos like `titolo`); missing required keys; wrong types; `tipo` not in the
  closed set; `categoria`/`nivel`/`estado` outside their allowed values; a `_de` key with no
  Spanish sibling.
- **Activity bodies** — every per-type error listed in §6, plus an empty body for a type that
  requires one.
- **Cross-file** — a lesson with no published activities (warning); `version` in `site.toml`
  not matching the generator's supported version (error).

Warnings do not fail the build; errors do. `aula check --strict` promotes warnings to errors,
which is what CI runs.

Example of the intended tone:

```
content/6G/01-primer-semestre-a/01-la-casa/02-donde-esta-el-gato.md:14
  error: this question has no correct option
  mark one of the options with [x]:
      - [x] entre ... y ...
```

## 8. Build output

`aula build` writes one directory per course, semester and lesson, each with an `index.html`;
assets under `assets/`. No JavaScript is required to read a lesson — only to interact with it.

Answers are present in the delivered HTML/JSON. This is accepted: the site is for self-study,
not for grading.

### 8.1 Deployment

The repository is a monorepo of several tools, published as a single GitHub Pages site.
`.github/workflows/pages.yml` assembles:

```
_site/
  index.html      <- www/index.html, the landing page
  CNAME           <- www/CNAME, the custom domain
  classes/        <- aula build --out _site/classes
  verbs/          <- the conjugation app, once migrated
```

The site is served from the apex domain **anapons.net**, so the repository root maps to the
domain root and `base_url` in `site.toml` is `/classes/`. Lessons end up at
`https://anapons.net/classes/6g/primer-semestre-a/la-casa/`.

`www/CNAME` is copied into the artifact on every build. It must stay in sync with the custom
domain configured in the repository's Settings → Pages; if the file is removed, Pages drops the
custom domain. DNS for the apex needs `A` records pointing at GitHub's Pages addresses (plus an
`AAAA` set for IPv6), and a `CNAME` record for `www` pointing at `<user>.github.io`.

The workflow runs on every push to `main` and on pull requests; only `main` deploys. A build
that fails validation does not deploy, so the live site always keeps the last good version.

The intended author workflow is to edit files directly on github.com and commit to `main`. If a
commit breaks validation, the site is unchanged and the error appears as a line annotation on
the commit.

## 9. Reserved for later

Deliberately specified now so the format does not have to change when we add them:

- **Activity bank / reuse.** An activity file containing only front matter with
  `usar = "6g/primer-semestre-a/la-casa/hay-estar"` includes another activity by its slug path,
  with local front matter overriding. Not implemented in v1; the key is reserved.
- **Media.** `audio = "audio/la-casa.mp3"` and `imagen = "img/cocina.jpg"` on activities and
  entries, resolved relative to an `_media/` directory inside the lesson. Reserved.
- **Printable worksheets.** Not in v1. The build already emits a machine-readable index of every
  activity, which is what a print view would consume.
- **More types.** `dictado` (listening), `flashcards` (from `vocabulario` entries),
  `conjugacion` (paradigm drill — overlaps with the existing verbs app, so it may stay there).

## 10. Version history

- **v1** — this document. Types: `vocabulario`, `opcion`, `huecos`, `pareja`, `orden`, `libre`,
  `nota`.
