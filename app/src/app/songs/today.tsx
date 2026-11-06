import { describeError } from '@/errors';
import { router } from 'expo-router';
import { useState } from 'react';
import { Linking, StyleSheet, TextInput, View } from 'react-native';

import { api } from '@/api';
import { Recording, appendAudio } from '@/audio';
import PushToTalk from '@/components/PushToTalk';
import TranslatableText from '@/components/TranslatableText';
import { Button, Card, ErrorText, Muted, Screen, SectionTitle, Text } from '@/components/ui';
import WordDiff from '@/components/WordDiff';
import { useTheme } from '@/theme';
import { DiffResult, SongChunk, SongToday } from '@/types';
import { useApi } from '@/useApi';

/** The chunk's lines with the grammar phrases underlined. */
function ChunkText({ chunk }: { chunk: SongChunk }) {
  const theme = useTheme();
  const phrases = chunk.highlights.map((h) => h.phrase.toLowerCase());
  return (
    <View style={{ gap: 4 }}>
      {chunk.text.split('\n').map((line, i) => {
        const hit = phrases.find((p) => line.toLowerCase().includes(p));
        if (!hit) return <TranslatableText key={i} text={line} style={{ color: theme.text, fontSize: 19, lineHeight: 27 }} />;
        const at = line.toLowerCase().indexOf(hit);
        return (
          <Text key={i} style={{ color: theme.text, fontSize: 19, lineHeight: 27 }}>
            {line.slice(0, at)}
            <Text style={{ color: theme.primary, fontSize: 19, fontWeight: '700', textDecorationLine: 'underline' }}>
              {line.slice(at, at + hit.length)}
            </Text>
            {line.slice(at + hit.length)}
          </Text>
        );
      })}
      {chunk.module_titles.length ? (
        <View style={styles.chips}>
          {chunk.module_titles.map((t) => (
            <View key={t} style={[styles.chip, { backgroundColor: theme.tint }]}>
              <Text style={{ color: theme.text, fontSize: 13, fontWeight: '700' }}>{t}</Text>
            </View>
          ))}
        </View>
      ) : null}
    </View>
  );
}

