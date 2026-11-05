import { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { useTheme } from '@/theme';

import { Button, Text } from '../ui';

/** Tap the words to build the sentence; tap a word in the sentence to take it back. */
export default function OrderExercise({ words, disabled, submitLabel, onAnswer }: {
  words: string[];
  disabled: boolean;
  submitLabel: string;
  onAnswer: (answer: string) => void;
}) {
  const theme = useTheme();
  const [built, setBuilt] = useState<number[]>([]);
  const left = words.map((w, i) => ({ w, i })).filter(({ i }) => !built.includes(i));

  return (
    <>
      <View style={[styles.line, { borderColor: theme.border, backgroundColor: theme.card }]}>
        {built.map((i) => (
          <Pressable key={i} accessibilityRole="button" accessibilityLabel={`Remover ${words[i]}`}
            onPress={() => setBuilt(built.filter((x) => x !== i))}
            style={[styles.chip, { backgroundColor: theme.tint, borderColor: theme.border }]}>
            <Text style={{ color: theme.text, fontSize: 17, fontWeight: '600' }}>{words[i]}</Text>
          </Pressable>
        ))}
      </View>
      <View style={styles.bank}>
        {left.map(({ w, i }) => (
          <Pressable key={i} accessibilityRole="button" accessibilityLabel={`Palavra ${w}`}
            onPress={() => setBuilt([...built, i])}
            style={[styles.chip, { backgroundColor: theme.card, borderColor: theme.border }]}>
            <Text style={{ color: theme.text, fontSize: 17 }}>{w}</Text>
          </Pressable>
        ))}
      </View>
      <Button label={submitLabel} disabled={disabled || left.length > 0}
        onPress={() => onAnswer(built.map((i) => words[i]).join(' '))} />
    </>
  );
}

const styles = StyleSheet.create({
  line: { minHeight: 60, borderWidth: 2, borderRadius: 16, padding: 8, flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  bank: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { borderWidth: 2, borderRadius: 12, paddingVertical: 8, paddingHorizontal: 12 },
});
