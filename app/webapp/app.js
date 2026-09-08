// ToyStore Ops — app.js v2.1 Pro
// Warm-milk styled TMA with Multi-Language & Dark Theme

const tg = window.Telegram?.WebApp;
if (tg) { tg.ready(); tg.expand(); }

// API base: reads from window.APP_CONFIG.API_BASE (set in index.html for Vercel),
// falls back to "" (relative) when served from the same origin (Render/local).
const BASE = (window.APP_CONFIG && window.APP_CONFIG.API_BASE) || "";


// ── i18n Dictionary ───────────────────────────────────────────────────────────
const i18n = {
  ru: {
    app_title: "Manager Bot", app_sub: "ToyStore Ops",
    tab_summary: "Сводка", tab_inventory: "Склад", tab_orders: "Заказы", tab_settings: "Настройки",
    sec_finance: "Финансы", lbl_revenue: "Выручка за месяц", lbl_profit: "Чистая прибыль", lbl_cash: "В кассе (Cash Flow)",
    sec_uchtepa: "Склад выдачи", lbl_uchtepa_title: "Офис Учтепа (фасовка)", lbl_uchtepa_limit_info: "Лимит: 100 коробок",
    lbl_free: "Свободно:", lbl_filled: "заполнен", lbl_uchtepa_pill: "Учтепа",
    sec_stocks: "Товары на складах", sec_all_products: "Все товары", btn_transfer: "📦 Переместить",
    sec_orders: "Заказы", sec_leads: "Лиды", empty_orders: "Заказов пока нет", empty_leads: "Нет новых лидов",
    sec_profile: "Профиль", sec_preferences: "Предпочтения", sec_system: "Система",
    lbl_lang: "Язык интерфейса", lbl_theme: "Тема", lbl_notif: "Уведомления в бот", val_notif: "Активны (Заказы, Склад, Алерты)",
    lbl_uchtepa_limit: "Ограничение склада Учтепа", val_uchtepa_limit: "100 коробок (Максимальный объем)",
    mod_lang_title: "Выберите язык", mod_theme_title: "Тема",
    theme_light: "☀️ Светлый", theme_dark: "🌙 Тёмный",
    mod_transfer_title: "Переместить в офис", lbl_product: "Товар", lbl_from: "Откуда", lbl_to: "Куда", lbl_qty: "Количество", btn_do_transfer: "Переместить", btn_cancel: "Отмена", opt_select: "— выберите —",
    currency: "сум", pcs: "шт.",
    lang_name: "Русский", theme_light_name: "Светлый", theme_dark_name: "Тёмный"
  },
  uz: {
    app_title: "Manager Bot", app_sub: "ToyStore Ops",
    tab_summary: "Hisobot", tab_inventory: "Ombor", tab_orders: "Buyurtmalar", tab_settings: "Sozlamalar",
    sec_finance: "Moliya", lbl_revenue: "Oylik tushum", lbl_profit: "Sof foyda", lbl_cash: "Kassada (Cash Flow)",
    sec_uchtepa: "Tarqatish ombori", lbl_uchtepa_title: "Uchtepa ofisi (qadoqlash)", lbl_uchtepa_limit_info: "Limit: 100 quti",
    lbl_free: "Bo'sh joy:", lbl_filled: "to'ldirilgan", lbl_uchtepa_pill: "Uchtepa",
    sec_stocks: "Omborlardagi tovarlar", sec_all_products: "Barcha tovarlar", btn_transfer: "📦 Ko'chirish",
    sec_orders: "Buyurtmalar", sec_leads: "Mijozlar", empty_orders: "Hozircha buyurtmalar yo'q", empty_leads: "Yangi mijozlar yo'q",
    sec_profile: "Profil", sec_preferences: "Sozlamalar", sec_system: "Tizim",
    lbl_lang: "Tilni tanlash", lbl_theme: "Rejim", lbl_notif: "Bot bildirishnomalari", val_notif: "Faol (Buyurtmalar, Ombor, Ogohlantirishlar)",
    lbl_uchtepa_limit: "Uchtepa ombori limiti", val_uchtepa_limit: "100 quti (Maksimal hajm)",
    mod_lang_title: "Tilni tanlang", mod_theme_title: "Rejim",
    theme_light: "☀️ Kunduzgi rejim", theme_dark: "🌙 Tungi rejim",
    mod_transfer_title: "Ofisga ko'chirish", lbl_product: "Tovar", lbl_from: "Qayerdan", lbl_to: "Qayerga", lbl_qty: "Miqdor", btn_do_transfer: "Ko'chirish", btn_cancel: "Bekor qilish", opt_select: "— tanlang —",
    currency: "so'm", pcs: "dona",
    lang_name: "O'zbekcha", theme_light_name: "Kunduzgi rejim", theme_dark_name: "Tungi rejim"
  }
};

