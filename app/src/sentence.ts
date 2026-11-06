/** The sentence (split on . ! ? and line breaks) that contains the character at `charIndex`. */
export function sentenceAround(text: string, charIndex: number): string {
  let start = 0;
  for (let i = charIndex - 1; i >= 0; i--) {
    if ('.!?\n'.includes(text[i])) {
      start = i + 1;
      break;
    }
  }
  let end = text.length;
  for (let i = charIndex; i < text.length; i++) {
    if (text[i] === '\n') {
      end = i;
      break;
    }
    if ('.!?'.includes(text[i])) {
      end = i + 1;
      break;
    }
  }
  return text.slice(start, end).trim();
}
