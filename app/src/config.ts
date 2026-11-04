// Set these in app/.env (see .env.example). EXPO_PUBLIC_* values are read at build time.
export const BASE_URL = (process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');
export const API_TOKEN = process.env.EXPO_PUBLIC_API_TOKEN ?? 'change-me';
