// @ts-nocheck
/**
 * OPTICA cart bundle integrity
 * ----------------------------
 * Keeps paired frame + lens add-on line items in sync when a customer removes
 * the frame from the cart drawer or cart page. Without this, removing the
 * frame leaves an orphan lens add-on line that:
 *   - keeps `cart.total_price` non-zero,
 *   - shows "Cart (0)" in the bubble (it subtracts add-ons),
 *   - leaves an enabled Checkout button for a phantom cart.
 *
 * We patch `cart-items-component.onLineItemRemove` once the custom element is
 * defined, so we layer on top of Horizon's component without forking core JS.
 *
 * Pairing convention (see blocks/atelier-lens-select.liquid):
 *   - The add-on line carries property `Linked frame variant: <frame variant id>`.
 *   - The frame row exposes `data-variant-id` and, when an add-on exists, also
 *     `data-optica-paired-addon-key` (see snippets/cart-products.liquid).
 */

(function () {
  const PAIRED_KEY_ATTR = 'data-optica-paired-addon-key';

  function fetchCartJson() {
    const root = (window.Shopify && window.Shopify.routes && window.Shopify.routes.root) || '/';
    return fetch(`${root}cart.js`, { headers: { Accept: 'application/json' } }).then((r) => r.json());
  }

  function findAddonKeyForVariant(cart, frameVariantId) {
    if (!cart || !Array.isArray(cart.items) || !frameVariantId) return null;
    const target = String(frameVariantId);
    for (const item of cart.items) {
      const props = item.properties || {};
      const linked = props['Linked frame variant'];
      if (linked && String(linked).trim() === target) return item.key;
    }
    return null;
  }

  /**
   * Issue a single /cart/update.js with both lines zeroed and the same
   * sections list the component would have requested, so Horizon's morph path
   * can re-render in one shot.
   */
  async function removeBundle(component, frameKey, addonKey) {
    const sectionsToUpdate = new Set();
    if (component.dataset.sectionId) sectionsToUpdate.add(component.dataset.sectionId);
    document.querySelectorAll('cart-items-component').forEach((el) => {
      if (el instanceof HTMLElement && el.dataset.sectionId) sectionsToUpdate.add(el.dataset.sectionId);
    });

    const body = {
      updates: { [frameKey]: 0, [addonKey]: 0 },
      sections: Array.from(sectionsToUpdate).join(','),
      sections_url: window.location.pathname,
    };

    const root = (window.Shopify && window.Shopify.routes && window.Shopify.routes.root) || '/';
    const response = await fetch(`${root}cart/update.js`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(body),
    });
    const cart = await response.json();
    if (!response.ok) throw new Error(cart && cart.description ? cart.description : 'Cart update failed');
    return cart;
  }

  function computeDisplayCount(cart) {
    let count = Number(cart.item_count || 0);
    for (const item of cart.items || []) {
      const linked = item.properties && item.properties['Linked frame variant'];
      if (linked) count -= Number(item.quantity || 0);
    }
    return count < 0 ? 0 : count;
  }

  function dispatchCartUpdate(component, cart) {
    document.dispatchEvent(
      new CustomEvent('cart:update', {
        bubbles: true,
        detail: {
          resource: cart,
          sourceId: 'optica-cart-bundle',
          data: {
            source: 'optica-cart-bundle',
            itemCount: computeDisplayCount(cart),
            sections: cart.sections || {},
          },
        },
      })
    );
  }

  customElements.whenDefined('cart-items-component').then(() => {
    const ctor = customElements.get('cart-items-component');
    if (!ctor || !ctor.prototype || typeof ctor.prototype.onLineItemRemove !== 'function') return;
    if (ctor.prototype.__opticaBundlePatched) return;
    ctor.prototype.__opticaBundlePatched = true;

    const originalOnLineItemRemove = ctor.prototype.onLineItemRemove;

    ctor.prototype.onLineItemRemove = function (line) {
      const row = this.refs && this.refs.cartItemRows ? this.refs.cartItemRows[line - 1] : null;
      const frameVariantId = row && row.getAttribute ? row.getAttribute('data-variant-id') : null;
      const frameKey = row && row.dataset ? row.dataset.key : null;
      const hintedAddonKey = row && row.getAttribute ? row.getAttribute(PAIRED_KEY_ATTR) : null;

      // No row or no variant id: nothing to bundle. Defer to Horizon.
      if (!row || !frameVariantId || !frameKey) {
        return originalOnLineItemRemove.call(this, line);
      }

      // Resolve the paired add-on key. Trust the SSR hint when present, else
      // discover it client-side. Either way, if there is no paired add-on we
      // fall back to the original Horizon flow (which also handles the
      // optimistic empty-cart UI when truly removing the last item).
      const resolveAddonKey = hintedAddonKey
        ? Promise.resolve(hintedAddonKey)
        : fetchCartJson().then((cart) => findAddonKeyForVariant(cart, frameVariantId));

      resolveAddonKey
        .then((addonKey) => {
          if (!addonKey) {
            originalOnLineItemRemove.call(this, line);
            return null;
          }

          // We have a bundle. Skip Horizon's optimistic empty-cart flash and
          // its single-line /cart/change call; do a single /cart/update.js
          // that zeroes both lines at once, then let cart-items-component's
          // own cart:update listener morph the section.
          this.classList.add('cart-items-disabled');
          return removeBundle(this, frameKey, addonKey)
            .then((cart) => {
              dispatchCartUpdate(this, cart);
            })
            .catch((error) => {
              console.error('[optica-cart-bundle]', error);
              // Hard fall back to original behavior so the user still gets
              // some response from clicking remove.
              originalOnLineItemRemove.call(this, line);
            })
            .finally(() => {
              this.classList.remove('cart-items-disabled');
            });
        })
        .catch((error) => {
          console.error('[optica-cart-bundle]', error);
          originalOnLineItemRemove.call(this, line);
        });
    };
  });
})();
