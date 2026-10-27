# &lt;maryland-statewide-footer&gt;

The Lit-based web component containing the **statewide service-directory footer** ("Explore Maryland.gov" with links to Top services, Government, Policies, Connect, Alerts). **Required at the very bottom of every Maryland.gov agency page**, below the agency-specific `maryland-footer`.

> Zero configuration. Drop in the tag and it renders the full statewide footer with the canonical state services links. **Do not edit the link list** — it's the same across every Maryland.gov site by design, and updating it is the design system team's responsibility.

## What it looks like

Visually **identical** to the "statewide" half of `maryland-footer` (the component reuses `maryland-footer` SCSS classes internally). Specifically:

- Dark `ink` (near-black) full-width background.
- Content constrained to a `widescreen` (1400px) `grid-container` with site margins.
- A large `<h2>` "Explore Maryland.gov" at the top (22px / `body-11`, semibold, white).
- A grid of five `<nav>` link-groups: **Top services**, **Government**, **Policies**, **Connect**, **Alerts**. Each group is a heading (`<h3>`, 16px semibold white) over an unstyled bulleted list of 4–8 links (14px / `body-4`, color `base-lighter`).
- Layout: 1 column on mobile, 2 columns at tablet (≥640px), 4 columns at desktop (≥1024px). Groups flow into the column layout via CSS `column-count`.
- A 1px `base-darker` horizontal divider with ~`units(7)` vertical margin at desktop.
- Bottom branding row: horizontal Maryland wordmark (inverted/white, 176×36px) on the left, copyright "© {current year} State of Maryland. All rights reserved." on the right (stacked on mobile, flex-space-between at desktop).

The footer content is fixed — there's no way to customize the link list, headings, or wordmark without a feature request to the MDWDS team.

## Default markup

```html
<!-- 1. Load the bundle that REGISTERS Lit custom elements (mdwds-core.js alone is NOT enough) -->
<script type="module" src="https://cdn.maryland.gov/mdwds/latest/js/mdwds-elements.js"></script>

<!-- 2. Place the element at the very bottom of the page -->
<maryland-statewide-footer></maryland-statewide-footer>
```

That's it. No attributes. No slot content. No props.

> **Critical:** `mdwds-core.js` does NOT register `<maryland-statewide-footer>`. The element is defined by `mdwds-elements.js` (or the per-component standalone script at `components/maryland-statewide-footer.js`). If you only load `mdwds-core.js`, this tag renders as an empty unknown HTML element. See `references/setup.md`.

## Placement in the page shell

Per `references/page-shell.md`:

```html
<body>
  <a class="usa-skipnav" href="#main-content">Skip to main content</a>
  <section class="usa-banner" aria-label="Official website of the State of Maryland">...</section>
  <header class="maryland-header">...</header>
  <main id="main-content" tabindex="-1">...</main>
  <footer class="maryland-footer">...</footer>          <!-- Agency footer -->
  <maryland-statewide-footer></maryland-statewide-footer>  <!-- Statewide footer (last) -->
</body>
```

## What you get (the rendered DOM)

The component renders the same structure that the HTML `maryland-footer` produces when `displaySitewide: true`. The full markup includes:

- `<footer class="maryland-footer">` wrapper
- `<div class="maryland-footer__container">` (grid container)
- `<section class="maryland-footer__section" aria-labelledby="global-footer">`
- `<h2 class="maryland-footer__title" id="global-footer">Explore Maryland.gov</h2>`
- `<div class="maryland-footer__content">` containing 5 `<nav class="maryland-footer__link-group">` blocks
- `<hr aria-hidden="true" class="maryland-footer__divider">`
- `<div class="maryland-footer__branding">` with the horizontal inverted Maryland wordmark and copyright

See `references/components/maryland-footer.md` for the class table — every rendered class is the same.

## What each class does

All visual styling comes from the published CSS. The component pulls in the MDWDS stylesheet during its connected lifecycle. Refer to `references/components/maryland-footer.md` for the full class table — the statewide variant uses these classes from there:

- `maryland-footer`, `maryland-footer__container`, `maryland-footer__section`
- `maryland-footer__title`, `maryland-footer__content`
- `maryland-footer__link-group`, `maryland-footer__link-group-heading`, `maryland-footer__link-group-list`
- `maryland-footer__divider`
- `maryland-footer__branding`, `maryland-footer__logo`, `maryland-footer__copyright`

## Prop schema

None required. The component is zero-config in English and takes a small handful of optional attributes/properties for i18n (see below).

| Attribute / property | Type | Default | Notes |
|---|---|---|---|
| `locale` (attribute) | string (BCP-47) | `"en"` | Target locale. Any English tag (`en`, `EN`, `en-US`, `en_US`, `eng`, empty, non-string) short-circuits to the bundled English catalog without any fetch. Non-English values trigger a catalog fetch. |
| `catalog-url` (attribute) | string (URL) | — | Override the default locale JSON endpoint. Only used when `locale` is non-English. |
| `catalog` (property, JS only) | `{locale, strings}` | — | Pre-resolved catalog object set imperatively from JS. Wins over `locale`/`catalog-url` fetching. Required when using the `light-dom` opt-out. |
| `light-dom` (attribute) | boolean | — | Opt out of Shadow DOM. Breaks slot-based translation — use `catalog` instead when set. |

## i18n and the `<maryland-translate>` picker (0.48.0+)

Introduced in **MDWDS 0.48.0** and completed in **0.50.3**, the footer carries its own locale/catalog system. A separate, independent `<maryland-translate>` web component provides a visitor-facing language-picker modal that invokes Google Translate on the whole page. The two features are often confused — they are not the same thing.

### Footer catalog system

The component ships with a bundled English catalog of **33 keys**:

- 1 title (`title`)
- 5 group headings (`group.<id>.heading` for `top-services`, `government`, `policies`, `connect`, `alerts`)
- 25 link labels (`link.<slug>`)
- 2 branding strings (`branding.logo-alt`, `branding.copyright`)

**32 of the 33 keys are exposed as named slots.** `branding.logo-alt` is the exception, because it feeds an `<img alt>` attribute, and attributes can't be slotted. That one is catalog-only.

### Four integration paths

| If this describes you | Do this |
|---|---|
| You render English only. | Nothing. English is the default, needs no configuration, and stays machine-translatable. |
| Your CMS or TMS already owns certified per-page translations. | Project a `<span slot="<catalog-key>">` child for each string you want to override, or set the `catalog` property if you hold a whole translated catalog. |
| You want state-owned translations that update without a redeploy. | Set `locale` and let the component fetch `i18n/maryland-statewide-footer/<locale>.json`. Catalogs are cached one hour, so a corrected string reaches visitors within the hour without a release. Set `catalog-url` to serve your own JSON instead. |
| You use the `light-dom` attribute. | Use the `catalog` property. Slots don't project without a shadow root; a `<span slot="…">` child next to a `light-dom` instance renders as unstyled text outside the footer while the footer keeps rendering its English fallback. |

### Markup — slot override

Pick-and-choose per-string override. Each child uses a `slot` attribute matching a catalog key.

```html
<maryland-statewide-footer>
  <span slot="title">Explorar Maryland.gov</span>
  <span slot="group.top-services.heading">Servicios principales</span>
  <span slot="link.vehicle-services">Servicios para vehículos</span>
  <span slot="link.taxes">Impuestos</span>
  <span slot="branding.copyright">© {year} Estado de Maryland. Todos los derechos reservados.</span>
</maryland-statewide-footer>
```

The `{year}` placeholder in `branding.copyright` is replaced with the current four-digit year at render time. Keep it literal in your string.

### Markup — hosted catalog fetch

Request a specific locale. The footer fetches `./i18n/maryland-statewide-footer/<locale>.json` relative to the page.

```html
<maryland-statewide-footer locale="es"></maryland-statewide-footer>
```

Or point at your own endpoint:

```html
<maryland-statewide-footer
  locale="es"
  catalog-url="https://cms.example.gov/i18n/footer-es.json"
></maryland-statewide-footer>
```

