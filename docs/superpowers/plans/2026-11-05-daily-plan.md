# Daily Plan, 27-Exercise Modules and Songs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the English app into a guided 7-block study day: 46 hand-written modules with 27 exercises each, song dictation/shadowing, minute tracking for calls/watching/reading, tap-to-translate, "teach the AI" calls and local reminders.

**Architecture:** Same stack (Expo app + FastAPI + SQLite). Exercises live as YAML in the repo and are graded without AI. Day-plan state is computed from the day's records; only skips and the Anki check are stored. AI is used only for conversation, reports, translation (cached) and one grammar-tagging call per song.

**Tech Stack:** Python 3 / FastAPI / SQLite / pytest · Expo SDK 58 / expo-router / TypeScript / Jest + RNTL 14 · Piper (local TTS) · faster-whisper (local STT) · Gemini (free profile).

**Spec:** [docs/superpowers/specs/2026-11-05-daily-plan-design.md](../specs/2026-11-05-daily-plan-design.md)

## Global Constraints

- All app copy in pt-BR; exercise content in English with pt-BR `explanation`; theory in pt-BR with English examples.
- Every time shown or entered in the app is in **minutes**.
- Exercises and reviews never call an AI provider (tests assert `providers.report.calls == []` and `providers.chat.calls == []`).
- Song lyrics are stored only in SQLite under `backend/data/` (gitignored). Never write lyrics to any tracked file, test fixture included (use invented lines in tests).
- No new backend dependencies (YouTube title uses `urllib.request`). The only new app dependency is `expo-notifications` (via `npx expo install`).
- Day targets (minutes): grammar 20, music none (task-based), call1 10, watch 45, read 40, call2 10 (cumulative 20), anki check.
- Active-time cap: any single gap counts at most **180 s** (grammar answers and call messages).
- Exercise distribution per module is exactly `BLOCK_PLAN` (Task 1); 27 exercises, ids `e01`–`e27`.
- The "day" is always `deps.clock.today()` (local tz from settings), never UTC date.
- Backend tests: `cd backend && .venv/Scripts/python -m pytest -q`; app tests: `cd app && npx jest` and `npx tsc --noEmit`. In Git Bash prepend `export PATH="/c/Program Files/nodejs:$PATH"` and use `set -o pipefail` when piping.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. A phone keyboard sends curly apostrophes/quotes (`I’m`, `“went”`) → must grade exactly like straight ones (test in Task 1).
2. An answer at 23:30 local time (02:30 UTC next day) → counts for the local day in grammar minutes and the day plan (test in Task 16).
3. Lyrics pasted with CRLF, several blank lines and section labels like `[Chorus]` / `(Verse 2)` on their own line → labels dropped, stanzas still split correctly (test in Task 14).
4. Double-tapping "Responder" sends the same answer twice → one attempt row, first answer kept (test in Task 9).
5. YouTube links in short/mobile/shorts form (`youtu.be/…`, `m.youtube.com/watch?v=…`, `youtube.com/shorts/…`) work; a non-YouTube URL returns `{"title": null}` without any network call (test in Task 12).

---

## File Map

**Backend — new:** `app/exercises.py` (normalize, grade, review picking), `app/reviews.py` (SRS scheduling moved out of report), `app/migrations.py` (column adds, module id migration), `app/daily_plan.py`, `app/call_time.py`, `app/songs.py` (chunking + word diff), `app/ai/song_grammar.py`, `app/ai/translate.py`, `app/routes/exercises.py`, `app/routes/today.py`, `app/routes/calls.py`, `app/routes/songs.py`, `app/routes/words.py`, `app/report_md.py`, `prompts/song_grammar.md`, `prompts/translate.md`, `prompts/teach_persona.md`, `scripts/prefill_audio.py`, `content/exercises/<module_id>.yaml` ×46, `tests/test_real_content.py`, plus one test file per new unit.

**Backend — modified:** `app/content.py`, `app/config.py`, `app/db.py`, `app/main.py`, `app/routes/modules.py`, `app/routes/media.py`, `app/routes/sessions.py`, `app/ai/conversation.py`, `app/ai/report.py`, `app/ai/prompts.py`, `content/modules/*.yaml`, `content/curriculum.yaml`, `tests/builders.py`.

**Backend — removed:** `app/ai/listening.py`, `app/ai/prefill.py`, `app/routes/listening.py` (keep only its `/audio/{name}` route, moved to `app/routes/exercises.py`), `app/scoring.py`, `app/goals.py`, `scripts/prefill_lessons.py`, `prompts/listening.md`, `tests/test_listening.py`, `tests/test_lesson_bank.py`, `tests/test_scoring.py`, `tests/test_goals.py`.

**App — new:** `src/components/exercises/` (one component per type + `ExercisePlayer.tsx`), `src/components/DayTrail.tsx`, `src/components/NextBlockCard.tsx`, `src/components/TappableText.tsx`, `src/components/TranslateSheet.tsx`, `src/components/CallTimer.tsx`, `src/components/WordDiff.tsx`, `src/app/songs/index.tsx`, `src/app/songs/new.tsx`, `src/app/songs/today.tsx`, `src/app/teach.tsx`, `src/download.ts`, `src/reminders.ts`, `src/sentence.ts`.

**App — modified:** `src/types.ts`, `src/api.ts`, `src/app/lesson/[id].tsx`, `src/app/review/[id].tsx`, `src/app/(tabs)/index.tsx`, `src/app/(tabs)/media.tsx`, `src/components/MediaForm.tsx`, `src/app/(tabs)/settings.tsx`, `src/app/chat/[sessionId].tsx`, `src/app/report/[sessionId].tsx`, `src/components/ReportView.tsx`, `src/components/ChatBubble.tsx`, `src/components/MarkdownText.tsx`. **Removed:** `ListeningStep.tsx`, `PillarBar.tsx` and their tests.

---

## Part A — Content and exercises

### Task 1: Answer normalization and grading

**Files:** Create `backend/app/exercises.py` · Test `backend/tests/test_grading.py`

**Interfaces:**
- Produces: `normalize(text: str) -> str`; `is_correct(exercise, answer: str) -> bool` (`exercise` only needs `.answers`; the `Exercise` model arrives in Task 2 — tests use a tiny `SimpleNamespace(answers=[...])` helper `ex(...)`)

`normalize`: NFKC; curly quotes/apostrophes → straight; lowercase; remove commas and `"`; strip leading/trailing `.!?;:` and spaces; collapse whitespace; expand contractions in this order: `won't→will not`, `can't→can not`, `cannot→can not`, `n't→ not`, `'m→ am`, `'re→ are`, `'ve→ have`, `'ll→ will` (`'s` and `'d` stay as typed — content lists both variants when needed). `is_correct` compares `normalize(answer)` with each `normalize(a)` in `exercise.answers`; for `order` the answer arrives as the words joined by spaces.

