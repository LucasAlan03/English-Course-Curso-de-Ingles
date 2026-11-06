# App de Inglês (B1 → C1): Especificação de Design

Data: 2026-11-03 · Prazo da v1: 2026-11-15 · Autor: Lucas (com Claude)

> **Atualização (2026-11-05):** aulas, revisões, plano do dia, provas de nível e músicas agora seguem [2026-11-05-daily-plan-design.md](2026-11-05-daily-plan-design.md), que substitui as partes de listening por IA, pilares do dia e fluxo da aula deste documento.

## 1. Objetivo

Um app Android de uso pessoal para treinar inglês do B1 ao C1, no estilo do Be Confident, mas com **repetição espaçada**, **listening gerado por IA**, **conversa ilimitada com IA** e um **registro diário de consumo em inglês**. O projeto também serve de portfólio para a vaga de GenAI do iFood, então o uso de IA precisa ser claro, organizado e fácil de explicar.

**Critérios de sucesso da v1**
1. Concluir um módulo de ponta a ponta (teoria → listening → conversa → relatório → nota) no Android e na web.
2. Um módulo concluído gera uma revisão agendada, e a revisão aparece em "Revisões de hoje" na data certa.
3. A conversa não tem limite de trocas, e o custo do mês aparece no app.
4. O registro de consumo (assistir/ler) funciona e mostra totais diários, semanais e mensais.
5. O código roda a partir do README em outra máquina, sem chaves de API no repositório.

**Fora do escopo da v1**: módulo de músicas com shadowing (v2), conversas por WhatsApp, vários usuários, login, hospedagem do backend para uso fora de casa.

## 2. Arquitetura

```
App (Expo / TypeScript)  ──HTTP/JSON──►  Backend (Python / FastAPI)  ──►  Claude · OpenAI
  Android + Web (localhost)                SQLite · currículo · SRS
```

- **App**: só interface. Telas, gravação de voz, player de áudio. Não guarda chaves nem regras de negócio.
- **Backend**: única fonte de verdade do progresso (SQLite). Guarda as chaves de API e concentra toda a lógica de IA e de repetição espaçada.
- **Rede**: em desenvolvimento, tudo no PC (`localhost`). O celular acessa o backend pelo IP do PC na mesma rede Wi-Fi. Como é uso pessoal, um token fixo (`API_TOKEN` no `.env`, enviado no cabeçalho) protege o backend.
- **Hospedagem fora de casa**: depois da v1.

### Provedores de IA (atrás de interfaces)

| Interface | Função | Perfil `free` (padrão) | Perfil `paid` |
|---|---|---|---|
| `ChatModel` | Respostas da conversa | Gemini (plano gratuito), modelo leve | Claude, modelo leve (Haiku) |
| `ReportModel` | Relatório final, geração de exercícios, correção de escrita | Gemini (plano gratuito), modelo forte | Claude, modelo forte (Sonnet) |
| `SpeechToText` | Voz → texto | Whisper local (`faster-whisper`, roda no PC do backend) | OpenAI Whisper (API) |
| `TextToSpeech` | Texto → voz | Voz local (Piper ou Kokoro) | OpenAI TTS (API) |

**Troca de perfil**: a variável `PROVIDER_PROFILE=free|paid` no `.env` escolhe o conjunto inteiro. Para misturar (ex.: conversa paga com voz gratuita), cada interface também aceita uma variável própria (`CHAT_PROVIDER`, `REPORT_PROVIDER`, `STT_PROVIDER`, `TTS_PROVIDER`) que vale mais que o perfil. O app não muda nada: só o backend precisa ser reiniciado.

Cada interface tem uma implementação por provedor, e todas as implementações passam pelos mesmos testes de contrato. Os identificadores exatos dos modelos e os preços são conferidos na implementação e ficam em `config`, nunca espalhados pelo código.

## 3. Currículo (26 módulos fixos)

Fonte do conteúdo: British Council/EAQUALS *Core Inventory for General English* e Cambridge *English Grammar Profile*. Cada módulo guarda sua referência. Os arquivos ficam em `backend/content/modules/*.yaml`, gerados com ajuda da IA e **revisados por você** antes de fechar.

