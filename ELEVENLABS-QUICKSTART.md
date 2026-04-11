# ElevenLabs Quick Start — No Code Required First

## The 5-Minute No-Code Test (Do This Tonight)

**Goal:** Hear Ron Burgundy announce one of your highlights. No Python, no FFmpeg, no setup.

### Step 1 — Get the commentary text
Run the Gemini analyzer on any single clip. In the output JSON, grab this field:
```json
"commentary": {
  "ron_burgundy_voice": "Stay classy, Seven Oaks. PickleBill just sent that drive back harder than the truth, and frankly, I'm not even mad."
}
```
Or use `announcement_text_for_tts` — it's cleaned up for voice (no special characters).

### Step 2 — Go to ElevenLabs
1. Go to **elevenlabs.io** → Sign in (free tier works for testing)
2. Click **"Text to Speech"** in the left nav
3. Paste the text from the JSON
4. Pick a voice — for Ron Burgundy energy, try:
   - **"Adam"** — authoritative, deep, slightly pompous = closest to Ron
   - **"Bill"** — ironic given the name
   - **"Daniel"** — British authority (works surprisingly well)
5. Hit **Generate** → **Download MP3**

### Step 3 — Merge with video (Mac, no code)
Open **iMovie** (free, already on your Mac):
1. Import your highlight MP4 (grab from cdn.courtana.com URL in the analysis JSON)
2. Drag the MP3 into the timeline as audio
3. Mute the original audio track if you want clean commentary
4. Export → Share → File

**Total time: ~10 minutes. You'll have a highlight clip with Ron Burgundy announcing it.**

---

## Voice Recommendations by Use Case

| Use Case | ElevenLabs Voice | Why |
|----------|-----------------|-----|
| Ron Burgundy | Adam | Deep, confident, slightly full of himself |
| ESPN Broadcast | Daniel (British) | Authority + gravitas |
| Hype/Hype Beast | Liam | Energetic, younger energy |
| Coaching Breakdown | George | Measured, instructional |
| Chuck Norris | Arnold (clone) | Third-person legendary energy |
| Social/TikTok | Bella | Punchy, quick, engaging |

---

## Voice IDs for the Code Pipeline (TASK 008)

These are real ElevenLabs voice IDs as of early 2026 — verify via `/v1/voices` first:

```python
VOICE_PRESETS = {
    "ron_burgundy": "pNInz6obpgDQGcFmaJgB",  # Adam — deep, authoritative
    "espn":         "onwK4e9ZLuTAKqWW03F9",  # Daniel — broadcast quality
    "hype":         "VR6AewLTigWG4xSOukaG",  # Arnold — high energy
    "coaching":     "EXAVITQu4vr4xnSDxMaL",  # Bella — clear, instructional
    "chuck_norris": "nPczCjzI2devNBz1zQrb",  # Patrick — commanding
}
```

**Note:** Always call `GET https://api.elevenlabs.io/v1/voices` first to get current voice IDs — they can change.

---

## The Full Automated Pipeline (Code Path)

Once TASK 008 is built, the full flow looks like this:

```bash
# 1. Analyze a clip
python pickle-daas-gemini-analyzer.py --url "https://cdn.courtana.com/.../clip.mp4"

# 2. Generate voice (reads the analysis JSON automatically)
python elevenlabs-voice-pipeline.py \
  --analysis ./output/test-001/analysis_*.json \
  --voice ron_burgundy \
  --merge-video  # automatically downloads original + merges with FFmpeg

# Output: analysis_XXXXX_with_voice_ron_burgundy.mp4
```

**What happens:**
1. Script reads `commentary.announcement_text_for_tts` from the JSON
2. Calls ElevenLabs API → saves `commentary_ron_burgundy.mp3`
3. Downloads original video from CDN URL stored in JSON
4. Calls FFmpeg: `ffmpeg -i original.mp4 -i commentary.mp3 -c:v copy -map 0:v -map 1:a -shortest output.mp4`
5. Saves final video file

**FFmpeg install (if not already):**
```bash
brew install ffmpeg  # Mac
```

---

## Cost Estimates

| Action | ElevenLabs Cost |
|--------|----------------|
| 30-second commentary (avg ~150 words) | ~1,500 characters → ~$0.02 |
| 20 clips with commentary | ~$0.40 |
| 4,097 clips (full corpus) | ~$82 |

Free tier gives 10,000 characters/month — enough for ~65 test clips.

---

## Demo Moment Script

**When you're in the Court Kings meeting with Rich + Bryan:**

1. Pull up the PickleBill dashboard in Lovable
2. Click on a highlight → video plays
3. Hit the "🎙️ Ron Burgundy" button (or play the pre-generated MP3)
4. Ron Burgundy announces the highlight in real-time
5. Drop the line: *"Every highlight at Court Kings, announced by whoever you want. ESPN. Chuck Norris. Your own brand voice. One API call."*

That's the product. That's the demo. That's the $500K conversation.
