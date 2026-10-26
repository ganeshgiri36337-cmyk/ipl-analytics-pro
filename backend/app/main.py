from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .data_service import CsvValidationError, IplDataStore


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("IPL_DATA_DIR", str(PROJECT_ROOT / "data"))).expanduser()
MAX_UPLOAD_BYTES = int(os.environ.get("IPL_MAX_UPLOAD_BYTES", 50 * 1024 * 1024))

app = FastAPI(
    title="IPL Analytics API",
    description="CSV-powered IPL match and player analytics.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.environ.get(
            "IPL_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.state.data_store = IplDataStore(DATA_DIR, MAX_UPLOAD_BYTES)


def get_store(request: Request) -> IplDataStore:
    return request.app.state.data_store


StoreDependency = Annotated[IplDataStore, Depends(get_store)]
SeasonFilter = Annotated[list[str] | None, Query()]
TeamFilter = Annotated[list[str] | None, Query()]
PlayerFilter = Annotated[list[str] | None, Query()]


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/filters")
def filters(store: StoreDependency) -> dict[str, list[str]]:
    return store.filter_options()


@app.get("/api/seasons")
def seasons(store: StoreDependency) -> dict:
    return store.seasons()


@app.get("/api/dashboard")
def dashboard(
    store: StoreDependency, season: SeasonFilter = None, team: TeamFilter = None
) -> dict:
    return store.dashboard(season, team)


@app.get("/api/teams")
def teams(
    store: StoreDependency, season: SeasonFilter = None, team: TeamFilter = None
) -> dict:
    return store.team_statistics(season, team)


@app.get("/api/players")
def players(
    store: StoreDependency,
    season: SeasonFilter = None,
    team: TeamFilter = None,
    player: PlayerFilter = None,
) -> dict:
    return store.player_statistics(season, team, player)


@app.get("/api/venues")
def venues(
    store: StoreDependency, season: SeasonFilter = None, team: TeamFilter = None
) -> dict:
    return store.venue_statistics(season, team)


@app.get("/api/toss")
def toss(
    store: StoreDependency, season: SeasonFilter = None, team: TeamFilter = None
) -> dict:
    return store.toss_statistics(season, team)


@app.get("/api/charts")
def charts(
    store: StoreDependency,
    season: SeasonFilter = None,
    team: TeamFilter = None,
    player: PlayerFilter = None,
) -> dict:
    return store.charts(season, team, player)


@app.get("/api/data-quality")
def data_quality(store: StoreDependency) -> dict:
    return store.data_quality()


async def upload_csv(dataset: str, file: UploadFile, store: IplDataStore) -> dict:
    contents = await file.read(store.max_upload_bytes + 1)
    try:
        return store.upload(dataset, file.filename, contents)
    except CsvValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except OSError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    finally:
        await file.close()


@app.post("/api/upload/matches")
async def upload_matches(
    file: Annotated[UploadFile, File(...)],
    store: StoreDependency,
) -> dict:
    return await upload_csv("matches", file, store)


@app.post("/api/upload/deliveries")
async def upload_deliveries(
    file: Annotated[UploadFile, File(...)],
    store: StoreDependency,
) -> dict:
    return await upload_csv("deliveries", file, store)
