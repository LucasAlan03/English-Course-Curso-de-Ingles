import { describeError } from '@/errors';
import { useEffect, useState } from 'react';
import { StyleSheet, TextInput, View } from 'react-native';

import { api } from '@/api';
import { useTheme } from '@/theme';

import { Button, ErrorText, Muted, SectionTitle } from './ui';

/** Times of the Android reminders (they only fire while the day is incomplete). */
export default function RemindersSection() {
  const theme = useTheme();
  const [text, setText] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    api<{ times: string[] }>('/settings/reminders')
      .then((r) => setText(r.times.join(', ')))
      .catch((e) => setError(describeError(e)));
  }, []);

  async function save() {
    setError('');
    setMessage('');
    const times = text.split(/[,\s]+/).map((t) => t.trim()).filter(Boolean);
    try {
      await api('/settings/reminders', { method: 'PUT', json: { times } });
      setMessage('Horários salvos. Valem a partir da próxima vez que abrir o app.');
    } catch (e) {
      setError(describeError(e));
    }
  }

  return (
    <View style={{ gap: 8 }}>
      <SectionTitle>Lembretes</SectionTitle>
      <Muted>Até 4 horários (HH:MM), separados por vírgula. Só tocam no Android e só se o dia não estiver completo.</Muted>
      <TextInput value={text} onChangeText={setText} placeholder="19:00, 21:00" placeholderTextColor={theme.muted}
        style={[styles.input, { color: theme.text, borderColor: theme.border, backgroundColor: theme.card }]} />
      {error ? <ErrorText>{error}</ErrorText> : null}
      {message ? <Muted>{message}</Muted> : null}
      <Button label="Salvar horários" kind="secondary" onPress={save} />
    </View>
  );
}

const styles = StyleSheet.create({ input: { borderWidth: 1, borderRadius: 12, padding: 12, fontSize: 16 } });
