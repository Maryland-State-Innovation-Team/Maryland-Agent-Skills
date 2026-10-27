# maryland-navigation

The current Maryland primary navigation system, introduced in MDWDS **0.48.0** and shipped as the recommended default from **0.50.0** onward. Four interoperating BEM families cover every pattern a Maryland.gov agency site needs: a horizontal top-level bar, dropdown panels, tabbed megamenus, and grouped sub-lists.

> **New work uses the components in this file.** The older `maryland-nav__*` family (`maryland-nav__items--level-one`, `maryland-nav__toggle`, `maryland-nav__mobile-panel`) is deprecated as of 0.48.0 and documented in `maryland-nav.md` for migration purposes only. The new system is a complete replacement, not an incremental revision — markup, class names, and composition rules are all different.
>
> **You usually don't render the navbar directly.** `maryland-header` composes it for you when `useMegamenu: true` (and renders the deprecated nav when `false`). Reach for the standalone markup only when building a custom header layout. See `maryland-header.md`.

## The four families

| Family | Purpose | Nests inside |
|---|---|---|
| `maryland-navbar` | The horizontal top-level bar and its mobile hamburger panel. | `maryland-header`. Standalone for custom shells. |
| `maryland-dropdown` | A single top-level item's panel. Opens on hover (desktop) or tap (mobile). Panels can be plain lists or `--mega` (full-width megamenus). | `maryland-navbar__item`. |
| `maryland-tabs` | A tabbed layout inside a mega panel. One tab per top-level child; each tab's section holds further grouped links. | `maryland-dropdown__panel--mega`. |
| `maryland-link-group` | A labeled sub-list with a title, icon, and "All <title>" see-all link. Groups related children inside a megamenu. | `maryland-dropdown__panel--mega` (non-tabbed) or `maryland-tabs__panel` (tabbed). |

The composition rule: `navbar → navbar__item → dropdown → dropdown__panel[--mega] → (tabs → tabs__panel →) link-group`. Simpler items collapse: a plain top-level link is just a `navbar__item > navbar__link`; a single-column dropdown is `navbar__item.maryland-dropdown > dropdown__button + dropdown__panel > dropdown__list`.

---

## What it looks like

**Desktop (≥1024px).** A horizontal row of top-level items sits at the bottom of the header, flush-left. Each top-level item is semibold dark text with a 3px transparent top border that becomes `secondary-vivid` red (on `--theme-white` headers) or white (on dark theme headers) when the item marks the current section (`maryland-navbar__link--active-trail`). Items with children render as `<button>` elements with a chevron that rotates 180° when the dropdown is open.

Dropdown panels open below the top-level item on hover or click. Non-mega panels are white columns that break into 2 columns when they hold 6+ children (the CSS triggers columns on `:has(>:nth-child(6))`). Mega panels (`maryland-dropdown__panel--mega`) span the full header width.

Mega panels can hold either a tabbed layout (`maryland-tabs`) with a vertical tab list on the left and a content area on the right, or a grid of link groups (`maryland-link-group`) stacked side by side.

Every link-group inside a mega panel renders as a titled block with a star icon prefix, a list of up to a few links, and a terminal "All <group title>" see-all link.

**Below desktop (<1024px).** The whole navbar collapses to a 24px hamburger toggle. Tapping it opens a full-viewport white panel (`maryland-navbar__mobile-panel.is-open`) that slides in over the page. The panel contains an optional top slot (typically the search form), the vertical list of top-level items, and an optional bottom slot (utility nav + the "Maryland.gov" agency-link row).

Items with children expand to nested panels inside the same mobile view. Each nested panel includes a `__back` button to return to the parent level — the hamburger drills, not pops; dropdown and tabs both expose their own `__back` controls.

---

## Default top-level markup (plain items only)

Four plain top-level links, no dropdowns.

```html
<nav class="maryland-navbar">
  <button
    class="maryland-navbar__toggle"
    aria-label="Toggle navigation"
  ></button>
  <div class="maryland-navbar__mobile-panel">
    <ul class="maryland-navbar__list">
      <li class="maryland-navbar__item">
        <a class="maryland-navbar__link" href="/services">Services</a>
      </li>
      <li class="maryland-navbar__item">
        <a class="maryland-navbar__link" href="/government">Government</a>
      </li>
      <li class="maryland-navbar__item">
        <a class="maryland-navbar__link" href="/residents">Residents</a>
      </li>
      <li class="maryland-navbar__item">
        <a class="maryland-navbar__link" href="/about">About</a>
      </li>
    </ul>
  </div>
</nav>
```

