# OPTICA / Atelier theme — structure & edit map

Internal reference for this codebase: **Shopify Horizon (OS 2.0)** base + **OPTICA** homepage and **Atelier** product/custom sections.

---

## 1. Directory map

| Area | Path | Purpose |
|------|------|---------|
| Layout shell | `layout/theme.liquid` | `<html>`, header group, `main`, footer group, `body` classes (`template-index` on homepage, `template-product` on product pages). |
| Global CSS | `assets/atelier-luxury.css` | OPTICA homepage-only styling (`body.template-index`), header/cart/logo tweaks, product cards, quick-add, marquee, newsletter, testimonials, category titles. |
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
| `sections/atelier-trust-features.liquid` | Icon grid “why choose us” (not used on current index if replaced by `optica-trust-bar`). |
| `sections/atelier-testimonials.liquid` | Testimonial cards + scroll / arrows. |
| `sections/atelier-ugc.liquid` | UGC grid (optional; not on current index). |
| `sections/atelier-newsletter.liquid` | Email signup + gold CTA styling. |

---

## 4. Product blocks (custom)

Registered on **`blocks/_product-details.liquid`** schema so they appear inside product details:

| File | Role |
|------|------|
| `blocks/atelier-lens-select.liquid` | `<select>` line item property (lens options). |
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
- **Homepage-only header polish**: **`assets/atelier-luxury.css`** under `body.template-index`.

### Footer columns & menus

- **`sections/footer-group.json`**: which sections load (e.g. `optica-footer-columns`).
- **`sections/optica-footer-columns.liquid`**: markup + schema; assign **Shop / Support / Company** menus in the editor per section instance.

### OPTICA hero copy & CTAs

- **`sections/optica-split-hero.liquid`** (defaults in schema) or **Theme Editor** → Home → OPTICA split hero.

### Marquee (gold strip)

- Section in **`templates/index.json`** (`marquee_strip`): `color_scheme` (e.g. `scheme-5`), text blocks.

### Trust bar copy

- **`sections/optica-trust-bar.liquid`** blocks or editor.

### New Arrivals grid

- **`templates/index.json`** → `new_arrivals` (`product-list`): `collection`, `max_products`, `columns`, `color_scheme`, and nested `static-header` / `static-product-card` blocks.

### Product page: lens / frame / swatches / recommendations

- **`templates/product.json`**: `order` starts with `optica-product-breadcrumbs`, then `main` (`product-information`), then `product-recommendations`. Inside `product-details`: badges, vendor, title, SKU + reviews, price + savings badge, `variant-picker`, lens + frame guide, inventory + buy buttons + wishlist, accordion (details / shipping / authenticity).
- **`assets/optica-pdp.css`**: PDP-only visual polish (`body.template-product`).
- **`product-recommendations`**: “COMPLETE THE LOOK” / “You May Also Like” header group + “VIEW ALL” button; `columns` 4, `max_products` 4, `complementary` intent.

### Global “luxury” tweaks without touching Horizon core

- Prefer **`assets/atelier-luxury.css`** and **`body.template-index`** scoping for homepage-only changes, and **`assets/optica-pdp.css`** for product pages.

---

## 6. Important conventions

- **JSON template keys**: Horizon mixes underscores (`block_order`, `vertical_on_mobile`) and hyphens (`padding-block-start`). Do not bulk-rename.
- **Homepage H1**: `layout/theme.liquid` does **not** output the visually hidden shop `h1` on `index` so the **split hero** can own the visible `<h1>` (see `sections/header.liquid` comment). Other templates still get the hidden `h1` where applicable.
- **Sticky header / cart drawer**: Controlled by theme settings + Horizon; cart is **`header-actions`** + `cart-drawer` when `cart_type` is drawer.
- **Updating Horizon upstream**: This theme is forked from Horizon; merging Shopify updates requires manual diff.

---

## 7. Quick file checklist for “make it look like the mockup again”

1. `assets/atelier-luxury.css` — spacing, gold borders, template-index overrides.  
2. `assets/optica-pdp.css` — product page mockup alignment.  
3. `templates/index.json` — section order and copy.  
4. `templates/product.json` — PDP structure and recommendations.  
5. `sections/header-group.json` — nav layout.  
6. `config/settings_data.json` — global colors & button radius.  
7. `sections/optica-split-hero.liquid` — hero structure & SVG.  
8. `sections/optica-footer-columns.liquid` — footer columns.

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

*Last updated to include post-`e945ad0` About/Contact additions and homepage/PDP refinements.*
