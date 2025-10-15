# Progress, current issues, and next steps

Date: 2025-10-15

This document summarizes what we've done so far in the repository, the errors still being encountered during test runs, root-cause hypotheses, and recommended next steps to reach a stable testable state.

## 1) High-level summary (what I implemented)
- Implemented missing app modules and entrypoint:
  - `app/main.py` — `create_app()` factory (lazy FastAPI import). Removed automatic module-level app construction to avoid import-time side effects.
  - `app/services/init_db.py` — seeder for Indian cultural data; adjusted to import `get_db` lazily and to ensure schema existence when called.
- Database core utilities:
  - `app/core/database.py` — Declarative Base, engine/session management, `init_db(reset: bool=False)`, `get_db()` context manager, `reset_db()`, `get_db_stats()`, and helpers.
  - Added `_rebuild_engine()` and lazy engine/session creation to reduce stale-engine issues when tests change `DB_PATH`.
- Models cleaned/added:
  - `app/models/story.py`, `app/models/cultural.py`, `app/models/user.py`, `app/models/sync.py` — Consolidated duplicate definitions, avoided reserved attribute names (e.g., `metadata`), added `__table_args__ = {"extend_existing": True}` where helpful during development.
  - `app/models/__init__.py` — exports for model classes.
- Tests and utilities:
  - Added tests under `tests/` (smoke seed test, API health, story CRUD, conceptnet cache).
  - Tests updated to: set `DB_PATH` to temporary files, reload `app.core.database` after monkeypatching, delete `app.models` package from `sys.modules` and re-import model submodules so model classes register against the intended Base, and call `init_db(reset=True)` to ensure a clean schema.
- Small scripts:
  - Added a DB inspector script earlier to help verify the manual seeder run.

## 2) What worked locally (manual runs)
- Running the seeder manually (outside pytest):
  - `python -m app.services.init_db` created `narrative_intelligence.db` and seeded Indian cultural data (festivals, contexts, mappings).
  - `get_db_stats()` shows expected tables present when run in the workspace environment.

## 3) Test results (what fails now)
- Pytest runs currently produce one persistent failing test:
  - `tests/test_api_health.py::test_health_and_seed` — 500 Internal Server Error from the `/seed-culture` endpoint when run under pytest.
  - The failing database exception is an OperationalError from SQLite when running DDL: "index ix_cultural_contexts_category already exists" (SQLAlchemy reports `sqlite3.OperationalError: index ... already exists`).
- Other tests (story CRUD, conceptnet cache, smoke DB init) were fixed or passing after iterative changes; the API health test remains failing.
- Multiple SAWarnings appear during tests: "declarative base already contains a class... will be replaced" which indicates models are being re-registered multiple times across reloads.
- Deprecation warnings: use of `sqlalchemy.ext.declarative.declarative_base()` (migrate to `sqlalchemy.orm.declarative_base()` or SQLAlchemy registry), and FastAPI `on_event` lifetime deprecation (move to lifespan handlers).

## 4) Root-cause analysis (why this is happening)
- The failures are caused by import-time / module reloading interactions between tests and the app's database/model code:
  - Tests monkeypatch `DB_PATH` and then reload `app.core.database`, expecting a fresh engine bound to the new file.
  - Model modules (`app.models.*`) need to be imported *after* the database module (and after the engine rebuild) so their classes attach to the correct `Base`/MetaData used by `create_all()`.
  - During iterative development many modules got imported at different times; tests attempted to reload or re-import models which caused SQLAlchemy to re-register table/index constructs on top of an existing DB file. When `create_all()` runs again against an existing DB file with the same indexes, SQLite raises "index already exists".
  - Frequent module reloads without a fully clean environment (or without removing the DB file) cause duplicate class registration warnings and index creation conflicts.

## 5) Short-term mitigations already applied
- Tests now:
  - Set `DB_PATH` to a temporary path via `monkeypatch.setenv()`.
  - Reload `app.core.database` using `importlib.reload()`.
  - Remove `app.models` (and specific submodules) from `sys.modules` and re-import the submodules to attempt a clean binding to the freshly reloaded `Base`/engine.
  - Call `adb.init_db(reset=True)` which attempts to remove the DB file before creating schema to avoid index recreation conflicts.
- `app/core/database.py` now contains `_rebuild_engine()` to create a fresh engine+SessionLocal bound to the current `DB_PATH`. `init_db(reset=True)` calls `_rebuild_engine()` so tests that call `init_db(reset=True)` should get a fresh engine.
- `app/main.py` no longer creates an `app` object at import time so importing `app.main` during tests doesn't create the FastAPI instance (which could cause additional startup/DB side effects during import).

## 6) Why the failing API test still occurs
- Even with the above mitigations, there is still a timing/order issue in `tests/test_api_health.py`:
  - `adb.init_db(reset=True)` is being called, but SQLite reports an "index already exists" error — this indicates the DB file may still already contain indexes (file wasn't removed), or multiple model/import registrations still attempt to create the same index while the DB file is partially shared between engines.
  - Possible contributing factors:
    - The global `engine` variable and event listeners may be being registered on a prior engine, causing unexpected DDL to run twice.
    - Some modules may have been imported earlier (by test harness, or by FastAPI internals when TestClient spins the app up), causing duplicate registration of indexes.

## 7) Recommended next steps (short, actionable)
I recommend one of the following approaches (in descending order of reliability and speed-to-fix):

1) Best, robust fix (recommended):
   - Move to a single, explicit DB factory pattern and avoid global engine/SessionLocal at module import time. Provide functions to create an engine and a new declarative base/registry per process (or per test) so tests can call a setup function to get a fully isolated DB environment.
   - Use SQLAlchemy's registry/explicit Base (sqlalchemy.orm.registry) and generate a Base via registry.generate_base(), then ensure models import Base from one, test-controlled place.
   - Add a test fixture (pytest) that:
     - sets the `DB_PATH` env var,
     - calls a small API in `app.core.database` (e.g. `rebuild_for_tests(db_path)` that removes file and builds a new engine and new Base if needed),
     - imports models once (fresh) and calls `init_db()`
   - This will eliminate the fragile sys.modules manipulations and avoid duplicate-registrations.

