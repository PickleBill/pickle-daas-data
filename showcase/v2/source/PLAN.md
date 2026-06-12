# Bill Bricker — Living Portfolio (v2) · Plan & Architecture

The magical roll-up: one home that lets each visitor **take their own journey** — skim the story,
or open the workshop and dig into the proof. Editorial/literary/warm world (Spectral serif, paper,
ridge-lines), not the cinematic-dark anti-pattern.

## The journey architecture

```
        THE CLIMB  (index.html)              ← front door · the story
        a 20-year ascent you click through
        ┌───────────────┬───────────────┐
        ▼               ▼               ▼
   THE WORK         RÉSUMÉ          DESIGN LAB
   (work.html)      (resume.html)   (design-lab/)
   proof engine     copy + links    the 5 directions
   room (bricker.os)                as reference
        │
        ├─ Operating companies   → Courtana.com · Dreamship.com
        ├─ Sales/GTM & AI collateral → Courtana Venue Connect
        ├─ Enterprise builds     → HeadsUpTime · NaughtyData · Litigator
        ├─ VibeCo & ecosystem    → vibeco.lovable.app (+ /simulate) · 40 apps
        └─ Pickle DaaS           → 6 v4 dashboards + intel card
```

Three reader speeds, one site:
- **90 seconds** (recruiter/investor): The Climb's rising ridge-line + the live pins.
- **The wanderer**: clicks pins, reads the human + professional stories (incl. The Long Walk).
- **The deep-diver** (an interviewer who's hooked): opens The Work, explores real proof by theme.

## Done (v2.0)
- [x] Pivoted to the editorial/warm world the samples point to.
- [x] The Climb wired with real metrics + live links (Courtana, Dreamship, Pickle, VibeCo) + a VibeCo flag.
- [x] The Work (bricker.os) rebuilt as the proof engine room — every real asset linked, by theme.
- [x] Résumé updated: contact (bricker3@gmail.com · 908-601-8152), asset links, nav.
- [x] Design Lab: all 5 sample directions saved + a navigable, annotated index.
- [x] content.json source of truth (this folder).

## Next (in priority order)
1. **Real URLs** for the missing builds (see content.json open_questions): ecommerce build, the 12-yr-old's app, FactFudge, The Load, AI cooking, the VibeCo build-ecosystem gallery.
2. **Clean domain** — billbricker.com (or a dedicated repo) to replace the github.io path.
3. **VibeCo guided journey** — a pre-populated walkthrough of the 11-agent simulator (Bill's stated intention).
4. **Mobile polish** on The Climb (the chart is desktop-first; verify pins/labels on phones).
5. **The Work → richer case studies** for the two interview-critical assets (Venue Connect, the Google deal).
6. **LinkedIn + outreach**, generated from this same source.

## Editing notes
- Regenerate by editing `content.json`, then re-running the transforms (or hand-edit the data blocks
  in index.html / work.html — the `NODES` object and the `.visuals` rail respectively).
- Keep `modeled_DO_NOT_PUBLISH` figures out of every public artifact.
- The five design-lab files are frozen reference; the live site is index/work/resume.
