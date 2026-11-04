# English — app de inglês B1 → C1 com IA

App Android (e versão web em localhost) para treinar inglês do B1 ao C1, no estilo do Be Confident, mas com **repetição espaçada**, **listening gerado por IA**, **conversa ilimitada com IA** e **registro diário de consumo em inglês**.

Projeto de portfólio de GenAI: toda a IA fica em um backend Python, atrás de interfaces de provedor que se trocam por configuração.

- Especificação: [docs/superpowers/specs/2026-11-03-english-app-design.md](docs/superpowers/specs/2026-11-03-english-app-design.md)
- Plano de implementação: [docs/superpowers/plans/2026-11-03-english-app.md](docs/superpowers/plans/2026-11-03-english-app.md)

## O que o app faz

- **26 módulos** (B1: 10, B2: 9, C1: 7) com teoria curta (pode pular), 5 exercícios de listening gerados na hora, conversa com a IA e relatório de correções com nota.
- **Revisão espaçada adaptativa**: a nota decide quando o tema volta (1 dia, 3 dias, depois cresce conforme o desempenho). Erros em conversa livre ou escrita antecipam a revisão do módulo relacionado.
- **Conversa livre** e **escrita corrigida**.
- **Metas do dia** (gramática, falar, escrever, ler, assistir) e sequência de dias completos.
- **Registro de consumo**: o que você assistiu ou leu, com minutos por dia, semana e mês.

## Arquitetura

```
App (Expo / TypeScript)  ──HTTP/JSON──►  Backend (Python / FastAPI)  ──►  Gemini · Claude · OpenAI · Whisper/Piper local
  Android + Web (localhost)                SQLite · currículo · repetição espaçada · controle de custo
```

- **App** (`app/`): só interface. Não guarda chaves nem regras.
- **Backend** (`backend/`): progresso (SQLite), currículo (`content/modules`), prompts (`prompts/`), repetição espaçada, custos e toda a IA.
- **Provedores** (`backend/app/providers/`): `chat`, `report`, `stt` (voz → texto) e `tts` (texto → voz), cada um com implementação gratuita e paga.

### Perfis de IA

| Função | Perfil `free` (padrão) | Perfil `paid` |
|---|---|---|
| Conversa | Gemini (plano gratuito) | Claude Haiku |
| Relatórios e exercícios | Gemini (plano gratuito) | Claude Sonnet |
| Voz → texto | Whisper local (`faster-whisper`) | OpenAI |
| Texto → voz | Piper local | OpenAI |

Troque com `PROVIDER_PROFILE=free|paid` no `.env` do backend e reinicie. Dá para misturar com `CHAT_PROVIDER`, `REPORT_PROVIDER`, `STT_PROVIDER` e `TTS_PROVIDER` (`gemini`, `local`, `anthropic`, `openai`). Os IDs dos modelos também são configuráveis (veja `.env.example`).

Observações do perfil gratuito: a voz local soa mais robótica, o Gemini gratuito tem limite de requisições (o app avisa), e no plano gratuito o Google pode usar os dados enviados para melhorar os modelos.

### Custos (perfil pago)

Os provedores pagos cobram por **créditos pré-pagos**. Compre créditos no console de cada um (Anthropic e OpenAI), deixe a **recarga automática desligada** e defina um **limite mensal** lá. O app mantém uma **estimativa** do gasto do mês (não é o saldo real): avisa em `MONTHLY_WARN_BRL` (R$ 45) e bloqueia chamadas pagas em `MONTHLY_CAP_BRL` (R$ 50). Se um provedor ficar sem crédito, o app mostra qual precisa de recarga.

> Preços e modelos mudam. Confira os preços atuais nas páginas oficiais; os valores em `backend/app/pricing.py` são estimativas.

## Como rodar

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate                       # Windows (Linux/macOS: source .venv/bin/activate)
pip install -e ".[dev,free]"                 # adicione ,paid para Claude e OpenAI
copy .env.example .env                       # preencha API_TOKEN e GEMINI_API_KEY
```

1. Crie uma chave do Gemini em <https://aistudio.google.com/apikey> e coloque em `GEMINI_API_KEY`.
2. Baixe a voz do Piper para `backend/data/voices/`:
   - <https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx>
   - <https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json>
3. Confira tudo: `python scripts/smoke.py` (deve mostrar `[OK]` nos quatro provedores).
4. Suba o servidor: `uvicorn app.server:app_factory --factory --host 0.0.0.0 --port 8000`

O modelo do Whisper local (`base`) é baixado sozinho na primeira transcrição.

### App

```bash
cd app
copy .env.example .env     # EXPO_PUBLIC_API_URL e EXPO_PUBLIC_API_TOKEN (o mesmo API_TOKEN do backend)
npm install
npm run web                # versão web em http://localhost:8081
npx expo start             # Android: escaneie o QR code com o Expo Go
```

No celular, use `EXPO_PUBLIC_API_URL=http://<IP-do-seu-PC>:8000` (celular e PC na mesma rede Wi-Fi; libere a porta 8000 no firewall do Windows). Teste o microfone em **Ajustes → Testar microfone**.

### Testes

```bash
cd backend && python -m pytest        # backend, com provedores falsos (não gasta nada)
cd app && npx jest && npx tsc --noEmit
```

Para o conteúdo: `python scripts/generate_modules.py --only <id> --force` gera de novo a teoria de um módulo com a IA configurada. **Revise os módulos** em `backend/content/modules/` antes de estudar.

## Segurança e privacidade

- Chaves só no `.env` (fora do Git). O app web/Android só conhece o `API_TOKEN`.
- `backend/data/` (banco, áudios, vozes) fica fora do Git.
- O token trafega em cabeçalho (`X-API-Token`); nos áudios, na URL (`?token=`), pois players não enviam cabeçalhos. Use só em rede de confiança.

## Próximos passos (v2)

Módulo de músicas com shadowing (letras coladas pelo usuário e guardadas só localmente) e hospedagem do backend para uso fora de casa.
