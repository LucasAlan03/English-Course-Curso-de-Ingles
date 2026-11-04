# App de Inglês (B1 → C1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** App Android + web (localhost) de inglês B1→C1 com revisão espaçada, listening gerado por IA, conversa ilimitada, metas diárias e registro de consumo em inglês.

**Architecture:** Backend Python/FastAPI com SQLite concentra currículo, repetição espaçada, custos e toda a IA, atrás de interfaces de provedor trocáveis por perfil (`free`/`paid`). O app Expo/TypeScript só mostra telas, grava e toca áudio, e chama o backend por HTTP/JSON.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, pydantic-settings, PyYAML, sqlite3, pytest, httpx, google-genai (Gemini), faster-whisper, Piper, anthropic, openai; Expo (TypeScript), expo-router, expo-audio, Jest + @testing-library/react-native.

**Spec:** `docs/superpowers/specs/2026-11-03-english-app-design.md`

## Global Constraints

- Prazo da v1: 2026-11-15. Fora da v1: músicas/shadowing, WhatsApp, multiusuário, login, hospedagem do backend.
- Perfil padrão `PROVIDER_PROFILE=free`: Gemini (chat+report), `faster-whisper` local (STT), Piper/Kokoro local (TTS). Perfil `paid`: Claude Haiku (chat), Claude Sonnet (report), OpenAI Whisper (STT), OpenAI TTS. Overrides por `CHAT_PROVIDER`, `REPORT_PROVIDER`, `STT_PROVIDER`, `TTS_PROVIDER`. IDs de modelo e preços ficam só em config (conferir nas páginas oficiais ao implementar).
- Autenticação: header `X-API-Token` igual a `API_TOKEN`; `/health` é a única rota sem token.
- Custo: `MONTHLY_WARN_BRL=45`, `MONTHLY_CAP_BRL=50`; valem só para provedores pagos. Erro de provedor sem crédito → código `provider_out_of_credit`.
- 26 módulos (B1=10, B2=9, C1=7) em `backend/content/modules/*.yaml`; prompts em `backend/prompts/*.md`.
- Listening: 5 itens, sendo 3 `choice` e 2 `gap`. Conversa: sem limite de trocas; últimas 10 mensagens completas, as anteriores em resumo. Saída estruturada da IA: JSON validado com Pydantic, 1 nova tentativa, depois erro.
- Nota final = `round(0.4 × listening_pct + 0.6 × conversation_score)`. Revisão espaçada: `ease` inicial 2,5 (mín. 1,3, máx. 3,0); intervalo inicial 1 dia, depois 3 dias; nota ≥85 → intervalo × `ease` e `ease` +0,1; 60–84 → intervalo × 1,2; <60 → intervalo 1, `ease` −0,2, `repetitions` 0.
- Módulo com ≥3 erros em 7 dias tem a revisão antecipada para amanhã.
- Pilares: `grammar`, `speak`, `write`, `read`, `watch`; status e sequência são calculados, nunca guardados.
- Chaves só em `.env` (fora do Git); `backend/data/` (banco e áudios) fora do Git. Fuso: `TZ=America/Sao_Paulo`.
- Testes do backend usam sempre provedores falsos; nenhum teste automático gasta dinheiro.
- Windows: sem `make`; o teste de fumaça é `python scripts/smoke.py`.

## Review Focus

Entradas e condições que o spec não detalha e que mais provavelmente quebram o uso. Cada linha tem um teste na tarefa dona:

1. Áudio mudo ou transcrição vazia não chega à IA e devolve erro claro (`empty_transcript`) — Task 12.
2. Encerrar uma sessão sem nenhuma fala do usuário não gera nota nem altera revisões — Task 12.
3. Encerrar a mesma sessão duas vezes não aplica a revisão espaçada duas vezes — Task 12.
4. Registro de consumo com minutos ≤ 0, data inválida ou editado/excluído mantém os totais corretos — Task 14.
5. Sessão encerrada às 23:30 (fuso de São Paulo) conta para o dia local, não para o dia UTC seguinte — Task 4.
6. IA devolvendo JSON inválido duas vezes vira erro `invalid_ai_output`, sem salvar dados parciais — Task 8.

---

## Estrutura de arquivos

```
backend/
  pyproject.toml  .env.example
  app/ main.py config.py clock.py db.py deps.py errors.py srs.py scoring.py goals.py content.py usage.py pricing.py
       providers/ base.py fakes.py factory.py gemini.py local_stt.py local_tts.py anthropic_provider.py openai_provider.py
       ai/ prompts.py schemas.py structured.py listening.py conversation.py report.py writing.py
       routes/ modules.py sessions.py listening.py home.py media.py writing.py usage.py
  content/curriculum.yaml  content/modules/*.yaml
  prompts/ chat_persona.md listening.md report.md summary.md writing_prompt.md writing_feedback.md
  scripts/ generate_modules.py smoke.py
  tests/ conftest.py test_*.py
app/   (Expo)  app/ (rotas) src/api.ts src/audio.ts src/components src/__tests__
README.md  .gitignore
```

