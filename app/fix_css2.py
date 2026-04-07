#!/usr/bin/env python3
"""Fix hero layout and add particles to sections."""
with open('/Users/golden-tenet/claw-spaces/Phoebe/Projects/openclaw-model-arena/app/src/styles/theme.css') as f:
    content = f.read()

# Hero: make canvas an accent background, not full overlay
old_hero_canvas = """.hero-canvas-wrap {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}"""
new_hero_canvas = """.hero-canvas-wrap {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.5;
}"""
content = content.replace(old_hero_canvas, new_hero_canvas)

# Hero: give content a proper dark background so text is readable
old_hero_content = """.hero-content {
  position: relative;
  z-index: 1;
  text-align: left;
  width: 100%;
  max-width: 680px;
  padding: calc(var(--nav-h) + 2rem) clamp(1rem, 4vw, 2.5rem) 3rem;
}"""
new_hero_content = """.hero-content {
  position: relative;
  z-index: 1;
  text-align: left;
  width: 100%;
  max-width: 640px;
  padding: calc(var(--nav-h) + 3rem) clamp(1rem, 4vw, 2.5rem) 3rem;
  background: linear-gradient(
    105deg,
    rgba(4,5,10,0.98) 0%,
    rgba(4,5,10,0.85) 50%,
    rgba(4,5,10,0.4) 100%
  );
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
}"""
content = content.replace(old_hero_content, new_hero_content)

# Hero kicker: even smaller
old_hero_kicker = """.hero-kicker {
  font-family: var(--font-ui);
  font-size: 0.7rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--blue);
  margin-bottom: 1rem;
  opacity: 0.7;
}"""
new_hero_kicker = """.hero-kicker {
  font-family: var(--font-ui);
  font-size: 0.68rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: var(--blue);
  margin-bottom: 0.75rem;
  opacity: 0.6;
}"""
content = content.replace(old_hero_kicker, new_hero_kicker)

# Hero headline: smaller but still prominent
old_hero_headline = """.hero-headline {
  font-family: var(--font-display);
  font-size: clamp(2.8rem, 7vw, 5rem);
  font-weight: 400;
  line-height: 1.05;
  letter-spacing: 0.03em;
  color: var(--text-primary);
  margin-bottom: 1.2rem;
  text-shadow: 0 0 40px rgba(91, 200, 255, 0.15);
}"""
new_hero_headline = """.hero-headline {
  font-family: var(--font-display);
  font-size: clamp(2rem, 5vw, 3.5rem);
  font-weight: 400;
  line-height: 1.1;
  letter-spacing: 0.03em;
  color: var(--text-primary);
  margin-bottom: 1rem;
  text-shadow: 0 0 40px rgba(91, 200, 255, 0.12);
}"""
content = content.replace(old_hero_headline, new_hero_headline)

# Hero KPIs: smaller, compact
old_hero_kpis = """.hero-kpis {
  display: flex;
  gap: 2.5rem;
}"""
new_hero_kpis = """.hero-kpis {
  display: flex;
  gap: 2rem;
  margin-top: 0.5rem;
}"""
content = content.replace(old_hero_kpis, new_hero_kpis)

old_hero_kpi_value = """.hero-kpi-value {
  font-family: var(--font-display);
  font-size: clamp(1.6rem, 3vw, 2.5rem);
  font-weight: 700;
  color: var(--gold);
  line-height: 1;
  display: block;
}"""
new_hero_kpi_value = """.hero-kpi-value {
  font-family: var(--font-display);
  font-size: clamp(1.1rem, 2.5vw, 1.8rem);
  font-weight: 700;
  color: var(--gold);
  line-height: 1;
  display: block;
  letter-spacing: 0.02em;
}"""
content = content.replace(old_hero_kpi_value, new_hero_kpi_value)

# Score ribbon: add particle canvas behind it
old_score_ribbon = """.score-ribbon {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}"""
new_score_ribbon = """.score-ribbon {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  background: rgba(10, 13, 20, 0.95);
  position: relative;
}
.score-ribbon::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse at 30% 50%, rgba(91,200,255,0.04) 0%, transparent 70%);
  pointer-events: none;
}"""
content = content.replace(old_score_ribbon, new_score_ribbon)

