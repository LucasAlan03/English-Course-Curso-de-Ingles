import { describeError } from '@/errors';
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { View } from 'react-native';

import { api, audioUrl } from '@/api';
import { playUrl } from '@/audio';
import { shortDate } from '@/dates';
import ExercisePlayer from '@/components/exercises/ExercisePlayer';
import LessonBar from '@/components/LessonBar';
import { Button, Card, ErrorText, Muted, Screen, Text } from '@/components/ui';
import { useTheme } from '@/theme';
import { AnswerResult, Exercise } from '@/types';

export default function ReviewScreen() {
  const theme = useTheme();
  const { id } = useLocalSearchParams<{ id: string }>();
  const [run, setRun] = useState<{ run_id: number; exercises: Exercise[] } | null>(null);
  const [outcome, setOutcome] = useState<AnswerResult | null>(null);
  const [finished, setFinished] = useState(false);
  const [error, setError] = useState('');
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    api<{ run_id: number; exercises: Exercise[] }>(`/reviews/${id}/start`, { method: 'POST' })
      .then(setRun)
      .catch((e) => setError(describeError(e)));
  }, [id]);

  async function submit(item: Exercise, answer: string, seconds: number) {
    const result = await api<AnswerResult>(`/exercises/${id}/${item.id}/answer`, {
      method: 'POST', json: { answer, seconds, run_id: run!.run_id },
    });
    if (result.module_completed) setOutcome(result);
    return result;
  }

  return (
    <View style={{ flex: 1 }}>
      <LessonBar stage={finished ? 'result' : 'exercises'} title="Revisão" />
      <Screen gap={14}>
        {error ? <ErrorText>{error}</ErrorText> : null}
        {!run && !error ? <Muted>Preparando a revisão…</Muted> : null}
        {run && !finished ? (
          <ExercisePlayer
            items={run.exercises}
            title="Revisão"
            submit={submit}
            play={(url) => {
              playUrl(audioUrl(url));
            }}
            onDone={() => setFinished(true)}
          />
        ) : null}
        {finished ? (
          <Card style={{ padding: 22, gap: 10, alignItems: 'center' }}>
            <Text style={{ color: theme.muted, fontSize: 15, fontWeight: '700' }}>Revisão concluída</Text>
            {outcome?.score != null ? <Text style={{ color: theme.text, fontSize: 44, fontWeight: '800' }}>{`${outcome.score}%`}</Text> : null}
            {outcome?.next_due ? <Muted>{`Próxima revisão: ${shortDate(outcome.next_due)}`}</Muted> : null}
            <Button label="Voltar para o dia" onPress={() => router.replace('/')} />
          </Card>
        ) : null}
      </Screen>
    </View>
  );
}