let currentLang = localStorage.getItem("app_lang") || "ru";
let currentTheme = localStorage.getItem("app_theme") || "light";

const $ = id => document.getElementById(id);

function applyTranslations() {
  const dict = i18n[currentLang];
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) el.textContent = dict[key];
  });
  
  $("lblCurrentLang").textContent = dict.lang_name;
  $("lblCurrentTheme").textContent = currentTheme === "dark" ? dict.theme_dark_name : dict.theme_light_name;
  
  const langInput = document.querySelector(`input[name="lang"][value="${currentLang}"]`);
  if (langInput) langInput.checked = true;
  
  const themeInput = document.querySelector(`input[name="theme"][value="${currentTheme}"]`);
  if (themeInput) themeInput.checked = true;
}

function applyTheme() {
  const isDark = currentTheme === "dark";
  document.documentElement.classList.toggle("dark", isDark);
  
  const metaColor = $("meta-theme-color");
  if (metaColor) metaColor.content = isDark ? "#0F172A" : "#F7F5F0";
  
  $("btnThemeToggle").textContent = isDark ? "🌙" : "☀️";
  const dict = i18n[currentLang];
  $("lblCurrentTheme").textContent = isDark ? dict.theme_dark_name : dict.theme_light_name;
}

function toggleTheme() {
  currentTheme = currentTheme === "dark" ? "light" : "dark";
  localStorage.setItem("app_theme", currentTheme);
  applyTheme();
  
  const themeInput = document.querySelector(`input[name="theme"][value="${currentTheme}"]`);
  if (themeInput) themeInput.checked = true;
}

$("btnThemeToggle").addEventListener("click", toggleTheme);

// ── Modals Setup ──────────────────────────────────────────────────────────────
function setupModal(modalId, triggerId, valueChangeCallback, nameAttr) {
  const modal = $(modalId);
  const trigger = $(triggerId);
  if (!modal || !trigger) return;
  
  trigger.addEventListener("click", () => modal.classList.add("open"));
  
  modal.addEventListener("click", e => {
    if (e.target === modal) modal.classList.remove("open");
  });
  
  modal.querySelectorAll(`input[name="${nameAttr}"]`).forEach(input => {
    input.addEventListener("change", (e) => {
      valueChangeCallback(e.target.value);
      setTimeout(() => modal.classList.remove("open"), 150);
    });
  });
}

setupModal("langModal", "btnLangSettings", (val) => {
  currentLang = val;
  localStorage.setItem("app_lang", val);
  applyTranslations();
  loadSummary();
  loadInventory();
  loadOrders();
}, "lang");

setupModal("themeModal", "btnThemeSettings", (val) => {
  currentTheme = val;
  localStorage.setItem("app_theme", val);
  applyTheme();
}, "theme");

// ── State ─────────────────────────────────────────────────────────────────────
let _stocks = [];
let _warehouses = [];
let _orders = [];

