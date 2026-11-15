import pytest

from cadac import snapshot
from cadac.archicad import NOT_REGISTERED, Archicad, CommandFailed, NotRunning
from cadac.standards import ELEMENT_TYPES


class Project:
    """A stand-in for Archicad with a small project open, answering in the
    shapes docs/archicad.md records."""

    def __init__(self, *, loriini: bool = True) -> None:
        self.loriini = loriini
        self.attributes = {
            "Layer": ["Wall - External", "Structure - Slab"],
            "LayerCombination": ["01 Model"],
            "Composite": [],
            "Profile": [],
            "Surface": ["Paint"],
            "PenTable": ["01 Documentation"],
            "ZoneCategory": ["Residential"],
            "BuildingMaterial": ["Concrete", "Air Space"],
        }

    def __call__(self, payload: dict) -> dict:
        if payload["command"] == "API.GetPublisherSetNames":
            return {"succeeded": True, "result": {"publisherSetNames": ["Issue - PDF"]}}
        identity = payload["parameters"]["addOnCommandId"]
        namespace, command = identity["commandNamespace"], identity["commandName"]
        given = payload["parameters"]["addOnCommandParameters"]
        if namespace == "Loriini" and not self.loriini:
            return {"succeeded": False, "error": {"code": NOT_REGISTERED, "message": "no such"}}
        return {"succeeded": True, "result": {"addOnCommandResponse": self.answer(command, given)}}

    def answer(self, command: str, given: dict) -> dict:
        if command == "GetAttributesByType":
            return {
                "attributes": [
                    {
                        "attributeId": {"guid": f"{given['attributeType']}-{name}"},
                        "index": i,
                        "name": name,
                    }
                    for i, name in enumerate(self.attributes[given["attributeType"]], start=1)
                ]
            }
        if command == "GetBuildingMaterials":
            assert given["fields"] == ["connPriority"]
            priorities = {"BuildingMaterial-Concrete": 800, "BuildingMaterial-Air Space": 100}
            return {
                "buildingMaterials": [
                    {"connPriority": priorities[row["attributeId"]["guid"]]}
                    for row in given["attributeIds"]
                ]
            }
        if command == "GetFavoritesByType":
            if given["elementType"] == "Railing":
                return {"error": {"code": 1, "message": "no favourites for this tool"}}
            return {"favorites": ["Wall - External 300"] if given["elementType"] == "Wall" else []}
        if command == "GetAllProperties":
            return {
                "properties": [
                    {"propertyGroupName": "Unit", "propertyName": "Unit Type", "propertyType": "x"},
                    {
                        "propertyGroupName": "Unit",
                        "propertyName": "Unit Number",
                        "propertyType": "x",
                    },
                ]
            }
        if command == "GetGraphicOverrideCombinations":
            return {"combinations": [{"guid": "1", "name": "Plans"}]}
        if command == "GetProjectInfo":
            return {"isUntitled": True}
        raise AssertionError(f"the snapshot asked for {command}, which nothing here answers")


def test_every_section_is_read_by_name_and_sorted() -> None:
    taken = snapshot.read(Archicad(send=Project()))
    sections = taken["sections"]
    assert taken["project"] == "Untitled"
    assert sections["layers"] == ["Structure - Slab", "Wall - External"]
    assert sections["layer_combinations"] == ["01 Model"]
    assert sections["composites"] == []
    assert sections["building_materials"] == [
        {"name": "Air Space", "priority": 100},
        {"name": "Concrete", "priority": 800},
    ]
    assert sections["favourites"]["Wall"] == ["Wall - External 300"]
    assert sections["properties"] == [
        {"group": "Unit", "name": "Unit Number"},
        {"group": "Unit", "name": "Unit Type"},
    ]
    assert sections["graphic_overrides"] == ["Plans"]
    assert sections["publisher_sets"] == ["Issue - PDF"]


def test_a_tool_whose_favourites_cannot_be_read_is_unread_and_the_rest_are_read() -> None:
    taken = snapshot.read(Archicad(send=Project()))
    assert set(taken["sections"]["favourites"]) == set(ELEMENT_TYPES) - {"Railing"}
    assert list(taken["unread"]) == ["favourites (Railing)"]
    assert "no favourites for this tool" in taken["unread"]["favourites (Railing)"]


def test_without_the_loriini_add_on_only_its_section_is_unread() -> None:
    taken = snapshot.read(Archicad(send=Project(loriini=False)))
    assert "graphic_overrides" not in taken["sections"]
    assert "graphic_overrides" in taken["unread"]
    assert taken["sections"]["layers"]


def test_no_add_on_stops_the_reading_with_one_message() -> None:
    def nothing_registered(payload: dict) -> dict:
        return {"succeeded": False, "error": {"code": NOT_REGISTERED, "message": "no such"}}

    with pytest.raises(CommandFailed, match="Install the Loriini add-on"):
        snapshot.read(Archicad(send=nothing_registered))


def test_archicad_going_away_part_way_stops_the_reading() -> None:
    """Not thirty sections each unread for the same reason."""
    project = Project()

    def gone_after_the_first(payload: dict) -> dict:
        if "GetProjectInfo" in str(payload):
            return project(payload)
        raise NotRunning("Could not reach Archicad")

    with pytest.raises(NotRunning):
        snapshot.read(Archicad(send=gone_after_the_first))
