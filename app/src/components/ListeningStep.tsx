import { describeError } from '@/errors';
import { useState } from 'react';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';

import { fonts, useTheme } from '@/theme';
import { AnswerResult, ListeningItem } from '@/types';

import { Button, Card, ErrorText, Text } from './ui';

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
      <View style={styles.counterRow}>
        <View style={[styles.track, { backgroundColor: theme.border }]}>
          <View
            style={{
              width: `${((index + (result ? 1 : 0)) / items.length) * 100}%`,
              height: '100%',
              backgroundColor: theme.good,
              borderRadius: 4,
            }}
          />
        </View>
        <Text style={{ color: theme.muted, fontSize: 14, fontWeight: '600' }}>{`Exercício ${index + 1} de ${items.length}`}</Text>
      </View>

      <Pressable
        accessibilityRole="button"
        accessibilityLabel="Ouvir"
        onPress={() => play(item.audio_url)}
        style={({ pressed }) => [styles.listen, { backgroundColor: theme.pine, opacity: pressed ? 0.85 : 1 }]}
      >
        <View style={[styles.playDisc, { backgroundColor: theme.sun }]}>
          <Text style={{ color: theme.onSun, fontSize: 18, marginLeft: 3 }}>▶</Text>
        </View>
        <Text style={{ color: theme.onPine, fontWeight: '700', fontSize: 17 }}>Ouvir</Text>
      </Pressable>

      <Text style={{ color: theme.text, fontSize: 23, fontWeight: '700', lineHeight: 30, letterSpacing: -0.3 }}>{item.prompt}</Text>

      {!result && item.kind === 'choice'
        ? item.options?.map((option) => (
            <Pressable
              key={option}
              accessibilityRole="button"
              disabled={busy}
              onPress={() => submit(option)}
              style={({ pressed }) => [
                styles.option,
                {
                  backgroundColor: theme.card,
                  borderColor: theme.border,
                  borderBottomWidth: pressed ? 2 : 4,
                  marginTop: pressed ? 2 : 0,
                  marginBottom: pressed ? 2 : 0,
                },
                busy && { opacity: 0.5 },
              ]}
            >
              <Text style={{ color: theme.text, fontSize: 17, fontWeight: '500' }}>{option}</Text>
            </Pressable>
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
            style={[
              styles.input,
              { color: theme.text, borderColor: theme.border, backgroundColor: theme.card, fontFamily: fonts[500] },
            ]}
          />
          <Button label="Verificar" disabled={busy || !typed.trim()} onPress={() => submit(typed)} />
        </>
      ) : null}

      {error ? <ErrorText>{error}</ErrorText> : null}

      {result ? (
        <>
          <Card
            style={{
              backgroundColor: result.correct ? theme.good + '22' : theme.bad + '22',
              borderColor: result.correct ? theme.good : theme.bad,
              padding: 18,
            }}
          >
            <Text style={{ color: result.correct ? theme.good : theme.bad, fontWeight: '800', fontSize: 18 }}>
              {result.correct ? 'Correto!' : `Resposta certa: ${result.correct_answer}`}
            </Text>
            <Text style={{ color: theme.text, fontSize: 16, lineHeight: 23 }}>{result.explanation}</Text>
          </Card>
          <Button label={isLast ? 'Ir para a conversa' : 'Próximo'} onPress={next} />
        </>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 14 },
  counterRow: { gap: 6 },
  track: { height: 8, borderRadius: 4, overflow: 'hidden' },
  listen: { flexDirection: 'row', alignItems: 'center', gap: 14, borderRadius: 20, padding: 14 },
  playDisc: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  option: { borderWidth: 2, borderRadius: 16, paddingVertical: 16, paddingHorizontal: 18 },
  input: { borderWidth: 2, borderRadius: 16, padding: 14, fontSize: 18 },
});
