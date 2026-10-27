# Maryland Geospatial Boundary Layers

Reference for every polygon layer Maryland iMap exposes for choropleth mapping. Each entry gives the URL, the joining key, property casing, and gotchas.

## Base URL structure

```
https://mdgeodata.md.gov/imap/rest/services/{Service}/{LayerName}/MapServer/{LayerID}/query
```

Required query parameters: `where=1%3D1&outFields=*&f=geojson`

The `f=geojson` parameter triggers the server-side reprojection from EPSG:3857 to EPSG:4326. Use the output directly in Leaflet / Mapbox / Google Maps. **Do not re-project.**

## 1. County boundaries (generalized)

24 jurisdictions: 23 counties + Baltimore City.

- **URL:** `https://mdgeodata.md.gov/imap/rest/services/Boundaries/MD_PhysicalBoundaries/MapServer/1/query?outFields=*&where=1%3D1&f=geojson`
- **Property casing:** **lowercase** (`county`, `county_fip`, `shape.STArea()`)
- **Join on:** `county` (full name) *or* `county_fip` (integer, no prefix, no padding)

### Properties

| Property | Type | Notes |
|---|---|---|
| `OBJECTID` | integer | Internal row id |
| `county` | string | Full name (e.g. `Allegany`, `Baltimore City`) |
| `district` | string | Legislative district number |
| `county_fip` | number | FIPS code — `1`, `3`, `47`. **Not** `"001"` or `"24001"` |
| `countynum` | number | Internal county id |
| `creation_d` | number | Unix timestamp |
| `last_updat` | number | Unix timestamp |
| `shape.STArea()` | number | Polygon area (lowercase `s`) |
| `shape.STLength()` | number | Polygon perimeter |

### County names (all 24, exact strings for joining)

`Allegany`, `Anne Arundel`, `Baltimore`, `Baltimore City`, `Calvert`, `Caroline`, `Carroll`, `Cecil`, `Charles`, `Dorchester`, `Frederick`, `Garrett`, `Harford`, `Howard`, `Kent`, `Montgomery`, `Prince George's`, `Queen Anne's`, `Somerset`, `St. Mary's`, `Talbot`, `Washington`, `Wicomico`, `Worcester`.

### FIPS normalization (critical)

When joining to Census or Socrata data that uses the 5-digit string FIPS (e.g. `"24001"`), normalize both sides:

```javascript
// Key from Socrata: "24001" → "001"
const socrataKey = item.fips.slice(-3);

// Key from iMap GeoJSON: 1 → "001"  (note lowercase county_fip)
const geojsonKey = String(feature.properties.county_fip).padStart(3, "0");
```

## 2. Municipal boundaries

Incorporated cities and towns.

- **URL:** `https://mdgeodata.md.gov/imap/rest/services/Boundaries/MD_PoliticalBoundaries/MapServer/2/query?outFields=*&where=1%3D1&f=geojson`
- **Property casing:** **UPPERCASE** (except `Shape.STArea()` which is TitleCase)
- **Join on:** `MUN_NAME` (uppercase string) or `JURSCODE` (four-letter code)

### Properties

| Property | Type | Notes |
|---|---|---|
| `OBJECTID` | integer | Internal row id |
| `MUN_NAME` | string | Full name UPPERCASE (`ANNAPOLIS`) |
| `JURSCODE` | string | Four-letter jurisdictional code |
| `Shape.STArea()` | number | Uppercase `S` |
| `Shape.STLength()` | number | Uppercase `S` |

### Municipality names

158 municipalities. Full list below (exact strings for joining; all UPPERCASE):