---

### Task 1: Backend scaffold, config, auth, clock

**Files:**
- Create: `backend/pyproject.toml`, `backend/.env.example`, `.gitignore`, `backend/app/{__init__,main,config,clock,deps}.py`, `backend/tests/{conftest,test_health.py}`

**Interfaces:**
- Produces: `Settings` (campos: `api_token`, `provider_profile`, `tz`, `monthly_warn_brl`, `monthly_cap_brl`, `data_dir`, `content_dir`, `prompts_dir`, chaves `gemini_api_key`/`anthropic_api_key`/`openai_api_key`, overrides de provedor); `Clock.now() -> datetime` (UTC) e `Clock.today() -> date` (no `tz`); `FixedClock(now: datetime, tz: str)`; `create_app(settings: Settings, *, providers=None, clock: Clock | None = None) -> FastAPI`; dependência `require_token`; fixture pytest `app_client` (TestClient com fakes, banco em `tmp_path`, header de token já definido).

- [ ] **Step 1: Write failing tests** em `test_health.py`: `test_health_open` (GET `/health` → 200 `{"status":"ok"}` sem token), `test_protected_requires_token` (GET `/home` sem header → 401; com `X-API-Token` errado → 401), `test_fixed_clock_today_uses_tz` (`FixedClock(datetime(2026,11,4,2,30,tzinfo=UTC), "America/Sao_Paulo").today() == date(2026,11,3)`).
- [ ] **Step 2: Run** `cd backend; python -m pytest tests/test_health.py -v` → FAIL (módulos inexistentes).
- [ ] **Step 3: Implement** o pacote, `pyproject.toml` com extras `dev` (pytest, httpx) e um extra por conjunto de provedores (`free`, `paid`). `.gitignore` cobre `.env`, `backend/data/`, `.venv`, `node_modules`, `__pycache__`. `.env.example` lista todas as variáveis da config. Rodar `git init` na raiz do projeto.
- [ ] **Step 4: Run** `python -m pip install -e ".[dev]"` e o teste → PASS.
- [ ] **Step 5: Commit** `git add -A && git commit -m "chore: backend scaffold, config, auth, clock"`.

### Task 2: Banco de dados

**Files:**
- Create: `backend/app/db.py`, `backend/tests/test_db.py`

**Interfaces:**
- Consumes: `Settings.data_dir`.
- Produces: `connect(path: str) -> sqlite3.Connection` (row_factory `sqlite3.Row`, foreign keys ligadas); `init_schema(conn) -> None` (idempotente); `insert(conn, table: str, **cols) -> int` (retorna o id).
- Tabelas conforme a seção 7 do spec, com estas adições necessárias: `sessions.finished_at TEXT`, `sessions.day TEXT` (data local do encerramento), `sessions.summary TEXT` (resumo da conversa), `sessions.is_finished INTEGER DEFAULT 0`, `mistakes.module_id` pode ser nulo.

- [ ] **Step 1: Write failing tests**: `test_init_schema_creates_all_tables` (as 7 tabelas do spec existem), `test_init_schema_idempotent` (chamar duas vezes não falha), `test_insert_returns_id`.
- [ ] **Step 2: Run** `python -m pytest tests/test_db.py -v` → FAIL.
- [ ] **Step 3: Implement** `db.py` com o DDL em uma constante; `connect` cria o diretório pai.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: sqlite schema and helpers`.

### Task 3: Repetição espaçada e nota final

**Files:**
- Create: `backend/app/srs.py`, `backend/app/scoring.py`, `backend/tests/{test_srs,test_scoring}.py`

**Interfaces:**
- Produces: `ReviewState(interval_days: int, ease: float, repetitions: int, next_due: date)` (dataclass congelada); `next_state(prev: ReviewState | None, score: int, today: date) -> ReviewState`; `final_score(listening_pct: float | None, conversation: int) -> int` (sem listening, devolve `conversation`).
- Regras: `prev is None` (aula) → intervalo 1, `repetitions` 0, `ease` 2,5. Com `prev.repetitions == 0` e nota ≥60 → intervalo 3, `repetitions` 1. Caso contrário aplica a tabela das Global Constraints; arredondamento `floor(x + 0.5)`; `repetitions` +1 quando nota ≥60.

- [ ] **Step 1: Write failing tests** (tabela): aula nota 90 → `(1, 2.5, 0, today+1)`; revisão nota 90 com `prev=(1,2.5,0)` → intervalo 3, reps 1; nota 90 com `prev=(3,2.5,1)` → intervalo 8, `ease` 2.6, reps 2; nota 70 com `prev=(8,2.6,2)` → intervalo 10, `ease` 2.6; nota 50 com `prev=(8,2.6,2)` → intervalo 1, `ease` 2.4, reps 0; `ease` nunca <1.3 nem >3.0; `final_score(80, 90) == 86`; `final_score(None, 73) == 73`.
- [ ] **Step 2: Run** `python -m pytest tests/test_srs.py tests/test_scoring.py -v` → FAIL.
- [ ] **Step 3: Implement** as duas funções puras.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: spaced repetition and scoring`.

