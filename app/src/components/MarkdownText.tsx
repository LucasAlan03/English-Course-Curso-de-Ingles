import { ReactNode } from 'react';
import { StyleSheet, View } from 'react-native';

import { useTheme } from '@/theme';

import { sentenceAround } from '@/sentence';

import { splitWords } from './TappableText';
import { Text } from './ui';

/** Index of the closing marker, skipping "**" pairs when looking for a single "*". */
function findClose(s: string, from: number, marker: '*' | '**'): number {
  for (let i = from; i < s.length; i++) {
    if (marker === '**') {
      if (s.startsWith('**', i)) return i;
    } else if (s[i] === '*') {
      if (s[i + 1] === '*') {
        i++; // skip the whole "**"
        continue;
      }
      return i;
    }
  }
  return -1;
}

/**
 * Inline markdown: **bold** and *example* (English examples get their own colour), nested either way.
 * Unmatched asterisks are dropped so raw markers never reach the screen.
 */
type InlineColors = { example: string; onWord?: (word: string, sentence: string) => void };

function renderInline(s: string, colors: InlineColors, bold = false, example = false, key = 'k'): ReactNode[] {
  const out: ReactNode[] = [];
  let buffer = '';
  const flush = () => {
    if (buffer) {
      out.push(
        <Text
          key={`${key}-${out.length}`}
          style={[
            bold && styles.bold,
            example && { color: colors.example, fontWeight: bold ? '800' : '600' },
          ]}
        >
          {example && colors.onWord
            ? splitWords(buffer).map((p) =>
                p.isWord ? (
                  <Text key={p.index} onPress={() => colors.onWord!(p.text, sentenceAround(buffer, p.index))}>{p.text}</Text>
                ) : (
                  p.text
                ),
              )
            : buffer}
        </Text>,
      );
      buffer = '';
    }
  };
  let i = 0;
  while (i < s.length) {
    if (s.startsWith('**', i)) {
      const end = findClose(s, i + 2, '**');
      if (end > i + 2) {
        flush();
        out.push(...renderInline(s.slice(i + 2, end), colors, true, example, `${key}-${out.length}`));
        i = end + 2;
        continue;
      }
    } else if (s[i] === '*') {
      const end = findClose(s, i + 1, '*');
      if (end > i + 1) {
        flush();
        out.push(...renderInline(s.slice(i + 1, end), colors, bold, true, `${key}-${out.length}`));
        i = end + 1;
        continue;
      }
    }
    if (s[i] !== '*') buffer += s[i];
    i++;
  }
  flush();
  return out;
}

/** Tiny markdown renderer for lesson theory: #/##/### headings, "- " bullets, **bold** and *examples*. */
export default function MarkdownText({ text, skipFirstHeading, onWord }: {
  text: string;
  skipFirstHeading?: boolean;
  /** When set, the words of the English *examples* can be tapped to translate. */
  onWord?: (word: string, sentence: string) => void;
}) {
  const theme = useTheme();
  const colors: InlineColors = { example: theme.lake, onWord };
  let skipped = !skipFirstHeading;

  return (
    <View style={styles.container}>
      {text.split('\n').map((raw, i) => {
        const line = raw.trimEnd();
        if (!line.trim()) return <View key={i} style={{ height: 2 }} />;
        const heading = line.match(/^#{1,3}\s+(.*)$/);
        if (heading) {
          if (!skipped) {
            skipped = true;
            return null;
          }
          return (
            <Text key={i} style={[styles.heading, { color: theme.text }]}>
              {heading[1]}
            </Text>
          );
        }
        const bullet = line.match(/^\s*[-•]\s+(.*)$/);
        if (bullet) {
          return (
            <View key={i} style={styles.bulletRow}>
              <View style={[styles.bulletDot, { backgroundColor: theme.sun }]} />
              <Text style={[styles.body, { color: theme.text, flex: 1 }]}>{renderInline(bullet[1], colors, false, false, `b${i}`)}</Text>
            </View>
          );
        }
        return (
          <Text key={i} style={[styles.body, { color: theme.text }]}>
            {renderInline(line, colors, false, false, `p${i}`)}
          </Text>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { gap: 10 },
  heading: { fontSize: 19, fontWeight: '800', marginTop: 6 },
  body: { fontSize: 16.5, lineHeight: 25 },
  bold: { fontWeight: '700' },
  bulletRow: { flexDirection: 'row', gap: 12, alignItems: 'flex-start' },
  bulletDot: { width: 8, height: 8, borderRadius: 4, marginTop: 9 },
});