// ── Utils ─────────────────────────────────────────────────────────────────────
function fmt(num) {
  if (num === null || num === undefined || num === "—") return "—";
  const n = Math.round(Number(num));
  return n.toLocaleString("ru-RU");
}

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("ru-RU", { day: "2-digit", month: "short" });
}

function toast(msg, type = "") {
  const el = $("toast");
  el.textContent = msg;
  el.className = `toast ${type} show`;
  setTimeout(() => { el.className = "toast"; }, 2800);
}

function productEmoji(title) {
  const t = title.toLowerCase();
  if (t.includes("карточк") || t.includes("карт")) return "🃏";
  if (t.includes("сортер") || t.includes("дерев")) return "🪵";
  if (t.includes("сенсор") || t.includes("тактил")) return "✋";
  if (t.includes("логик") || t.includes("счёт") || t.includes("счет")) return "🔢";
  if (t.includes("живот")) return "🦁";
  return "🧸";
}

function payBadge(status) {
  if (status === "PAID") return `<span class="badge badge-paid">Оплачено</span>`;
  return `<span class="badge badge-unpaid">Ждёт оплаты</span>`;
}

function statusBadge(status) {
  const map = {
    NEW: ["badge-new", "Новый"],
    PACKED: ["badge-packed", "Собран"],
    DELIVERING: ["badge-delivering", "Доставляется"],
    DELIVERED: ["badge-delivered", "Доставлен"],
    CANCELLED: ["badge-unpaid", "Отменён"],
  };
  const [cls, label] = map[status] || ["badge-new", status];
  return `<span class="badge ${cls}">${label}</span>`;
}

function sourceBadge(source) {
  if (source === "website") return `<span class="badge badge-website">Сайт</span>`;
  return "";
}

