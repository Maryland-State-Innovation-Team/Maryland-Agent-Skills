# maryland-header

The Maryland-branded site header. Sits below the statewide banner and contains a small utility-link strip, the Maryland (or agency) wordmark logo, and the primary navigation. Required on every Maryland.gov agency page.

> **This is a composite component.** It bundles the utility nav, logo, primary nav, and search form. You normally render `maryland-header` as a whole rather than each piece separately. See `references/components/maryland-nav.md` and `references/components/maryland-utility-nav.md` for the pieces in isolation.

## What it looks like

White background, full-width, with content centered to the page's `widescreen` (1400px) max-width and standard site margins. The header is a flex container with three logical rows:

1. **Utility nav** — a small right-aligned strip of secondary links (sign-in, language, "Make a payment"). Plain links are 13px (`font-size("ui", 3)`) semibold gray (`base-dark`) separated by 1px vertical dividers; button-styled items become small `usa-button` pills. Visible only at desktop (≥1024px) — hidden on mobile, where the items move into the hamburger panel.
2. **Logo row** — the Maryland horizontal wordmark (176px × 36px / 11rem × 2.25rem) sits on the left. On agency sites, the wordmark switches to a vertical form (~85px × 58px mobile, ~85px × 70px desktop) and the agency name appears next to it as bold 22px Source Sans text (`body-11`, semibold, color `ink`).
3. **Nav row** — full-width primary navigation bar with top-level links rendered as 16px (`body-6`) semibold tabs separated by 16px (`units(2)`) gaps. Each tab gets a 3px top border that activates Maryland blue (`primary`) on hover and Maryland gold (`secondary-vivid`) when it marks the active trail.

Below the nav row a 1px `base-light` horizontal divider (`maryland-header__divider`) separates the header from the page content. The divider is **hidden** by default on flush-hero pages (where the hero sits tight against the header) but **visible** on agency sites and at desktop with an expanded nav.

**Below mobile-lg (480px) breakpoint:** the logo and agency name stack vertically. **Below desktop (1024px):** the utility-nav strip and primary nav disappear in favor of a hamburger toggle button (24px square, menu icon → close icon when open) at the top-right. Tapping it slides in a full-viewport white panel with the search input, primary nav links, utility links, and an optional "Maryland.gov" link.

## Variants

The header has two visual modes, driven by whether an `agency` value is set:

| Mode | Visual |
|---|---|
| **Statewide** (`agency: ""`) | Horizontal Maryland wordmark logo only. Used on Maryland.gov itself. |
| **Agency** (`agency: "Department of Natural Resources"`) | Vertical wordmark + agency name. Used on every agency site. The agency-name text trims to a max-width matching the tablet container minus 24px. |

There is no other variant — header layout is otherwise determined by composition (with or without utility nav, with or without primary nav).

## Default markup — agency header