`ABERDEEN`, `ACCIDENT`, `ANNAPOLIS`, `BALTIMORE CITY`, `BARCLAY`, `BARNESVILLE`, `BARTON`, `BEL AIR`, `BERLIN`, `BERWYN HEIGHTS`, `BETTERTON`, `BLADENSBURG`, `BOONSBORO`, `BOWIE`, `BRENTWOOD`, `BROOKEVILLE`, `BROOKVIEW`, `BRUNSWICK`, `BURKITTSVILLE`, `CAMBRIDGE`, `CAPITOL HEIGHTS`, `CECILTON`, `CENTREVILLE`, `CHARLESTOWN`, `CHESAPEAKE BEACH`, `CHESAPEAKE CITY`, `CHESTERTOWN`, `CHEVERLY`, `CHEVY CHASE SECTION 3`, `CHEVY CHASE SECTION 5`, `CHEVY CHASE TOWN`, `CHEVY CHASE VIEW`, `CHEVY CHASE VILLAGE`, `CHURCH CREEK`, `CHURCH HILL`, `CLEAR SPRING`, `COLLEGE PARK`, `COLMAR MANOR`, `COTTAGE CITY`, `CRISFIELD`, `CUMBERLAND`, `DEER PARK`, `DELMAR`, `DENTON`, `DISTRICT HEIGHTS`, `EAGLE HARBOR`, `EAST NEW MARKET`, `EASTON`, `EDMONSTON`, `ELDORADO`, `ELKTON`, `EMMITSBURG`, `FAIRMOUNT HEIGHTS`, `FEDERALSBURG`, `FOREST HEIGHTS`, `FREDERICK`, `FRIENDSVILLE`, `FROSTBURG`, `FRUITLAND`, `FUNKSTOWN`, `GAITHERSBURG`, `GALENA`, `GALESTOWN`, `GARRETT PARK`, `GLEN ECHO`, `GLENARDEN`, `GOLDSBORO`, `GRANTSVILLE`, `GREENBELT`, `GREENSBORO`, `HAGERSTOWN`, `HAMPSTEAD`, `HANCOCK`, `HAVRE DE GRACE`, `HEBRON`, `HENDERSON`, `HIGHLAND BEACH`, `HILLSBORO`, `HURLOCK`, `HYATTSVILLE`, `INDIAN HEAD`, `KEEDYSVILLE`, `KENSINGTON`, `KITZMILLER`, `LA PLATA`, `LANDOVER HILLS`, `LAUREL`, `LAYTONSVILLE`, `LEONARDTOWN`, `LOCH LYNN HEIGHTS`, `LONACONING`, `LUKE`, `MANCHESTER`, `MARDELA SPRINGS`, `MARTINS ADDITIONS`, `MARYDEL`, `MIDDLETOWN`, `MIDLAND`, `MILLINGTON`, `MORNINGSIDE`, `MOUNT AIRY`, `MOUNT RAINIER`, `MOUNTAIN LAKE PARK`, `MYERSVILLE`, `NEW CARROLLTON`, `NEW MARKET`, `NEW WINDSOR`, `NORTH BEACH`, `NORTH BRENTWOOD`, `NORTH CHEVY CHASE`, `NORTH EAST`, `OAKLAND`, `OCEAN CITY`, `OXFORD`, `PERRYVILLE`, `PITTSVILLE`, `POCOMOKE CITY`, `POOLESVILLE`, `PORT DEPOSIT`, `PORT TOBACCO`, `PRESTON`, `PRINCESS ANNE`, `QUEEN ANNE`, `QUEENSTOWN`, `RIDGELY`, `RISING SUN`, `RIVERDALE PARK`, `ROCK HALL`, `ROCKVILLE`, `ROSEMONT`, `SALISBURY`, `SEAT PLEASANT`, `SECRETARY`, `SHARPSBURG`, `SHARPTOWN`, `SMITHSBURG`, `SNOW HILL`, `SOMERSET`, `ST. MICHAELS`, `SUDLERSVILLE`, `SYKESVILLE`, `TAKOMA PARK`, `TANEYTOWN`, `TEMPLEVILLE`, `THURMONT`, `TRAPPE`, `UNION BRIDGE`, `UNIVERSITY PARK`, `UPPER MARLBORO`, `VIENNA`, `WALKERSVILLE`, `WASHINGTON GROVE`, `WESTERNPORT`, `WESTMINSTER`, `WILLARDS`, `WILLIAMSPORT`, `WOODSBORO`.

## 3. Legislative districts (2022)

Maryland State Senate / House of Delegates districts.

