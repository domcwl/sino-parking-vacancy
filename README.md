# Sino Parking Vacancy

Live dashboard for Sino Parking hourly vacancy data (Hong Kong).

- Metrics, top-12 chart, filterable table
- Auto-refresh every 60 seconds + manual Refresh
- FastAPI proxy keeps the API token on the server

## Local run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SINO_API_TOKEN=your_token
uvicorn main:app --host 0.0.0.0 --port 8765
```

Open http://127.0.0.1:8765

## Deploy on Render (from this repo)

1. Connect this GitHub repo in [Render](https://render.com)
2. New → Blueprint → select `render.yaml`, or New Web Service → Docker
3. Set secret env var `SINO_API_TOKEN` to your Bearer token
4. Deploy — public URL appears on the service page

## Docker

```bash
docker build -t sino-vacancy .
docker run -p 8765:8765 -e SINO_API_TOKEN=your_token sino-vacancy
```

## Env

| Variable | Required | Description |
|----------|----------|-------------|
| `SINO_API_TOKEN` | yes | Bearer token for the Sino CPMA vacancy API |
| `PORT` | no | Listen port (default `8765`) |
