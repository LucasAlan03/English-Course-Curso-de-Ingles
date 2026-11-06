# English — app de inglês B1 → C1 com IA

App Android (e versão web em localhost) para treinar inglês do B1 ao C1, no estilo do Be Confident: um **dia de estudo guiado em 7 blocos**, **1.242 exercícios feitos à mão** corrigidos sem IA, **repetição espaçada**, **provas de nível**, **músicas com ditado e shadowing**, **conversa ilimitada com IA** e **registro de minutos** de ligações, séries e leitura.

Projeto de portfólio de GenAI: toda a IA fica em um backend Python, atrás de interfaces de provedor que se trocam por configuração.

- Especificação: [docs/superpowers/specs/2026-11-03-english-app-design.md](docs/superpowers/specs/2026-11-03-english-app-design.md)
- Plano de implementação: [docs/superpowers/plans/2026-11-03-english-app.md](docs/superpowers/plans/2026-11-03-english-app.md)
- Plano do dia, exercícios, provas e músicas: [spec](docs/superpowers/specs/2026-11-05-daily-plan-design.md) · [plano](docs/superpowers/plans/2026-11-05-daily-plan.md)

## O que o app faz

- **O dia em 7 blocos**, um liberando o próximo: Gramática (10–20 min) → Música → Ligação 1 (10 min) → Assistir (45 min) → Ler (40 min) → Ligação 2 (10 min) → Anki. Dá para pular e voltar. A sequência conta dias com os 7 blocos feitos. No Android, lembretes locais nos horários escolhidos.
- **46 módulos** (B1: 19, B2: 16, C1: 11), cada um com teoria curta e **27 exercícios** em 3 blocos (reconhecer → praticar → produzir): múltipla escolha, ouvir, lacuna, ditado, corrigir o erro, ordenar, transformar e traduzir. Corrigidos **sem IA**, com tradução pronta do enunciado e glossário.
- **Revisão espaçada**: a nota do módulo decide quando ele volta; a revisão traz 9 exercícios do próprio banco, primeiro os que você errou.
- **Provas de nível**: 30 questões sorteadas de um banco de 40 por nível. Precisa de 75% para abrir o nível seguinte.
- **Músicas**: você cola a letra (fica só no seu banco local); o app divide em trechos e, a cada dia, faz ditado e shadowing de um trecho até o desafio final de cantar a música inteira. A IA aponta, uma vez por música, onde aparece a gramática do curso.
- **Ligações**: a conversa do cenário do módulo (Ligação 1) e o **Ensine a IA** (Ligação 2, você explica o assunto para uma aluna confusa). O tempo é contado pelo app e você pode lançar ligações de fora (ex.: Be Confident). O relatório pode ser baixado em Markdown.
- **Tocar para traduzir**: qualquer palavra em inglês na conversa, na teoria e nas letras; palavras salvas viram CSV para o Anki.
- **Registro em minutos**: séries (episódios × minutos, com **+**), vídeos do YouTube (título automático pelo link) e leitura (páginas e palavras novas).

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

Conteúdo: teoria em `backend/content/modules/`, exercícios em `backend/content/exercises/`, provas em `backend/content/exams/`. Os testes validam todo o conteúdo (distribuição dos 27 exercícios, uma única opção certa, glossário que não entrega a resposta etc.). Depois de mudar exercícios de ouvir ou ditado, grave os áudios uma vez com o Piper: `python scripts/prefill_audio.py` (ou `--only <id>`). Pelo botão "Reportar exercício" você marca um exercício suspeito para corrigir depois.

## Segurança e privacidade

- Chaves só no `.env` (fora do Git). O app web/Android só conhece o `API_TOKEN`.
- `backend/data/` (banco, áudios, vozes e as **letras das músicas**) fica fora do Git. Letras nunca vão para arquivos versionados.
- O token trafega em cabeçalho (`X-API-Token`); nos áudios, na URL (`?token=`), pois players não enviam cabeçalhos. Use só em rede de confiança.

## Próximos passos (v2)

Análise de desempenho com sugestões automáticas ("você está fraco em X") e hospedagem do backend para uso fora de casa. Os lembretes funcionam no app Android (na web só existe o cartão do próximo bloco).
