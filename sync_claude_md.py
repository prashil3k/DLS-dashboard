#!/usr/bin/env python3
"""
Sync Project Card (memory file) into CLAUDE.md's session context section.

Usage:
    python sync_claude_md.py

What it does:
    1. Reads the Project Card from Claude's memory folder
    2. Finds the <!-- SESSION CONTEXT --> markers in CLAUDE.md
    3. Replaces everything between the markers with the Project Card content
    4. Saves CLAUDE.md

The operational reference section (below the markers) is never touched.
"""

import re
from pathlib import Path

# --- Configuration ---
# Project Card location (Claude's hidden memory folder)
PROJECT_CARD = Path.home() / ".claude/projects/-Users-prashil3k-Documents-Claude-Code/memory/project-demo-led-seo.md"

# CLAUDE.md location (in the repo)
CLAUDE_MD = Path(__file__).parent / "CLAUDE.md"

# Markers in CLAUDE.md that bound the synced section
START_MARKER = "<!-- AUTO-SYNCED FROM PROJECT CARD — DO NOT EDIT MANUALLY -->"
END_MARKER = "<!-- END SESSION CONTEXT -->"


def read_project_card() -> str:
    """Read the Project Card, stripping the YAML frontmatter."""
    text = PROJECT_CARD.read_text()
    # Remove YAML frontmatter (between --- delimiters)
    text = re.sub(r'^---\n.*?\n---\n*', '', text, flags=re.DOTALL)
    return text.strip()


def sync():
    card_content = read_project_card()
    claude_md = CLAUDE_MD.read_text()

    if START_MARKER not in claude_md:
        print(f"ERROR: Could not find start marker in CLAUDE.md")
        print(f"  Expected: {START_MARKER}")
        return False

    if END_MARKER not in claude_md:
        print(f"ERROR: Could not find end marker in CLAUDE.md")
        print(f"  Expected: {END_MARKER}")
        return False

    # Replace everything between the markers
    pattern = re.escape(START_MARKER) + r'.*?' + re.escape(END_MARKER)
    replacement = f"{START_MARKER}\n\n{card_content}\n\n{END_MARKER}"
    new_claude_md = re.sub(pattern, replacement, claude_md, flags=re.DOTALL)

    if new_claude_md == claude_md:
        print("No changes — CLAUDE.md is already in sync.")
        return True

    CLAUDE_MD.write_text(new_claude_md)
    print(f"✓ Synced Project Card ({len(card_content.splitlines())} lines) into CLAUDE.md")
    print(f"  Source: {PROJECT_CARD}")
    print(f"  Target: {CLAUDE_MD}")
    return True


if __name__ == "__main__":
    sync()
