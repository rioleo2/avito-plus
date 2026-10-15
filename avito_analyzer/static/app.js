// Инициализация иконок Lucide
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) lucide.createIcons();
  restoreSettings();
  renderHistory();
  document.getElementById("query").focus();
});

const PER_PAGE = 10;
let ALL_LISTINGS = [];
let currentPage = 1;

// Текст из Авито вставляем в innerHTML — экранируем, чтобы объявление не могло внедрить разметку
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function setSeller(type) {
  document.getElementById("seller_type").value = type;
  document.querySelectorAll(".seller-btn").forEach(btn => {
    btn.classList.remove("active", "bg-neutral-900", "text-white");
    btn.classList.add("text-neutral-600");
  });
  event.target.classList.add("active", "bg-neutral-900", "text-white");
  event.target.classList.remove("text-neutral-600");
}

function toggleFilters() {
  document.getElementById("filtersPanel").classList.toggle("hidden");
  document.getElementById("filtersArrow").classList.toggle("rotate-180");
}

function formatRub(num) {
  return (num || 0).toLocaleString("ru-RU") + " ₽";
}

function setLoader(stage, pct) {
  document.getElementById("loaderStage").innerText = stage;
  document.getElementById("loaderPct").innerText = pct + "%";
  document.getElementById("loaderBar").style.width = pct + "%";
}

function showError(msg) {
  const box = document.getElementById("errorBox");
  box.innerText = msg;
  box.classList.toggle("hidden", !msg);
}

const sleep = ms => new Promise(r => setTimeout(r, ms));
let currentJobId = null;

async function cancelAnalysis() {
  const id = currentJobId;
  currentJobId = null;
  if (id) {
    try { await fetch(`/api/jobs/${id}/cancel`, { method: "POST" }); } catch (e) { /* сервер мог уже завершить задачу */ }
  }
  document.getElementById("loader").classList.add("hidden");
  const btn = document.getElementById("submitBtn");
  btn.disabled = false;
  btn.classList.remove("opacity-50");
}

// ----- Запоминание настроек и история запросов (localStorage может быть недоступен) -----

const SETTINGS_KEY = "avito_analyzer_settings";
const HISTORY_KEY = "avito_analyzer_history";
const SETTING_FIELDS = ["city", "pages", "verify_top", "price_from", "price_to", "seller_type", "words_in_desc", "exclude_words"];

function lsGet(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch (e) { return fallback; }
}
function lsSet(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* не страшно */ }
}

function saveSettings() {
  const st = {};
  SETTING_FIELDS.forEach(id => { st[id] = document.getElementById(id).value; });
  st.delivery = document.getElementById("delivery").checked;
  lsSet(SETTINGS_KEY, st);
}

function restoreSettings() {
  const st = lsGet(SETTINGS_KEY, null);
  if (!st) return;
  SETTING_FIELDS.forEach(id => { if (st[id] !== undefined && st[id] !== null) document.getElementById(id).value = st[id]; });
  document.getElementById("delivery").checked = !!st.delivery;
  // подсветка выбранного типа продавца
  const map = { all: 0, private: 1, company: 2 };
  const btns = document.querySelectorAll(".seller-btn");
  if (btns.length && st.seller_type in map) {
    btns.forEach(b => { b.classList.remove("active", "bg-neutral-900", "text-white"); b.classList.add("text-neutral-600"); });
    const b = btns[map[st.seller_type]];
    b.classList.add("active", "bg-neutral-900", "text-white");
    b.classList.remove("text-neutral-600");
  }
}

function pushHistory(query, city) {
  let h = lsGet(HISTORY_KEY, []).filter(x => !(x.query.toLowerCase() === query.toLowerCase() && x.city === city));
  h.unshift({ query, city });
  lsSet(HISTORY_KEY, h.slice(0, 8));
  renderHistory();
}

function renderHistory() {
  const h = lsGet(HISTORY_KEY, []);
  const box = document.getElementById("historyBox");
  const chips = document.getElementById("historyChips");
  chips.innerHTML = "";
  h.forEach(x => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "px-2 py-0.5 rounded-full border border-neutral-200 bg-white text-neutral-700 hover:border-neutral-400";
    b.innerText = `${x.query} · ${x.city}`;
    b.onclick = () => {
      document.getElementById("query").value = x.query;
      document.getElementById("city").value = x.city;
      startAnalysis();
    };
    chips.appendChild(b);
  });
  box.classList.toggle("hidden", h.length === 0);
  box.classList.toggle("flex", h.length > 0);
}