**Important:** every top-level item lives inside `<ul class="maryland-navbar__list">`, which itself lives inside `<div class="maryland-navbar__mobile-panel">` — even on desktop. The mobile panel is the shared layout container; `--mobile-panel` is a historical name, not a desktop/mobile switch. The CSS lays out the same list differently per breakpoint.

**Important:** the `<button class="maryland-navbar__toggle">` is required even on desktop. CSS hides it on wide viewports; `mdwds-core.js` wires its click handler to toggle `.is-open` on the mobile panel. Omitting it breaks the mobile hamburger entirely.

---

## Dropdown — single column (`isMega: 0`)

A top-level item with a plain dropdown of child links.

```html
<li class="maryland-navbar__item maryland-dropdown">
  <button class="maryland-navbar__link maryland-dropdown__button">
    Services
  </button>
  <div class="maryland-dropdown__panel">
    <a class="maryland-dropdown__see-all" href="/services">All Services</a>
    <ul class="maryland-dropdown__list">
      <li class="maryland-dropdown__item">
        <a class="maryland-dropdown__link" href="/services/permits">
          Permits
        </a>
      </li>
      <li class="maryland-dropdown__item">
        <a class="maryland-dropdown__link" href="/services/licenses">
          Licenses
        </a>
      </li>
      <li class="maryland-dropdown__item">
        <a class="maryland-dropdown__link" href="/services/payments">
          Payments
        </a>
      </li>
      <li class="maryland-dropdown__item">
        <a class="maryland-dropdown__link" href="/services/vehicles">
          Vehicles
        </a>
      </li>
    </ul>
  </div>
</li>
```

**Important:** `<li>` carries two classes — `maryland-navbar__item` (positions it inside the navbar list) and `maryland-dropdown` (makes it dropdown-aware). Omit `maryland-dropdown` and the `__panel` won't be positioned or interactive.

**Important:** the top-level control is a `<button>`, not an `<a>`, when there are children. Buttons can be the current trail without being the current page — buttons never carry `aria-current`.

The `__see-all` link appears above the list (`All <top-level label>`), linking to the top-level URL. Omit the `href` on the top-level control and the `__see-all` becomes the user's only way to reach the parent section — don't do that unless intentional.

Columns: when the `__list` has 6 or more items the CSS automatically breaks it into 2 columns via `.maryland-dropdown__list:has(>:nth-child(6))`.

---

## Dropdown — megamenu (no tabs) (`isMega: 1`, children have no `children` themselves)

Full-width panel that holds a row of link groups instead of a plain `<ul>`.

```html
<li class="maryland-navbar__item maryland-dropdown">
  <button class="maryland-navbar__link maryland-dropdown__button">
    Residents
  </button>
  <div class="maryland-dropdown__panel maryland-dropdown__panel--mega">
    <div class="maryland-tabs">
      <div class="maryland-tabs__panels">
        <section class="maryland-tabs__panel">
          <a class="maryland-tabs__panel-see-all" href="/residents">
            All Residents
          </a>

          <div class="maryland-link-group">
            <p class="maryland-link-group__title">
              <span class="maryland-link-group__icon" aria-hidden="true">
                <!-- Star icon from mdwds-icons -->
              </span>
              Housing
            </p>
            <ul class="maryland-link-group__list">
              <li>
                <a class="maryland-link-group__link" href="/residents/housing/apply">
                  Apply for housing
                </a>
              </li>
              <li>
                <a class="maryland-link-group__link" href="/residents/housing/assistance">
                  Rental assistance
                </a>
              </li>
            </ul>
            <a class="maryland-link-group__see-all" href="/residents/housing">
              All Housing
            </a>
          </div>

          <div class="maryland-link-group">
            <p class="maryland-link-group__title">
              <span class="maryland-link-group__icon" aria-hidden="true">
                <!-- Star icon -->
              </span>
              Transportation
            </p>
            <ul class="maryland-link-group__list">
              <li>
                <a class="maryland-link-group__link" href="/residents/transportation/dl">
                  Driver's license
                </a>
              </li>
            </ul>
            <a class="maryland-link-group__see-all" href="/residents/transportation">
              All Transportation
            </a>
          </div>
        </section>
      </div>
    </div>
  </div>
</li>
```