- [ ] **Step 1: Failing tests**

```python
@pytest.mark.parametrize("given", ["I'm going home.", "i am going home", "I’m going home", "  I'm   going home!  "])
def test_equivalent_forms_are_correct(given):
    assert is_correct(ex(answers=["I'm going home"]), given)

def test_dont_and_do_not_match():
    assert is_correct(ex(answers=["She doesn't like it"]), "she does not like it")

def test_wrong_word_is_wrong():
    assert not is_correct(ex(answers=["I went"]), "I goed")

def test_curly_quotes_in_accepted_answer_also_normalize():
    assert is_correct(ex(answers=["It’s “fine”"]), "it's fine")
```

- [ ] **Step 2–4:** run (FAIL) → implement → run (PASS).
- [ ] **Step 5: Commit** `feat(exercises): answer normalization and grading`.

### Task 2: Exercise schema and loader

**Files:**
- Modify: `backend/app/content.py`, `backend/app/config.py`, `backend/tests/builders.py`, `backend/tests/conftest.py`
- Test: `backend/tests/test_exercise_content.py`

**Interfaces:**
- Produces:
  - `ExerciseType = Literal["choice", "listen", "gap", "dictation", "fix", "transform", "order", "translate"]`
  - `class Exercise(BaseModel)`: `id: str`, `block: Literal[1,2,3]`, `type: ExerciseType`, `prompt: str`, `answers: list[str]` (min 1), `explanation: str`, `options: list[str] | None = None`, `words: list[str] | None = None`, `audio_text: str | None = None`
  - `BLOCK_PLAN: dict[int, dict[str, int]] = {1: {"choice": 5, "listen": 2, "gap": 2}, 2: {"choice": 3, "gap": 1, "fix": 2, "order": 2, "dictation": 1}, 3: {"choice": 2, "listen": 1, "fix": 1, "transform": 2, "translate": 2, "dictation": 1}}`
  - `validate_exercises(exercises: list[Exercise]) -> list[str]` — human-readable problems, empty when valid
  - `ContentRepo.load(modules_dir: str, exercises_dir: str | None = None)`; `ContentRepo.exercises(module_id) -> list[Exercise]` (empty list when the module has no file; ordered by `id`)
  - `Settings.exercises_dir: str = str(BASE_DIR / "content" / "exercises")`
  - builders: `valid_exercises() -> list[dict]` (27 dicts satisfying every rule), `write_exercises(directory, module_id, exercises=None)`
- File format `content/exercises/<module_id>.yaml`: `{module_id: str, exercises: [Exercise...]}`

Validation rules for `validate_exercises` (each produces a message naming the exercise id): exactly 27 exercises; ids exactly `e01`…`e27`; per-block type counts equal `BLOCK_PLAN`; `choice` has 3–4 options and exactly one option whose `normalize()` is in the normalized answers (use `normalize` from Task 1); `listen` and `dictation` need `audio_text`; `listen` options, when present, follow the `choice` rule; `dictation` answers contain `audio_text`; `order` has `words` and the sorted normalized tokens of `answers[0]` equal the sorted normalized `words`; no two exercises share the same `(prompt, audio_text)` pair.

- [ ] **Step 1: Write the failing tests**

```python
def test_valid_exercises_pass():
    assert validate_exercises([Exercise(**e) for e in valid_exercises()]) == []

def test_wrong_block_distribution_is_reported():
    data = valid_exercises(); data[0]["type"] = "gap"  # e01 was a block-1 choice
    problems = validate_exercises([Exercise(**e) for e in data])
    assert any("block 1" in p for p in problems)

def test_choice_needs_exactly_one_correct_option():
    data = valid_exercises(); data[0]["options"] = ["went", "goes", "go"]; data[0]["answers"] = ["went", "goes"]
    assert any("e01" in p for p in validate_exercises([Exercise(**e) for e in data]))

def test_order_words_must_match_answer():
    data = valid_exercises(); order = next(e for e in data if e["type"] == "order"); order["words"] = order["words"][:-1]
    assert any(order["id"] in p for p in validate_exercises([Exercise(**e) for e in data]))

def test_duplicate_prompt_is_reported(): ...  # copy e02's prompt into e03 (both choice) → message names e03

def test_repo_loads_exercises_and_tolerates_missing_files(tmp_path, module_dir):
    ex_dir = tmp_path / "ex"; ex_dir.mkdir(); write_exercises(ex_dir, "b1_futures")
    repo = ContentRepo.load(str(module_dir), str(ex_dir))
    assert len(repo.exercises("b1_futures")) == 27 and repo.exercises("b2_passive_voice") == []
```

- [ ] **Step 2: Run** `pytest tests/test_exercise_content.py -q` → FAIL (`ImportError`).
- [ ] **Step 3: Implement** the models, `BLOCK_PLAN`, `validate_exercises`, the loader change and the builders. `create_app` passes `settings.exercises_dir`; the `settings` fixture sets `exercises_dir=str(tmp_path / "exercises")` and writes `valid_exercises()` for `b1_past_simple_continuous` so API tests have one module with exercises.
- [ ] **Step 4: Run** the file and the full suite → PASS.
- [ ] **Step 5: Commit** `feat(content): exercise schema, block plan and validator`.

### Task 3: New curriculum (46 modules), migration map

**Files:**
- Modify/Create: `backend/content/modules/*.yaml`, `backend/content/curriculum.yaml`
- Create: `backend/app/migrations.py`
- Test: `backend/tests/test_real_content.py`, `backend/tests/test_migrations.py`

**Interfaces:**
- Produces:
  - `MODULE_IDS` (in `test_real_content.py`) — the 46 ids below in order.
  - `MODULE_MIGRATION: dict[str, str]` (old → new) in `app/migrations.py`
  - `migrate_module_ids(conn) -> None` — rewrites `reviews.module_id` (keeps the earliest `next_due` when the new id already has a row), `sessions.module_id`, `mistakes.module_id`; idempotent.
  - `ensure_columns(conn, table: str, columns: dict[str, str]) -> None` — `ALTER TABLE ADD COLUMN` for missing columns (used by later tasks).