// ── API ───────────────────────────────────────────────────────────────────────
async function api(path, opts = {}) {
  const r = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${r.status}`);
  }
  return r.json();
}

// ── Load Summary ──────────────────────────────────────────────────────────────
async function loadSummary() {
  try {
    const data = await api("/api/inventory/summary");
    const dict = i18n[currentLang];

    const rev = data.total_revenue || 0;
    const exp = data.total_expenses || 0;
    const profit = rev - exp;
    const cash = profit;

    $("mRevenue").textContent = fmt(rev);
    $("mRevenue").className = "metric-value";

    $("mProfit").textContent = fmt(profit);
    $("mProfit").className = `metric-value ${profit >= 0 ? "positive" : "negative"}`;

    $("mCash").textContent = fmt(cash);
    $("mCash").className = `metric-value ${cash >= 0 ? "positive" : "negative"}`;

    const cap = data.uchtepa_capacity || {};
    const cur = cap.current || 0;
    const lim = cap.limit || 100;
    const pct = Math.round((cur / lim) * 100);
    const free = lim - cur;

    $("capCount").innerHTML = `${cur}<span>/${lim}</span>`;
    $("capText").textContent = `${dict.lbl_uchtepa_pill} ${cur}/${lim}`;
    $("capBar").style.width = `${pct}%`;
    $("capBar").className = `progress-fill ${pct >= 90 ? "danger" : pct >= 70 ? "warning" : ""}`;
    $("capDot").className = `badge-dot ${pct >= 90 ? "red" : pct >= 70 ? "orange" : "green"}`;
    $("capPct").textContent = `${dict.lbl_free} ${free}`;
    $("capStatus").textContent = `${pct}% ${dict.lbl_filled}`;

    _warehouses = data.warehouses || [];
    const container = $("summaryStocks");
    container.innerHTML = "";
    for (const wh of _warehouses) {
      const wCard = document.createElement("div");
      wCard.className = "capacity-card";
      wCard.style.marginBottom = "8px";
      const rows = wh.products.map(p =>
        `<div class="order-item-row">
          <span class="order-item-dot"></span>
          <span class="order-item-name">${p.title}</span>
          <span class="order-item-qty">${p.quantity} ${dict.pcs}</span>
        </div>`
      ).join("");
      wCard.innerHTML = `
        <div class="capacity-title" style="margin-bottom:10px;">${wh.name}</div>
        ${rows}
      `;
      container.appendChild(wCard);
    }
  } catch (e) {
    toast("Ошибка загрузки сводки", "error");
    console.error(e);
  }
}

// ── Load Inventory ────────────────────────────────────────────────────────────
async function loadInventory() {
  try {
    _stocks = await api("/api/inventory/stocks");
    const dict = i18n[currentLang];

    const byProd = {};
    for (const s of _stocks) {
      const pid = s.product.id;
      if (!byProd[pid]) byProd[pid] = { product: s.product, wh: {} };
      byProd[pid].wh[s.warehouse.id] = { qty: s.quantity, wh: s.warehouse };
    }

    const container = $("productList");
    container.innerHTML = "";

    const tfProd = $("tfProduct");
    tfProd.innerHTML = `<option value="" data-i18n="opt_select">${dict.opt_select}</option>`;

    for (const [pid, info] of Object.entries(byProd)) {
      const prod = info.product;
      const emoji = productEmoji(prod.title);
      const whEntries = Object.values(info.wh);

      const chipsHtml = whEntries.map(w =>
        `<span class="stock-chip ${w.wh.capacity_limit ? "office" : "main"}">${w.wh.name.split("(")[1]?.replace(")", "") || w.wh.name.split(" ")[0]}: ${w.qty}</span>`
      ).join("");

      const card = document.createElement("div");
      card.className = "product-card";
      card.dataset.pid = pid;
      card.innerHTML = `
        <div class="product-emoji">${emoji}</div>
        <div class="product-info">
          <div class="product-title">${prod.title}</div>
          <div class="product-sku">${prod.sku}</div>
          <div class="product-stocks">${chipsHtml}</div>
        </div>
        <div>
          <div class="product-price">${fmt(prod.retail_price)}</div>
          <div class="product-price-sub">${dict.currency}</div>
          <button class="btn-move" style="margin-top:6px;" data-pid="${pid}">→ ${dict.lbl_uchtepa_pill}</button>
        </div>
      `;
      container.appendChild(card);

      tfProd.innerHTML += `<option value="${pid}">${prod.title}</option>`;
    }

    const allWh = [...new Map(_stocks.map(s => [s.warehouse.id, s.warehouse])).values()];
    const tfFrom = $("tfFrom");
    const tfTo = $("tfTo");
    tfFrom.innerHTML = allWh.map(w => `<option value="${w.id}">${w.name}</option>`).join("");
    tfTo.innerHTML = allWh.map(w => `<option value="${w.id}">${w.name}</option>`).join("");
    if (allWh.length > 1) tfTo.selectedIndex = 1;

    container.addEventListener("click", e => {
      const btn = e.target.closest(".btn-move");
      if (!btn) return;
      $("tfProduct").value = btn.dataset.pid;
      openTransferModal();
    });

  } catch (e) {
    toast("Ошибка загрузки склада", "error");
    console.error(e);
  }
}

// ── Load Orders ───────────────────────────────────────────────────────────────
const _NEXT_STATUS = {
  NEW: "PACKED",
  PACKED: "DELIVERING",
  DELIVERING: "DELIVERED",
};
const _STATUS_ACTION_LABEL = {
  NEW: "📦 Собрать",
  PACKED: "🚚 В доставку",
  DELIVERING: "✅ Доставлен",
};

async function updateOrderStatus(orderId, statusUpdate) {
  try {
    await api(`/api/orders/${orderId}/status`, {
      method: "PATCH",
      body: JSON.stringify(statusUpdate),
    });
    toast("✓ Статус обновлён", "success");
    loaded.orders = false;
    await loadOrders();
    await loadSummary();
  } catch (e) {
    toast(`✗ ${e.message}`, "error");
  }
}

async function loadOrders() {
  try {
    _orders = await api("/api/orders");
    const dict = i18n[currentLang];
    const container = $("orderList");
    container.innerHTML = "";

    if (!_orders.length) {
      container.innerHTML = `<div class="empty-state"><div class="empty-icon">🛒</div><p>${dict.empty_orders}</p></div>`;
      return;
    }

    for (const ord of _orders) {
      const itemsHtml = ord.items.map(i =>
        `<div class="order-item-row">
          <span class="order-item-dot"></span>
          <span class="order-item-name" id="item-name-${i.product_id}">${productTitle(i.product_id)}</span>
          <span class="order-item-qty">${i.quantity} ${dict.pcs}</span>
        </div>`
      ).join("");

      const cust = ord.customer;
      const contact = cust.instagram_handle || cust.telegram_username
        ? (cust.instagram_handle || "@" + cust.telegram_username)
        : cust.phone || "";

      // Action buttons
      const nextStatus = _NEXT_STATUS[ord.status];
      const nextLabel = _STATUS_ACTION_LABEL[ord.status];
      let actionsHtml = "";

      if (nextStatus) {
        actionsHtml += `<button class="btn-move btn-status" data-oid="${ord.id}" data-next="${nextStatus}">${nextLabel}</button>`;
      }
      if (ord.payment_status !== "PAID" && ord.status !== "CANCELLED") {
        actionsHtml += `<button class="btn-move btn-pay" data-oid="${ord.id}" style="background:var(--green)">💳 Оплачено</button>`;
      }

      const card = document.createElement("div");
      card.className = "order-card";
      card.innerHTML = `
        <div class="order-header">
          <div>
            <div class="order-number">#${String(ord.id).padStart(4,"0")} ${sourceBadge(ord.source)}</div>
            <div class="order-date">${fmtDate(ord.created_at)}</div>
          </div>
          <div class="order-badges">
            ${payBadge(ord.payment_status)}
            ${statusBadge(ord.status)}
          </div>
        </div>
        <div class="order-items">${itemsHtml}</div>
        <div class="divider"></div>
        <div class="order-footer">
          <div class="order-customer">
            <div class="order-customer-name">${cust.full_name}</div>
            ${contact ? `<div class="order-contact">${contact}</div>` : ""}
            ${ord.district ? `<div class="order-district">📍 ${ord.district}</div>` : ""}
          </div>
          <div class="order-total">${fmt(ord.total_amount)}<br><span style="font-size:10px;font-weight:500;color:var(--muted)">${dict.currency}</span></div>
        </div>
        ${actionsHtml ? `<div class="divider"></div><div class="order-actions">${actionsHtml}</div>` : ""}
      `;
      container.appendChild(card);
    }

    // Bind action buttons
    container.querySelectorAll(".btn-status").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        updateOrderStatus(btn.dataset.oid, { status: btn.dataset.next });
      });
    });
    container.querySelectorAll(".btn-pay").forEach(btn => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        updateOrderStatus(btn.dataset.oid, { payment_status: "PAID" });
      });
    });

  } catch (e) {
    toast("Ошибка загрузки заказов", "error");
    console.error(e);
  }
}

// ── Load Leads ────────────────────────────────────────────────────────────────
let _leads = [];
async function loadLeads() {
  try {
    _leads = await api("/api/leads");
    const dict = i18n[currentLang];
    const container = $("leadList");
    container.innerHTML = "";

    if (!_leads.length) {
      container.innerHTML = `<div class="empty-state"><div class="empty-icon">👥</div><p>${dict.empty_leads || 'Нет лидов'}</p></div>`;
      return;
    }

    for (const lead of _leads) {
      const card = document.createElement("div");
      card.className = "order-card"; // Reusing order-card styles
      
      let statusCls = "badge-new";
      let statusLabel = lead.status;
      if (lead.status === "NEW") { statusCls = "badge-new"; statusLabel = "Новый"; }
      if (lead.status === "IN_PROGRESS") { statusCls = "badge-packed"; statusLabel = "В работе"; }
      if (lead.status === "ORDERED") { statusCls = "badge-delivered"; statusLabel = "Заказ оформлен"; }
      if (lead.status === "CANCELLED") { statusCls = "badge-unpaid"; statusLabel = "Отказ"; }

      card.innerHTML = `
        <div class="order-header">
          <div>
            <div class="order-number">${lead.name || 'Без имени'}</div>
            <div class="order-date">${fmtDate(lead.created_at)}</div>
          </div>
          <div class="order-badges">
            <span class="badge ${statusCls}">${statusLabel}</span>
          </div>
        </div>
        <div class="order-items">
          <div class="order-item-row">
            <span class="order-item-dot"></span>
            <span class="order-item-name">${lead.interested_in || 'Не указано'}</span>
          </div>
        </div>
        <div class="divider"></div>
        <div class="order-footer">
          <div class="order-customer">
            <div class="order-contact">${lead.contact || ''}</div>
            ${lead.source ? `<div class="order-district">📍 ${lead.source}</div>` : ""}
          </div>
        </div>
      `;
      container.appendChild(card);
    }
  } catch (e) {
    toast("Ошибка загрузки лидов", "error");
    console.error(e);
  }
}

// Toggle logic
$("btnToggleOrders").addEventListener("click", () => {
  $("btnToggleOrders").classList.add("active");
  $("btnToggleLeads").classList.remove("active");
  $("orderList").style.display = "block";
  $("leadList").style.display = "none";
});

$("btnToggleLeads").addEventListener("click", () => {
  $("btnToggleLeads").classList.add("active");
  $("btnToggleOrders").classList.remove("active");
  $("orderList").style.display = "none";
  $("leadList").style.display = "block";
  loadLeads();
});

function productTitle(pid) {
  const stock = _stocks.find(s => s.product.id === pid);
  if (stock) return stock.product.title;
  return `Товар #${pid}`;
}

