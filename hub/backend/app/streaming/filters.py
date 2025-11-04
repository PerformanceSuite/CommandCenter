"""Event filtering utilities for streaming.

Provides NATS-style pattern matching for event subjects.
"""
import re
from typing import Pattern


def matches_subject_pattern(subject: str, pattern: str) -> bool:
    """Match NATS subject against wildcard pattern.

    Patterns:
        * - matches single token (segment between dots)
        > - matches one or more tokens (everything remaining)

    Examples:
        hub.*.health.* matches hub.local-hub.health.postgres
        hub.> matches hub.local-hub.project.created
        hub.*.> matches hub.test.foo.bar.baz

    Args:
        subject: Event subject to test (e.g., 'hub.local.project.created')
        pattern: NATS wildcard pattern (e.g., 'hub.*.project.*')

    Returns:
        True if subject matches pattern
    """
    # Handle special cases
    if pattern == "*":
        return True  # Match anything (single token)
    if pattern == ">":
        return True  # Match anything (all tokens)

    # Convert NATS pattern to regex
    # First, replace > (multi-token wildcard) before escaping dots
    # > can appear at the end or middle: "hub.>" or "hub.*.>"
    if ">" in pattern:
        # Replace > with a placeholder that will become .*
        pattern = pattern.replace(">", "MULTIWILDCARD")

    # Escape dots (literal in NATS, regex special char)
    regex_pattern = pattern.replace(".", r"\.")

    # Replace NATS wildcards with regex equivalents
    # * matches single token (non-dot characters)
    regex_pattern = regex_pattern.replace("*", r"[^.]+")

    # Replace multi-wildcard placeholder with regex
    regex_pattern = regex_pattern.replace("MULTIWILDCARD", ".*")

    # Anchor pattern (must match entire subject)
    regex_pattern = f"^{regex_pattern}$"

    # Compile and test
    compiled: Pattern = re.compile(regex_pattern)
    return bool(compiled.match(subject))
