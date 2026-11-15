import json
import shutil
from pathlib import Path

import pytest

from cadac import cli


@pytest.fixture
def repo(root: Path, tmp_path: Path) -> Path:
    for folder in ("standards", "projects"):
        shutil.copytree(root / folder, tmp_path / folder)
    return tmp_path


def holding(repo: Path, **changed: object) -> Path:
    """A snapshot of a template that holds exactly what the standards list."""
    from cadac import standards

    found, _ = standards.load(repo / "standards")
    sections: dict = {section: list(names) for section, names in found.names.items()}
    sections["building_materials"] = [
        {"name": name, "priority": priority} for name, priority in found.building_materials.items()
    ]
    sections["favourites"] = {kind: list(names) for kind, names in found.favourites.items()}
    sections["properties"] = [{"group": group, "name": name} for group, name in found.properties]
    sections.update(changed)
    path = repo / "snapshot.json"
    path.write_text(json.dumps({"project": "Template", "sections": sections, "unread": {}}))
    return path


def test_validate_passes_on_the_repository_and_says_what_is_not_agreed(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["--root", str(repo), "validate"]) == 0
    out = capsys.readouterr().out
    assert "standards: read without a problem" in out
    assert "layers (example)" in out
    assert "not ready to build from (1 open question(s))" in out


def test_validate_fails_on_a_spoiled_brief(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "projects" / "_example" / "brief.yaml").write_text("project: {}\n")
    assert cli.main(["--root", str(repo), "validate"]) == 1
    assert "project has no name" in capsys.readouterr().out


def test_audit_of_a_template_that_holds_the_standards_passes(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["--root", str(repo), "audit", "--snapshot", str(holding(repo))]) == 0
    assert capsys.readouterr().out.rstrip().endswith("PASSED")


def test_audit_fails_and_names_what_is_missing(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    saved = holding(repo, layers=["Structure - Slab"])
    assert cli.main(["--root", str(repo), "audit", "--snapshot", str(saved)]) == 1
    out = capsys.readouterr().out
    assert "    - layer: Wall - External" in out
    assert out.rstrip().endswith("FAILED")


def test_audit_does_not_compare_against_standards_with_a_problem(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    saved = holding(repo)
    (repo / "standards" / "layers.yaml").unlink()
    assert cli.main(["--root", str(repo), "audit", "--snapshot", str(saved)]) == 1
    assert "layers.yaml: the file is missing." in capsys.readouterr().out


def test_no_archicad_is_one_line_and_a_failure(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Port 9 is the discard port: nothing answers JSON there.
    assert cli.main(["--root", str(repo), "audit", "--port", "9"]) == 1
    assert "Could not reach Archicad at http://127.0.0.1:9" in capsys.readouterr().err
