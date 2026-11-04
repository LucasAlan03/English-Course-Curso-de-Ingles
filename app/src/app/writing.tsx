import { describeError } from '@/errors';
import { useEffect, useRef, useState } from 'react';
import { ScrollView, StyleSheet, TextInput } from 'react-native';
import { Text } from '@/components/ui';

import { api } from '@/api';
import { Button, Card, ErrorText, Muted, SectionTitle } from '@/components/ui';
import { useTheme } from '@/theme';
import { WritingFeedback } from '@/types';

export default function WritingScreen() {
  const theme = useTheme();
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [prompt, setPrompt] = useState('');
  const [text, setText] = useState('');
  const [feedback, setFeedback] = useState<WritingFeedback | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    api<{ session_id: number; prompt: string }>('/writing/prompt', { method: 'POST' })
      .then((r) => {
        setSessionId(r.session_id);
        setPrompt(r.prompt);
      })
      .catch((e) => setError(describeError(e)));
  }, []);

  async function submit() {
    setBusy(true);
    setError('');
    try {
      setFeedback(await api<WritingFeedback>('/writing/submit', { method: 'POST', json: { session_id: sessionId, text } }));
    } catch (e) {
      setError(describeError(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <SectionTitle>Escrita</SectionTitle>
      {!prompt && !error ? <Muted>Buscando um tema…</Muted> : null}
      {prompt ? (
        <Card>
          <Text style={{ color: theme.text, fontSize: 17 }}>{prompt}</Text>
        </Card>
      ) : null}
      {error ? <ErrorText>{error}</ErrorText> : null}

      {prompt && !feedback ? (
        <>
          <TextInput
            value={text}
            onChangeText={setText}
            placeholder="Escreva seu texto em inglês"
            placeholderTextColor={theme.muted}
            multiline
            style={[styles.input, { color: theme.text, borderColor: theme.border, backgroundColor: theme.card }]}
          />
          <Button label="Enviar para correção" onPress={submit} disabled={busy || text.trim().length < 10} />
        </>
      ) : null}

      {feedback ? (
        <>
          <Muted>{`Nota ${feedback.score}`}</Muted>
          <SectionTitle>Texto corrigido</SectionTitle>
          <Card>
            <Text style={{ color: theme.text, fontSize: 16 }}>{feedback.corrected_text}</Text>
          </Card>
          <SectionTitle>Versão mais natural</SectionTitle>
          <Card>
            <Text style={{ color: theme.text, fontSize: 16 }}>{feedback.improved_text}</Text>
          </Card>
          <SectionTitle>Erros</SectionTitle>
          {feedback.mistakes.length === 0 ? <Muted>Nenhum erro encontrado. Muito bem!</Muted> : null}
          {feedback.mistakes.map((m, i) => (
            <Card key={i}>
              <Text style={{ color: theme.bad, textDecorationLine: 'line-through' }}>{m.said}</Text>
              <Text style={{ color: theme.good, fontWeight: '600' }}>{m.corrected}</Text>
              <Text style={{ color: theme.text }}>{m.explanation}</Text>
            </Card>
          ))}
        </>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, gap: 12 },
  input: { borderWidth: 1, borderRadius: 12, padding: 14, fontSize: 16, minHeight: 160, textAlignVertical: 'top' },
});
