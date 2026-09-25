---
doc: checklist
status: approved
---

# Build checklist

1. **Declared floors** — pyproject, setup.cfg, setup.py, classifiers, contradiction detection.
   *done, 6 tests*
2. **Shipped files** — packages from src/ or top level, implicit namespace packages, single-module
   distributions; tests and tooling excluded; the directories read are named in the report. *done*
3. **Features** — eleven constructs, each decidable from the syntax tree alone. *done*
4. **Guards** — `sys.version_info`, `try/except ImportError`, `if TYPE_CHECKING`,
   `from __future__ import annotations`. *done, both directions tested*
5. **Report** — four groups, summary, exit codes, `--json`, `--floor` for what-ifs. *done, 9 tests*
6. **Tests** — 30, each writing the package it is about. *done*
7. **Real repositories** — thirty maintained projects, 1 060 shipped files, zero broken, five
   guarded. The two guarded cases in black and poetry are exactly the false positives the probe
   produced before the guard analysis existed. *done*
8. **The other direction** — removing poetry's version guard produces one finding and exit 1;
   `--floor 3.8` on requests produces six, each with its line. *done*
9. **Dogfood** — run on itself in CI, on 3.9 and 3.12. Running it on 3.9 found a real bug in this
   tool that the tool itself cannot catch: `ast.Match` does not exist before 3.10. Written up in
   the README's limits rather than quietly fixed. *done*
10. **Video and submission.** *in progress*
