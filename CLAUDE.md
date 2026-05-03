# Guidelines for Claude Code

## Commands

Start commands with `uv run ...` to run in the uv virtualenv.

* Python: `uv run python ...`
* Tests: `DJANGO_SETTINGS_MODULE=django_settings uv run python -m testsweet`

## File locations

| File                 | Path                                           |
|----------------------|------------------------------------------------|
| Design specs         | claude/specs/YYYY-MM-DD_design-name.md         |
| Implementation plans | claude/plans/YYYY-MM-DD_implementation-name.md |
| Review feedback      | claude/reviews/YYYY-MM-DD_review-name.md       |
