import { describeError } from '@/errors';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { api, audioUrl } from '@/api';
import { playUrl } from '@/audio';
import LessonBar from '@/components/LessonBar';
import ListeningStep from '@/components/ListeningStep';
import MarkdownText from '@/components/MarkdownText';
import { Button, Card, ErrorText, Muted, Screen, Text } from '@/components/ui';
import { useTheme } from '@/theme';
import { AnswerResult, ListeningItem, ModuleDetail } from '@/types';
import { useApi } from '@/useApi';

type Step = 'theory' | 'loading' | 'listening';

export default function LessonScreen() {
  const theme = useTheme();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: module, error: loadError } = useApi<ModuleDetail>(`/modules/${id}`);
  const [step, setStep] = useState<Step>('theory');
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [items, setItems] = useState<ListeningItem[]>([]);
  const [error, setError] = useState('');

  async function startListening() {
    setStep('loading');
    setError('');
    try {
      const session = await api<{ id: number }>('/sessions', { method: 'POST', json: { kind: 'lesson', module_id: id } });
      const exercises = await api<ListeningItem[]>(`/sessions/${session.id}/listening`);
      setSessionId(session.id);
      setItems(exercises);
      setStep('listening');
    } catch (e) {
      setError(describeError(e));
      setStep('theory');
    }
  }

  const checkAnswer = (itemId: number, answer: string) =>
    api<AnswerResult>(`/listening/${itemId}/answer`, { method: 'POST', json: { answer } });

  return (
    <View style={styles.page}>
      <LessonBar stage={step === 'listening' ? 'listening' : 'theory'} />
      <Screen gap={14}>
        {loadError || error ? <ErrorText>{loadError || error}</ErrorText> : null}

        {module && step === 'theory' ? (
          <>
            <View style={[styles.chip, { backgroundColor: theme.tint }]}>
              <Text style={{ color: theme.text, fontWeight: '700', fontSize: 13 }}>
                {`Nível ${module.level}`}
              </Text>
            </View>
            <Text accessibilityRole="header" style={{ color: theme.text, fontSize: 32, fontWeight: '800', letterSpacing: -1, lineHeight: 36 }}>
              {module.title}
            </Text>
            <Card style={{ padding: 20 }}>
              <MarkdownText text={module.theory_md} skipFirstHeading />
            </Card>
            <View style={[styles.next, { backgroundColor: theme.pine }]}>
              <Text style={{ color: theme.onPine, opacity: 0.75, fontSize: 14 }}>Depois da teoria</Text>
              <Text style={{ color: theme.onPine, fontWeight: '800', fontSize: 18 }}>{module.scenario.title}</Text>
              <Text style={{ color: theme.sun, fontSize: 14, fontWeight: '600' }}>{`com ${module.scenario.character}`}</Text>
            </View>
            <Button label="Continuar" onPress={startListening} />
            <Button label="Pular teoria" kind="secondary" onPress={startListening} />
          </>
        ) : null}

        {step === 'loading' ? <Muted>Gerando os exercícios de listening…</Muted> : null}

        {step === 'listening' && sessionId !== null ? (
          <ListeningStep
            items={items}
            checkAnswer={checkAnswer}
            play={(url) => {
              playUrl(audioUrl(url));
            }}
            onFinish={() => router.replace(`/chat/${sessionId}`)}
          />
        ) : null}
      </Screen>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1 },
  chip: { alignSelf: 'flex-start', borderRadius: 999, paddingVertical: 4, paddingHorizontal: 12 },
  next: { borderRadius: 20, padding: 18, gap: 3 },
});
