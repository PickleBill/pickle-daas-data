# Lovable Prompt 07 — Pickle DaaS Scale Section

## What This Builds
A pitch-closing section at the bottom of the dashboard showing the DaaS scale opportunity.

## Paste This Into Lovable

---

Add a "Pickle DaaS Scale" section at the very bottom of the dashboard, above the footer.

**Full-width dark section (bg #0d1117):**

**Animated counter row (3 stat cards):**
- "4,097 Highlights Analyzed" — animate count up from 0 on scroll-into-view
- "47 Brands Detected" — same animation
- "25+ Players Profiled" — same

**Scale multiplier line:**
- Large text: "4,097 highlights at The Underground."
- Accent line (green): "× 1,000 venues = **4,097,000 data points**"

**Big quote (centered, large, italic):**
> "What would you do with the world's largest pickleball data corpus?"

**CTA:**
- Button: "Talk to us about Pickle DaaS" → mailto:bill@courtana.com
- Subtext: "bill@courtana.com"

Use Mantine `NumberFormatter` or a simple JS counter for the animated numbers.
Trigger animation when section enters viewport (IntersectionObserver).
