# Bill Bricker — Living Portfolio v3 · Architecture & Roadmap

## What changed in v3 (the rethink)
- **One coalesced home** (`index.html`) replacing the Climb-as-front-door: hero + stat strip →
  operating companies (Courtana.com, Dreamship.com) → **VibeCo front and center as "the engine"**
  with its three downstream lanes (GTM collateral / enterprise builds / the wider lab) →
  **Pickle DaaS as the tech proof, explicitly tied back to Courtana's corpus** → story band → contact.
- **The Climb preserved** at `climb.html` as the narrative deep-dive (nav: "The Story").
- **The OS engine room** stays at `work.html`, now with LayupLab, FreakFoSho, and the ecosystem link.
- **Fully-baked résumé** at `resume.html`: complete V7 spine (all 7 Dreamship bullets, GearLaunch,
  IntroStellar, WibiData, IBM, RivalHealth/NWM, education, tools) + 3 new "builder" bullets under
  Courtana linking to Pickle DaaS, VibeCo, and Venue Connect. Print-to-PDF ready.

## The user journey
```
index.html (90-sec read, every claim clickable)
 ├── climb.html      — the 20-year story, pin by pin (incl. The Long Walk)
 ├── work.html       — the engine room: all proof, by theme
 ├── resume.html     — full V7 résumé + live links + Save-as-PDF
 └── design-lab/     — the five design directions (reference)
```

## Production-readiness roadmap (prioritized)

### Blocked on Bill (do these first)
1. **Custom domain** — buy `billbricker.com`, point DNS at GitHub Pages; I add the CNAME.
   The single biggest credibility upgrade; the github.io path reads as borrowed real estate.
2. **Dedicated repo** — create empty public repo `bill-bricker` under PickleBill (my access can't
   create repos); I push this exact site there → cleaner URL even without a domain.
3. **Verify external links render logged-out** — LayupLab links to `/app/dashboard` (may require
   auth on Lovable), Venue Connect, NaughtyData, Litigator `/dashboard`. Open each in an incognito
   window; tell me which gate and I'll swap in screenshots or public routes.
4. **Remaining build URLs** (lower priority): FactFudge, The Load, AI cooking platform, the
   12-year-old's app — or confirm the VibeCo #model wall covers them.

### On me (next build session)
5. **VibeCo guided journey** — pre-populated walkthrough of the simulator so a visitor gets the
   11-agent flow in 30 seconds without typing anything.
6. **Two interview-grade case studies** in work.html — the Google deal (full STAR) and Venue
   Connect (the connected-AI selling thesis). These are the two sharpest interview weapons.
7. **Mobile pass on climb.html** — chart is desktop-first; pins need a phone layout.
8. **OG/social cards** — preview image + meta so the link unfurls well in DMs/LinkedIn.
9. **LinkedIn package** — headline, About, experience blurbs generated from content.json.
10. **PDF résumé artifact** — exported one-pager pinned in the repo for ATS uploads.

### Connectors worth enabling (in Claude settings)
- **Google Drive** — so I can pull decks/screenshots (e.g., Dreamship metrics, Courtana photos)
  directly into case studies.
- **Gmail** (optional, later) — for the outreach-engine phase of the Frontier 2026 playbook.

## Editing
All facts live in `source/content.json`. The modeled Pickle revenue projections stay excluded
from public artifacts.
