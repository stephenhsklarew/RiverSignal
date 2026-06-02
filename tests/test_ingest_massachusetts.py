"""Unit tests for the massachusetts adapter (network- and DB-free).

Exercises the MassWildlife stocking parser + Ipswich-basin scoping with a
synthetic stocking table and fake httpx-client / session objects. Also covers
the two graceful-degradation paths (mass.gov 403 UA-gating; no server-rendered
table) and the watershed-scoping guard.
"""

import json
import uuid

from pipeline.ingest.massachusetts import MassachusettsDataAdapter, _is_ipswich_water


# Synthetic MassWildlife-style stocking table: header + 2 Ipswich-basin rows
# (Ipswich River/Topsfield, Boston Brook/Middleton) + 1 out-of-basin row
# (Walden Pond/Concord — Sudbury-Assabet-Concord drainage, not Ipswich).
_MA_TABLE_HTML = """
<table>
  <tr><th>Date Stocked</th><th>Water Body</th><th>Town</th><th>Species</th></tr>
  <tr><td>04/15/2026</td><td>Ipswich River</td><td>Topsfield</td><td>Rainbow Trout</td></tr>
  <tr><td>04/22/2026</td><td>Boston Brook</td><td>Middleton</td><td>Brook Trout, Brown Trout</td></tr>
  <tr><td>04/18/2026</td><td>Walden Pond</td><td>Concord</td><td>Rainbow Trout</td></tr>
</table>
"""


class _FakeResp:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        return None


class _FakeClient:
    def __init__(self, text, status_code=200):
        self._text = text
        self._status = status_code

    def get(self, url, **kw):
        return _FakeResp(self._text, self._status)


class _FakeScalars:
    def all(self):
        return []


class _FakeResult:
    def scalars(self):
        return _FakeScalars()


class _FakeSession:
    def __init__(self):
        self.inserts = []

    def execute(self, stmt, params=None):
        if "INSERT INTO interventions" in str(stmt):
            self.inserts.append(params)
        return _FakeResult()

    def commit(self):
        pass


class _FakeSite:
    watershed = "ipswich_river_ma"
    bbox = {"north": 42.78, "south": 42.46, "east": -70.68, "west": -71.25}


def _make_adapter():
    a = MassachusettsDataAdapter.__new__(MassachusettsDataAdapter)
    a.session = _FakeSession()
    a.site_id = uuid.uuid4()
    a.from_date = None
    a.source_type = "massachusetts"
    return a


def test_is_ipswich_water():
    assert _is_ipswich_water("Ipswich River", "Topsfield")
    assert _is_ipswich_water("Boston Brook", "Middleton")
    assert _is_ipswich_water("Some Unlisted Pond", "Ipswich")   # town signal
    assert not _is_ipswich_water("Walden Pond", "Concord")
    assert not _is_ipswich_water("Quabbin Reservoir", "Belchertown")


def test_parser_scopes_to_ipswich_and_inserts():
    a = _make_adapter()
    inserted = a._ingest_dfw_stocking(_FakeClient(_MA_TABLE_HTML), _FakeSite())

    # Ipswich River (1 species) + Boston Brook (2 species) = 3 rows; Walden out.
    assert inserted == 3
    waters = sorted(json.loads(p["desc"])["waterbody"] for p in a.session.inserts)
    assert any(w == "Ipswich River" for w in waters)
    assert any(w == "Boston Brook" for w in waters)
    assert not any("Walden" in w for w in waters)

    sample = json.loads(a.session.inserts[0]["desc"])
    assert sample["source"] == "ma_dfw"
    assert sample["stocking_date"]
    assert sample["species"]


def test_403_degrades_to_zero():
    a = _make_adapter()
    assert a._ingest_dfw_stocking(_FakeClient("", status_code=403), _FakeSite()) == 0
    assert a.session.inserts == []


def test_no_table_degrades_to_zero():
    a = _make_adapter()
    html = "<html><body><div>JS-rendered app, no table</div></body></html>"
    assert a._ingest_dfw_stocking(_FakeClient(html), _FakeSite()) == 0
    assert a.session.inserts == []


def test_scoping_guard_skips_non_ma_watershed():
    a = _make_adapter()

    class _OtherSite:
        watershed = "mckenzie"
        bbox = {"north": 1, "south": 0, "east": 1, "west": 0}

    a.session.get = lambda model, sid: _OtherSite()
    assert a.ingest() == (0, 0)
    assert a.session.inserts == []
