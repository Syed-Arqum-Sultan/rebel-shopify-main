/**
 * OPTICA predictive search enhancements
 * -------------------------------------
 * Layered on top of Horizon's predictive search. Adds:
 *   1. cmdK / Ctrl+K global shortcut to open the search modal.
 *   2. Recent searches sidebar (localStorage-backed, capped at 6, deduped).
 *   3. Pane-aware keyboard navigation (Left/Right when input is empty).
 *
 * Does not modify Horizon's predictive search engine.
 */

const STORAGE_KEY = 'optica:recent_searches';
const MAX_RECENT = 6;
const SELECTORS = {
  modal: '#search-modal',
  input: '#cmdk-input',
  recentGroup: '[data-optica-recent-group]',
  recentList: '[data-optica-recent-list]',
  sidebar: '[data-optica-search-sidebar]',
  mainPane: '.optica-search-panes__main',
  form: '.predictive-search-form',
};

/* ---------- storage ---------- */

function readRecent() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.slice(0, MAX_RECENT) : [];
  } catch (_) {
    return [];
  }
}

function writeRecent(list) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_RECENT)));
  } catch (_) {
    /* quota or privacy mode — silently ignore */
  }
}

function pushRecent(query) {
  const q = (query || '').trim();
  if (q.length < 2) return;
  const existing = readRecent().filter((item) => item.toLowerCase() !== q.toLowerCase());
  existing.unshift(q);
  writeRecent(existing);
}

function searchUrlFor(query) {
  const root = (window.Shopify && window.Shopify.routes && window.Shopify.routes.root) || '/';
  return `${root.replace(/\/$/, '')}/search?q=${encodeURIComponent(query)}`;
}

/* ---------- render ---------- */

function renderRecent(modal) {
  const group = modal.querySelector(SELECTORS.recentGroup);
  const list = modal.querySelector(SELECTORS.recentList);
  if (!group || !list) return;

  const items = readRecent();
  if (items.length === 0) {
    group.hidden = true;
    list.innerHTML = '';
    return;
  }

  group.hidden = false;
  list.innerHTML = items
    .map(
      (q) =>
        `<li><a href="${searchUrlFor(q)}" data-optica-recent-item>${escapeHtml(q)}</a></li>`
    )
    .join('');
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (ch) => {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch];
  });
}

/* ---------- modal control ---------- */

function openModal() {
  const modal = document.querySelector(SELECTORS.modal);
  if (!modal) return;
  if (typeof modal.showDialog === 'function') {
    modal.showDialog();
  } else {
    const dialog = modal.querySelector('dialog');
    if (dialog && typeof dialog.showModal === 'function') dialog.showModal();
  }
  renderRecent(modal);
  // Focus the input on the next frame so the dialog has time to mount.
  requestAnimationFrame(() => {
    const input = modal.querySelector(SELECTORS.input);
    if (input) input.focus();
  });
}

/* ---------- cmdK shortcut ---------- */

function isEditableTarget(el) {
  if (!el) return false;
  if (el.isContentEditable) return true;
  const tag = el.tagName;
  return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
}

document.addEventListener('keydown', (event) => {
  const isCmdK =
    (event.metaKey || event.ctrlKey) &&
    !event.shiftKey &&
    !event.altKey &&
    event.key.toLowerCase() === 'k';
  if (!isCmdK) return;

  // Allow the browser shortcut in dev tools / address-bar focus.
  // We only steal cmdK from regular page focus.
  if (isEditableTarget(document.activeElement)) {
    // If the user is in our own search input, don't steal.
    const modal = document.querySelector(SELECTORS.modal);
    if (modal && modal.contains(document.activeElement)) return;
  }

  event.preventDefault();
  openModal();
});

/* ---------- recent-searches lifecycle ---------- */

document.addEventListener('submit', (event) => {
  const form = event.target;
  if (!(form instanceof HTMLFormElement)) return;
  if (!form.matches(SELECTORS.form)) return;
  const input = form.querySelector('input[name="q"]');
  if (input) pushRecent(input.value);
});

// Also capture clicks on predictive product results — those are navigations
// without a form submit.
document.addEventListener('click', (event) => {
  const link = event.target.closest(`${SELECTORS.modal} a[href*="/search?"]`);
  if (link) {
    try {
      const url = new URL(link.href, window.location.origin);
      const q = url.searchParams.get('q');
      if (q) pushRecent(q);
    } catch (_) {
      /* ignore malformed urls */
    }
    return;
  }
  // For product cards inside results, capture the current input value.
  const productLink = event.target.closest(
    `${SELECTORS.modal} .predictive-search-results__card a, ${SELECTORS.modal} .predictive-search-results__product a`
  );
  if (productLink) {
    const input = document.querySelector(SELECTORS.input);
    if (input && input.value) pushRecent(input.value);
  }
});

// Re-render recents whenever the dialog opens.
document.addEventListener('click', (event) => {
  const trigger = event.target.closest('[on\\:click="#search-modal/showDialog"]');
  if (!trigger) return;
  // Defer so the dialog mounts first.
  requestAnimationFrame(() => {
    const modal = document.querySelector(SELECTORS.modal);
    if (modal) renderRecent(modal);
  });
});

/* ---------- pane-aware arrow navigation ---------- */

document.addEventListener('keydown', (event) => {
  const modal = document.querySelector(SELECTORS.modal);
  if (!modal || !modal.contains(event.target)) return;
  const key = event.key;
  if (key !== 'ArrowRight' && key !== 'ArrowLeft') return;

  // Only intervene when the input is empty/unfocused (otherwise let the user
  // move the caret inside the search field normally).
  const input = modal.querySelector(SELECTORS.input);
  if (input && document.activeElement === input && input.value.length > 0) return;

  const sidebar = modal.querySelector(SELECTORS.sidebar);
  const main = modal.querySelector(SELECTORS.mainPane);
  if (!sidebar || !main) return;

  const goingRight = key === 'ArrowRight';
  const target = goingRight ? sidebar : main;
  const firstFocusable = target.querySelector('a, button, [tabindex]:not([tabindex="-1"])');
  if (firstFocusable) {
    event.preventDefault();
    firstFocusable.focus();
  }
});

// Initial render in case the modal is open on page load (rare, but harmless).
const initialModal = document.querySelector(SELECTORS.modal);
if (initialModal) renderRecent(initialModal);