### Task 4: Metas do dia e sequência

**Files:**
- Create: `backend/app/goals.py`, `backend/tests/test_goals.py`

**Interfaces:**
- Consumes: `insert`, `FixedClock`.
- Produces: `pillars_for_day(conn, day: date) -> dict[str, bool]` (chaves `grammar`, `speak`, `write`, `read`, `watch`); `streak(conn, today: date) -> int`.
- Regras: `grammar` = sessão `lesson`/`review` com `is_finished=1` em `sessions.day == day`; `speak` = sessão `lesson`/`review`/`free` encerrada no dia com ao menos 1 mensagem do usuário; `write` = sessão `writing` encerrada; `read`/`watch` = existe `media_logs` com `type` e `date == day`. `streak` conta dias completos (5 pilares) consecutivos terminando hoje, ou ontem se hoje ainda está incompleto.

- [ ] **Step 1: Write failing tests**: `test_pillars_auto_from_sessions`, `test_pillars_manual_from_media`, `test_streak_counts_consecutive_complete_days`, `test_streak_keeps_yesterday_when_today_incomplete`, `test_session_finished_2330_local_counts_for_local_day` (cria sessão com `finished_at` em UTC `2026-11-04T02:30Z` e `day` calculado pelo `FixedClock` → `pillars_for_day(date(2026,11,3))["grammar"] is True`).
- [ ] **Step 2: Run** `python -m pytest tests/test_goals.py -v` → FAIL.
- [ ] **Step 3: Implement** `goals.py` com SQL direto; o `day` é gravado por quem encerra a sessão (Task 12) usando `Clock.today()`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: daily pillars and streak`.

### Task 5: Carregador de currículo

**Files:**
- Create: `backend/app/content.py`, `backend/content/curriculum.yaml`, `backend/tests/test_content.py`

**Interfaces:**
- Produces: `Module` (Pydantic: `id`, `level: Literal["B1","B2","C1"]`, `title`, `order: int`, `theory_md`, `scenario: Scenario(title, character, goal)`, `target_structures: list[str]`, `source: str`); `ContentRepo.load(directory: str) -> ContentRepo` com `.all() -> list[Module]` (ordenados por nível e `order`), `.get(module_id: str) -> Module` (levanta `KeyError`), `.ids() -> list[str]`.
- `curriculum.yaml`: os 26 módulos do spec (seção 3) com `id`, `level`, `title`, `order` e `source`, usado depois pelo gerador (Task 22).

- [ ] **Step 1: Write failing tests** com YAMLs de exemplo em `tmp_path`: `test_load_orders_by_level_then_order`, `test_get_unknown_raises_keyerror`, `test_duplicate_ids_rejected`, `test_curriculum_outline_has_26_modules_10_9_7` (lê `curriculum.yaml` real).
- [ ] **Step 2: Run** `python -m pytest tests/test_content.py -v` → FAIL.
- [ ] **Step 3: Implement** `content.py` e escrever `curriculum.yaml`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: curriculum loader and outline`.

### Task 6: Contratos de provedor, fakes e fábrica por perfil

**Files:**
- Create: `backend/app/providers/{base,fakes,factory}.py`, `backend/tests/{test_providers_factory,test_provider_contract}.py`

**Interfaces:**
- Produces (`base.py`): `Msg(role: Literal["user","assistant"], content: str)`; `Usage(provider: str, model: str, kind: str, input_units: int, output_units: int)`; `TextResult(text: str, usage: Usage)`; `SttResult(text: str, usage: Usage)`; `TtsResult(audio: bytes, mime: str, usage: Usage)`; protocolos `TextModel.generate(system: str, messages: list[Msg], json_mode: bool = False) -> TextResult`, `SpeechToText.transcribe(audio: bytes, mime: str) -> SttResult`, `TextToSpeech.synthesize(text: str) -> TtsResult`; cada implementação tem `is_paid: bool`; `Providers(chat: TextModel, report: TextModel, stt: SpeechToText, tts: TextToSpeech)`.
- Produces (`fakes.py`): `FakeTextModel(responses: list[str])` (fila; guarda `calls`), `FakeStt(text: str)`, `FakeTts()` (devolve `b"FAKEAUDIO"`); todos `is_paid=False`.
- Produces (`factory.py`): `build_providers(settings: Settings) -> Providers` (perfil + overrides); nomes válidos: `gemini`, `local` (STT/TTS), `anthropic`, `openai`; nome inválido → `ValueError`.

