# OPTICA / Atelier theme — structure & edit map

Internal reference for this codebase: **Shopify Horizon (OS 2.0)** base with **OPTICA** homepage patterns and **Atelier** reusable product/custom components.

---

## 1. Directory map

| Area | Path | Purpose |
|------|------|---------|
| Layout shell | `layout/theme.liquid` | `<html>`, header group, `main`, footer group. **`body`** always includes **`atelier-optica`** on the main storefront layout; plus `template-index` (homepage) and `template-product` (PDP) when applicable. Password uses `layout/password.liquid` and does not get `atelier-optica`. |
| Global CSS | `assets/atelier-luxury.css` | **Header** (centered nav, logo type, cart): scoped with **`body.atelier-optica`** so it matches the homepage on all templates using `theme.liquid`. **Homepage-only** sections (marquee, product cards, quick-add, newsletter, testimonials, category titles, button radius vars): scoped with **`body.template-index`**. |
| Product page CSS | `assets/optica-pdp.css` | OPTICA PDP-only styling (`body.template-product`): gold accents, typography, gallery thumbnails, variant selection, ATC + wishlist row, accordions, recommendations header. |
| Core CSS | `assets/base.css` | Horizon (do not fork lightly). |
| Styles load order | `snippets/stylesheets.liquid` | Loads `base.css` + `atelier-luxury.css`; loads `optica-pdp.css` when `template.name == 'product'`. |
| SEO / meta | `snippets/meta-tags.liquid` | `theme-color`, OG, Twitter, canonical. |
| Theme settings schema | `config/settings_schema.json` | Fonts, color schemes, cart, quick-add, etc. |
| Saved settings | `config/settings_data.json` | Live values (colors, `quick_add`, button radius, fonts). |
| Homepage JSON | `templates/index.json` | Section order & section settings for the index template. |
| Product template | `templates/product.json` | Product page: breadcrumb strip section + `product-information` (gallery, details blocks) + recommendations. |
| About page templates | `sections/optica-about.liquid` + `templates/page.about.json` | Dedicated About page section and JSON template. |
| Contact page templates | `sections/optica-contact.liquid` + `templates/page.contact.json` | Dedicated Contact page section and JSON template wiring. |
| PDP breadcrumbs | `sections/optica-product-breadcrumbs.liquid` + `snippets/optica-breadcrumbs.liquid` | Centered Home / collection / product strip under the header (product template only). |
| Header instance | `sections/header-group.json` | Announcement bar + header section settings (logo position, menu row, actions as text). |
| Footer instance | `sections/footer-group.json` | Which footer sections render and their settings. |

---

## 2. OPTICA-specific sections (custom)

| File | Role |
|------|------|
| `sections/optica-split-hero.liquid` | Split hero: copy + gold-outline CTAs + right SVG (glasses/watch) + watermark text. |
| `sections/optica-trust-bar.liquid` | Four trust items with icons + dividers. |
| `sections/optica-footer-columns.liquid` | Four-column footer (brand + 3× `link_list`) + copyright + payment icons. Enabled **only** in footer group. |
| `sections/optica-product-breadcrumbs.liquid` | Product template breadcrumb strip; enabled in `templates/product.json` `order` before `main`. |

**Homepage order** is defined in `templates/index.json` (`order` array). Current stack: split hero → marquee → trust bar → category tiles → New Arrivals (product list) → testimonials → newsletter.

---

## 3. Atelier sections (reusable)

| File | Role |
|------|------|
| `sections/atelier-category-tiles.liquid` | Three category tiles (image, title, URL). |
| `sections/atelier-trust-features.liquid` | Icon grid “why choose us” section (optional when `optica-trust-bar` is used). |
| `sections/atelier-testimonials.liquid` | Testimonial cards + scroll / arrows. |
| `sections/atelier-ugc.liquid` | UGC grid (optional; not on current index). |
| `sections/atelier-newsletter.liquid` | Email signup + gold CTA styling. |