| B1 (10) | B2 (9) | C1 (7) |
|---|---|---|
| Past simple × past continuous | Present perfect continuous | Inversion |
| Present perfect × past simple | Past perfect e narrativas | Cleft sentences |
| Futuros (will / going to / present continuous) | 3º condicional e mistos | Modais no passado |
| 1º e 2º condicionais | Voz passiva | Causative |
| Modais de obrigação e conselho | Reported speech | Hedging |
| Comparativos e superlativos | Modais de dedução | Participle clauses |
| Preposições (tempo, lugar, movimento) | *Used to / would / be used to* | Collocations e idioms |
| Gerúndio × infinitivo | *Wish / if only* | |
| Phrasal verbs do dia a dia | Conectivos de contraste e argumentação | |
| Relative clauses | | |

**Formato de cada arquivo de módulo**: `id`, `level`, `title`, `order`, `theory_md` (2–3 min de leitura, com exemplos), `scenario` (situação real, personagem da IA e objetivo da conversa), `target_structures` (lista usada nos prompts) e `source`.

**Navegação**: livre entre os níveis. A tela de trilhas mostra todos os módulos, o progresso por nível e marca o "próximo sugerido" (o primeiro módulo não concluído do seu nível atual, B1 no início).

## 4. Fluxo de um módulo

1. **Teoria**: texto curto, com botão "Pular".
2. **Listening (5 itens)**: gerados na hora. 3 de múltipla escolha e 2 de lacuna digitada. Cada item tem um áudio (TTS), a pergunta, a resposta correta e uma explicação curta mostrada após responder. Os prompts recebem a lista dos seus erros recentes naquele módulo.
3. **Conversa**: a IA assume o personagem do cenário e conduz a conversa para usar as estruturas do módulo.
   - Sem limite de trocas. Botão "Encerrar e ver relatório".
   - Entrada por voz (segurar para falar, soltar para enviar) ou por texto.
   - Resposta da IA em texto, com áudio opcional (chave "ouvir/ler").
   - Depois de umas 6 trocas, a IA pode sugerir encerrar, e a decisão é sua.
   - **Memória**: as últimas 10 trocas vão completas, e as anteriores viram um resumo atualizado, para o custo por troca não crescer.
4. **Relatório** (modelo forte, uma chamada sobre a conversa inteira): lista de erros (`said`, `corrected`, `explanation`, `module_id`), expressões mais naturais, pontos fortes e nota de 0 a 100.
5. **Agendamento**: nota final = 40% listening + 60% nota da conversa. A nota alimenta a revisão espaçada.

**Revisão** (~5 min): 3 itens de listening novos + mini conversa de 3–4 trocas, gerados a partir dos erros daquele módulo.

**Conversa livre**: sem módulo. Você escolhe um assunto (ou a IA sugere). O relatório mapeia cada erro ao módulo mais próximo. Se um módulo acumular **3 ou mais erros em 7 dias**, sua revisão é antecipada para amanhã.

**Escrita**: a IA sugere um tema curto, você escreve um texto (3–8 linhas), e o modelo forte devolve correções, uma versão melhorada e os erros (que entram em `mistakes`).

## 5. Repetição espaçada

Estado por módulo em `reviews`: `next_due`, `interval_days`, `ease` (inicial 2,5), `repetitions`.

| Nota | Efeito |
|---|---|
| ≥ 85 | Intervalo × `ease`; `ease` + 0,1 (máx. 3,0) |
| 60–84 | Intervalo × 1,2; `ease` inalterada |
| < 60 | `interval_days` = 1 (volta amanhã); `ease` − 0,2 (mín. 1,3); `repetitions` = 0 |

Sequência inicial: a 1ª revisão acontece 1 dia após a aula, a 2ª 3 dias depois, e a partir da 3ª vale a fórmula acima. A tela inicial mostra "Revisões de hoje" (atrasadas primeiro) e "Continuar trilha".

## 6. Metas do dia e registro de consumo

**Cinco pilares** exibidos como uma barra na tela inicial:

| Pilar | Como é marcado |
|---|---|
| Gramática | Automático: módulo ou revisão concluído no dia |
| Falar | Automático: conversa (módulo, revisão ou livre) no dia |
| Escrever | Automático: tarefa de escrita concluída no dia |
| Ler | Check quando existe ao menos um registro de leitura no dia |
| Assistir | Check quando existe ao menos um registro de assistir no dia |

