# DEVELOPER HANDOFF — CONTENT SYSTEM

## FRONTEND
- Next.js recommended.
- Create `lib/getMarketing.ts` to fetch from API with fallback.
- Components reference content keys, not text literals.

## BACKEND
- Implement GET /api/marketing
- Implement POST /api/marketing (ADMIN_TOKEN protected)
- Implement GET /api/content/[slug]
- Implement POST /api/content/[slug]
- JSON validated and saved to filesystem.

## ADMIN EDITOR UI
- Use simple form with textareas.
- JSON saved via POST to backend.
- Confirm with toast, then reload.

## CACHE
- 5-minute memory cache.
- ?reload=true forces refresh.