function clearHistory() {
  lsSet(HISTORY_KEY, []);
  renderHistory();
}

// Запуск анализа: создаём задачу и опрашиваем прогресс
async function startAnalysis() {
  const query = document.getElementById("query").value.trim();
  if (!query) return;
  if (document.getElementById("submitBtn").disabled) return; // анализ уже идёт

  const payload = {
    query,
    city: document.getElementById("city").value.trim() || "Москва",
    price_from: parseInt(document.getElementById("price_from").value) || null,
    price_to: parseInt(document.getElementById("price_to").value) || null,
    seller_type: document.getElementById("seller_type").value,
    contact_type: "all",
    delivery: document.getElementById("delivery").checked,
    words_in_description: document.getElementById("words_in_desc").value || null,
    exclude_words: document.getElementById("exclude_words").value || null,
    use_cache: !document.getElementById("fresh").checked,
    pages: parseInt(document.getElementById("pages").value) || 3,
    verify_top: parseInt(document.getElementById("verify_top").value)
  };
  if (Number.isNaN(payload.verify_top)) payload.verify_top = 12;

  saveSettings();
  const results = document.getElementById("resultsSection");
  const submitBtn = document.getElementById("submitBtn");
  showError("");
  results.classList.add("hidden");
  document.getElementById("loader").classList.remove("hidden");
  setLoader("Отправляю запрос…", 0);
  submitBtn.disabled = true;
  submitBtn.classList.add("opacity-50");

  let superseded = false; // этот цикл опроса уже не актуален (задачу отменили)
  try {
    const start = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!start.ok) throw new Error(`Ошибка сервера: ${start.status}`);
    const { job_id } = await start.json();
    currentJobId = job_id;

    while (true) {
      await sleep(1200);
      if (currentJobId !== job_id) { superseded = true; return; } // отменили
      const r = await fetch(`/api/jobs/${job_id}`);
      if (!r.ok) throw new Error(`Ошибка сервера: ${r.status}`);
      const job = await r.json();
      setLoader(job.stage, job.progress);
      if (job.state === "done") {
        pushHistory(query, payload.city);
        renderResults(job.result);
        break;
      }
      if (job.state === "cancelled") { superseded = true; return; }
      if (job.state === "error") throw new Error(job.error || "Неизвестная ошибка");
    }
  } catch (err) {
    showError(err.message);
    console.error(err);
  } finally {
    if (!superseded) {
      document.getElementById("loader").classList.add("hidden");
      submitBtn.disabled = false;
      submitBtn.classList.remove("opacity-50");
    }
  }
}

