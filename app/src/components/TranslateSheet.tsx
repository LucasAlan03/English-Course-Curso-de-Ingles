import { describeError } from '@/errors';
import { useCallback, useEffect, useState } from 'react';
import { StyleSheet, View } from 'react-native';

import { api } from '@/api';
import { useTheme } from '@/theme';

import { Button, ErrorText, Muted, Text } from './ui';

type Translation = { translation: string; note: string; cached: boolean };

/** AI translation of one word in its sentence (cached on the server), with "save word" for Anki. */
export default function TranslateSheet({ word, sentence, onClose }: { word: string; sentence: string; onClose: () => void }) {
  const theme = useTheme();
  const [result, setResult] = useState<Translation | null>(null);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    setError('');
    setResult(null);
    try {
      setResult(await api<Translation>('/translate', { method: 'POST', json: { word, sentence } }));
    } catch (e) {
      setError(describeError(e));
    }
  }, [word, sentence]);

  useEffect(() => {
    setSaved(false);
    load();
  }, [load]);

  async function save() {
    if (!result) return;
    try {
      await api('/words', {
        method: 'POST',
        json: { word, sentence, translation: result.translation, note: result.note, source: 'tap' },
      });
      setSaved(true);
    } catch (e) {
      setError(describeError(e));
    }
  }

  return (
    <View style={[styles.sheet, { backgroundColor: theme.card, borderColor: theme.border }]}>
      <Text style={{ color: theme.muted, fontSize: 13, fontWeight: '700' }}>{word}</Text>
      {!result && !error ? <Muted>Traduzindo…</Muted> : null}
      {result ? <Text style={{ color: theme.text, fontSize: 18, fontWeight: '700' }}>{result.translation}</Text> : null}
      {result?.note ? <Muted>{result.note}</Muted> : null}
      {error ? <ErrorText>{error}</ErrorText> : null}
      <View style={styles.actions}>
        {error ? <Button label="Tentar de novo" kind="secondary" onPress={load} /> : null}
        {result ? (
          saved ? <Text style={{ color: theme.good, fontWeight: '700' }}>Salva!</Text>
            : <Button label="Salvar palavra" kind="secondary" onPress={save} />
        ) : null}
        <Button label="Fechar" kind="secondary" onPress={onClose} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  sheet: { borderWidth: 1, borderRadius: 16, padding: 12, gap: 6 },
  actions: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, alignItems: 'center' },
});
