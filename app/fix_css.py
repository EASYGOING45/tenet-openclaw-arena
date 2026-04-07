#!/usr/bin/env python3
"""Fix CSS for better layout."""
with open('/Users/golden-tenet/claw-spaces/Phoebe/Projects/openclaw-model-arena/app/src/styles/theme.css') as f:
    content = f.read()

# Score ribbon: back to 3 items
content = content.replace(
    "grid-template-columns: repeat(4, 1fr);",
    "grid-template-columns: repeat(3, 1fr);"
)
content = content.replace(
    ".score-ribbon-item {\n  padding: clamp(1.5rem, 4vw, 2.5rem) clamp(1rem, 3vw, 2rem);\n  text-align: center;\n}",
    ".score-ribbon-item {\n  padding: 1.75rem 1.5rem;\n  text-align: center;\n}"
)

# Ranking acts gap
content = content.replace(
    ".ranking-acts {\n  display: grid;\n  grid-template-columns: repeat(3, 1fr);\n  gap: 1rem;\n}",
    ".ranking-acts {\n  display: grid;\n  grid-template-columns: repeat(3, 1fr);\n  gap: 0.75rem;\n  align-items: stretch;\n}"
)

# Ranking act: #1 gets gold accent
content = content.replace(
    """.ranking-act {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1.5rem 1.75rem;
  position: relative;
  overflow: hidden;
  transition: border-color 0.25s, transform 0.25s;
}
.ranking-act:hover {
  border-color: var(--border-hover);
  transform: translateY(-2px);
}""",
    """.ranking-act {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1.25rem 1.5rem;
  position: relative;
  overflow: hidden;
  transition: border-color 0.25s, transform 0.25s, box-shadow 0.25s;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.ranking-act:first-child {
  border-color: rgba(245, 200, 66, 0.35);
  box-shadow: 0 0 20px rgba(245, 200, 66, 0.06);
}
.ranking-act:hover {
  border-color: var(--border-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(91, 200, 255, 0.08);
}"""
)

# Ranking rank: smaller opacity
content = content.replace(
    """.ranking-rank {
  font-family: var(--font-display);
  font-size: 3.5rem;
  color: var(--blue);
  line-height: 1;
  margin-bottom: 0.5rem;
  opacity: 0.85;
}""",
    """.ranking-rank {
  font-family: var(--font-display);
  font-size: 2.5rem;
  color: rgba(91, 200, 255, 0.35);
  line-height: 1;
  margin-bottom: 0.2rem;
}
.ranking-act:first-child .ranking-rank {
  color: rgba(245, 200, 66, 0.45);
}"""
)

# Ranking name
content = content.replace(
    """.ranking-name {
  font-family: var(--font-ui);
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}""",
    """.ranking-name {
  font-family: var(--font-ui);
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.2rem;
  letter-spacing: 0.01em;
}"""
)

# Ranking stats
content = content.replace(
    """.ranking-stats {
  display: flex;
  gap: 1.25rem;
  margin-top: auto;
}""",
    """.ranking-stats {
  display: flex;
  gap: 1rem;
  margin-top: auto;
  padding-top: 0.75rem;
}"""
)

content = content.replace(
    """.ranking-stat-label {
  font-family: var(--font-ui);
  font-size: 0.7rem;
  color: var(--text-muted);
  letter-spacing: 0.1em;
  display: block;
}""",
    """.ranking-stat-label {
  font-family: var(--font-ui);
  font-size: 0.65rem;
  color: var(--text-muted);
  letter-spacing: 0.08em;
  display: block;
  margin-bottom: 0.1rem;
}"""
)

content = content.replace(
    """.ranking-stat-value {
  font-family: var(--font-display);
  font-size: 1.1rem;
  color: var(--text-primary);
  display: block;
}""",
    """.ranking-stat-value {
  font-family: var(--font-display);
  font-size: 1.2rem;
  color: var(--blue);
  display: block;
  letter-spacing: 0.02em;
}"""
)

# Tasks: horizontal scroll
content = content.replace(
    """.task-focus-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem;
}""",
    """.task-focus-grid {
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
  scroll-snap-type: x mandatory;
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.task-focus-grid::-webkit-scrollbar { display: none; }"""
)

content = content.replace(
    """.task-focus-strip {
  scroll-snap-align: start;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  transition: border-color 0.2s;
}""",
    """.task-focus-strip {
  scroll-snap-align: start;
  flex: 0 0 200px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.task-focus-strip:hover {
  border-color: var(--border-hover);
  box-shadow: 0 2px 12px rgba(91, 200, 255, 0.06);
}"""
)

# Failure: remove number, 2-col grid
content = content.replace(
    """.failure-row {
  display: grid;
  grid-template-columns: 2.5rem 1fr auto;
  gap: 1.5rem;
  align-items: start;
  padding-block: 1rem;
  border-bottom: 1px solid var(--border);
}""",
    """.failure-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 1.5rem;
  align-items: start;
  padding-block: 1.25rem;
  border-bottom: 1px solid var(--border);
}
.failure-row:first-child {
  border-top: 1px solid var(--border);
}"""
)

