import { describeError } from '@/errors';
import { useState } from 'react';
import { View } from 'react-native';

import { api, apiText } from '@/api';
import { saveText } from '@/download';
import { useTheme } from '@/theme';
import { useApi } from '@/useApi';

import { Button, Card, ErrorText, Muted, SectionTitle, Text } from './ui';

type Word = { id: number; word: string; sentence: string; translation: string; note: string; source: string };

/** The saved words (tap-to-translate and reading) with delete and the CSV export for Anki. */
export default function WordsSection() {
  const theme = useTheme();
  const words = useApi<Word[]>('/words');
  const [error, setError] = useState('');

  async function exportCsv() {
    setError('');
    try {
      await saveText('palavras.csv', await apiText('/words/export.csv'), 'text/csv');
    } catch (e) {
      setError(describeError(e));
    }
  }

  async function remove(id: number) {
    try {
      await api(`/words/${id}`, { method: 'DELETE' });
      await words.reload();
    } catch (e) {
      setError(describeError(e));
    }
  }

  const list = words.data ?? [];
  return (
    <View style={{ gap: 10 }}>
      <SectionTitle>{`Palavras novas (${list.length})`}</SectionTitle>
      {words.error || error ? <ErrorText>{words.error || error}</ErrorText> : null}
      {list.length === 0 ? <Muted>Toque numa palavra em inglês para traduzir e salvar.</Muted> : null}
      {list.slice(0, 50).map((w) => (
        <Card key={w.id} style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
          <View style={{ flex: 1 }}>
            <Text style={{ color: theme.text, fontSize: 16, fontWeight: '600' }}>{`${w.word} — ${w.translation || '…'}`}</Text>
            {w.sentence ? <Muted>{w.sentence}</Muted> : null}
          </View>
          <Button label="Excluir" kind="secondary" onPress={() => remove(w.id)} />
        </Card>
      ))}
      <Button label="Exportar para o Anki" kind="secondary" disabled={list.length === 0} onPress={exportCsv} />
    </View>
  );
}
