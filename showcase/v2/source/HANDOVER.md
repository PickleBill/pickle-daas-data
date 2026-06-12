# HANDOVER — Bill Bricker Living Portfolio
_Last updated: 2026-06-12 · written for a fresh Claude thread (or any collaborator) to take this to ultra-pristine._

## 0. Kickoff prompt for a NEW thread (paste this verbatim)

> I'm Bill Bricker. I have a live portfolio system at
> https://picklebill.github.io/pickle-daas-data/showcase/v2/ deployed from the
> `gh-pages` branch of `PickleBill/pickle-daas-data` under `/showcase/v2/`.
> Read `source/HANDOVER.md` and `source/content.json` in that folder FIRST —
> they are the source of truth for facts, design system, open items, and the
> game plan. Never invent metrics beyond content.json. Aesthetic: dark premium
> (#08090a), green→cyan→violet→coral gradients, glass cards, Inter+JetBrains
> Mono, 🥒 brand mark. Target: GTM/partnership roles at frontier AI labs +
> founder/advisory. Work item for this session: [PICK ONE FROM §6].

## 1. Live URLs (all verified 200)

| Page | URL | Status |
|---|---|---|
| Home (master) | …/showcase/v2/ | dark FH-style, interactive operator card |
| Story | …/showcase/v2/climb.html | full-bleed drag chart, chevron cues |
| Work | …/showcase/v2/work.html | interactive terminal + plain-English `ask` |
| Résumé (canonical) | …/showcase/v2/resume-v2.html | DreamWork style, condensed |
| Résumé (ATS/minimal) | …/showcase/v2/resume.html | clean dark |
| Archive | home-warm.html · home-fn.html · design-lab/ | earlier directions |
| Pickle dashboards | …/pickle-daas-data/dashboards/showcase-portal-v4.html | v4 set |

Base prefix: `https://picklebill.github.io/pickle-daas-data/`

## 2. How to deploy
Worktree the `gh-pages` branch of `PickleBill/pickle-daas-data`, replace
`showcase/v2/`, commit, push. Pages CDN takes 1–5 min; verify with a
cache-buster (`?v=timestamp`). Source mirror lives in the deploy folder itself
(`source/`). Never touch other paths on gh-pages (live Pickle DaaS data).

## 3. Design system (keep consistent)
- Canvas `#08090a` · glass `rgba(255,255,255,.045)` + 1px `rgba(255,255,255,.09)` border, 22px radius, blur 20px
- Accents: sage `#8cf0a0` · cyan `#5ee0d6` · violet `#a78bfa` · coral `#ff8a5c` · cream pills `#f3ecdc`
- Type: Inter (800–900 display) + JetBrains Mono (labels/terminal); Climb keeps Spectral/Caveat paper world
- Brand: 🥒 emoji + "Bill Bricker"; nav = Home · Story · Work · Résumé · Email (identical everywhere; 2-line stack <600px; active = cream chip)
- Motion: drifting mesh blobs, scroll-reveal, count-ups, ring draw, sheen sweep, glow hovers

## 4. Product critique (recruiter / hiring-manager / product-leader lens)
**Working well:** differentiated thesis ("sells AND builds") proven by the artifact itself; terminal is a genuine signature; every claim clickable; consistent nav; the interactive operator card.

**Gaps / risks (ranked):**
1. **URL kills credibility** — `picklebill.github.io/pickle-daas-data/showcase/v2/` reads as borrowed real estate. → billbricker.com (~$12) + CNAME. Single biggest upgrade.
2. **No share preview** — link unfurls as plain text on LinkedIn/iMessage. → OG image + meta.
3. **No human evidence** — zero photos/video of Bill. A 60–90s Loom on the Work page would outperform everything else. Recruiters hire faces.
4. **Narrative gaps an interviewer WILL probe:** why Dreamship → Courtana (the transition story is untold); GearLaunch/IntroStellar/WibiData are one-liners (fine on résumé, but `git log` could tell them better); "fka DJ Billygoat" is charming but unexplained everywhere except the terminal easter egg — consider one line of payoff on the Climb.
5. **Screenshot dependency** — thum.io free tier + Clearbit can be slow/flaky. Replace with locally captured PNGs committed to the repo (15 min of work, removes the only flaky dependency).
6. **Numbers consistency** — site now says **20K+ clips**; older Pickle docs say 4,097 analyzed. Decide the defensible number and align site + résumé + dashboards. (Same for "$1M/yr profitable business" if added.)
7. **Stat band final six** — current: 11x · $35M+ · 8-fig · 40+ apps · 20K+ clips · 3 startups. Bill's menu of alternates lives in the 2026-06-12 thread (revenue/capital/sales/build/founding categories).
8. **Climb content** — pins are tight now; consider adding a "Dreamship→Courtana bridge" pin telling the transition story.

## 5. Open items needing BILL's input
- Venue Connect: URL of the **discovery / venue-analytics page** (more compelling than its homepage) for the build-card screenshot.
- Pickle DaaS: preferred hero visual ("shot of the day" CDN asset vs. brand-intel dashboard, currently the latter).
- Confirm/replace **20K+ clips** figure; confirm $350K/36 courts/44-court LOI remain current.
- Real URLs (optional): FactFudge, The Load, AI cooking app, the 12-year-old's app, ecommerce build (VibeCo #model wall covers them today).
- Buy **billbricker.com**; create empty public repo `bill-bricker` (assistant's GitHub scope can't create repos) for a cleaner path even pre-domain.
- DreamWork reference: dreamworkhq.com blocks bots (403) — more screenshots/video if résumé should match it closer.

## 6. Game plan (priority order — pick one per session)
1. **Ship-ready pass:** custom domain + CNAME + OG share image + favicon (🥒) + page `<title>` polish.
2. **Local screenshots:** capture & commit PNGs for all build cards; drop thum.io/Clearbit.
3. **Loom embed:** 60–90s walkthrough of the Pickle investor dashboard on Work + Featured on LinkedIn.
4. **Case studies:** interview-grade Google-deal (STAR) + Venue Connect (connected-AI selling thesis) pages.
5. **LinkedIn package** from content.json: headline ≤220 chars, About ≤2,600, experience blurbs, Featured plan.
6. **Outreach engine:** 3 warm-intro + 2 cold templates, ≤120 words, each leading with one proof point.
7. **Interview story bank:** Google deal, 11x year, 24→<10 restructure, Dreamship→Courtana bridge, "why a lab"; then mock screens.
8. **PDF résumé export** pinned in repo for ATS uploads.

## 7. Claude Design expansion prompts (paste-ready)
**HOME** — "Design a dark premium personal homepage for an AI-native founder/GTM operator (Function Health × Linear). Near-black #08090a, vibrant green→cyan→violet→coral gradients, glass cards, generous margins. Sections: 2-col hero (3-line headline 'Frontier tech evangelist, / vibe pusher, / 0→1 builder' + interactive operator-profile card whose ring metric swaps as 5 skill bars cycle), 6 glowing count-up stats, two equal company cards w/ logos + full site screenshots (teal Courtana / purple Dreamship), screenshot-led VibeCo gallery, Pickle 'data warehouse from video' panel w/ analytics screenshot + 3 metrics, climb teaser, contact. Everything clickable, hover glows, scroll reveals, mobile-first."

**STORY/CLIMB** — "Hand-drawn paper 'ascent' chart of a 20-year career as a full-bleed horizontal canvas, starting at the beginning with pulsing chevron edge cues; drag/swipe to travel; monogram medallion pins w/ glow halos rising to a live summit; tap → field-note bottom-sheet. Spectral + Caveat, sienna ink, minimal copy."

**WORK/TERMINAL** — "Interactive 'bricker-os' terminal: boots with 2-line intro + blinking cursor; two auto-scrolling marquee rows of command chips above (pause on hover, glow on 'ask me anything'); commands incl. whoami, google-deal (STAR), git log (career as commits), builds, pickle-daas, stats, contact, plus a keyword-matched plain-English ask engine with a graceful email fallback. Compact one-line title bar; green flash on command echo."

**RÉSUMÉ** — "DreamWork-style résumé: near-black, animated pink→orange→yellow→purple gradient headline, gradient pill CTAs, mono wordmark w/ blinking cursor, tracked uppercase section labels, chips. Lightweight web companion to a PDF — ≤4 punchy bullets/role, larger type, print-to-PDF clean."

**NEW (not yet built):** OG share card (1200×630, 🥒 + headline + 3 stats) · Google-deal case-study page (editorial, single column, pull quotes) · "Now" page (what I'm shipping this month, JSON-driven).

## 8. Facts guardrails
All metrics live in `source/content.json`. Modeled/projected figures (e.g. Pickle $60M/yr, 1,337:1) are flagged `DO_NOT_PUBLISH` — keep them off public artifacts. Claims must survive "show me."
