import { useState } from 'react';
import { StyleProp, TextStyle, View } from 'react-native';

import { sentenceAround } from '@/sentence';

import TappableText from './TappableText';
import TranslateSheet from './TranslateSheet';

/** Free English text (chat, lyrics): tap a word to see its AI translation in context, right below. */
export default function TranslatableText({ text, style }: { text: string; style?: StyleProp<TextStyle> }) {
  const [picked, setPicked] = useState<{ word: string; sentence: string } | null>(null);
  return (
    <View style={{ gap: 6 }}>
      <TappableText text={text} style={style} onWord={(word, index) => setPicked({ word, sentence: sentenceAround(text, index) })} />
      {picked ? <TranslateSheet word={picked.word} sentence={picked.sentence} onClose={() => setPicked(null)} /> : null}
    </View>
  );
}
