"""
Tests for tools/interactions.py — Supplement Interaction Checker.

Covers:
- Interaction dataclass and display
- Database completeness checks
- lookup_interactions() — bilateral / severity filtering
- lookup_single() — single compound
- format_interaction_report()
- Evidence tier validation
- Severity ordering
"""
from kiwi_core.tools.interactions import (
    INTERACTION_DB,
    SEVERITY_EMOJI,
    SEVERITY_ORDER,
    Interaction,
    _make_key,
    format_interaction_report,
    lookup_interactions,
    lookup_single,
)

# ── Database Integrity ─────────────────────────────────────────────────────────

def test_all_interactions_have_required_fields():
    """Every interaction must have compound_a, compound_b, severity, mechanism, recommendation."""
    for ix in INTERACTION_DB:
        assert ix.compound_a, f"Missing compound_a: {ix}"
        assert ix.compound_b, f"Missing compound_b: {ix}"
        assert ix.severity in SEVERITY_ORDER, f"Invalid severity '{ix.severity}': {ix}"
        assert len(ix.mechanism) > 20, f"Mechanism too short: {ix.compound_a}+{ix.compound_b}"
        assert len(ix.recommendation) > 10, f"Recommendation too short: {ix.compound_a}+{ix.compound_b}"


def test_evidence_tiers_valid():
    """All evidence tiers must be one of the defined emoji levels."""
    valid_tiers = {"🟢", "🟡", "🟠", "🔵"}
    for ix in INTERACTION_DB:
        assert ix.evidence_tier in valid_tiers, (
            f"Invalid tier '{ix.evidence_tier}' for {ix.compound_a}+{ix.compound_b}"
        )


def test_database_has_minimum_interactions():
    """Must have at least 10 interactions covering multiple categories."""
    assert len(INTERACTION_DB) >= 10


def test_database_covers_all_severity_levels():
    """Database should include synergistic, caution, avoid categories."""
    severities = {ix.severity for ix in INTERACTION_DB}
    assert "synergistic" in severities
    assert "caution" in severities
    assert "avoid" in severities


def test_severity_ordering_values():
    """Severity order should put avoid first (most dangerous)."""
    assert SEVERITY_ORDER["avoid"] < SEVERITY_ORDER["caution"]
    assert SEVERITY_ORDER["caution"] < SEVERITY_ORDER["monitor"]
    assert SEVERITY_ORDER["monitor"] < SEVERITY_ORDER["synergistic"]


def test_all_severities_have_emoji():
    """Every severity level must have a display emoji."""
    for sev in SEVERITY_ORDER:
        assert sev in SEVERITY_EMOJI, f"Missing emoji for {sev}"


# ── Interaction Dataclass ──────────────────────────────────────────────────────

def test_interaction_display_format():
    """display() must include compound names, severity, mechanism, recommendation."""
    ix = Interaction(
        compound_a="creatine",
        compound_b="beta-alanine",
        severity="synergistic",
        mechanism="Complementary energy system support.",
        evidence_tier="🟡",
        recommendation="Safe to combine. 3–5g/day each.",
        sources=["Smith 2020 IJSN"],
    )
    text = ix.display()
    assert "Creatine" in text
    assert "Beta-Alanine" in text
    assert "SYNERGISTIC" in text
    assert "Complementary" in text
    assert "Safe to combine" in text
    assert "Smith 2020" in text


def test_interaction_display_no_sources():
    """display() must not crash when sources is empty."""
    ix = Interaction(
        compound_a="zinc",
        compound_b="iron",
        severity="caution",
        mechanism="Competitive absorption via DMT1.",
        evidence_tier="🟢",
        recommendation="Separate by 2 hours.",
    )
    text = ix.display()
    assert "Zinc" in text
    assert "Iron" in text


# ── lookup_interactions() ─────────────────────────────────────────────────────

def test_lookup_known_synergistic_pair():
    """creatine + beta-alanine should return synergistic result."""
    results = lookup_interactions(["creatine", "beta-alanine"])
    names = [(ix.compound_a, ix.compound_b) for ix in results]
    found = any(
        ("creatine" in pair and "beta-alanine" in pair)
        for pair in names
    )
    assert found, "creatine + beta-alanine synergistic interaction not found"


