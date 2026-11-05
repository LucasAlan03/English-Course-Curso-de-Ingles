# Plano do Dia, Exercícios e Músicas: Especificação de Design

Data: 2026-11-05 · Autor: Lucas (com Claude) · Base: [2026-11-03-english-app-design.md](2026-11-03-english-app-design.md)

## 1. Objetivo

Deixar o app **mais ativo e mais divertido**, sem virar um curso extenso. Hoje cada aula tem só 5 exercícios e o dia é um checklist solto de 5 pilares. Depois desta mudança:

1. O curso tem **46 módulos**, cada um com **27 exercícios** feitos à mão, em 3 blocos de 9.
2. O app guia um **dia de estudo em 7 blocos**, que se liberam um depois do outro com alertas.
3. Cada dia tem um **trecho de uma música** que você escolheu, do começo ao fim, até conseguir cantá-la.
4. O tempo de **ligação**, de **séries/vídeos** e de **leitura** é registrado em minutos e soma em barras de progresso.
5. Qualquer palavra em inglês pode ser **tocada para traduzir**, com o contexto da frase.

O app é o **mediador** do dia: mostra o que fazer agora e mede o tempo. Análise de desempenho e sugestões automáticas ficam para depois. Por enquanto, você baixa o relatório da conversa e traz para análise.

### Base na pesquisa e no vídeo de referência
- **Tentar lembrar e produzir** é melhor do que reler. Os blocos vão de reconhecer → praticar → produzir.
- **Leitura extensiva** (inclusive quadrinhos) e **séries com legenda em inglês** ensinam vocabulário. As palavras precisam se repetir, por isso existe o campo "palavras novas".
- **Músicas repetidas** fixam vocabulário. **Shadowing** melhora fluência e listening. **Ditado** treina a percepção palavra por palavra.
- Do vídeo *"How I Went From Zero English to C2"*: usar seus hobbies em inglês, transcrever, cantar rap junto, falar sozinho em inglês e **ensinar o que aprendeu**.

### Critérios de sucesso
1. Um dia completo pode ser feito do bloco 1 ao 7 no Android e na web, com cada bloco liberando o próximo.
2. Os 46 módulos carregam com 27 exercícios válidos cada, e os testes de conteúdo passam.
3. Uma música colada é dividida em trechos; ditado e shadowing de um trecho funcionam e a barra da música avança.
4. Ligação, séries/vídeos e leitura somam minutos corretamente (app e lançamento manual).
5. Tocar numa palavra traduz considerando a frase, e a segunda vez não chama a IA.
6. Abrir um bloco de exercícios não chama nenhuma IA.

### Fora do escopo
- Cálculo de desempenho e sugestões automáticas ("você está fraco em X").
- O app sugerir músicas sozinho, ou guardar áudio de música.
- Integração direta com o Anki (o bloco é só um check, mas as palavras novas podem ser exportadas em CSV).
- Notificações push por servidor.

## 2. O dia em 7 blocos

| # | Bloco | Meta | Conta como feito quando |
|---|---|---|---|
| 1 | Gramática | 10–20 min | Concluiu um módulo hoje (respondeu o último exercício do bloco 3) **ou** somou 20 min de exercícios no dia |
| 2 | Música | 10–20 min | Fez o ditado **e** o shadowing do trecho do dia |
| 3 | Ligação 1 | 10 min | Os minutos de ligação do dia chegaram a 10 |
| 4 | Assistir | 45 min | Séries + filmes + vídeos do dia somam 45 min |
| 5 | Ler | 40 min | As leituras do dia somam 40 min |
| 6 | Ligação 2 | 10 min | Os minutos de ligação do dia chegaram a 20 |
| 7 | Anki | 10 min | Você marcou o check |

**Trilha guiada.** Os blocos seguem essa ordem e só um é o "bloco atual". Ao concluir um bloco, aparece um cartão de comemoração com o próximo ("Boa! Agora a música de hoje 🎵"). Você pode **pular** o bloco atual e **voltar** a um bloco pulado quando quiser. Registros feitos fora de ordem (ex.: lançar leitura antes da música) contam normalmente, e um bloco já cumprido é marcado como feito quando a trilha chega nele.

