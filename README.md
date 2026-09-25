# Runs On

A package declares `requires-python = ">=3.9"`. This reads the code that ships and asks whether
that promise is true.

```bash
./run.sh --repo .
```

Get the floor wrong and `pip` cheerfully installs your package on a Python that cannot import it.
The failure lands on a stranger, at import time, as a `SyntaxError` that names your file and not
the reason. Tests run on the developer's Python. CI runs the versions in the matrix, usually the
same set. The declared floor is a number in a file nobody re-derives after a refactor adds a
`match` statement.

Four groups, and the last two matter as much as the first:

- **breaks its promise** — an unguarded construct needs a newer Python, with file, line and version;
- **guarded** — a newer construct is there, but behind `sys.version_info`, a `try/except
  ImportError` fallback, `if TYPE_CHECKING:`, or `from __future__ import annotations`;
- **contradiction** — the project states two different floors in two different places;
- **not judged** — a file that would not parse, or a project that declares no floor at all.

Exits non-zero on a broken promise. No dependencies, no network, and it never imports or executes
the package under test.

## On real repositories

Thirty maintained Python projects, 1 060 shipped files, nothing reported broken:

| project | promises | files | broken | guarded |
|---|---|---|---|---|
| poetry | 3.10 | 193 | 0 | 1 |
| sqlmodel | 3.10 | 166 | 0 | 0 |
| pendulum | 3.10 | 120 | 0 | 0 |
| rich | 3.9 | 100 | 0 | 0 |
| werkzeug | 3.10 | 54 | 0 | 0 |
| apscheduler | 3.10 | 45 | 0 | 0 |
| black | 3.10 | 41 | 0 | 1 |
| mkdocs | 3.8 | 35 | 0 | 0 |
| urllib3 | 3.10 | 35 | 0 | 0 |
| typer | 3.10 | 32 | 0 | 0 |
| tqdm | 3.8 | 31 | 0 | 0 |
| jinja | 3.10 | 25 | 0 | 0 |
| httpx | 3.9 | 23 | 0 | 0 |
| loguru | 3.5 | 19 | 0 | 2 |
| arrow | 3.8 | 10 | 0 | 1 |
| …and 15 more | | | 0 | 0 |
| **total** | | **1 060** | **0** | **5** |

Reproduce with `./demo/scan.sh`.

Those five guarded findings are the point. Before writing any of this I probed the idea with a
throwaway script, and it immediately reported `import tomllib` as a broken promise in **black** and
**poetry**. Both were wrong: black wraps it in `try/except ImportError`, poetry in
`if sys.version_info < (3, 11)`. That pair of false positives is what the guard analysis was built
from, and the tool now names them as guarded rather than accusing them.

## The other direction

Remove the guard, exactly as a cleanup commit would:

```
$ sed -i '/version_info < (3, 11)/,+4c\import tomllib' src/poetry/utils/_compat.py
$ runs-on --repo poetry --quiet
BREAKS ITS PROMISE  1
  src/poetry/utils/_compat.py:11  import tomllib
      needs 3.11, this package promises 3.10
exit 1
```

## Asking what-if

`--floor` answers the question a maintainer actually has — *can I still support this?* — without
editing any metadata:

```
$ runs-on --repo requests --floor 3.8 --quiet
BREAKS ITS PROMISE  6
  src/requests/_internal_utils.py:26  X | Y in a runtime annotation
      needs 3.10, this package promises 3.8
  src/requests/help.py:67  dict[…] in a runtime annotation
      needs 3.9, this package promises 3.8
```

`rich` can drop to 3.8 with nothing broken, and to 3.7 with seven things broken — all walrus
operators, each with its line.

## What carries a version floor

Only constructs decidable from the syntax tree, with no inference about what a name refers to:

| Construct | Needs |
|---|---|
| `match` statement | 3.10 |
| `except*` | 3.11 |
| `type X = …`, `def f[T](…)` | 3.12 |
| `X \| Y` in a runtime annotation | 3.10 |
| `list[int]` in a runtime annotation | 3.9 |
| walrus `:=`, positional-only `/` | 3.8 |
| f-string, variable annotation | 3.6 |
| `import tomllib`, `zoneinfo`, `graphlib`, … | per module |

Everything else is silent by design. `a | b` outside an annotation could be integers, sets, or a
class with its own `__or__`; `d1 | d2` could be anything. A checker that guessed there would be
wrong on ordinary correct code, which is the one failure it cannot afford.

## Usage

```bash
./run.sh --repo .                  # the declared floor
./run.sh --repo . --floor 3.8      # a what-if
./run.sh --repo . --include-tests  # also read tests and tooling, which never ship
./run.sh --repo . --json
./run.sh --repo . --quiet
```

| Exit code | Meaning |
|---|---|
| 0 | the promise holds |
| 1 | something needs a newer Python than the package claims |
| 2 | the repository could not be read, or ships no Python package |

## Tests

```bash
PYTHONPATH=src python3 -m pytest tests -q      # 30 tests, no network
```

Each test writes the package it is about into a temporary directory, so every assertion is about
source the test itself created: both directions of every guard, one case per construct, and the
rule that `a | b` outside an annotation is never reported.

## Honest limits

- **It reads what ships, not what runs.** Code reached through `exec`, a plugin, or a generated
  file is invisible.
- **It reads syntax and imports, not attribute access.** This one is not hypothetical: the first
  time this tool was run under Python 3.9 — the version its own `pyproject.toml` promises — it
  crashed on `ast.Match`, which does not exist before 3.10. Its own check had been silent, because
  a missing attribute is not a syntax error. The fix is in `features.py`; the lesson is in this
  paragraph.
- **It says nothing about your dependencies.** Whether *they* support your floor is a larger
  question.
- **The floor is read as text**, from `pyproject.toml`, `setup.cfg`, `setup.py` and the trove
  classifiers. A floor computed at build time by a plugin is not seen.

MIT licensed. Planned with the Devpost Learn skill pack; `devpost/` holds the scope, PRD and spec
written before the code.
