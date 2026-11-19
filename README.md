# FedSync Emergency Engine

> A live federal emergency data MCP server for IBM Bob — providing real-time weather telemetry, FEMA disaster declarations, and U.S. Treasury reserve balances via natural language queries.

---

## Overview

FedSync Emergency Engine is a custom [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server built for IBM Bob. It connects Bob to live federal data sources — Open-Meteo/NOAA weather grids, the OpenFEMA Disaster Declarations API, and the U.S. Treasury Fiscal Data API — so you can query emergency conditions directly from the Bob chat interface.

Built for the IBM Bob Hackathon.

---

## Tools

| Tool | Description |
|---|---|
| `get_incident_weather` | Live weather telemetry (temperature, wind, gusts, precipitation, severe condition codes) for a 2-letter US state |
| `get_disaster_declarations` | Active FEMA major disaster declarations and assistance programs for a 2-letter US state |
| `get_disaster_fund_balance` | U.S. Treasury General Account (TGA) operating cash balance |

---

## Supported States

| Code | State |
|---|---|
| FL | Florida |
| TX | Texas |
| CA | California |
| NY | New York |
| LA | Louisiana |
| NC | North Carolina |
| GA | Georgia |
| WA | Washington |
| IL | Illinois |
| OH | Ohio |
| PA | Pennsylvania |
| SC | South Carolina |

---

## Requirements

- Python 3.8+
- IBM Bob 2.1.0+
- No third-party Python packages — uses stdlib only (`sys`, `json`, `urllib`)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/fedsync-emergency-engine.git
cd fedsync-emergency-engine
```

### 2. Register the MCP server in IBM Bob

Add the following to `~/.bob/settings/mcp.json` (create the file if it doesn't exist):

```json
{
  "mcpServers": {
    "fedsync-emergency-engine": {
      "command": "python3",
      "args": ["/absolute/path/to/fedsync_mcp_server_live.py"],
      "alwaysAllow": [
        "get_incident_weather",
        "get_disaster_declarations",
        "get_disaster_fund_balance"
      ]
    }
  }
}
```

> Replace `/absolute/path/to/fedsync_mcp_server_live.py` with the actual path on your machine.

### 3. Enable auto-approval (optional but recommended)

In IBM Bob:
1. Click the gear icon → **MCP**
2. Expand **fedsync-emergency-engine**
3. Toggle **Always allow** on for each tool

### 4. Restart IBM Bob

The server connects automatically on startup. You should see **fedsync-emergency-engine** listed as connected in the MCP panel.

---

## Usage

Once connected, ask Bob naturally:

```
Check active NWS severe weather alerts and the most recent FEMA disaster declarations for Florida (FL).
```

```
What is the current U.S. Treasury disaster fund balance?
```

```
Show me live weather conditions and active FEMA declarations for North Carolina.
```

---

## Data Sources

| Source | API | Notes |
|---|---|---|
| Weather | [Open-Meteo](https://open-meteo.com) | Free, no API key required |
| FEMA Declarations | [OpenFEMA API v2](https://www.fema.gov/about/openfema/api) | Public, no API key required |
| Treasury Balance | [U.S. Treasury Fiscal Data API](https://fiscaldata.treasury.gov/api-documentation/) | Public, no API key required |

---

## Architecture

```
IBM Bob (chat)
     │
     ▼
MCP Tool Call (stdio)
     │
     ▼
fedsync_mcp_server_live.py
     │
     ├── get_incident_weather ──► Open-Meteo API (live)
     ├── get_disaster_declarations ──► OpenFEMA API (live / snapshot fallback)
     └── get_disaster_fund_balance ──► Treasury Fiscal Data API (live / snapshot fallback)
```

The server communicates with Bob over stdio using the [MCP protocol (2024-11-05)](https://spec.modelcontextprotocol.io). If a live `.gov` API is unreachable (WAF-restricted environments), the server falls back to a curated snapshot of recent declarations.

---
