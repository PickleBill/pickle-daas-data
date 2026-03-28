# Lovable Prompt 02 — Wire Live Courtana API

## What This Does
Replaces the static JSON import with live Courtana data via Supabase Edge Function proxy.

## Prerequisites
- Supabase project with `courtana-proxy` Edge Function deployed
- SUPABASE_URL set in Lovable env vars

## Paste This Into Lovable

---

Connect this dashboard to live Courtana data. Replace ALL static/mock data with these API calls:

**Supabase proxy URL:** `{VITE_SUPABASE_URL}/functions/v1/courtana-proxy`

Fetch highlight groups:
```
GET {proxy}?endpoint=/app/highlight-groups/?page_size=20
```

Fetch leaderboard (for player rank/XP):
```
GET {proxy}?endpoint=/accounts/profiles/action_get_leaderboard/
```

**Changes to make:**
1. Add a `useEffect` to fetch data on mount
2. Show Mantine `Skeleton` loading state while fetching (match the card dimensions)
3. Add error state with a "Retry" button if fetch fails
4. Keep the exact same component structure — only the data source changes
5. Store fetched data in React state, replace the static const

The live data will have real PickleBill thumbnails from cdn.courtana.com and real video URLs.
