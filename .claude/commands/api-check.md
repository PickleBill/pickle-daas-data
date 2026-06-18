---
description: Verify the Courtana API is up before a batch run
---
Run the pre-batch health check from CLAUDE.md and report the result:

`curl -s -o /dev/null -w "%{http_code}" -H "Accept: application/json" "https://courtana.com/app/anon-highlight-groups/?page_size=1"`

A `200` means the API is up — proceed. Anything else means it's down — stop and report it. Reminders: the base domain is always `courtana.com` (NEVER `api.courtana.com`), the `Accept: application/json` header is required or you get HTML back, and never use the `next` pagination field (port 443 bug) — construct `?page=N&page_size=100` instead.
