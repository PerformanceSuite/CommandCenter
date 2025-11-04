"""Tests for streaming event filters."""
import pytest
from app.streaming.filters import matches_subject_pattern


def test_matches_subject_exact():
    """Test exact subject matching."""
    assert matches_subject_pattern(
        "hub.local.project.created",
        "hub.local.project.created"
    )
    assert not matches_subject_pattern(
        "hub.local.project.created",
        "hub.local.project.deleted"
    )


def test_matches_subject_single_wildcard():
    """Test single token wildcard (*)."""
    pattern = "hub.*.project.created"

    assert matches_subject_pattern("hub.local.project.created", pattern)
    assert matches_subject_pattern("hub.remote.project.created", pattern)
    assert not matches_subject_pattern("hub.local.task.created", pattern)
    assert not matches_subject_pattern("hub.local.deep.project.created", pattern)


def test_matches_subject_multi_wildcard():
    """Test multi-token wildcard (>)."""
    pattern = "hub.>"

    assert matches_subject_pattern("hub.local.project.created", pattern)
    assert matches_subject_pattern("hub.remote", pattern)
    assert matches_subject_pattern("hub.a.b.c.d.e", pattern)
    assert not matches_subject_pattern("other.local.project", pattern)


def test_matches_subject_combined_wildcards():
    """Test combining wildcards."""
    pattern = "hub.*.health.>"

    assert matches_subject_pattern("hub.local.health.postgres", pattern)
    assert matches_subject_pattern("hub.local.health.redis.up", pattern)
    assert not matches_subject_pattern("hub.local.project.created", pattern)


def test_matches_subject_wildcard_all():
    """Test wildcard matching all."""
    assert matches_subject_pattern("anything.here", "*")
    assert matches_subject_pattern("hub.test.created", ">")
