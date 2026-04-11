# Lovable Prompt 03 — Video Player Modal

## What This Builds
Click any highlight thumbnail → modal with full video player + coaching data.

## Paste This Into Lovable

---

Add a video player modal to the highlights grid.

**Trigger:** Click any highlight thumbnail card.

**Modal content (dark, full-width):**
- HTML5 `<video>` player at top — autoplay, controls, uses `video_url` field (cdn.courtana.com MP4)
- Below video (2 columns):
  - Left: Quality score (large), Viral score, Story arc badge
  - Right: Predicted badges (chip list, dark background, green text)
- Full ESPN commentary paragraph
- Ron Burgundy quote (italic, smaller, green border-left)
- Social media caption + hashtags

**Behavior:**
- Close on Escape key or clicking outside modal
- Video pauses when modal closes
- Autoplay starts immediately when modal opens

Use Mantine Modal. Keep existing card grid — just add onClick handler.