- [ ] **Step 1: Write failing tests**: `test_free_profile_selects_free_providers`, `test_paid_profile_selects_paid_providers`, `test_override_beats_profile` (perfil `free` + `TTS_PROVIDER=openai` → TTS pago, resto gratuito), `test_unknown_provider_raises`; teste de contrato parametrizado (`@pytest.mark.parametrize` sobre fakes; implementações reais entram nas Tasks 9–10) que verifica tipos de retorno e `usage` preenchido.
- [ ] **Step 2: Run** `python -m pytest tests/test_providers_factory.py tests/test_provider_contract.py -v` → FAIL.
- [ ] **Step 3: Implement** os módulos; a fábrica importa cada implementação real só quando escolhida (para o perfil `free` não exigir SDKs pagos).
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: provider contracts, fakes and profile factory`.

### Task 7: Erros, custo e teto mensal

**Files:**
- Create: `backend/app/{errors,usage,pricing}.py`, `backend/app/routes/usage.py`, `backend/tests/test_usage.py`
- Modify: `backend/app/main.py` (handlers de erro e rota)

**Interfaces:**
- Produces (`errors.py`): `AppError(code: str, status: int, detail: str = "")` e subclasses `ProviderOutOfCredit(provider)` (402, `provider_out_of_credit`), `ProviderRateLimited(provider)` (429, `provider_rate_limited`), `MonthlyCapReached()` (402, `monthly_cap_reached`), `InvalidAIOutput()` (502, `invalid_ai_output`), `EmptyTranscript()` (422, `empty_transcript`); resposta JSON `{"error": code, "detail": str}`.
- Produces (`pricing.py`): `cost_brl(usage: Usage) -> float` lendo tabela por `(provider, model, kind)`; provedor gratuito → 0. Preços e IDs de modelo conferidos nas páginas oficiais e anotados em comentário com a data.
- Produces (`usage.py`): `UsageTracker(conn, settings, clock)` com `record(usage: Usage) -> float`, `month_total_brl() -> float`, `status() -> dict` (`{"total","warn","cap","level": "ok"|"warn"|"blocked"}`), `ensure_can_spend(is_paid: bool) -> None` (levanta `MonthlyCapReached` se pago e total ≥ teto).
- Rota: `GET /usage/month` → `status()`.

- [ ] **Step 1: Write failing tests**: `test_free_usage_costs_zero`, `test_month_total_sums_only_current_month`, `test_status_levels_ok_warn_blocked` (44, 45, 50), `test_cap_blocks_paid_but_not_free`, `test_error_json_shape` (via rota de teste que levanta `ProviderOutOfCredit("openai")`).
- [ ] **Step 2: Run** `python -m pytest tests/test_usage.py -v` → FAIL.
- [ ] **Step 3: Implement** os módulos e registrar `app.add_exception_handler(AppError, ...)`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: errors, cost tracking and monthly cap`.

### Task 8: Saída estruturada e prompts

**Files:**
- Create: `backend/app/ai/{prompts,schemas,structured}.py`, `backend/prompts/*.md` (esqueletos com as variáveis), `backend/tests/test_structured.py`

**Interfaces:**
- Produces (`schemas.py`): `ListeningItem(kind: Literal["choice","gap"], audio_text: str, prompt: str, options: list[str] | None, answer: str, explanation: str)`; `ListeningSet(items: list[ListeningItem])` (validador: 5 itens, 3 `choice` com 3–4 opções incluindo a resposta, 2 `gap`); `MistakeOut(said, corrected, explanation, module_id: str | None)`; `Report(mistakes: list[MistakeOut], natural_expressions: list[str], strengths: list[str], score: int)` (`score` 0–100); `WritingFeedback(corrected_text, improved_text, mistakes: list[MistakeOut], score: int)`.
- Produces (`prompts.py`): `render(name: str, prompts_dir: str, **vars) -> str` (substitui `{{var}}`; variável faltando → `KeyError`).
- Produces (`structured.py`): `generate_structured(model: TextModel, system: str, messages: list[Msg], schema: type[T], tracker: UsageTracker) -> T` — registra o uso a cada chamada, repete **uma vez** se `ValidationError`/JSON inválido, depois levanta `InvalidAIOutput`; aceita JSON dentro de cerca ```json.

- [ ] **Step 1: Write failing tests**: `test_valid_json_parsed`, `test_fenced_json_accepted`, `test_retries_once_then_succeeds` (fake com 1 resposta inválida + 1 válida; 2 chamadas), `test_invalid_twice_raises_invalid_ai_output`, `test_listening_set_requires_3_choice_2_gap`, `test_render_missing_var_raises`.
- [ ] **Step 2: Run** `python -m pytest tests/test_structured.py -v` → FAIL.
- [ ] **Step 3: Implement** os três módulos; escrever os esqueletos dos prompts (persona sem correção durante a conversa, nível B1/B2/C1 e estruturas-alvo, regras de saída JSON).
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: structured AI output with retry`.

### Task 9: Provedores gratuitos

**Files:**
- Create: `backend/app/providers/{gemini,local_stt,local_tts}.py`, `backend/tests/test_free_providers.py`