**The 46 modules** (`level order id`). B1: 1 `b1_past_simple`, 2 `b1_past_continuous`, 3 `b1_present_perfect`, 4 `b1_future_will`, 5 `b1_future_going_to`, 6 `b1_future_present_continuous`, 7 `b1_first_conditional`, 8 `b1_second_conditional`, 9 `b1_modals_obligation`, 10 `b1_modals_advice`, 11 `b1_comparatives`, 12 `b1_superlatives`, 13 `b1_prepositions_time`, 14 `b1_prepositions_place`, 15 `b1_prepositions_movement`, 16 `b1_verb_ing`, 17 `b1_verb_to`, 18 `b1_phrasal_verbs`, 19 `b1_relative_clauses`. B2: 1 `b2_present_perfect_continuous`, 2 `b2_past_perfect_narrative`, 3 `b2_third_conditional`, 4 `b2_mixed_conditionals`, 5 `b2_passive_basic`, 6 `b2_passive_advanced`, 7 `b2_reported_statements`, 8 `b2_reported_questions`, 9 `b2_deduction_present`, 10 `b2_deduction_past`, 11 `b2_used_to_would`, 12 `b2_be_used_to`, 13 `b2_wish_present`, 14 `b2_wish_past`, 15 `b2_contrast`, 16 `b2_argumentation`. C1: 1 `c1_inversion_negative`, 2 `c1_inversion_conditional`, 3 `c1_it_cleft`, 4 `c1_wh_cleft`, 5 `c1_past_modals_criticism`, 6 `c1_past_modals_possibility`, 7 `c1_causative`, 8 `c1_hedging`, 9 `c1_participle_clauses`, 10 `c1_collocations`, 11 `c1_idioms`.

**`MODULE_MIGRATION`:** `b1_past_simple_continuous→b1_past_simple`, `b1_present_perfect_vs_past→b1_present_perfect`, `b1_futures→b1_future_will`, `b1_first_second_conditionals→b1_first_conditional`, `b1_modals_obligation_advice→b1_modals_obligation`, `b1_comparatives_superlatives→b1_comparatives`, `b1_prepositions→b1_prepositions_time`, `b1_gerund_infinitive→b1_verb_ing`, `b2_third_mixed_conditionals→b2_third_conditional`, `b2_passive_voice→b2_passive_basic`, `b2_reported_speech→b2_reported_statements`, `b2_modals_deduction→b2_deduction_present`, `b2_wish_if_only→b2_wish_present`, `b2_contrast_connectors→b2_contrast`, `c1_inversion→c1_inversion_negative`, `c1_cleft_sentences→c1_it_cleft`, `c1_past_modals→c1_past_modals_criticism`, `c1_collocations_idioms→c1_collocations`.

Content rules for every new/rewritten module YAML: same fields as today; theory 5–8 bullets in pt-BR, starting with the form, then use, then a **Erro comum** line, English examples in italics; each split module gets its own scenario (title, character, goal) and 3–4 `target_structures`; the contrast notes listed in spec §3.1 go into the theory of the second module of the pair. Kept modules keep their file unchanged except `order`. Old ids' files are deleted.

- [ ] **Step 1: Failing tests**

```python
def test_real_curriculum_has_the_46_modules_in_order():
    repo = ContentRepo.load(Settings(_env_file=None).content_dir)
    assert repo.ids() == MODULE_IDS
    assert Counter(m.level for m in repo.all()) == {"B1": 19, "B2": 16, "C1": 11}

def test_every_module_has_theory_with_a_common_mistake_and_a_scenario():
    for m in ContentRepo.load(Settings(_env_file=None).content_dir).all():
        assert "Erro comum" in m.theory_md or "Dica" in m.theory_md, m.id
        assert 3 <= len(m.target_structures) <= 4, m.id

def test_migration_moves_reviews_and_sessions(conn):
    insert(conn, "reviews", module_id="b1_futures", next_due="2026-11-10", interval_days=3, ease=2.5, repetitions=1)
    sid = insert(conn, "sessions", kind="lesson", module_id="b1_futures", started_at="x")
    migrate_module_ids(conn); migrate_module_ids(conn)
    assert conn.execute("SELECT module_id FROM reviews").fetchone()[0] == "b1_future_will"
    assert conn.execute("SELECT module_id FROM sessions WHERE id=?", (sid,)).fetchone()[0] == "b1_future_will"

def test_migration_keeps_earliest_due_when_both_ids_exist(conn): ...  # old due 11-08, new due 11-12 → one row due 11-08
```

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Write** the module YAMLs and `curriculum.yaml`; implement `app/migrations.py`; call `migrate_module_ids(conn)` in `create_app` after `init_schema`.
- [ ] **Step 4: Run** full suite → PASS.
- [ ] **Step 5: Commit** `feat(content): split modules into 46 and migrate old ids`.

### Tasks 4–8: Write the exercises (five independent batches)

Each batch is one task with the same shape; batches touch disjoint files and can run in parallel.

| Task | Modules |
|---|---|
| 4 | B1 orders 1–10 |
| 5 | B1 orders 11–19 |
| 6 | B2 orders 1–8 |
| 7 | B2 orders 9–16 |
| 8 | C1 orders 1–11 |

**Files:** Create `backend/content/exercises/<module_id>.yaml` for each module of the batch · Test `backend/tests/test_real_content.py` (shared, parametrized).

**Interfaces:** Consumes the format and `validate_exercises` (Task 1), `normalize` (Task 2), the module's theory (Task 3).

Authoring rules (beyond the validator): block 1 tests recognition of the form; block 2 builds with support; block 3 produces (the pair contrast lives here for split modules); everyday adult contexts (work, travel, friends, series, music, food); no exercise with two defensible answers unless all are in `answers`; `translate` and `transform` list every natural variant (contracted and full forms, `'s`/`is`); `fix` prompts contain exactly one error; `explanation` one sentence in pt-BR; `listen` `audio_text` ≤ 25 words, `dictation` `audio_text` 6–14 words; use the module's `target_structures`; never quote song lyrics.

- [ ] **Step 1: Add the parametrized test (first batch only; later batches just extend coverage automatically)**

```python
@pytest.mark.parametrize("module_id", [m for m in MODULE_IDS if (EX_DIR / f"{m}.yaml").exists()])
def test_real_exercises_are_valid(module_id):
    assert validate_exercises(REPO.exercises(module_id)) == []
```

- [ ] **Step 2: Write** the batch's YAML files.
- [ ] **Step 3: Run** `pytest tests/test_real_content.py -q` → PASS for the batch's ids.
- [ ] **Step 4: Commit** `content: exercises for <batch>`.

**Task 8 additionally** adds `test_all_46_modules_have_exercises` (`all((EX_DIR / f"{m}.yaml").exists() for m in MODULE_IDS)`) and must be run after Tasks 4–7 are merged.

### Task 9: Lesson exercises API, attempts, module score and audio