**Estado calculado, não guardado.** O backend calcula o estado de cada bloco a partir dos registros do dia (exercícios, músicas, ligações, mídia, checks). Só os pulos e o check do Anki são gravados. O "dia" segue a data local do backend, como hoje.

**Sequência (streak).** Um dia conta como completo quando os 7 blocos estão feitos. Bloco pulado não conta. A sequência atual por pilares é substituída.

**Alertas.**
- **No app:** o cartão do próximo bloco aparece ao concluir um bloco e na tela inicial.
- **No Android:** lembretes locais (`expo-notifications`) em horários escolhidos nas Configurações (padrão: 19h e 21h). O lembrete só dispara se o dia ainda não estiver completo e diz o que falta. Na web só existe o cartão.

A tela inicial passa a mostrar a trilha do dia (7 blocos, o atual em destaque, barras de minutos) no lugar dos pilares.

## 3. Currículo e exercícios

### 3.1 Novos módulos (26 → 46)
Os módulos que juntam dois assuntos viram módulos separados. Cada módulo novo tem teoria própria, curta (pt-BR com exemplos em inglês), e um cenário de conversa próprio.

| Módulo antigo | Vira |
|---|---|
| B1 Past simple × past continuous | Past simple · Past continuous (o contraste entra no bloco 3) |
| B1 Present perfect × past simple | Present perfect (o contraste com o past simple entra no bloco 3) |
| B1 Futuros | Will · Going to · Present continuous para o futuro |
| B1 1º e 2º condicionais | 1º condicional · 2º condicional |
| B1 Modais de obrigação e conselho | Obrigação e proibição · Conselho |
| B1 Comparativos e superlativos | Comparativos · Superlativos |
| B1 Preposições | Tempo · Lugar · Movimento |
| B1 Gerúndio × infinitivo | Verbo + -ing · Verbo + to (o contraste entra no bloco 3) |
| B1 Phrasal verbs · Relative clauses | mantidos |
| B2 Present perfect continuous · Past perfect | mantidos |
| B2 3º condicional e mistos | 3º condicional · Condicionais mistos |
| B2 Voz passiva | Passiva no presente e passado · Passiva perfect, futuro e com modais |
| B2 Reported speech | Afirmações · Perguntas e pedidos |
| B2 Modais de dedução | Dedução no presente · Dedução no passado |
| B2 Used to / would / be used to | Used to e would · Be/get used to |
| B2 Wish / if only | Desejos no presente · Arrependimentos no passado |
| B2 Conectivos | Contraste · Argumentação |
| C1 Inversion | Advérbios negativos · Condicional invertida |
| C1 Cleft sentences | It-cleft · Wh-cleft |
| C1 Modais no passado | Crítica e arrependimento · Possibilidades não realizadas |
| C1 Collocations e idioms | Collocations · Idioms |
| C1 Causative · Hedging · Participle clauses | mantidos |

Total: B1 19 · B2 16 · C1 11 = **46 módulos**.

### 3.2 Os 27 exercícios
Escritos à mão por Claude, versionados no repositório em `backend/content/exercises/<module_id>.yaml`. A teoria continua em `backend/content/modules/<module_id>.yaml`.

| Bloco | Foco | Os 9 exercícios |
|---|---|---|
| 1 · Reconhecer | entender a forma | 5 múltipla escolha · 2 ouvir e responder · 2 lacunas |
| 2 · Praticar | montar com apoio | 3 múltipla escolha · 1 lacuna · 2 corrigir o erro · 2 ordenar palavras · 1 ditado |
| 3 · Produzir | criar sozinho | 2 múltipla escolha · 1 ouvir e responder · 1 corrigir o erro · 2 transformar · 2 traduzir PT→EN · 1 ditado |

Totais por módulo: 10 múltipla escolha, 3 lacunas, 3 ouvir, 2 ditados, 3 corrigir, 2 transformar, 2 ordenar, 2 traduzir.

