import { StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@/theme';

/** Tiny markdown renderer: #/##/### headings, "- " bullets and **bold**. Enough for lesson theory. */
export default function MarkdownText({ text }: { text: string }) {
  const theme = useTheme();

  function inline(line: string, keyPrefix: string) {
    return line.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
      part.startsWith('**') && part.endsWith('**') && part.length > 4 ? (
        <Text key={`${keyPrefix}-${i}`} style={styles.bold}>
          {part.slice(2, -2)}
        </Text>
      ) : (
        part
      ),
    );
  }

  return (
    <View style={styles.container}>
      {text.split('\n').map((raw, i) => {
        const line = raw.trimEnd();
        if (!line.trim()) return <View key={i} style={{ height: 4 }} />;
        const heading = line.match(/^#{1,3}\s+(.*)$/);
        if (heading) {
          return (
            <Text key={i} style={[styles.heading, { color: theme.text }]}>
              {heading[1]}
            </Text>
          );
        }
        const bullet = line.match(/^\s*[-*]\s+(.*)$/);
        return (
          <Text key={i} style={[styles.body, { color: theme.text }]}>
            {bullet ? '• ' : ''}
            {inline(bullet ? bullet[1] : line, String(i))}
          </Text>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 4 },
  heading: { fontSize: 20, fontWeight: '700', marginTop: 6 },
  body: { fontSize: 16, lineHeight: 23 },
  bold: { fontWeight: '700' },
});