**Important:** even in the no-tabs megamenu, the panel wraps a `maryland-tabs > maryland-tabs__panels > section.maryland-tabs__panel` scaffold. The tabs scaffold is the layout container for mega panels. Without it, the link groups won't flow correctly inside the full-width region.

**Important:** every `maryland-link-group__title` is a `<p>`, not a heading. Semantic headings here would compete with the page's `<h1>`/`<h2>` outline. The icon is a `<span class="maryland-link-group__icon">` with `aria-hidden="true"` — the icon is decorative; the group title communicates meaning.

---

## Megamenu with tabs (`isMega: 1`, children have `children` themselves)

Section tabs on the left, a `maryland-link-group` grid on the right. Used when a dropdown exceeds ~8 groups and users need to pivot by topic.

```html
<li class="maryland-navbar__item maryland-dropdown">
  <button class="maryland-navbar__link maryland-dropdown__button">
    Government
  </button>
  <div class="maryland-dropdown__panel maryland-dropdown__panel--mega">
    <div class="maryland-tabs">
      <a class="maryland-tabs__see-all" href="/government">
        All Government
      </a>

      <ul class="maryland-tabs__list">
        <li class="maryland-tabs__item">
          <a class="maryland-tabs__tab" href="#tab-executive">Executive</a>
        </li>
        <li class="maryland-tabs__item">
          <a class="maryland-tabs__tab" href="#tab-legislative">Legislative</a>
        </li>
        <li class="maryland-tabs__item">
          <a class="maryland-tabs__tab" href="#tab-judicial">Judicial</a>
        </li>
      </ul>

      <div class="maryland-tabs__panels">
        <section class="maryland-tabs__panel" id="tab-executive">
          <a class="maryland-tabs__panel-see-all" href="/government/executive">
            All Executive
          </a>

          <div class="maryland-link-group">
            <p class="maryland-link-group__title">
              <span class="maryland-link-group__icon" aria-hidden="true"></span>
              Governor
            </p>
            <ul class="maryland-link-group__list">
              <li>
                <a class="maryland-link-group__link" href="/governor/office">
                  Governor's office
                </a>
              </li>
              <li>
                <a class="maryland-link-group__link" href="/governor/cabinet">
                  Cabinet
                </a>
              </li>
            </ul>
            <a class="maryland-link-group__see-all" href="/government/executive/governor">
              All Governor
            </a>
          </div>
        </section>

        <section class="maryland-tabs__panel" id="tab-legislative">
          <a class="maryland-tabs__panel-see-all" href="/government/legislative">
            All Legislative
          </a>
          <!-- link-group blocks for the Legislative tab -->
        </section>

        <section class="maryland-tabs__panel" id="tab-judicial">
          <a class="maryland-tabs__panel-see-all" href="/government/judicial">
            All Judicial
          </a>
          <!-- link-group blocks for the Judicial tab -->
        </section>
      </div>
    </div>
  </div>
</li>
```

**Important:** `maryland-tabs__panel` elements use unique `id` attributes and the matching `maryland-tabs__tab` anchors use `href="#<id>"`. The IDs must be unique within the page (two megamenus on one page would need different id namespaces — use a prefix). Tab anchors use `aria-selected` (not `aria-current`) at runtime; the JS sets this.

**Important:** the top-level `maryland-tabs__see-all` and per-section `maryland-tabs__panel-see-all` are two different links. The top one goes to the section parent; the panel-level one goes to the tab's parent. Both can be omitted for a given tab, but it's an accessibility regression — users on a non-interactive viewer get no overview link.

---

## Link group — standalone (outside the navbar)

The `maryland-link-group` block is also usable on its own, outside the nav, for in-page "related links" sections.

```html
<div class="maryland-link-group">
  <p class="maryland-link-group__title">
    <span class="maryland-link-group__icon" aria-hidden="true">
      <!-- Star icon -->
    </span>
    Housing
  </p>
  <ul class="maryland-link-group__list">
    <li>
      <a class="maryland-link-group__link" href="/residents/housing/apply">
        Apply for housing
      </a>
    </li>
    <li>
      <a class="maryland-link-group__link" href="/residents/housing/assistance">
        Rental assistance
      </a>
    </li>
    <li>
      <a class="maryland-link-group__link" href="/residents/housing/code">
        Housing code
      </a>
    </li>
    <li>
      <a class="maryland-link-group__link" href="/residents/housing/landlord">
        For landlords
      </a>
    </li>
  </ul>
  <a class="maryland-link-group__see-all" href="/residents/housing">
    All Housing
  </a>
</div>
```

