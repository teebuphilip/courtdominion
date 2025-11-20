Short Answers for Claude:

- Use minimal, clean, data-first design.
- Primary color: #3B82F6.
- Dark theme background: #0F172A.
- Navigation: Dashboard, Projections, Lineup Optimizer, Waiver Wire, About, Blog (future), Settings.
- Users do NOT need a league to browse.
- Load all text from JSON in /content; no hardcoded text.
- API: /api/marketing + /api/content/[slug].
- Cache: 5 minutes, reload via ?reload=true.
- Admin editor must write JSON back to filesystem.
- Fallback to local JSON if backend unavailable.
- All 39 questions fully answered in the attached full document.

Message to send Claude:
"Claude, here are my short answers. Detailed full requirements are in the attached file. Build everything exactly following the file. Do NOT ask clarifying questions."
