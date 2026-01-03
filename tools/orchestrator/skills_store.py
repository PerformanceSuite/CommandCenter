"""
Skills Store for Long-Running Agent Orchestrator

Two-way skills management:
- Read skills to provide context to agents
- Write learned patterns back after successful runs
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class SkillUpdate:
    """A skill update from an agent run"""
    domain: str
    patterns: list[str] = field(default_factory=list)
    pitfalls: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    confidence: float = 0.7
    source_task: str = ""

    def to_dict(self) -> dict:
        return {
            "domain": self.domain,
            "patterns": self.patterns,
            "pitfalls": self.pitfalls,
            "examples": self.examples,
            "confidence": self.confidence,
            "source_task": self.source_task,
            "timestamp": datetime.utcnow().isoformat(),
        }


class SkillsStore:
    """
    Skills storage with read and write capabilities.

    Directory structure:
    ~/.claude/skills/
    ├── core/                    # Read-only (human-maintained)
    │   ├── autonomy/SKILL.md
    │   └── ...
    ├── learned/                 # Writable (agent-maintained)
    │   ├── domain-name/
    │   │   ├── SKILL.md
    │   │   └── history.jsonl
    │   └── ...
    └── pending/                 # Staging for review
        └── proposed-skill.md
    """

    def __init__(self, skills_dir: str | Path = "~/.claude/skills"):
        self.skills_dir = Path(skills_dir).expanduser()
        self.core_dir = self.skills_dir / "core"
        self.learned_dir = self.skills_dir / "learned"
        self.pending_dir = self.skills_dir / "pending"

        # Also check the default Claude skills location
        self.default_skills_dir = Path("~/.claude/skills").expanduser()

        # Ensure writable directories exist
        for d in [self.learned_dir, self.pending_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def load(self, skill_names: list[str]) -> str:
        """
        Load multiple skills for agent context.

        Search order:
        1. learned/ (agent-generated, may be most recent)
        2. core/ (human-maintained)
        3. default skills location (if different)
        """
        context_parts = []

        for name in skill_names:
            skill_content = self._find_skill(name)
            if skill_content:
                context_parts.append(f"## Skill: {name}\n\n{skill_content}")

        if not context_parts:
            return ""

        return "\n\n---\n\n".join(context_parts)

    def _find_skill(self, name: str) -> Optional[str]:
        """Find a skill by name, checking multiple locations"""

        # Try learned first
        learned_path = self.learned_dir / name / "SKILL.md"
        if learned_path.exists():
            return learned_path.read_text()

        # Try core
        core_path = self.core_dir / name / "SKILL.md"
        if core_path.exists():
            return core_path.read_text()

        # Try default location (if different)
        if self.skills_dir != self.default_skills_dir:
            default_path = self.default_skills_dir / name / "SKILL.md"
            if default_path.exists():
                return default_path.read_text()

        return None

    def write(self, update: SkillUpdate):
        """
        Write a skill update.

        If confidence >= 0.8, writes directly to learned/
        Otherwise, writes to pending/ for human review
        """
        if update.confidence >= 0.8:
            self._write_learned(update)
        else:
            self._write_pending(update)

    def _write_learned(self, update: SkillUpdate):
        """Write directly to learned skills"""
        skill_dir = self.learned_dir / update.domain
        skill_dir.mkdir(parents=True, exist_ok=True)

        skill_path = skill_dir / "SKILL.md"
        history_path = skill_dir / "history.jsonl"

        # Build content
        content = self._format_skill(update)

        # Merge with existing if present
        if skill_path.exists():
            existing = skill_path.read_text()
            content = self._merge_skills(existing, update)

        skill_path.write_text(content)

        # Log to history
        with open(history_path, "a") as f:
            f.write(json.dumps(update.to_dict()) + "\n")

        print(f"📝 Skill updated: learned/{update.domain}")

    def _write_pending(self, update: SkillUpdate):
        """Write to pending for review"""
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        filename = f"{update.domain}-{timestamp}.md"

        path = self.pending_dir / filename
        path.write_text(self._format_skill(update))

        print(f"📋 Skill pending review: pending/{filename}")

    def _format_skill(self, update: SkillUpdate) -> str:
        """Format a skill update as SKILL.md content"""
        patterns_text = "\n".join(f"- {p}" for p in update.patterns) or "No patterns captured."
        pitfalls_text = "\n".join(f"- {p}" for p in update.pitfalls) or "No pitfalls captured."
        examples_text = "\n\n".join(f"```\n{e}\n```" for e in update.examples) or "No examples yet."

        return f"""---
name: {update.domain}
description: Auto-generated from successful agent runs
updated: {datetime.utcnow().isoformat()}
source_task: {update.source_task}
confidence: {update.confidence}
---

# {update.domain.replace('-', ' ').title()}

> Auto-generated skill from agent learnings

## Patterns Learned

{patterns_text}

## Common Pitfalls

{pitfalls_text}

## Example Code

{examples_text}
"""

    def _merge_skills(self, existing: str, update: SkillUpdate) -> str:
        """Merge new learnings into existing skill"""
        # Simple append for now - could be smarter
        new_section = f"""

---

## Update from {update.source_task} ({datetime.utcnow().strftime('%Y-%m-%d')})

### New Patterns

{chr(10).join(f'- {p}' for p in update.patterns)}

### New Pitfalls

{chr(10).join(f'- {p}' for p in update.pitfalls)}
"""
        return existing + new_section

    def approve_pending(self, filename: str) -> bool:
        """Move a pending skill to learned"""
        pending_path = self.pending_dir / filename
        if not pending_path.exists():
            print(f"⚠️ Pending skill not found: {filename}")
            return False

        # Parse domain from filename (domain-timestamp.md)
        domain = filename.rsplit("-", 1)[0]

        # Read and move to learned
        content = pending_path.read_text()

        skill_dir = self.learned_dir / domain
        skill_dir.mkdir(parents=True, exist_ok=True)

        skill_path = skill_dir / "SKILL.md"
        if skill_path.exists():
            # Merge
            existing = skill_path.read_text()
            skill_path.write_text(existing + "\n\n---\n\n" + content)
        else:
            skill_path.write_text(content)

        # Remove from pending
        pending_path.unlink()

        print(f"✅ Skill approved: {domain}")
        return True

    def list_pending(self) -> list[str]:
        """List pending skills awaiting review"""
        return [p.name for p in self.pending_dir.glob("*.md")]

    def list_learned(self) -> list[str]:
        """List all learned skills"""
        return [p.name for p in self.learned_dir.iterdir() if p.is_dir()]