```html
<header class="maryland-header">
  <!-- Utility nav (desktop only — at <1024px, these items move into the mobile panel) -->
  <div class="maryland-header__util-nav-container">
    <ul class="maryland-header__util-nav">
      <li><a href="/sign-in">Sign in</a></li>
      <li><a href="/language">Language</a></li>
      <li><a href="/pay" class="usa-button usa-button--small">Make a payment</a></li>
    </ul>
  </div>

  <!-- Logo + agency name -->
  <a class="maryland-header__home" href="/">
    <img
      class="maryland-header__logo"
      src="/img/md_wordmark_vertical.svg"
      alt="Department of Natural Resources home"
    />
    <span class="maryland-header__agency">Department of Natural Resources</span>
  </a>

  <!-- Desktop search form (sits between logo and nav at desktop; hidden at mobile) -->
  <div class="maryland-search-form">
    <form action="/" role="search" class="maryland-search-form__form" id="header-search-form">
      <label class="maryland-search-form__label usa-sr-only" for="header-search">Search</label>
      <div class="maryland-search-form__widget">
        <input
          class="maryland-search-form__input"
          type="text"
          autocomplete="on"
          name="q"
          placeholder="How do I..."
          id="header-search"
        />
        <button type="submit" class="maryland-search-form__submit">Search</button>
      </div>
    </form>
  </div>

  <!-- Primary nav -->
  <nav class="maryland-nav">
    <button class="maryland-nav__toggle" aria-label="Toggle Nav" type="button"></button>
    <div class="maryland-nav__mobile-panel" id="md-nav-panel">
      <!-- Mobile search form (same template as the desktop one above; rendered inside the mobile panel) -->
      <div class="maryland-nav__mobile-slot">
        <div class="maryland-search-form">
          <form action="/" role="search" class="maryland-search-form__form" id="mobile-search-form">
            <label class="maryland-search-form__label usa-sr-only" for="mobile-search">Search</label>
            <div class="maryland-search-form__widget">
              <input
                class="maryland-search-form__input"
                type="text"
                autocomplete="on"
                name="q"
                placeholder="How do I..."
                id="mobile-search"
              />
              <button type="submit" class="maryland-search-form__submit">Search</button>
            </div>
          </form>
        </div>
      </div>

      <ul class="maryland-nav__items maryland-nav__items--level-one">
        <li id="nav-item-parks" class="maryland-nav__item maryland-nav__item--level-one">
          <a class="maryland-nav__link maryland-nav__link--level-one" href="/parks">Parks</a>
        </li>
        <li id="nav-item-licenses" class="maryland-nav__item maryland-nav__item--level-one">
          <button type="button" class="maryland-nav__link maryland-nav__link--level-one">Licenses &amp; permits</button>
          <div id="nav-children-licenses" class="maryland-nav__children">
            <a class="maryland-nav__button maryland-nav__button--level-two" href="/licenses">Explore licenses &amp; permits</a>
            <ul class="maryland-nav__items maryland-nav__items--level-two">
              <li class="maryland-nav__item maryland-nav__item--level-two">
                <a class="maryland-nav__link maryland-nav__link--level-two" href="/fishing">Fishing</a>
              </li>
              <li class="maryland-nav__item maryland-nav__item--level-two">
                <a class="maryland-nav__link maryland-nav__link--level-two" href="/hunting">Hunting</a>
              </li>
              <li class="maryland-nav__item maryland-nav__item--level-two">
                <a class="maryland-nav__link maryland-nav__link--level-two" href="/boating">Boating</a>
              </li>
            </ul>
            <a class="maryland-nav__button maryland-nav__button--level-two" href="/licenses">See all licenses &amp; permits topics</a>
          </div>
        </li>
        <li id="nav-item-wildlife" class="maryland-nav__item maryland-nav__item--level-one">
          <a class="maryland-nav__link maryland-nav__link--level-one" href="/wildlife">Wildlife</a>
        </li>
        <li id="nav-item-about" class="maryland-nav__item maryland-nav__item--level-one">
          <a class="maryland-nav__link maryland-nav__link--level-one" href="/about">About</a>
        </li>
      </ul>
    </div>
  </nav>

  <hr aria-hidden="true" class="maryland-header__divider" />
</header>
```

**Note:** The level-two dropdown (`maryland-nav__children`) wraps its `<ul>` between two `maryland-nav__button--level-two` anchors — an "Explore {parent}" link before the list and a "See all {parent} topics" link after. Both link to the parent section. The MDWDS nav JS depends on this structure.

## Markup — statewide header (Maryland.gov)

Same structure, but with the horizontal wordmark and no agency name:

```html
<header class="maryland-header">
  <div class="maryland-header__util-nav-container">
    <ul class="maryland-header__util-nav">
      <li><a href="/services">Services</a></li>
      <li><a href="/agencies">Agencies</a></li>
    </ul>
  </div>

  <a class="maryland-header__home" href="/">
    <img
      class="maryland-header__logo"
      src="/img/md_wordmark_horizontal.svg"
      alt="Maryland.gov home"
    />
  </a>

  <nav class="maryland-nav">
    <!-- ... same nav structure as above ... -->
  </nav>

  <hr aria-hidden="true" class="maryland-header__divider" />
</header>
```

## What each class does

