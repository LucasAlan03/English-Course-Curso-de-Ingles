import { describeError } from '@/errors';
import { useState } from 'react';
import { StyleSheet, Text, TextInput, View } from 'react-native';

import { useTheme } from '@/theme';
import { AnswerResult, ListeningItem } from '@/types';

import { Button, Card, ErrorText, Muted } from './ui';

type Props = {
  items: ListeningItem[];
  checkAnswer: (itemId: number, answer: string) => Promise<AnswerResult>;
  play: (audioUrl: string) => void;
  onFinish: () => void;
};

export default function ListeningStep({ items, checkAnswer, play, onFinish }: Props) {
  const theme = useTheme();
  const [index, setIndex] = useState(0);
  const [typed, setTyped] = useState('');
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const item = items[index];
  const isLast = index === items.length - 1;

  async function submit(answer: string) {
    if (busy || !answer.trim()) return;
    setBusy(true);
    setError('');
    try {
      setResult(await checkAnswer(item.id, answer));
    } catch (e) {
      setError(describeError(e));
    } finally {
      setBusy(false);
    }
  }

  function next() {
    if (isLast) {
      onFinish();
      return;
    }
    setIndex(index + 1);
    setResult(null);
    setTyped('');
  }

  return (
    <View style={styles.container}>
      <Muted>{`Exercício ${index + 1} de ${items.length}`}</Muted>
      <Button label="Ouvir" kind="secondary" onPress={() => play(item.audio_url)} />
      <Card>
        <Text style={{ color: theme.text, fontSize: 18 }}>{item.prompt}</Text>
      </Card>

      {!result && item.kind === 'choice'
        ? item.options?.map((option) => (
            <Button key={option} label={option} kind="secondary" disabled={busy} onPress={() => submit(option)} />
          ))
        : null}

      {!result && item.kind === 'gap' ? (
        <>
          <TextInput
            value={typed}
            onChangeText={setTyped}
            placeholder="Digite a palavra"
            placeholderTextColor={theme.muted}
            autoCapitalize="none"
            autoCorrect={false}
            style={[styles.input, { color: theme.text, borderColor: theme.border, backgroundColor: theme.card }]}
          />
          <Button label="Verificar" disabled={busy || !typed.trim()} onPress={() => submit(typed)} />
        </>
      ) : null}

      {error ? <ErrorText>{error}</ErrorText> : null}

      {result ? (
        <>
          <Card>
            <Text style={{ color: result.correct ? theme.good : theme.bad, fontWeight: '700', fontSize: 16 }}>
              {result.correct ? 'Correto!' : `Resposta certa: ${result.correct_answer}`}
            </Text>
            <Text style={{ color: theme.text }}>{result.explanation}</Text>
          </Card>
          <Button label={isLast ? 'Ir para a conversa' : 'Próximo'} onPress={next} />
        </>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 12 },
  input: { borderWidth: 1, borderRadius: 12, padding: 14, fontSize: 18 },
});
