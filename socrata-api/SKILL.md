---
name: socrata-api
description: Use when querying or building dashboards against a Socrata-powered open-data portal — opendata.maryland.gov, data.cdc.gov, data.cityofnewyork.us, and the hundreds of other government portals built on Socrata. Covers endpoint discovery, SoQL ($where / $select / $limit / $order / $q), authentication with App Tokens, pagination, and robust fetch patterns in Python and JavaScript. Trigger whenever the user mentions Socrata, SoQL, a `/resource/<four-four>.json` URL, data.cdc.gov, opendata.maryland.gov, or any dataset identifier of the form `xxxx-xxxx`.
license: See repository LICENSE
---

# Socrata Open Data APIs

Technical reference for querying Socrata-powered portals. The same patterns work on every Socrata deployment because they all expose the same URL shape and SoQL query language.

## The two rules

**1. Live API, never mocked.** Generated code must call the Socrata endpoint at runtime (`fetch`, `requests`, etc.) and parse the JSON at runtime. Do not inline the dataset as a `const` or `list`.

**2. Verify the schema before writing code.** A Socrata URL like `https://opendata.maryland.gov/resource/9qyj-bhez.json` is an **identifier**. The four-four code (`9qyj-bhez`) tells you nothing about the columns. If the user gives you only a URL, **stop and ask** for:

1. The dataset's title (from the portal page).
2. A copy of the first row of JSON from the raw endpoint.

Then write the query. Guessing column names from the URL path or surrounding chat is the single most common cause of a dashboard that renders zero rows.

A good ask: *"That looks like a Socrata endpoint. Could you open the JSON URL in your browser and paste back the dataset title plus the first record? I need the column names before I can write the SoQL query."*

## Endpoint shape

```
https://{portal-domain}/resource/{dataset-id}.json
```

Examples:
- `https://data.cdc.gov/resource/cwsq-ngmh.json` (CDC PLACES)
- `https://opendata.maryland.gov/resource/sk8g-4e43.json` (Maryland population)
- `https://data.cityofnewyork.us/resource/erm2-nwe9.json` (NYC 311)

The `.json` suffix returns JSON. The portal also offers `.csv`, `.geojson` (when the dataset has geometry), and `.xml`. Prefer `.json` for apps and `.geojson` for maps when available.

To find the endpoint for a dataset: open its page on the portal → **API** button (sometimes under **Actions**) → copy the **API Endpoint**.

## Authentication — App Tokens

The API works without a token but is heavily throttled. For anything beyond a quick lookup, obtain an **App Token** from the portal (free; register an account, create a token in the user profile).

Pass the token as a header:

```
X-App-Token: YOUR_APP_TOKEN
```

Never hard-code the token. Read from an environment variable (`SOCRATA_APP_TOKEN`, `process.env.SOCRATA_APP_TOKEN`, etc.). Private datasets additionally require HTTP Basic Auth with portal username/password.

## SoQL — the query language

Socrata exposes **one endpoint per dataset** and customizes with query parameters prefixed with `$`.

| Parameter | Purpose | Example |
|---|---|---|
| `$where` | Filter rows (SQL-ish) | `$where=stateabbr = 'MD' AND year = '2022'` |
| `$select` | Project columns | `$select=locationname, measureid, data_value` |
| `$limit` | Row cap (default 1000) | `$limit=50000` |
| `$offset` | Pagination | `$offset=50000` (page 2 of 50k) |
| `$order` | Sort | `$order=year DESC, locationname ASC` |
| `$q` | Full-text search | `$q=Baltimore` |
| `$group` | Aggregation | `$group=county` |

**String values in `$where` must be single-quoted** (`'MD'`, not `"MD"`). Numeric values are bare. `IN(...)` works: `measureid IN('FOODINSECU', 'LACKTRPT')`.

### SoQL gotchas

- Column API names are usually `snake_case`, often different from the display label on the portal. Always check the raw JSON to confirm (`stateabbr`, not `State Abbreviation`).
- Dates in `$where` require ISO 8601 (`'2022-01-01T00:00:00.000'`) or `date >= '2022-01-01'` — not US formats.
- Numeric fields filter as numbers (`year = 2022`), but Socrata sometimes stores years as strings — check the sample row.
- `$limit=0` returns 0 rows + the row count in metadata (useful for pagination planning).

## Robust fetch patterns

### Python

```python
import os
import requests
import pandas as pd

base_url = "https://data.cdc.gov/resource/cwsq-ngmh.json"
measures = ["FOODINSECU", "LACKTRPT"]

# Build the $where clause — quote the string values
measures_sql = ",".join(f"'{m}'" for m in measures)
where = f"stateabbr = 'MD' AND year = '2022' AND measureid IN({measures_sql})"

# Let `requests` URL-encode the parameters for you — never concat by hand
params = {
    "$where": where,
    "$select": "locationname, measureid, data_value",
    "$limit": 10000,
}

headers = {"Accept": "application/json"}
token = os.getenv("SOCRATA_APP_TOKEN")
if token:
    headers["X-App-Token"] = token

try:
    resp = requests.get(base_url, headers=headers, params=params, timeout=30)
    if not resp.ok:
        # The body often contains the specific SoQL error, e.g. "query.soql.parsingError"
        print(f"HTTP {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    df = pd.DataFrame(resp.json())
    print(df.head())
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

### JavaScript (browser or Node)

```javascript
const endpoint = "https://opendata.maryland.gov/resource/sk8g-4e43.json";

async function fetchMarylandPopulation() {
  // Always use URLSearchParams — never string-concat the query
  const url = new URL(endpoint);
  const params = new URLSearchParams();
  params.append("$where", "year >= 2000");
  params.append("$order", "year DESC");
  url.search = params.toString();

  const headers = { Accept: "application/json" };
  const token = process.env.SOCRATA_APP_TOKEN; // or import.meta.env in Vite, etc.
  if (token) headers["X-App-Token"] = token;

  const res = await fetch(url, { headers });

  // fetch() does NOT throw on 4xx/5xx — check explicitly
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Socrata ${res.status}: ${body || res.statusText}`);
  }

  const data = await res.json();
  if (data.length === 0) {
    console.warn("No rows matched the query.");
  }
  return data;
}
```

## Implementation checklist

- [ ] Code hits a live Socrata endpoint — no static fixtures.
- [ ] The dataset's column names were confirmed by inspecting a real row before writing SoQL.
- [ ] Query parameters go through `URLSearchParams` / `requests.get(..., params=...)` — never string concatenation.
- [ ] `Accept: application/json` is set.
- [ ] `X-App-Token` is included when a token is available via env var.
- [ ] 4xx/5xx responses are inspected: print the response body (that's where the SoQL error message lives).
- [ ] Pagination is implemented (`$limit` + `$offset`) for datasets larger than ~50k rows.
- [ ] Empty-result responses (`[]`) are handled explicitly rather than crashing a downstream chart.

## Common failure modes

- **Guessing column names.** If `data_value` returns `undefined`, the column is probably `datavalue` or `value_num` on this dataset. Open the raw JSON once; read the keys.
- **Omitting the quotes in `$where`.** `measureid = FOODINSECU` is a syntax error. `measureid = 'FOODINSECU'` works.
- **Using `fetch` without checking `response.ok`.** Socrata returns a 400 with a JSON error body when SoQL is malformed. `await response.json()` on that body will succeed and give you `{error: true, message: ...}` — easy to miss. Check `res.ok` first.
- **Hitting default pagination.** Default `$limit` is **1000**. If your dashboard "has fewer rows than expected," you're probably hitting the default.
