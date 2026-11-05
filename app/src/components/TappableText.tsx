import { useState } from 'react';
import { Pressable, StyleProp, StyleSheet, TextStyle, View } from 'react-native';

import { useTheme } from '@/theme';

import { Text } from './ui';

const WORD = /[A-Za-z’']+/g;

type Piece = { text: string; isWord: boolean; index: number };

export function splitWords(text: string): Piece[] {
  const pieces: Piece[] = [];
  let last = 0;
  for (const match of text.matchAll(WORD)) {
    const at = match.index ?? 0;
    if (at > last) pieces.push({ text: text.slice(last, at), isWord: false, index: last });
    pieces.push({ text: match[0], isWord: true, index: at });
    last = at + match[0].length;
  }
  if (last < text.length) pieces.push({ text: text.slice(last), isWord: false, index: last });
  return pieces;
}

type Props = {
  text: string;
  style?: StyleProp<TextStyle>;
  /** Exercises and exams: ready-made translations, never the network. */
  glossary?: Record<string, string>;
  promptPt?: string | null;
  /** Free text (chat, theory, lyrics): called with the word and its position; opens the AI sheet. */
  onWord?: (word: string, index: number) => void;
};

/** Text whose English words can be tapped to see a translation. */
export default function TappableText({ text, style, glossary, promptPt, onWord }: Props) {
  const theme = useTheme();
  const [balloon, setBalloon] = useState<{ word: string | null; body: string } | null>(null);

  function press(word: string, index: number) {
    if (glossary) {
      const key = word.toLowerCase().replace(/’/g, "'");
      const hit = glossary[key] ?? Object.entries(glossary).find(([k]) => k.toLowerCase() === key)?.[1];
      if (hit) setBalloon({ word, body: hit });
      else setBalloon({ word: null, body: promptPt ? `Tradução da frase: ${promptPt}` : 'Sem tradução pronta para esta palavra.' });
      return;
    }
    onWord?.(word, index);
  }

  return (
    <View style={{ gap: 6 }}>
      <Text style={style}>
        {splitWords(text).map((p) =>
          p.isWord ? (
            <Text
              key={p.index}
              style={[style, glossary && hasKey(glossary, p.text) ? { textDecorationLine: 'underline' } : null]}
              onPress={() => press(p.text, p.index)}
              suppressHighlighting
            >
              {p.text}
            </Text>
          ) : (
            p.text
          ),
        )}
      </Text>
      {balloon ? (
        <Pressable onPress={() => setBalloon(null)} accessibilityRole="button" accessibilityLabel="Fechar tradução"
          style={[styles.balloon, { backgroundColor: theme.tint, borderColor: theme.border }]}>
          {balloon.word ? <Text style={{ color: theme.muted, fontSize: 13, fontWeight: '700' }}>{balloon.word}</Text> : null}
          <Text style={{ color: theme.text, fontSize: 15 }}>{balloon.body}</Text>
        </Pressable>
      ) : null}
    </View>
  );
}

function hasKey(glossary: Record<string, string>, word: string) {
  const key = word.toLowerCase();
  return Object.keys(glossary).some((k) => k.toLowerCase() === key);
}

const styles = StyleSheet.create({
  balloon: { borderWidth: 1, borderRadius: 14, paddingVertical: 8, paddingHorizontal: 12, alignSelf: 'flex-start' },
});
