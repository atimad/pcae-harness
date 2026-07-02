"""Tests for Phase 106L — v0.1 RC GitHub Release Publication.

Documentation-focused: verifies the release-publication doc, RC handoff
doc, and release notes make the required (and only the required) release
publication / safety claims. No live GitHub network access is exercised
here; publication itself was performed once, out-of-band, via `gh
release create`. Non-executing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PUBLICATION_PATH = REPO_ROOT / "docs" / "PHASE_106_RC_GITHUB_RELEASE_PUBLICATION.md"
HANDOFF_PATH = REPO_ROOT / "docs" / "RELEASE_HANDOFF_V0_1_RC1.md"
NOTES_DRAFT_PATH = REPO_ROOT / "docs" / "RELEASE_NOTES_V0_1_DRAFT.md"
NOTES_RC1_PATH = REPO_ROOT / "docs" / "RELEASE_NOTES_V0_1_RC1.md"


@pytest.fixture(scope="module")
def publication_text() -> str:
    return PUBLICATION_PATH.read_text()


@pytest.fixture(scope="module")
def handoff_text() -> str:
    return HANDOFF_PATH.read_text()


@pytest.fixture(scope="module")
def notes_draft_text() -> str:
    return NOTES_DRAFT_PATH.read_text()


@pytest.fixture(scope="module")
def notes_rc1_text() -> str:
    return NOTES_RC1_PATH.read_text()


# --- release publication doc ------------------------------------------------


def test_release_publication_doc_exists():
    assert PUBLICATION_PATH.is_file()


def test_release_publication_doc_references_v0_1_0_rc1(publication_text):
    assert "v0.1.0-rc1" in publication_text


def test_release_publication_doc_states_github_release_published(publication_text):
    assert "GitHub Release Publication Result" in publication_text
    assert "created" in publication_text.lower()


def test_release_publication_doc_includes_artifact_names_and_checksums(publication_text):
    assert "pcae_harness-0.1.0.tar.gz" in publication_text
    assert "pcae_harness-0.1.0-py3-none-any.whl" in publication_text
    assert "6c0b896a945beb9b81d28a869dc3a7f3bbc51c8b26f4dc2d1d2a79543f6ccf7d" in publication_text
    assert "f9b52572298b999d1e78a8b4725642bbbb441eb569f8a21c3c723c1c67ff994e" in publication_text


def test_release_publication_doc_states_prerelease_status(publication_text):
    assert "Prerelease" in publication_text
    assert "`true`" in publication_text


def test_release_publication_doc_confirms_no_pypi_publication(publication_text):
    assert "Confirmation: No PyPI Publication" in publication_text


def test_release_publication_doc_confirms_no_github_packages_publication(publication_text):
    assert "Confirmation: No GitHub Packages Publication" in publication_text


def test_release_publication_doc_does_not_create_new_tag(publication_text):
    assert "No new git tag was created" in publication_text


def test_release_publication_doc_does_not_claim_final_v0_1_0_tag(publication_text):
    lowered = " ".join(publication_text.lower().split())
    assert "no final `v0.1.0` tag" in lowered or "no final v0.1.0 tag" in lowered


def test_release_publication_doc_recommends_next_phase_107a(publication_text):
    assert "107A" in publication_text


# --- release handoff doc ----------------------------------------------------


def test_release_handoff_references_github_release_publication(handoff_text):
    assert "GitHub Release Publication" in handoff_text
    assert "PHASE_106_RC_GITHUB_RELEASE_PUBLICATION.md" in handoff_text


def test_release_handoff_states_prerelease_and_no_registry_publication(handoff_text):
    assert "Prerelease:** yes" in handoff_text
    assert "PyPI publication:** not performed" in handoff_text
    assert "GitHub Packages publication:** not performed" in handoff_text


# --- release notes -----------------------------------------------------------


def test_release_notes_draft_mentions_github_release_availability(notes_draft_text):
    assert "RELEASE_NOTES_V0_1_RC1.md" in notes_draft_text
    assert "published" in notes_draft_text.lower()


def test_release_notes_rc1_doc_exists():
    assert NOTES_RC1_PATH.is_file()


def test_release_notes_rc1_references_v0_1_0_rc1(notes_rc1_text):
    assert "v0.1.0-rc1" in notes_rc1_text


def test_release_notes_rc1_states_prerelease(notes_rc1_text):
    assert "prerelease" in notes_rc1_text.lower()


def test_release_notes_rc1_confirms_no_pypi_or_packages_publication(notes_rc1_text):
    lowered = " ".join(notes_rc1_text.lower().split())
    assert "no pypi publication" in lowered
    assert "no github packages publication" in lowered


# --- non-executing / v0.2 boundary claims across all three docs ------------


@pytest.mark.parametrize(
    "fixture_name",
    ["publication_text", "handoff_text", "notes_rc1_text"],
)
def test_docs_state_v0_1_remains_non_executing(fixture_name, request):
    text = request.getfixturevalue(fixture_name)
    assert "non-executing" in text.lower()


@pytest.mark.parametrize(
    "fixture_name",
    ["publication_text", "handoff_text", "notes_rc1_text"],
)
def test_docs_state_v0_2_remains_autonomy_target(fixture_name, request):
    text = request.getfixturevalue(fixture_name)
    assert "v0.2" in text


@pytest.mark.parametrize(
    "fixture_name",
    ["publication_text", "handoff_text", "notes_rc1_text"],
)
def test_docs_do_not_claim_execution_capabilities_exist(fixture_name, request):
    text = request.getfixturevalue(fixture_name)
    lowered = text.lower()
    forbidden_phrases = [
        "runtime enforcement is implemented",
        "pcae autonomously executes",
        "telegram inbound is available",
        "telegram inbound control is enabled",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lowered
