# maryland-table / usa-table

MDWDS table component. **Rewritten in MDWDS 0.50.0** to adopt the USWDS table family wholesale, with Maryland theming applied via CSS. The two class names resolve to parallel implementations:

- `usa-table` — the current, feature-complete API (0.50.0+). Full variant set, sortable columns, sticky header, GA tracking attributes. This is the one new work should use. Documented under the Storybook title **USWDS Components/Table**.
- `maryland-table` — the earlier Maryland-prefixed selector family. Still ships. Smaller variant set (`--borderless`, `--striped`, `--stacked`, `--compact`, `--sticky-header`), no `data-sortable`, no GA attributes. Documented under **MDWDS Components/Table**.

Both render Maryland-themed visuals; the Maryland typography and color tokens are mixed into both selector trees. Pick `usa-table` unless you're migrating an existing `maryland-table` page.

> **Use the USWDS variant on new Maryland pages.** The `maryland-table` family has not been removed, but every feature added since 0.50.0 lives on the USWDS side. Mixing the two class names on the same table (`class="maryland-table usa-table"`) will double-apply padding and borders — pick one.

## What it looks like

Default: a bordered table with cream-colored (`base-lightest`) header cells, dark text, and body cells with light row borders. Column headers are semibold Source Sans with 24px vertical padding; body cells are regular weight at ~16px (mobile) / 20px (mobile-lg+). The table has a 1px `base-light` outer border.

Variants modify the border/background treatment, the mobile collapse behavior, or add stacked column labels. The sortable variant adds a toggle button inside each sortable header; the sticky-header variant freezes `<thead>` during vertical scroll.

Caption: italic body-xs (~13px) `base-darkest` text positioned above the table. Required for accessibility — never omit it.

## Variants

Set `variant` to one of: `default`, `borderless`, `striped`, `stacked`, `stacked-header`, `compact`.

| Variant | Visual |
|---|---|
| `default` | Bordered, no modifier class. All cells have left/right borders. |
| `borderless` | Removes the outer border and inner column borders. Header retains its bottom border. |
| `striped` | Alternating `base-lightest` background on `<tbody>` rows. Preserves default borders. |
| `stacked` | On mobile widths (<640px), each row collapses to a single-column block with headers hidden. Each `<td>` carries a `data-label` attribute that the CSS surfaces as a pseudo-element label. |
| `stacked-header` | Like `stacked`, but at mobile widths each `<td>` renders its column header *and* value side by side. Best for tables where every column name is meaningful. |
| `compact` | Reduces vertical padding by ~50% for dense data. |

Feature flags are **orthogonal** to variants — combine freely:

- `scrollable` — wrap the table in `<div class="usa-table-container--scrollable" tabindex="0">` for horizontal scroll on narrow viewports.
- `sortable` — add `data-sortable` to each sortable `<th>`; USWDS JS inserts sort controls at runtime.
- `stickyHeader` — add `usa-table--sticky-header` to the table; `<thead>` stays visible during vertical scroll. Pairs well with `scrollable` on long datasets.

Analytics flags: `enableAnalytics` turns on the `data-ga-*` attributes on both the `<table>` and each sortable `<th>`.

## Default markup

```html
<table class="usa-table">
  <caption>Agency contact information</caption>
  <thead>
    <tr>
      <th scope="col" role="columnheader">Agency</th>
      <th scope="col" role="columnheader">Contact</th>
      <th scope="col" role="columnheader">Email</th>
      <th scope="col" role="columnheader">Phone</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Department of Information Technology</th>
      <td>John Smith</td>
      <td>john.smith@maryland.gov</td>
      <td>(410) 555-1234</td>
    </tr>
    <tr>
      <th scope="row">Department of Health</th>
      <td>Jane Doe</td>
      <td>jane.doe@maryland.gov</td>
      <td>(410) 555-5678</td>
    </tr>
    <tr>
      <th scope="row">Department of Transportation</th>
      <td>Bob Johnson</td>
      <td>bob.johnson@maryland.gov</td>
      <td>(410) 555-9012</td>
    </tr>
  </tbody>
</table>
```

**Important:** the first cell of each `<tbody>` row is a `<th scope="row">`, not a `<td>`. This is a WCAG requirement for data tables so screen readers can associate values with their row-identifying column. The template emits it automatically; preserve it when writing by hand.

**Important:** `role="columnheader"` on column `<th>`s is defensive — browsers assign it implicitly, but some screen-reader modes drop the implicit role when extra DOM is injected by sortable JS. Keep it.