The fetched JSON shape:

```json
{
  "locale": "es",
  "strings": {
    "title": "Explorar Maryland.gov",
    "group.top-services.heading": "Servicios principales",
    "link.vehicle-services": "Servicios para vehículos",
    "link.taxes": "Impuestos"
  }
}
```

- `locale` is **required**. Without it the catalog is rejected and English renders. The value stamps `lang` / `xml:lang` on the rendered `<footer>` so screen readers announce the right language.
- `strings` is a map from catalog key → translated string. Missing keys fall back to English per-key (not whole-catalog). Every value must be a string.

### Markup — imperative catalog (JS property)

Required when using `light-dom`; also usable in Shadow DOM mode.

```html
<maryland-statewide-footer light-dom></maryland-statewide-footer>

<script type="module">
  const footer = document.querySelector("maryland-statewide-footer");
  footer.catalog = {
    locale: "es",
    strings: {
      title: "Explorar Maryland.gov",
      "group.top-services.heading": "Servicios principales",
      "link.vehicle-services": "Servicios para vehículos",
    },
  };
</script>
```

### Resolution order

For any given string, the value is resolved in this order — first match wins:

1. **Slot** — a `<span slot="…">` child always wins visually, regardless of locale, as long as the instance uses Shadow DOM.
2. **`catalog` property** — a fully-resolved catalog object set on the element. When present it wins outright and no network fetch happens.
3. **`catalog-url` attribute** — a host-owned JSON endpoint, replacing the default CDN location when a fetch is performed.
4. **CDN locale JSON** — the default `i18n/maryland-statewide-footer/<locale>.json` endpoint, fetched when `locale` is non-English and neither `catalog` nor `catalog-url` is provided.
5. **Bundled English** — the last-resort fallback. Any missing key in a fetched or supplied catalog falls back per-key; any fetch failure (network error, non-2xx, malformed shape) falls back to the full English catalog.

The `lang` / `xml:lang` attributes always report the **effective rendered locale**, not the requested one. A failed Spanish fetch renders English under `lang="en"` instead of mislabelling the content.

### Machine-translation opt-out

When the footer renders a **non-English** catalog it marks its root `<footer>` with both `translate="no"` and the `notranslate` class so machine translators (Google Translate, browser auto-translate) don't re-translate strings the component has already translated. Re-translating certified copy degrades its quality; the opt-out protects it.

```html
<!-- Rendered output when locale != "en" -->
<footer class="maryland-footer notranslate" translate="no" lang="es" xml:lang="es">
  ...
</footer>
```

The rendered `<footer>` also carries the `maryland-footer` class so it inherits the shared statewide/agency footer styling.

### English detection

The following values ALL count as English and short-circuit the fetch path to the bundled catalog:

- `en`, `EN`, `en-US`, `en_US`, `eng`
- Whitespace-padded values of the above
- The empty string, `null`, `undefined`, or any non-string

Consequence: there's no way to load a regional English catalog like `en-GB.json` via the `locale` attribute. If you need region-specific English copy, supply it with the `catalog` property or slot overrides. The trade-off is deliberate — silently fetching an `en-US.json` that almost no host publishes produced guaranteed console warnings on every page load.

### Console diagnostics

When something is misconfigured, the component writes a prefixed console message (`maryland-statewide-footer:`). The most common ones:

| Message | What happened |
|---|---|
| `supplied "catalog" has no "locale" field` (error) | Catalog rejected, English rendered — `lang`/`xml:lang` could not describe the strings (WCAG 2.1 SC 3.1.2). Add `locale` to the catalog object. |
| `supplied "catalog" is not a valid locale catalog` (warn) | Shape validation failed. A catalog is `{ locale, strings }` where every value in `strings` is a string. |
| `"catalog-url" is ignored when the locale is English` (warn) | `locale` is unset or exactly English, which never takes the fetch path. Set `locale` to a non-English value. |
| `failed to load locale catalog "<x>"; falling back to English` (warn) | The fetch threw, returned non-2xx, or returned an unusable shape. English rendered. |
| `slot projection requires a shadow root, but this instance uses the "light-dom" opt-out` (warn) | Slots were supplied to a `light-dom` instance. Use the `catalog` property instead. The warning names the affected slots. |
| `global fetch is unavailable; falling back to English` (warn) | No global `fetch` (older SSR context). English rendered. |

