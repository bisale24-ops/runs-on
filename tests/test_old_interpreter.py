"""What happens when the tool runs on a Python older than the code it is reading."""
import sys

import pytest

from runson import cli

from helpers import make_package, write


@pytest.mark.skipif(sys.version_info >= (3, 10),
                    reason="only meaningful on an interpreter that cannot parse a match statement")
def test_an_unparsable_file_is_not_judged_rather_than_passed(tmp_path, capsys):
    make_package(tmp_path, floor=">=3.9")
    write(tmp_path, "demo/newer.py", "def pick(v):\n    match v:\n        case _:\n            return 1\n")
    assert cli.main(["--repo", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "NOT JUDGED" in out
    assert "may need a newer Python" in out
