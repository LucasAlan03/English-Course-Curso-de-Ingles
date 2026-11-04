import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { api } from '@/api';
import { Button, ErrorText, Muted, SectionTitle } from '@/components/ui';
import { useTheme } from '@/theme';

const SUGGESTIONS = ['Travel', 'Music', 'Work', 'Food', 'Football', 'Movies'];

export default function FreeScreen() {
  const theme = useTheme();
  const [topic, setTopic] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function start() {
    setBusy(true);
    setError('');
    try {
      const clean = topic.trim();
      const session = await api<{ id: number }>('/sessions', {
        method: 'POST',
        json: clean ? { kind: 'free', topic: clean } : { kind: 'free' },
      });
      router.replace(`/chat/${session.id}`);
    } catch (e) {
      setError((e as { detail?: string }).detail ?? String(e));
      setBusy(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <SectionTitle>Conversa livre</SectionTitle>
      <Muted>Escolha um assunto ou deixe em branco. Os erros que aparecerem alimentam suas revisões.</Muted>
      <TextInput
        value={topic}
        onChangeText={setTopic}
        placeholder="Assunto (opcional)"
        placeholderTextColor={theme.muted}
        style={[styles.input, { color: theme.text, borderColor: theme.border, backgroundColor: theme.card }]}
      />
      <View style={styles.chips}>
        {SUGGESTIONS.map((s) => (
          <Pressable key={s} onPress={() => setTopic(s)} style={[styles.chip, { borderColor: theme.border }]}>
            <Text style={{ color: theme.text }}>{s}</Text>
          </Pressable>
        ))}
      </View>
      {error ? <ErrorText>{error}</ErrorText> : null}
      <Button label="Começar conversa" onPress={start} disabled={busy} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, gap: 12 },
  input: { borderWidth: 1, borderRadius: 12, padding: 14, fontSize: 16 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { borderWidth: 1, borderRadius: 999, paddingVertical: 8, paddingHorizontal: 14 },
});
