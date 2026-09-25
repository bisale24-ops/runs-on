"""Every Python floor a project states, and where it states it.

A package can promise a version in four places, and they drift apart quietly. `requires-python` is
the one pip enforces, so it decides what actually installs; a classifier that disagrees is still
worth reporting, because a package promising two different things has already broken one of them.

Everything here is read as text. No build backend is invoked and nothing is imported: the point is
to check a package without being able to install it.
"""
import dataclasses
import pathlib
import re

# setup.py states it inside a call, pyproject and setup.cfg on a line of their own
REQUIRES = re.compile(r"""(?:^|[\s(,])(?:requires-python|python_requires)\s*=\s*["']?\s*([^"'\n)]+)""",
                      re.M)
LOWER_BOUND = re.compile(r">=\s*(\d+)\.(\d+)|~=\s*(\d+)\.(\d+)")
CLASSIFIER = re.compile(r"Programming Language :: Python :: (\d+)\.(\d+)")


@dataclasses.dataclass
class Declared:
    floor: tuple            # the version pip will honour, or None
    sources: list           # [(where, (major, minor), raw)]

    @property
    def contradiction(self):
        """Two stated floors that are not the same number."""
        versions = {version for _, version, _ in self.sources}
        return sorted(versions) if len(versions) > 1 else None

    def text(self, version=None):
        version = version or self.floor
        return f"{version[0]}.{version[1]}" if version else "none"


def _lower_bound(specifier):
    """The smallest version a specifier admits: '>=3.9,<4' -> (3, 9)."""
    found = []
    for match in LOWER_BOUND.finditer(specifier):
        major, minor = (match.group(1), match.group(2)) if match.group(1) else (match.group(3), match.group(4))
        found.append((int(major), int(minor)))
    return min(found) if found else None


def read(repo):
    repo = pathlib.Path(repo)
    sources = []
    for name in ("pyproject.toml", "setup.cfg", "setup.py"):
        path = repo / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in REQUIRES.finditer(text):
            bound = _lower_bound(match.group(1))
            if bound:
                sources.append((name, bound, match.group(1).strip()))
                break
        classifiers = [(int(a), int(b)) for a, b in CLASSIFIER.findall(text)]
        if classifiers:
            lowest = min(classifiers)
            sources.append((f"{name} classifiers", lowest, f"Python :: {lowest[0]}.{lowest[1]}"))
    floor = min((version for _, version, _ in sources), default=None)
    return Declared(floor=floor, sources=sources)
