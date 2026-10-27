# Page Shell

Every Maryland state page follows the same top-to-bottom structural order. **Do not improvise the shell** — use this exact sequence.

## The structure

```
<!DOCTYPE html>
<html lang="en">
<head>
  <!-- See references/setup.md for CDN tags and init script -->
</head>
<body>

  <!-- 1. Skip nav link (keyboard accessibility) -->
  <a class="usa-skipnav" href="#main-content">Skip to main content</a>

  <!-- 2. USWDS Statewide Banner (REQUIRED) -->
  <section class="usa-banner" aria-label="Official website of the State of Maryland">
    ...
  </section>

  <!-- 3. Optional global alert (statewide/emergency notification) -->
  <div class="maryland-alert maryland-alert--info">
    ...
  </div>

  <!-- 4. Maryland Header (logo + utility nav + primary nav) -->
  <header class="maryland-header">
    ...
  </header>

  <!-- 5. Main content -->
  <main id="main-content" tabindex="-1">
    ...
  </main>

  <!-- 6. Maryland footer — one <footer>, two __section siblings:
          agency section first, statewide section second. See
          references/components/maryland-footer.md for the rationale
          (margin-collapse between the sections depends on them being
          siblings inside the same <footer>). -->
  <footer class="maryland-footer">
    <div class="maryland-footer__container">
      <section class="maryland-footer__section">
        <!-- agency identity, contact, link groups -->
      </section>
      <div class="maryland-footer__section">
        <!-- "Explore Maryland.gov" + statewide link groups + branding -->
      </div>
    </div>
  </footer>

</body>
</html>
```

## Visual top-to-bottom

| # | Component | Visual | Required? |
|---|---|---|---|
| 1 | `usa-skipnav` | Hidden until keyboard-focused; appears as a dark link at the very top. | Yes (accessibility) |
| 2 | `usa-banner` | Thin gray strip with "An official website of the State of Maryland", expandable "Here's how you know" section. Optional Maryland.gov link + Translate link on the right. | **Yes** (state requirement) |
| 3 | `maryland-alert` (global) | Full-width colored strip below banner. Color = severity (info/warning/error/success/emergency). | No |
| 4 | `maryland-header` | White background. Top-row utility links (small text right-aligned), then full Maryland wordmark logo + agency name, then horizontal nav bar with primary links. Mobile collapses to a hamburger menu. | Yes |
| 5 | `<main>` | Page-specific content. Often starts with a `maryland-hero` then `usa-prose` body + components. | Yes |
| 6 | `maryland-footer` with two `__section` children | Dark navy. First section: agency identity, address, phone, email, social, link groups. Second section: statewide "Explore Maryland.gov" link groups and branding. | **Yes** (state branding) |
| 6a | `<maryland-statewide-footer>` web component | Alternative to #6, for state-level pages only (Maryland.gov homepage, standalone pages with no agency block). Do **not** use alongside #6 on agency pages — causes a double-gap spacing bug. | For state-level pages only |

## Why this order matters

- **`usa-skipnav` must be the first focusable element** so a keyboard user can bypass the banner/header on every page.
- **The banner before the header** because state branding takes precedence over agency branding.
- **`<main id="main-content" tabindex="-1">`** is the skipnav target. The `id` and `tabindex` are both required for the skipnav to work — without `tabindex="-1"`, focus won't move to `<main>` when the link is activated.
- **Agency pages render both the agency and statewide blocks as sibling `__section` children of one `<footer class="maryland-footer">`.** Agency section first, statewide section second. The `<maryland-statewide-footer>` web component is reserved for state-level pages without an agency block (Maryland.gov homepage). Mixing the two causes a double-gap spacing bug — see `references/components/maryland-footer.md`.

## Page-type variations

- **Maryland.gov homepage** uses no agency footer (just the statewide footer) and has the `landing-main` hero variant.
- **Agency homepage** uses the agency footer plus the statewide footer.
- **Pages with a sidebar** wrap `<main>` content in a `grid-row` with `desktop:grid-col-3` (sidebar) + `desktop:grid-col-8` (content).
- **Listing pages** put a search/filter strip at the top of `<main>`, then a `usa-collection` body, then pagination.

See `references/recipes/` for assembled examples of each.

## Mandatory accessibility attributes

| Element | Attribute | Why |
|---|---|---|
| `<html>` | `lang="en"` | WCAG 3.1.1 — Language of Page |
| `<a class="usa-skipnav">` | `href="#main-content"` | Skip navigation target |
| `<section class="usa-banner">` | `aria-label="Official website of the State of Maryland"` | Banner role announcement |
| `<main>` | `id="main-content"` and `tabindex="-1"` | Skipnav target + focusable |
| Header logo `<img>` | `alt="{Agency} home"` or `alt="Maryland.gov home"` | Decorative-text equivalent |
| Each `<section>` with a heading | `aria-labelledby` matching the heading's `id` | Landmark naming |

## Common shell mistakes (from real bug reports)

1. **Skipping `<a class="usa-skipnav">`** — keyboard users can't bypass the banner/header.
2. **Putting `usa-js-loading` on `<body>` instead of `<html>`** — init script targets `<html>`.
3. **Omitting `tabindex="-1"` on `<main>`** — skipnav appears to work but focus stays on the banner.
4. **Wrapping the banner in a `<header>`** — the banner is its own landmark; wrapping it changes semantics.
5. **Putting the agency footer below the statewide footer** — order is fixed: agency, then statewide.
6. **Using `<header><h1>` inside `<main>`** — the page `<h1>` lives inside the hero, not the page header.

## Full skeleton (copy and adapt)

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Page Title — Agency Name</title>

  <!-- Inline init script (see references/setup.md) -->
  <script>
    "use strict";
    const loadingClass = "usa-js-loading";
    document.documentElement.classList.add(loadingClass);
    function revertClass() { document.documentElement.classList.remove(loadingClass); }
    const fallback = setTimeout(revertClass, 8000);
    function verifyLoaded() {
      if (window.uswdsPresent) {
        clearTimeout(fallback);
        revertClass();
        window.removeEventListener("load", verifyLoaded, true);
      }
    }
    window.addEventListener("load", verifyLoaded, true);
  </script>

  <link rel="stylesheet" data-mdwds href="https://cdn.maryland.gov/mdwds/latest/css/mdwds.min.css" />
  <script type="module" src="https://cdn.maryland.gov/mdwds/latest/js/mdwds-core.js"></script>
  <script type="module" src="https://cdn.maryland.gov/mdwds/latest/js/mdwds-elements.js"></script>
</head>
<body>
  <a class="usa-skipnav" href="#main-content">Skip to main content</a>

  <section class="usa-banner" aria-label="Official website of the State of Maryland">
    <!-- See references/components/usa-banner.md for full markup -->
  </section>

  <header class="maryland-header">
    <!-- See references/components/maryland-header.md -->
  </header>

  <main id="main-content" tabindex="-1">
    <!-- Page content -->
  </main>

  <footer class="maryland-footer">
    <div class="maryland-footer__container">
      <section class="maryland-footer__section">
        <!-- agency identity + contact + link groups -->
        <!-- see references/components/maryland-footer.md -->
      </section>
      <div class="maryland-footer__section">
        <!-- "Explore Maryland.gov" + statewide links + branding -->
      </div>
    </div>
  </footer>
</body>
</html>
```
