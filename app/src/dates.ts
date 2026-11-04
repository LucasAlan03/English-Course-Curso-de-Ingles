function pad(n: number) {
  return String(n).padStart(2, '0');
}

/** Local calendar date as YYYY-MM-DD (not UTC, so late-night entries stay on the right day). */
export function toIso(date: Date): string {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function todayIso(): string {
  return toIso(new Date());
}

export function shiftDay(iso: string, days: number): string {
  const [y, m, d] = iso.split('-').map(Number);
  return toIso(new Date(y, m - 1, d + days));
}

export function shortDate(iso: string): string {
  const [, m, d] = iso.split('-');
  return `${d}/${m}`;
}
