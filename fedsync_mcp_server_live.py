import sys
import json
import urllib.request
import urllib.parse

STATE_COORDS = {
    "FL": (27.99, -81.76, "Florida"), "TX": (31.97, -99.90, "Texas"),
    "CA": (36.78, -119.42, "California"), "NY": (43.00, -75.00, "New York"),
    "LA": (30.98, -91.96, "Louisiana"), "NC": (35.76, -79.02, "North Carolina"),
    "GA": (32.16, -82.90, "Georgia"), "WA": (47.75, -120.74, "Washington"),
    "IL": (40.63, -89.40, "Illinois"), "OH": (40.42, -82.91, "Ohio"),
    "PA": (41.20, -77.19, "Pennsylvania"), "SC": (33.84, -81.16, "South Carolina")
}

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 51: "Light drizzle", 61: "Slight rain", 63: "Moderate rain",
    65: "Heavy rain", 71: "Slight snow", 75: "Heavy snow", 80: "Rain showers",
    95: "SEVERE: Thunderstorm", 96: "SEVERE: Thunderstorm with hail", 99: "SEVERE: Heavy hailstorm"
}

def send_response(response):
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()

def fetch_live_weather(state_code):
    st = state_code.strip().upper()
    if st not in STATE_COORDS:
        return f"State '{state_code}' not in regional grid. Try FL, TX, CA, NY, LA, NC, GA, WA, IL, OH, PA, or SC."
    lat, lon, name = STATE_COORDS[st]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,weather_code,wind_speed_10m,wind_gusts_10m&temperature_unit=fahrenheit&wind_speed_unit=mph"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            cur = json.loads(r.read().decode("utf-8")).get("current", {})
            cond = WMO_CODES.get(cur.get("weather_code", 0), "Active atmospheric system")
            return (
                f"LIVE TELEMETRY [{name} ({st}) - Open-Meteo/NOAA Grid]:\n"
                f" - Condition: {cond}\n"
                f" - Temperature: {cur.get('temperature_2m')} F | Precipitation: {cur.get('precipitation')} mm\n"
                f" - Wind Speed: {cur.get('wind_speed_10m')} mph (Gusts: {cur.get('wind_gusts_10m')} mph)\n"
                f" - Observed At: {cur.get('time')} UTC"
            )
    except Exception as e:
        return f"Weather telemetry error for {st}: {str(e)}"

def fetch_fema_declarations(state_code):
    st = state_code.strip().upper()
    base = "https://www.fema.gov/api/open/v2/disasterDeclarationsSummaries"
    q = urllib.parse.urlencode({"$filter": f"state eq '{st}'", "$orderby": "declarationDate desc", "$top": "10"})
    try:
        req = urllib.request.Request(f"{base}?{q}", headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r:
            recs = json.loads(r.read().decode("utf-8")).get("DisasterDeclarationsSummaries", [])
            if recs:
                seen = {}
                for row in recs:
                    did = row.get("femaDeclarationString")
                    if did and did not in seen:
                        seen[did] = f"- {did} ({row.get('declarationDate', '')[:10]}): {row.get('incidentType')} - {row.get('declarationTitle')}"
                return f"LIVE OPENFEMA DECLARATIONS [{st}]:\n" + "\n".join(list(seen.values())[:4])
    except Exception:
        pass
    snapshots = {
        "FL": "- DR-4834-FL: Hurricane Milton (Individual & Public Assistance Active)\n- DR-4828-FL: Hurricane Helene (Individual, Public & Hazard Mitigation Active)",
        "TX": "- DR-4798-TX: Hurricane Beryl (Individual & Public Assistance Active)\n- DR-4781-TX: Severe Storms & Flooding (Public Assistance Active)",
        "CA": "- DR-4856-CA: Wildfires & Straight-line Winds (Individual & Public Assistance Active)\n- DR-4769-CA: Severe Winter Storms (Public Assistance Active)",
        "NC": "- DR-4827-NC: Tropical Storm Helene (Individual, Public & Hazard Mitigation Active)"
    }
    data = snapshots.get(st, f"- No active major disaster declarations in cached federal snapshot for {st}.")
    return f"OPENFEMA DISASTER SUMMARY [{st}] (Sandbox Fallback Snapshot - .gov WAF restricted):\n{data}"

def fetch_treasury_balance():
    url = "https://treasury.gov"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            recs = json.loads(r.read().decode("utf-8")).get("data", [])
            if recs:
                latest = recs[0]
                dollars = float(latest.get("close_today_bal", 0)) * 1_000_000
                return f"LIVE U.S. TREASURY TGA BALANCE ({latest.get('record_date')}): ${dollars:,.2f} USD"
    except Exception:
        pass
    return (
        "FEDERAL EMERGENCY & TREASURY RESERVE SUMMARY (Sandbox Fallback Snapshot - .gov DNS restricted):\n"
        " - FEMA Disaster Relief Fund (DRF) Unobligated Balance: $12,480,000,000.00 USD\n"
        " - Immediate Discretionary Emergency Allocation: $42,500,000.00 USD\n"
        " - Operational Readiness Status: ACTIVE"
    )

def main():
    tools = [
        {"name": "get_incident_weather", "description": "Retrieves live weather telemetry (temp, wind, gusts, precipitation, severe codes) for a 2-letter US state.", "inputSchema": {"type": "object", "properties": {"state": {"type": "string"}}, "required": ["state"]}},
        {"name": "get_disaster_declarations", "description": "Retrieves federal FEMA disaster declarations and active aid programs for a 2-letter US state.", "inputSchema": {"type": "object", "properties": {"state": {"type": "string"}}, "required": ["state"]}},
        {"name": "get_disaster_fund_balance", "description": "Retrieves federal emergency aid and U.S. Treasury operating reserve balances.", "inputSchema": {"type": "object", "properties": {}}}
    ]
    for line in sys.stdin:
        if not line.strip() or line.startswith("Content-Length:"):
            continue
        req_id = None
        try:
            req = json.loads(line.strip())
            req_id = req.get("id")
            m = req.get("method")
            if m == "initialize":
                send_response({"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "FedSync-Emergency-Engine", "version": "2.1.0"}}})
            elif m == "tools/list":
                send_response({"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools}})
            elif m == "tools/call":
                p = req.get("params", {})
                name, args = p.get("name"), p.get("arguments", {})
                if name == "get_incident_weather":
                    out = fetch_live_weather(args.get("state", ""))
                elif name == "get_disaster_declarations":
                    out = fetch_fema_declarations(args.get("state", ""))
                elif name == "get_disaster_fund_balance":
                    out = fetch_treasury_balance()
                else:
                    out = f"Unknown tool: {name}"
                send_response({"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": out}]}})
        except Exception as e:
            if req_id is not None:
                send_response({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": str(e)}})

if __name__ == "__main__":
    main()
