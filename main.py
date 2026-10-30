"""Sino Parking vacancy dashboard — FastAPI backend."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

SINO_HOST = "apps.sino-parking.com"
SINO_PORT = 8080
SINO_PATH = "/cpma/rest/vacancy"
SINO_ACCEPT = "application/vnd.sino-cpma.vacancy-v1.0+json"
DOH_URL = "https://cloudflare-dns.com/dns-query"
FALLBACK_IPS = ["8.217.125.21", "8.218.152.96"]

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Sino Parking Vacancy")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _bearer() -> str:
    token = os.environ.get("SINO_API_TOKEN", "").strip()
    if not token:
        raise HTTPException(
            status_code=500,
            detail="SINO_API_TOKEN is not set. Add it as an environment variable.",
        )
    return token


async def resolve_sino_ips() -> list[str]:
    """Resolve apps.sino-parking.com via Cloudflare DoH (avoids box sinkhole)."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                DOH_URL,
                params={"name": SINO_HOST, "type": "A"},
                headers={"accept": "application/dns-json"},
            )
            r.raise_for_status()
            data = r.json()
            ips = [
                ans["data"]
                for ans in data.get("Answer", [])
                if ans.get("type") == 1 and ans.get("data")
            ]
            seen: set[str] = set()
            out: list[str] = []
            for ip in ips:
                if ip not in seen and not ip.startswith("198.18."):
                    seen.add(ip)
                    out.append(ip)
            if out:
                return out
    except Exception:
        pass
    return list(FALLBACK_IPS)


async def fetch_vacancy() -> Any:
    ips = await resolve_sino_ips()
    headers = {
        "Accept": SINO_ACCEPT,
        "Authorization": f"Bearer {_bearer()}",
        "Host": f"{SINO_HOST}:{SINO_PORT}",
    }
    errors: list[str] = []
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        for ip in ips:
            url = f"http://{ip}:{SINO_PORT}{SINO_PATH}"
            try:
                r = await client.get(url, headers=headers)
                if r.status_code == 200:
                    return r.json()
                errors.append(f"{ip}: HTTP {r.status_code}")
            except Exception as exc:
                errors.append(f"{ip}: {exc}")
    raise HTTPException(
        status_code=502,
        detail=f"Upstream Sino API unreachable. Tried: {'; '.join(errors)}",
    )


@app.get("/api/vacancy")
async def api_vacancy() -> Any:
    return await fetch_vacancy()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8765"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
