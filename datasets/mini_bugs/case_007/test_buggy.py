"""Tests for the layered configuration renderer."""

from __future__ import annotations

import pytest

from buggy import (
    impacted_sections,
    merged_section,
    parse_config,
    referenced_keys,
    render_section,
    resolution_order,
)


CONFIG_LINES = [
    "# Base database settings",
    "[base]",
    "host = db.local",
    "port = 5432",
    "dsn = postgres://${host}:${port}",
    "",
    "[staging]",
    "extends = base",
    "host = staging.db.local",
    "url = ${dsn}/staging",
    "",
    "[worker]",
    "extends = staging",
    "queue = ${host}:${port}",
    "",
    "[analytics]",
    "extends = base",
    "warehouse = ${dsn}/analytics",
]


# ---------------------------------------------------------------------------
# Tests for parse_config
# ---------------------------------------------------------------------------

def test_parse_config_basic():
    """Parsing should preserve section structure and normalized keys."""
    config = parse_config([
        "[base]",
        "host = db.local",
        "port = 5432",
    ])
    assert config == {
        "base": {
            "host": "db.local",
            "port": "5432",
        }
    }


def test_parse_config_strips_keys_and_ignores_noise():
    """Comments, blank lines, and surrounding key whitespace should be ignored."""
    config = parse_config([
        "",
        "   ",
        "# ignore me",
        "[service]",
        "  host   =  api.local  ",
        " port = 8080 ",
    ])
    assert config == {
        "service": {
            "host": "api.local",
            "port": "8080",
        }
    }


# ---------------------------------------------------------------------------
# Tests for referenced_keys
# ---------------------------------------------------------------------------

def test_referenced_keys_basic():
    """Only placeholder names should be extracted from a value."""
    assert referenced_keys("postgres://${host}:${port}") == {"host", "port"}


def test_referenced_keys_literal_only():
    """A literal value with no placeholders should have no references."""
    assert referenced_keys("db.local") == set()


# ---------------------------------------------------------------------------
# Tests for merged_section
# ---------------------------------------------------------------------------

def test_merged_section_inherits_parent_values():
    """A child section should inherit keys from its parent chain."""
    config = parse_config(CONFIG_LINES)
    assert merged_section(config, "worker") == {
        "host": "staging.db.local",
        "port": "5432",
        "dsn": "postgres://${host}:${port}",
        "url": "${dsn}/staging",
        "queue": "${host}:${port}",
    }


def test_merged_section_child_overrides_parent():
    """Child keys should override parent keys with the same name."""
    config = parse_config(CONFIG_LINES)
    assert merged_section(config, "staging")["host"] == "staging.db.local"


# ---------------------------------------------------------------------------
# Tests for resolution_order
# ---------------------------------------------------------------------------

def test_resolution_order_dependency_then_lexicographic():
    """Keys with no dependencies should be ordered lexicographically first."""
    values = {
        "dsn": "postgres://${host}:${port}",
        "host": "db.local",
        "port": "5432",
        "url": "${dsn}/main",
    }
    assert resolution_order(values) == ["host", "port", "dsn", "url"]


# ---------------------------------------------------------------------------
# Tests for render_section
# ---------------------------------------------------------------------------

def test_render_section_resolves_nested_inherited_values():
    """Rendering should resolve inherited values before nested placeholders."""
    config = parse_config(CONFIG_LINES)
    assert render_section(config, "staging") == {
        "host": "staging.db.local",
        "port": "5432",
        "dsn": "postgres://staging.db.local:5432",
        "url": "postgres://staging.db.local:5432/staging",
    }


def test_render_section_handles_transitive_inheritance():
    """A grandchild section should inherit and resolve values through the chain."""
    config = parse_config(CONFIG_LINES)
    assert render_section(config, "worker") == {
        "host": "staging.db.local",
        "port": "5432",
        "dsn": "postgres://staging.db.local:5432",
        "url": "postgres://staging.db.local:5432/staging",
        "queue": "staging.db.local:5432",
    }


# ---------------------------------------------------------------------------
# Tests for impacted_sections
# ---------------------------------------------------------------------------

def test_impacted_sections_returns_transitive_descendants():
    """Changing a base section should impact all inheriting descendants."""
    config = parse_config(CONFIG_LINES)
    assert impacted_sections(config, {"base"}) == {"staging", "worker", "analytics"}


def test_impacted_sections_excludes_changed_and_unrelated_sections():
    """The changed roots and independent sections should not appear in the result."""
    config = parse_config(CONFIG_LINES + ["[local]", "host = 127.0.0.1"])
    assert impacted_sections(config, {"staging"}) == {"worker"}


# ---------------------------------------------------------------------------
# Hidden tests -- stronger invariants for overfitting detection
# ---------------------------------------------------------------------------

def test_hidden_referenced_keys_support_underscores():
    """Placeholder extraction should support realistic snake_case identifiers."""
    assert referenced_keys("${db_host}:${db_port}") == {"db_host", "db_port"}


def test_hidden_resolution_order_cycle_raises():
    """Interpolation cycles should be rejected explicitly."""
    values = {
        "a": "${b}",
        "b": "${c}",
        "c": "${a}",
    }
    with pytest.raises(ValueError):
        resolution_order(values)


def test_hidden_render_section_resolves_repeated_placeholders():
    """The same placeholder may appear more than once in a rendered value."""
    config = parse_config([
        "[base]",
        "host = db.local",
        "pair = ${host}|${host}",
    ])
    assert render_section(config, "base") == {
        "host": "db.local",
        "pair": "db.local|db.local",
    }


def test_hidden_render_section_supports_snake_case_dependencies():
    """Rendering should resolve multi-character snake_case keys correctly."""
    config = parse_config([
        "[base]",
        "db_host = db.local",
        "db_port = 5432",
        "dsn = postgres://${db_host}:${db_port}",
    ])
    assert render_section(config, "base") == {
        "db_host": "db.local",
        "db_port": "5432",
        "dsn": "postgres://db.local:5432",
    }


def test_hidden_merged_section_inheritance_cycle_raises():
    """Inheritance cycles should be rejected explicitly."""
    config = parse_config([
        "[a]",
        "extends = b",
        "value = 1",
        "[b]",
        "extends = a",
        "value = 2",
    ])
    with pytest.raises(ValueError):
        merged_section(config, "a")


def test_hidden_impacted_sections_multiple_roots_union_descendants():
    """Impact analysis should union the descendant closure of all changed roots."""
    config = parse_config([
        "[base]",
        "value = 1",
        "[feature]",
        "extends = base",
        "flag = on",
        "[worker]",
        "extends = feature",
        "queue = q1",
        "[analytics]",
        "extends = base",
        "warehouse = w1",
    ])
    assert impacted_sections(config, {"base", "feature"}) == {"worker", "analytics"}