def test_lookup_avoid_combination():
    """melatonin + caffeine should return an avoid interaction."""
    results = lookup_interactions(["melatonin", "caffeine"], min_severity="avoid")
    assert len(results) > 0
    assert results[0].severity == "avoid"
    assert "melatonin" in results[0].compound_a.lower() or "melatonin" in results[0].compound_b.lower()


def test_lookup_returns_most_dangerous_first():
    """Results must be sorted by severity (most dangerous first = lowest SEVERITY_ORDER value)."""
    results = lookup_interactions(["caffeine", "melatonin", "creatine", "beta-alanine"])
    if len(results) >= 2:
        for i in range(len(results) - 1):
            assert SEVERITY_ORDER[results[i].severity] <= SEVERITY_ORDER[results[i + 1].severity]


def test_lookup_case_insensitive():
    """Compound names should be matched case-insensitively."""
    lower = lookup_interactions(["caffeine", "melatonin"])
    upper = lookup_interactions(["CAFFEINE", "MELATONIN"])
    assert len(lower) == len(upper)


def test_lookup_unknown_compounds_returns_empty():
    """Compounds not in the database return no results."""
    results = lookup_interactions(["unicornase", "dragonite"])
    assert results == []


def test_lookup_single_compound():
    """lookup_single returns all interactions involving the compound."""
    results = lookup_single("caffeine")
    assert len(results) > 0
    for ix in results:
        assert "caffeine" in ix.compound_a.lower() or "caffeine" in ix.compound_b.lower()


def test_lookup_single_sorted_by_severity():
    """lookup_single results sorted by severity (most dangerous first)."""
    results = lookup_single("caffeine")
    if len(results) >= 2:
        for i in range(len(results) - 1):
            assert SEVERITY_ORDER[results[i].severity] <= SEVERITY_ORDER[results[i + 1].severity]


def test_lookup_single_unknown_returns_empty():
    """lookup_single for unknown compound returns empty list."""
    assert lookup_single("unobtanium") == []


# ── format_interaction_report() ───────────────────────────────────────────────

def test_format_report_with_interactions():
    """Report with found interactions must show header and severity sections."""
    compounds = ["caffeine", "melatonin"]
    interactions = lookup_interactions(compounds)
    report = format_interaction_report(compounds, interactions)
    assert "Supplement Interaction Report" in report
    assert "Caffeine" in report or "caffeine" in report
    assert "Total interactions found:" in report
    assert "AVOID" in report


def test_format_report_no_interactions():
    """Report with no interactions shows 'No significant interactions' message."""
    compounds = ["unicornase", "dragonite"]
    interactions = []
    report = format_interaction_report(compounds, interactions)
    assert "No significant interactions" in report
    assert "0" in report or "No" in report


def test_format_report_multiple_severity_sections():
    """Report with mixed severity interactions shows multiple sections."""
    compounds = ["caffeine", "creatine", "melatonin", "beta-alanine"]
    interactions = lookup_interactions(compounds, min_severity="synergistic")
    report = format_interaction_report(compounds, interactions)
    # Should have content about the compounds
    assert "Supplement Interaction Report" in report


def test_lookup_melatonin_caffeine_avoid():
    """Melatonin + caffeine is marked as avoid in the database."""
    results = lookup_interactions(["melatonin", "caffeine"])
    avoid_ixs = [ix for ix in results if ix.severity == "avoid"]
    assert len(avoid_ixs) >= 1
    avoid_ix = avoid_ixs[0]
    assert "adenosine" in avoid_ix.mechanism.lower() or "CYP" in avoid_ix.mechanism


def test_lookup_5htp_ssri_avoid():
    """5-HTP + SSRI is marked avoid due to serotonin syndrome risk."""
    results = lookup_interactions(["5-htp", "ssri"])
    assert len(results) > 0
    assert results[0].severity == "avoid"
    assert "serotonin" in results[0].mechanism.lower()


def test_no_duplicate_interactions_in_db():
    """Each compound pair should appear at most once in the database."""
    seen: set[frozenset] = set()
    for ix in INTERACTION_DB:
        pair = frozenset([ix.compound_a.lower(), ix.compound_b.lower()])
        assert pair not in seen, f"Duplicate interaction: {ix.compound_a} + {ix.compound_b}"
        seen.add(pair)


