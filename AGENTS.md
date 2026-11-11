# Working on Ableton Agent Kit

Keep musical decisions revisable and distinguish measured evidence from subjective listening.
Never add real user audio, projects, lyrics, screenshots, generated reports, credentials or machine-specific paths to this repository. Use synthetic fixtures created during tests.

Run `python -m pytest` and `python -m ruff check .` after changes to code. Native Live tests are separate from mocks; record limitations honestly in docs/verification.md.

Do not change audio devices, drivers, OS settings or hardware monitoring as a side effect of toolkit work. Do not replace an active Remote Script. The staging installer produces a separate copy.

For extension work, every LOM call runs on Live's main thread. Preserve read pagination, identity/value preconditions, automation protection and rollback error visibility. Never add remote eval/exec.

Keep SKILL.md short. Put substantial task-specific detail in linked references; do not load all references for every task. Do not invent successful listening, native saving or native loading from static tests.
