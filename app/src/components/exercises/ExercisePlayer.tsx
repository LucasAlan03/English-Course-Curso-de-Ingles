import { describeError } from '@/errors';
import { useRef, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { useTheme } from '@/theme';
import { Exercise, ExerciseType, Feedback } from '@/types';

import TappableText from '../TappableText';
import { Button, Card, ErrorText, Muted, Text } from '../ui';
import ChoiceExercise from './ChoiceExercise';
import OrderExercise from './OrderExercise';
import TypedExercise from './TypedExercise';

export const INSTRUCTIONS: Record<ExerciseType, string> = {
  choice: 'Escolha a opção certa',
  listen: 'Ouça e responda',
  gap: 'Complete a lacuna',
  dictation: 'Escreva o que ouvir',
  fix: 'Corrija o erro',
  transform: 'Reescreva a frase',
  order: 'Monte a frase',
  translate: 'Traduza para o inglês',
};
const BLOCK_SIZE = 9; // every module has 3 blocks of 9 (backend BLOCK_PLAN)
const BLOCK_NAMES: Record<number, string> = { 1: 'Reconhecer', 2: 'Praticar', 3: 'Produzir' };

type Props = {
  items: Exercise[];
  /** Returns the correction, or null in exam mode (no feedback until the end). */
  submit: (item: Exercise, answer: string, seconds: number) => Promise<Feedback | null>;
  play: (audioUrl: string) => void;
  onDone: () => void;
  onReport?: (item: Exercise) => void;
  instantFeedback?: boolean;
  /** Single-block mode (reviews and exams): header becomes "<title> · k de N". */
  title?: string;
};

export default function ExercisePlayer({ items, submit, play, onDone, onReport, instantFeedback = true, title }: Props) {
  const theme = useTheme();
  const firstOpen = items.findIndex((i) => !i.answered);
  const [index, setIndex] = useState(firstOpen === -1 ? items.length - 1 : firstOpen);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const [transition, setTransition] = useState<number | null>(null);
  const [showPt, setShowPt] = useState(false);
  const [busy, setBusy] = useState(false);
  const [reported, setReported] = useState(false);
  const [error, setError] = useState('');
  const shownAt = useRef(Date.now());

  const item = items[index];
  if (!item) return null;
  const isLast = index === items.length - 1;
  const inBlock = items.filter((i) => i.block === item.block);
  const header = title
    ? `${title} · ${index + 1} de ${items.length}`
    : `Bloco ${item.block} de 3 · Exercício ${inBlock.indexOf(item) + 1} de ${BLOCK_SIZE}`;

  function goNext() {
    if (isLast) {
      onDone();
      return;
    }
    const next = items[index + 1];
    setIndex(index + 1);
    setFeedback(null);
    setShowPt(false);
    setReported(false);
    shownAt.current = Date.now();
    if (!title && next.block !== item.block) setTransition(next.block);
  }

  async function answer(text: string) {
    if (busy || !text.trim()) return;
    setBusy(true);
    setError('');
    try {
      const seconds = Math.round((Date.now() - shownAt.current) / 1000);
      const result = await submit(item, text, seconds);
      if (instantFeedback && result) setFeedback(result);
      else goNext();
    } catch (e) {
      setError(describeError(e));
    } finally {
      setBusy(false);
    }
  }

  if (transition !== null) {
    return (
      <Card style={{ padding: 22, gap: 10 }}>
        <Text style={{ color: theme.text, fontSize: 24, fontWeight: '800' }}>{`Bloco ${transition} · ${BLOCK_NAMES[transition]}`}</Text>
        <Muted>{transition === 2 ? 'Agora você monta as frases com apoio.' : 'Agora é com você: produza sozinho.'}</Muted>
        <Button label="Começar" onPress={() => setTransition(null)} />
      </Card>
    );
  }

  const submitLabel = instantFeedback ? 'Verificar' : 'Responder';
  const done = items.filter((i) => i.answered).length;
  const progress = Math.max(index + (feedback ? 1 : 0), done) / items.length;

  return (
    <View style={styles.container}>
      <View style={{ gap: 6 }}>
        <View style={[styles.track, { backgroundColor: theme.border }]}>
          <View style={{ width: `${progress * 100}%`, height: '100%', backgroundColor: theme.good, borderRadius: 4 }} />
        </View>
        <Text style={{ color: theme.muted, fontSize: 14, fontWeight: '600' }}>{header}</Text>
      </View>

      <Text style={{ color: theme.muted, fontSize: 15, fontWeight: '700' }}>{INSTRUCTIONS[item.type]}</Text>

      {item.audio_url ? (
        <Pressable accessibilityRole="button" accessibilityLabel="Ouvir" onPress={() => play(item.audio_url!)}
          style={({ pressed }) => [styles.listen, { backgroundColor: theme.pine, opacity: pressed ? 0.85 : 1 }]}>
          <View style={[styles.playDisc, { backgroundColor: theme.sun }]}>
            <Text style={{ color: theme.onSun, fontSize: 18, marginLeft: 3 }}>▶</Text>
          </View>
          <Text style={{ color: theme.onPine, fontWeight: '700', fontSize: 17 }}>Ouvir</Text>
        </Pressable>
      ) : null}

      {item.type === 'translate' ? (
        <Text style={styles.prompt(theme.text)}>{item.prompt}</Text>
      ) : (
        <TappableText text={item.prompt} style={styles.prompt(theme.text)} glossary={item.glossary ?? {}} promptPt={item.prompt_pt} />
      )}

      {item.prompt_pt ? (
        <Pressable accessibilityRole="button" onPress={() => setShowPt(!showPt)}>
          <Text style={{ color: theme.primary, fontWeight: '700', fontSize: 14 }}>{showPt ? 'Esconder tradução' : 'Ver tradução'}</Text>
        </Pressable>
      ) : null}
      {showPt && item.prompt_pt ? <Muted>{item.prompt_pt}</Muted> : null}

      {!feedback ? (
        item.type === 'order' && item.words ? (
          <OrderExercise key={item.id} words={item.words} disabled={busy} submitLabel={submitLabel} onAnswer={answer} />
        ) : item.options && (item.type === 'choice' || item.type === 'listen') ? (
          <ChoiceExercise options={item.options} disabled={busy} onAnswer={answer} />
        ) : (
          <TypedExercise key={item.id} initial={item.type === 'fix' ? item.prompt : ''} disabled={busy}
            submitLabel={submitLabel} onAnswer={answer} />
        )
      ) : null}

      {error ? <ErrorText>{error}</ErrorText> : null}

      {feedback ? (
        <>
          <Card style={{ backgroundColor: (feedback.correct ? theme.good : theme.bad) + '22', borderColor: feedback.correct ? theme.good : theme.bad, padding: 18 }}>
            <Text style={{ color: feedback.correct ? theme.good : theme.bad, fontWeight: '800', fontSize: 18 }}>
              {feedback.correct ? 'Correto!' : `Resposta certa: ${feedback.correct_answer}`}
            </Text>
            <Text style={{ color: theme.text, fontSize: 16, lineHeight: 23 }}>{feedback.explanation}</Text>
          </Card>
          {onReport ? (
            <Pressable accessibilityRole="button" disabled={reported} onPress={() => { onReport(item); setReported(true); }}>
              <Text style={{ color: theme.muted, fontSize: 13, textDecorationLine: 'underline' }}>
                {reported ? 'Obrigado! Exercício reportado.' : 'Reportar exercício'}
              </Text>
            </Pressable>
          ) : null}
          <Button label={isLast ? 'Ver resultado' : 'Próximo'} onPress={goNext} />
        </>
      ) : null}
    </View>
  );
}

const styles = {
  ...StyleSheet.create({
    container: { gap: 14 },
    track: { height: 8, borderRadius: 4, overflow: 'hidden' },
    listen: { flexDirection: 'row', alignItems: 'center', gap: 14, borderRadius: 20, padding: 14 },
    playDisc: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center' },
  }),
  prompt: (color: string) => ({ color, fontSize: 23, fontWeight: '700' as const, lineHeight: 30, letterSpacing: -0.3 }),
};
