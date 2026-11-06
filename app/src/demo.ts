// Demo mode for the public web showcase (EXPO_PUBLIC_DEMO=1).
// Instead of calling the backend, the app reads responses recorded by
// backend/scripts/build_demo_data.py (demo-data.json) and grades lesson
// exercises in the browser. Nothing is saved.
import { ApiError } from './api';

export const DEMO = process.env.EXPO_PUBLIC_DEMO === '1';
// Where demo-data.json and audio/ are served from (e.g. "/English-Course-Curso-de-Ingl-s").
export const DEMO_BASE = (process.env.EXPO_PUBLIC_DEMO_BASE ?? '').replace(/\/$/, '');

export const DEMO_NOTICE = 'Isto é uma demonstração: nada é salvo e a IA fica desligada. Rode o projeto localmente para usar de verdade.';

type Recorded = { status: number; body: unknown };
type DemoData = {
  date: string;
  responses: Record<string, Recorded>;
  answers: Record<string, { answers: string[]; explanation: string }>;
};

let data: Promise<DemoData> | null = null;

function load(): Promise<DemoData> {
  if (!data) {
    data = fetch(`${DEMO_BASE}/demo-data.json`).then((r) => r.json() as Promise<DemoData>);
  }
  return data;
}

const QUOTES: Record<string, string> = { '‘': "'", '’': "'", 'ʼ': "'", '`': "'", '“': '"', '”': '"' };
const CONTRACTIONS: [RegExp, string][] = [
  [/\bwon't\b/g, 'will not'],
  [/\bcan't\b/g, 'can not'],
  [/\bcannot\b/g, 'can not'],
  [/n't\b/g, ' not'],
  [/'m\b/g, ' am'],
  [/'re\b/g, ' are'],
  [/'ve\b/g, ' have'],
  [/'ll\b/g, ' will'],
];

/** Same rules as normalize() in backend/app/exercises.py. */
export function normalize(text: string): string {
  let t = text.normalize('NFKC').replace(/[‘’ʼ`“”]/g, (c) => QUOTES[c]).toLowerCase();
  t = t.replace(/,/g, ' ').replace(/"/g, ' ');
  t = t.replace(/^[ .!?;:\t\n\r]+|[ .!?;:\t\n\r]+$/g, '');
  t = t.replace(/\s+/g, ' ');
  for (const [pattern, replacement] of CONTRACTIONS) t = t.replace(pattern, replacement);
  return t.replace(/\s+/g, ' ').trim();
}

const ANSWER = /^\/exercises\/([^/]+)\/([^/]+)\/answer$/;

export async function demoRequest<T>(path: string, method: string, json: unknown): Promise<T> {
  const d = await load();
  if (method === 'GET') {
    const hit = d.responses[path] ?? d.responses[path.split('?')[0]];
    if (!hit) throw new ApiError('demo_mode', 'Esta tela não faz parte da demonstração.');
    if (hit.status >= 400) {
      const b = hit.body as { error?: string; detail?: string };
      throw new ApiError(b.error ?? 'http_error', b.detail ?? '', hit.status);
    }
    return hit.body as T;
  }
  const m = ANSWER.exec(path);
  const body = (json ?? {}) as { answer?: string; run_id?: number | null };
  if (method === 'POST' && m && body.run_id == null) {
    const key = d.answers[`${m[1]}/${m[2]}`];
    if (!key) throw new ApiError('exercise_not_found', 'Exercício não encontrado.', 404);
    const given = normalize(body.answer ?? '');
    return {
      correct: key.answers.some((a) => normalize(a) === given),
      correct_answer: key.answers[0],
      explanation: key.explanation,
      module_completed: false,
      score: null,
      next_due: null,
    } as T;
  }
  throw new ApiError('demo_mode', DEMO_NOTICE);
}

/** Exercise audio is published next to the demo (only synthetic voices of exercises). */
export function demoAudioUrl(path: string): string {
  return `${DEMO_BASE}${path}`;
}
