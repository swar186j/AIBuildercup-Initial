# Draft1 Frontend

React + TypeScript + Vite. Backend proxy: `/api/*` -> `http://127.0.0.1:8000`.

## Run

```bash
npm install
npm run dev
```

Open http://localhost:5173.

## Backend integration

Implemented: GET `/api/health` (response `{status, application, version}`).

Not implemented: evidence upload, Gemini analysis, Firestore persistence, case decisions. The case preview is explicitly local-only; no request is sent and no analysis is fabricated.

Backend team should agree on submission API method/path, multipart fields, response schema and async processing lifecycle before connecting it in `src/api.ts`.

Use synthetic test data; do not upload real medical documents until appropriate security/privacy controls are in place.
