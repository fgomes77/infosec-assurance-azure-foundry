"""Offline tests for the SharePoint list provisioning spec.

The lists are where the platform's state of record lives — the portfolio, the
score history, the evidence cache, the research ledger. They were provisioned
by hand from a click-path, and their documented column names had drifted from
the names functions/delivery/function_app.py actually writes: a site built to
the documentation would have taken a Graph 400 on every portfolio_update and
history_append, in production, on the write that matters.

These tests are that class of failure, encoded. The last one is the important
one: it proves the gate still catches the drift, so the gate cannot rot into a
green tick that checks nothing.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent          # scripts/
sys.path.insert(0, str(HERE))

import provision_sharepoint_lists as prov  # noqa: E402


@pytest.fixture(autouse=True)
def restore_spec():
    """Every test may mutate the spec; none may leak into the next."""
    saved = copy.deepcopy(prov.LISTS)
    yield
    prov.LISTS.clear()
    prov.LISTS.update(saved)


def test_spec_matches_the_code_that_writes_it():
    assert prov.check() == []


def test_every_written_list_has_a_spec():
    written = prov.written_fields()
    assert written, "no _list_upsert call site parsed — the gate is inert"
    for const in written:
        assert const in prov.LISTS, f"{const} is written but never provisioned"


def test_upsert_keys_are_indexed():
    """An unindexed key still works — until the list passes the 5 000-item view
    threshold, when the $filter starts failing and the cache/ledger degrades to
    a permanent miss that nobody notices."""
    for const, spec in prov.LISTS.items():
        indexed = {c[0] for c in spec["columns"] if c[2]}
        for key in spec["key"]:
            assert key in indexed, f"{const}: {key} must be indexed"


def test_json_bearing_columns_are_multiline():
    """Facts and the ledger's free text hold extracted JSON and page titles; a
    single-line text column truncates them at 255 characters, silently."""
    for const in ("EVIDENCE_CACHE_LIST", "RESEARCH_LEDGER_LIST"):
        kinds = {c[0]: c[1] for c in prov.LISTS[const]["columns"]}
        assert kinds["Facts"] == "note"
    ledger = {c[0]: c[1] for c in prov.LISTS["RESEARCH_LEDGER_LIST"]["columns"]}
    for col in ("Query", "Url", "Citation"):
        assert ledger[col] == "note", f"{col} can exceed a text column"


def test_history_is_append_only():
    """A score history that upserts is not a history: re-running an assessment
    would overwrite the trend it exists to show."""
    assert prov.LISTS["HISTORY_LIST"]["key"] == []


def test_every_column_kind_is_renderable():
    for const, spec in prov.LISTS.items():
        for col, kind, _ in spec["columns"]:
            assert kind in prov.KINDS, f"{const}.{col}: unknown kind {kind}"


@pytest.mark.parametrize("mutate,expected", [
    # a column the Function writes is missing from the spec
    (lambda s: s["PORTFOLIO_LIST"]["columns"].remove(
        next(c for c in s["PORTFOLIO_LIST"]["columns"] if c[0] == "ApprovedBy")),
     "ApprovedBy"),
    # the exact drift that was in sharepoint/README.md before this gate existed
    (lambda s: s["HISTORY_LIST"].update(
        {"columns": [("SupplierName", "text", True), ("ServiceName", "text", True)]}),
     "Supplier"),
    # an upsert key that is not indexed
    (lambda s: s["EVIDENCE_CACHE_LIST"].update(
        {"columns": [(c[0], c[1], False) for c in s["EVIDENCE_CACHE_LIST"]["columns"]]}),
     "CacheKey"),
])
def test_the_gate_catches_drift(mutate, expected):
    mutate(prov.LISTS)
    problems = prov.check()
    assert problems, "drift introduced but the gate stayed green"
    assert any(expected in p for p in problems), problems