**Files:**
- Create: `backend/app/reviews.py`, `backend/app/routes/exercises.py`, `backend/scripts/prefill_audio.py`
- Modify: `backend/app/db.py`, `backend/app/main.py`, `backend/app/routes/modules.py`, `backend/app/ai/report.py`
- Remove: `app/ai/listening.py`, `app/ai/prefill.py`, `app/routes/listening.py`, `app/scoring.py`, `scripts/prefill_lessons.py`, `prompts/listening.md` (and its `PROMPT_VARS` entry), `tests/test_listening.py`, `tests/test_lesson_bank.py`, `tests/test_scoring.py`
- Test: `backend/tests/test_exercises_api.py`, `backend/tests/test_prefill_audio.py`

**Interfaces:**
- Produces:
  - Table `exercise_attempts(id PK, module_id TEXT, exercise_id TEXT, kind TEXT CHECK(kind IN ('lesson','review')), run_id INTEGER, answer TEXT, correct INTEGER, seconds INTEGER, day TEXT, created_at TEXT)` + `UNIQUE INDEX ON (module_id, exercise_id) WHERE kind='lesson'` + `UNIQUE INDEX ON (run_id, exercise_id) WHERE kind='review'`; table `exercise_reports(id, module_id, exercise_id, note, created_at)`; `DROP TABLE IF EXISTS lesson_bank`.
  - `schedule_review(deps, module_id: str, score: int) -> str` in `app/reviews.py` (moved from `report._schedule_review`, uses `deps.clock.today()`, returns next_due iso).
  - `exercise_audio_name(module_id: str, exercise_id: str) -> str` = `f"ex_{module_id}_{exercise_id}.wav"`; `ensure_exercise_audio(deps, module_id, exercise) -> str` (synthesizes with `providers.tts` only when the file is missing; records usage).
  - `completed_module_ids(deps) -> set[str]` now = modules with 27 lesson attempts.
  - `GET /modules/{id}/exercises` → `[{id, block, type, prompt, options, words (shuffled deterministically by seed module_id+id), audio_url|null, answered: bool, result: null | {correct, user_answer, correct_answer, explanation}}]` — never includes `answers` or `audio_text` for unanswered items.
  - `POST /exercises/{module_id}/{exercise_id}/answer` body `{answer: str, seconds: int ≥0, run_id: int|null}` → `{correct, correct_answer, explanation, module_completed: bool, score: int|null, next_due: str|null}`; `seconds` stored as `min(seconds, 180)`; `day = clock.today()`; lesson repeat → returns the stored result unchanged; when the 27th lesson attempt lands, `score = round(100 * correct / 27)`, `schedule_review` runs and `module_completed=True`.
  - `POST /exercises/{module_id}/{exercise_id}/report` body `{note: str}` → `{ok: true}`.
  - `GET /audio/{name}` (moved here unchanged).
  - `finish_session` no longer computes listening or schedules reviews: `final_score = report.score`, `next_due = None`, result drops `listening_score`.
- `scripts/prefill_audio.py [--only ID]`: calls `ensure_exercise_audio` for every `listen`/`dictation` exercise; prints `done/skipped/failed`.

- [ ] **Step 1: Failing tests** (fixture module `b1_past_simple_continuous` has `valid_exercises()`)

```python
def test_listing_hides_answers_until_answered(app_client):
    items = app_client.get("/modules/b1_past_simple_continuous/exercises").json()
    assert len(items) == 27 and all("answers" not in i and "audio_text" not in i for i in items)

def test_answer_is_graded_without_ai(app_client, providers):
    r = app_client.post("/exercises/b1_past_simple_continuous/e01/answer", json={"answer": CORRECT["e01"], "seconds": 12}).json()
    assert r["correct"] is True and providers.report.calls == [] and providers.chat.calls == []

def test_double_submit_keeps_first_answer(app_client, deps):
    url = "/exercises/b1_past_simple_continuous/e01/answer"
    app_client.post(url, json={"answer": "wrong", "seconds": 5}); again = app_client.post(url, json={"answer": CORRECT["e01"], "seconds": 5}).json()
    assert again["correct"] is False
    assert deps.conn.execute("SELECT COUNT(*) FROM exercise_attempts").fetchone()[0] == 1

def test_seconds_are_capped_at_180(app_client, deps): ...  # seconds=999 → stored 180

def test_last_answer_completes_module_and_schedules_review(app_client, deps):
    answer_all(app_client, "b1_past_simple_continuous", wrong={"e01", "e02", "e03"})
    last = deps.conn.execute("SELECT next_due FROM reviews WHERE module_id='b1_past_simple_continuous'").fetchone()
    assert last["next_due"] == "2026-11-04"  # first schedule = tomorrow
    assert app_client.get("/modules").json()["levels"][0]["modules"][0]["completed"] is True

def test_completion_response_has_score(app_client): ...  # 24/27 correct → score 89, module_completed True

def test_resume_shows_answered_items(app_client): ...  # answer e01 → listing marks e01 answered with result

def test_unknown_module_or_exercise_404(app_client): ...

def test_finish_session_no_longer_schedules(app_client, deps, providers): ...  # lesson conversation finish → next_due None, no reviews row
```

`test_prefill_audio.py`: `ensure_exercise_audio` writes the wav once (second call makes no TTS call).

- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement**, delete the removed files, fix imports and the remaining tests that referenced them.
- [ ] **Step 4: Run** full suite → PASS. Then run `python scripts/prefill_audio.py` against the real content once Tasks 4–8 are in (report counts; failures are fine to retry).
- [ ] **Step 5: Commit** `feat: lesson exercises from the bank, graded without AI`.

### Task 10 (review): Reviews from the bank

**Files:** Modify `backend/app/exercises.py`, `backend/app/routes/exercises.py` · Test `backend/tests/test_reviews_bank.py`

**Interfaces:**
- Produces: `pick_review(conn, module_id: str, exercises: list[Exercise], size: int = 9) -> list[Exercise]` — first the exercises whose latest attempt (any kind) was wrong, newest mistakes first; then the rest ordered by oldest latest attempt (never attempted counts as oldest); ties by id.
- `POST /reviews/{module_id}/start` → `{run_id: int, exercises: [same item shape as Task 9, unanswered]}`; `run_id` = new row id in `review_runs(id PK, module_id, started_at, finished_at, score)`.
- Answers go to the Task 9 endpoint with `run_id`; when 9 attempts exist for the run: `score = round(100*correct/9)`, `schedule_review`, response `module_completed=True` and `next_due`.

- [ ] **Step 1: Failing tests**: missed exercises come first; a 9/9 review moves `next_due` forward (3 days after first schedule); review answers never call AI; answering with an unknown `run_id` → 404.
- [ ] **Steps 2–5:** FAIL → implement → PASS → commit `feat: reviews draw from the exercise bank`.

## Part B — Records

### Task 11 (media): Media rows with counts, links and new words

