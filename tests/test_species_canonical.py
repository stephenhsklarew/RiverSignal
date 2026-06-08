"""Unit tests for fish-species canonicalization (FEAT-026, Phase 1)."""
from app.lib.species_canonical import canonicalize


def test_chinook_variants_collapse_to_one():
    keys = {canonicalize(n).key for n in ["Chinook", "Chinook Salmon", "Fall Chinook", "Spring Chinook", "chinook salmon"]}
    assert keys == {"chinook salmon"}
    assert canonicalize("Fall Chinook").label == "Chinook Salmon"
    assert canonicalize("Fall Chinook").run == "fall"
    assert canonicalize("Spring Chinook").run == "spring"


def test_steelhead_variants_collapse_but_stay_separate_from_rainbow():
    steel = {canonicalize(n).key for n in ["steelhead", "Summer Steelhead", "Winter Steelhead"]}
    rainbow = {canonicalize(n).key for n in ["rainbow", "Rainbow Trout", "rainbow trout", "Coastal Rainbow Trout", "Redband Trout"]}
    assert steel == {"steelhead"}
    assert rainbow == {"rainbow trout"}
    # the product decision: Steelhead and Rainbow Trout are NOT merged
    assert steel.isdisjoint(rainbow)
    assert canonicalize("Summer Steelhead").label == "Steelhead"
    assert canonicalize("Coastal Rainbow Trout").label == "Rainbow Trout"


def test_case_and_spacing_normalized():
    assert canonicalize("rainbow trout").key == canonicalize("Rainbow Trout").key
    assert canonicalize("Small Mouth Bass").label == "Smallmouth Bass"
    assert canonicalize("Musky").key == canonicalize("Muskellunge").key == "muskellunge"


def test_kokanee_separate_from_sockeye():
    # landlocked form kept distinct, same logic as steelhead/rainbow
    assert canonicalize("Kokanee").key != canonicalize("Sockeye Salmon").key


def test_unknown_name_title_cased():
    c = canonicalize("redbreast sunfish")
    assert c.label == "Redbreast Sunfish"
    assert c.run is None


def test_override_wins_for_long_tail():
    ov = {"columbia river redband trout": "Rainbow Trout"}
    assert canonicalize("Columbia River Redband Trout", overrides=ov).key == "rainbow trout"
    # case-insensitive on the raw name
    assert canonicalize("columbia river redband trout", overrides=ov).label == "Rainbow Trout"
    # without the override it stays a distinct entry (rules can't infer it)
    assert canonicalize("Columbia River Redband Trout").key != "rainbow trout"