On mobile the link-group collapses behind a `__button` that uses `aria-expanded` to toggle the `__content` region — the CSS exposes `.maryland-link-group__button[aria-expanded=false]` and `.maryland-link-group__content` for the collapsed state. When used standalone outside the navbar, the collapsible treatment stays off; it's only applied when the link-group is nested inside a mega panel's mobile layout.

---

## Mobile slots and the agency-link row

The mobile panel accepts "slot" regions above and below the primary list. The default agency header uses a top slot for the search form and a bottom slot for the utility nav + "Maryland.gov" agency link.

```html
<nav class="maryland-navbar">
  <button class="maryland-navbar__toggle" aria-label="Toggle navigation"></button>
  <div class="maryland-navbar__mobile-panel">

    <div class="maryland-navbar__mobile-slot">
      <!-- Top slot: typically the search form -->
      <form class="maryland-search-form" role="search">
        <!-- ... -->
      </form>
    </div>

    <ul class="maryland-navbar__list">
      <!-- Top-level items -->
    </ul>

    <div class="maryland-navbar__mobile-slot">
      <!-- Bottom slot: utility nav + agency link -->
      <ul class="maryland-header__util-nav">
        <!-- ... -->
      </ul>
      <div class="maryland-navbar__agency-link">
        <a href="/">Maryland.gov</a>
      </div>
    </div>

  </div>
</nav>
```

- `maryland-navbar__mobile-slot` — generic slot wrapper used for both top (search) and bottom (utility + agency link). Multiple slots are allowed.
- `maryland-navbar__agency-link` — the "Maryland.gov" row at the bottom of an agency's mobile menu, linking back to the state portal. Shown only on agency sites, not on the state-level site. Set `showMarylandGovLink: true` on `maryland-header` to generate it.

Slots render inline on desktop above/below the top-level list; on mobile they bookend the list inside the slide-in panel.

---

## Active trail (marking the current section)

Add `maryland-navbar__link--active-trail` to the top-level link or button of the section the current page belongs to. Also set `aria-current="page"` on the actual current-page link wherever it appears in the menu.

```html
<!-- Section with a dropdown -->
<li class="maryland-navbar__item maryland-dropdown">
  <button class="maryland-navbar__link maryland-dropdown__button maryland-navbar__link--active-trail">
    Services
  </button>
  <div class="maryland-dropdown__panel">
    <a class="maryland-dropdown__link" href="/services/permits" aria-current="page">
      Permits
    </a>
  </div>
</li>

<!-- Plain top-level link, the page itself -->
<li class="maryland-navbar__item">
  <a class="maryland-navbar__link maryland-navbar__link--active-trail" href="/about" aria-current="page">
    About
  </a>
</li>
```

In Drupal Twig:

```twig
<button class="maryland-navbar__link maryland-dropdown__button{{ item.in_active_trail ? ' maryland-navbar__link--active-trail' }}">
```

Rules of thumb:
- One section per page carries `--active-trail`. Never multiple.
- `aria-current="page"` goes on the current-page link only. The visual trail bar does not depend on `aria-current` — it's purely a modifier class.
- Tab controls (`maryland-tabs__tab`) use `aria-selected`, never `aria-current`. The tab in use is "selected"; it isn't "the current page."

---

## What each class does

### `maryland-navbar` family