**Interfaces:**
- Consumes: protocolos da Task 6, `errors.ProviderRateLimited`.
- Produces: `GeminiText(api_key: str, model: str)` implementa `TextModel` (`json_mode=True` pede JSON; erro de quota → `ProviderRateLimited("gemini")` após 1 nova tentativa com espera); `LocalWhisperStt(model_size: str = "base")` implementa `SpeechToText` com `faster-whisper` (inglês); `LocalTts(voice: str)` implementa `TextToSpeech` com Piper (WAV). Todos `is_paid=False`; imports pesados dentro do construtor.

- [ ] **Step 1: Write failing tests** com clientes injetados/mocados (sem rede nem modelos): `test_gemini_maps_quota_error_to_rate_limited`, `test_gemini_returns_text_and_usage`, `test_local_stt_returns_text_for_wav` (cliente falso injetado), `test_local_tts_returns_wav_bytes`; entram no teste de contrato da Task 6.
- [ ] **Step 2: Run** `python -m pytest tests/test_free_providers.py -v` → FAIL.
- [ ] **Step 3: Implement**; conferir na documentação atual os nomes de SDK e modelo; baixar o modelo de voz do Piper para `backend/data/voices/` (instruções no README, Task 23).
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: free providers (Gemini, local Whisper, local TTS)`.

### Task 10: Provedores pagos

**Files:**
- Create: `backend/app/providers/{anthropic_provider,openai_provider}.py`, `backend/tests/test_paid_providers.py`

**Interfaces:**
- Produces: `AnthropicText(api_key, model)` implementa `TextModel`; `OpenAIStt(api_key, model)` implementa `SpeechToText`; `OpenAITts(api_key, model, voice)` implementa `TextToSpeech`. Todos `is_paid=True`; erro de saldo/billing → `ProviderOutOfCredit(<provider>)`; limite de requisições → `ProviderRateLimited`. `Usage` com tokens (texto), segundos (STT) e caracteres (TTS) para o `pricing`.

- [ ] **Step 1: Write failing tests** com clientes mocados: `test_anthropic_maps_billing_error_to_out_of_credit`, `test_openai_stt_returns_text_and_seconds`, `test_openai_tts_returns_audio_and_chars`; incluídos no teste de contrato.
- [ ] **Step 2: Run** `python -m pytest tests/test_paid_providers.py -v` → FAIL.
- [ ] **Step 3: Implement**; confirmar IDs de modelo e preços atuais e preencher `pricing.py`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: paid providers (Claude, OpenAI)`.

### Task 11: Listening

**Files:**
- Create: `backend/app/ai/listening.py`, `backend/app/routes/listening.py`, `backend/tests/test_listening.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `generate_structured`, `ListeningSet`, `Providers.report`/`.tts`, `UsageTracker`, `insert`, `ContentRepo`.
- Produces: `generate_listening(deps, session_id: int, count: int = 5) -> list[dict]` (gera via `report`, sintetiza `audio_text` via TTS, grava em `data/audio/` e em `listening_items`; `count=3` nas revisões; usa os últimos erros do módulo no prompt); `GET /sessions/{id}/listening` → itens sem `answer`; `POST /listening/{item_id}/answer` body `{"answer": str}` → `{"correct": bool, "correct_answer": str, "explanation": str}` (comparação de `gap` ignora caixa e pontuação); `GET /audio/{name}` serve o arquivo (token exigido).

- [ ] **Step 1: Write failing tests**: `test_generate_listening_creates_5_items_with_audio`, `test_review_session_generates_3_items`, `test_listing_hides_answers`, `test_answer_choice_correct_and_wrong`, `test_gap_answer_ignores_case_and_punctuation`, `test_recent_mistakes_included_in_prompt` (inspeciona `FakeTextModel.calls`).
- [ ] **Step 2: Run** `python -m pytest tests/test_listening.py -v` → FAIL.
- [ ] **Step 3: Implement**.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: generated listening exercises`.

### Task 12: Sessões, conversa e encerramento

