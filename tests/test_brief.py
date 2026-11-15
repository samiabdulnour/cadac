from pathlib import Path

import yaml

from cadac import brief

GOOD = {
    "project": {"name": "Test"},
    "site": {"address": "1 Street", "area_m2": 900},
    "building": {
        "use": "residential",
        "storeys_above_ground": 4,
        "basements": 1,
        "floor_to_floor_m": {"ground": 3.6, "typical": 3.1},
    },
    "programme": [{"type": "1B", "count": 6, "area_m2": 50}],
    "open_questions": [],
    "approved": {"by": "A Person", "date": "2026-11-15"},
}


def write(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "brief.yaml"
    path.write_text(yaml.safe_dump(data))
    return path


def change(**replaced: object) -> dict:
    return {**GOOD, **replaced}


def test_the_example_brief_reads_and_is_not_ready(root: Path) -> None:
    read, problems = brief.load(root / "projects" / "_example" / "brief.yaml")
    assert problems == []
    assert read.name == "Example House of Flats"
    assert read.open_questions and not read.approved_by
    assert not read.ready


def test_a_whole_brief_with_an_approval_is_ready(tmp_path: Path) -> None:
    read, problems = brief.load(write(tmp_path, GOOD))
    assert problems == []
    assert read.ready and read.approved_by == "A Person, 2026-11-15"


def test_an_open_question_holds_an_approved_brief_back(tmp_path: Path) -> None:
    read, problems = brief.load(write(tmp_path, change(open_questions=["Retail or not?"])))
    assert problems == [] and not read.ready


def test_an_approval_needs_a_name_and_a_date(tmp_path: Path) -> None:
    read, problems = brief.load(write(tmp_path, change(approved={"by": "A Person"})))
    assert not read.ready
    assert len(problems) == 1 and "approved needs both by and date" in problems[0]


def test_every_missing_part_is_reported_in_one_reading(tmp_path: Path) -> None:
    _, problems = brief.load(write(tmp_path, {"project": {}}))
    said = " | ".join(problems)
    for part in ("project has no name", "no site", "no building", "programme lists nothing"):
        assert part in said


def test_numbers_must_be_numbers_above_zero(tmp_path: Path) -> None:
    bad = change(
        site={"address": "1 Street", "area_m2": 0},
        building={
            "use": "residential",
            "storeys_above_ground": 2.5,
            "basements": -1,
            "floor_to_floor_m": {"typical": "3.1"},
        },
        programme=[
            {"type": "1B", "count": True, "area_m2": 50},
            {"type": "1B", "count": 1, "area_m2": 1},
        ],
    )
    _, problems = brief.load(write(tmp_path, bad))
    said = " | ".join(problems)
    for part in (
        "area_m2 is 0",
        "storeys_above_ground is 2.5",
        "basements is -1",
        "typical is '3.1'",
        "count is True",
        "'1B' is listed twice",
    ):
        assert part in said
    assert len(problems) == 6


def test_a_missing_file_is_a_problem_not_a_crash(tmp_path: Path) -> None:
    _, problems = brief.load(tmp_path / "brief.yaml")
    assert len(problems) == 1 and problems[0].endswith("the file is missing.")