| Class | Effect |
|---|---|
| `maryland-navbar` | Root `<nav>` element. Positions the top-level bar on desktop; converts to a hamburger shell on mobile. |
| `maryland-navbar--mobile` | Programmatic marker added by `mdwds-core.js` when the nav is in its hamburger state. Not something you add by hand. |
| `maryland-navbar__toggle` | The hamburger button. CSS-masked `menu`/`close` glyph. Always present in markup; hidden on desktop. **Required** for mobile to function. |
| `maryland-navbar__mobile-panel` | The layout container for the item list and slots. Despite the name, it is also the desktop layout wrapper — CSS reshapes it per breakpoint. |
| `maryland-navbar__mobile-panel.is-open` | Open state on mobile. Toggled by the JS when the hamburger is pressed. |
| `maryland-navbar__mobile-header` | Optional heading strip at the top of the mobile panel (used by some layouts for a close button + logo). |
| `maryland-navbar__mobile-slot` | Container for content stacked above or below the primary list (search, utility nav, agency link). |
| `maryland-navbar__list` | `<ul>` holding top-level items. Flex row on desktop, column on mobile. |
| `maryland-navbar__item` | `<li>` wrapper. Add `maryland-dropdown` as a second class when the item owns a dropdown. |
| `maryland-navbar__link` | Top-level link or button. Semibold, with the 3px active-trail bar on top. |
| `maryland-navbar__link--active-trail` | Marks the top-level item for the current section. Bar on top (desktop); bold on mobile. |
| `maryland-navbar__agency-link` | The "Maryland.gov" row at the bottom of an agency-site mobile menu. |

### `maryland-dropdown` family

| Class | Effect |
|---|---|
| `maryland-dropdown` | Second class on `<li.maryland-navbar__item>` when the item owns a panel. |
| `maryland-dropdown__button` | The top-level `<button>` when the item has children. Co-classed with `maryland-navbar__link`. Carries `aria-expanded`. |
| `maryland-dropdown__panel` | The dropdown panel. White background, box-shadow, positioned absolutely below the button. |
| `maryland-dropdown__panel--mega` | Full-width mega panel. Spans the header width instead of sitting below a single item. |
| `maryland-dropdown__panel.is-open` | Open state. Toggled by `mdwds-core.js`. |
| `maryland-dropdown__list` | `<ul>` of child links inside a non-mega panel. Breaks into 2 columns at 6+ children. |
| `maryland-dropdown__item` | `<li>` wrapper. |
| `maryland-dropdown__link` | Child link. 12px plain weight with blue underline on hover. |
| `maryland-dropdown__see-all` | "All <section>" link above the list, linking to the top-level URL. Can also carry the `.ext` modifier for external destinations. |
| `maryland-dropdown__back` | A back button inside nested mobile panels. Hidden on desktop. Used when drilling into a child category on mobile. |

### `maryland-tabs` family

| Class | Effect |
|---|---|
| `maryland-tabs` | Container for the tabbed layout. Lives inside `maryland-dropdown__panel--mega`. |
| `maryland-tabs__list` | `<ul>` of tab anchors. |
| `maryland-tabs__item` | `<li>` wrapper for each tab anchor. |
| `maryland-tabs__tab` | `<a href="#panel-id">` that opens its panel. Carries `aria-selected`. |
| `maryland-tabs__panels` | Container for the right-hand panel region. |
| `maryland-tabs__panel` | Each panel; one per tab. Carries an `id` that the tab's `href` targets. |
| `maryland-tabs__panel.is-open` | Open panel. Toggled by JS. |
| `maryland-tabs__see-all` | "All <section>" link at the top of the whole tabs block, linking to the section parent. |
| `maryland-tabs__panel-see-all` | "All <tab>" link inside a specific panel, linking to the tab's parent. |
| `maryland-tabs__back` | Back button for the mobile nested-panel navigation. |

### `maryland-link-group` family

| Class | Effect |
|---|---|
| `maryland-link-group` | Root block of a titled sub-list. |
| `maryland-link-group__title` | `<p>` with the group's heading text and icon. Not a semantic heading. |
| `maryland-link-group__icon` | `<span aria-hidden="true">` wrapping the decorative glyph (usually the star icon from `mdwds-icons`). |
| `maryland-link-group__list` | `<ul>` of child links. |
| `maryland-link-group__link` | Each child link inside the list. |
| `maryland-link-group__see-all` | "All <title>" link below the list, linking to the group parent. |
| `maryland-link-group__button` | On mobile inside a mega panel, this `<button>` collapses the group behind an expand/collapse toggle. Has `aria-expanded`. |
| `maryland-link-group__content` | The expand/collapse region on mobile. |

---

## Prop schema

The storybook `maryland-header` story passes the following shape through to the navigation template (`useMegamenu: true`).