---

## 4. Product blocks (custom)

Registered on **`blocks/_product-details.liquid`** schema so they appear inside product details:

| File | Role |
|------|------|
| `blocks/atelier-lens-select.liquid` | `<select>` line item property (lens options). |
| `blocks/atelier-prescription-input.liquid` | Prescription capture (OD/OS + PD) shown when selected lens requires Rx; supports optional manual entry and optional file upload, plus optional send-later toggle. Uses `custom.enable_prescription` when present, with safe default-on behavior when the metafield is unset. |
| `blocks/atelier-frame-guide.liquid` | `<dialog>` frame size guide. |
| `blocks/optica-product-badges.liquid` | “NEW ARRIVAL” (tag-driven) + “IN STOCK” badges. |
| `blocks/optica-savings-badge.liquid` | “SAVE X%” when `compare_at_price` &gt; price. |
| `blocks/optica-wishlist-button.liquid` | Outline heart link (set URL in editor; no native wishlist). |

**Product template** block order: `templates/product.json` → `main` → `product-details` → `blocks` / `block_order`.

**Reviews**: The `review` block uses Shopify standard rating metafields (`reviews.rating`); a reviews app or compatible data is required for stars to appear.

**Wishlist**: The wishlist control is a configurable link (default `/pages/wishlist`); replace with an app URL when needed.

---

## 5. Where to change common things

### Brand colors & typography (whole store)

1. **Theme Editor** → Theme settings → Colors / Typography (preferred for merchants).
2. Or **`config/settings_data.json`** → `current.color_schemes` (`scheme-1` … `scheme-6`) and font keys (`type_heading_font`, `type_body_font`, etc.).

### Homepage content & section order

- **`templates/index.json`**: reorder `order`, edit each section’s `settings` and `blocks`.
- **Theme Editor** → Customize → Home: drag sections and edit (syncs to JSON on save in admin).

### Header (centered logo, menu under logo, cart style)

- **`sections/header-group.json`**: `header_section.settings` (e.g. `logo_position`, `menu_row`, `actions_display_style`, `color_scheme_top`).
- **`sections/header.liquid`**: core Horizon header (avoid large edits; sync with `assets/utilities.js` if touching header height logic).
- **OPTICA header look storewide**: **`assets/atelier-luxury.css`** — rules under **`body.atelier-optica`** (≥750px breakpoint for layout tweaks). The class is output on **`<body>`** in **`layout/theme.liquid`** so collection, page, cart, and other templates match the homepage header without duplicating selectors per template.

### Footer columns & menus

- **`sections/footer-group.json`**: which sections load (e.g. `optica-footer-columns`).
- **`sections/optica-footer-columns.liquid`**: markup + schema; assign **Shop / Support / Company** menus in the editor per section instance.

### OPTICA hero copy & CTAs

- **`sections/optica-split-hero.liquid`** (defaults in schema) or **Theme Editor** → Home → OPTICA split hero.

### Marquee (gold strip)

- Section in **`templates/index.json`** (`marquee_strip`): `color_scheme` (e.g. `scheme-5`), text blocks.

### Trust bar copy

- **`sections/optica-trust-bar.liquid`**: edit blocks in code or Theme Editor.

### New Arrivals grid

- **`templates/index.json`** → `new_arrivals` (`product-list`): `collection`, `max_products`, `columns`, `color_scheme`, and nested `static-header` / `static-product-card` blocks.

### Product page: layout, lens flow, and recommendations

- **`templates/product.json`**: `order` starts with `optica-product-breadcrumbs`, then `main` (`product-information`), then `product-recommendations`. Inside `product-details` the intent is variant-first flow, then lens, then prescription, then buy actions (with frame guide optional/disabled by default), followed by inventory, wishlist, and accordion blocks (details / shipping / authenticity).
- **`assets/optica-pdp.css`**: PDP-only visual polish (`body.template-product`).
- **`product-recommendations`**: “COMPLETE THE LOOK” / “You May Also Like” header group + “VIEW ALL” button; `columns` 4, `max_products` 4, `complementary` intent.

