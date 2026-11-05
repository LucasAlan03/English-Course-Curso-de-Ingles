import { describeError } from '@/errors';
import { router, useLocalSearchParams } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import { View } from 'react-native';

import { api } from '@/api';
import ExamResult from '@/components/ExamResult';
import ExercisePlayer from '@/components/exercises/ExercisePlayer';
import LessonBar from '@/components/LessonBar';
import { ErrorText, Muted, Screen } from '@/components/ui';
import { Exercise, ExamRun } from '@/types';

type Question = Omit<Exercise, 'block' | 'audio_url' | 'result'>;
type Started = { run_id: number; level: string; questions: Question[] };

export default function ExamScreen() {
  const { level } = useLocalSearchParams<{ level: string }>();
  const [started, setStarted] = useState<Started | null>(null);
  const [run, setRun] = useState<ExamRun | null>(null);
  const [error, setError] = useState('');
  const once = useRef(false);

  const start = useCallback(async () => {
    setError('');
    setRun(null);
    setStarted(null);
    try {
      setStarted(await api<Started>(`/exams/${level}/start`, { method: 'POST' }));
    } catch (e) {
      setError(describeError(e));
    }
  }, [level]);

  useEffect(() => {
    if (once.current) return;
    once.current = true;
    start();
  }, [start]);

  async function submit(item: Exercise, answer: string, seconds: number) {
    await api(`/exams/runs/${started!.run_id}/${item.id}/answer`, { method: 'POST', json: { answer, seconds } });
    return null;
  }

  async function finish() {
    try {
      setRun(await api<ExamRun>(`/exams/runs/${started!.run_id}`));
    } catch (e) {
      setError(describeError(e));
    }
  }

  const items: Exercise[] = (started?.questions ?? []).map((q) => ({ ...q, block: 1, audio_url: null, result: null }));

  return (
    <View style={{ flex: 1 }}>
      <LessonBar stage={run ? 'result' : 'exercises'} title={`Prova ${level}`} />
      <Screen gap={14}>
        {error ? <ErrorText>{error}</ErrorText> : null}
        {!started && !error ? <Muted>Preparando a prova…</Muted> : null}
        {started && !run ? (
          <ExercisePlayer
            key={started.run_id}
            items={items}
            title={`Prova ${level}`}
            instantFeedback={false}
            submit={submit}
            play={() => undefined}
            onDone={finish}
          />
        ) : null}
        {run ? <ExamResult run={run} onRetry={start} onBack={() => router.replace('/tracks')} /> : null}
      </Screen>
    </View>
  );
}
