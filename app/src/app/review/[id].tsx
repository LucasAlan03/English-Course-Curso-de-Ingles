import { describeError } from '@/errors';
import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { View } from 'react-native';

import { api, audioUrl } from '@/api';
import { playUrl } from '@/audio';
import LessonBar from '@/components/LessonBar';
import ListeningStep from '@/components/ListeningStep';
import { ErrorText, Muted, Screen } from '@/components/ui';
import { AnswerResult, ListeningItem } from '@/types';

export default function ReviewScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [items, setItems] = useState<ListeningItem[]>([]);
  const [error, setError] = useState('');
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    (async () => {
      try {
        const session = await api<{ id: number }>('/sessions', { method: 'POST', json: { kind: 'review', module_id: id } });
        setItems(await api<ListeningItem[]>(`/sessions/${session.id}/listening`));
        setSessionId(session.id);
      } catch (e) {
        setError(describeError(e));
      }
    })();
  }, [id]);

  return (
    <View style={{ flex: 1 }}>
      <LessonBar stage="listening" title="Revisão" />
      <Screen>
      {error ? <ErrorText>{error}</ErrorText> : null}
      {!sessionId && !error ? <Muted>Preparando a revisão…</Muted> : null}
      {sessionId !== null ? (
        <ListeningStep
          items={items}
          checkAnswer={(itemId, answer) =>
            api<AnswerResult>(`/listening/${itemId}/answer`, { method: 'POST', json: { answer } })
          }
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