### Global “luxury” tweaks without touching Horizon core

- Prefer **`assets/atelier-luxury.css`** for shared UI: use **`body.atelier-optica`** for cross-template header styling and **`body.template-index`** for homepage-only sections. Use **`assets/optica-pdp.css`** for product-page styling under **`body.template-product`**.

---

## 6. Important conventions

- **JSON template keys**: Horizon mixes underscores (`block_order`, `vertical_on_mobile`) and hyphens (`padding-block-start`). Do not bulk-rename.
- **Homepage H1**: `layout/theme.liquid` does **not** output the visually hidden shop `h1` on `index` so the **split hero** can own the visible `<h1>` (see `sections/header.liquid` comment). Other templates still get the hidden `h1` where applicable.
- **`atelier-optica` body class**: Declared in **`layout/theme.liquid`** for storefront pages; use it in **`atelier-luxury.css`** when a style should follow the homepage header on every template (not only `template-index` / `template-product`).
- **Sticky header / cart drawer**: Controlled by theme settings + Horizon; cart is **`header-actions`** + `cart-drawer` when `cart_type` is drawer.
- **Updating Horizon upstream**: This theme is forked from Horizon; merging Shopify updates requires manual diff.

---

## 7. Quick file checklist for “make it look like the mockup again”

1. `layout/theme.liquid` — `body` classes (`atelier-optica`, `template-index`, `template-product`).  
2. `assets/atelier-luxury.css` — `body.atelier-optica` header; `body.template-index` homepage sections.  
3. `assets/optica-pdp.css` — product page mockup alignment.  
4. `templates/index.json` — section order and copy.  
5. `templates/product.json` — PDP structure and recommendations.  
6. `sections/header-group.json` — nav layout.  
7. `config/settings_data.json` — global colors & button radius.  
8. `sections/optica-split-hero.liquid` — hero structure & SVG.  
9. `sections/optica-footer-columns.liquid` — footer columns.

---

## 8. Changes since last doc update

Changes detected since the previous reference update commit (`e945ad0`):

- **Added page templates / sections**
  - `sections/optica-about.liquid`
  - `sections/optica-contact.liquid`
  - `templates/page.about.json`
- **Homepage + PDP template updates**
  - `templates/index.json`
  - `templates/product.json`
  - `templates/page.contact.json`
- **Section updates**
  - `sections/optica-split-hero.liquid`
  - `sections/optica-product-breadcrumbs.liquid`
  - `sections/atelier-category-tiles.liquid`
  - `sections/atelier-testimonials.liquid`
  - `sections/atelier-trust-features.liquid`
  - `sections/header-group.json`
  - `sections/footer-group.json`
- **Product block updates**
  - `blocks/atelier-prescription-input.liquid`
  - `blocks/atelier-frame-guide.liquid`
  - `blocks/atelier-lens-select.liquid`
  - `blocks/optica-product-badges.liquid`
  - `blocks/optica-savings-badge.liquid`
  - `blocks/optica-wishlist-button.liquid`
- **Styling / behavior updates**
  - `assets/atelier-luxury.css`
  - `assets/optica-pdp.css`
  - `assets/auto-close-details.js`
  - `snippets/stylesheets.liquid`
- **Theme data update**
  - `config/settings_data.json`

---

*Last updated: documented `atelier-optica` on `body` (`layout/theme.liquid`) and storewide header rules in `assets/atelier-luxury.css`; §8 above remains the file delta since commit `e945ad0`.*

---

## 9. Phase 1 customer-experience foundation

Shipped on branch `phase-1-cx-foundation` as three independent commits. All new selectors are scoped under `body.atelier-optica`; no Horizon-core JS files were forked.