| Class | Effect |
|---|---|
| `maryland-header` | Top-level flex container. Applies `padding-block: 20px` (`units(2.5)`) on mobile (removed at desktop when nav is expanded), centers within a `widescreen` (1400px) max-width grid container, sets `z-index: 2` so dropdowns layer above page content. |
| `maryland-header__home` | The `<a>` wrapping logo + agency name. Inline-flex column on mobile, row at `mobile-lg` (480px+). On agency sites, takes up at most `100% - 64px` of header width. Underline on hover. |
| `maryland-header__logo` | The wordmark `<img>`. Sized to ~176×36px (11rem × 2.25rem) for statewide variant. Agency variant sizes the logo to ~70×85px (mobile) / ~85×85px (desktop) since the vertical wordmark is used. |
| `maryland-header__agency` | Agency name next to the logo. 22px (`body-11`) semibold, color `ink` (near-black). Trimmed with a text-trim mixin so descenders don't add extra space. Max-width caps it at ~tablet width minus 24px on tablet+. |
| `maryland-header__util-nav-container` | Wrapper around the utility-nav `<ul>`. Hidden on mobile (display: none). Shown as a full-width block at desktop unless the primary nav is in hamburger mode. |
| `maryland-header__util-nav` | The utility-nav `<ul>`. Flex row, right-justified, no list bullets. 13px font (`ui-3`). Vertical 1px `base-light` divider between adjacent plain links. Button-styled items get 8px horizontal margin and become inline `usa-button--small` pills. |
| `maryland-header__divider` | 1px horizontal rule below the nav, color `base-light`. Hidden on mobile; visible at desktop when nav is expanded; visible at all sizes on agency sites; hidden by default on flush-hero pages. |
| `maryland-nav` | Primary navigation `<nav>`. See `references/components/maryland-nav.md` for its sub-classes. Below the desktop breakpoint it shows the hamburger toggle; at desktop it lays out as a horizontal tab bar. |
| `maryland-search-form` | Wrapper `<div>` around the search `<form>`. Hidden inside the header until desktop, when it sits flush-right between the logo and the nav. The mobile equivalent moves into the nav's `mobile-slot`. |
| `maryland-search-form__form` | The inner `<form>` element. Holds the label and the `__widget` row. |
| `maryland-search-form__label` | `<label>` for the search input. Add `usa-sr-only` to visually hide it in the header (default behavior — the header passes `hideSearchLabel: true`). |
| `maryland-search-form__widget` | Flex row wrapping the input + submit button. |
| `maryland-search-form__input` | The `<input type="text">`. **Use `type="text"`, not `type="search"`** — the published CSS targets the `__input` class, not the input type. |
| `maryland-search-form__submit` | The submit `<button>`. Styled as a Maryland-blue pill at desktop; collapses to an icon-only button in some compact layouts. |
| `maryland-nav__children` | Wrapper `<div>` around a level-two `<ul>` inside a parent `<li>`. Adds the "Explore {parent}" link above the list and the "See all {parent} topics" link below it. **Required** — the nav JS reads this wrapper to position the dropdown. |
| `maryland-nav__button maryland-nav__button--level-two` | The "Explore X" / "See all X topics" anchors that bookend the level-two `<ul>` inside `maryland-nav__children`. |

## Prop schema

| Prop | Type | Default | Notes |
|---|---|---|---|
| `agency` | string | `""` | Agency name. Empty string = statewide Maryland.gov header (horizontal wordmark). Any string = agency header (vertical wordmark + name). |
| `enableUtil` | bool | `true` | Render the utility-nav strip. |
| `util` | array of `{label, url, isButton?}` | sample 3-item list | Utility-nav items. `isButton: true` styles the item as a `usa-button--small`. |
| `enableNav` | bool | `true` | Render the primary nav. |
| `showMarylandGovLink` | bool | `false` | Add a "Maryland.gov" link at the bottom of the mobile nav panel (used on agency sites to link back to the state portal). |
| `navItems` | array of `{label, url, children?}` | extensive default list | Primary-nav items. Each can have a nested `children` array for dropdown submenus. |
| `showAlert` | bool | `false` | Render a global alert directly inside the header (uncommon — use the page-level alert slot instead). |
| `alertStatus` | string | `"info"` | Status for the optional embedded alert. |
| `alertHeading` / `alertMessage` | string | — | Alert content if `showAlert` is true. |

## Heading level adjustment

