from runson import cli

from helpers import make_package, write


def test_exit_zero_when_the_promise_holds(tmp_path, capsys):
    make_package(tmp_path, floor=">=3.11", module="import tomllib\n")
    assert cli.main(["--repo", str(tmp_path)]) == 0
    assert "0 broken" in capsys.readouterr().out


def test_exit_one_when_the_promise_breaks(tmp_path, capsys):
    make_package(tmp_path, floor=">=3.9", module="import tomllib\n")
    assert cli.main(["--repo", str(tmp_path)]) == 1
    assert "BREAKS ITS PROMISE" in capsys.readouterr().out


def test_exit_two_when_the_repository_is_missing(tmp_path):
    assert cli.main(["--repo", str(tmp_path / "nowhere")]) == 2


def test_exit_two_when_there_is_no_package(tmp_path):
    write(tmp_path, "README.md", "prose only\n")
    assert cli.main(["--repo", str(tmp_path)]) == 2


def test_floor_override_answers_a_what_if(tmp_path, capsys):
    make_package(tmp_path, floor=">=3.11", module="import tomllib\n")
    assert cli.main(["--repo", str(tmp_path)]) == 0
    assert cli.main(["--repo", str(tmp_path), "--floor", "3.9"]) == 1
    assert "needs 3.11, this package promises 3.9" in capsys.readouterr().out


def test_a_contradiction_is_reported(tmp_path, capsys):
    make_package(tmp_path, floor=">=3.8", classifiers=["3.10", "3.11"])
    cli.main(["--repo", str(tmp_path)])
    out = capsys.readouterr().out
    assert "CONTRADICTION" in out and "3.8" in out and "3.10" in out


def test_a_project_with_no_floor_is_not_judged(tmp_path, capsys):
    make_package(tmp_path, floor=None, module="import tomllib\n")
    assert cli.main(["--repo", str(tmp_path)]) == 0
    assert "declares no Python floor" in capsys.readouterr().out


def test_json_output_is_machine_readable(tmp_path, capsys):
    import json
    make_package(tmp_path, floor=">=3.9", module="import tomllib\n")
    cli.main(["--repo", str(tmp_path), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["promises"] == "3.9"
    assert payload["broken"][0]["needs"] == "3.11"


def test_a_file_that_does_not_parse_is_not_judged(tmp_path, capsys):
    make_package(tmp_path, floor=">=3.9")
    write(tmp_path, "demo/newer.py", "def f(:\n    pass\n")
    assert cli.main(["--repo", str(tmp_path)]) == 0
    assert "does not parse here" in capsys.readouterr().out
