# Frontend

Next.js App Router chat UI for the Enterprise RAG + RBAC backend.

## What it does

- Lets you pick a mock user role/user_id from a dropdown
- Sends messages to the backend `/chat` endpoint
- Renders assistant responses, sources, and access-denied states
- Uses a rewrite so the browser can call `/chat` without CORS issues

## Run it

1. Copy the example env file:

```bash
copy .env.local.example .env.local
```

1. Install dependencies:

```bash
npm install
```

1. Start the app:

```bash
npm run dev
```

The UI will run at `http://localhost:3000` and proxy `/chat` to the FastAPI backend at `NEXT_PUBLIC_API_BASE_URL`.

## Notes

- Start the Python backend first on `http://localhost:8000`.
- The frontend uses a mock unsigned JWT that matches the selected `user_id`.