**Files:**
- Create: `backend/app/ai/{conversation,report}.py`, `backend/app/routes/sessions.py`, `backend/tests/test_sessions.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `next_state`, `final_score`, `generate_structured`, `Report`, `UsageTracker.ensure_can_spend`, `ContentRepo`, `Clock`.
- Produces: `POST /sessions` body `{"kind": "lesson"|"review"|"free"|"writing", "module_id"?: str, "topic"?: str}` → `{"id": int}`; `POST /sessions/{id}/turn` (multipart: `text` **ou** `audio` + `want_audio: bool`) → `{"user_text": str, "reply_text": str, "reply_audio_url": str | None}`; `POST /sessions/{id}/finish` → `{"report": Report, "listening_score": int | None, "conversation_score": int, "final_score": int, "next_due": str | None}`; `build_context(messages: list[Msg], summary: str | None, chat: TextModel, tracker) -> tuple[str | None, list[Msg]]` (mantém as 10 últimas completas e resume as anteriores).
- `finish` é idempotente (segunda chamada devolve o resultado salvo). Em `lesson`/`review` atualiza `reviews` via `next_state`; em qualquer sessão grava `mistakes` (com `module_id` do módulo da sessão, ou o sugerido pela IA se for um id conhecido) e antecipa para amanhã a revisão de módulos com ≥3 erros nos últimos 7 dias. Grava `finished_at`, `day` (`Clock.today()`), `is_finished`.

- [ ] **Step 1: Write failing tests**: `test_turn_with_text_returns_reply_and_stores_messages`, `test_turn_with_audio_transcribes_first`, `test_empty_transcript_returns_422_and_no_ai_call` (FakeStt devolve `"  "`; `FakeTextModel.calls` vazio), `test_turn_without_audio_flag_has_no_audio_url`, `test_context_keeps_last_10_and_summarizes_older` (25 mensagens → resumo gravado e 10 recentes), `test_finish_creates_review_and_returns_scores`, `test_finish_without_user_messages_returns_error_and_no_review`, `test_finish_twice_is_idempotent` (uma linha em `reviews`, mesmas notas, `repetitions` não dobra), `test_free_session_pulls_review_forward_after_3_mistakes`, `test_paid_provider_blocked_when_cap_reached`.
- [ ] **Step 2: Run** `python -m pytest tests/test_sessions.py -v` → FAIL.
- [ ] **Step 3: Implement**; o prompt de persona usa `scenario`, `target_structures` e nível do módulo; em `free`, tema vem de `topic`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: conversation sessions, report and review scheduling`.

### Task 13: Home e módulos

**Files:**
- Create: `backend/app/routes/{home,modules}.py`, `backend/tests/test_home_modules.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `GET /modules` → níveis com módulos, `completed: bool` e progresso por nível; `GET /modules/{id}` → módulo completo (404 se desconhecido); `GET /home` → `{"reviews_due": [{module_id, title, next_due, overdue_days}], "next_module": {...} | null, "pillars": dict, "streak": int, "usage": status}`. Revisões ordenadas com atrasadas primeiro. `next_module` = primeiro módulo B1 não concluído (depois B2, C1). Módulo "concluído" = existe sessão `lesson` encerrada.

- [ ] **Step 1: Write failing tests**: `test_modules_lists_all_with_progress`, `test_unknown_module_404`, `test_home_reviews_due_only_today_or_earlier_sorted_overdue_first`, `test_home_next_module_skips_completed`, `test_home_includes_pillars_streak_usage`.
- [ ] **Step 2: Run** `python -m pytest tests/test_home_modules.py -v` → FAIL.
- [ ] **Step 3: Implement**.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: home and modules endpoints`.

### Task 14: Registro de consumo

**Files:**
- Create: `backend/app/routes/media.py`, `backend/tests/test_media.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `POST /media` body `{date, type: "watch"|"read", category, title, episode?, minutes: int, pages?: int}` → registro com `id`; `GET /media?date=YYYY-MM-DD`; `PUT /media/{id}`; `DELETE /media/{id}`; `GET /media/summary?date=YYYY-MM-DD` → `{"day": {...}, "week": {...}, "month": {...}}`, cada um com `total_minutes` e `by_category`. Categorias válidas: `series|movie|video|podcast` (watch) e `hq|book|article|other` (read). Semana começa na segunda-feira. `minutes` entre 1 e 1440.

- [ ] **Step 1: Write failing tests**: `test_create_and_list_by_date`, `test_invalid_minutes_rejected` (0, -5, 2000 → 422), `test_invalid_date_rejected`, `test_category_must_match_type`, `test_summary_totals_by_day_week_month`, `test_update_and_delete_change_totals`, `test_multiple_items_same_day`.
- [ ] **Step 2: Run** `python -m pytest tests/test_media.py -v` → FAIL.
- [ ] **Step 3: Implement** com modelos Pydantic de entrada.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: media consumption log`.

### Task 15: Escrita corrigida

**Files:**
- Create: `backend/app/ai/writing.py`, `backend/app/routes/writing.py`, `backend/tests/test_writing.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `POST /writing/prompt` → `{"session_id": int, "prompt": str}` (cria sessão `writing`; tema curto no nível do usuário); `POST /writing/submit` body `{"session_id": int, "text": str}` → `WritingFeedback`; texto vazio ou <10 caracteres → 422; grava `mistakes`, encerra a sessão (`finished_at`, `day`, `is_finished`) e aplica a antecipação de revisão da Task 12 (reutilizar a função, não duplicar).

- [ ] **Step 1: Write failing tests**: `test_prompt_creates_writing_session`, `test_submit_returns_feedback_and_saves_mistakes`, `test_submit_empty_text_422`, `test_submit_marks_write_pillar`.
- [ ] **Step 2: Run** `python -m pytest tests/test_writing.py -v` → FAIL.
- [ ] **Step 3: Implement**.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: corrected writing`.

### Task 16: App Expo e teste de voz (risco inicial)

