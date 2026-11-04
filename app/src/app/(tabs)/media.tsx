import { describeError } from '@/errors';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, View } from 'react-native';
import { Text } from '@/components/ui';

import { api } from '@/api';
import MediaForm, { MediaPayload } from '@/components/MediaForm';
import MediaSummary from '@/components/MediaSummary';
import { Button, Card, ErrorText, Muted, SectionTitle } from '@/components/ui';
import { shiftDay, shortDate, todayIso } from '@/dates';
import { CATEGORY_LABELS } from '@/labels';
import { useTheme } from '@/theme';
import { MediaItem, MediaSummary as Summary } from '@/types';
import { useApi } from '@/useApi';

export default function MediaScreen() {
  const theme = useTheme();
  const [date, setDate] = useState(todayIso());
  const [editing, setEditing] = useState<MediaItem | null>(null);
  const [error, setError] = useState('');
  const items = useApi<MediaItem[]>(`/media?date=${date}`);
  const summary = useApi<Summary>(`/media/summary?date=${date}`);

  async function run(action: () => Promise<unknown>) {
    setError('');
    try {
      await action();
      await Promise.all([items.reload(), summary.reload()]);
    } catch (e) {
      setError(describeError(e));
    }
  }

  const save = (payload: MediaPayload) =>
    run(async () => {
      if (editing) {
        await api(`/media/${editing.id}`, { method: 'PUT', json: payload });
        setEditing(null);
      } else {
        await api('/media', { method: 'POST', json: payload });
      }
    });

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.dateRow}>
        <Pressable onPress={() => setDate(shiftDay(date, -1))}>
          <Text style={{ color: theme.primary, fontSize: 18 }}>‹ Anterior</Text>
        </Pressable>
        <Text style={{ color: theme.text, fontWeight: '700', fontSize: 18 }}>
          {date === todayIso() ? `Hoje (${shortDate(date)})` : shortDate(date)}
        </Text>
        <Pressable onPress={() => setDate(shiftDay(date, 1))}>
          <Text style={{ color: theme.primary, fontSize: 18 }}>Próximo ›</Text>
        </Pressable>
      </View>

      {summary.data ? <MediaSummary summary={summary.data} /> : null}
      {error || items.error ? <ErrorText>{error || items.error}</ErrorText> : null}

      <SectionTitle>{editing ? 'Editar registro' : 'Registrar'}</SectionTitle>
      <Card>
        <MediaForm key={editing?.id ?? 'new'} date={date} initial={editing ?? undefined} onSubmit={save} onCancel={editing ? () => setEditing(null) : undefined} />
      </Card>

      <SectionTitle>Registros do dia</SectionTitle>
      {items.data?.length === 0 ? <Muted>Nada registrado neste dia.</Muted> : null}
      {items.data?.map((item) => (
        <Card key={item.id}>
          <Text style={{ color: theme.text, fontWeight: '600', fontSize: 16 }}>{item.title}</Text>
          <Muted>
            {`${item.type === 'watch' ? 'Assistir' : 'Ler'} · ${CATEGORY_LABELS[item.category]}${item.episode ? ` · ${item.episode}` : ''} · ${item.minutes} min`}
          </Muted>
          <View style={styles.actions}>
            <Button label="Editar" kind="secondary" onPress={() => setEditing(item)} />
            <Button label="Excluir" kind="secondary" onPress={() => run(() => api(`/media/${item.id}`, { method: 'DELETE' }))} />
          </View>
        </Card>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, gap: 12 },
  dateRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  actions: { flexDirection: 'row', gap: 8, marginTop: 6 },
});
