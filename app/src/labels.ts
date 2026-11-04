export const WATCH_CATEGORIES = ['series', 'movie', 'video', 'podcast'] as const;
export const READ_CATEGORIES = ['hq', 'book', 'article', 'other'] as const;

export const CATEGORY_LABELS: Record<string, string> = {
  series: 'Série',
  movie: 'Filme',
  video: 'Vídeo',
  podcast: 'Podcast',
  hq: 'HQ',
  book: 'Livro',
  article: 'Artigo',
  other: 'Outro',
};
