# What's Happening Right Now & What You Need to Do

## Already Running
The 500-clip analysis batch is running RIGHT NOW in the background. It's analyzing new clips through Gemini and saving results. Expected to process 400-450 clips (some oversized full-match recordings will be skipped).

**You don't need to do anything for this.** It's running.

---

## Three Things Bill Needs to Do (total: 15 minutes)

### 1. Create Supabase Account (5 min)
Go to https://supabase.com → Sign up → Create a project named `pickle-daas`

Once created, go to **Settings → API** and copy:
- **Project URL** (looks like `https://xxx.supabase.co`)
- **service_role key** (the longer one, NOT the anon key)

Paste the service_role key into `PICKLE-DAAS/.env` on the line that says:
```
SUPABASE_SERVICE_KEY=paste_it_here
```

That's it. Claude Code does the rest — runs the schema, pushes all data, wires it into the Lovable app.

### 2. Open Claude Code CLI Tonight (5 min)
Navigate to the PICKLE-DAAS folder and paste the overnight prompt:

```bash
cd ~/path/to/PICKLE-DAAS
claude
```

Then paste the contents of `OVERNIGHT-500-CLIP-PROMPT.md` — it tells Claude Code to:
- Check on the batch run (may be done by then)
- Aggregate all player DNA profiles
- Generate brand intelligence reports
- Publish updated data to GitHub Pages
- Push everything to Supabase

### 3. Share Your COURTANA_TOKEN Status (1 min)
Your JWT token expires around Apr 20. The anon endpoint (which the batch uses) doesn't need it. But for future authenticated API calls, check if it's still valid by running:

```bash
curl -s -o /dev/null -w "%{http_code}" -H "Accept: application/json" -H "Authorization: Bearer $(grep COURTANA_TOKEN .env | cut -d= -f2)" https://courtana.com/accounts/profiles/current/
```

If it returns `200`, you're good. If `401`, you'll need to grab a fresh token from courtana.com DevTools.

---

## What Claude Code Will Do Overnight (autonomous)

1. ✅ Aggregate all ~590 clips into unified corpus export
2. ✅ Generate player DNA profiles for every player detected
3. ✅ Build brand intelligence reports (JOOLA, LIFE TIME, Recovery Cave)
4. ✅ Publish updated JSON files to GitHub Pages (the Lovable app auto-refreshes)
5. ✅ Push all analyses to Supabase (if service key is set)
6. ✅ Publish missing data files: creative-badges.json, dashboard-stats.json, player-profiles.json
7. ✅ Generate overnight summary report

---

## After Tonight: What Changes

- Lovable DaaS Explorer shows ~590 clips instead of 101
- Brand detection covers dozens of brands across 590 clips
- Player profiles have statistical significance (not just 12 clips per player)
- Supabase API is live — anyone can query the data
- You can walk into any investor or brand meeting and say: "We've analyzed 590 pickleball clips — the largest structured dataset in the sport."