**Files:**
- Create: `app/` (Expo + TypeScript + expo-router), `app/src/{api.ts,audio.ts,config.ts}`, `app/app/_layout.tsx`, `app/app/voice-test.tsx`, `app/src/__tests__/api.test.ts`
- Create: `backend/app/routes/stt.py` (`POST /stt`, multipart `audio` → `{"text": str}`; `EmptyTranscript` se vazio) e `backend/tests/test_stt.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces (`api.ts`): `api<T>(path: string, init?: RequestInit): Promise<T>` com `BASE_URL` e `X-API-Token` vindos de `config.ts` (`EXPO_PUBLIC_API_URL`, `EXPO_PUBLIC_API_TOKEN`); lança `ApiError(code: string, detail: string)` quando a resposta traz `{"error"}`. `audio.ts`: `startRecording(): Promise<void>`, `stopRecording(): Promise<{uri: string; mime: string}>`, `playUrl(url: string): Promise<void>`.

- [ ] **Step 1: Write failing tests**: backend `test_stt_returns_text` e `test_stt_empty_returns_422`; app `api.test.ts` com `fetch` mocado (`sends token header`, `throws ApiError with code`).
- [ ] **Step 2: Run** `python -m pytest tests/test_stt.py -v` e `cd app; npx jest` → FAIL.
- [ ] **Step 3: Implement** a rota, o cliente e a tela `voice-test` (segurar para gravar → enviar a `/stt` → mostrar o texto). Usar `expo-audio`; se a versão do SDK instalada não o oferecer, usar `expo-av`. Tratar permissão de microfone negada (mostrar mensagem e esconder o botão de voz).
- [ ] **Step 4: Run** testes → PASS; **verificação manual**: abrir na web (`npx expo start --web`) e no Android (Expo Go, mesma rede Wi-Fi, `EXPO_PUBLIC_API_URL=http://<IP-do-PC>:8000`) e confirmar gravação → texto nos dois. Se falhar, resolver aqui antes de seguir.
- [ ] **Step 5: Commit** `feat: expo app scaffold and voice round-trip`.

### Task 17: Telas Home e trilhas

**Files:**
- Create: `app/app/(tabs)/{_layout,index,tracks}.tsx`, `app/src/components/{PillarBar,ReviewList,ModuleCard}.tsx`, `app/src/__tests__/home.test.tsx`

**Interfaces:**
- Consumes: `GET /home`, `GET /modules`.
- Produces: tab Home ("Revisões de hoje", "Continuar trilha", `PillarBar` com 5 pilares e sequência, aviso de custo) e tab Trilhas (B1/B2/C1 com progresso e módulos livres; o próximo sugerido destacado). Navegação para `/lesson/[id]`, `/review/[id]`.

- [ ] **Step 1: Write failing tests** (API mocada): `PillarBar renders 5 pillars with done state`, `Home shows overdue reviews first`, `Tracks marks suggested next module`.
- [ ] **Step 2: Run** `npx jest` → FAIL.
- [ ] **Step 3: Implement** as telas e componentes.
- [ ] **Step 4: Run** → PASS; conferir visualmente na web e no Android.
- [ ] **Step 5: Commit** `feat: home and tracks screens`.

### Task 18: Fluxo da aula (teoria e listening)

**Files:**
- Create: `app/app/lesson/[id].tsx`, `app/src/components/{Theory,ListeningStep}.tsx`, `app/src/__tests__/listening.test.tsx`

**Interfaces:**
- Consumes: `GET /modules/{id}`, `POST /sessions`, `GET /sessions/{id}/listening`, `POST /listening/{item_id}/answer`, `playUrl`.
- Produces: tela com etapas Teoria (botão "Pular") → Listening (5 itens: tocar áudio, responder, ver correção e explicação, avançar) → navega para `/chat/[sessionId]`.

- [ ] **Step 1: Write failing tests**: `Theory skip button goes to listening`, `ListeningStep shows correction after answering`, `gap item accepts typed answer`.
- [ ] **Step 2: Run** `npx jest` → FAIL.
- [ ] **Step 3: Implement**.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: lesson flow with listening`.

### Task 19: Conversa, relatório, revisão e conversa livre

**Files:**
- Create: `app/app/chat/[sessionId].tsx`, `app/app/report/[sessionId].tsx`, `app/app/review/[id].tsx`, `app/app/free.tsx`, `app/src/components/{ChatBubble,PushToTalk,ReportView}.tsx`, `app/src/__tests__/chat.test.tsx`

**Interfaces:**
- Consumes: `POST /sessions/{id}/turn`, `POST /sessions/{id}/finish`, `audio.ts`.
- Produces: chat com entrada por voz (segurar/soltar) ou texto, chave "ouvir/ler" (`want_audio`), botão "Encerrar e ver relatório"; relatório com nota, erros (corrigido + explicação), expressões e pontos fortes, e a data da próxima revisão; revisão (3 itens de listening + mini conversa, mesmo chat); conversa livre (escolher assunto ou aceitar sugestão).

- [ ] **Step 1: Write failing tests**: `chat sends text and shows reply`, `empty_transcript error shows retry message`, `finish navigates to report`, `ReportView lists mistakes with corrections`.
- [ ] **Step 2: Run** `npx jest` → FAIL.
- [ ] **Step 3: Implement**; sem limite de trocas; se `ApiError.code` for `provider_out_of_credit`/`provider_rate_limited`/`monthly_cap_reached`, mostrar a mensagem da Task 21.
- [ ] **Step 4: Run** → PASS; **verificação manual** de um módulo completo (teoria → listening → conversa → relatório) na web e no Android.
- [ ] **Step 5: Commit** `feat: chat, report, review and free conversation screens`.

### Task 20: Telas de escrita e consumo

**Files:**
- Create: `app/app/writing.tsx`, `app/app/media.tsx`, `app/src/components/{MediaForm,MediaSummary}.tsx`, `app/src/__tests__/media.test.tsx`

**Interfaces:**
- Consumes: `POST /writing/prompt`, `POST /writing/submit`, `/media*`.
- Produces: escrita (tema → texto → correção); consumo com seletor Assistir/Ler, categoria, título, episódio, minutos, lista do dia editável/excluível e totais dia/semana/mês por categoria.

- [ ] **Step 1: Write failing tests**: `MediaForm blocks minutes <= 0`, `MediaForm submits watch entry with episode`, `MediaSummary shows totals by category`.
- [ ] **Step 2: Run** `npx jest` → FAIL.
- [ ] **Step 3: Implement**.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: writing and media screens`.

