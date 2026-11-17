from datetime import datetime, timezone
import json
import math
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="RePlate NS Agentic API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "replate-ns-demo-key"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "shelters.json"
RECIPIENTS = json.loads(DATA_PATH.read_text(encoding="utf-8"))
ALERTS: List[dict] = []
LEDGER = {"kg_rescued": 0.0, "meals_saved": 0, "co2_avoided_kg": 0.0}


class SurplusRequest(BaseModel):
    donor_name: str = Field(..., min_length=2)
    food_item: str = Field(..., min_length=2)
    category: str  # prepared, produce, bakery, dairy, packaged
    weight_kg: float = Field(..., gt=0, le=500)
    hours_until_expiry: float = Field(..., ge=-24, le=720)
    donor_lat: float = 44.6488
    donor_lon: float = -63.5752


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return round(2 * r * math.asin(math.sqrt(a)), 2)


def triage_agent(req: SurplusRequest) -> dict:
    if req.hours_until_expiry <= 0:
        return {
            "tag": "REJECTED",
            "safe": False,
            "reason": "Past safe expiry window; blocked by food-safety guardrail.",
        }
    if req.hours_until_expiry <= 24:
        return {
            "tag": "RED",
            "safe": True,
            "reason": f"Urgent (<24h): {req.hours_until_expiry}h remaining. Priority dispatch.",
        }
    if req.hours_until_expiry <= 120:
        return {
            "tag": "YELLOW",
            "safe": True,
            "reason": f"Moderate (2-5 days): {req.hours_until_expiry}h remaining.",
        }
    return {
        "tag": "GREEN",
        "safe": True,
        "reason": f"Shelf-stable (>5 days): {req.hours_until_expiry}h remaining.",
    }


def routing_agent(req: SurplusRequest, exclude_ids: Optional[set] = None) -> List[dict]:
    exclude_ids = exclude_ids or set()
    candidates = []
    for rec in RECIPIENTS:
        if rec["id"] in exclude_ids:
            continue
        if req.category not in rec["accepts"]:
            continue
        if rec["cold_storage_kg"] < req.weight_kg:
            continue
        dist = haversine_km(req.donor_lat, req.donor_lon, rec["lat"], rec["lon"])
        candidates.append({**rec, "distance_km": dist})
    return sorted(candidates, key=lambda x: x["distance_km"])


@app.post("/api/donate")
def process_surplus(req: SurplusRequest, x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    trace = []
    triage = triage_agent(req)
    trace.append(f"[Auto-Triage Agent] Tagged {triage['tag']}: {triage['reason']}")

    if not triage["safe"]:
        return {"status": "rejected", "triage": triage, "agent_trace": trace}

    matches = routing_agent(req)
    if not matches:
        trace.append("[Smart Routing Agent] No recipient has enough cold-storage capacity.")
        return {"status": "unmatched", "triage": triage, "agent_trace": trace}

    primary = matches[0]
    backup = matches[1] if len(matches) > 1 else None
    trace.append(
        f"[Smart Routing Agent] Selected {primary['name']} ({primary['distance_km']} km, "
        f"{primary['cold_storage_kg']} kg cap)."
    )
    if backup:
        trace.append(
            f"[Smart Routing Agent] Backup ready: {backup['name']} ({backup['distance_km']} km)."
        )

    alert = {
        "alert_id": f"ALT-{len(ALERTS) + 1}",
        "donor": req.donor_name,
        "item": req.food_item,
        "weight_kg": req.weight_kg,
        "triage_tag": triage["tag"],
        "recipient_id": primary["id"],
        "recipient_name": primary["name"],
        "backup_name": backup["name"] if backup else None,
        "status": "PENDING_CLAIM",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    ALERTS.insert(0, alert)
    trace.append(f"[Instant Alert Agent] Dispatched alert {alert['alert_id']} to {primary['name']}.")

    return {"status": "matched", "triage": triage, "alert": alert, "agent_trace": trace}


@app.post("/api/alerts/{alert_id}/claim")
def claim_alert(alert_id: str, x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    for alert in ALERTS:
        if alert["alert_id"] == alert_id and alert["status"] == "PENDING_CLAIM":
            alert["status"] = "CLAIMED"
            LEDGER["kg_rescued"] = round(LEDGER["kg_rescued"] + alert["weight_kg"], 2)
            LEDGER["meals_saved"] += int(round(alert["weight_kg"] * 2.2))
            LEDGER["co2_avoided_kg"] = round(LEDGER["kg_rescued"] * 2.5, 2)
            return {"alert": alert, "ledger": LEDGER}
    raise HTTPException(status_code=404, detail="Pending alert not found")


@app.get("/api/dashboard")
def get_dashboard():
    return {"alerts": ALERTS, "ledger": LEDGER, "recipients": RECIPIENTS}