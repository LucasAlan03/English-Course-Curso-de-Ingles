// The public demo is served from a sub-path (GitHub Pages), so the build needs a baseUrl.
// Normal runs are unchanged: without EXPO_PUBLIC_DEMO_BASE this returns app.json as is.
module.exports = ({ config }) => {
  const base = process.env.EXPO_PUBLIC_DEMO_BASE;
  if (!base) return config;
  return { ...config, experiments: { ...config.experiments, baseUrl: base } };
};
