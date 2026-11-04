import { describeError } from '@/errors';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ScrollView, StyleSheet } from 'react-native';

import { api, audioUrl } from '@/api';
import { playUrl } from '@/audio';
import ListeningStep from '@/components/ListeningStep';
import MarkdownText from '@/components/MarkdownText';
import { Button, Card, ErrorText, Muted, SectionTitle } from '@/components/ui';
import { AnswerResult, ListeningItem, ModuleDetail } from '@/types';
import { useApi } from '@/useApi';

type Step = 'theory' | 'loading' | 'listening';

export default function LessonScreen() {
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
    <ScrollView contentContainerStyle={styles.container}>
      {loadError || error ? <ErrorText>{loadError || error}</ErrorText> : null}

      {module && step === 'theory' ? (
        <>
          <SectionTitle>{module.title}</SectionTitle>
          <Card>
            <MarkdownText text={module.theory_md} />
          </Card>
          <Muted>{`Depois: ${module.scenario.title}, com ${module.scenario.character}.`}</Muted>
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
    </ScrollView>
  );
}

const styles = StyleSheet.create({ container: { padding: 16, gap: 12 } });
