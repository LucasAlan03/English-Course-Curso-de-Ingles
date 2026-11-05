export type PillarKey = 'grammar' | 'speak' | 'write' | 'read' | 'watch';
export type Pillars = Record<PillarKey, boolean>;

export type UsageStatus = { total: number; warn: number; cap: number; level: 'ok' | 'warn' | 'blocked' };

export type ReviewDue = { module_id: string; title: string; next_due: string; overdue_days: number };

export type Home = {
  reviews_due: ReviewDue[];
  next_module: { id: string; title: string; level: string } | null;
  pillars: Pillars;
  streak: number;
  usage: UsageStatus;
};

export type ModuleSummary = { id: string; title: string; order: number; completed: boolean };
export type ExamStatus = {
  available: boolean;
  missing_modules: number;
  passed: boolean;
  best_score: number | null;
  open_run_id: number | null;
};
export type LevelSummary = {
  level: string;
  total: number;
  completed: number;
  modules: ModuleSummary[];
  unlocked?: boolean;
  exam?: ExamStatus;
};
export type Modules = { levels: LevelSummary[] };

export type ModuleDetail = {
  id: string;
  level: string;
  title: string;
  theory_md: string;
  scenario: { title: string; character: string; goal: string };
  target_structures: string[];
  completed: boolean;
};

export type ExerciseType = 'choice' | 'listen' | 'gap' | 'dictation' | 'fix' | 'transform' | 'order' | 'translate';

export type Feedback = { correct: boolean; correct_answer: string; explanation: string };

export type Exercise = {
  id: string;
  block: 1 | 2 | 3;
  type: ExerciseType;
  prompt: string;
  prompt_pt: string | null;
  glossary: Record<string, string>;
  options: string[] | null;
  words: string[] | null;
  audio_url: string | null;
  answered: boolean;
  result: (Feedback & { user_answer: string }) | null;
};

export type AnswerResult = Feedback & {
  module_completed: boolean;
  score: number | null;
  next_due: string | null;
};

export type Mistake = { said: string; corrected: string; explanation: string; module_id: string | null };
export type Report = { mistakes: Mistake[]; natural_expressions: string[]; strengths: string[]; score: number };
export type FinishResult = {
  report: Report;
  listening_score: number | null;
  conversation_score: number;
  final_score: number;
  next_due: string | null;
};

export type TurnResult = { user_text: string; reply_text: string; reply_audio_url: string | null };

export type WritingFeedback = { corrected_text: string; improved_text: string; mistakes: Mistake[]; score: number };

export type MediaItem = {
  id: number;
  date: string;
  type: 'watch' | 'read';
  category: string;
  title: string;
  episode: string | null;
  minutes: number;
  pages: number | null;
};
export type MediaTotals = { total_minutes: number; by_type: Record<string, number>; by_category: Record<string, number> };
export type MediaSummary = { day: MediaTotals; week: MediaTotals; month: MediaTotals };

export type ExamResultItem = {
  id: string;
  prompt: string;
  module_id: string;
  module_title: string;
  user_answer: string | null;
  correct: boolean;
  correct_answer: string;
  explanation: string;
};
export type ExamRun = {
  run_id: number;
  level: string;
  finished: boolean;
  score: number | null;
  passed: boolean | null;
  pass_percent: number;
  results: ExamResultItem[] | null;
};