function renderResults(data) {
  const results = document.getElementById("resultsSection");
  results.classList.remove("hidden");
  ALL_LISTINGS = data.listings;
  currentPage = 1;

  renderPriceRangeLine(data.stats);

  // Сводка запуска
  const parts = [
    `Собрано ${data.scraped_total} объявлений (${data.pages_scraped} стр.)`,
    `рынок посчитан по ${data.stats.total_listings} подходящим`,
    data.verified_count ? `цена сверена на странице у ${data.verified_count}` : "цены на странице не сверялись",
    data.llm_used ? "ИИ проанализировал топ" : "без ИИ"
  ];
  document.getElementById("runSummary").innerText = parts.join(" · ");

  const wb = document.getElementById("warningsBox");
  wb.innerHTML = data.warnings.map(w => `<div>⚠ ${esc(w)}</div>`).join("");
  wb.classList.toggle("hidden", data.warnings.length === 0);

  // Лучшие предложения
  const byId = Object.fromEntries(data.listings.map(i => [i.id, i]));
  const best = data.best_deals.map(id => byId[id]).filter(Boolean);
  const bestContainer = document.getElementById("bestContainer");
  bestContainer.innerHTML = "";
  if (best.length) {
    best.forEach((item, idx) => bestContainer.appendChild(buildCard(item, idx + 1)));
  } else {
    bestContainer.innerHTML = `<div class="apple-card rounded-xl p-4 text-xs text-neutral-500">Ничего заметно дешевле рынка не нашлось. Попробуйте уточнить запрос или собрать больше страниц.</div>`;
  }

  renderListPage();
  if (window.lucide) lucide.createIcons();
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderPriceRangeLine(stats) {
  const minP = stats.min_price || 0;
  const maxP = stats.max_price || 0;
  const p25 = stats.p25_price || minP;
  const p75 = stats.p75_price || maxP;
  const median = stats.median_price || Math.round((minP + maxP) / 2);

  document.getElementById("scaleMin").innerText = formatRub(minP);
  document.getElementById("scaleMax").innerText = formatRub(maxP);
  document.getElementById("scaleAcceptable").innerText = `${formatRub(p25)} – ${formatRub(p75)}`;
  document.getElementById("rangeSummary").innerText = `Медиана: ${formatRub(median)}`;

  const spread = maxP - minP;
  const bar = document.getElementById("priceRangeBar");
  const pin = document.getElementById("medianMarker");
  if (spread <= 0) {
    bar.style.left = "0%";
    bar.style.width = "100%";
    pin.style.left = "50%";
  } else {
    const leftPct = Math.max(0, Math.min(100, ((p25 - minP) / spread) * 100));
    const rightPct = Math.max(0, Math.min(100, ((p75 - minP) / spread) * 100));
    const medianPct = Math.max(0, Math.min(100, ((median - minP) / spread) * 100));
    bar.style.left = `${leftPct.toFixed(1)}%`;
    bar.style.width = `${Math.max(8, rightPct - leftPct).toFixed(1)}%`;
    pin.style.left = `${medianPct.toFixed(1)}%`;
  }
}

// ----- Список с сортировкой и страницами -----

function visibleListings() {
  const hide = document.getElementById("hideBad").checked;
  let items = ALL_LISTINGS.filter(i => !hide || (i.relevant && !i.unavailable && (i.ai_analysis?.is_target ?? true)));
  const sort = document.getElementById("sortSelect").value;
  if (sort === "price_asc") items = [...items].sort((a, b) => a.price - b.price);
  else if (sort === "price_desc") items = [...items].sort((a, b) => b.price - a.price);
  return items; // по умолчанию сервер уже отсортировал по выгоде
}

function changeSort() {
  currentPage = 1;
  renderListPage();
}

function goPage(p) {
  currentPage = p;
  renderListPage();
  document.getElementById("listingsContainer").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderListPage() {
  const items = visibleListings();
  const totalPages = Math.max(1, Math.ceil(items.length / PER_PAGE));
  currentPage = Math.min(currentPage, totalPages);
  document.getElementById("listingsCount").innerText = `${items.length} лотов`;

  const container = document.getElementById("listingsContainer");
  container.innerHTML = "";
  items.slice((currentPage - 1) * PER_PAGE, currentPage * PER_PAGE).forEach(it => container.appendChild(buildCard(it)));

  const pager = document.getElementById("pager");
  pager.innerHTML = "";
  if (totalPages > 1) {
    for (let p = 1; p <= totalPages; p++) {
      const b = document.createElement("button");
      b.innerText = p;
      b.className = "w-8 h-8 text-xs rounded-lg border " + (p === currentPage
        ? "bg-neutral-900 text-white border-neutral-900"
        : "bg-white text-neutral-700 border-neutral-200 hover:border-neutral-400");
      b.onclick = () => goPage(p);
      pager.appendChild(b);
    }
  }
  if (window.lucide) lucide.createIcons();
}

// ----- Карточка объявления -----

function verdictBadge(item) {
  const ai = item.ai_analysis || {};
  const v = ai.verdict || "";
  let cls = "bg-neutral-100 text-neutral-700 border-neutral-200";
  if (v.includes("Топ") || v.includes("Хорошая")) cls = "bg-emerald-50 text-emerald-700 border-emerald-200";
  else if (v.includes("🚨") || v.includes("риск") || v.includes("🚫") || v.includes("🧩")) cls = "bg-red-50 text-red-700 border-red-200";
  else if (v.includes("Дороже")) cls = "bg-amber-50 text-amber-700 border-amber-200";
  return `<span class="px-2 py-0.5 rounded-md text-xs font-medium border ${cls}">${esc(v)} • ${ai.deal_rating ?? "?"}/10</span>`;
}

function priceCheckBadge(item) {
  if (item.unavailable) return `<span class="text-[11px] text-red-600">Снято с публикации</span>`;
  if (item.price_verified === true) return `<span class="text-[11px] text-emerald-600 flex items-center gap-1">✓ цена сверена на странице</span>`;
  if (item.price_verified === false) return `<span class="text-[11px] text-amber-600">⚠ ${esc(item.price_note)}</span>`;
  return `<span class="text-[11px] text-neutral-400">цена из выдачи, не сверена</span>`;
}

function discountText(item) {
  if (item.discount_pct === null || item.discount_pct === undefined) return "";
  const d = item.discount_pct;
  if (d >= 3) return `<span class="text-emerald-700 font-medium">−${d.toFixed(0)}% к рынку</span>`;
  if (d <= -3) return `<span class="text-amber-700">+${Math.abs(d).toFixed(0)}% к рынку</span>`;
  return `<span class="text-neutral-500">на уровне рынка</span>`;
}

function photoBlock(item) {
  const imgs = (item.images && item.images.length ? item.images : (item.image_url ? [item.image_url] : [])).slice(0, 5);
  if (!imgs.length) {
    return `<div class="w-28 h-28 sm:w-36 sm:h-36 shrink-0 rounded-lg bg-neutral-100 flex items-center justify-center text-[11px] text-neutral-400">нет фото</div>`;
  }
  const thumbs = imgs.slice(1).map(u =>
    `<img src="${esc(u)}" loading="lazy" referrerpolicy="no-referrer" onclick="swapPhoto(this)" class="w-7 h-7 object-cover rounded cursor-pointer border border-neutral-200">`
  ).join("");
  return `
    <div class="shrink-0 space-y-1.5">
      <img src="${esc(imgs[0])}" loading="lazy" referrerpolicy="no-referrer" class="main-photo w-28 h-28 sm:w-36 sm:h-36 object-cover rounded-lg bg-neutral-100">
      ${thumbs ? `<div class="flex gap-1">${thumbs}</div>` : ""}
    </div>`;
}

// Клик по миниатюре меняет местами её и главное фото
function swapPhoto(thumb) {
  const main = thumb.closest("div.shrink-0").querySelector(".main-photo");
  const tmp = main.src;
  main.src = thumb.src;
  thumb.src = tmp;
}

function listHtml(arr, cls) {
  return (arr || []).slice(0, 3).map(x => `<li class="${cls}">${esc(x)}</li>`).join("");
}

function buildCard(item, place) {
  const ai = item.ai_analysis || {};
  const card = document.createElement("div");
  const dim = item.unavailable || !item.relevant ? "opacity-60" : "";
  const ring = place === 1 ? "ring-2 ring-emerald-500/60" : "";
  card.className = `apple-card rounded-xl p-4 sm:p-5 hover:border-neutral-300 transition ${dim} ${ring}`;

  const specs = Object.entries(ai.extracted_specs || {}).filter(([, v]) => v)
    .map(([k, v]) => `<span class="px-1.5 py-0.5 rounded bg-neutral-100 text-[11px] text-neutral-600">${esc(k)}: ${esc(v)}</span>`).join(" ");

  card.innerHTML = `
    <div class="flex gap-4">
      ${photoBlock(item)}
      <div class="flex-1 min-w-0 space-y-2">
        <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
          <h3 class="text-base font-semibold text-neutral-900 leading-snug">
            ${place ? `<span class="text-emerald-600 mr-1">#${place}</span>` : ""}
            <a href="${esc(item.url)}" target="_blank" rel="noopener noreferrer" class="hover:underline">${esc(item.title)}</a>
          </h3>
          <div class="sm:text-right shrink-0">
            <div class="text-lg font-bold text-neutral-900 tracking-tight">${formatRub(item.price)}</div>
            <div class="text-xs">${discountText(item)}</div>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-x-3 gap-y-1">
          ${verdictBadge(item)}
          ${priceCheckBadge(item)}
        </div>

        <div class="text-xs text-neutral-500 flex flex-wrap items-center gap-x-3 gap-y-1">
          <span>${esc(item.location || "")}</span>
          ${item.date_posted ? `<span>· ${esc(item.date_posted)}</span>` : ""}
          ${item.seller ? `<span>· ${esc(item.seller)}</span>` : ""}
          ${item.badge ? `<span class="text-neutral-400">· Авито: ${esc(item.badge)}</span>` : ""}
        </div>

        ${specs ? `<div class="flex flex-wrap gap-1">${specs}</div>` : ""}

        ${ai.summary && ai.source === "llm" ? `<p class="text-xs text-neutral-700">${esc(ai.summary)}</p>` : ""}
        <ul class="text-xs space-y-0.5 list-none">
          ${listHtml(ai.why_good, "text-emerald-700 before:content-['+_']")}
          ${listHtml(ai.risks_and_defects, "text-amber-700 before:content-['−_']")}
        </ul>

        <p class="text-xs text-neutral-500 leading-relaxed line-clamp-2">${esc(item.full_description || item.description_snippet || "")}</p>

        <a href="${esc(item.url)}" target="_blank" rel="noopener noreferrer"
           class="inline-flex items-center gap-1 text-xs font-medium text-neutral-800 hover:text-black hover:underline">
          Перейти к объявлению <i data-lucide="arrow-up-right" class="w-3.5 h-3.5"></i>
        </a>
      </div>
    </div>`;
  return card;
}
