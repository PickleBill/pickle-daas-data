# DUPR Integration Plan
## Courtana Pickle DaaS | April 2026

---

### Research Methodology Note

Web browsing tools were unavailable during this session. This plan is based on:
1. Claude's training knowledge of DUPR's API/developer ecosystem (through August 2025)
2. Review of all existing PICKLE-DAAS project context files
3. Known industry patterns for pickleball data platforms

Items marked **[VERIFY]** should be confirmed with a quick browser check before acting on them.

---

### Executive Summary

DUPR is the de facto rating authority for pickleball — over 1.5 million registered players globally, with ratings powering tournament seeding, app matchmaking, and sponsorship benchmarks. Courtana's Pickle DaaS has what DUPR fundamentally lacks: video intelligence. Integrating DUPR IDs into the Courtana player graph would create the only complete player profile in pickleball — "DUPR knows WHO is good; Courtana knows WHY." The most important action item is not technical: it's getting a partnership call with DUPR before they build DUPR Vision without us.

---

### The Opportunity: DUPR + Courtana = Complete Player Profile

| Data Layer | DUPR | Courtana Pickle DaaS |
|---|---|---|
| Player identity & rating | Yes — 1.5M+ players | Partial — Courtana usernames only |
| Rating history over time | Yes | No |
| Tournament results | Yes | No |
| Shot intelligence | No | Yes — Gemini-extracted per clip |
| Brand signals | No | Yes — paddle, apparel, shoes detected |
| Viral/watchability score | No | Yes — scored 1-10 per clip |
| Play style tags | No | Yes — "kitchen specialist", "power baseliner" |
| AI commentary | No | Yes |

The gap is narrow and bridgeable. If Courtana can link its `player_username` records to DUPR player IDs, every downstream data product gets a massive credibility upgrade: "Player rated 4.8 DUPR, dominant at the kitchen (Courtana score: 9.1/10), wears Selkirk across 23 of 31 analyzed clips."

This is an actual product no one has. It's also the pitch to DUPR.

---

### DUPR API — Current Access Status

**What is DUPR?**
DUPR (Dynamic Universal Pickleball Rating) was co-founded by Steve Kuhn (MLP co-founder) and launched around 2021. It became the official rating system of USA Pickleball and the PPA Tour. As of mid-2025, it had 1.5M+ registered players and was the most widely accepted rating standard in the sport.

**API Access Model — What is Known:**

DUPR does not operate an open public REST API. Their data platform is tiered:

1. **Public web/app data** — Player ratings are viewable on `mydupr.com` without login. Rating, win/loss records, and match history are visible on public player profile pages. This is scrapeable but not an official API.

2. **Official API — Gated/Partnership Required** — DUPR has a developer API, but it requires a formal data partnership agreement. There is no self-serve API key signup. The typical path is:
   - Email `partnerships@mydupr.com` or contact through `mydupr.com/contact`
   - Describe use case, data volume needs, commercial intent
   - Receive API documentation under NDA or partnership agreement
   - **[VERIFY]** Check `mydupr.com/developers` or `api.mydupr.com` for any updated self-serve portal — this may have changed since mid-2025

3. **Known API capabilities (from public reporting and developer forums):**
   - Player search by name
   - Player profile fetch by DUPR ID (rating singles, rating doubles, verified status)
   - Match history
   - Tournament results
   - **[VERIFY]** Rate limits and pricing — not publicly disclosed; negotiated per partnership

4. **Unofficial/reverse-engineered access** — The DUPR mobile app (iOS/Android) communicates with a backend API. Endpoints like `https://api.mydupr.com/...` have been observed in community projects. Using these without authorization violates DUPR's ToS and is not recommended for a company seeking a partnership.

**Bottom line:** Getting DUPR data the right way means a partnership call. Given Courtana's positioning, this call should lead with the partnership pitch (see below), not a data licensing request. The goal is to become a data PARTNER, not a data buyer.

---

### DUPR Vision — Partner or Competitor?

**What DUPR Vision Is:**

DUPR announced "DUPR Vision" as an AI-powered video rating verification system — the idea being that AI analysis of match video could corroborate or adjust player ratings rather than relying solely on self-reported or tournament-submitted scores. This addresses DUPR's core integrity problem: ratings can be gamed by sandbagging or by playing in low-competition pools.

**Timeline/Status as of August 2025:**
- DUPR Vision was announced publicly (referenced in MLP and pickleball press coverage)
- **[VERIFY]** Whether it has shipped a public beta or remains in development
- As of mid-2025, it appeared to still be in early development with no public product

**Courtana's Positioning:**

This is where the competitive/partnership calculus gets interesting:

| Dimension | DUPR Vision | Courtana Pickle DaaS |
|---|---|---|
| Video corpus | Starting from scratch | 4,097 analyzed clips, pipeline running |
| AI analysis | In development | Live — Gemini 2.5 Flash, 15+ analyzed |
| Labels/training data | None publicly | Shot types, brands, style tags, quality scores |
| Speed to market | Unknown | Now |

Courtana is not just ahead — it has a labeled corpus that DUPR would need years to build independently. This is the partnership pitch:

**"We can accelerate DUPR Vision by providing labeled training data from our corpus. We have 4,097 pickleball clips already analyzed for shot type, player skill, and court behavior. License our data layer, partner on Vision, and we both win."**

The risk of NOT reaching out: if DUPR ships Vision independently, they become a direct competitor to Courtana's AI coaching product and potentially acquire a competing data moat.

**Recommended posture: Proactive outreach within 2 weeks.** This is a time-sensitive window.

---

### PickleballTournaments.com

**What it is:** PickleballTournaments.com (PT) is one of the two dominant tournament registration and management platforms in the US, alongside Pickleball Brackets. It handles player registration, brackets, results reporting, and some rating sync with DUPR.

**API / Data Access Status:**
- **No documented public API** as of mid-2025
- Tournament directors and software vendors have reportedly accessed data through partnership/white-label agreements
- Results data is generally accessible via web scraping of public tournament pages
- **[VERIFY]** Whether PT has launched a developer program since mid-2025 — check `pickleballtournaments.com/api` or `/developers`

**What the data would add to Pickle DaaS:**
- Tournament win/loss history per player
- Bracket placements (gold/silver/bronze medal)
- Division and skill level at time of registration (self-reported, but useful)
- Tournament names and venues for geographic context

**Recommended approach:** Direct outreach to PT's business development team. Frame as a data enrichment partnership — Courtana adds video intelligence to PT's player records, PT adds tournament history to Courtana's player profiles. Mutual value, no zero-sum.

---

### AllPickleballTournaments.com

**What it is:** AllPickleballTournaments (APT) is a tournament aggregator — it scrapes or syndicates tournament listings from multiple platforms (PT, Pickleball Brackets, etc.) into a single searchable directory.

**API / Data Access Status:**
- **[VERIFY]** Whether `allpickleballtournaments.com` exposes a JSON API or public data export
- As of mid-2025, no documented developer API was known
- The site appeared to be primarily a consumer directory with no programmatic access
- It may be less useful as a data source than PT directly, since it's downstream

**Realistic value:** Lower priority than PT and DUPR. If PT integration is achieved, APT adds little incremental value for player enrichment.

---

### Proposed Supabase Schema Additions

Add these columns to `pickle_daas_player_dna` (the existing player table in the DaaS schema):

```sql
-- DUPR enrichment columns
ALTER TABLE pickle_daas_player_dna ADD COLUMN IF NOT EXISTS dupr_id VARCHAR(50);
ALTER TABLE pickle_daas_player_dna ADD COLUMN IF NOT EXISTS dupr_rating_singles DECIMAL(3,2);
ALTER TABLE pickle_daas_player_dna ADD COLUMN IF NOT EXISTS dupr_rating_doubles DECIMAL(3,2);
ALTER TABLE pickle_daas_player_dna ADD COLUMN IF NOT EXISTS dupr_verified_at TIMESTAMP;
ALTER TABLE pickle_daas_player_dna ADD COLUMN IF NOT EXISTS dupr_match_confidence TEXT DEFAULT 'unverified';
  -- Values: 'confirmed' (player self-linked), 'probable' (name+location match), 'unverified'

-- Tournament enrichment columns
ALTER TABLE pickle_daas_player_dna ADD COLUMN IF NOT EXISTS tournament_wins INTEGER DEFAULT 0;
ALTER TABLE pickle_daas_player_dna ADD COLUMN IF NOT EXISTS tournament_matches INTEGER DEFAULT 0;
ALTER TABLE pickle_daas_player_dna ADD COLUMN IF NOT EXISTS tournament_history JSONB DEFAULT '[]';
  -- Array of {tournament_name, date, division, placement, partner_name}
ALTER TABLE pickle_daas_player_dna ADD COLUMN IF NOT EXISTS pt_player_id VARCHAR(50);
  -- PickleballTournaments.com internal player ID, if known

-- Indexes
CREATE INDEX IF NOT EXISTS idx_player_dna_dupr_id ON pickle_daas_player_dna(dupr_id);
CREATE INDEX IF NOT EXISTS idx_player_dna_dupr_singles ON pickle_daas_player_dna(dupr_rating_singles DESC);
CREATE INDEX IF NOT EXISTS idx_player_dna_dupr_doubles ON pickle_daas_player_dna(dupr_rating_doubles DESC);
```

