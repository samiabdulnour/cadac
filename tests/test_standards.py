import shutil
from pathlib import Path

import pytest

from cadac import standards


@pytest.fixture
def copy(root: Path, tmp_path: Path) -> Path:
    """The repository's standards, somewhere they can be spoiled."""
    target = tmp_path / "standards"
    shutil.copytree(root / "standards", target, ignore=shutil.ignore_patterns("*.md"))
    return target


def test_the_repository_standards_read_without_a_problem(root: Path) -> None:
    found, problems = standards.load(root / "standards")
    assert problems == []
    assert set(found.status) == set(standards.FILES)
    assert found.names["layers"]
    assert found.favourites["Wall"]
    assert found.properties


def test_a_missing_file_is_named(copy: Path) -> None:
    (copy / "layers.yaml").unlink()
    _, problems = standards.load(copy)
    assert problems == ["layers.yaml: the file is missing."]


def test_a_status_outside_the_three_is_refused(copy: Path) -> None:
    path = copy / "layers.yaml"
    path.write_text(path.read_text().replace("status: example", "status: final"))
    _, problems = standards.load(copy)
    assert len(problems) == 1 and "status is 'final'" in problems[0]


def test_a_misspelled_section_is_not_silently_empty(copy: Path) -> None:
    path = copy / "layers.yaml"
    path.write_text(path.read_text().replace("layer_combinations:", "layer_combos:"))
    found, problems = standards.load(copy)
    assert problems == ["layers.yaml: 'layer_combos' is not a section of this file."]
    assert found.names["layer_combinations"] == ()


def test_a_name_listed_twice_is_reported_once_and_kept_once(copy: Path) -> None:
    (copy / "layers.yaml").write_text(
        'status: draft\nlayers:\n  - "A"\n  - name: "A"\n  - ""\nlayer_combinations: []\n'
    )
    found, problems = standards.load(copy)
    assert found.names["layers"] == ("A",)
    assert problems == [
        "layers.yaml: layers: 'A' is listed twice.",
        "layers.yaml: layers: entry 3 has no name.",
    ]


def test_a_favourite_must_belong_to_a_tool_the_add_on_knows(copy: Path) -> None:
    (copy / "favourites.yaml").write_text(
        "status: draft\nfavourites:\n"
        '  - { name: "Good", element: Wall }\n'
        '  - { name: "Bad", element: Walls }\n'
    )
    found, problems = standards.load(copy)
    assert found.favourites == {"Wall": ("Good",)}
    assert len(problems) == 1 and "'Bad' has element 'Walls'" in problems[0]


@pytest.mark.parametrize("priority", ["high", 1000, -1, True, 4.5])
def test_a_priority_is_a_whole_number_in_archicads_range(copy: Path, priority: object) -> None:
    (copy / "attributes.yaml").write_text(
        f"status: draft\nbuilding_materials:\n  - {{ name: Concrete, priority: {priority} }}\n"
    )
    found, problems = standards.load(copy)
    assert found.building_materials == {"Concrete": None}
    assert len(problems) == 1 and "whole number from 0 to 999" in problems[0]


def test_a_pattern_that_is_not_a_pattern_is_refused(copy: Path) -> None:
    (copy / "naming.yaml").write_text('status: draft\npatterns:\n  wall_id: "W-(\\\\d{3}"\n')
    found, problems = standards.load(copy)
    assert found.patterns == {}
    assert len(problems) == 1 and "'wall_id' is not a valid pattern" in problems[0]


def test_files_not_agreed_are_named_with_how_far_they_got(root: Path) -> None:
    found, _ = standards.load(root / "standards")
    assert "layers (example)" in found.not_agreed()
