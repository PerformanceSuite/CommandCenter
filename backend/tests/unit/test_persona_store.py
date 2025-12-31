"""
Tests for the Persona Store.
"""

import tempfile
from pathlib import Path

import pytest
from libs.agent_framework.persona_store import Persona, PersonaStore


class TestPersonaStore:
    """Tests for the PersonaStore class."""

    def test_list_builtin_personas(self):
        """Should list built-in personas."""
        store = PersonaStore()
        personas = store.list()

        # Should have at least the built-in personas
        names = [p.name for p in personas]
        assert "backend-coder" in names
        assert "frontend-coder" in names
        assert "reviewer" in names
        assert "challenger" in names
        assert "arbiter" in names

    def test_list_by_category(self):
        """Should filter personas by category."""
        store = PersonaStore()

        coding_personas = store.list(category="coding")
        assert all(p.category == "coding" for p in coding_personas)
        assert len(coding_personas) >= 2  # backend-coder, frontend-coder

        verification_personas = store.list(category="verification")
        assert all(p.category == "verification" for p in verification_personas)

    def test_get_persona(self):
        """Should get a specific persona by name."""
        store = PersonaStore()
        persona = store.get("backend-coder")

        assert persona.name == "backend-coder"
        assert persona.display_name == "Backend Coder"
        assert persona.category == "coding"
        assert "python" in persona.preferred_languages
        assert persona.requires_sandbox is True
        assert len(persona.system_prompt) > 100

    def test_get_nonexistent_persona(self):
        """Should raise FileNotFoundError for nonexistent persona."""
        store = PersonaStore()

        with pytest.raises(FileNotFoundError):
            store.get("nonexistent-persona")

    def test_save_and_get_persona(self):
        """Should save and retrieve a custom persona."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PersonaStore(personas_dir=Path(tmpdir))

            persona = Persona(
                name="test-agent",
                display_name="Test Agent",
                description="A test agent",
                system_prompt="You are a test agent.",
                category="custom",
                tags=["test"],
            )

            store.save(persona)

            # Should be able to retrieve it
            retrieved = store.get("test-agent")
            assert retrieved.name == "test-agent"
            assert retrieved.display_name == "Test Agent"
            assert retrieved.system_prompt == "You are a test agent."

    def test_delete_persona(self):
        """Should delete a persona."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PersonaStore(personas_dir=Path(tmpdir))

            # Create a persona
            persona = Persona(
                name="to-delete",
                display_name="To Delete",
                description="Will be deleted",
                system_prompt="You will be deleted.",
            )
            store.save(persona)

            # Verify it exists
            assert store.exists("to-delete")

            # Delete it
            result = store.delete("to-delete")
            assert result is True

            # Verify it's gone
            assert not store.exists("to-delete")

    def test_delete_nonexistent_returns_false(self):
        """Should return False when deleting nonexistent persona."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = PersonaStore(personas_dir=Path(tmpdir))

            result = store.delete("nonexistent")
            assert result is False

    def test_exists(self):
        """Should check if persona exists."""
        store = PersonaStore()

        assert store.exists("backend-coder") is True
        assert store.exists("nonexistent-persona") is False

    def test_persona_to_dict(self):
        """Should convert persona to dictionary."""
        persona = Persona(
            name="test",
            display_name="Test",
            description="A test",
            system_prompt="You are a test.",
            category="custom",
            model="claude-sonnet-4-20250514",
            temperature=0.5,
            tags=["test", "example"],
        )

        d = persona.to_dict()

        assert d["name"] == "test"
        assert d["display_name"] == "Test"
        assert d["system_prompt"] == "You are a test."
        assert d["temperature"] == 0.5
        assert d["tags"] == ["test", "example"]


class TestBuiltinPersonas:
    """Tests for the built-in personas."""

    def test_backend_coder_has_required_fields(self):
        """Backend coder should have all required fields."""
        store = PersonaStore()
        p = store.get("backend-coder")

        assert p.name == "backend-coder"
        assert p.category == "coding"
        assert p.requires_sandbox is True
        assert "python" in p.preferred_languages
        assert "fastapi" in p.system_prompt.lower() or "FastAPI" in p.system_prompt

    def test_frontend_coder_has_required_fields(self):
        """Frontend coder should have all required fields."""
        store = PersonaStore()
        p = store.get("frontend-coder")

        assert p.name == "frontend-coder"
        assert p.category == "coding"
        assert p.requires_sandbox is True
        assert "typescript" in p.preferred_languages
        assert "react" in p.system_prompt.lower() or "React" in p.system_prompt

    def test_reviewer_has_required_fields(self):
        """Reviewer should have all required fields."""
        store = PersonaStore()
        p = store.get("reviewer")

        assert p.name == "reviewer"
        assert p.category == "verification"
        assert "json" in p.system_prompt.lower()  # Should output JSON

    def test_challenger_has_required_fields(self):
        """Challenger should have all required fields."""
        store = PersonaStore()
        p = store.get("challenger")

        assert p.name == "challenger"
        assert p.category == "verification"
        assert p.requires_sandbox is True
        assert "dialectic" in p.system_prompt.lower() or "methodology" in p.system_prompt.lower()

    def test_arbiter_has_required_fields(self):
        """Arbiter should have all required fields."""
        store = PersonaStore()
        p = store.get("arbiter")

        assert p.name == "arbiter"
        assert p.category == "synthesis"
        assert p.requires_sandbox is False  # Arbiter works with text, not code
        assert "verdict" in p.system_prompt.lower()
