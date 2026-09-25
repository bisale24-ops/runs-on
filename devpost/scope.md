---
doc: scope
status: approved
---

# Scope — Does this actually run on the Python you promise?

## The idea in one line

A package declares `requires-python = ">=3.9"`. This reads the code that ships and asks whether
that promise is true.

## Why this one

`requires-python` is a contract with the installer. Get it wrong and `pip` cheerfully installs your
package on a Python that cannot import it — the failure lands on a stranger, at import time, with a
`SyntaxError` that names your file and not the reason.

Nothing in the normal pipeline catches it. Tests run on the developer's Python. CI runs on the
versions the matrix lists, which is usually the same set. The declared floor is a number in a file
that no one re-derives after a refactor adds a `match` statement.

## The claim and the evidence

The claim is a version. The evidence is syntax: a `match` statement needs 3.10, `except*` needs
3.11, `import tomllib` needs 3.11, `list[int]` evaluated at runtime needs 3.9. Each of those is
decidable from the syntax tree alone, with no inference about types and nothing executed.

## Three verdicts

- **keeps its promise** — nothing that ships needs more than the floor it declares.
- **breaks its promise** — an unguarded construct needs a newer Python, named with file, line and
  the version it requires.
- **guarded** — a newer construct is there, but behind `sys.version_info`, a `try/except
  ImportError` fallback, `if TYPE_CHECKING:`, or `from __future__ import annotations`. Reported so
  the reader can see the tool looked, and counted as fine.

A fourth list, **not judged**, holds files that do not parse and projects that declare no floor at
all, with the reason.

## What "done" means for the proof of concept

- Runs on any local repository. No install of the project, nothing imported, nothing executed.
- On a maintained project with an honest floor, nothing is reported.
- A `match` statement added to a package declaring 3.9 is caught, with file and line.
- The same construct behind `if sys.version_info >= (3, 10):` is reported as guarded, not broken.
- Two declared floors that contradict each other — `requires-python` against the trove classifiers
  — are reported, because a package that promises two different things is already wrong.
- Exits non-zero on a broken promise.

## Deliberately out of scope

- Type inference. `a | b` is only a version signal inside an annotation, where the operands are
  types by construction; anywhere else this tool says nothing.
- Third-party dependencies. Whether *they* support your floor is a different, larger question.
- Raising the floor for you, or editing any file.
- Anything needing the network or a package index.

## Why it is a proof of concept

It sees the code that ships, not the code that runs. A package that reaches a newer construct
through `exec`, a plugin, or a generated file is invisible to it, and the report says so.