**Files:** Modify `backend/app/routes/media.py`, `backend/app/db.py` · Create `backend/app/routes/words.py` (only the `words` table + insert helper here; routes in Task 15) · Test `backend/tests/test_media.py` (extend)

**Interfaces:**
- `ensure_columns(conn, "media_logs", {"unit_minutes": "INTEGER", "count": "INTEGER", "url": "TEXT", "new_words": "TEXT"})` on startup.
- Table `words(id PK, word TEXT, sentence TEXT, translation TEXT, note TEXT, source TEXT, created_at TEXT, UNIQUE(word, sentence))`; `add_word(conn, word, sentence, translation, note, source, now) -> int` (ignores duplicates, returns existing id).
- `MediaIn` gains `unit_minutes: int|None (1..600)`, `count: int|None (1..100)`, `url: str|None`, `new_words: str|None`. For `category in {"series","movie"}`: `unit_minutes` and `count` required and `minutes = unit_minutes*count` (any `minutes` sent is ignored); otherwise `minutes` required (make it optional in the model and validate per category).
- On create/update with `new_words` (comma or newline separated): each word goes to `add_word(..., sentence="", translation="", note="", source="read:<title>")`.
- `_row` includes the four new fields.

- [ ] **Step 1: Failing tests**: series 22 min × 3 eps → minutes 66; summary sums two series rows + a video row; series without `count` → 422; reading with `new_words="grim, vigilante\nrooftop"` creates 3 words; old rows (null new columns) still list.
- [ ] **Steps 2–5:** FAIL → implement → PASS → commit `feat(media): episode counts, links and new words`.

### Task 12 (youtube): YouTube title lookup

**Files:** Modify `backend/app/routes/media.py` · Test `backend/tests/test_youtube_title.py`

**Interfaces:**
- `youtube_video_url(url: str) -> str | None` — canonical `https://www.youtube.com/watch?v=<id>` for `youtube.com/watch?v=`, `m.youtube.com/watch?v=`, `youtu.be/<id>`, `youtube.com/shorts/<id>`; `None` otherwise.
- `fetch_oembed(url: str) -> dict` (module-level, `urllib.request.urlopen("https://www.youtube.com/oembed?format=json&url=" + quote(url), timeout=5)`), monkeypatched in tests.
- `GET /media/youtube-title?url=` → `{"title": str | None}`; any network/parse error → `null`.

- [ ] **Step 1: Failing tests**: the four URL shapes map to the canonical URL; non-YouTube URL → `{"title": None}` and `fetch_oembed` not called; fetch raising `OSError` → `{"title": None}`; success → title string.
- [ ] **Steps 2–5:** FAIL → implement → PASS → commit `feat(media): fill the YouTube video title from the link`.

### Task 13 (calls): Call time and external calls

**Files:** Create `backend/app/call_time.py`, `backend/app/routes/calls.py` · Modify `backend/app/main.py` · Test `backend/tests/test_call_time.py`

**Interfaces:**
- `active_seconds(times: list[datetime], cap: int = 180) -> int` — sum of `min(gap, cap)` over consecutive sorted times.
- `call_minutes_for_day(deps, day: date) -> int` — app sessions of kinds `lesson|review|free|teach` whose `started_at` falls on `day` in local tz and that have ≥1 user message: events = `started_at` + every message `created_at` + `finished_at` if set; sum `active_seconds` over sessions, plus `call_logs.minutes*60` for the day; result `floor(total/60)`.
- `GET /sessions/{id}/elapsed` → `{"seconds": int}` (same formula plus `now` as last event, for the live timer).
- Table `call_logs(id, date, source, minutes, note, created_at)`; `POST /calls/external {date, source, minutes (1..600), note?}`, `GET /calls?date=` → `{"app_minutes", "external": [...], "total_minutes"}`, `DELETE /calls/external/{id}`, `GET /calls/summary?date=` → day/week totals (Monday-based week like media).

- [ ] **Step 1: Failing tests**: gaps `[0, 60, 600]` s → 60+180 = 240 s; a session with only the assistant opener counts 0; a session started 23:50 local counts on that local day; external 25 min + app 4 min → total 29; elapsed uses `clock.now()`.
- [ ] **Steps 2–5:** FAIL → implement → PASS → commit `feat(calls): call minutes from the app and from outside`.

## Part C — Songs

### Task 14 (songs-core): Chunking and word diff

**Files:** Create `backend/app/songs.py` · Test `backend/tests/test_songs_core.py`

**Interfaces:**
- `@dataclass Chunk: index: int, text: str, repeat_of: int | None`
- `split_chunks(lyrics: str, max_lines: int = 4) -> list[Chunk]` — normalize CRLF; drop lines that are only a section label (`^\s*[\[(].*[\])]\s*$`); stanzas = groups separated by blank lines; each stanza cut into pieces of ≤ `max_lines` lines, balanced (a 5-line stanza → 3+2, not 4+1); `repeat_of` = index of the first earlier chunk with equal `normalize(text)`.
- `word_diff(expected: str, got: str) -> dict` → `{"score": int 0..100, "tokens": [{"word": str, "status": "ok"|"missing"|"wrong"|"extra"}]}` — tokens via `normalize` then split; alignment with `difflib.SequenceMatcher` (equal → ok, delete → missing, replace → wrong (expected words), insert → extra); `score = round(100 * ok / len(expected_tokens))`.

- [ ] **Step 1: Failing tests** (invented lyrics only)

```python
LYRICS = "[Intro]\r\nline one\r\nline two\r\n\r\n\r\nchorus a\nchorus b\n\n(Verse 2)\nv1\nv2\nv3\nv4\nv5\n\nchorus a\nchorus b\n"

def test_split_drops_labels_handles_crlf_and_balances():
    chunks = split_chunks(LYRICS)
    assert [c.text.splitlines() for c in chunks] == [["line one", "line two"], ["chorus a", "chorus b"], ["v1", "v2", "v3"], ["v4", "v5"], ["chorus a", "chorus b"]]
    assert chunks[4].repeat_of == 1 and chunks[1].repeat_of is None

def test_word_diff_marks_missing_and_wrong():
    r = word_diff("his palms are sweaty", "his palm are")
    assert [t["status"] for t in r["tokens"]] == ["ok", "wrong", "ok", "missing"] and r["score"] == 50

def test_empty_lyrics_give_no_chunks():
    assert split_chunks("\n\n[Chorus]\n") == []
```

- [ ] **Steps 2–5:** FAIL → implement → PASS → commit `feat(songs): split lyrics into chunks and compare words`.

### Task 15 (songs-api): Song library, grammar tagging and practice

