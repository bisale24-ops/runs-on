"""The acceptance criteria, each on a package the test wrote itself."""
import ast
import sys

import pytest

from runson import declared, features, shipped

from helpers import make_package, write

# A construct can only be recognised by an interpreter that can parse it. On 3.9 `ast.parse`
# refuses a match statement outright, so these two cases cannot run there - and the tool itself
# reports such a file as not judged rather than as clean. That behaviour has its own test in
# test_cli.py; here the fixtures simply cannot be built.
needs_match = pytest.mark.skipif(sys.version_info < (3, 10),
                                 reason="ast.parse cannot read a match statement before 3.10")


def run(root, floor=None):
    stated = declared.read(root)
    if floor:
        stated = declared.Declared(floor=floor, sources=[("--floor", floor, str(floor))])
    paths, _ = shipped.files(root)
    broken, guarded = [], []
    for path in paths:
        tree = ast.parse(path.read_text())
        for feature in features.collect(tree, str(path.relative_to(root))):
            if not stated.floor or feature.needs <= stated.floor:
                continue
            (guarded if feature.guard else broken).append(feature)
    return broken, guarded


def names(found):
    return [f.name for f in found]


@needs_match
def test_a_bare_match_statement_below_the_floor_is_broken(tmp_path):
    make_package(tmp_path, floor=">=3.9", module="""
        def pick(value):
            match value:
                case 1:
                    return "one"
                case _:
                    return "other"
    """)
    broken, guarded = run(tmp_path)
    assert names(broken) == ["match statement"]
    assert broken[0].needs == (3, 10)
    assert broken[0].line == 2
    assert guarded == []


@needs_match
def test_the_same_match_behind_a_version_check_is_guarded(tmp_path):
    make_package(tmp_path, floor=">=3.9", module="""
        import sys

        if sys.version_info >= (3, 10):
            def pick(value):
                match value:
                    case _:
                        return None
    """)
    broken, guarded = run(tmp_path)
    assert broken == []
    assert guarded[0].guard == "sys.version_info check"


def test_an_import_behind_an_importerror_fallback_is_guarded(tmp_path):
    make_package(tmp_path, floor=">=3.9", module="""
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
    """)
    broken, guarded = run(tmp_path)
    assert broken == []
    assert guarded[0].guard == "try/except ImportError fallback"


def test_a_bare_newer_stdlib_import_is_broken(tmp_path):
    make_package(tmp_path, floor=">=3.9", module="import tomllib\n")
    broken, _ = run(tmp_path)
    assert names(broken) == ["import tomllib"]
    assert broken[0].needs == (3, 11)


def test_a_union_annotation_is_broken_below_3_10(tmp_path):
    # two unions on one line are one finding: a reader fixes the line, not each half of it
    make_package(tmp_path, floor=">=3.9", module="def f(x: int | None) -> str | None:\n    return None\n")
    broken, _ = run(tmp_path)
    assert names(broken) == ["X | Y in a runtime annotation"]
    assert broken[0].needs == (3, 10)


def test_unions_on_separate_lines_are_separate_findings(tmp_path):
    make_package(tmp_path, floor=">=3.9", module="""
        def f(
            x: int | None,
            y: str | None,
        ):
            return x, y
    """)
    broken, _ = run(tmp_path)
    assert [f.line for f in broken] == [2, 3]


def test_postponed_annotations_remove_the_floor(tmp_path):
    make_package(tmp_path, floor=">=3.9", module="""
        from __future__ import annotations

        def f(x: int | None) -> str | None:
            return None
    """)
    broken, guarded = run(tmp_path)
    assert broken == [] and guarded == []


def test_annotations_under_type_checking_are_guarded(tmp_path):
    make_package(tmp_path, floor=">=3.9", module="""
        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            Alias: int | None = None
    """)
    broken, guarded = run(tmp_path)
    assert broken == []
    assert guarded[0].guard == "if TYPE_CHECKING"


def test_an_or_outside_an_annotation_is_never_reported(tmp_path):
    make_package(tmp_path, floor=">=3.6", module="""
        def combine(a, b):
            merged = a | b
            flags = 1 | 2
            return merged, flags
    """)
    broken, guarded = run(tmp_path)
    assert broken == [] and guarded == []


def test_builtin_generics_need_3_9(tmp_path):
    make_package(tmp_path, floor=">=3.8", module="def f(x: list[int]):\n    return x\n")
    broken, _ = run(tmp_path)
    assert broken[0].needs == (3, 9)


def test_a_walrus_needs_3_8(tmp_path):
    make_package(tmp_path, floor=">=3.7", module="""
        def f(values):
            if (n := len(values)) > 2:
                return n
            return 0
    """)
    broken, _ = run(tmp_path)
    assert names(broken) == ["walrus :="]


def test_an_f_string_needs_3_6(tmp_path):
    make_package(tmp_path, floor=">=3.5", module='def f(x):\n    return f"{x}"\n')
    broken, _ = run(tmp_path)
    assert names(broken) == ["f-string"]


def test_nothing_is_reported_when_the_floor_already_covers_it(tmp_path):
    make_package(tmp_path, floor=">=3.11", module="import tomllib\n")
    broken, guarded = run(tmp_path)
    assert broken == [] and guarded == []


def test_tests_and_tooling_are_not_read(tmp_path):
    make_package(tmp_path, floor=">=3.9")
    write(tmp_path, "tests/test_thing.py", "import tomllib\n")
    write(tmp_path, "noxfile.py", "import tomllib\n")
    broken, _ = run(tmp_path)
    assert broken == []


def test_include_tests_reads_them(tmp_path):
    make_package(tmp_path, floor=">=3.9")
    write(tmp_path, "demo/tests/test_thing.py", "import tomllib\n")
    paths, _ = shipped.files(tmp_path, include_tests=True)
    assert any("test_thing" in str(path) for path in paths)


def test_an_annotation_inside_a_function_body_is_not_evaluated(tmp_path):
    """`self.x: list[str] = []` never runs, so it carries no floor. Verified against CPython."""
    make_package(tmp_path, floor=">=3.7", module="""
        class Holder:
            def __init__(self):
                self.result: list[str] = []

        def build():
            names: list[str] = []
            return names
    """)
    broken, guarded = run(tmp_path)
    assert broken == [] and guarded == []


def test_an_annotation_in_a_class_body_is_evaluated(tmp_path):
    make_package(tmp_path, floor=">=3.7", module="""
        class Holder:
            result: list[str] = []
    """)
    broken, _ = run(tmp_path)
    assert [f.needs for f in broken] == [(3, 9)]


def test_an_annotation_at_module_level_is_evaluated(tmp_path):
    make_package(tmp_path, floor=">=3.7", module="RESULT: list[str] = []\n")
    broken, _ = run(tmp_path)
    assert [f.needs for f in broken] == [(3, 9)]