- **URL:** `https://mdgeodata.md.gov/imap/rest/services/Boundaries/MD_ElectionBoundaries/MapServer/1/query?outFields=*&where=1%3D1&f=geojson`
- **Property casing:** mixed; `Shape` uses uppercase `S`
- **Join on:** `DISTRICT` (string — note multi-member district suffixes like `11A`, `11B`)

### Properties

| Property | Type | Notes |
|---|---|---|
| `OBJECTID` | integer | Internal id |
| `DISTRICT` | string | `10`, `11A`, `11B`, `27A`, `01B` — note zero-padding on 1-9 |
| `State_Senator` | string | Full name |
| `State_Representative_1` | string | First delegate |
| `State_Representative_2` | string | Second delegate (may be null) |
| `State_Representative_3` | string | Third delegate (may be null) |
| `State_Senator_Party` | string | Party |
| `State_Representative_{1,2,3}_Party` | string | |
| `StateSenator_MDManualURL` | string | Link to the Maryland Manual bio |
| `StateRepresentative{1,2,3}MDManualURL` | string | |
| `Latitude` | number | District centroid |
| `Longitude` | number | District centroid |
| `Shape.STArea()` / `Shape.STLength()` | number | Uppercase `S` |

### District codes (exact strings)

`01A`, `01B`, `01C`, `02A`, `02B`, `03`, `04`, `05`, `06`, `07A`, `07B`, `08`, `09A`, `09B`, `10`, `11A`, `11B`, `12A`, `12B`, `13`, `14`, `15`, `16`, `17`, `18`, `19`, `20`, `21`, `22`, `23`, `24`, `25`, `26`, `27A`, `27B`, `27C`, `28`, `29A`, `29B`, `29C`, `30A`, `30B`, `31`, `32`, `33A`, `33B`, `33C`, `34A`, `34B`, `35A`, `35B`, `36`, `37A`, `37B`, `38A`, `38B`, `38C`, `39`, `40`, `41`, `42A`, `42B`, `42C`, `43A`, `43B`, `44A`, `44B`, `45`, `46`, `47A`, `47B`.

## 4. 5-digit ZIP code boundaries

Generalized ZIP Code Tabulation Areas within Maryland.

- **URL:** `https://mdgeodata.md.gov/imap/rest/services/Boundaries/MD_PoliticalBoundaries/MapServer/4/query?outFields=*&where=1%3D1&f=geojson`
- **Property casing:** UPPERCASE; `Shape` uses uppercase `S`
- **Join on:** `ZIPCODE1` (5-digit string)

### Properties

| Property | Type | Notes |
|---|---|---|
| `OBJECTID` | integer | Internal id |
| `ZIPCODE1` | string | 5-digit ZIP as string (`"21201"`) |
| `ZIPNAME` | string | Primary city/town for the ZIP |
| `EXISTING` | string | Internal version marker |
| `Shape.STArea()` / `Shape.STLength()` | number | Uppercase `S` |

## Full example — county choropleth

Fetch the generalized county boundaries, join to an external population dataset, hand to Leaflet.

```javascript
const countyBoundariesUrl =
  "https://mdgeodata.md.gov/imap/rest/services/Boundaries/MD_PhysicalBoundaries/MapServer/1/query?outFields=*&where=1%3D1&f=geojson";

const countyPopulation = [
  { countyName: "Anne Arundel", population: 590336 },
  { countyName: "Baltimore City", population: 576498 },
  { countyName: "Prince George's", population: 955363 },
  // ...fill in the remaining 21 jurisdictions
];

async function buildChoropleth() {
  const res = await fetch(countyBoundariesUrl);
  if (!res.ok) throw new Error(`iMap responded ${res.status}`);
  const geo = await res.json();

  geo.features.forEach((f) => {
    const match = countyPopulation.find(
      (r) => r.countyName === f.properties.county, // lowercase!
    );
    f.properties.population = match ? match.population : null;
  });

  return geo;
}

buildChoropleth().then((merged) => {
  // L.geoJSON(merged, { style: byPopulation }).addTo(map);
});
```
