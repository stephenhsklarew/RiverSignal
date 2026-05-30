"""Unit tests for the ohio_stocking adapter (network- and DB-free).

Uses a captured fragment of the ODNR statewide put-and-take table and fake
httpx-client / session objects so the parser + Mad-River scoping logic can be
exercised without a live DB or network call.
"""

import json
import uuid

from pipeline.ingest.ohio_stocking import OhioStockingAdapter, _is_mad_river_water


# A captured fragment of the ODNR trout-stockings table (2026-03 spring
# put-and-take schedule). Two out-of-basin pond rows + one synthetic Mad River
# row + a Buck Creek (Clark Co., Mad River drainage) row to prove scoping.
_ODNR_TABLE_HTML = """
<table>
  <tr><th>Location</th><th>County</th><th>District</th><th>Release Date</th></tr>
  <tr><td>BARNESVILLE RESERVOIR #4</td><td>BELMONT</td><td>4</td><td>03/11/2026</td></tr>
  <tr><td>ENGLEWOOD NORTH PARK POND</td><td>MONTGOMERY</td><td>5</td><td>03/12/2026</td></tr>
  <tr><td>BUCK CREEK (C.J. Brown Tailwater)</td><td>CLARK</td><td>5</td><td>03/18/2026</td></tr>
  <tr><td>MAD RIVER - Eagle City access</td><td>CLARK</td><td>5</td><td>03/19/2026</td></tr>
</table>
"""


class _FakeResp:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        return None


class _FakeClient:
    def __init__(self, text):
        self._text = text

    def get(self, url, **kw):
        return _FakeResp(self._text)


class _FakeScalars:
    def all(self):
        return []


class _FakeResult:
    def scalars(self):
        return _FakeScalars()


class _FakeSession:
    """Records INSERT executions; returns no existing rows for the dedup SELECT."""

    def __init__(self):
        self.inserts = []

    def execute(self, stmt, params=None):
        sql = str(stmt)
        if "INSERT INTO interventions" in sql:
            self.inserts.append(params)
            return _FakeResult()
        # dedup SELECT
        return _FakeResult()

    def commit(self):
        pass


class _FakeSite:
    watershed = "mad_river_oh"
    bbox = {"north": 40.60, "south": 39.65, "east": -83.45, "west": -84.30}


def _make_adapter():
    adapter = OhioStockingAdapter.__new__(OhioStockingAdapter)
    adapter.session = _FakeSession()
    adapter.site_id = uuid.uuid4()
    adapter.from_date = None
    adapter.source_type = "ohio_stocking"
    return adapter


def test_is_mad_river_water():
    assert _is_mad_river_water("MAD RIVER - Eagle City access")
    assert _is_mad_river_water("Buck Creek (C.J. Brown Tailwater)")
    assert _is_mad_river_water("c j brown reservoir")
    assert not _is_mad_river_water("BARNESVILLE RESERVOIR #4")
    assert not _is_mad_river_water("ENGLEWOOD NORTH PARK POND")


def test_parser_scopes_to_mad_river_and_inserts():
    adapter = _make_adapter()
    inserted = adapter._ingest_odnr_trout_stocking(_FakeClient(_ODNR_TABLE_HTML), _FakeSite())

    # Only the Buck Creek + Mad River rows are in-basin; the two ponds are not.
    assert inserted == 2
    waterbodies = sorted(
        json.loads(p["desc"])["waterbody"] for p in adapter.session.inserts
    )
    assert "MAD RIVER - Eagle City access" in waterbodies
    assert any("buck creek" in w.lower() for w in waterbodies)
    assert not any("BARNESVILLE" in w for w in waterbodies)

    # Row shape matches the va_dwr/interventions contract.
    sample = json.loads(adapter.session.inserts[0]["desc"])
    assert sample["source"] == "ohio_dnr"
    assert sample["species"] == "Rainbow Trout"
    assert sample["needs_review"] is True
    assert sample["stocking_date"]  # ISO date present


def test_scoping_guard_skips_non_oh_watershed():
    adapter = _make_adapter()

    class _OtherSite:
        watershed = "mckenzie"
        bbox = {"north": 1, "south": 0, "east": 1, "west": 0}

    # Patch session.get to return a non-OH site; ingest() must early-return.
    adapter.session.get = lambda model, sid: _OtherSite()
    assert adapter.ingest() == (0, 0)
    assert adapter.session.inserts == []
