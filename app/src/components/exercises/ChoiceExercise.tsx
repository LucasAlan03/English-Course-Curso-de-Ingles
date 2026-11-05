import { Pressable, StyleSheet } from 'react-native';

import { useTheme } from '@/theme';

import { Text } from '../ui';

export default function ChoiceExercise({ options, disabled, onAnswer }: {
  options: string[];
  disabled: boolean;
  onAnswer: (answer: string) => void;
}) {
  const theme = useTheme();
  return (
    <>
      {options.map((option) => (
        <Pressable
          key={option}
          accessibilityRole="button"
          disabled={disabled}
          onPress={() => onAnswer(option)}
          style={({ pressed }) => [
            styles.option,
            {
              backgroundColor: theme.card,
              borderColor: theme.border,
              borderBottomWidth: pressed ? 2 : 4,
              marginTop: pressed ? 2 : 0,
              marginBottom: pressed ? 2 : 0,
            },
            disabled && { opacity: 0.5 },
          ]}
        >
          <Text style={{ color: theme.text, fontSize: 17, fontWeight: '500' }}>{option}</Text>
        </Pressable>
      ))}
    </>
  );
}

const styles = StyleSheet.create({
  option: { borderWidth: 2, borderRadius: 16, paddingVertical: 16, paddingHorizontal: 18 },
});