The header contains no semantic heading. The agency name is a `<span>` (not an `<h1>`) because the page's `<h1>` belongs to the hero. **Do not** replace `maryland-header__agency` with an `<h1>` — it would create a duplicate-h1 accessibility violation.

## Color theme variants (0.49.0+)

Starting in MDWDS **0.49.0** the header supports five color themes selected via a modifier class on the `<header>` element. **0.50.0** then changed the themed header into a full-bleed band — the colored band spans the full viewport width (overriding the normal page `grid-container` max-width) and the agency wordmark receives a dark "panel" treatment where the band meets the content column.

Set the modifier to one of:

| Modifier class | Band color | Logo pairing |
|---|---|---|
| `maryland-header--theme-white` | White (default) | Horizontal wordmark on white. No band treatment. |
| `maryland-header--theme-navy` | Maryland navy | Inverted wordmark on the band + dark panel version in the content column. |
| `maryland-header--theme-red` | Maryland red (`secondary-vivid`) | Inverted wordmark on band + dark panel. |
| `maryland-header--theme-green` | Maryland green | Inverted wordmark on band + dark panel. |
| `maryland-header--theme-black` | Black | Inverted wordmark on band + dark panel. |

The `--theme-white` class is emitted by the template for the default too, so a page always carries exactly one `maryland-header--theme-*` modifier. Styling targets the non-white themes via explicit `:not()` guards; the default visual is the "no theme" style the CSS falls through to.

### White theme (default) markup

Default — single logo image, no band treatment.

```html
<header class="maryland-header maryland-header--theme-white">
  <a class="maryland-header__home" href="/">
    <img
      class="maryland-header__logo"
      src="https://cdn.maryland.gov/mdwds/0.51.1/img/md_wordmark_horizontal.svg"
      alt="Maryland.gov home"
    />
  </a>
  <!-- utility nav + primary nav here -->
  <hr aria-hidden="true" class="maryland-header__divider" />
</header>
```

With an agency name, the horizontal wordmark becomes a vertical wordmark and the agency `<span>` renders beside it:

```html
<header class="maryland-header maryland-header--theme-white">
  <a class="maryland-header__home" href="/">
    <img
      class="maryland-header__logo"
      src="https://cdn.maryland.gov/mdwds/0.51.1/img/md_wordmark_vertical.svg"
      alt="Department of Natural Resources home"
    />
    <span class="maryland-header__agency">Department of Natural Resources</span>
  </a>
  <!-- utility nav + primary nav here -->
  <hr aria-hidden="true" class="maryland-header__divider" />
</header>
```

### Dark-theme markup (navy / red / green / black)

Dark themes use **two logo images** — one for the colored band region (`__logo--band`, drawn in inverted colors so it reads on the band) and one for the white panel below (`__logo--panel`). CSS swaps which image is visible based on viewport width and the full-bleed band treatment.

```html
<header class="maryland-header maryland-header--theme-navy">
  <a class="maryland-header__home" href="/">
    <img
      class="maryland-header__logo maryland-header__logo--band"
      src="https://cdn.maryland.gov/mdwds/0.51.1/img/md_wordmark_horizontal_inverted.svg"
      alt="Maryland.gov home"
    />
    <img
      class="maryland-header__logo maryland-header__logo--panel"
      src="https://cdn.maryland.gov/mdwds/0.51.1/img/md_wordmark_horizontal.svg"
      alt="Maryland.gov home"
    />
  </a>
  <!-- utility nav + primary nav here -->
  <hr aria-hidden="true" class="maryland-header__divider" />
</header>
```

Agency variant: same two-image pattern, but using the vertical wordmark on both sides, plus the agency `<span>`.

```html
<header class="maryland-header maryland-header--theme-navy">
  <a class="maryland-header__home" href="/">
    <img
      class="maryland-header__logo maryland-header__logo--band"
      src="https://cdn.maryland.gov/mdwds/0.51.1/img/md_wordmark_vertical_inverted.svg"
      alt="Department of Natural Resources home"
    />
    <img
      class="maryland-header__logo maryland-header__logo--panel"
      src="https://cdn.maryland.gov/mdwds/0.51.1/img/md_wordmark_vertical.svg"
      alt="Department of Natural Resources home"
    />
    <span class="maryland-header__agency">Department of Natural Resources</span>
  </a>
  <!-- utility nav + primary nav here -->
  <hr aria-hidden="true" class="maryland-header__divider" />
</header>
```

