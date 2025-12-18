# INSTRUCTIONS FOR CLAUDE — CONTENT SYSTEM IMPLEMENTATION

Implement the following exactly:

1. Use `content/` as the single source of truth for all marketing-related copy.
2. Never hardcode text inside components — always load from JSON.
3. Build `/api/marketing` to load and merge JSON from content/marketing.
4. Build `/api/content/[slug]` for SEO, ads, email templates, etc.
5. Build admin editor route protected by ADMIN_TOKEN.
6. Implement cache with ?reload=true bypass.
7. Add fallback to local JSON if backend fails (frontend SSR/CSR).
8. Follow DEVELOPER_HANDOFF.md for coding patterns.

