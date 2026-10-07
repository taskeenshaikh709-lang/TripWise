# TripWise frontend

Responsive React + Vite app for TripWise. It uses a Vite `/api` proxy during
development, and `VITE_API_BASE_URL` can point to another Flask API origin.

Start the frontend from this folder:

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

The frontend runs on http://localhost:5173. Create a production bundle with
`npm run build`.
