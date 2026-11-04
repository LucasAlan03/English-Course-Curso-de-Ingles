import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ScrollView, StyleSheet } from 'react-native';

import { api, audioUrl } from '@/api';
import { playUrl } from '@/audio';
import ListeningStep from '@/components/ListeningStep';
import { ErrorText, Muted, SectionTitle } from '@/components/ui';
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
        setError((e as { detail?: string }).detail ?? String(e));
      }
    })();
  }, [id]);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <SectionTitle>Revisão</SectionTitle>
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
    </ScrollView>
  );
}

const styles = StyleSheet.create({ container: { padding: 16, gap: 12 } });
