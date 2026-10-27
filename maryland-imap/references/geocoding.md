# Maryland iMap Geocoder

Reference for the ArcGIS GeocodeServer that converts Maryland addresses to coordinates (and vice versa).

## Base URL

```
https://mdgeodata.md.gov/imap/rest/services/GeocodeServices/MD_MultiroleLocator/GeocodeServer/
```

## Critical: coordinate reference system

**All geocoder input and output coordinates are in `EPSG:3857` (Pseudo-Mercator).**

- Received a point → convert `3857 → 4326` before plotting on Leaflet / Mapbox / Google Maps.
- Sending a point (for reverse geocoding) → convert `4326 → 3857` before including it in the request.

Use `proj4js` (or your language's `pyproj`, `proj` crate, etc.). Skipping this is the single most common bug — a Maryland address will show up off the African coast if you treat the output `x`/`y` as lat/lng.

```javascript
import proj4 from "proj4";

const sourceCRS = "EPSG:3857"; // geocoder output
const destCRS = "EPSG:4326";   // standard lat/lng

const [lng, lat] = proj4(sourceCRS, destCRS, [location.x, location.y]);
```

## Endpoints

### 1. Batch geocode — multi-field addresses

Best for high-volume batch geocoding when you already have address components.

- **Endpoint:** `geocodeAddresses`
- **Method:** `POST`
- **Content-Type:** `application/x-www-form-urlencoded`
- **Body:** `f=json&addresses=<url-encoded JSON>`

The `addresses` field is a JSON object with a `records` array; **URL-encode the JSON string** when appending it to the form body (don't double-encode).

Payload shape:

```json
{
  "records": [
    {
      "attributes": {
        "OBJECTID": 1,
        "Address": "501 E Pratt St",
        "City": "Baltimore",
        "Zip": "21202"
      }
    },
    {
      "attributes": {
        "OBJECTID": 2,
        "Address": "333 W Camden St",
        "City": "Baltimore",
        "Zip": "21201"
      }
    }
  ]
}
```

- `OBJECTID` is a client-supplied id. It round-trips as `attributes.ResultID` in the response — use it to map results back to your inputs.

Response shape:

```json
{
  "spatialReference": { "wkid": 3857, "latestWkid": 3857 },
  "locations": [
    {
      "address": "501 E Pratt St, Baltimore, Maryland, 21202",
      "location": { "x": -8527878.29, "y": 4758235.13 },
      "score": 100,
      "attributes": { "ResultID": 1 }
    }
  ]
}
```

- `score` is 0–100 (confidence).
- Low scores (< 85) often mean the address was fuzzy-matched; surface them to the user.

### 2. Batch geocode — single-line addresses

Same endpoint, different attribute shape.

- **Endpoint:** `geocodeAddresses`
- **Payload:**

```json
{
  "records": [
    {
      "attributes": {
        "OBJECTID": 1,
        "SingleLine": "501 E Pratt St, Baltimore, MD 21202"
      }
    }
  ]
}
```

Use this when the user hands you free-text addresses rather than structured components.

### 3. Reverse geocode

Convert a known coordinate to the nearest address.

- **Endpoint:** `reverseGeocode`
- **Method:** `GET`
- **Query parameters:**
  - `location` — `x,y` in **EPSG:3857**, e.g. `-8527878,4758235`
  - `distance` (optional) — search radius in meters
  - `f=json`

Example: `.../reverseGeocode?f=json&location=-8527878,4758235`

Response:

```json
{
  "address": { "Match_addr": "501 E Pratt St, Baltimore, Maryland, 21202" },
  "location": { "x": -8527878, "y": 4758235 }
}
```

### 4. Find address candidates

Return multiple possible matches with scores. Useful for an autocomplete UI.

- **Endpoint:** `findAddressCandidates`
- **Method:** `GET`
- **Query parameters:** any of `SingleLine`, `Address`, `City`, `Postal`, plus `maxLocations` and `f=json`.

Example: `.../findAddressCandidates?f=json&SingleLine=501 E Pratt St&maxLocations=5`

Response: `{ "candidates": [{ "address", "location", "score" }, ...] }`

## Full example — batch geocode + project

```javascript
import proj4 from "proj4";

const geocodeURL =
  "https://mdgeodata.md.gov/imap/rest/services/GeocodeServices/MD_MultiroleLocator/GeocodeServer/geocodeAddresses";

const sourceCRS = "EPSG:3857";
const destCRS = "EPSG:4326";

const addresses = [
  { id: 1, street: "501 E Pratt St", city: "Baltimore", zip: "21202" },
  { id: 2, street: "333 W Camden St", city: "Baltimore", zip: "21201" },
];

const payload = {
  records: addresses.map((a) => ({
    attributes: {
      OBJECTID: a.id,
      Address: a.street,
      City: a.city,
      Zip: a.zip,
    },
  })),
};

async function geocode(records) {
  const body = `f=json&addresses=${encodeURIComponent(JSON.stringify(records))}`;
  const res = await fetch(geocodeURL, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error(`Geocoder responded ${res.status}`);
  const data = await res.json();

  return data.locations.map((loc) => {
    const [lng, lat] = proj4(sourceCRS, destCRS, [loc.location.x, loc.location.y]);
    return {
      resultId: loc.attributes.ResultID,
      address: loc.address,
      score: loc.score,
      lat,
      lng,
    };
  });
}

geocode(payload).then((points) => {
  // L.marker([p.lat, p.lng]) for each
});
```

## Checklist

- [ ] POST body is form-encoded; the `addresses` value is the URL-encoded JSON string (single-encoded).
- [ ] Every output `(x, y)` is converted from EPSG:3857 to EPSG:4326 before plotting.
- [ ] Every input `(x, y)` for reverse geocoding is converted from EPSG:4326 to EPSG:3857 before sending.
- [ ] `OBJECTID` round-trips through `attributes.ResultID` so you can rejoin to source records.
- [ ] Low-score results (`< 85`) are flagged or surfaced to the user instead of silently plotted.
