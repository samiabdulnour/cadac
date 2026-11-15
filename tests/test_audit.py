from cadac.audit import Finding, compare
from cadac.standards import SECTIONS, Standards


def standards(**given: object) -> Standards:
    names = {section: () for section in SECTIONS}
    names.update(given.pop("names", {}))  # type: ignore[arg-type]
    return Standards(names=names, **given)  # type: ignore[arg-type]


def snapshot(**sections: object) -> dict:
    return {"project": "Template", "sections": sections, "unread": {}}


def test_a_template_that_holds_everything_passes() -> None:
    report = compare(
        standards(
            names={"layers": ("A", "B")},
            building_materials={"Concrete": 800, "Air": None},
            favourites={"Wall": ("W1",)},
            properties=(("Unit", "Unit Type"),),
        ),
        snapshot(
            layers=["A", "B", "C"],
            building_materials=[
                {"name": "Concrete", "priority": 800},
                {"name": "Air", "priority": 100},
            ],
            favourites={"Wall": ["W1", "W2"], "Slab": ["S1"]},
            properties=[
                {"group": "Unit", "name": "Unit Type"},
                {"group": "ID", "name": "Element ID"},
            ],
        ),
    )
    assert report.passed
    assert report.confirmed == 6
    assert report.extra == {"layer": ["C"], "favourite (Wall)": ["W2"]}


def test_what_the_template_lacks_is_missing_and_fails() -> None:
    report = compare(standards(names={"layers": ("A", "B")}), snapshot(layers=["A"]))
    assert not report.passed
    assert report.missing == [Finding("layer", "B")]
    assert report.confirmed == 1


def test_a_name_off_by_case_or_spacing_is_missing_and_says_what_it_nearly_was() -> None:
    report = compare(
        standards(names={"layers": ("Wall - External",)}), snapshot(layers=["Wall -  external"])
    )
    assert [finding.describe() for finding in report.missing] == [
        "layer: Wall - External -- the template has 'Wall -  external', "
        "which differs only in case or spacing"
    ]


def test_a_priority_other_than_the_standards_is_different_and_fails() -> None:
    report = compare(
        standards(building_materials={"Concrete": 800}),
        snapshot(building_materials=[{"name": "Concrete", "priority": 700}]),
    )
    assert not report.passed
    assert report.missing == []
    assert report.confirmed == 0
    assert report.different == [
        Finding(
            "building material", "Concrete", "priority 700 in the template, 800 in the standards"
        )
    ]


def test_a_priority_the_snapshot_did_not_carry_is_unchecked_not_passed() -> None:
    report = compare(
        standards(building_materials={"Concrete": 800}),
        snapshot(building_materials=[{"name": "Concrete", "priority": None}]),
    )
    assert not report.passed
    assert report.unchecked == [
        ("priority of Concrete", "the snapshot does not carry its priority")
    ]


def test_a_section_that_could_not_be_read_is_unchecked_with_its_reason() -> None:
    report = compare(
        standards(names={"graphic_overrides": ("Plans",)}),
        {"sections": {}, "unread": {"graphic_overrides": "the add-on has no such command"}},
    )
    assert not report.passed
    assert report.missing == []
    assert report.unchecked == [("graphic_overrides", "the add-on has no such command")]


def test_a_section_the_standards_say_nothing_about_needs_no_reading() -> None:
    assert compare(standards(), {"sections": {}, "unread": {"layers": "refused"}}).passed


def test_an_element_type_whose_favourites_were_not_read_is_unchecked() -> None:
    report = compare(
        standards(favourites={"Wall": ("W1",), "Slab": ("S1",)}),
        {
            "sections": {"favourites": {"Wall": ["W1"]}},
            "unread": {"favourites (Slab)": "refused"},
        },
    )
    assert report.confirmed == 1
    assert report.unchecked == [("favourites (Slab)", "refused")]


def test_archicads_own_properties_are_not_listed_as_extra() -> None:
    report = compare(
        standards(properties=(("Unit", "Unit Type"),)),
        snapshot(properties=[{"group": "Unit", "name": "Unit Type"}, {"group": "ID", "name": "x"}]),
    )
    assert report.passed and report.extra == {}
