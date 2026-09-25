---
doc: prd
status: approved
---

# PRD — Runs On

## User

A maintainer about to publish a release, or a reviewer looking at a pull request that modernises
syntax. They have a `requires-python` line they last thought about a year ago.

## The job

Answer one question before an installer does: *if someone installs this on the oldest Python you
claim to support, will it import?*

## Core loop

1. Read every declared floor: `requires-python` in `pyproject.toml`, `python_requires` in
   `setup.cfg` or `setup.py`, and the `Programming Language :: Python :: 3.x` classifiers.
2. Report a contradiction between them as a finding in its own right.
3. Decide which files actually ship, and parse each one.
4. Collect the constructs that carry a version floor, noting for each whether it sits inside a
   guard.
5. Compare against the declared floor, print the four groups, exit non-zero on a broken promise.

## What carries a version floor

Only constructs decidable from syntax, with no inference about types:

| Construct | Needs | Recognised from |
|---|---|---|
| `match` statement | 3.10 | `ast.Match` |
| `except*` | 3.11 | `ast.TryStar` |
| `type X = ...` | 3.12 | `ast.TypeAlias` |
| `def f[T](...)` | 3.12 | type parameters on a definition |
| walrus `:=` | 3.8 | `ast.NamedExpr` |
| positional-only `/` | 3.8 | `posonlyargs` |
| `X | Y` in a runtime annotation | 3.10 | `BitOr` inside an annotation |
| `list[int]` in a runtime annotation | 3.9 | subscript of a builtin container |
| `import tomllib`, `zoneinfo`, `graphlib`, … | per module | import statement |

Everything else is silent by design. `a | b` outside an annotation could be integers, sets, or a
custom `__or__`; `d1 | d2` could be anything. A tool that guessed there would be wrong on ordinary
code, which is the one failure that makes a checker worthless.

## What counts as a guard

- `if sys.version_info >= (3, N):` or `<` around the construct, in any enclosing block;
- `try: import X / except ImportError:` with a fallback;
- `if TYPE_CHECKING:` — the body is never evaluated at runtime;
- `from __future__ import annotations` in the module, which turns every annotation into a string
  and so removes the floor for annotation-only constructs.

## Acceptance criteria

1. A package declaring 3.9 with a bare `match` statement is *broken*, naming file, line and 3.10.
2. The same `match` under `if sys.version_info >= (3, 10):` is *guarded*, not broken.
3. `import tomllib` inside `try/except ImportError` is *guarded*.
4. `def f(x: int | None)` is *broken* at floor 3.9, and silent with
   `from __future__ import annotations`.
5. `a | b` in ordinary code is never reported, at any floor.
6. `requires-python = ">=3.8"` beside a `Python :: 3.10` classifier as the lowest is a
   contradiction finding.
7. A project with no declared floor is *not judged*, with that reason.
8. Exit codes: 0 clean, 1 broken promise, 2 unreadable repository.
9. On thirteen maintained public projects, nothing is reported as broken.

## Non-goals

Third-party dependency floors, type inference, autofix, non-Python projects, anything networked.

## Risks

- **Test and tooling files.** A `noxfile.py` or a test may legitimately use newer syntax than the
  package ships. Scanning them would produce findings no user could ever hit. Mitigated by scanning
  only what ships, and saying which directories that was.
- **Over-reporting annotations.** Mitigated by honouring `from __future__ import annotations` and
  `if TYPE_CHECKING:`.