2) Medium-term quick fix (less invasive):
   - Make `_rebuild_engine()` public and call it from tests immediately after monkeypatching `DB_PATH`, before importing any `app.models.*` modules, and *remove the file* if it exists to avoid leftover indexes:
     - in tests: set DB_PATH -> importlib.reload(app.core.database) -> call app.core.database._rebuild_engine() -> ensure `app.models` is not in sys.modules -> import models -> call init_db(reset=True)
   - Add a small `app.core.database.rebuild_for_tests()` convenience wrapper to encapsulate those steps so tests are simpler and less error-prone.

3) Quick hacky workaround (temporary):
   - In `init_db(reset=True)` delete the DB file and ensure the engine is recreated (already attempted). Ensure `init_db()` always calls `_rebuild_engine()` instead of only when reset True (this increases safety but may cause surprising behavior in some production runs).
   - Alternatively, run tests in a fresh subprocess for each test (slower) so module import state always starts clean.

## 8) Additional low-risk cleanups I recommend
- Replace `declarative_base()` import with `from sqlalchemy.orm import declarative_base` (SQLAlchemy 2.0 style) or migrate to `registry.generate_base()` for cleaner behavior.
- Convert FastAPI `@app.on_event('startup')` handlers to a lifespan context manager (newer pattern; avoids deprecation warnings).
- Remove `__table_args__ = {'extend_existing': True}` when the duplicate-definition issue is fixed (these were used as a guard during iterative development and mask underlying issues).
- Add a test fixture `db_engine` that centralizes DB creation and teardown for tests; use `tmp_path` fixtures to isolate.
- Consider adding Alembic migrations for production-quality schema management.


## Phase 4: Cross-Cultural Fine-Tuning (Personalization & Evaluation Loop)

Goal: teach the model to learn from human feedback and improve its rewriting style per audience.

🧩 Subtasks

- Collect Adaptation Pairs
  - Save original + adapted story + user rating (e.g. "too complex" or "too literal").
  - Store these in a new table `StoryAdaptationFeedback` (schema: id, story_id, original, adapted, rating, meta JSON, created_at).

- Implement Feedback Loop
  - When users rate an adaptation, append the feedback to a small JSONL dataset for training.
  - Example JSONL format:
    {"prompt": "Rewrite for Western 8-year-olds", "input": "...", "output": "...", "rating": 0.8}

- Run PEFT/LoRA Fine-Tuning
  - Use `peft` to apply lightweight fine-tuning on `flan-t5-small`.
  - Train for 2–3 epochs on aggregated feedback pairs and save checkpoint to `models/adaptive-t5-lora/`.

- Integrate Model Reload
  - `AdaptiveStoryteller` should check if the fine-tuned checkpoint exists and prefer loading it automatically.

- Add Evaluation Dashboard
  - New endpoint `/feedback-dashboard` to visualize top-scoring vs low-scoring adaptations and recent feedback.

✅ Outcome
- The model adapts culturally better over time as real users rate outputs.


## Phase 5: Voice & Emotion Layer (Multimodal UX)

Goal: make stories spoken, emotional, and immersive.

🧩 Subtasks

- Add Text-to-Speech (TTS)
  - Use `gTTS` (or an offline alternative like `bark` if you add it later) to produce audio.
  - Generate .wav or .mp3 files from the adapted story text.
  - Store generated audio in `public/audio/adapted_stories/`.

- Add Emotional Prosody
  - Use a small sentiment/emotion classifier (from `transformers`) to tag tone.
  - Adjust TTS parameters (pitch, rate) based on emotion.

- Add Voice Streaming API
  - Endpoint `/stream-audio/{story_id}` streams generated audio chunks for front-end playback.

- Optional: Multilingual Output
  - Use MarianMT models (Helsinki-NLP) via `transformers` to translate adapted stories to Tamil/Hindi/etc.

✅ Outcome
- A "listenable" storytelling engine with emotional prosody for demos and education.


## Phase 6: Integration with ConceptNet + Graphviz UI

Goal: visualize how the system "understands" culture and show explainability for adaptations.

🧩 Subtasks

- Enhance ConceptNet Analyzer
  - Extract 5–10 core cultural/moral concepts from the original story and produce a prioritized list.
  - Feed those concepts into `AdaptiveStoryteller.adapt()` to condition rewrites.

- Add Visualization
  - New endpoint `/visualize-concepts/{story_id}` that renders a concept graph (Graphviz/pyvis).
  - Display nodes like "Light", "Festival", "Community", "Joy" linked by semantic relations.

- Front-End Dashboard
  - Show side-by-side: Original story, Concept graph, Adapted story, Adaptation score, Audio playback button.

✅ Outcome
- A fully explainable storytelling system for demos and research — you can show "why" the AI made cultural changes.

---

If you want, I can implement Phase 4 first (create `StoryAdaptationFeedback` model, JSONL writer, and a simple PEFT training wrapper). Or I can add the `/feedback-dashboard` and TTS endpoints first — tell me which subtask to pick and I’ll implement it next.

