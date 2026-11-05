import { describeError } from '@/errors';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { api, audioUrl } from '@/api';
import { playUrl } from '@/audio';
import { shortDate } from '@/dates';
import ExercisePlayer from '@/components/exercises/ExercisePlayer';
import LessonBar from '@/components/LessonBar';
import MarkdownText from '@/components/MarkdownText';
import { Button, Card, ErrorText, Muted, Screen, Text } from '@/components/ui';
import { useTheme } from '@/theme';
import { AnswerResult, Exercise, ModuleDetail } from '@/types';
import { useApi } from '@/useApi';

type Step = 'theory' | 'loading' | 'exercises' | 'result';

export default function LessonScreen() {
  const theme = useTheme();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: module, error: loadError } = useApi<ModuleDetail>(`/modules/${id}`);
  const [step, setStep] = useState<Step>('theory');
  const [items, setItems] = useState<Exercise[]>([]);
  const [outcome, setOutcome] = useState<AnswerResult | null>(null);
  const [error, setError] = useState('');

  async function start() {
    setStep('loading');
    setError('');
    try {
      const exercises = await api<Exercise[]>(`/modules/${id}/exercises`);
      setItems(exercises);
      setStep(exercises.length && exercises.every((e) => e.answered) ? 'result' : 'exercises');
    } catch (e) {
      setError(describeError(e));
      setStep('theory');
    }
  }

  async function submit(item: Exercise, answer: string, seconds: number) {
    const result = await api<AnswerResult>(`/exercises/${id}/${item.id}/answer`, {
      method: 'POST', json: { answer, seconds },
    });
    if (result.module_completed) setOutcome(result);
    return result;
  }

  function report(item: Exercise) {
    api(`/exercises/${id}/${item.id}/report`, { method: 'POST', json: { note: '' } }).catch(() => undefined);
  }

  const answered = items.filter((i) => i.result);
  const savedScore = answered.length ? Math.round((100 * answered.filter((i) => i.result?.correct).length) / answered.length) : null;
  const score = outcome?.score ?? savedScore;

  return (
    <View style={styles.page}>
      <LessonBar stage={step === 'result' ? 'result' : step === 'exercises' ? 'exercises' : 'theory'} />
      <Screen gap={14}>
        {loadError || error ? <ErrorText>{loadError || error}</ErrorText> : null}

        {module && step === 'theory' ? (
          <>
            <View style={[styles.chip, { backgroundColor: theme.tint }]}>
              <Text style={{ color: theme.text, fontWeight: '700', fontSize: 13 }}>{`Nível ${module.level}`}</Text>
            </View>
            <Text accessibilityRole="header" style={{ color: theme.text, fontSize: 32, fontWeight: '800', letterSpacing: -1, lineHeight: 36 }}>
              {module.title}
            </Text>
            <Card style={{ padding: 20 }}>
              <MarkdownText text={module.theory_md} skipFirstHeading />
            </Card>
            <Muted>27 exercícios em 3 blocos: reconhecer, praticar e produzir. Seu progresso fica salvo.</Muted>
            <Button label="Começar exercícios" onPress={start} />
            <Button label="Pular teoria" kind="secondary" onPress={start} />
          </>
        ) : null}

        {step === 'loading' ? <Muted>Carregando os exercícios…</Muted> : null}

        {step === 'exercises' ? (
          <ExercisePlayer
            items={items}
            submit={submit}
            play={(url) => {
              playUrl(audioUrl(url));
            }}
            onReport={report}
            onDone={() => setStep('result')}
          />
        ) : null}

        {step === 'result' ? (
          <Card style={{ padding: 22, gap: 10, alignItems: 'center' }}>
            <Text style={{ color: theme.muted, fontSize: 15, fontWeight: '700' }}>Módulo concluído</Text>
            {score !== null ? <Text style={{ color: theme.text, fontSize: 44, fontWeight: '800' }}>{`${score}%`}</Text> : null}
            {outcome?.next_due ? <Muted>{`Próxima revisão: ${shortDate(outcome.next_due)}`}</Muted> : null}
            <Button label="Voltar para o dia" onPress={() => router.replace('/')} />
          </Card>
        ) : null}
      </Screen>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1 },
  chip: { alignSelf: 'flex-start', borderRadius: 999, paddingVertical: 4, paddingHorizontal: 12 },
});
