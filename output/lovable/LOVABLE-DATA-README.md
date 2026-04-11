# Lovable Data Import Guide — Discovery V2

## Files

| File | Purpose |
|------|---------|
| `discovery-v2-export.json` | Complete data package for Lovable dashboard |
| `dashboard-data.json` | Legacy V1 dashboard data |
| `clips-metadata.json` | Clip-level metadata |
| `player-dna.json` | Player profile data |
| `brand-registry.json` | Brand detection registry |

## discovery-v2-export.json Structure

```json
{
  "meta": { ... },           // Generation metadata, version, clip count
  "corpus": [ ... ],         // Raw corpus export (96 items)
  "discoveries": [ ... ],    // 11 ranked discoveries with V2 honesty metadata
  "census": { ... },         // V2 census: clips, players, shots, brands
  "scaling": [ ... ],        // 3 revenue scenarios (conservative/base/optimistic)
  "verification": { ... },   // Re-analysis agreement rates
  "data_quality": { ... },   // Venue distribution, bias flags, confidence caps
  "comparables": { ... }     // Sportradar, StatsBomb, ShotTracker, Hudl pricing
}
```

## Field Mapping to UI Components

| JSON Path | UI Component |
|-----------|-------------|
| `meta.clips_analyzed` | Hero stat card |
| `meta.pipeline_cost_per_clip` | Cost metric display |
| `discoveries[].headline` | Discovery card title |
| `discoveries[].confidence.capped` | Confidence badge (color by value) |
| `discoveries[].verification_badge` | Status chip (verified/needs_data/bias/unreliable) |
| `discoveries[].counter_argument` | Expandable section per card |
| `discoveries[].pricing` | Pricing detail per card |
| `verification.brand_agreement` | Verification dashboard gauge |
| `scaling[].mrr_month12` | Revenue projection chart |
| `data_quality.bias_flags` | Alert banner component |
| `comparables` | Pricing comparison table |

## How to Swap from Hardcoded to Supabase

1. Deploy Supabase instance (see `supabase/SUPABASE-SETUP-GUIDE.md`)
2. Push data: `python supabase/push-analysis-to-db.py`
3. In Lovable, replace static JSON imports with Supabase client queries:
   ```ts
   // Before (hardcoded)
   import data from './discovery-v2-export.json'

   // After (Supabase)
   const { data } = await supabase.from('discoveries').select('*').order('rank')
   ```
4. Tables: `clip_analyses`, `discoveries`, `verification_results`, `census_snapshots`
5. RLS policy: public read, service-key write