### Motion tokens (commit 1)

Defined at the top of `assets/atelier-luxury.css` and reused across cart, search, and view transitions:

| Token | Default | Purpose |
|---|---|---|
| `--optica-ease` | `cubic-bezier(.22,.61,.36,1)` | General-purpose easing |
| `--optica-ease-out` | `cubic-bezier(.16,1,.3,1)` | Editorial slide / morph |
| `--optica-dur-fast` | `180ms` | Micro-interactions |
| `--optica-dur-base` | `320ms` | Drawer / modal slides |
| `--optica-dur-slow` | `560ms` | View transitions, fly-to-cart |

A `prefers-reduced-motion: reduce` block collapses all three durations to `0ms`.

### Cart drawer (commit 2)

- New file: `assets/optica-cart-enhance.js` — module loaded from `snippets/header-actions.liquid` next to `cart-drawer.js`. Listens for the existing `cart:update` event (from `assets/events.js`) and refreshes the free-ship bar without re-render flash; runs a FLIP fly-to-cart animation on `submit` of any `/cart/add` form.
- `snippets/cart-summary.liquid` injects a free-ship progress bar above `.cart-totals`. Controlled by `settings.optica_free_shipping_threshold` (cents). Shows "Complimentary shipping included" with a line-drawn check when met.
- `snippets/cart-products.liquid` widens the visible-property filter from the hardcoded `'Lens package'` to any non-`_` property, so Rx status, lens coatings, engraving notes, etc. all surface.
- `layout/theme.liquid` exposes the new ATC-fly setting via `data-optica-atc-fly` on `<body>`.

### Predictive search (commit 3)

- New file: `assets/optica-search-enhance.js` — module loaded from `snippets/search-modal.liquid`. Binds `cmdK`/`Ctrl+K` to open the existing search dialog (uses Horizon's `showDialog()` API on `<dialog-component id="search-modal">`), maintains `localStorage` key `optica:recent_searches` (cap 6, dedupe, newest first), and implements Left/Right arrow pane navigation when the input is empty.
- `snippets/search-modal.liquid` adds an `<aside data-optica-search-sidebar>` with Popular links and a Recent searches slot populated by JS.
- Two-pane CSS grid layout (`.optica-search-panes`) activates ≥900px; modal width widens to `min(78dvw, 980px)`.

### New theme settings (additive)

Under "OPTICA cart" in `config/settings_schema.json`:

| Setting id | Type | Default | Used by |
|---|---|---|---|
| `optica_free_shipping_threshold` | number (cents) | `10000` ($100) | Free-ship bar — set to `0` to disable |
| `optica_atc_fly_animation` | checkbox | `true` | Fly-to-cart animation |

### New body-scoped class families

| Prefix | Where |
|---|---|
| `.optica-freeship*` | `snippets/cart-summary.liquid` + CSS in `assets/atelier-luxury.css` |
| `.optica-line-item-props` | `snippets/cart-products.liquid` |
| `.optica-cart-icon--pulse` | injected by `optica-cart-enhance.js` |
| `.optica-atc-fly-clone` | injected by `optica-cart-enhance.js` |
| `.optica-search-modal`, `.optica-search-panes*`, `.optica-search-sidebar*` | `snippets/search-modal.liquid` + CSS |

### Horizon-core edits

None required. The original plan reserved hooks in `sections/header.liquid` and `assets/cart-drawer.js`; both were avoided because Horizon already dispatches `cart:update` via `assets/events.js` and the search modal already exposes the `showDialog()` method and a `#cmdk-input` id. Future Horizon upstream merges therefore remain clean.

### Deferred (not in this phase)

- Lens-type / Rx-ready badge on predictive-search product cards (requires a merchant tag convention; revisit when collection schema is finalized).
- Mega-menu, sticky mini-PDP header, virtual try-on, Rx OCR — see broader roadmap.

