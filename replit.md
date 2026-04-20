# Agenda Turma A - Escala Ferroviária 2x2 (2026-2030)

## Project Overview

A progressive web application (PWA) for railway workers ("Turma A") to manage their work schedules, time-off (folgas), mandatory documents, and professional audits.

## Architecture

- **Type:** Static single-page application (no build step required)
- **Core file:** `index.html` — contains all HTML, CSS, and JavaScript
- **Data persistence:** Browser `localStorage` (key: `turmaA_v10`)
- **No external dependencies** — fully self-contained

## Key Features

- Railway 2x2 shift rotation calculator (2026–2030)
- Document management (CNH, ASO, NR-11) with expiration alerts
- Audit period visualization on calendar
- "Viriato" assistant chatbot for schedule queries
- Built-in alarm clock and browser notification support
- Dark/light theme

## Running the App

The app is served via Python's built-in HTTP server on port 5000:

```
python3 -m http.server 5000 --bind 0.0.0.0
```

## Deployment

Configured as a **static** deployment with `publicDir: "."`.
