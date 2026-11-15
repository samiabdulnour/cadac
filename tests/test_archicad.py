import pytest

from cadac.archicad import NOT_REGISTERED, Archicad, CommandFailed


class Fake:
    """An Archicad that answers from a table and remembers what it was asked."""

    def __init__(self, answers: dict) -> None:
        self.answers = answers
        self.asked: list[tuple[str, str]] = []

    def __call__(self, payload: dict) -> dict:
        command = payload["command"]
        if command != "API.ExecuteAddOnCommand":
            self.asked.append(("", command))
            return self.answers[command]
        identity = payload["parameters"]["addOnCommandId"]
        key = (identity["commandNamespace"], identity["commandName"])
        self.asked.append(key)
        if key not in self.answers:
            return {"succeeded": False, "error": {"code": NOT_REGISTERED, "message": "no such"}}
        return {"succeeded": True, "result": {"addOnCommandResponse": self.answers[key]}}


def test_an_official_command_returns_its_result() -> None:
    fake = Fake(
        {"API.GetPublisherSetNames": {"succeeded": True, "result": {"publisherSetNames": ["A"]}}}
    )
    assert Archicad(send=fake).official("API.GetPublisherSetNames") == {"publisherSetNames": ["A"]}


def test_an_outer_refusal_raises_with_its_code() -> None:
    fake = Fake({"API.X": {"succeeded": False, "error": {"code": 7, "message": "not now"}}})
    with pytest.raises(CommandFailed, match="not now") as caught:
        Archicad(send=fake).official("API.X")
    assert caught.value.code == 7


def test_an_error_inside_a_successful_answer_raises() -> None:
    """The dangerous level: Archicad says the call succeeded and the add-on's
    own answer carries the failure."""
    fake = Fake(
        {("LoriiniTapir", "GetStories"): {"error": {"code": -2130313112, "message": "bad"}}}
    )
    with pytest.raises(CommandFailed, match="LoriiniTapir.GetStories failed: bad") as caught:
        Archicad(send=fake).tapir("GetStories")
    assert caught.value.code == -2130313112


def test_tapir_is_found_in_the_loriini_add_on_first_and_kept() -> None:
    fake = Fake({("LoriiniTapir", "GetStories"): {"stories": []}})
    archicad = Archicad(send=fake)
    archicad.tapir("GetStories")
    archicad.tapir("GetStories")
    assert fake.asked == [("LoriiniTapir", "GetStories")] * 2


def test_a_stand_alone_tapir_answers_when_loriini_does_not_and_is_kept() -> None:
    fake = Fake({("TapirCommand", "GetStories"): {"stories": []}})
    archicad = Archicad(send=fake)
    assert archicad.tapir("GetStories") == {"stories": []}
    archicad.tapir("GetStories")
    assert fake.asked == [
        ("LoriiniTapir", "GetStories"),
        ("TapirCommand", "GetStories"),
        ("TapirCommand", "GetStories"),
    ]


def test_no_add_on_at_all_says_what_to_install() -> None:
    with pytest.raises(CommandFailed, match="Install the Loriini add-on"):
        Archicad(send=Fake({})).tapir("GetStories")


def test_a_real_failure_is_not_retried_under_the_other_namespace() -> None:
    fake = Fake({("LoriiniTapir", "GetStories"): {"error": {"code": 1, "message": "broken"}}})
    with pytest.raises(CommandFailed, match="broken"):
        Archicad(send=fake).tapir("GetStories")
    assert fake.asked == [("LoriiniTapir", "GetStories")]