export default function SongTodayScreen() {
  const theme = useTheme();
  const today = useApi<SongToday>('/songs/current/today');
  const [typed, setTyped] = useState('');
  const [diff, setDiff] = useState<DiffResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const data = today.data;

  async function call(action: () => Promise<DiffResult>) {
    setBusy(true);
    setError('');
    try {
      setDiff(await action());
    } catch (e) {
      setError(describeError(e));
    } finally {
      setBusy(false);
    }
  }

  const sendDictation = () =>
    call(() => api<DiffResult>(`/songs/chunks/${data!.chunk!.id}/dictation`, { method: 'POST', json: { text: typed } }));

  async function sendRecording(path: string, recording: Recording) {
    await call(async () => {
      const form = new FormData();
      await appendAudio(form, recording);
      return api<DiffResult>(path, { method: 'POST', body: form });
    });
  }

  function next() {
    setDiff(null);
    setTyped('');
    today.reload();
  }

  if (!data) return <Screen>{today.error ? <ErrorText>{today.error}</ErrorText> : <Muted>Carregando…</Muted>}</Screen>;

  if (data.stage === 'no_song' || !data.song) {
    return (
      <Screen gap={14}>
        <SectionTitle>Música do dia</SectionTitle>
        <Muted>Cadastre uma música que você ama. O app divide a letra em trechos e você aprende um por dia, até cantar inteira.</Muted>
        <Button label="Cadastrar música" onPress={() => router.push('/songs/new')} />
      </Screen>
    );
  }

  const song = data.song;
  return (
    <Screen gap={14}>
      <Text accessibilityRole="header" style={{ color: theme.text, fontSize: 24, fontWeight: '800' }}>
        {`${song.title} · ${data.progress.done}/${data.progress.total} trechos`}
      </Text>
      <Muted>{song.artist}</Muted>
      {song.link ? <Button label="Abrir música" kind="secondary" onPress={() => Linking.openURL(song.link!)} /> : null}
      {error ? <ErrorText>{error}</ErrorText> : null}

      {data.review_chunks.length ? (
        <Card>
          <Muted>Revisão rápida do refrão</Muted>
          {data.review_chunks.map((c) => <ChunkText key={c.id} chunk={c} />)}
        </Card>
      ) : null}

      {data.stage === 'dictation' && data.chunk ? (
        <Card style={{ gap: 10 }}>
          <Text style={{ color: theme.text, fontSize: 18, fontWeight: '800' }}>{`Trecho ${data.chunk.idx + 1} · Ditado`}</Text>
          <Muted>Ouça o trecho na música e escreva o que entendeu. Pode voltar e ouvir de novo.</Muted>
          {diff ? (
            <>
              <Text style={{ color: theme.text, fontSize: 18, fontWeight: '700' }}>{`${diff.score}% das palavras`}</Text>
              <WordDiff tokens={diff.tokens} />
              <Button label="Ir para o shadowing" onPress={next} />
            </>
          ) : (
            <>
              <TextInput value={typed} onChangeText={setTyped} multiline placeholder="Escreva o que você ouviu"
                placeholderTextColor={theme.muted} autoCapitalize="none"
                style={[styles.input, { color: theme.text, borderColor: theme.border, backgroundColor: theme.card }]} />
              <Button label="Comparar" disabled={busy || !typed.trim()} onPress={sendDictation} />
            </>
          )}
        </Card>
      ) : null}

      {data.stage === 'shadow' && data.chunk ? (
        <Card style={{ gap: 10 }}>
          <Text style={{ color: theme.text, fontSize: 18, fontWeight: '800' }}>{`Trecho ${data.chunk.idx + 1} · Shadowing`}</Text>
          <ChunkText chunk={data.chunk} />
          <Muted>Cante ou fale junto com a música e grave.</Muted>
          {diff ? (
            <>
              <Text style={{ color: theme.text, fontSize: 18, fontWeight: '700' }}>{`${diff.score}% das palavras`}</Text>
              <WordDiff tokens={diff.tokens} />
              <Button label="Concluir trecho" onPress={next} />
            </>
          ) : (
            <PushToTalk disabled={busy} onRecorded={(r) => sendRecording(`/songs/chunks/${data.chunk!.id}/shadow`, r)} />
          )}
        </Card>
      ) : null}

      {data.stage === 'done_today' ? (
        <Card>
          <Text style={{ color: theme.good, fontSize: 18, fontWeight: '800' }}>Trecho de hoje feito! 🎵</Text>
          <Muted>Amanhã vem o próximo. Ouça a música inteira quando quiser.</Muted>
        </Card>
      ) : null}

      {data.stage === 'final' ? (
        <Card style={{ gap: 10 }}>
          <Text style={{ color: theme.text, fontSize: 18, fontWeight: '800' }}>Desafio final</Text>
          <Muted>Você passou por todos os trechos. Grave a música inteira (ou o maior pedaço que conseguir).</Muted>
          {diff ? (
            <>
              <Text style={{ color: theme.text, fontSize: 18, fontWeight: '700' }}>{`${diff.score}% das palavras`}</Text>
              <WordDiff tokens={diff.tokens} />
              <Button label="Concluir" onPress={next} />
            </>
          ) : (
            <PushToTalk disabled={busy} onRecorded={(r) => sendRecording(`/songs/${song.id}/final`, r)} />
          )}
        </Card>
      ) : null}

      {data.stage === 'finished' ? (
        <Card style={{ gap: 10 }}>
          <Text style={{ color: theme.good, fontSize: 18, fontWeight: '800' }}>Música concluída! 🎤</Text>
          <Muted>Escolha a próxima música do momento.</Muted>
          <Button label="Minhas músicas" onPress={() => router.push('/songs')} />
        </Card>
      ) : null}

      <Button label="Minhas músicas" kind="secondary" onPress={() => router.push('/songs')} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  input: { borderWidth: 2, borderRadius: 16, padding: 14, fontSize: 17, minHeight: 90 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 4 },
  chip: { borderRadius: 999, paddingVertical: 3, paddingHorizontal: 10 },
});
