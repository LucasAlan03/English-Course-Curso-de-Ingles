import { useState } from 'react';
import { StyleSheet, TextInput } from 'react-native';

import { fonts, useTheme } from '@/theme';

import { Button } from '../ui';

export default function TypedExercise({ initial = '', disabled, submitLabel, onAnswer }: {
  initial?: string;
  disabled: boolean;
  submitLabel: string;
  onAnswer: (answer: string) => void;
}) {
  const theme = useTheme();
  const [typed, setTyped] = useState(initial);
  return (
    <>
      <TextInput
        value={typed}
        onChangeText={setTyped}
        placeholder="Sua resposta"
        placeholderTextColor={theme.muted}
        autoCapitalize="none"
        autoCorrect={false}
        multiline
        style={[styles.input, { color: theme.text, borderColor: theme.border, backgroundColor: theme.card, fontFamily: fonts[500] }]}
      />
      <Button label={submitLabel} disabled={disabled || !typed.trim()} onPress={() => onAnswer(typed)} />
    </>
  );
}

const styles = StyleSheet.create({
  input: { borderWidth: 2, borderRadius: 16, padding: 14, fontSize: 18, minHeight: 56 },
});
