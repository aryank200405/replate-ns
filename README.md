# RePlate NS — Agentic Surplus Food Rescue

**Cognizant BrAInstorm Challenge | Track: Sustainability (Agentic AI for Good)**  
**Team:** Aryan Kapoor, Aashay Shah, Nitya Negi  

An autonomous multi-agent supply-chain bridge connecting Halifax restaurants and food businesses with local shelters, community kitchens, and fridges before safe surplus food spoils.

---

## 1. Problem & Solution

### The Problem
Every day, restaurants, cafes, and event venues discard large quantities of safe, edible surplus food while local communities face food insecurity—not from a lack of generosity, but because busy kitchen staff and food rescue organizations lack the time to manually track inventory, verify food-safety windows, and coordinate urgent pickups before food spoils.

### Our Agentic AI Solution
**RePlate NS** eliminates manual coordination through an autonomous 4-step AI workflow:
1. **Smart Vision Intake (`/api/vision-scan`):** Uploads and previews food or expiry-label photos, automatically detecting and pre-filling item name, food category, multiple allergens, estimated weight, and remaining pickup window.
2. **Auto-Triage Agent:** Evaluates food safety and urgency (`RED` <24h urgent, `YELLOW` 2–5 days, `GREEN` >5 days shelf-stable), tracks **multi-select allergen flags** (`Gluten`, `Dairy`, `Nuts`, `Soy`), and blocks expired items (`REJECTED`).
3. **Smart Routing Agent:** Filters recipients by accepted food types and **live remaining cold-storage capacity**, ranks by Haversine distance, and queues a backup shelter.
4. **Autonomous Fallback & Impact Ledger:** If a shelter clicks **Decline (Full)**, the agent automatically re-routes the pickup to the next closest partner and displays the full `Re-routed from → Assigned to` audit trail. Claimed pickups persist in SQLite (`replate.db`), decrement live shelter capacity, and update `kg rescued`, `meals provided`, and `CO2e avoided`.

---

## 2. Project Structure

```text
replate-ns/
├── BACKEND/
│   ├── main.py              # FastAPI server, 3-agent pipeline, SQLite ledger & API-key auth
│   └── requirements.txt     # Python dependencies (fastapi, uvicorn, python-multipart)
├── FRONTEND/
│   ├── frontend.html        # Restaurant/Business Portal & Shelter/Food Bank Portal
│   └── styles.css           # Responsive styling, allergen pills & capacity bars
├── DATA/
│   └── shelters.json        # Halifax partner shelters & community fridges (365 kg total capacity)
├── replate.db               # SQLite persistent alerts & community impact ledger
└── README.md
