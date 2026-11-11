"""The sentence shapes the front end accepts, and the ones it refuses."""

from mooremind.english import UNHANDLED, parse_question, parse_sentence


def _fact(text: str) -> dict[str, object]:
    parsed = parse_sentence(text)
    assert parsed is not None, text
    return parsed


def test_location_shapes_from_ordinary_sentences():
    cases = {
        "Nim is in the loft.": ("nim", "in", "loft"),
        "The spoon is in the cup.": ("spoon", "in", "cup"),
        "Pock stays in the workshop.": ("pock", "in", "workshop"),
        "The tin sits in the hallway.": ("tin", "in", "hallway"),
        "Bramble stands in the kitchen.": ("bramble", "in", "kitchen"),
        "Tess begins in the cellar.": ("tess", "in", "cellar"),
        "The ribbon was left in the yard.": ("ribbon", "in", "yard"),
        "At first Nim is in the porch.": ("nim", "in", "porch"),
        "Then Nim moves to the yard.": ("nim", "in", "yard"),
        "After that Bramble is in the pantry.": ("bramble", "in", "pantry"),
        "Next Tess is in the hallway.": ("tess", "in", "hallway"),
        "Later Lumen is in the garden.": ("lumen", "in", "garden"),
        "The spoon is inside the cup.": ("spoon", "in", "cup"),
    }
    for text, triple in cases.items():
        parsed = _fact(text)
        assert (parsed["source"], parsed["type"], parsed["target"]) == triple


def test_holding_and_containers():
    assert _fact("The basket is held by Veda.")["type"] == "held_by"
    assert _fact("The basket is held by Veda.")["source"] == "basket"
    assert _fact("The basket is held by Veda.")["target"] == "veda"
    carried = _fact("Veda is holding the cup.")
    assert (carried["source"], carried["type"], carried["target"]) == ("cup", "held_by", "veda")
    same = _fact("Veda carries the ribbon.")
    assert (same["source"], same["type"], same["target"]) == ("ribbon", "held_by", "veda")
    inside = _fact("The basket contains the pebble.")
    assert (inside["source"], inside["type"], inside["target"]) == ("pebble", "in", "basket")
    nested = _fact("The cup has the pot in it.")
    assert (nested["source"], nested["type"], nested["target"]) == ("pot", "in", "cup")
    deeper = _fact("The pot has the peg inside it.")
    assert (deeper["source"], deeper["type"], deeper["target"]) == ("peg", "in", "pot")


def test_classes_and_colours_and_a_refusal():
    kind = _fact("A mottle is rust.")
    assert (kind["source"], kind["type"], kind["target"]) == ("mottle", "color", "rust")
    member = _fact("Nim is a mottle.")
    assert (member["source"], member["type"], member["target"]) == ("nim", "is_a", "mottle")
    other = _fact("The brindle kind is pearl.")
    assert (other["source"], other["type"], other["target"]) == ("brindle", "color", "pearl")
    counted = _fact("Tess counts as a brindle.")
    assert (counted["source"], counted["type"], counted["target"]) == ("tess", "is_a", "brindle")
    parent = _fact("A snip is a mottle.")
    assert (parent["source"], parent["type"], parent["target"]) == ("snip", "is_a", "mottle")
    linked = _fact("The snip kind counts as a mottle.")
    assert (linked["source"], linked["type"], linked["target"]) == ("snip", "is_a", "mottle")
    own = _fact("Nim alone is olive.")
    assert (own["source"], own["type"], own["target"]) == ("nim", "color", "olive")
    plain = _fact("Nim is navy.")
    assert plain["target"] == "navy"
    assert parse_sentence("Remember this about Nim, please.") is None
    assert parse_sentence("In the loft sits Nim.") is None
    assert parse_sentence("Nim went from the porch to the yard.") is None


def test_question_gate_refuses_a_form_it_does_not_know():
    names = {"nim": "nim", "spoon": "spoon"}
    found = parse_question("Where is Nim?", names)
    assert found is not None and found.kind == "where" and found.entity == "nim"
    earlier = parse_question("Where was Nim earlier?", names)
    assert earlier is not None and earlier.kind == "before"
    assert parse_question("In which room do we find Nim?", names) is None
    assert parse_question("Name the hue Nim wears.", names) is None
    assert UNHANDLED