O status dos pilares e a **sequência de dias completos** são **calculados** a partir de `sessions` e `media_logs`, sem tabela própria.

**Registro de consumo** (`media_logs`):
- **Assistir**: categoria (série / filme / vídeo / podcast), título, episódio (opcional), minutos. Vários itens por dia.
- **Ler**: categoria (HQ / livro / artigo / outro), título, minutos, páginas (opcional).
- Telas: formulário rápido do dia, lista do dia, e totais de minutos por dia, semana e mês, por categoria. Itens podem ser editados e excluídos.

## 7. Modelo de dados (SQLite)

| Tabela | Campos principais |
|---|---|
| `sessions` | id, kind (`lesson`/`review`/`free`/`writing`), module_id?, started_at, duration_s, listening_score?, conversation_score?, final_score? |
| `messages` | id, session_id, role (`user`/`assistant`), text, audio_path?, created_at |
| `mistakes` | id, session_id, module_id, said, corrected, explanation, created_at |
| `reviews` | module_id (PK), next_due, interval_days, ease, repetitions, last_score |
| `listening_items` | id, session_id, kind (`choice`/`gap`), prompt, audio_path, options?, answer, explanation, user_answer?, correct? |
| `media_logs` | id, date, type (`watch`/`read`), category, title, episode?, minutes, pages?, created_at |
| `api_usage` | id, provider, model, kind, input_units, output_units, cost_brl, created_at |

Os módulos vivem nos arquivos YAML. O banco só guarda o `module_id` (texto). Os áudios gerados ficam em `backend/data/audio/` (fora do Git).

## 8. API do backend (resumo)

| Rota | Função |
|---|---|
| `GET /modules` · `GET /modules/{id}` | Trilhas, progresso e conteúdo do módulo |
| `POST /sessions` | Inicia aula, revisão, conversa livre ou escrita |
| `GET /sessions/{id}/listening` | Gera e devolve os 5 itens |
| `POST /listening/{item_id}/answer` | Registra a resposta e devolve a correção |
| `POST /sessions/{id}/turn` | Envia texto ou áudio, devolve a resposta da IA (texto + áudio) |
| `POST /sessions/{id}/finish` | Gera o relatório, calcula a nota e atualiza a revisão |
| `POST /writing/prompt` · `POST /writing/submit` | Tema de escrita e correção |
| `GET /home` | Revisões de hoje, próximo módulo, pilares, sequência |
| `GET/POST/PUT/DELETE /media` · `GET /media/summary` | Registro de consumo e totais |
| `GET /usage/month` | Custo acumulado do mês |

## 9. Prompts e saídas estruturadas

- Toda saída estruturada (itens de listening, relatório, correção de escrita) usa **JSON validado com Pydantic**. Se a validação falhar, o backend repete a chamada **uma vez**, e depois devolve erro claro ao app.
- **Persona da conversa**: o prompt de sistema recebe o cenário, as estruturas-alvo e o nível (B1/B2/C1). A IA responde em frases do nível indicado, faz perguntas abertas, **não corrige durante a conversa** e não sai do personagem.
- **Prompts ficam em arquivos** (`backend/prompts/*.md`), versionados e separados do código.
- **Listening**: o prompt pede diálogos curtos em situações reais, usando a estrutura-alvo, e recebe os erros recentes do módulo para variar o foco.

## 10. Controle de custo

- A v1 começa no perfil `free`, com custo R$ 0. Os avisos e o bloqueio abaixo só entram em ação para chamadas de provedores **pagos**.
- Cada chamada registra o uso em `api_usage` (custo 0 nos provedores gratuitos), com preços lidos de `config`.
- O app mostra o total do mês e avisa ao passar de **R$ 45**. Em **R$ 50** o backend bloqueia novas chamadas pagas até você liberar manualmente.
- **Limites do plano gratuito**: se o Gemini responder "limite de requisições", o backend espera e tenta de novo uma vez; se persistir, o app avisa e sugere aguardar ou ativar o perfil pago.
- Áudio da IA é opcional, e o modelo leve responde nas trocas.
- **Pagamento (só no perfil `paid`)**: créditos pré-pagos nos consoles da Anthropic e da OpenAI, com recarga automática desligada e limite mensal definido lá. O contador do app é uma **estimativa**, não o saldo real. Os avisos (R$ 45) e o bloqueio (R$ 50) são um teto configurável (`MONTHLY_CAP_BRL`, `MONTHLY_WARN_BRL`).
- Se um provedor responder "sem crédito" ou "limite atingido", o backend devolve um erro específico (`provider_out_of_credit`), e o app mostra qual provedor precisa de recarga. O README explica como comprar créditos.

