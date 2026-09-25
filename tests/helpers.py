"""Each test writes the package it is about, so every assertion is about known source."""
import pathlib
import textwrap


def write(root, relative, text):
    path = pathlib.Path(root) / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text).lstrip(), encoding="utf-8")
    return path


def make_package(tmp_path, floor=">=3.9", module="", classifiers=None, name="demo"):
    lines = ["[project]", 'name = "demo"', 'version = "0.1.0"']
    if floor:
        lines.append(f'requires-python = "{floor}"')
    if classifiers:
        lines.append("classifiers = [")
        lines += [f'  "Programming Language :: Python :: {c}",' for c in classifiers]
        lines.append("]")
    write(tmp_path, "pyproject.toml", "\n".join(lines) + "\n")
    write(tmp_path, f"{name}/__init__.py", "\n")
    write(tmp_path, f"{name}/core.py", module or "VALUE = 1\n")
    return tmp_path
