# veiko-data

Pulls metering data for your home metering point from the Elering Estfeed customer portal API into a pandas DataFrame, and writes it to CSV.

## Getting Started

Prerequisites: Python 3.14+, [uv](https://docs.astral.sh/uv/), and an Elering API key (client id + secret) from the customer portal.

```bash
# 1. Enter the project
cd veiko-data

# 2. Install dependencies (creates .venv, pinned by uv.lock)
uv sync

# 3. Configure — priority: system env → config/.env → config/.env.example
cp config/.env.example config/.env
# edit config/.env: ELERING_CLIENT_ID, ELERING_CLIENT_SECRET and ELERING_EIC are required.
# The two URLs already have working values in config/.env.example.

# 4. Verify the install (must pass before you continue)
uv run pytest

# 5. Run it — one day of hourly data for the configured metering point
uv run main.py --start 2026-01-01 --end 2026-01-02
```

Step 5 writes `data/<eic>_20260101_20260102.csv` and prints a summary line:

```
24 rows | 2026-01-01 00:00:00+00:00 -> 2026-01-01 23:00:00+00:00 | consumption 13.310 kWh | production 0.000 kWh
```

If step 5 fails, see [Troubleshooting](#troubleshooting).

## Usage

Ranges longer than the API's 31-day cap are split automatically, with the required 5-second pause between requests. A full year is 12 requests and takes about a minute.

```bash
# A full year, daily resolution, to a chosen file
uv run main.py --start 2025-01-01 --end 2026-01-01 --resolution one_day --out data/2025.csv

# A different metering point (repeat --eic for up to 10)
uv run main.py --start 2026-01-01 --end 2026-02-01 --eic 38ZEE-10000000-A

# Debug logging: one line per token and per window
uv run main.py --start 2026-01-01 --end 2026-01-02 -v
```

`--end` is exclusive. Dates may be `2026-01-01` or `2026-01-01T00:00:00Z`; naive input is read as UTC.

From a notebook or another script:

```python
from main import Settings, fetch_metering_data, parse_moment

df = fetch_metering_data(
    Settings(),
    parse_moment("2026-01-01"),
    parse_moment("2026-02-01"),
    "one_hour",
)
```

The frame has one row per interval, sorted by metering point then time:

| column | dtype | notes |
|---|---|---|
| `metering_point_eic` | `string` | |
| `period_start` | `datetime64[ns, UTC]` | start of the interval |
| `consumption_kwh` / `production_kwh` | `float64` | electricity |
| `consumption_m3` / `production_m3` | `float64` | gas; `NaN` for an electricity point |

**`--resolution` values are not published** in Elering's OpenAPI spec — only `one_day` appears, in their manual's example. The value is passed through to the API verbatim, and a rejected one comes back with the server's own message listing what it accepts. `one_hour` is the default.

## Configuration

`config/.env` (git-ignored), `KEY=value`. Blank values count as unset, so a half-filled file fails at startup rather than at the 401.

| Variable | Required | Default | Description |
|---|---|---|---|
| `ELERING_CLIENT_ID` | yes | — | API key client id |
| `ELERING_CLIENT_SECRET` | yes | — | API key client secret |
| `ELERING_EIC` | yes | — | Your metering point EIC code |
| `ELERING_TOKEN_URL` | yes | set in `.env.example` | Keycloak token endpoint |
| `ELERING_API_BASE_URL` | yes | set in `.env.example` | Portal base URL |

An unrecognised `ELERING_*` key in a `.env` file is an error, not a silent no-op — a typo like `ELERING_TOEKN_URL` fails at startup.

## Development

```bash
uv run pytest                 # tests + coverage gate (no network: httpx.MockTransport)
uv run ruff check .           # lint
uv run ruff format .          # format
uv run mypy --strict main.py test_main.py
```

## Reading the logs

Every run prints its trail at INFO, so an empty result is always attributable. A healthy run:

```
info  fetch.start        eics=['38ZEE-...'] start=... end=... resolution=one_hour windows=1
info  window.start       n=1/1 start=... end=...
info  auth.requesting    client_id=veiko-home token_url=https://kc.elering.ee/...
info  auth.ok            scope='read:metering-data profile' expires_in=300 token_chars=190
info  request.sent       method=GET url='https://estfeed.elering.ee/api/public/v1/metering-data?startDateTime=...'
info  response.received  status=200 elapsed_ms=412 bytes=1997
info  point.data         eic=38ZEE-... intervals=24
info  fetch.done         rows=24 first=... last=...
```

`request.sent` is the fully-encoded URL — paste it into `curl` with a bearer header to reproduce a call by hand. The access token is never logged (only `token_chars`), and neither is the client secret.

When nothing comes back, the event that fires tells you which of the three causes it was:

| Event | Level | Meaning |
|---|---|---|
| `auth.ok` missing, `fetch.failed` with `401` | error | Credentials rejected — the request was never made |
| `auth.ok` with a `scope` lacking `read:metering-data` | info | Key authenticated but was issued without data access |
| `response.no_metering_points` | warning | `200 OK` with an empty array — the EIC is not on this API key |
| `point.no_data` | warning | Point exists, no error, but zero intervals — period outside your grid agreement, or no readings at that resolution |
| `point.error` | warning | The API rejected that one point; `trace_id` is quotable to Elering support |
| `fetch.empty` | warning | Summary: everything succeeded, nothing came back |
| `fetch.failed` with a `400` | error | Bad parameter; the message quotes the API's own reason verbatim |

Add `-v` for debug level. An empty result still writes a (headers-only) CSV and exits `0` — the query succeeded, so it is not an error; the warnings say why it was empty.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `3 validation errors for Settings` | `config/.env` missing or blank | `cp config/.env.example config/.env`, fill in the three required keys |
| `token request failed [401]: invalid_client` | Wrong client id/secret | Re-check the API key in the customer portal |
| `metering-data request failed [400]` | Bad `--resolution`, or range end before start | The message quotes the API's reason verbatim |
| `at most 10 metering points per request` | More than 10 `--eic` flags | Split into several runs |
| `all N metering point responses returned an error` | No valid grid agreement for those EICs in that period | Check the date range against your contract |
| Empty CSV, exit 0 | Range valid but no data recorded | Try a wider range or a coarser `--resolution` |

Requests are rate limited to one every 5 seconds. The script paces itself; a `429` still gets one retry after 10s before failing.
