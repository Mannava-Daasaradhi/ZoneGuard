# ZoneGuard UI Design — 2026-03-20

## Overview

A static React (TypeScript) + Tailwind CSS + Recharts single-page application deployed to GitHub Pages. Two distinct visual worlds for two personas, switchable via a top-level persona toggle.

## Constraints

- GitHub Pages static deployment (no SSR, no backend)
- HashRouter for GH Pages compatibility
- All data mocked in frontend (realistic simulated values)
- Tech: React + TypeScript + Tailwind CSS + Recharts

## Routing

```
HashRouter
├── /                    → Landing / Persona Selector
├── /rider               → Rider Dashboard (warm theme)
├── /admin               → Insurer Admin Dashboard (dark theme)
└── /onboarding          → 3-step onboarding flow
```

## Design System

### Rider World (warm, reassuring)
- Background: #FFFBF3 (warm white)
- Primary: #D97706 (amber-600, saffron tone)
- Accent: #059669 (emerald — "protected" green)
- Text: #1C1917 (warm near-black)
- Cards: white with amber-100 border, soft shadow

### Admin World (cool, precise)
- Background: #0F172A (slate-900)
- Primary: #3B82F6 (blue-500)
- Alert: #F59E0B (amber — signal firing)
- Danger: #EF4444 (red — fraud flag)
- Cards: slate-800 with slate-700 border

### Shared
- Font: Inter
- Border radius: rounded-xl
- Charts: Recharts

## Pages

### Landing (`/`)
- ZoneGuard logo + tagline
- Two persona cards: Rider → /rider, Insurer → /admin
- Ambient CSS animation background

### Rider Dashboard (`/rider`)
- Top bar: rider name, zone, policy badge
- Week Timeline (hero): Mon–Sun horizontal, normal=amber dot, disruption=red + payout badge
- Coverage Card: active policy, zone health ring
- Payout History: past events with celebration state
- Zone Status: signal monitoring summary

### Admin Dashboard (`/admin`)
- Zone Heatmap: SVG Bengaluru zones colored by risk score
- QuadSignal Panel: S1–S4 status cards + TRIGGER DEMO button (disruption simulation)
- Claims Queue: MEDIUM-confidence events with LLM audit preview
- KPI Strip: Loss Ratio, Active Policies, Payouts This Week, Zones at Risk + Recharts sparklines

### Onboarding (`/onboarding`)
- Step 1: Rider ID input
- Step 2: Zone selector (10 Bengaluru zones with risk tier)
- Step 3: Premium quote + confirm

## Mock Data

All data simulated in `/src/data/mock.ts`:
- 10 Bengaluru zones with risk scores and premium tiers
- Ravi's week (Mon–Fri) with Wednesday/Thursday disruption + payouts
- Historical payout list
- QuadSignal live state
- Claims queue (3 MEDIUM-confidence items)
- KPI values

## Deployment

- `npm run build` → `dist/`
- `gh-pages` package deploys to `gh-pages` branch
- `homepage` field in `package.json` set to GH Pages URL
