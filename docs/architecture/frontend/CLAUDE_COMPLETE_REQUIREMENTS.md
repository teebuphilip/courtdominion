# CLAUDE COMPLETE REQUIREMENTS

## Core Principles
- All marketing/content text comes from /content JSON files.
- No hardcoded UI text.
- Dark minimal design, data-first.
- Primary accent: #3B82F6.
- Background: #0F172A.

## Navigation
Dashboard, Projections, Lineup Optimizer, Waiver Wire, About, Blog (future), Settings.

## Behavior
- Users may browse without connecting a league.
- API: /api/marketing and /api/content/[slug].
- Cache: 5 minutes. Use ?reload=true to bypass.
- Admin editor writes JSON files to filesystem.
- Fallback: frontend uses local JSON if backend fails.

## 39 Question Answers
1. Purpose: display insights + convert visitors.
2. Audience: fantasy basketball managers.
3. Primary action: view projections and sign up.
4. Secondary actions: explore features, read social proof, join waitlist.
5. Required pages: Home, Projections, Optimizer, Waiver, About, Blog.
6. Auth: optional for MVP.
7. Static/dynamic: hybrid with JSON content.
8. Editable copy without redeploy: YES.
9. CMS: NO.
10. Marketing content loaded from JSON with fallback.
11. Cache: 5 minutes.
12. Cache bypass: ?reload=true.
13. SEO externalized: yes in seo.json.
14. Social posts in repo.
15. Ad copy in repo.
16. Email templates in repo.
17. Blog content in repo.
18. Pro-tier placeholders in repo.
19. Design vibe: minimal, modern, data-first.
20. Primary color: #3B82F6.
21. Logo: text-only MVP.
22. Inspiration sites: BasketballMonster, FanDuel, Bloomberg, Linear.
23. Env vars required.
24. Admin editing API required.
25. Editor: simple JSON editor.
26. Preview via reload.
27. Missing field behavior: safe fallback.
28. JSON validation required.
29. Admin API secured by token.
30. Analytics later.
31. Mobile responsive required.
32. Dark mode optional later.
33. Fetch projections via backend.
34. Loading states required.
35. Error states required.
36. Offline not required.
37. Prefetch content recommended.
38. Pro-tier UI placeholders required.
39. Full documentation included here.

## Implementation Requirements
- Build content loader utilities.
- SSR with fallback to local JSON.
- Editor UI: textarea, save to /api/marketing.
- Backend merges JSON from content.
- Ensure system runs even if content API fails.

END OF FILE