**Files:** Create `backend/app/ai/song_grammar.py`, `backend/prompts/song_grammar.md`, `backend/app/routes/songs.py` · Modify `backend/app/db.py`, `backend/app/main.py`, `backend/app/ai/prompts.py`, `backend/app/ai/schemas.py` · Test `backend/tests/test_songs_api.py`

**Interfaces:**
- Tables: `songs(id, title, artist, link, lyrics, is_current INTEGER, grammar_status TEXT CHECK IN ('pending','done'), created_at)`, `song_chunks(id, song_id, idx, text, repeat_of INTEGER, highlights TEXT JSON)`, `song_practice(id, chunk_id NULL, song_id, kind TEXT CHECK IN ('dictation','shadow','final'), text, score, day, created_at)`.
- Schema `SongGrammar(BaseModel): chunks: list[ChunkGrammar]`, `ChunkGrammar: index: int, highlights: list[Highlight]`, `Highlight: phrase: str, module_id: str`.
- `tag_song(deps, song_id) -> None` — one `generate_structured(providers.report, …)` call with prompt `song_grammar` (vars: `modules` = "id: title" lines, `chunks` = numbered chunk texts); keeps a highlight only if `module_id` is known and `normalize(phrase)` is contained in `normalize(chunk.text)`; sets `grammar_status='done'`. Errors propagate to the caller.
- `POST /songs {title, artist, link?, lyrics}` → creates song + chunks (422 `empty_lyrics` when `split_chunks` is empty); first song becomes current; tagging is attempted and its failure is swallowed (status stays `pending`). Response `{id, title, artist, link, grammar_status, total_chunks}` where `total_chunks` counts non-repeat chunks.
- `POST /songs/{id}/tag` (retry, errors map like other AI calls), `GET /songs` (with `done_chunks`, `total_chunks`, `is_current`), `PUT /songs/{id}/current`, `DELETE /songs/{id}`.
- Chunk done = has a `dictation` row and a `shadow` row.
- `GET /songs/current/today` → `{song, chunk: {id, idx, text, highlights, module_titles} | null, review_chunks: [repeat chunks with idx between the previous new chunk and this one], progress: {done, total}, stage: "dictation"|"shadow"|"done_today"|"final"|"finished"|"no_song"}`. `final` when all new chunks are done and no `final` row exists; `finished` after a final row exists.
- `POST /songs/chunks/{id}/dictation {text}` → `word_diff(chunk.text, text)` + stores row; `POST /songs/chunks/{id}/shadow` multipart `audio` → STT then `word_diff`; `EmptyTranscript` when nothing heard (row not stored); `POST /songs/{id}/final` multipart `audio` → diff against the whole lyrics without labels, kind `final`.

- [ ] **Step 1: Failing tests**: create song → chunks stored and current; AI failure on create keeps the song with `pending`; tagging drops a highlight whose phrase is not in the chunk and one with an unknown module id; today's chunk advances only after dictation + shadow; a repeat chunk is returned in `review_chunks`, never as `chunk`; final stage after the last chunk; shadow with silent audio → error and no row; lyrics never appear in `GET /songs` list response (only in `/songs/current/today` chunk text).
- [ ] **Steps 2–5:** FAIL → implement → PASS → commit `feat(songs): library, grammar highlights, dictation and shadowing`.

## Part D — The day

### Task 16 (plan): Day plan, skips, Anki and streak

**Files:** Create `backend/app/daily_plan.py`, `backend/app/routes/today.py` · Modify `backend/app/routes/modules.py`, `backend/app/main.py`, `backend/app/db.py` · Remove `backend/app/goals.py`, `backend/tests/test_goals.py` · Test `backend/tests/test_daily_plan.py`

**Interfaces:**
- Consumes: `exercise_attempts` (Task 9/10), `song_practice` (Task 15), `call_minutes_for_day` (Task 13), `media_logs` (Task 11).
- Table `day_state(date TEXT, block TEXT, skipped INTEGER, checked INTEGER, PRIMARY KEY(date, block))`.
- `BLOCKS = ("grammar", "music", "call1", "watch", "read", "call2", "anki")`, `TITLES = {"grammar": "Gramática", "music": "Música", "call1": "Ligação 1", "watch": "Assistir", "read": "Ler", "call2": "Ligação 2", "anki": "Anki"}`, `TARGETS = {"grammar": 20, "call1": 10, "watch": 45, "read": 40, "call2": 10}`.
- `day_plan(deps, day: date) -> dict` → `{"date", "blocks": [{"key", "title", "status": "done"|"current"|"skipped"|"pending", "minutes": int|None, "target": int|None}], "current": key|None, "complete": bool}`.
  - grammar done: a module's 27th lesson attempt has `day == day`, or `sum(seconds)` of the day's lesson+review attempts ≥ 1200; `minutes = floor(sum/60)`.
  - music done: some chunk's later of its dictation/shadow rows has `day == day`, or a `final` row on that day.
  - calls: `total = call_minutes_for_day`; call1 minutes `min(total,10)` done at ≥10; call2 minutes `min(max(total-10,0),10)` done at ≥20.
  - watch/read: sum of `media_logs.minutes` by type; done at target.
  - anki: `checked=1`.
  - status: done wins; otherwise `skipped` if a skip row exists; `current` = first block in `BLOCKS` order that is neither done nor skipped; the rest `pending`.
- `streak(deps, today) -> int` — consecutive `complete` days ending today (or yesterday when today is incomplete), max 366 days scanned.
- Routes: `GET /today` → `day_plan(today)` + `"streak"`; `POST /today/{block}/skip`, `POST /today/{block}/unskip`, `POST /today/anki` body `{checked: bool}` (400 on unknown block). `GET /home` replaces `pillars` with `today` (the plan) and keeps `streak`, `reviews_due`, `next_module`, `usage`.

- [ ] **Step 1: Failing tests**: empty day → current grammar, nothing done; 20 min of answers → grammar done and current music; skipping music makes call1 current and unskip restores; leitura logged before music marks read done while current stays music; 25 external call minutes → call1 and call2 done; an attempt saved at `2026-11-04T02:30Z` counts for `2026-11-03` (clock tz São Paulo); all 7 done → complete and streak 1; a skipped block keeps `complete` False.
- [ ] **Steps 2–5:** FAIL → implement → PASS → commit `feat: guided day plan with skips, Anki check and streak`.

## Part E — Words, teach, report

### Task 17 (translate): Tap-to-translate and words

**Files:** Create `backend/app/ai/translate.py`, `backend/prompts/translate.md` · Modify `backend/app/routes/words.py`, `backend/app/ai/schemas.py`, `backend/app/ai/prompts.py`, `backend/app/db.py` · Test `backend/tests/test_translate.py`

