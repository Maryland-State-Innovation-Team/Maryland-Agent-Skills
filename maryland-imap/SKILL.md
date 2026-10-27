---
name: maryland-imap
description: Use when building Maryland maps, choropleths, or geocoding workflows against the official Maryland iMap ArcGIS REST services at mdgeodata.md.gov. Covers geospatial boundary layers (counties, municipalities, legislative districts, ZIP codes, and more) and the geocoder (batch geocoding, reverse geocoding, address candidates). Trigger whenever the user asks for Maryland GeoJSON, a map of Maryland jurisdictions, geocoding of Maryland addresses, Maryland iMap, mdgeodata, or an ArcGIS FeatureServer/MapServer within Maryland state government.
license: See repository LICENSE
metadata:
  source: Maryland iMap (mdgeodata.md.gov)
---

# Maryland iMap

Technical reference for Maryland's official ArcGIS REST services at **`mdgeodata.md.gov/imap/rest/services/`**. Covers two capability areas:

- **Boundaries** — polygon layers for jurisdictions, districts, and ZIP codes. See [references/boundaries.md](references/boundaries.md).
- **Geocoding** — forward (batch), reverse, and address-candidate lookups. See [references/geocoding.md](references/geocoding.md).

Authentication: **none** (public service). No API key, no rate-limit header. Use responsibly.

## Decide which reference to load

- "Make a map of Maryland {counties, cities, districts, ZIP codes}" → [references/boundaries.md](references/boundaries.md)
- "Geocode / plot / look up {addresses} in Maryland" → [references/geocoding.md](references/geocoding.md)
- Both (map addresses onto a jurisdiction choropleth) → load both

## The three directives for every iMap task

**1. Live API, never mocked.** The generated code must call the live endpoint at runtime with `fetch` (or the language's equivalent). Do not inline the GeoJSON response as a `const` or paste coordinates. If you need to seed test data, call the API once and let the user cache it — but the shipped code must hit the live service.

**2. Prefer MapServer over FeatureServer for boundary layers.** The `MapServer` endpoints respond faster and are less likely to return `504 Gateway Timeout` on complex geometries than their `FeatureServer` siblings. Only use `FeatureServer` when you need edit operations the user has explicitly asked for.

**3. Know the CRS before you plot.**
- **Boundary layers served with `f=geojson`** → the API transforms to **EPSG:4326** (WGS 84 lat/lng) for you. Use directly with Leaflet, Mapbox, Google Maps. **Do not re-project.**
- **Geocoder responses** → always **EPSG:3857** (Pseudo-Mercator). You **must** convert to EPSG:4326 before plotting. Use `proj4js` or an equivalent library.

Confusing these is the #1 failure mode. If a point lands in the ocean off the African coast, you forgot to project geocoder output.

## Shared query patterns

All layer `query` endpoints accept these parameters:

| Param | Value | Purpose |
|---|---|---|
| `where` | `1=1` | Return all features |
| `outFields` | `*` | Return all attributes |
| `f` | `geojson` | Output format (triggers the EPSG:4326 reprojection) |
| `returnGeometry` | `true` / `false` | Omit shapes when you only need attributes |

URL-encode the `where` clause (`1%3D1` for `1=1`).

## Common failure modes

- **FIPS codes don't match.** The county layer returns `county_fip` as a *number* (e.g. `1`), without the `24` state prefix or leading zeros. Socrata and Census data use five-digit strings (`"24001"`). Normalize to a common form before joining — see [references/boundaries.md](references/boundaries.md) for the exact fix.
- **Property casing varies by layer.** County boundaries use lowercase (`county`, `shape.STArea()`); municipalities use UPPERCASE (`MUN_NAME`, `Shape.STArea()`). Always read the per-layer property section before writing a `properties.X` reference.
- **Mixing MapServer and FeatureServer URLs.** They have different layer IDs. Pick one family and stay in it.
- **Forgetting to URL-encode the geocoder JSON payload.** The `addresses` form field is a JSON string that must then be URL-encoded; double-encoding is wrong, single-encoding is required.

## Implementation checklist

- [ ] Code makes a live `fetch` (or equivalent) to the documented endpoint — no static data.
- [ ] Boundary GeoJSON is used as-is (EPSG:4326); geocoder output is converted from EPSG:3857 before plotting.
- [ ] Property names are copied verbatim from the reference, with correct casing.
- [ ] Joins to external data normalize keys on both sides (FIPS padding, case, state prefix).
- [ ] No API token is sent — the service is public.