### Task 21: Custo e erros na interface

**Files:**
- Create: `app/src/components/{UsageBanner,ErrorNotice}.tsx`, `app/app/settings.tsx`, `app/src/__tests__/errors.test.tsx`

**Interfaces:**
- Consumes: `GET /usage/month`, `ApiError`.
- Produces: `UsageBanner` (nível `warn`/`blocked` com total do mês); `ErrorNotice({error: ApiError})` com textos por código: `provider_out_of_credit` ("Os créditos de <provedor> acabaram. Recarregue no console."), `provider_rate_limited` (aguarde ou ative o perfil pago), `monthly_cap_reached`, `invalid_ai_output` (tentar de novo), `empty_transcript` (repita); tela de configurações mostra o perfil ativo e o gasto do mês.

- [ ] **Step 1: Write failing tests**: um por código de erro (texto exibido) e `UsageBanner hidden when ok`.
- [ ] **Step 2: Run** `npx jest` → FAIL.
- [ ] **Step 3: Implement** e usar `ErrorNotice` nas telas das Tasks 18–20.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: cost banner and error messages`.

### Task 22: Conteúdo dos 26 módulos

**Files:**
- Create: `backend/scripts/generate_modules.py`, `backend/content/modules/*.yaml` (26)
- Test: `backend/tests/test_content.py` (já existe)

**Interfaces:**
- Consumes: `curriculum.yaml`, `Providers.report`, `Module`.
- Produces: `python scripts/generate_modules.py [--only <id>] [--force]` gera o YAML de cada módulo (teoria curta com exemplos, cenário real, estruturas-alvo), valida com `Module` e não sobrescreve arquivos existentes sem `--force`.

- [ ] **Step 1: Write failing test**: `test_real_content_has_26_valid_modules` (10 B1, 9 B2, 7 C1, ids iguais aos de `curriculum.yaml`, `theory_md` e `scenario` não vazios).
- [ ] **Step 2: Run** `python -m pytest tests/test_content.py::test_real_content_has_26_valid_modules -v` → FAIL.
- [ ] **Step 3: Implement** o script e rodá-lo para gerar os 26 arquivos (perfil ativo).
- [ ] **Step 4: Run** o teste → PASS. **Revisão humana**: Lucas lê os módulos B1 primeiro (os que ele vai usar já) e corrige o que estiver errado; B2 e C1 podem ser revisados depois, antes de serem estudados.
- [ ] **Step 5: Commit** `feat: curriculum content for 26 modules`.

### Task 23: README, teste de fumaça e verificação final

**Files:**
- Create: `README.md`, `backend/scripts/smoke.py`

**Interfaces:**
- Produces: `python scripts/smoke.py` faz uma chamada real a cada provedor do perfil ativo (texto curto, transcrição de um WAV de exemplo gerado pelo próprio TTS, síntese) e imprime OK/FALHA por provedor. README: o que é, arquitetura (diagrama), perfis `free`/`paid` e como trocar, como comprar créditos e definir limite nos consoles, como baixar a voz do Piper, como rodar backend e app (web e Android pela rede local), como rodar os testes e GIF/vídeo de demonstração.

- [ ] **Step 1: Run** `cd backend; python -m pytest -v` → todos PASS.
- [ ] **Step 2: Run** `cd app; npx jest` → todos PASS.
- [ ] **Step 3: Write** README e `smoke.py`; `python scripts/smoke.py` → OK em todos os provedores do perfil `free`.
- [ ] **Step 4: Verificação manual completa** no Android e na web: concluir um módulo B1; ver a revisão agendada para amanhã; registrar um item de assistir e um de ler; conferir pilares, sequência e `/usage/month`.
- [ ] **Step 5: Commit** `docs: README and smoke test`.