**Interfaces:**
- Table `translations(key TEXT PK, translation TEXT, note TEXT, created_at)`; `key = normalize(word) + "|" + normalize(sentence)`.
- Schema `Translation(BaseModel): translation: str, note: str` (note empty when nothing special).
- `translate(deps, word: str, sentence: str) -> dict` — cache hit returns `{translation, note, cached: True}`; miss → `generate_structured(providers.chat, render("translate", …, word=, sentence=), …)`, stores, `cached: False`.
- `POST /translate {word (1..60 chars), sentence (≤500)}`; `GET /words`, `POST /words {word, sentence, translation, note, source}`, `DELETE /words/{id}`, `GET /words/export.csv` → `text/csv; charset=utf-8`, header-less rows `front;back` where front = word (+ ` — ` + sentence when present) and back = translation (+ ` (` note `)`), fields quoted with `csv` module, `;` delimiter.

- [ ] **Step 1: Failing tests**: first call hits the fake chat once, second identical call (different case/spacing) hits it zero more times; blank word → 422; export of two words has 2 lines and quotes a field containing `;`.
- [ ] **Steps 2–5:** FAIL → implement → PASS → commit `feat: tap-to-translate with cache and Anki export`.

### Task 18 (teach): "Teach the AI" calls and report download

**Files:** Create `backend/prompts/teach_persona.md`, `backend/app/report_md.py` · Modify `backend/app/routes/sessions.py`, `backend/app/ai/conversation.py`, `backend/app/ai/report.py`, `backend/app/ai/prompts.py` · Test `backend/tests/test_teach.py`, `backend/tests/test_report_md.py`

**Interfaces:**
- `CreateSession.kind` accepts `"teach"` (requires `module_id`, like lesson).
- `persona_prompt` for `teach` renders `teach_persona` with `level`, `module_title`, `target_structures`: the AI is a confused learner of that grammar who asks short questions, makes one typical mistake per turn for the learner to correct, and never explains the rule itself.
- `run_turn` and `finish_session` accept `teach`; the report context for teach is `"Learner explains {module.title} to a confused student. Judge clarity of the explanation and the learner's own English."`; no review scheduling (already true after Task 9).
- `report_markdown(deps, session_id) -> str` — title (kind + module title + date), score, transcript (`**Você:**` / `**IA:**`), mistakes (said → corrected — explanation), natural expressions, strengths; `GET /sessions/{id}/report.md` → `text/markdown; charset=utf-8`, 409 `not_finished` when the session has no report.

- [ ] **Step 1: Failing tests**: teach session renders the teach persona (fake chat receives a system prompt containing the module title and "confused"); teach finish returns a report and creates no `reviews` row; report.md contains the transcript lines and each mistake; unfinished session → 409.
- [ ] **Steps 2–5:** FAIL → implement → PASS → commit `feat: teach-the-AI calls and markdown report download`.

## Part F — App

All app tasks: update `src/types.ts` for the shapes they consume; tests with `jest` + RNTL 14 (`await render(...)`, `within(...)`), `api` mocked via `jest.mock('@/api')` as existing tests do. UI copy in pt-BR.

### Task 19 (app-exercises): Exercise player and lesson flow

**Files:** Create `app/src/components/exercises/{ChoiceExercise,TypedExercise,OrderExercise,ExercisePlayer}.tsx` · Modify `app/src/app/lesson/[id].tsx`, `app/src/components/LessonBar.tsx` · Remove `ListeningStep.tsx`, `__tests__/listening.test.tsx` · Test `app/src/__tests__/exercises.test.tsx`

**Interfaces:**
- Consumes Task 9 endpoints. `Exercise` / `AnswerResult` types: `{id, block, type, prompt, options, words, audio_url, answered, result}`; `{correct, correct_answer, explanation, module_completed, score, next_due}`.
- `ExercisePlayer({ items, submit(id, answer, seconds) => Promise<AnswerResult>, play(url), onDone(result: AnswerResult) })` — starts at the first unanswered item; header "Bloco N de 3 · Exercício k de 9"; a block-transition screen between blocks ("Bloco 2 · Praticar"); measures seconds since the item appeared; `choice`/`listen` with options → `ChoiceExercise`; `gap`/`fix`/`transform`/`translate`/`dictation`/`listen` without options → `TypedExercise` (with ▶ button when `audio_url`); `order` → `OrderExercise` (tap words to build the sentence, tap again to remove). After answering: feedback + "Reportar exercício" link (posts the report) + "Próximo".
- Lesson screen: theory (skippable) → player → result card (score %, "Próxima revisão: <date>", button "Voltar para o dia").

- [ ] **Step 1: Failing tests**: resumes at the first unanswered item; choosing an option calls `submit` with the option text; order builds "she was cooking" from taps; block 1→2 shows the transition screen; last answer with `module_completed` shows the score.
- [ ] **Step 2–4:** FAIL → implement → PASS (`npx jest`, `npx tsc --noEmit`).
- [ ] **Step 5: Commit** `feat(app): 27-exercise lesson player`.

### Task 20 (app-review): Review screen on the bank

**Files:** Modify `app/src/app/review/[id].tsx` · Test `app/src/__tests__/review.test.tsx`

- Starts `POST /reviews/{id}/start`, plays the 9 items with `ExercisePlayer` (single block: hide block header), passes `run_id` in submits, ends on the score and next date.
- [ ] Tests → implement → PASS → commit `feat(app): reviews with bank exercises`.

### Task 21 (app-records): Media rows with +, YouTube, reading, external calls

**Files:** Modify `app/src/components/MediaForm.tsx`, `app/src/app/(tabs)/media.tsx`, `app/src/components/MediaSummary.tsx` · Test `app/src/__tests__/media.test.tsx` (rewrite)

- Sections "Assistir" (series/movie rows: título, min por episódio, stepper `−  N  +` episodes, row total `N × M = T min`; video rows: link field → on blur calls `/media/youtube-title` and fills the title if empty, minutes), "Ler" (título, minutos, páginas, palavras novas multiline), "Ligações de fora" (origem, minutos, nota). Each section has "+ outra série" / "+ outro vídeo" / "+ outra leitura" / "+ lançar ligação". Day totals at the top of each section in minutes, week totals in the summary.
- [ ] Tests: + episode updates the row total and saves `count`; pasting a YouTube link fills the title; adding a second series adds a second row; external call saves to `/calls/external`. → implement → PASS → commit `feat(app): watch, read and call records in minutes`.

### Task 22 (app-calls): Call timer, teach mode, report download

**Files:** Create `app/src/components/CallTimer.tsx`, `app/src/app/teach.tsx`, `app/src/download.ts` · Modify `app/src/app/chat/[sessionId].tsx`, `app/src/app/report/[sessionId].tsx`, `app/src/components/ReportView.tsx`, `app/src/api.ts` · Test `app/src/__tests__/calls.test.tsx`