# Ranking section: add subtle particle accent
old_ranking_section = """.ranking-section {
  position: relative;
}"""
new_ranking_section = """.ranking-section {
  position: relative;
}
.ranking-section::before {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 40%;
  height: 100%;
  background: radial-gradient(ellipse at right center, rgba(91,200,255,0.03) 0%, transparent 70%);
  pointer-events: none;
  z-index: 0;
}
.ranking-section .container { position: relative; z-index: 1; }"""
content = content.replace(old_ranking_section, new_ranking_section)

# Tasks section: add subtle glow
old_tasks_section = """.tasks-section {
  position: relative;
}"""
new_tasks_section = """.tasks-section {
  position: relative;
}
.tasks-section::before {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 50%;
  height: 60%;
  background: radial-gradient(ellipse at left bottom, rgba(245,200,66,0.03) 0%, transparent 70%);
  pointer-events: none;
}"""
content = content.replace(old_tasks_section, new_tasks_section)

# Failures section: subtle red glow
old_failures_section = """.failures-section {
  position: relative;
}"""
new_failures_section = """.failures-section {
  position: relative;
}
.failures-section::before {
  content: '';
  position: absolute;
  top: 20%;
  right: 5%;
  width: 30%;
  height: 60%;
  background: radial-gradient(ellipse, rgba(255,95,95,0.03) 0%, transparent 70%);
  pointer-events: none;
}"""
content = content.replace(old_failures_section, new_failures_section)

# Evidence section: subtle blue glow
old_evidence_section = """.evidence-section {
  position: relative;
}"""
new_evidence_section = """.evidence-section {
  position: relative;
}
.evidence-section::before {
  content: '';
  position: absolute;
  bottom: 0;
  right: 10%;
  width: 40%;
  height: 80%;
  background: radial-gradient(ellipse at right, rgba(91,200,255,0.04) 0%, transparent 70%);
  pointer-events: none;
}"""
content = content.replace(old_evidence_section, new_evidence_section)

# Verdict section canvas: more visible
old_verdict_canvas = """.verdict-canvas-wrap {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.12;
}"""
new_verdict_canvas = """.verdict-canvas-wrap {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.2;
}"""
content = content.replace(old_verdict_canvas, new_verdict_canvas)

# Verdict section: full-width particle canvas
old_verdict_section = """.verdict-section {
  position: relative;
  text-align: center;
  overflow: hidden;
}"""
new_verdict_section = """.verdict-section {
  position: relative;
  text-align: center;
  overflow: hidden;
  background: var(--surface);
}"""
content = content.replace(old_verdict_section, new_verdict_section)

# Nav brand: slightly more prominent
old_nav_brand = """.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-family: var(--font-display);
  font-size: 1.5rem;
  letter-spacing: 0.08em;
  color: var(--text-primary);
}"""
new_nav_brand = """.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-family: var(--font-display);
  font-size: 1.3rem;
  letter-spacing: 0.12em;
  color: var(--text-primary);
}"""
content = content.replace(old_nav_brand, new_nav_brand)

# Hero section: make sure it fills viewport
old_hero_section = """.hero-section {
  position: relative;
  min-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}"""
new_hero_section = """.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: stretch;
  overflow: hidden;
}"""
content = content.replace(old_hero_section, new_hero_section)

# Score ribbon: tighter
old_score_ribbon_item = """.score-ribbon-item {
  padding: 1.75rem 1.5rem;
  text-align: center;
}"""
new_score_ribbon_item = """.score-ribbon-item {
  padding: 1.25rem 1.5rem;
  text-align: center;
}"""
content = content.replace(old_score_ribbon_item, new_score_ribbon_item)

old_score_ribbon_value = """.score-ribbon-value {
  font-family: var(--font-display);
  font-size: clamp(1.4rem, 3vw, 2.2rem);
  font-weight: 700;
  color: var(--blue);
  line-height: 1.1;
  letter-spacing: 0.02em;
}"""
new_score_ribbon_value = """.score-ribbon-value {
  font-family: var(--font-display);
  font-size: clamp(1.2rem, 2.5vw, 1.8rem);
  font-weight: 700;
  color: var(--blue);
  line-height: 1.1;
  letter-spacing: 0.02em;
}"""
content = content.replace(old_score_ribbon_value, new_score_ribbon_value)

open('/Users/golden-tenet/claw-spaces/Phoebe/Projects/openclaw-model-arena/app/src/styles/theme.css', 'w').write(content)
print("Done")
