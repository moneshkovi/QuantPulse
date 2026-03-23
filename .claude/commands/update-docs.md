Detect what source files changed (use `git diff HEAD --name-only` or `git diff HEAD~1 HEAD --name-only` if that returns nothing), then update the relevant files in `docs/` to reflect those changes.

**Doc mapping** — which source file affects which doc:
- `strategies/mean_reversion.py` → `docs/strategies/mean_reversion.md`
- `strategies/momentum.py` → `docs/strategies/momentum.md`
- `strategies/breakout.py` → `docs/strategies/breakout.md`
- `strategies/base.py` → all three strategy docs
- `data/fetch.py`, `data/universe.py`, `broker/alpaca_client.py`, `scanner/scan.py`, `scanner/eod.py`, `journal/ledger.py`, `notifications/email_client.py` → `docs/tools.md`
- `config.py` → `docs/risk_management.md`
- Any new `strategies/*.py` file → create a new `docs/strategies/<name>.md`

**Rules for updating each doc:**
- Read the current doc first
- Read the changed source file to understand what actually changed
- Keep all existing explanations that are still accurate
- Update only sections that are now outdated
- Add new sections for new functionality
- Explain the WHY — these docs are study material for learning algorithmic trading
- Do NOT add content about things that didn't change
- Write in plain English with concrete examples
- Preserve existing structure and tone
