from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
from typing import List, Optional
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="RePlate NS Agentic API", version="1.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "replate-ns-demo-key"
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "data" / "shelters.json"
DB_PATH = ROOT_DIR / "replate.db"

RECIPIENTS = json.loads(DATA_PATH.read_text(encoding="utf-8"))
for r in RECIPIENTS:
    r["max_storage_kg"] = r["cold_storage_kg"]


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS alerts (
                alert_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS ledger (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                kg_rescued REAL NOT NULL,
                meals_saved INTEGER NOT NULL,
                co2_avoided_kg REAL NOT NULL
            )"""
        )
        conn.execute(
            "INSERT OR IGNORE INTO ledger (id, kg_rescued, meals_saved, co2_avoided_kg) VALUES (1, 0.0, 0, 0.0)"
        )


init_db()


def get_alerts() -> List[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT payload FROM alerts ORDER BY rowid DESC").fetchall()
    return [json.loads(r[0]) for r in rows]


def save_alert(alert: dict):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO alerts (alert_id, payload) VALUES (?, ?)",
            (alert["alert_id"], json.dumps(alert)),
        )


def get_ledger() -> dict:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT kg_rescued, meals_saved, co2_avoided_kg FROM ledger WHERE id = 1").fetchone()
    return {"kg_rescued": row[0], "meals_saved": row[1], "co2_avoided_kg": row[2]}


def update_ledger(added_kg: float) -> dict:
    cur = get_ledger()
    new_kg = round(cur["kg_rescued"] + added_kg, 2)
    new_meals = cur["meals_saved"] + int(round(added_kg * 2.2))
    new_co2 = round(new_kg * 2.5, 2)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE ledger SET kg_rescued = ?, meals_saved = ?, co2_avoided_kg = ? WHERE id = 1",
            (new_kg, new_meals, new_co2),
        )
    return {"kg_rescued": new_kg, "meals_saved": new_meals, "co2_avoided_kg": new_co2}


class SurplusRequest(BaseModel):
    donor_name: str = Field(..., min_length=2)
    food_item: str = Field(..., min_length=2)
    category: str
    allergens: str = "None"
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
        return {"tag": "REJECTED", "safe": False, "reason": "Past safe expiry window; blocked by food-safety guardrail."}
    if req.hours_until_expiry <= 24:
        return {"tag": "RED", "safe": True, "reason": f"Urgent (<24h): {req.hours_until_expiry}h left. Priority dispatch."}
    if req.hours_until_expiry <= 120:
        return {"tag": "YELLOW", "safe": True, "reason": f"Moderate (2-5 days): {req.hours_until_expiry}h left."}
    return {"tag": "GREEN", "safe": True, "reason": f"Shelf-stable (>5 days): {req.hours_until_expiry}h left."}


def routing_agent(
    category: str, weight_kg: float, donor_lat: float, donor_lon: float, exclude_ids: Optional[set] = None
) -> List[dict]:
    exclude_ids = exclude_ids or set()
    candidates = []
    for rec in RECIPIENTS:
        if rec["id"] in exclude_ids:
            continue
        if category not in rec["accepts"]:
            continue
        if rec["cold_storage_kg"] < weight_kg:
            continue
        dist = haversine_km(donor_lat, donor_lon, rec["lat"], rec["lon"])
        candidates.append({**rec, "distance_km": dist})
    return sorted(candidates, key=lambda x: x["distance_km"])


@app.post("/api/vision-scan")
async def smart_vision_scan(file: UploadFile = File(...), x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    name = (file.filename or "").lower()
    if "bread" in name or "bakery" in name or "pastry" in name:
        detected = {"food_item": "Artisan Bread & Pastries", "category": "bakery", "allergens": "Gluten", "weight_kg": 10, "hours_until_expiry": 48}
    elif "produce" in name or "salad" in name or "veg" in name:
        detected = {"food_item": "Fresh Mixed Produce", "category": "produce", "allergens": "None", "weight_kg": 14, "hours_until_expiry": 36}
    elif "milk" in name or "dairy" in name or "expired" in name:
        detected = {"food_item": "Chilled Dairy Cartons", "category": "dairy", "allergens": "Dairy", "weight_kg": 12, "hours_until_expiry": -2}
    else:
        detected = {"food_item": "Prepared Catering Trays", "category": "prepared", "allergens": "Gluten", "weight_kg": 18, "hours_until_expiry": 10}

    return {
        "detected": detected,
        "trace": f"[Smart Vision Agent] Scanned '{file.filename}' -> {detected['food_item']} ({detected['weight_kg']} kg, Allergen: {detected['allergens']}).",
    }


@app.post("/api/donate")
def process_surplus(req: SurplusRequest, x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    trace = []
    triage = triage_agent(req)
    allergen_note = f" | Allergen flag: {req.allergens}" if req.allergens != "None" else " | Allergen-free"
    trace.append(f"[Auto-Triage Agent] Tagged {triage['tag']}: {triage['reason']}{allergen_note}")

    if not triage["safe"]:
        return {"status": "rejected", "triage": triage, "agent_trace": trace}

    matches = routing_agent(req.category, req.weight_kg, req.donor_lat, req.donor_lon)
    if not matches:
        trace.append("[Smart Routing Agent] No recipient has enough remaining cold-storage capacity.")
        return {"status": "unmatched", "triage": triage, "agent_trace": trace}

    primary = matches[0]
    backup = matches[1] if len(matches) > 1 else None
    trace.append(
        f"[Smart Routing Agent] Selected {primary['name']} ({primary['distance_km']} km, "
        f"{primary['cold_storage_kg']} kg free)."
    )
    if backup:
        trace.append(f"[Smart Routing Agent] Backup queued: {backup['name']} ({backup['distance_km']} km).")

    existing = get_alerts()
    alert = {
        "alert_id": f"ALT-{len(existing) + 1}",
        "donor": req.donor_name,
        "item": req.food_item,
        "category": req.category,
        "allergens": req.allergens,
        "weight_kg": req.weight_kg,
        "donor_lat": req.donor_lat,
        "donor_lon": req.donor_lon,
        "triage_tag": triage["tag"],
        "recipient_id": primary["id"],
        "recipient_name": primary["name"],
        "backup_name": backup["name"] if backup else None,
        "excluded_ids": [],
        "rerouted": False,
        "status": "PENDING_CLAIM",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    save_alert(alert)
    trace.append(f"[Instant Alert Agent] Saved to SQLite & dispatched {alert['alert_id']} to {primary['name']}.")

    return {"status": "matched", "triage": triage, "alert": alert, "agent_trace": trace}


@app.post("/api/alerts/{alert_id}/claim")
def claim_alert(alert_id: str, x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    for alert in get_alerts():
        if alert["alert_id"] == alert_id and alert["status"] == "PENDING_CLAIM":
            alert["status"] = "CLAIMED"
            save_alert(alert)
            for rec in RECIPIENTS:
                if rec["id"] == alert["recipient_id"]:
                    rec["cold_storage_kg"] = max(0, round(rec["cold_storage_kg"] - alert["weight_kg"], 1))
            ledger = update_ledger(alert["weight_kg"])
            return {"alert": alert, "ledger": ledger}
    raise HTTPException(status_code=404, detail="Pending alert not found")


@app.post("/api/alerts/{alert_id}/decline")
def decline_and_reroute(alert_id: str, x_api_key: str = Header(default="")):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    for alert in get_alerts():
        if alert["alert_id"] == alert_id and alert["status"] == "PENDING_CLAIM":
            prev_name = alert["recipient_name"]
            alert["excluded_ids"].append(alert["recipient_id"])
            matches = routing_agent(
                alert["category"],
                alert["weight_kg"],
                alert["donor_lat"],
                alert["donor_lon"],
                exclude_ids=set(alert["excluded_ids"]),
            )
            if not matches:
                alert["status"] = "UNMATCHED"
                save_alert(alert)
                return {"alert": alert, "message": f"{prev_name} declined; no remaining capacity."}
            next_rec = matches[0]
            next_backup = matches[1] if len(matches) > 1 else None
            alert["recipient_id"] = next_rec["id"]
            alert["recipient_name"] = next_rec["name"]
            alert["backup_name"] = next_backup["name"] if next_backup else None
            alert["rerouted"] = True
            save_alert(alert)
            return {
                "alert": alert,
                "message": f"[Fallback Agent] {prev_name} full -> auto-rerouted to {next_rec['name']} ({next_rec['distance_km']} km).",
            }
    raise HTTPException(status_code=404, detail="Pending alert not found")


@app.get("/api/dashboard")
def get_dashboard():
    return {"alerts": get_alerts(), "ledger": get_ledger(), "recipients": RECIPIENTS}