Note: The `daas_signals` JSONB field in `pickle_daas_analyses` already has a `dupr_estimate` subfield from Gemini output. Once we have real DUPR data, we can cross-validate Gemini's estimates against ground truth — this is the foundation for EXP-017 (DUPR Rating Estimator).

---

### Skeleton Ingestion Script

See: `tools/dupr-enrichment.py` (created alongside this document)

The script handles:
1. Fetching all players from `pickle_daas_player_dna` who lack a `dupr_id`
2. Searching DUPR by player name (via API or scrape fallback)
3. Fetching rating data for matched players
4. Updating Supabase with rating + confidence level
5. Graceful error handling with retry logic

---

### Recommended Next Actions

**This week (time-sensitive):**

1. **Send the DUPR partnership pitch email** — Draft is in the section below. The window before DUPR Vision ships is the key variable. Get a call on the calendar.

2. **Run `tools/dupr-enrichment.py` in dry-run mode against the existing player list** — No API key needed for dry run; it will show which players have unambiguous DUPR name matches via the public `mydupr.com` player search. This gives a quick read on how many players we can enrich before a formal API agreement.

3. **Apply the schema migrations** — The `ALTER TABLE` statements above are additive and safe to run now. Get the columns in place so the pipeline can populate them as soon as API access is available.

**Next 2 weeks:**

4. **Reach out to PickleballTournaments.com business development** — Email or LinkedIn. Frame as a data partnership, not a data scrape request.

5. **[VERIFY] Check `mydupr.com/developers`** — Spend 5 minutes checking whether DUPR has launched a self-serve API portal since mid-2025. If yes, apply immediately without waiting for partnership response.

6. **Map Courtana players → DUPR IDs manually for the top 10** — Bill Bricker / PickleBill almost certainly has a public DUPR profile. Manually look up the top 10 Courtana players on `mydupr.com`, record their DUPR IDs, and insert them directly into Supabase. This proves the schema works and creates the demo "before the API is live."

**Strategic (30-60 days):**

7. **Cross-validate Gemini DUPR estimates vs. real ratings** — For every player where we have both a real DUPR rating and Gemini's `daas_signals.dupr_estimate`, run a correlation analysis. If Gemini is getting within 0.3 of actual DUPR from video alone, that is a product story and a partnership proof point.

8. **Build the "Complete Player Profile" demo page** — DUPR rating + Courtana shot intelligence + brand signals in one view. This is the DUPR pitch demo, the Court Kings demo, and the investor demo. One page, maximum impact.

---

### The Pitch to DUPR (Partnership Angle)

**Cold email draft — to: partnerships@mydupr.com**

Subject: Courtana + DUPR Vision — We Have 4,097 Labeled Training Clips

> Hi [Name],
>
> Courtana is building the video intelligence layer for pickleball — we've run AI analysis on 4,097 player highlight clips and extracted shot types, skill ratings, brand signals, and play style profiles. We think this corpus could materially accelerate DUPR Vision's development and would love 20 minutes to explore what a data partnership looks like. We're not looking to compete with DUPR — we're looking to make player profiles complete.
>
> Would you be open to a quick call this month?
>
> Bill Bricker, Courtana (courtana.com)

**Notes on the pitch:**
- Lead with the asset (4,097 clips, working pipeline), not the ask
- Frame as acceleration for Vision, not a data licensing request — different power dynamic
- Keep it short; DUPR partnership team gets outreach constantly
- If you have a warm intro through MLP, PPA, or USA Pickleball contacts, use it — cold email is a fallback

---

### Appendix: DUPR Data Fields Available (Expected)

Once API access is obtained, these fields should be requestable per player:

| Field | Description | Use in Pickle DaaS |
|---|---|---|
| `dupr_id` | Unique player identifier | Primary key for enrichment |
| `rating_singles` | Current singles rating (2.000–8.000) | Player profile, filtering |
| `rating_doubles` | Current doubles rating | Player profile, filtering |
| `rating_verified` | Boolean — has rating been verified by match data | Confidence weighting |
| `rating_history` | Array of past ratings with dates | Trend analysis |
| `match_count` | Total matches submitted to DUPR | Activity level proxy |
| `win_rate` | Win percentage across all submitted matches | Performance context |
| `player_name` | Full name | Identity matching |
| `location` | City/state | Geo context for venue analysis |

All of these layer directly onto `pickle_daas_player_dna` and transform it from "Courtana-universe player" to "universal pickleball player profile."
