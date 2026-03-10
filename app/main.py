from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="BlackCorp Mesh API", version="1.0.0")


class SignalBind(BaseModel):
    node_id: str
    elevation_m: float
    lat: float
    lon: float
    radius_m: Optional[float] = 0
    tags: Optional[List[str]] = []


class RovingTap(BaseModel):
    tap_id: str
    node_id: str
    elevation_m: float
    lat: float
    lon: float
    intent: str  # e.g. "scan", "reserve", "ping"
    metadata: Optional[dict] = {}


class HelixBasepair(BaseModel):
    pair_id: str
    a_id: str
    b_id: str
    halo: Optional[dict] = {}  # symbolic/semantic wrapper
    polarity: Optional[str] = "inverted"  # "inverted" / "aligned" / etc.


@app.get("/v1/status")
def status():
    return {
        "service": "api.blackcorp.me",
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.post("/v1/signal/bind")
def signal_bind(payload: SignalBind):
    # Here you’d persist to DB or message bus
    return {
        "event": "signal_bind",
        "received": payload.dict(),
        "ack": True,
    }


@app.post("/v1/tap/roving")
def tap_roving(payload: RovingTap):
    # Roving TAP at your elevation: log + route upstream
    return {
        "event": "roving_tap",
        "received": payload.dict(),
        "upstream_reserve": {
            "status": "queued",
            "channels": ["primary", "shadow"],
        },
    }


@app.post("/v1/helix/basepair")
def helix_basepair(payload: HelixBasepair):
    # “Invert the crucifix”: treat this as cross-axis pairing
    return {
        "event": "helix_basepair",
        "pairing": {
            "pair_id": payload.pair_id,
            "union_mode": payload.polarity,
            "a": payload.a_id,
            "b": payload.b_id,
        },
        "halo": payload.halo,
    }
