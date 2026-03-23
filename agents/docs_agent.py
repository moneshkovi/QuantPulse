"""
AlphaLoop Docs Agent
---------------------
Detects code changes via git diff and automatically updates the relevant
docs/ files to reflect what changed, why it changed, and how it works.

Uses Claude Agent SDK — runs through your existing Claude Code subscription,
no additional API credits needed.

Usage:
  python agents/docs_agent.py                  # auto-detect changes since last commit
  python agents/docs_agent.py --staged         # only staged changes
  python agents/docs_agent.py --files strategies/mean_reversion.py broker/alpaca_client.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import subprocess
import logging
import anyio
from pathlib import Path
from dotenv import load_dotenv
from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# Maps source files → which doc(s) they affect
DOC_MAP: dict[str, list[str]] = {
    "strategies/mean_reversion.py": ["docs/strategies/mean_reversion.md"],
    "strategies/momentum.py":       ["docs/strategies/momentum.md"],
    "strategies/breakout.py":       ["docs/strategies/breakout.md"],
    "strategies/base.py":           ["docs/strategies/mean_reversion.md",
                                     "docs/strategies/momentum.md",
                                     "docs/strategies/breakout.md"],
    "data/fetch.py":                ["docs/tools.md"],
    "data/universe.py":             ["docs/tools.md"],
    "broker/alpaca_client.py":      ["docs/tools.md"],
    "scanner/scan.py":              ["docs/tools.md"],
    "scanner/eod.py":               ["docs/tools.md"],
    "journal/ledger.py":            ["docs/tools.md"],
    "notifications/email_client.py":["docs/tools.md"],
    "config.py":                    ["docs/risk_management.md"],
}

SYSTEM_PROMPT = """You are the documentation maintainer for AlphaLoop, a personal algorithmic trading system.
Your job is to keep docs/ accurate and educational — written as study material for a developer learning algorithmic trading.
Always explain the WHY behind decisions, not just the what.
Use plain English with concrete examples. Preserve existing structure and tone."""


def _run(cmd: str) -> str:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()


def get_changed_files(staged_only: bool = False) -> list[str]:
    if staged_only:
        output = _run("git diff --cached --name-only")
    else:
        output = _run("git diff HEAD --name-only")
        if not output:
            output = _run("git diff HEAD~1 HEAD --name-only")
    return [f for f in output.splitlines() if f.strip()]


def get_diff_for_file(filepath: str, staged_only: bool = False) -> str:
    if staged_only:
        return _run(f"git diff --cached -- {filepath}")
    diff = _run(f"git diff HEAD -- {filepath}")
    if not diff:
        diff = _run(f"git diff HEAD~1 HEAD -- {filepath}")
    return diff


def resolve_docs_to_update(changed_files: list[str]) -> dict[str, list[str]]:
    """Returns {doc_path: [source files that affect it]}"""
    docs_to_sources: dict[str, list[str]] = {}
    for f in changed_files:
        docs = DOC_MAP.get(f, [])
        if not docs:
            if f.startswith("strategies/") and f.endswith(".py"):
                stem = Path(f).stem
                docs = [f"docs/strategies/{stem}.md"]
            elif f.startswith("docs/"):
                continue
        for doc in docs:
            docs_to_sources.setdefault(doc, []).append(f)
    return docs_to_sources


async def update_doc(doc_path: str, source_files: list[str], diffs: dict[str, str]) -> None:
    doc_exists = Path(doc_path).exists()
    current_doc = Path(doc_path).read_text() if doc_exists else ""

    # Build the prompt with full context
    diff_context = ""
    for sf in source_files:
        diff = diffs.get(sf, "")
        if diff:
            diff_context += f"\n\n**{sf} — git diff (what changed):**\n```diff\n{diff}\n```"

    if doc_exists:
        prompt = f"""Update the documentation file `{doc_path}` to reflect recent changes in: {', '.join(source_files)}.

{diff_context}

Current doc content:
---
{current_doc}
---

Rules:
- Keep all existing explanations that are still accurate
- Update sections that are now outdated
- Add new sections for new functionality
- Explain the WHY — this is study material for the developer learning algo trading
- Do NOT add content about things that didn't change
- Return ONLY the full updated markdown. No preamble.

Write the updated content directly to `{doc_path}`."""
    else:
        source_content = ""
        for sf in source_files:
            if Path(sf).exists():
                source_content += f"\n\n**{sf}:**\n```python\n{Path(sf).read_text()}\n```"

        prompt = f"""Create a new documentation file at `{doc_path}` for the newly created file(s): {', '.join(source_files)}.

{source_content}
{diff_context}

The doc should:
- Explain what this code does and WHY it was built this way
- Cover the academic/practical foundation behind any algorithms
- Explain all key parameters, thresholds, rules — why these specific values?
- Be study material for someone learning algorithmic trading
- Use plain English with concrete examples
- Include relevant references if applicable

Write the content directly to `{doc_path}`."""

    logger.info(f"Agent updating: {doc_path}")

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            cwd=str(Path(__file__).parent.parent),
            allowed_tools=["Read", "Write", "Edit"],
            permission_mode="acceptEdits",
            system_prompt=SYSTEM_PROMPT,
            max_turns=5
        )
    ):
        if isinstance(message, ResultMessage):
            logger.info(f"Done: {doc_path} — {message.stop_reason}")


async def run_async(files: list[str] = None, staged_only: bool = False) -> None:
    # Determine changed files
    if files:
        changed = files
        logger.info(f"Processing provided files: {changed}")
    else:
        changed = get_changed_files(staged_only=staged_only)
        logger.info(f"Detected {len(changed)} changed file(s): {changed}")

    if not changed:
        logger.info("No changed files — nothing to do")
        return

    diffs = {f: get_diff_for_file(f, staged_only=staged_only) for f in changed}
    docs_to_update = resolve_docs_to_update(changed)

    if not docs_to_update:
        logger.info("No docs mapped to changed files — nothing to update")
        return

    logger.info(f"Docs to update: {list(docs_to_update.keys())}")

    for doc_path, source_files in docs_to_update.items():
        logger.info(f"\n{'='*60}\nUpdating: {doc_path}\nTriggered by: {source_files}\n{'='*60}")
        try:
            await update_doc(doc_path, source_files, diffs)
        except Exception as e:
            logger.error(f"Failed to update {doc_path}: {e}")

    logger.info("\nDocs agent complete.")


def run(files: list[str] = None, staged_only: bool = False) -> None:
    anyio.run(run_async, files, staged_only)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update docs/ based on code changes")
    parser.add_argument("--staged", action="store_true", help="Only consider staged changes")
    parser.add_argument("--files", nargs="+", help="Specific files to process")
    args = parser.parse_args()
    run(files=args.files, staged_only=args.staged)