content = content.replace(
    """.failure-num {
  font-family: var(--font-display);
  font-size: 1.1rem;
  color: var(--danger);
  opacity: 0.75;
  line-height: 1.6;
}""",
    """.failure-num {
  display: none;
}"""
)

content = content.replace(
    """.failure-label {
  font-family: var(--font-ui);
  font-size: 0.95rem;
  color: var(--text-primary);
  font-weight: 500;
  margin-bottom: 0.2rem;
}""",
    """.failure-label {
  font-family: var(--font-ui);
  font-size: 0.9rem;
  color: var(--text-primary);
  font-weight: 600;
  margin-bottom: 0.3rem;
  letter-spacing: 0.01em;
}"""
)

content = content.replace(
    """.failure-models {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--gold);
  white-space: nowrap;
  padding-top: 0.1rem;
}""",
    """.failure-models {
  font-family: var(--font-ui);
  font-size: 0.7rem;
  color: var(--gold);
  white-space: nowrap;
  padding-top: 0.15rem;
  opacity: 0.8;
}"""
)

# Evidence cards: narrower
content = content.replace(
    "flex: 0 0 320px;",
    "flex: 0 0 260px;"
)
content = content.replace(
    "flex: 0 0 300px;",
    "flex: 0 0 260px;"
)

# Section title: simple, not oversized
content = content.replace(
    """.section-title {
  font-family: var(--font-display);
  font-size: clamp(1.4rem, 3vw, 2rem);
  font-weight: 400;
  color: var(--text-primary);
  line-height: 1.3;
  letter-spacing: 0.03em;
}""",
    """.section-title {
  font-family: var(--font-ui);
  font-size: 0.8rem;
  font-weight: 400;
  color: var(--text-muted);
  line-height: 1.5;
  letter-spacing: 0.04em;
}"""
)

content = content.replace(
    ".section-heading { margin-bottom: clamp(2rem, 4vw, 3rem); }",
    ".section-heading { margin-bottom: 1.5rem; }"
)

# Hero: left-align content
content = content.replace(
    """.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
  width: 100%;
  max-width: 700px;
  margin-inline: auto;
  padding: calc(var(--nav-h) + 3rem) clamp(1rem, 4vw, 2.5rem) 3rem;
}""",
    """.hero-content {
  position: relative;
  z-index: 1;
  text-align: left;
  width: 100%;
  max-width: 680px;
  padding: calc(var(--nav-h) + 2rem) clamp(1rem, 4vw, 2.5rem) 3rem;
}"""
)

content = content.replace(
    """.hero-summary {
  font-family: var(--font-ui);
  font-size: clamp(0.9rem, 2vw, 1.05rem);
  color: var(--text-muted);
  line-height: 1.7;
  max-width: 520px;
  margin-inline: auto;
  margin-bottom: 2.5rem;
}""",
    """.hero-summary {
  font-family: var(--font-ui);
  font-size: 0.95rem;
  color: var(--text-muted);
  line-height: 1.7;
  max-width: 480px;
  margin-bottom: 2rem;
}"""
)

content = content.replace(
    """.hero-kpis {
  display: flex;
  justify-content: center;
  gap: clamp(2rem, 6vw, 4rem);
}""",
    """.hero-kpis {
  display: flex;
  gap: 2.5rem;
}"""
)

# Verdict
content = content.replace(
    """.verdict-content { position: relative; z-index: 1; }""",
    """.verdict-content { position: relative; z-index: 1; text-align: left; }"""
)

content = content.replace(
    """.verdict-recommendation {
  font-family: var(--font-display);
  font-size: clamp(1.2rem, 3vw, 1.8rem);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.04em;
  margin-bottom: 1.5rem;
}""",
    """.verdict-recommendation {
  font-family: var(--font-ui);
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-muted);
  letter-spacing: 0.04em;
  margin-bottom: 0.75rem;
}"""
)

content = content.replace(
    """.verdict-callout {
  font-family: var(--font-display);
  font-size: clamp(1rem, 2.5vw, 1.4rem);
  color: var(--blue);
  letter-spacing: 0.08em;
}""",
    """.verdict-callout {
  font-family: var(--font-display);
  font-size: clamp(1.4rem, 3vw, 2rem);
  color: var(--blue);
  letter-spacing: 0.06em;
  text-shadow: 0 0 30px rgba(91, 200, 255, 0.15);
}"""
)

content = content.replace(
    """.verdict-summary {
  font-family: var(--font-ui);
  font-size: clamp(0.9rem, 2vw, 1.05rem);
  color: var(--text-muted);
  max-width: 580px;
  margin-inline: auto;
  line-height: 1.8;
  margin-bottom: 2rem;
}""",
    """.verdict-summary {
  font-family: var(--font-ui);
  font-size: 0.88rem;
  color: var(--text-muted);
  max-width: 520px;
  line-height: 1.8;
  margin-bottom: 1.5rem;
}"""
)

open('/Users/golden-tenet/claw-spaces/Phoebe/Projects/openclaw-model-arena/app/src/styles/theme.css', 'w').write(content)
print("Done")