## 11. Tratamento de erros

| Situação | Comportamento |
|---|---|
| Falha de rede ou da API de IA | Uma nova tentativa automática; depois, mensagem clara, sem perder a sessão |
| Sessão interrompida (app fechado) | Mensagens já salvas permitem retomar ou encerrar e gerar o relatório |
| Transcrição vazia ou ruído | Pede para repetir, sem enviar à IA |
| Permissão de microfone negada | Cai para o modo texto |
| Limite de custo atingido | Mensagem explicando, e as telas sem IA continuam funcionando (revisão de erros, registro de consumo) |
| JSON inválido da IA | Uma nova tentativa; depois, erro com opção de repetir |

## 12. Testes

- **Backend (pytest)**: regras de repetição espaçada (tabela de notas), cálculo de nota, cálculo dos pilares e da sequência, totais do registro de consumo, validação dos esquemas Pydantic e controle de custo. Todos com provedores de IA **falsos (fakes)**, sem gastar dinheiro.
- **Contrato dos provedores**: o mesmo conjunto de testes roda contra o fake e contra cada implementação real, garantindo que trocar de perfil não quebra o resto.
- **Provedores reais**: um teste de fumaça manual (`make smoke`) que faz uma chamada real a cada provedor do perfil ativo.
- **App**: testes de componentes nas telas de registro e home; fluxo completo de um módulo conferido manualmente no Android e na web.
- A lógica de data usa um relógio injetável, para testar revisões sem esperar dias.

## 13. Estrutura do projeto

```
AP - ORG ESTUDOS/
├─ backend/   (FastAPI) app/ · content/modules/ · prompts/ · tests/ · data/ (ignorado no Git)
├─ app/       (Expo, TypeScript) telas · api client · hooks de áudio
├─ docs/superpowers/specs/
├─ .env.example · .gitignore · README.md
```

## 14. Segurança e portfólio

- Chaves só em `.env` (ignorado no Git); `.env.example` documenta as variáveis.
- Dados pessoais (`data/`, banco, áudios) ficam fora do repositório.
- O README explica a arquitetura, a camada de provedores, o controle de custo e como rodar, e inclui um vídeo ou GIF de demonstração.

## 15. Riscos e pontos a validar na implementação

- **Gravação de voz na web e no Android** (Expo) pode se comportar de forma diferente: validar cedo, no começo da implementação.
- **Latência da conversa** (STT → LLM → TTS): se passar de ~4 s, mostrar o texto da IA antes do áudio. No perfil `free`, o Whisper local depende do seu PC; validar cedo com um modelo pequeno.
- **Qualidade do perfil gratuito**: a voz local e os limites do Gemini são o ponto fraco. Depois de alguns dias de uso, você decide se vale ativar o perfil `paid` ou parte dele.
- **Privacidade no plano gratuito do Gemini**: não enviar dados sensíveis; só as conversas de estudo.
- **Qualidade do conteúdo gerado**: sua revisão dos 26 módulos é uma etapa do plano, não um detalhe.
- **Preços e identificadores de modelos** mudam: conferir na implementação.
- **Prazo de 12 dias**: ordem sugerida — 1º backend e SRS, 2º conversa com voz, 3º listening, 4º home/pilares/registro, 5º conteúdo e polimento. Se apertar, a escrita corrigida é o primeiro item a sair da v1.

## 16. v2 (depois do dia 15)

Módulo de músicas com shadowing: você cola a letra (guardada só localmente), a IA explica gírias e gramática, e o Whisper compara sua gravação com a letra. Hospedagem do backend para uso fora de casa.
