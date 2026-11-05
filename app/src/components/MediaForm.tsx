import { useState } from 'react';
import { Pressable, StyleSheet, TextInput, View } from 'react-native';

import { api } from '@/api';
import { Text } from '@/components/ui';
import { CATEGORY_LABELS, READ_CATEGORIES, WATCH_CATEGORIES } from '@/labels';
import { useTheme } from '@/theme';
import { MediaItem } from '@/types';

import { Button, ErrorText } from './ui';

export type MediaPayload = Omit<MediaItem, 'id'>;

const EPISODIC = ['series', 'movie'];

type Props = {
  date: string;
  /** The kind of row this form adds (from the section's "+" button). */
  category?: string;
  initial?: MediaItem;
  onSubmit: (payload: MediaPayload) => void | Promise<void>;
  onCancel?: () => void;
};

const toInt = (text: string) => (/^\d+$/.test(text.trim()) ? Number(text.trim()) : NaN);

export default function MediaForm({ date, category: preset, initial, onSubmit, onCancel }: Props) {
  const theme = useTheme();
  const [category, setCategory] = useState(initial?.category ?? preset ?? 'series');
  const type: 'watch' | 'read' = (WATCH_CATEGORIES as readonly string[]).includes(category) ? 'watch' : 'read';
  const [title, setTitle] = useState(initial?.title ?? '');
  const [episode, setEpisode] = useState(initial?.episode ?? '');
  const [minutes, setMinutes] = useState(initial && !initial.unit_minutes ? String(initial.minutes) : '');
  const [unit, setUnit] = useState(initial?.unit_minutes ? String(initial.unit_minutes) : '');
  const [count, setCount] = useState(initial?.count ?? 1);
  const [pages, setPages] = useState(initial?.pages ? String(initial.pages) : '');
  const [url, setUrl] = useState(initial?.url ?? '');
  const [newWords, setNewWords] = useState(initial?.new_words ?? '');
  const [error, setError] = useState('');
  const episodic = EPISODIC.includes(category);

  async function fillTitle() {
    if (!url.trim() || title.trim()) return;
    try {
      const found = await api<{ title: string | null }>(`/media/youtube-title?url=${encodeURIComponent(url.trim())}`);
      if (found.title) setTitle((current) => current || found.title!);
    } catch {
      // offline or not a YouTube link: the user types the title
    }
  }

  async function save() {
    const cleanTitle = title.trim();
    if (!cleanTitle) return setError('Informe o título.');
    let total: number;
    if (episodic) {
      const perEpisode = toInt(unit);
      if (!(perEpisode >= 1 && perEpisode <= 600)) return setError('Informe os minutos por episódio (de 1 a 600).');
      total = perEpisode * count;
    } else {
      total = toInt(minutes);
      if (!(total >= 1 && total <= 1440)) return setError('Informe os minutos (de 1 a 1440).');
    }
    const pageCount = type === 'read' && toInt(pages) > 0 ? toInt(pages) : null;
    setError('');
    await onSubmit({
      date,
      type,
      category,
      title: cleanTitle,
      episode: type === 'watch' && episode.trim() ? episode.trim() : null,
      minutes: total,
      pages: pageCount,
      unit_minutes: episodic ? toInt(unit) : null,
      count: episodic ? count : null,
      url: category === 'video' && url.trim() ? url.trim() : null,
      new_words: type === 'read' && newWords.trim() ? newWords.trim() : null,
    });
    if (!initial) {
      setTitle('');
      setEpisode('');
      setMinutes('');
      setUnit('');
      setCount(1);
      setPages('');
      setUrl('');
      setNewWords('');
    }
  }

  const categories = type === 'watch' ? WATCH_CATEGORIES : READ_CATEGORIES;
  const inputStyle = [styles.input, { color: theme.text, borderColor: theme.border, backgroundColor: theme.card }];

  return (
    <View style={styles.container}>
      <View style={styles.row}>
        {categories.map((c) => (
          <Pressable key={c} onPress={() => setCategory(c)}
            style={[styles.chip, { borderColor: category === c ? theme.primary : theme.border }]}>
            <Text style={{ color: category === c ? theme.primary : theme.text }}>{CATEGORY_LABELS[c]}</Text>
          </Pressable>
        ))}
      </View>
      {category === 'video' ? (
        <TextInput value={url} onChangeText={setUrl} onBlur={fillTitle} placeholder="Link do YouTube"
          placeholderTextColor={theme.muted} autoCapitalize="none" autoCorrect={false} style={inputStyle} />
      ) : null}
      <TextInput value={title} onChangeText={setTitle} placeholder="Título" placeholderTextColor={theme.muted} style={inputStyle} />
      {episodic ? (
        <>
          <TextInput value={unit} onChangeText={setUnit} placeholder="Min por episódio" placeholderTextColor={theme.muted}
            keyboardType="number-pad" style={inputStyle} />
          <View style={styles.stepper}>
            <Pressable accessibilityRole="button" accessibilityLabel="Menos um episódio" onPress={() => setCount(Math.max(1, count - 1))}
              style={[styles.step, { borderColor: theme.border }]}>
              <Text style={{ color: theme.text, fontSize: 20, fontWeight: '800' }}>−</Text>
            </Pressable>
            <Text style={{ color: theme.text, fontSize: 18, fontWeight: '700' }}>{`${count} ep.`}</Text>
            <Pressable accessibilityRole="button" accessibilityLabel="Mais um episódio" onPress={() => setCount(Math.min(100, count + 1))}
              style={[styles.step, { borderColor: theme.border }]}>
              <Text style={{ color: theme.text, fontSize: 20, fontWeight: '800' }}>+</Text>
            </Pressable>
            {toInt(unit) > 0 ? (
              <Text style={{ color: theme.muted, fontSize: 15 }}>{`${count} × ${toInt(unit)} = ${count * toInt(unit)} min`}</Text>
            ) : null}
          </View>
        </>
      ) : (
        <TextInput value={minutes} onChangeText={setMinutes} placeholder="Minutos" placeholderTextColor={theme.muted}
          keyboardType="number-pad" style={inputStyle} />
      )}
      {type === 'watch' && episodic ? (
        <TextInput value={episode} onChangeText={setEpisode} placeholder="Episódio (opcional)" placeholderTextColor={theme.muted} style={inputStyle} />
      ) : null}
      {type === 'read' ? (
        <>
          <TextInput value={pages} onChangeText={setPages} placeholder="Páginas" placeholderTextColor={theme.muted}
            keyboardType="number-pad" style={inputStyle} />
          <TextInput value={newWords} onChangeText={setNewWords} placeholder="Palavras novas (opcional)" placeholderTextColor={theme.muted}
            multiline style={[inputStyle, { minHeight: 70 }]} />
        </>
      ) : null}
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
  stepper: { flexDirection: 'row', alignItems: 'center', gap: 12, flexWrap: 'wrap' },
  step: { width: 40, height: 40, borderRadius: 20, borderWidth: 2, alignItems: 'center', justifyContent: 'center' },
});
