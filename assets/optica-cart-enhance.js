/**
 * OPTICA cart enhancements
 * ------------------------
 * Layered on top of Horizon's cart drawer without forking core JS. Provides:
 *   1. Live updates to the free-shipping progress bar on every cart change.
 *   2. A FLIP "fly-to-cart" animation when a product is added from the PDP.
 *
 * Listens to the existing Horizon `cart:update` event (see `assets/events.js`).
 */

const SELECTORS = {
  freeship: '[data-optica-freeship]',
  freeshipFill: '[data-optica-freeship-fill]',
  freeshipLabel: '[data-optica-freeship-label]',
  freeshipRemaining: '[data-optica-freeship-remaining]',
  cartIcon: 'cart-icon',
  cartDrawerTrigger: '[data-testid="cart-drawer-trigger"]',
};

const reduceMotion =
  typeof window !== 'undefined' &&
  window.matchMedia &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* ---------- Free-shipping progress bar ---------- */

function formatMoney(cents) {
  // Use Shopify's money format when available, otherwise fall back to a plain
  // localized number. This avoids a network roundtrip for every keystroke.
  try {
    const locale = document.documentElement.lang || 'en';
    const currency = window.Shopify?.currency?.active || 'USD';
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(cents / 100);
  } catch (_) {
    return `$${(cents / 100).toFixed(2)}`;
  }
}

function updateFreeShipBars(totalCents) {
  const bars = document.querySelectorAll(SELECTORS.freeship);
  bars.forEach((bar) => {
    const threshold = Number(bar.dataset.threshold) || 0;
    if (threshold <= 0) return;

    const total = Number.isFinite(totalCents) ? totalCents : Number(bar.dataset.total) || 0;
    const remaining = Math.max(threshold - total, 0);
    const progress = Math.min(100, Math.round((total / threshold) * 100));
    const met = total >= threshold;

    bar.dataset.total = String(total);
    bar.classList.toggle('optica-freeship--met', met);

    const fill = bar.querySelector(SELECTORS.freeshipFill);
    if (fill) fill.style.width = `${progress}%`;

    const label = bar.querySelector(SELECTORS.freeshipLabel);
    if (!label) return;

    if (met) {
      label.innerHTML =
        '<span class="optica-freeship__check" aria-hidden="true">' +
        '<svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" width="14" height="14">' +
        '<path d="M3 8.5 L6.5 12 L13 4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>' +
        '</svg></span> Complimentary shipping included';
    } else {
      label.innerHTML = `Add <strong data-optica-freeship-remaining>${formatMoney(
        remaining
      )}</strong> to unlock complimentary shipping`;
    }
  });
}

function handleCartUpdate(event) {
  const resource = event?.detail?.resource;
  if (resource && typeof resource.total_price === 'number') {
    updateFreeShipBars(resource.total_price);
    return;
  }
  // Fall back to a fetch when the event doesn't carry the cart payload.
  fetch(`${window.Shopify?.routes?.root || '/'}cart.js`, {
    headers: { Accept: 'application/json' },
  })
    .then((res) => res.json())
    .then((cart) => updateFreeShipBars(cart.total_price))
    .catch(() => {});
}

document.addEventListener('cart:update', handleCartUpdate);

/* ---------- Fly-to-cart animation ---------- */

const FLY_ENABLED = (() => {
  // The Liquid template exposes this through a data attribute on body when set.
  // Default-on; users opt out via theme settings -> body[data-optica-atc-fly="false"].
  const flag = document.body?.dataset?.opticaAtcFly;
  if (flag === 'false') return false;
  return !reduceMotion;
})();

function getFirstVisibleProductImage(form) {
  // Try to find the product's main image associated with this form's section.
  const section =
    form.closest('[data-section-id]') ||
    form.closest('section') ||
    document;

  return (
    section.querySelector(
      '.product-media__image, .product-media-container img, .product-media img, .product__media img'
    ) ||
    document.querySelector('img[data-product-featured-image]')
  );
}

function flyToCart(imgEl, targetEl) {
  if (!imgEl || !targetEl) return;

  const startRect = imgEl.getBoundingClientRect();
  const endRect = targetEl.getBoundingClientRect();
  if (startRect.width === 0 || endRect.width === 0) return;

  const clone = imgEl.cloneNode(true);
  clone.classList.add('optica-atc-fly-clone');
  Object.assign(clone.style, {
    position: 'fixed',
    top: `${startRect.top}px`,
    left: `${startRect.left}px`,
    width: `${startRect.width}px`,
    height: `${startRect.height}px`,
    margin: '0',
    pointerEvents: 'none',
    zIndex: '9999',
    borderRadius: '4px',
    transition: 'transform var(--optica-dur-slow, 560ms) var(--optica-ease, cubic-bezier(.22,.61,.36,1)), opacity 200ms ease-out',
    willChange: 'transform, opacity',
  });
  document.body.appendChild(clone);

  const dx =
    endRect.left + endRect.width / 2 - (startRect.left + startRect.width / 2);
  const dy =
    endRect.top + endRect.height / 2 - (startRect.top + startRect.height / 2);

  requestAnimationFrame(() => {
    clone.style.transform = `translate(${dx}px, ${dy}px) scale(0.08)`;
    clone.style.opacity = '0';
  });

  const cleanup = () => clone.remove();
  clone.addEventListener('transitionend', cleanup, { once: true });
  setTimeout(cleanup, 1000);

  // Pulse the cart icon.
  const cartIcon = document.querySelector(SELECTORS.cartIcon);
  if (cartIcon) {
    cartIcon.classList.remove('optica-cart-icon--pulse');
    void cartIcon.offsetWidth;
    cartIcon.classList.add('optica-cart-icon--pulse');
    setTimeout(() => cartIcon.classList.remove('optica-cart-icon--pulse'), 600);
  }
}

if (FLY_ENABLED) {
  document.addEventListener(
    'submit',
    (event) => {
      const form = event.target;
      if (!(form instanceof HTMLFormElement)) return;
      if (form.getAttribute('action') !== '/cart/add' && !form.matches('form[action*="/cart/add"]'))
        return;

      const target =
        document.querySelector(SELECTORS.cartDrawerTrigger) ||
        document.querySelector(SELECTORS.cartIcon);
      const img = getFirstVisibleProductImage(form);
      flyToCart(img, target);
    },
    true
  );
}