## Striped variant

```html
<table class="usa-table usa-table--striped">
  <caption>Agency contact information (striped)</caption>
  <thead>
    <tr>
      <th scope="col" role="columnheader">Agency</th>
      <th scope="col" role="columnheader">Contact</th>
      <th scope="col" role="columnheader">Email</th>
      <th scope="col" role="columnheader">Phone</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Department of Information Technology</th>
      <td>John Smith</td>
      <td>john.smith@maryland.gov</td>
      <td>(410) 555-1234</td>
    </tr>
    <!-- Repeat body rows -->
  </tbody>
</table>
```

Alternating backgrounds come from `tbody tr:nth-child(odd)`. No per-row class is required.

## Borderless variant

```html
<table class="usa-table usa-table--borderless">
  <caption>Agency contact information (borderless)</caption>
  <thead>
    <tr>
      <th scope="col" role="columnheader">Agency</th>
      <th scope="col" role="columnheader">Contact</th>
      <th scope="col" role="columnheader">Email</th>
      <th scope="col" role="columnheader">Phone</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Department of Information Technology</th>
      <td>John Smith</td>
      <td>john.smith@maryland.gov</td>
      <td>(410) 555-1234</td>
    </tr>
    <!-- ...more rows... -->
  </tbody>
</table>
```

Removes all outer and column borders; keeps the thin bottom border under `<thead>`.

## Compact variant

```html
<table class="usa-table usa-table--compact">
  <caption>Agency contact information (compact)</caption>
  <thead>
    <tr>
      <th scope="col" role="columnheader">Agency</th>
      <th scope="col" role="columnheader">Contact</th>
      <th scope="col" role="columnheader">Email</th>
      <th scope="col" role="columnheader">Phone</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Department of Information Technology</th>
      <td>John Smith</td>
      <td>john.smith@maryland.gov</td>
      <td>(410) 555-1234</td>
    </tr>
    <!-- ...more rows... -->
  </tbody>
</table>
```

Cell padding drops to roughly half the default. Use for data-dense tables where visual density matters more than scanability.

## Stacked variant (mobile collapse, no header labels)

```html
<table class="usa-table usa-table--stacked">
  <caption>Agency contact information (stacked on mobile)</caption>
  <thead>
    <tr>
      <th scope="col" role="columnheader">Agency</th>
      <th scope="col" role="columnheader">Contact</th>
      <th scope="col" role="columnheader">Email</th>
      <th scope="col" role="columnheader">Phone</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row" data-label="Agency">Department of Information Technology</th>
      <td data-label="Contact">John Smith</td>
      <td data-label="Email">john.smith@maryland.gov</td>
      <td data-label="Phone">(410) 555-1234</td>
    </tr>
    <!-- ...more rows... -->
  </tbody>
</table>
```

**Important:** every `<td>` (and the row `<th>`) must carry a `data-label` attribute matching its column header. On narrow viewports the headers are hidden and `data-label` becomes the only indication of what each value is.

## Stacked-header variant (mobile collapse, with inline column labels)

```html
<table class="usa-table usa-table--stacked-header">
  <caption>Agency contact information (stacked with headers on mobile)</caption>
  <thead>
    <tr>
      <th scope="col" role="columnheader">Agency</th>
      <th scope="col" role="columnheader">Contact</th>
      <th scope="col" role="columnheader">Email</th>
      <th scope="col" role="columnheader">Phone</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row" data-label="Agency">Department of Information Technology</th>
      <td data-label="Contact">John Smith</td>
      <td data-label="Email">john.smith@maryland.gov</td>
      <td data-label="Phone">(410) 555-1234</td>
    </tr>
    <!-- ...more rows... -->
  </tbody>
</table>
```

Same `data-label` requirement as `stacked`; the difference is purely CSS — labels render alongside values rather than above them.

## Scrollable wrapper

Wrap the table in a scrollable container with a focusable scroll region.

```html
<div class="usa-table-container--scrollable" tabindex="0">
  <table class="usa-table">
    <caption>Wide dataset requiring horizontal scroll</caption>
    <thead>
      <tr>
        <th scope="col" role="columnheader">Agency</th>
        <th scope="col" role="columnheader">Contact</th>
        <th scope="col" role="columnheader">Email</th>
        <th scope="col" role="columnheader">Phone</th>
        <th scope="col" role="columnheader">Department</th>
        <th scope="col" role="columnheader">Building</th>
        <th scope="col" role="columnheader">Floor</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <th scope="row">Department of Information Technology</th>
        <td>John Smith</td>
        <td>john.smith@maryland.gov</td>
        <td>(410) 555-1234</td>
        <td>Infrastructure</td>
        <td>State House</td>
        <td>3rd</td>
      </tr>
      <!-- ...more rows... -->
    </tbody>
  </table>
</div>
```

