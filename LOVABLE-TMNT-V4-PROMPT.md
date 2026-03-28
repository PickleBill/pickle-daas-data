# Pickle DaaS — TMNT Voice Mode + Full Feature Upgrade
# Paste into picklestats-hub Lovable chat

---

You're upgrading picklestats-hub with three major additions:
1. **TMNT Voice Mode** — full Ninja Turtles broadcast experience
2. **Live ElevenLabs Audio** — fix TTS to actually play audio
3. **Multi-Sport Clip Browser** — sport-classified video grid

Execute all three. Here's the complete spec:

---

## PART 1: FIX LIVE ELEVENLABS AUDIO

The current "Play Voice" buttons don't produce actual audio. Fix this now.

The existing Supabase edge function `elevenlabs-tts` should already exist. If it doesn't, create it:

```typescript
// supabase/functions/elevenlabs-tts/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
}

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS })

  const { text, voice_id, stability = 0.6, similarity_boost = 0.8 } = await req.json()

  const resp = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${voice_id}`, {
    method: "POST",
    headers: {
      "Accept": "audio/mpeg",
      "Content-Type": "application/json",
      "xi-api-key": Deno.env.get("ELEVENLABS_API_KEY") || "",
    },
    body: JSON.stringify({
      text,
      model_id: "eleven_turbo_v2_5",
      voice_settings: { stability, similarity_boost }
    })
  })

  if (!resp.ok) {
    return new Response(JSON.stringify({ error: await resp.text() }), {
      status: 500, headers: { ...CORS, "Content-Type": "application/json" }
    })
  }

  const audioBuffer = await resp.arrayBuffer()
  return new Response(audioBuffer, {
    headers: { ...CORS, "Content-Type": "audio/mpeg" }
  })
})
```

In the React components, when "Play Voice" is clicked:

```typescript
const playElevenLabsVoice = async (text: string, voiceId: string) => {
  setIsPlaying(true)
  try {
    const { data, error } = await supabase.functions.invoke('elevenlabs-tts', {
      body: { text, voice_id: voiceId, stability: 0.6, similarity_boost: 0.8 }
    })
    if (error) throw error

    // Convert to blob and play
    const blob = new Blob([data], { type: 'audio/mpeg' })
    const url = URL.createObjectURL(blob)
    const audio = new Audio(url)
    audio.onended = () => { setIsPlaying(false); URL.revokeObjectURL(url) }
    await audio.play()
  } catch (err) {
    // Fallback to speechSynthesis
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.onend = () => setIsPlaying(false)
    speechSynthesis.speak(utterance)
  }
}
```

Voice IDs:
- ESPN: `TxGEqnHWrfWFTfGW9XjX`
- Hype: `ErXwobaYiN019PkySvjV`
- Ron Burgundy: `pNInz6obpgDQGcFmaJgB`
- Chuck Norris: `VR6AewLTigWG4xSOukaG`
- Michelangelo: `ErXwobaYiN019PkySvjV` (same as Hype — high energy)
- Leonardo: `TxGEqnHWrfWFTfGW9XjX` (same as ESPN — calm authority)
- Raphael: `VR6AewLTigWG4xSOukaG` (same as Chuck — tough)
- Donatello: `pNInz6obpgDQGcFmaJgB` (same as Ron — smart/precise)
- Splinter: `EXAVITQu4vr4xnSDxMaL` (Bella — wise, measured)

---

## PART 2: TMNT VOICE MODE

Add a "🐢 TMNT MODE" toggle button to the nav bar (right side, green). When toggled:

### Theme Changes (TMNT mode active):
- Background shifts from `#0a0f1a` to `#0a0f0a` (green-black tint)
- Card borders switch from green to TMNT character colors
- Header shows `🐢 COWABUNGA SPORTS INTEL 🍕` subtitle
- YouTube music embed activates (muted, user can unmute): `https://www.youtube.com/embed/LFhN8vRBSzs?autoplay=1&mute=1`

### TMNT Voice Tab Row (replaces or supplements existing voice tabs):
When TMNT mode is ON, add 5 new voice tabs:

| Tab | Emoji | Color | ElevenLabs Voice | Personality |
|-----|-------|-------|-----------------|-------------|
| LEO | 🐢 | blue | TxGEqnHWrfWFTfGW9XjX | Calm, disciplined, martial arts wisdom |
| RAPH | 🔴 | red | VR6AewLTigWG4xSOukaG | Sarcastic, tough, Brooklyn energy |
| MIKEY | 🟠 | orange | ErXwobaYiN019PkySvjV | HYPER, surfer, pizza obsessed |
| DON | 🟣 | purple | pNInz6obpgDQGcFmaJgB | Nerdy, analytical, precise stats |
| SPLINTER | 🥋 | gold | EXAVITQu4vr4xnSDxMaL | Wise, haiku-like, deep wisdom |

### TMNT Commentary Generator
When a clip is selected and TMNT mode is ON, generate commentary by transforming the existing clip commentary through each turtle's persona:

For each voice tab, show the turtle's take on the clip. Use the `commentary` object from clips-metadata.json as the base, then apply persona:
- Leo → use `neutral_announcer_espn` as base, prepend "Discipline and focus..."
- Raph → use `hype_announcer_charged` as base, transform to Brooklyn sarcastic
- Mikey → use `hype_announcer_charged` as base, add COWABUNGA/RADICAL/DUDE
- Don → use `coaching_breakdown` as base, add statistics and tech specs
- Splinter → use `coaching_breakdown` as base, transform to Zen wisdom/haiku

### "🍕 PIZZA TIME" Easter Egg
A small pizza emoji button in the corner. Clicking it:
1. Shows "PIZZA DELIVERY IN PROGRESS 🍕" toast for 3 seconds
2. Plays Web Audio API sound: `audioCtx.oscillator(440 → 880hz, 0.3s, triangle wave)`
3. Confetti burst of 🍕 emojis (CSS animation, 10 pizza emojis scatter from click point)

---

## PART 3: MULTI-SPORT CLIP BROWSER

Add a new page/tab called **"Sports"** between Brands and Voice Lab.

### Sport Filter Bar (top)
Horizontal pill buttons: `🥒 Pickleball (8)` | `🏒 Hockey (2)` | `⛳ Golf (2)` | `🏀 All Sports`

Clicking a sport filters the grid below.

### Sport Card Grid
Same card design as Highlights page but with sport icon overlay in top-left corner (instead of viral score).

Sport icon color coding:
- Pickleball: 🥒 green
- Hockey: 🏒 blue
- Golf: ⛳ yellow-green

### Sport DNA Card (right sidebar on desktop)
When a sport filter is selected, show a sport-specific stat card:
- Pickleball: "8 clips · avg quality 7.3 · top brand JOOLA · dominant style: Banger"
- Hockey: "2 clips · avg quality 8.5 · top brand Bauer · dominant style: Power Shot"
- Golf: "2 clips · avg quality 6.5 · top brand Callaway · dominant style: Precision"

Fetch sport data from:
`https://raw.githubusercontent.com/PickleBill/pickle-daas-data/main/output/sport-classified-clips.json`

With hardcoded fallback data if fetch fails.

---

## PART 4: DESIGN UPGRADES

### Interactive Highlights Grid
- Video cards auto-play on hover (muted), pause on leave — smooth transition
- Quality score chip animates (count up from 0 to final value on card mount)
- Story arc badge: shimmer animation when card first loads

### Dashboard Score Strip
- 4 score chips animate sliding in from below on page load (staggered 100ms)
- Hovering a chip shows tooltip: "Quality: How production-ready is this clip for broadcast"

### Commentary Panel
- Text appears character-by-character (typewriter effect, 20ms per char) when switching tabs
- Waveform bars pulse while audio is playing (match the audio amplitude if possible)

### Brands Page
- Brand presence bars animate filling from 0% to final % on page load
- Clicking a brand card expands to show which specific clips contain that brand

### Mobile Nav
- Bottom tab bar on mobile: 5 icons (📊 Dashboard | 🎬 Highlights | 🏃 DNA | 🏷️ Brands | 🐢 Sports)
- Active tab: green icon + small green dot underneath

---

## IMPLEMENTATION ORDER

1. Fix ElevenLabs edge function + React audio playback (30 min)
2. Add Sports page with sport filter + classified clips (20 min)
3. Add TMNT mode toggle + voice tabs (25 min)
4. Add pizza easter egg (5 min)
5. Apply design animations (15 min)
6. Mobile nav bar (10 min)

Build everything. Ship it.
