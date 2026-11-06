import { StyleSheet, View } from 'react-native';

import { useTheme } from '@/theme';

import TranslatableText from './TranslatableText';
import { Text } from './ui';

export default function ChatBubble({ role, text }: { role: 'user' | 'assistant'; text: string }) {
  const theme = useTheme();
  const mine = role === 'user';
  return (
    <View
      style={[
        styles.bubble,
        mine ? styles.mine : styles.theirs,
        { backgroundColor: mine ? theme.primary : theme.card, borderColor: mine ? theme.primary : theme.border },
      ]}
    >
      {mine ? (
        <Text style={{ color: theme.onPrimary, fontSize: 16, lineHeight: 22 }}>{text}</Text>
      ) : (
        <TranslatableText text={text} style={{ color: theme.text, fontSize: 16, lineHeight: 22 }} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  bubble: { maxWidth: '85%', borderWidth: 1, borderRadius: 16, paddingVertical: 10, paddingHorizontal: 14 },
  mine: { alignSelf: 'flex-end' },
  theirs: { alignSelf: 'flex-start' },
});
