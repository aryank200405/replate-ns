# RePlate NS — Agentic Surplus Food Rescue

**Cognizant BrAInstorm Challenge | Track: Sustainability (Agentic AI for Good)**

---

## 1. The Idea: What Is RePlate NS?

### The Problem
Every day, restaurants, cafes, and event venues discard large amounts of safe, edible surplus food while local communities struggle with food insecurity. This happens not from a lack of generosity, but because busy kitchen staff and food rescue organizations lack the time to manually track inventory, verify food safety windows, and coordinate urgent pickups before food spoils.

### Our Solution
**RePlate NS** is an autonomous supply-chain bridge connecting local food businesses with verified food security networks in Halifax and across Nova Scotia. Powered by a multi-step AI agent pipeline, RePlate NS eliminates manual coordination by:
1. **Auto-Triaging** surplus inventory by spoilage risk and food-safety rules (`RED` = <24h urgent, `YELLOW` = 2–5 days, `GREEN` = >5 days shelf-stable, `REJECTED` = past safe expiry).
2. **Smart Routing** pickups dynamically to the closest verified recipient that accepts that food category and has available cold-storage capacity—while queuing an automatic backup if the #1 recipient declines or is full.
3. **Instant Alerts & Impact Tracking** notifying best-fit recipients in real time and logging `kg rescued`, `meals provided`, and `CO2e avoided`.

### Who It Serves
- **Donors (Restaurant / Business Portal):** Restaurants & cafes, event catering companies, hotels & conference venues, and university meal halls & corporate cafeterias. *(Scalable to supermarkets, local farms & greenhouses, and wholesale cold-storage distributors.)*
- **Recipients (Shelter & Food Bank Portal):** Shelters, community kitchens, community fridges, local & large-scale food banks, distribution hubs, and verified individuals in need.

---

## 2. What Is Built So Far (Live & Working)
- **Halifax Seed Network (`data/shelters.json`):** 4 local recipients (Adsum House Shelter, Dalhousie Community Fridge, Hope Cottage Community Kitchen, Feed Nova Scotia Hub) with GPS coordinates, cold-storage capacity, and accepted food types.
- **3-Agent FastAPI Backend (`BACKEND/main.py`):**
  - **Auto-Triage Agent:** Scores safety/urgency and blocks expired items.
  - **Smart Routing Agent:** Filters by food type and cold-storage capacity, ranks by Haversine distance, and queues a backup recipient.
  - **Instant Alert & Impact Agent:** Dispatches pickup alerts, handles one-click claiming, and updates the community impact ledger.
  - **Security & Validation:** Pydantic schema validation and `x-api-key` header verification.
- **Two-Portal Web UI (`FRONTEND/frontend.html`):**
  - **Restaurant / Business Portal:** Surplus intake form, 1-click demo presets, 3-step pipeline tracker, and live AI reasoning trace.
  - **Shelter & Food Bank Portal:** Live community impact KPIs, active pickup requests, and Halifax partner capacity grid.

---

## 3. How Teammates Pull & Run Locally
1. Clone `replate-ns` in VS Code (`Ctrl+Shift+P` → `Git: Clone` → `Clone from GitHub`).
2. Whenever someone pushes updates, click **Sync Changes** in VS Code's Source Control sidebar.
3. Install dependencies once:
   ```bash
   python -m pip install fastapi uvicorn


   Hey Aashay & Nitya — RePlate NS MVP is built and pushed to GitHub!
## Here's our final game plan for tomorrow (Wed, Nov 18 — Deadline: 11:59 PM):

1. WHAT'S ALREADY DONE & PUSHED
• FastAPI 3-Agent Backend (BACKEND/main.py): Smart Vision photo scan, Auto-Triage (RED/YELLOW/GREEN/REJECTED + Allergen flags), Smart Routing (distance + live cold-storage capacity), Autonomous Fallback (Decline -> Auto-Reroute), and SQLite persistence.
• Two-Portal UI (FRONTEND/frontend.html + styles.css): Restaurant/Business Portal + Shelter & Food Bank Portal with live impact KPIs and capacity bars.
• Seed Data (data/shelters.json): 4 starter Halifax shelters/fridges.

2. HOW TO PULL & RUN IT TOMORROW MORNING
1. Clone `replate-ns` in VS Code (or click Sync Changes if already cloned).
2. Run in VS Code terminal:
   python -m pip install -r BACKEND/requirements.txt
   python -m uvicorn BACKEND.main:app --reload
3. Open FRONTEND/frontend.html in Chrome (or click Go Live in VS Code).

3. WHO DOES WHAT TOMORROW (Nov 18)
• Nitya (data/ & Pitch Lead):
  1. Add 3–4 more Halifax shelters/community fridges to data/shelters.json.
  2. Update our flowchart diagram (fix typos: Problem, Restaurants, Smart Vision) & draft the 3-minute video talking points.
• Aashay (FRONTEND/ & QA Lead):
  1. Test all 4 demo flows end-to-end (Smart Vision scan, Urgent RED dispatch, Expired REJECTED block, Decline -> Auto-Reroute).
  2. Tweak any UI text/mobile spacing if needed and verify live capacity bars update cleanly.
• Aryan (BACKEND/ & Integration Lead):
  1. Review/merge any pulls, fix any backend bugs during testing, and prep the GitHub README for judges.

4. TIMELINE FOR TOMORROW
• 5:00 PM: Code & data freeze
• 7:00 PM: Record & trim our max 3-minute demo video together
• 10:00 PM: Submit Form #2 (GitHub link + 3-min video) well before 11:59 PM!