**Important:** `tabindex="0"` on the wrapper is required. Without it, keyboard users can't reach the horizontally scrolled region. The `tabindex` makes the container itself focusable so arrow-key scrolling works.

## Sortable columns

Add `data-sortable` to each column header that should be sortable. The USWDS table JS (loaded by `mdwds-core.js`) inserts a toggle button inside the `<th>` at runtime and manages `aria-sort`.

```html
<table class="usa-table">
  <caption>Sortable agency contact information</caption>
  <thead>
    <tr>
      <th scope="col" role="columnheader" data-sortable>Agency</th>
      <th scope="col" role="columnheader" data-sortable>Contact</th>
      <th scope="col" role="columnheader">Email</th>
      <th scope="col" role="columnheader">Phone</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Department of Information Technology</th>
      <td>John Smith</td>
      <td>john.smith@maryland.gov</td>
      <td>(410) 555-1234</td>
    </tr>
    <!-- ...more rows... -->
  </tbody>
</table>
```

**Important:** sort is lexicographic by default. For dates, format them `YYYY-MM-DD` so sort order equals chronological order. For numbers, format them with equal digit widths (pad leading zeros) or let the user pre-sort.

**Important:** the USWDS JS announces sort changes via a live region injected into `<tbody>` as `.usa-table__announcement-region`. Don't remove or style it.

## Sticky header

```html
<table class="usa-table usa-table--sticky-header">
  <caption>Table with sticky header</caption>
  <thead>
    <tr>
      <th scope="col" role="columnheader">Agency</th>
      <th scope="col" role="columnheader">Contact</th>
      <th scope="col" role="columnheader">Email</th>
      <th scope="col" role="columnheader">Phone</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Department of Information Technology</th>
      <td>John Smith</td>
      <td>john.smith@maryland.gov</td>
      <td>(410) 555-1234</td>
    </tr>
    <!-- Many more rows... -->
  </tbody>
</table>
```

Only kicks in on tall tables that scroll past the viewport. Needs a scrolling ancestor (either the page itself, or a `max-height` container around the table).

## Google Analytics tracking

When `enableAnalytics` is on, add `data-ga-category`, `data-ga-action`, `data-ga-label` to the `<table>` and to each sortable `<th>`. The USWDS sortable JS fires GA events using these values when the user sorts.

```html
<table class="usa-table"
       id="table-contacts"
       data-ga-category="Table"
       data-ga-action="Interact"
       data-ga-label="Agency Contacts">
  <caption>Sortable table with Google Analytics tracking</caption>
  <thead>
    <tr>
      <th scope="col"
          role="columnheader"
          data-sortable
          data-ga-category="Table"
          data-ga-action="Sort"
          data-ga-label="Agency Contacts - Agency">
        Agency
      </th>
      <th scope="col"
          role="columnheader"
          data-sortable
          data-ga-category="Table"
          data-ga-action="Sort"
          data-ga-label="Agency Contacts - Contact">
        Contact
      </th>
      <th scope="col" role="columnheader">Email</th>
      <th scope="col" role="columnheader">Phone</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th scope="row">Department of Information Technology</th>
      <td>John Smith</td>
      <td>john.smith@maryland.gov</td>
      <td>(410) 555-1234</td>
    </tr>
    <!-- ...more rows... -->
  </tbody>
</table>
```

The non-sortable headers do not emit `data-ga-*` even when analytics is enabled — only sortable headers generate GA events.

## What each class does

### `usa-table` family (preferred)

| Class | Effect |
|---|---|
| `usa-table` | Base. Default-bordered Maryland-themed table. |
| `usa-table--borderless` | Removes column and outer borders. Keeps `<thead>` bottom border. |
| `usa-table--striped` | Alternating row backgrounds via `tr:nth-child(odd)`. |
| `usa-table--stacked` | Mobile collapse to one column per row; headers hidden; relies on `data-label`. |
| `usa-table--stacked-header` | Mobile collapse with inline column labels alongside values. |
| `usa-table--compact` | Half vertical padding. |
| `usa-table--sticky-header` | `<thead>` stays visible during vertical scroll. |
| `usa-table-container--scrollable` | Wrapper `<div>` for horizontal scroll. Needs `tabindex="0"`. |
| `usa-table__header__button` | Injected by USWDS JS inside sortable `<th>`. Carries sort icon and state. |