// ── Transfer Modal ────────────────────────────────────────────────────────────
function openTransferModal() {
  $("transferModal").classList.add("open");
}

function closeTransferModal() {
  $("transferModal").classList.remove("open");
}

$("btnOpenTransfer").addEventListener("click", openTransferModal);
$("btnCancelTransfer").addEventListener("click", closeTransferModal);
$("transferModal").addEventListener("click", e => {
  if (e.target === $("transferModal")) closeTransferModal();
});

$("btnDoTransfer").addEventListener("click", async () => {
  const btn = $("btnDoTransfer");
  const product_id = parseInt($("tfProduct").value);
  const from_id    = parseInt($("tfFrom").value);
  const to_id      = parseInt($("tfTo").value);
  const qty        = parseInt($("tfQty").value);

  if (!product_id || !qty || qty < 1) { toast("Выберите товар и количество", "warning"); return; }
  if (from_id === to_id) { toast("Выберите разные склады", "warning"); return; }

  btn.disabled = true;

  try {
    const res = await api("/api/inventory/transfer", {
      method: "POST",
      body: JSON.stringify({ product_id, from_warehouse_id: from_id, to_warehouse_id: to_id, quantity: qty }),
    });
    toast(`✓ ${res.message}`, "success");
    closeTransferModal();
    $("tfQty").value = "";
    await loadInventory();
    await loadSummary();
  } catch (e) {
    toast(`✗ ${e.message}`, "error");
  } finally {
    btn.disabled = false;
  }
});

// ── Tab Switching ─────────────────────────────────────────────────────────────
let loaded = { summary: false, inventory: false, orders: false, settings: false };

document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const tab = btn.dataset.tab;
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`page-${tab}`).classList.add("active");

    if (!loaded[tab]) {
      loaded[tab] = true;
      if (tab === "summary")   loadSummary();
      if (tab === "inventory") loadInventory();
      if (tab === "orders")    loadOrders();
    }
  });
});

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  applyTheme();
  applyTranslations();
  await Promise.all([loadSummary(), loadInventory()]);
  loaded.summary = true;
  loaded.inventory = true;
}

init();
