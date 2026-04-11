# Lovable Prompt 05 — Ron Burgundy Voice Button

## What This Builds
A speaker button on each highlight card that plays pre-generated or live TTS commentary.

## Paste This Into Lovable

---

Add a voice playback button to each highlight card.

**Button:** Small speaker icon (🔊) in the bottom-right of each thumbnail card.

**On click:**
- If `window.ELEVENLABS_API_KEY` is set: call ElevenLabs API directly from the browser using `announcement_text_for_tts` field from the highlight data
- Otherwise: try to fetch a pre-generated MP3 from the same CDN path as the video but with `.commentary.mp3` extension
- Fallback: use browser's built-in `speechSynthesis.speak()` with the `announcement_text_for_tts` text

**While playing:**
- Show a simple 3-bar waveform animation (CSS keyframes, green bars)
- Speaker icon changes to ⏸ pause icon

**Auto-stop:**
- When video modal opens
- When another card's speaker button is clicked

Keep button subtle (small, bottom-right, slight transparency). This is an easter egg for demos.