### `maryland-table` family (legacy)

| Class | Effect |
|---|---|
| `maryland-table` | Legacy base. Same visual as `usa-table` but with Maryland-prefixed selectors. |
| `maryland-table--borderless` / `--striped` / `--stacked` / `--compact` / `--sticky-header` | Legacy modifier equivalents. No `--stacked-header` modifier here. |
| `maryland-table-container--scrollable` | Legacy scrollable wrapper. Also uses `tabindex="0"`. |
| `maryland-table-layout--scrollable` | Internal state marker added by the legacy JS when horizontal overflow is detected. Not something you add by hand. |
| `maryland-table__caption` | Legacy caption classname — used by Tabled.js (the legacy horizontal-scroll library) when it clones the caption. The USWDS variant does not use this. |
| `maryland-table__header__button` | Legacy sort button. Only present if the legacy Tabled.js is loaded. |

## Prop schema (USWDS table generator)

| Prop | Type | Default | Notes |
|---|---|---|---|
| `variant` | `default` \| `borderless` \| `striped` \| `stacked` \| `stacked-header` \| `compact` | `default` | Table style variant. |
| `caption` | string | `"Agency contact information"` | Required for accessibility. Visible above the table. |
| `columns` | `{header, accessor, sortable}[]` | sample | Column defs. `accessor` is the row-object key for each column. |
| `rows` | `object[]` | sample | Data rows. Keys match column accessors. |
| `scrollable` | boolean | `false` | Wrap in `usa-table-container--scrollable`. |
| `sortable` | boolean | `false` | Enable sort — individual columns opt in via `sortable: true` in `columns`. |
| `stickyHeader` | boolean | `false` | Add `usa-table--sticky-header`. |
| `enableAnalytics` | boolean | `false` | Emit `data-ga-*` attributes. |
| `gaCategory` / `gaAction` / `gaLabel` | string | `"Table"` / `"Interact"` / `"Contact Information"` | GA tracking values. |

## Heading-level guidance

The `<caption>` is not a heading — it's an element inside the table that screen readers announce before the content. If the table has its own section title above it, use an `<h2>` or `<h3>` as appropriate to the page outline and the caption as a shorter accessible description.

Row `<th>` elements are not headings in the document outline either — they're semantic row identifiers. Screen readers associate them with each row's cells via `scope="row"`.

## Common mistakes

1. **Mixing class families.** `<table class="maryland-table usa-table">` double-applies styles. Pick one. New work: `usa-table`.
2. **Using `<td>` for the first column.** The first cell of each row must be `<th scope="row">`. Otherwise screen-reader users can't tell which row's value they're hearing.
3. **Omitting `<caption>`.** The caption is the table's accessible name. Without it, users of assistive tech encounter an unlabeled data block.
4. **Forgetting `data-label` on stacked variants.** On mobile, the column headers are hidden by CSS. The only indication of what each value represents is the `data-label` attribute — leave it off and mobile users get a bare list of values with no context.
5. **Removing `tabindex="0"` from the scrollable wrapper.** The container needs a focusable surface for arrow-key scrolling. Without the tabindex, keyboard users can't reach the overflowing columns.
6. **Expecting sort to understand dates/numbers.** The USWDS sort is lexicographic. Format dates `YYYY-MM-DD`; left-pad numbers; or sort server-side.
7. **Setting `aria-sort` manually.** The USWDS JS sets `aria-sort` at runtime. Pre-setting it desyncs the state the first time the user clicks a header.
8. **Adding `data-ga-*` to non-sortable headers.** GA events fire only on sort, which non-sortable columns never trigger. The attributes are inert there, and silently hint that this column *should* be sortable.
9. **Writing CSS to add column borders inside `--borderless`.** The variant deliberately strips them. If you need column separation, use `--default`, `--striped`, or `--stacked-header`.
10. **Rendering sticky-header without a scroll ancestor.** The sticky position needs an ancestor whose overflow is clipped. If the table is directly inside `<main>` and the page is the scroll ancestor, it works. If it's inside a `max-height: ...; overflow-y: auto` wrapper, that wrapper is the scroll ancestor. Confirm which, or sticky silently does nothing.