### `<maryland-translate>` — the visitor language picker

A **separate, independent** web component registered by `mdwds-elements.js`. It renders a small globe-icon button; tapping it opens a modal with a list of 100+ languages, each triggering Google Translate on the whole page. It is **not** the footer's i18n system — it's a visitor-facing translation shortcut.

```html
<maryland-translate></maryland-translate>
```

Minimal zero-config: drop the tag anywhere (typical placements: inside `<maryland-utility-nav>` or near the top of the mobile nav slot). The component is self-styled and self-contained; it has no public attributes.

Interactions:
- Click/tap the globe → modal opens with a list of languages (Spanish, Chinese Simplified/Traditional, 100+ others).
- `Escape` closes the modal.
- Selecting a language invokes Google Translate on the current page.

Because `<maryland-translate>` works via Google Translate, pages whose statewide footer is set to a specific `locale` will see the footer stay in that locale (its `translate="no"` opt-out) while Google Translate re-renders the rest of the page in the picked language. The two systems co-exist cleanly — just document to editors that the footer is **always** served in the configured `locale`, independent of what a visitor picks in `<maryland-translate>`.

### Deciding which system to use

| Need | Use |
|---|---|
| Served Spanish for a Spanish-first site, with reviewed copy | `maryland-statewide-footer locale="es"` + the rest of the page in Spanish source. |
| Visitor-triggered on-the-fly translation to any language | `<maryland-translate>` — accept that it uses Google Translate for all strings. |
| Both, so a Spanish-first page can still offer other languages | Both. They don't conflict. |

## Heading level adjustment

The component's headings are fixed at `<h2>` (the "Explore Maryland.gov" title) and `<h3>` (each link-group title). These are the canonical levels and **cannot** be changed via attribute. Since the footer is a top-level section of the page (alongside `<main>`), `<h2>` is the correct level for its title.

## Common mistakes

1. **Loading only `mdwds-core.js` and not `mdwds-elements.js`** — the most common silent-failure mode. `mdwds-core.js` registers behaviors (banner toggle, accordion, nav JS) but does NOT register the Lit custom elements. `<maryland-statewide-footer>` will sit in the DOM as an empty unknown element with no visible output. You need a `<script type="module">` tag for either `mdwds-elements.js` (covers all `<maryland-*>` web components) or the per-component file at `components/maryland-statewide-footer.js`. See `references/setup.md`.
2. **Forgetting the `data-mdwds` attribute on the stylesheet `<link>`** — second most common silent failure. The component renders into Shadow DOM and looks up the CDN stylesheet via `link[rel="stylesheet"][data-mdwds]` to adopt it into the shadow root. Without `data-mdwds`, the footer registers and renders its markup but appears as invisible/unstyled text — no fonts, no colors, no layout.
3. **Putting it above the agency footer** — order is fixed: `maryland-footer` (agency) first, then `<maryland-statewide-footer>` last. See `references/page-shell.md`.
4. **Trying to pass attributes (`<maryland-statewide-footer agency="...">`)** — there are no attributes. The element ignores any you add.
5. **Rendering it AND `maryland-footer` with `displaySitewide: true`** — that produces two statewide blocks. Use one approach: either `maryland-footer` (agency only) + `<maryland-statewide-footer>` separately, or `maryland-footer` with both `displayAgency` and `displaySitewide` set (and skip the web component).
6. **Customizing the links via JS** — the link list is intentionally fixed. If a link is wrong, file a request with the design system team rather than DOM-patching the shadow root.
7. **Wrapping the element in a `<footer>`** — the component already renders a `<footer>` internally. An outer `<footer>` creates a redundant landmark.
8. **Skipping the statewide footer entirely** — even agencies that have rich agency-specific footers must include `<maryland-statewide-footer>` per state branding policy. It's the same requirement as the statewide banner.
