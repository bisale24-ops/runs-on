---
doc: spec
status: approved
---

# Spec — Runs On

## Command

```
runs-on [--repo PATH] [--floor X.Y] [--include-tests] [--json] [--quiet]
```

`--floor` overrides the declared floor, for answering "could I claim 3.9?" without editing
metadata.

## Modules

| Module | Responsibility |
|---|---|
| `declared.py` | Every floor the project states, and any contradiction between them. |
| `shipped.py` | Which files ship: packages from the build metadata, else top-level packages; tests, docs, CI and tooling excluded unless asked for. |
| `features.py` | Walk one module, yield `Feature(name, needs, line, guarded, reason)`. |
| `guards.py` | Decide whether a node sits under a version check, an import fallback, or `TYPE_CHECKING`. |
| `report.py` | Four groups, summary line, `--json`, exit code. |
| `cli.py` | Arguments and orchestration. |

## Data

```python
Declared = (floor, sources)            # sources: [(where, version)]
Feature  = (name, needs, path, line, guarded, guard_reason)
```

## Rules

1. The floor is the **highest** lower bound stated anywhere, because a project that says both
   `>=3.8` and `Python :: 3.10` has promised the lower one to pip and the higher one to a reader.
   The contradiction is reported and the comparison uses the lowest, since that is what installs.
2. Annotation constructs (`X | Y`, `list[int]`) are skipped entirely when the module has
   `from __future__ import annotations`, and when they sit under `if TYPE_CHECKING:`.
3. A feature is guarded when any enclosing `If` tests `sys.version_info` against a tuple whose
   first two elements are integers, or when its `Import` is inside a `Try` with an
   `ImportError`/`ModuleNotFoundError` handler.
4. A file that fails to parse is *not judged* with the syntax error's line — never *broken*,
   because it may simply be a Python newer than the one running this tool.
5. Only modules under the shipped packages are read. The report names the directories it read.

## Output

Broken first, with `path:line`, the construct, the version it needs and the floor it breaks. Then
guarded, then the summary: `N files · M constructs · K broken · G guarded · U not judged`.

## Tests

Temporary packages written by the test itself: each acceptance criterion, both directions of every
guard, and one case per recognised construct.

## CI

Run the suite, then run the tool against this repository, which declares its own floor.