**Formato de cada exercício:** `id`, `block` (1–3), `type`, `prompt` (enunciado), `options` (só múltipla escolha e ouvir com opções), `words` (só ordenar), `audio_text` (só ouvir e ditado), `answers` (lista de respostas aceitas), `explanation` (pt-BR, curta).

**Correção sem IA.** A resposta é normalizada (minúsculas, sem pontuação nas pontas, espaços e apóstrofos uniformes, contrações equivalentes como *I'm* = *I am*) e comparada com `answers`. Em traduzir e transformar, a lista traz as variações aceitáveis. A primeira resposta é a que conta, como hoje.

**Áudio.** Os textos de ouvir e ditado viram `.wav` pelo Piper uma única vez (script de preparo, `scripts/prefill_audio.py`). Nenhuma IA de texto é usada nos exercícios.

**Testes de conteúdo** (falham o build se o conteúdo quebrar): cada módulo tem 27 exercícios na distribuição exata acima, ids únicos, toda múltipla escolha tem exatamente uma opção entre `answers`, ordenar usa exatamente as palavras da resposta, sem enunciados repetidos dentro do módulo, todo módulo tem teoria e cenário.

**Reportar exercício.** Um botão discreto marca o exercício como suspeito (`exercise_reports`). Você me traz a lista e eu corrijo o YAML.

### 3.3 Fluxo de uma aula
Teoria (pode pular) → bloco 1 → bloco 2 → bloco 3 → tela de resultado do módulo. O progresso é salvo por exercício: se o tempo acabar, amanhã você continua de onde parou. A **conversa do cenário** sai da aula e vira a Ligação 1 (seção 5).

**Tempo de gramática.** O app envia, a cada resposta, os segundos desde a resposta anterior (máximo de 3 min contados por intervalo). A soma do dia alimenta a regra dos 20 min.

### 3.4 Nota e revisões
- **Nota do módulo** = % de acertos nos 27 exercícios. Ao concluir o bloco 3, a nota entra na repetição espaçada (`srs.next_state`), como hoje.
- **Revisão** = 9 exercícios do próprio módulo, primeiro os que você errou e depois os que viu há mais tempo. A nota da revisão atualiza o agendamento. As revisões **não usam IA**.
- O banco de listening gerado por IA (`lesson_bank`) e o listening de revisão gerado por IA saem do app.

### 3.5 Migração dos dados atuais
Uma tabela de equivalência (módulo antigo → primeiro módulo novo) atualiza `reviews` e `sessions.module_id`. O `lesson_bank` é apagado. Os relatórios e os erros antigos continuam no histórico.

## 4. Músicas

**Biblioteca.** Você cola título, artista, link (YouTube/Spotify) e a letra. A letra fica **só no banco local** (`backend/data`, fora do git). Você escolhe uma **música do momento**.

**Trechos.** O backend divide a letra do começo ao fim: separa por estrofes e quebra cada estrofe em trechos de até 4 versos. Um trecho com o mesmo texto de um anterior (o refrão repetido) é marcado como **repetição**: aparece como revisão rápida e não conta trecho novo. Barra: "*Lose Yourself*: 5/14 trechos".

**Gramática apontada.** Ao cadastrar a música, a IA lê a letra **uma única vez** e marca, por trecho, frases que usam a gramática de algum módulo (ex.: *"If you had one shot… would you capture it"* → 2º condicional). Resultado salvo. Na missão, o trecho mostra o destaque quando ele existe; se não existe, nada aparece. Se a IA estiver indisponível, a música é salva sem marcações e dá para tentar de novo depois.

**Missão do dia (um trecho, na ordem):**
1. **Ditado:** você toca a música no YouTube/Spotify (botão abre o link), ouve o trecho e escreve o que entendeu. O app compara palavra por palavra com a letra (sem IA) e mostra acertos, faltas e trocas.
2. **Shadowing:** você grava cantando ou falando junto. O Whisper transcreve e o app mostra a % de palavras que bateram.

O trecho conta como feito ao completar os dois passos. Depois do último trecho vem o **desafio final**: gravar a música inteira (ou o maior pedaço que conseguir) e ver a % de acerto. Você pode trocar a música do momento a qualquer hora, e o progresso de cada música fica guardado.

## 5. Ligações

- **Ligação 1 (sugerida):** conversa por voz com o personagem do cenário do módulo atual. É a conversa que hoje fica no fim da aula, com o mesmo relatório.
- **Ligação 2 (sugerida):** **Ensine a IA**. A IA faz o papel de um aluno confuso, que pergunta sobre a gramática do dia, e você explica em inglês. O relatório avalia a clareza da explicação e os erros. A conversa livre também vale.
- Qualquer ligação do dia conta para os dois blocos. Os minutos enchem a Ligação 1 até 10 e o excedente vai para a Ligação 2.

**Tempo no app.** O cronômetro aparece na tela ("6:40 / 10:00"). O backend calcula a duração pelos horários das mensagens: soma os intervalos entre início, mensagens e fim, e cada intervalo conta no máximo 3 min (pausa automática quando ninguém fala).

**Tempo de fora.** Botão "Lançar ligação de fora": origem (ex.: "Be Confident"), minutos e nota opcional. Soma com o tempo do app.

**Histórico.** Minutos de ligação por dia e por semana na aba de registro.

**Baixar relatório.** A tela do relatório ganha "Baixar relatório", que gera um `.md` com a conversa, as correções e as notas. Na web é um download e no Android abre o compartilhar do sistema.

## 6. Assistir e ler

O registro de mídia atual (`media_logs`) é ampliado. **Todo tempo é em minutos.**

- **Séries e filmes:** cada linha tem título, duração do episódio (min) e quantidade de episódios com botão **+**. Minutos = duração × quantidade. O botão **+ outra série** adiciona uma linha no mesmo dia.
- **Vídeos do YouTube:** campo para colar o link. O título é preenchido sozinho (oEmbed do YouTube, sem chave) e pode ser editado. Você informa os minutos. Botão **+ outro vídeo**. Conta na mesma barra de 45 min.
- **Leitura:** título, minutos e páginas (os dois você anota), e um campo opcional de **palavras novas**. Botão **+ outra leitura**.

## 7. Palavras: tocar para traduzir

**Onde:** mensagens da conversa, exercícios (depois de respondidos), teoria e letras das músicas.

**Como:** tocar numa palavra abre um balão com a tradução **considerando a frase** e uma nota curta quando for gíria, phrasal verb ou expressão (ex.: *done* em *"How many people done doubted you"* → "já (informal, rap)"). A tradução vem da IA de chat (modelo leve) e fica guardada por palavra + frase: tocar de novo não chama a IA. Se a IA falhar, o balão mostra o erro e um "tentar de novo".

**Palavras novas.** O botão "salvar" no balão e o campo de palavras novas da leitura alimentam uma única lista (palavra, frase, tradução, origem). A lista pode ser **exportada em CSV para o Anki**.

## 8. Arquitetura

Tudo continua no app Expo + backend FastAPI + SQLite atuais. Nenhuma dependência nova no backend. No app entra `expo-notifications` (lembretes locais).

### Unidades novas no backend
| Unidade | Faz | Depende de |
|---|---|---|
| `content.py` (ampliado) | Carrega módulos e exercícios dos YAML, valida o formato | YAML |
| `exercises.py` | Normaliza e corrige respostas, escolhe os exercícios da revisão | conteúdo, banco |
| `daily_plan.py` | Calcula o estado dos 7 blocos e o próximo bloco | registros do dia, relógio |
| `call_time.py` | Calcula os minutos de uma ligação pelos horários das mensagens | mensagens |
| `songs.py` | Divide a letra em trechos, marca repetições, compara palavras | — |
| `ai/song_grammar.py` | Marca a gramática dos trechos (uma chamada por música) | IA de relatório |
| `ai/translate.py` | Traduz palavra + frase, com cache | IA de chat |
| `ai/teach.py` | Persona do "aluno confuso" para o Ensine a IA | IA de chat |

### Tabelas novas ou alteradas
- `exercise_attempts` (módulo, exercício, sessão, resposta, acerto, segundos, data)
- `exercise_reports` (módulo, exercício, nota, data)
- `songs` (título, artista, link, letra, música do momento) · `song_chunks` (música, ordem, texto, repetição de, gramática) · `song_practice` (trecho, tipo ditado/shadowing/final, texto, % acerto, data)
- `call_logs` (data, origem, minutos, nota)
- `media_logs` + colunas `unit_minutes`, `count`, `url`, `new_words`
- `words` (palavra, frase, tradução, nota, origem, data) · `translations` (cache por palavra + frase)
- `day_state` (data, bloco, pulado/check do Anki)
- `sessions.kind` aceita `teach`. `lesson_bank` é removida.

### Rotas novas (principais)
`GET /today` (plano do dia) · `POST /today/{block}/skip` e `/unskip` · `POST /today/anki` · `GET /modules/{id}/exercises` · `POST /exercises/{module}/{id}/answer` · `POST /exercises/{module}/{id}/report` · `GET /reviews/{module}/exercises` · CRUD `/songs`, `GET /songs/current/today`, `POST /songs/chunks/{id}/dictation`, `POST /songs/chunks/{id}/shadow` (áudio) · `POST /calls/external` · `GET /media/youtube-title?url=` · `POST /translate` · CRUD `/words`, `GET /words/export.csv` · `GET /sessions/{id}/report.md`.

### App
- Tela inicial = trilha do dia (7 blocos) + cartão do próximo bloco.
- Aula = teoria → 3 blocos de exercícios (um componente por tipo) → resultado.
- Música = biblioteca, música do momento, tela do trecho (ditado → shadowing → feito).
- Ligação = a tela de conversa atual com cronômetro; Ensine a IA usa a mesma tela.
- Registro = séries/filmes, vídeos e leituras com as linhas de **+**, ligações de fora, palavras novas.
- `TappableText` = componente que torna cada palavra tocável, usado nos quatro lugares da seção 7.
- Configurações = horários dos lembretes, exportar palavras.

## 9. Erros e casos de borda
- **IA fora do ar ou no limite:** exercícios, revisões, trilha, registros e ditado continuam funcionando, porque não usam IA. Só tradução, marcação de gramática da música, conversa e relatório mostram o erro com "tentar de novo".
- **Shadowing sem fala reconhecida:** "Não ouvi nada, tente de novo". A tentativa não conta.
- **Letra vazia ou só com linhas em branco:** o cadastro é recusado com mensagem clara.
- **Link do YouTube inválido ou sem internet:** o título fica em branco para você digitar.
- **Ligação deixada aberta:** intervalos acima de 3 min contam só 3 min.
- **Nenhuma música cadastrada:** o bloco Música mostra "Cadastre sua primeira música" e pode ser pulado.
- **Música terminada:** depois do desafio final, o bloco pede para escolher a próxima música do momento.
- **Virada do dia no meio de um bloco:** o registro vale para o dia em que foi salvo.

## 10. Testes
- **Backend (pytest, TDD):** validador de conteúdo rodando sobre os 46 módulos reais; normalização e correção; regras de cada bloco e do pular/voltar; cálculo de minutos de ligação; divisão de letras e repetições; comparação palavra por palavra; cache de tradução; migração de módulos; exportação CSV e relatório `.md`. IA sempre falsa nos testes.
- **App (Jest + RNTL):** trilha do dia, cada tipo de exercício, linhas com **+** e somas de minutos, tela do trecho da música, balão de tradução.
- **Manual:** um dia completo na web e no Android, incluindo um lembrete local.

## 11. Ordem de construção sugerida
1. Conteúdo: novos módulos, exercícios dos 46 módulos e validador. É a maior parte do trabalho e pode avançar em paralelo.
2. Exercícios na aula e revisões a partir do banco; migração; áudios pelo Piper.
3. Registros: mídia com **+**, ligações de fora, tempo de ligação.
4. Plano do dia, tela inicial e alertas.
5. Músicas.
6. Tocar para traduzir, palavras novas, exportação; Ensine a IA; baixar relatório.
