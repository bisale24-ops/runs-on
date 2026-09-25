from runson import declared

from helpers import make_package, write


def test_reads_requires_python(tmp_path):
    make_package(tmp_path, floor=">=3.9")
    assert declared.read(tmp_path).floor == (3, 9)


def test_reads_a_compound_specifier(tmp_path):
    make_package(tmp_path, floor=">=3.8,<4.0")
    assert declared.read(tmp_path).floor == (3, 8)


def test_reads_setup_py_when_there_is_no_pyproject(tmp_path):
    write(tmp_path, "setup.py", "from setuptools import setup\nsetup(python_requires='>=3.7')\n")
    write(tmp_path, "demo/__init__.py", "\n")
    assert declared.read(tmp_path).floor == (3, 7)


def test_a_project_with_no_floor_has_none(tmp_path):
    make_package(tmp_path, floor=None)
    assert declared.read(tmp_path).floor is None


def test_agreeing_sources_are_not_a_contradiction(tmp_path):
    make_package(tmp_path, floor=">=3.9", classifiers=["3.9", "3.10"])
    assert declared.read(tmp_path).contradiction is None


def test_a_classifier_that_disagrees_is_a_contradiction(tmp_path):
    make_package(tmp_path, floor=">=3.8", classifiers=["3.10", "3.11"])
    found = declared.read(tmp_path)
    assert found.contradiction == [(3, 8), (3, 10)]
    assert found.floor == (3, 8)        # pip honours the lowest, so that is what installs