**Interfaces:**
- `apiText(path): Promise<string>` in `api.ts` (same headers/errors as `api`, returns text).
- `saveText(filename: string, text: string, mime: string): Promise<void>` in `download.ts` — web: Blob + anchor click; native: `Share.share({ message: text, title: filename })`.
- `CallTimer({ sessionId, target = 10 })` — fetches `/sessions/{id}/elapsed` on mount and every 30 s, ticks locally each second, shows `m:ss / 10:00`.
- `teach.tsx`: picks the current module (from `/home`.next_module or a param) and creates a `teach` session, then routes to the chat.
- Report screen: button "Baixar relatório" → `apiText('/sessions/{id}/report.md')` → `saveText('relatorio-<id>.md', …, 'text/markdown')`. `ReportView` drops the listening score row.
- [ ] Tests: timer renders `6:40 / 10:00` from `{seconds: 400}`; download calls `saveText` with the markdown; teach screen posts `kind: 'teach'`. → implement → PASS → commit `feat(app): call timer, teach mode and report download`.

### Task 23 (app-songs): Songs screens

**Files:** Create `app/src/app/songs/{index,new,today}.tsx`, `app/src/components/WordDiff.tsx` · Modify `app/src/app/(tabs)/_layout.tsx` (no new tab; songs open from the day trail and settings) · Test `app/src/__tests__/songs.test.tsx`

- `new.tsx`: título, artista, link, letra (multiline) → `POST /songs`; shows "Marcação de gramática pendente — tentar de novo" when `grammar_status == 'pending'`.
- `index.tsx`: list with progress bars "5/14 trechos", star for current, "Tornar música do momento".
- `today.tsx`: by `stage`: `no_song` → button to add; `dictation` → "Abrir música" (Linking.openURL(link)), chunk lines hidden, text field, submit → `WordDiff`; `shadow` → chunk text visible (with highlights: phrase underlined + module title chip) + `PushToTalk` recording → `WordDiff` + %; `done_today` → celebration and progress; `final` → record the whole song; `finished` → prompt to pick the next song. `review_chunks` shown as a collapsible "Revisão rápida do refrão".
- `WordDiff({ tokens })` — ok = normal, missing = struck-through muted, wrong = red, extra = italic muted.
- [ ] Tests: dictation submit renders the diff; stage `shadow` shows the highlight chip; `no_song` shows the add button. → implement → PASS → commit `feat(app): song library, dictation and shadowing screens`.

### Task 24 (app-translate): TappableText, translation sheet, words

**Files:** Create `app/src/components/TappableText.tsx`, `app/src/components/TranslateSheet.tsx`, `app/src/sentence.ts` · Modify `ChatBubble.tsx`, `MarkdownText.tsx`, exercise feedback (Task 19), song chunk text (Task 23), `app/src/app/(tabs)/settings.tsx` · Test `app/src/__tests__/translate.test.tsx`

**Interfaces:**
- `sentenceAround(text: string, charIndex: number): string` — the sentence (split on `.!?` + newline) containing the index, trimmed.
- `TappableText({ text, style })` — renders words (`[A-Za-z’']+`) as pressables, other characters as plain text; press → `TranslateSheet` with `word` and `sentenceAround`.
- `TranslateSheet({ word, sentence, onClose })` — calls `POST /translate`, shows translation + note, buttons "Salvar palavra" (`POST /words` with source `"tap"`) and "Fechar"; error → message + "Tentar de novo".
- Settings: "Palavras novas (N)" list with delete, "Exportar para o Anki" → `apiText('/words/export.csv')` → `saveText('palavras.csv', …, 'text/csv')`.
- [ ] Tests: `sentenceAround` picks the middle sentence; tapping a word opens the sheet and shows the mocked translation; save posts the word. → implement → PASS → commit `feat(app): tap any word to translate and save it`.

### Task 25 (app-day): Day trail, next-block card, reminders

**Files:** Create `app/src/components/DayTrail.tsx`, `app/src/components/NextBlockCard.tsx`, `app/src/reminders.ts` · Modify `app/src/app/(tabs)/index.tsx`, `app/src/app/(tabs)/settings.tsx`, `app/package.json` (via `npx expo install expo-notifications`) · Remove `PillarBar.tsx` · Test `app/src/__tests__/home.test.tsx` (rewrite), `app/src/__tests__/reminders.test.ts`

**Interfaces:**
- Backend addition in this task: table `app_settings(key PK, value TEXT)`, `GET/PUT /settings/reminders` `{times: ["19:00","21:00"]}` (validated `HH:MM`, max 4) — with a backend test in `tests/test_settings.py`.
- `remindersToSchedule(times: string[], now: Date, plan: DayPlan): {at: Date, body: string}[]` — only times later than `now` today, none when `plan.complete`; body lists the titles of blocks not done, e.g. "Faltam: Ler, Ligação 2, Anki".
- `syncReminders(plan)` — native only: cancel all scheduled, request permission once, schedule each item as a one-shot local notification. Called from the home screen after loading `/home`.
- `DayTrail({ plan, onOpen(block), onSkip(block), onUnskip(block), onAnki(checked) })` — 7 rows: status icon, title, `minutes / target min` bar when target exists, "Pular" on the current block, "Voltar" on skipped ones, checkbox on Anki.
- `NextBlockCard({ plan, previous })` — when a block became done since `previous` (kept in a ref across focus reloads) shows "Boa! Agora: <próximo bloco>"; otherwise "Agora: <bloco atual>"; button routes: grammar → `/lesson/<next_module>` (or the first due review), music → `/songs/today`, call1 → lesson-scenario chat for the current module, call2 → `/teach`, watch/read → media tab, anki → toggles the check.
- [ ] Tests: `remindersToSchedule` drops past times and returns nothing for a complete day; home renders 7 blocks with the current one highlighted; pressing "Pular" posts the skip and reloads; card shows "Boa! Agora: Música" when grammar flips to done.
- [ ] Implement → PASS → commit `feat(app): guided day trail with reminders`.

### Task 26: Docs and full verification

**Files:** Modify `README.md`, `docs/superpowers/specs/2026-11-03-english-app-design.md` (one line pointing to the new spec for lessons/day plan)

- [ ] README: new scripts (`prefill_audio.py`), songs stay local, reminders need the Android app (not web).
- [ ] Run backend suite, app suite and `tsc` → all green.
- [ ] Manual check in the browser: one module end-to-end, a song chunk (dictation + shadow), media rows with +, a skip/unskip, the day completing. Note anything not checkable (Android reminders) in the final summary.
- [ ] Commit `docs: daily plan, exercises and songs`.