| Prop | Type | Default | Notes |
|---|---|---|---|
| `items` | `MenuItem[]` | sample data | Top-level menu items. See the item shape below. |
| `util` | `UtilItem[]` | — | Items for the utility nav rendered inside the mobile bottom slot. |
| `enableUtil` | boolean | `true` | Project utility nav into the mobile bottom slot. |
| `showMarylandGovLink` | boolean | `false` | Append the "Maryland.gov" `__agency-link` row to the mobile bottom slot. Agency sites only. |

### `MenuItem` shape

```ts
type MenuItem = {
  label: string;
  url?: string;                 // required for plain items; "#" for pure dropdown parents
  isMega?: 0 | 1;               // 1 = full-width megamenu
  activeTrail?: boolean;        // mark this top-level item for the current section
  current?: boolean;            // mark the actual current page (adds aria-current="page")
  children?: MenuItem[];        // sub-items. If any child itself has children, mega renders as tabs.
}
```

The template auto-selects the mega sub-layout:
- `isMega: 0` → non-mega dropdown with a plain `__list` of children.
- `isMega: 1`, no grandchildren → mega panel with children rendered as a single `maryland-tabs__panel` holding link groups.
- `isMega: 1`, children-of-children exist → mega panel with full `maryland-tabs` scaffold; each top-level child becomes a tab, each grandchild becomes a `maryland-link-group`, each great-grandchild becomes a `maryland-link-group__link`.

That last depth is the hard cap: the storybook data goes `top → tab → group → link` and no deeper. There is no "fourth-level" rendering; extra `children` nesting is ignored.

---

## Heading-level guidance

The navigation uses `<p>` for group titles and plain anchors throughout. **Do not introduce `<h2>`/`<h3>` headings inside the dropdowns.** Nested headings compete with the page's `<main>` outline and confuse screen readers that use heading-navigation shortcuts.

The top-level items should be inside the page's `<header>` landmark; the `<nav>` element is implicitly the primary navigation landmark. If the page needs multiple navs (e.g., a footer utility nav), label this one with `aria-label="Primary navigation"` on the `<nav class="maryland-navbar">` element.

---

## Common mistakes

1. **Omitting `maryland-dropdown` as a second class on `<li>`.** A dropdown parent `<li>` needs both `maryland-navbar__item` *and* `maryland-dropdown`. With only the first, the panel sits unpositioned next to the top-level items and the JS can't locate it. Example:
   `<li class="maryland-navbar__item maryland-dropdown">` ← both classes required.
2. **Using `<a>` for a dropdown parent.** Top-level controls with children must be `<button>`. The USWDS/MDWDS JS sets `aria-expanded` on them; `<a>` doesn't accept interactive expansion semantics cleanly, and keyboard focus moves wrong.
3. **Skipping the `maryland-tabs` scaffold inside a mega panel.** Even megamenus that have no visible tabs wrap their content in `maryland-tabs > maryland-tabs__panels > section.maryland-tabs__panel`. Without this, the mega panel has no layout column and link-groups collapse.
4. **Adding real headings inside dropdowns.** `maryland-link-group__title` is a `<p>`. Replacing it with `<h3>` breaks the page outline. Use `<p>` and let the CSS handle styling.
5. **Giving two megamenus the same `maryland-tabs__panel` id.** The tab `href="#..."` resolves to the first match in document order; the second menu's panel becomes unreachable. Prefix ids per menu: `#svc-tab-1`, `#gov-tab-1`.
6. **Setting `aria-current="page"` on the `__link--active-trail` top-level button.** `aria-current` goes on the actual current-page link, which lives further down inside the dropdown. The top-level active-trail button is "in the trail," not "the page."
7. **Marking the current page with `aria-selected` on a tab.** Tabs use `aria-selected` for their open/closed state. `aria-current="page"` goes on anchor links, not tab controls.
8. **Omitting `aria-label` on the toggle.** The hamburger is an icon-only button; without `aria-label="Toggle navigation"` (or an equivalent screen-reader string), it's unlabeled.
9. **Styling the "All <section>" see-all links as regular links.** They are deliberately distinct — the CSS makes them larger and adds an arrow glyph. Overriding with inline styles usually drops the arrow.
10. **Writing custom CSS for mobile breakpoint behavior.** The `.maryland-navbar--mobile` marker class is added by the JS at runtime based on breakpoint. Don't apply it from your markup or your SCSS — let the init script own the state.