# ── i18n key generation (v0.3.0) ───────────────────────────────────────────────
#
# Each Interaction row carries a `mechanism_key` and `recommendation_key`
# auto-generated by __post_init__ via _make_key(). Frontends (e.g.
# Calsanova's next-intl catalog at apps/web/messages/{locale}/interactions.json)
# look these keys up to render the localized mechanism / recommendation strings.
# The English values on the dataclass remain canonical + dev fallback.


def test_make_key_is_alphabetization_stable():
    """The same compound pair in either order produces the same key."""
    assert _make_key("caffeine", "melatonin", "mechanism") == _make_key(
        "melatonin", "caffeine", "mechanism"
    )
    assert _make_key("vitamin c", "iron", "recommendation") == _make_key(
        "iron", "vitamin c", "recommendation"
    )


def test_make_key_normalizes_special_chars():
    """Whitespace, hyphens, dots, parens all collapse to underscores so
    the resulting key is safe for both JSON object keys and next-intl
    namespace path components."""
    assert _make_key("Vitamin C", "Iron", "mechanism") == "iron__vitamin_c__mechanism"
    assert _make_key("Caffeine", "L-Theanine", "mechanism") == "caffeine__l_theanine__mechanism"
    assert _make_key("CoQ10 (ubiquinol)", "Statins", "recommendation") == (
        "coq10_ubiquinol__statins__recommendation"
    )


def test_make_key_is_idempotent():
    """Repeated calls with identical inputs produce identical output."""
    a = _make_key("Caffeine", "L-Theanine", "mechanism")
    b = _make_key("Caffeine", "L-Theanine", "mechanism")
    c = _make_key("caffeine", "l-theanine", "mechanism")
    assert a == b == c


def test_post_init_auto_fills_keys_when_blank():
    """An Interaction constructed without explicit keys gets them filled
    by __post_init__ from compound_a + compound_b + field name."""
    ix = Interaction(
        compound_a="X", compound_b="Y",
        severity="caution",
        mechanism="m", evidence_tier="🟡", recommendation="r",
    )
    assert ix.mechanism_key == "x__y__mechanism"
    assert ix.recommendation_key == "x__y__recommendation"


def test_post_init_respects_explicit_keys():
    """Explicit mechanism_key / recommendation_key are NOT overwritten."""
    ix = Interaction(
        compound_a="X", compound_b="Y",
        severity="caution",
        mechanism="m", evidence_tier="🟡", recommendation="r",
        mechanism_key="custom__mechanism_key",
    )
    assert ix.mechanism_key == "custom__mechanism_key"
    # Only the empty one gets filled.
    assert ix.recommendation_key == "x__y__recommendation"


def test_db_keys_are_globally_unique_no_collisions():
    """Every (mechanism_key, recommendation_key) across INTERACTION_DB is
    unique. Formalizes the implicit "one row per compound pair" invariant
    so a future contributor adding a colliding row gets a CI red instead
    of silently shipping the wrong translation under one key."""
    mechanism_keys = [r.mechanism_key for r in INTERACTION_DB]
    recommendation_keys = [r.recommendation_key for r in INTERACTION_DB]
    assert len(mechanism_keys) == len(set(mechanism_keys)), (
        "Duplicate mechanism_key in INTERACTION_DB — two rows would share "
        "one localized mechanism string in any translation catalog"
    )
    assert len(recommendation_keys) == len(set(recommendation_keys)), (
        "Duplicate recommendation_key in INTERACTION_DB — two rows would "
        "share one localized recommendation string"
    )


def test_db_keys_match_compound_pair_for_every_row():
    """Every existing row's auto-generated keys match what _make_key
    would produce from its compound pair. Catches manual edits that
    accidentally orphan a translation by using a non-canonical key."""
    for ix in INTERACTION_DB:
        expected_mech = _make_key(ix.compound_a, ix.compound_b, "mechanism")
        expected_rec = _make_key(ix.compound_a, ix.compound_b, "recommendation")
        assert ix.mechanism_key == expected_mech, (
            f"{ix.compound_a}+{ix.compound_b}: mechanism_key {ix.mechanism_key!r} "
            f"does not match canonical {expected_mech!r}"
        )
        assert ix.recommendation_key == expected_rec, (
            f"{ix.compound_a}+{ix.compound_b}: recommendation_key {ix.recommendation_key!r} "
            f"does not match canonical {expected_rec!r}"
        )
