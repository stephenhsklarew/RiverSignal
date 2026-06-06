"""Unit tests for the mo_geology (Missouri Geological Survey) attribute mapping.

Pure functions, no network/DB — mirrors test_ingest_georgia.py. Verifies the MGS
Bedrock ArcGIS feature attributes map onto geologic_units insert params the way
the adapter expects (UNIT_NAME → unit_name/lithology, UNIT_LABEL → formation,
GEO_AGE → period).
"""
from pipeline.ingest.geology import _mo_geology_params

# Representative MGS Bedrock features (Ozark karst column of the Meramec basin).
GASCONADE = {
    "OBJECTID": 4217,
    "UNIT_NAME": "Gasconade Dolomite",
    "UNIT_LABEL": "Og",
    "MAP_UNIT": "Og",
    "GEO_AGE": "Ordovician",
}
ROUBIDOUX = {
    "OBJECTID": 4218,
    "UNIT_NAME": "Roubidoux Formation",
    "UNIT_LABEL": "Or",
    "GEO_AGE": "Ordovician",
}


def test_unit_name_and_label_map_through():
    p = _mo_geology_params(GASCONADE)
    assert p["source_id"] == "4217"
    assert p["unit_name"] == "Gasconade Dolomite"
    assert p["formation"] == "Og"            # UNIT_LABEL → formation (map symbol)
    assert p["lithology"] == "Gasconade Dolomite"


def test_geo_age_maps_to_period():
    p = _mo_geology_params(GASCONADE)
    assert p["period"] == "Ordovician"
    assert "(Ordovician)" in p["description"]


def test_rock_type_extracted_from_unit_name():
    # _extract_rock_type should pick "dolomite" out of "Gasconade Dolomite".
    p = _mo_geology_params(GASCONADE)
    assert p["rock_type"] and "dolomite" in p["rock_type"].lower()


def test_falls_back_to_map_unit_when_no_label():
    attrs = dict(ROUBIDOUX)
    del attrs["UNIT_LABEL"]
    attrs["MAP_UNIT"] = "Or"
    p = _mo_geology_params(attrs)
    assert p["formation"] == "Or"            # MAP_UNIT used when UNIT_LABEL absent


def test_missing_fields_do_not_crash():
    p = _mo_geology_params({"OBJECTID": 1})
    assert p["source_id"] == "1"
    assert p["unit_name"] == ""
    assert p["period"] is None