### Theme-specific child classes

| Class | When present | Effect |
|---|---|---|
| `maryland-header__home` | Always | The `<a>` wrapping the logo + agency span. Clickable area that returns to the site root. |
| `maryland-header__logo` | Always (default theme), paired with `--band` and `--panel` on dark themes | The logo `<img>` element. |
| `maryland-header__logo--band` | Dark themes only | Logo variant drawn on the colored band. CSS hides the panel copy at this slot. |
| `maryland-header__logo--panel` | Dark themes only | Logo variant drawn on the white content panel below/beside the band. |
| `maryland-header__logo--agency-custom` | Optional | Marker for an agency's custom logo (e.g., a seal) replacing the standard wordmark. CSS adjusts padding and max-width when present. |
| `maryland-header__agency` | Only when `agency` is set | The agency name `<span>` next to the logo. 20px semibold. |
| `maryland-header__divider` | Always | The `<hr aria-hidden="true">` at the bottom of the header. Separates the header from the hero / main content. Hidden on mobile; visible at desktop widths. |

### Full-bleed band behavior (0.50.0+)

On themed headers, the band extends to the viewport edges even when the surrounding page uses `grid-container` (which otherwise caps content at the design max-width). The CSS achieves this with `width: 100vw; margin-left: calc(50% - 50vw)` on the `<header>` itself; **do not wrap the themed header in `grid-container` or any other max-width container** or the band will stop at the content column edge.

The content column *inside* the band — the utility nav, logo, and primary nav — still respects `grid-container` and sits inside the normal max-width. The `__logo--panel` image sits in this content column; the `__logo--band` image spans the band edges on wide viewports where the band is visible outside the panel.

Choosing a theme: `--theme-navy` is the most common agency choice (brand-aligned, strong contrast). `--theme-red` and `--theme-green` are reserved for specific agencies with those brand colors; confirm with the Maryland design team before using them. `--theme-black` is a neutral alternative for agencies that have no brand color.

---

## Common mistakes

1. **Skipping the wrapping `<header class="maryland-header">`** — the header's flex layout, max-width container, and responsive logo sizing all depend on this element. Without it the logo and nav lay out wrong.
2. **Using the horizontal wordmark with an agency name** — the published CSS resizes the logo based on whether `.maryland-header__agency` is present. The horizontal wordmark expects no agency text next to it; use the vertical wordmark (`md_wordmark_vertical.svg`) on agency pages.
3. **Adding an `<h1>` inside the header** — the page `<h1>` belongs to the hero, not the header. Use a `<span class="maryland-header__agency">` for the agency name.
4. **Putting the utility nav outside `maryland-header__util-nav-container`** — without the container wrapper, the strip won't hide on mobile and won't move into the hamburger panel.
5. **Forgetting the `maryland-nav__toggle` button** — the hamburger menu needs this button (with the `aria-label="Toggle Nav"`) for the mobile panel to open. Missing it leaves mobile users with no way to access the nav.
6. **Wrapping the header in a `grid-container`** — the header applies its own `grid-container` and `add-responsive-site-margins` mixins. Wrapping it again creates nested margins and the header content slides inward.
7. **Loading the nav JS twice** — `mdwds-core.js` attaches the nav behaviors automatically when the page loads. If you copy the markup and then call the JS init manually, dropdowns will double-bind.
8. **Using only one `<img>` on a dark theme.** Dark themes expect `__logo--band` *and* `__logo--panel`. Omitting one leaves either the band region or the content column with no logo. Use the two-image pattern for every non-white theme.
9. **Pairing a dark theme with the inverted wordmark in the `__logo--panel` slot.** The panel sits over white; use the standard (non-inverted) wordmark there. Reserve the inverted versions for `__logo--band`.
10. **Mixing the new navigation system with `--theme-navy` and expecting the active-trail bar to be red.** The red active-trail bar is specific to `--theme-white`. On dark themes the bar is white. The modifier class on the top-level `maryland-navbar__link--active-trail` is identical; the color is a theme-contextual override.
