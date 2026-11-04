import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';

import { CATEGORY_LABELS, READ_CATEGORIES, WATCH_CATEGORIES } from '@/labels';
import { useTheme } from '@/theme';
import { MediaItem } from '@/types';

import { Button, ErrorText } from './ui';

export type MediaPayload = Omit<MediaItem, 'id'>;

type Props = {
  date: string;
  initial?: MediaItem;
  onSubmit: (payload: MediaPayload) => void | Promise<void>;
  onCancel?: () => void;
};

export default function MediaForm({ date, initial, onSubmit, onCancel }: Props) {
  const theme = useTheme();
  const [type, setType] = useState<'watch' | 'read'>(initial?.type ?? 'watch');
  const [category, setCategory] = useState(initial?.category ?? 'series');
  const [title, setTitle] = useState(initial?.title ?? '');
  const [episode, setEpisode] = useState(initial?.episode ?? '');
  const [minutes, setMinutes] = useState(initial ? String(initial.minutes) : '');
  const [pages, setPages] = useState(initial?.pages ? String(initial.pages) : '');
  const [error, setError] = useState('');

  function chooseType(next: 'watch' | 'read') {
    setType(next);
    setCategory(next === 'watch' ? 'series' : 'hq');
  }

  async function save() {
    const cleanTitle = title.trim();
    const mins = /^\d+$/.test(minutes.trim()) ? Number(minutes.trim()) : NaN;
    if (!cleanTitle) return setError('Informe o título.');
    if (!(mins >= 1 && mins <= 1440)) return setError('Informe os minutos (de 1 a 1440).');
    const pageCount = type === 'read' && /^\d+$/.test(pages.trim()) && Number(pages) > 0 ? Number(pages) : null;
    setError('');
    await onSubmit({
      date,
      type,
      category,
      title: cleanTitle,
      episode: type === 'watch' && episode.trim() ? episode.trim() : null,
      minutes: mins,
      pages: pageCount,
    });
    if (!initial) {
      setTitle('');
      setEpisode('');
      setMinutes('');
      setPages('');
    }
  }

  const categories = type === 'watch' ? WATCH_CATEGORIES : READ_CATEGORIES;
  const inputStyle = [styles.input, { color: theme.text, borderColor: theme.border, backgroundColor: theme.card }];

  return (
    <View style={styles.container}>
      <View style={styles.row}>
        {(['watch', 'read'] as const).map((t) => (
          <Pressable
            key={t}
            onPress={() => chooseType(t)}
            style={[styles.chip, { borderColor: type === t ? theme.primary : theme.border }]}
          >
            <Text style={{ color: type === t ? theme.primary : theme.text, fontWeight: '600' }}>
              {t === 'watch' ? 'Assistir' : 'Ler'}
            </Text>
          </Pressable>
        ))}
      </View>
      <View style={styles.row}>
        {categories.map((c) => (
          <Pressable
            key={c}
            onPress={() => setCategory(c)}
            style={[styles.chip, { borderColor: category === c ? theme.primary : theme.border }]}
          >
            <Text style={{ color: category === c ? theme.primary : theme.text }}>{CATEGORY_LABELS[c]}</Text>
          </Pressable>
        ))}
      </View>
      <TextInput value={title} onChangeText={setTitle} placeholder="Título" placeholderTextColor={theme.muted} style={inputStyle} />
      {type === 'watch' ? (
        <TextInput
          value={episode}
          onChangeText={setEpisode}
          placeholder="Episódio (opcional)"
          placeholderTextColor={theme.muted}
          style={inputStyle}
        />
      ) : (
        <TextInput
          value={pages}
          onChangeText={setPages}
          placeholder="Páginas (opcional)"
          placeholderTextColor={theme.muted}
          keyboardType="number-pad"
          style={inputStyle}
        />
      )}
      <TextInput
        value={minutes}
        onChangeText={setMinutes}
        placeholder="Minutos"
        placeholderTextColor={theme.muted}
        keyboardType="number-pad"
        style={inputStyle}
      />
      {error ? <ErrorText>{error}</ErrorText> : null}
      <Button label="Salvar" onPress={save} />
      {onCancel ? <Button label="Cancelar" kind="secondary" onPress={onCancel} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 10 },
  row: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { borderWidth: 1.5, borderRadius: 999, paddingVertical: 8, paddingHorizontal: 14 },
  input: { borderWidth: 1, borderRadius: 12, padding: 12, fontSize: 16 },
});
