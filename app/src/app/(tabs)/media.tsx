import { describeError } from '@/errors';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, TextInput, View } from 'react-native';

import { api } from '@/api';
import MediaForm, { MediaPayload } from '@/components/MediaForm';
import MediaSummary from '@/components/MediaSummary';
import { Button, Card, ErrorText, Muted, SectionTitle, Text } from '@/components/ui';
import { shiftDay, shortDate, todayIso } from '@/dates';
import { CATEGORY_LABELS } from '@/labels';
import { useTheme } from '@/theme';
import { CallsDay, MediaItem, MediaSummary as Summary } from '@/types';
import { useApi } from '@/useApi';

function payloadOf(item: MediaItem): MediaPayload {
  const { id: _id, ...rest } = item;
  return rest;
}

export default function MediaScreen() {
  const theme = useTheme();
  const [date, setDate] = useState(todayIso());
  const [adding, setAdding] = useState<string | null>(null);
  const [editing, setEditing] = useState<MediaItem | null>(null);
  const [callForm, setCallForm] = useState(false);
  const [source, setSource] = useState('');
  const [callMinutes, setCallMinutes] = useState('');
  const [error, setError] = useState('');
  const items = useApi<MediaItem[]>(`/media?date=${date}`);
  const summary = useApi<Summary>(`/media/summary?date=${date}`);
  const calls = useApi<CallsDay>(`/calls?date=${date}`);

  async function run(action: () => Promise<unknown>) {
    setError('');
    try {
      await action();
      await Promise.all([items.reload(), summary.reload(), calls.reload()]);
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
        setAdding(null);
      }
    });

  const changeEpisodes = (item: MediaItem, delta: number) => {
    const count = Math.max(1, Math.min(100, (item.count ?? 1) + delta));
    if (count === item.count) return;
    run(() => api(`/media/${item.id}`, { method: 'PUT', json: { ...payloadOf(item), count } }));
  };

  async function saveCall() {
    const mins = /^\d+$/.test(callMinutes.trim()) ? Number(callMinutes.trim()) : NaN;
    if (!source.trim() || !(mins >= 1 && mins <= 600)) {
      setError('Informe onde foi a ligação e os minutos (1 a 600).');
      return;
    }
    await run(() => api('/calls/external', { method: 'POST', json: { date, source: source.trim(), minutes: mins } }));
    setSource('');
    setCallMinutes('');
    setCallForm(false);
  }

  function form(category: string) {
    if (editing && editing.category === category) {
      return <MediaForm key={editing.id} date={date} initial={editing} onSubmit={save} onCancel={() => setEditing(null)} />;
    }
    return null;
  }

  function list(type: 'watch' | 'read') {
    return (items.data ?? []).filter((i) => i.type === type).map((item) => (
      <Card key={item.id}>
        <Text style={{ color: theme.text, fontWeight: '600', fontSize: 16 }}>{item.title}</Text>
        {item.unit_minutes && item.count ? (
          <View style={styles.stepper}>
            <Pressable accessibilityRole="button" accessibilityLabel={`Menos um episódio de ${item.title}`} onPress={() => changeEpisodes(item, -1)}
              style={[styles.step, { borderColor: theme.border }]}>
              <Text style={{ color: theme.text, fontSize: 18, fontWeight: '800' }}>−</Text>
            </Pressable>
            <Muted>{`${item.count} × ${item.unit_minutes} = ${item.minutes} min`}</Muted>
            <Pressable accessibilityRole="button" accessibilityLabel={`Mais um episódio de ${item.title}`} onPress={() => changeEpisodes(item, 1)}
              style={[styles.step, { borderColor: theme.border }]}>
              <Text style={{ color: theme.text, fontSize: 18, fontWeight: '800' }}>+</Text>
            </Pressable>
          </View>
        ) : (
          <Muted>{`${CATEGORY_LABELS[item.category] ?? item.category} · ${item.minutes} min${item.pages ? ` · ${item.pages} pág.` : ''}`}</Muted>
        )}
        {item.new_words ? <Muted>{`Palavras novas: ${item.new_words}`}</Muted> : null}
        {editing?.id === item.id ? form(item.category) : (
          <View style={styles.actions}>
            <Button label="Editar" kind="secondary" onPress={() => { setAdding(null); setEditing(item); }} />
            <Button label="Excluir" kind="secondary" onPress={() => run(() => api(`/media/${item.id}`, { method: 'DELETE' }))} />
          </View>
        )}
      </Card>
    ));
  }

  const addButton = (category: string, label: string) =>
    adding === category ? (
      <Card key={category}>
        <MediaForm key={`new-${category}`} date={date} category={category} onSubmit={save} onCancel={() => setAdding(null)} />
      </Card>
    ) : (
      <Button key={category} label={label} kind="secondary" onPress={() => { setEditing(null); setAdding(category); }} />
    );

  const day = summary.data?.day.by_type ?? {};

  return (
    <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
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

      <SectionTitle>{`Assistir · ${day.watch ?? 0}/45 min`}</SectionTitle>
      {list('watch')}
      {addButton('series', '+ outra série')}
      {addButton('video', '+ outro vídeo')}

      <SectionTitle>{`Ler · ${day.read ?? 0}/40 min`}</SectionTitle>
      {list('read')}
      {addButton('hq', '+ outra leitura')}

      <SectionTitle>Ligações</SectionTitle>
      <Muted>{`Ligações hoje: ${calls.data?.total_minutes ?? 0} min`}</Muted>
      {(calls.data?.external ?? []).map((c) => (
        <Card key={c.id}>
          <Text style={{ color: theme.text, fontWeight: '600', fontSize: 16 }}>{`${c.source} · ${c.minutes} min`}</Text>
          <Button label="Excluir" kind="secondary" onPress={() => run(() => api(`/calls/external/${c.id}`, { method: 'DELETE' }))} />
        </Card>
      ))}
      {callForm ? (
        <Card>
          <TextInput value={source} onChangeText={setSource} placeholder="Onde (ex.: Be Confident)" placeholderTextColor={theme.muted}
            style={[styles.input, { color: theme.text, borderColor: theme.border }]} />
          <TextInput value={callMinutes} onChangeText={setCallMinutes} placeholder="Minutos da ligação" placeholderTextColor={theme.muted}
            keyboardType="number-pad" style={[styles.input, { color: theme.text, borderColor: theme.border }]} />
          <Button label="Salvar ligação" onPress={saveCall} />
          <Button label="Cancelar" kind="secondary" onPress={() => setCallForm(false)} />
        </Card>
      ) : (
        <Button label="+ lançar ligação" kind="secondary" onPress={() => setCallForm(true)} />
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, gap: 12, width: '100%', maxWidth: 640, alignSelf: 'center' },
  dateRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  actions: { flexDirection: 'row', gap: 8, marginTop: 6 },
  stepper: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  step: { width: 34, height: 34, borderRadius: 17, borderWidth: 2, alignItems: 'center', justifyContent: 'center' },
  input: { borderWidth: 1, borderRadius: 12, padding: 12, fontSize: 16 },
});
