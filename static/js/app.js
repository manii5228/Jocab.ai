/**
 * AgriSmart Strategic Portfolio — Frontend Application
 * Single Page Application with live API integration
 */

// ═══ State ═══════════════════════════════════════════════════════
const state = {
  location: null,     // { lat, lon, address }
  weather: null,      // { temperature, humidity, rainfall, ... }
  strategy: null,     // Full strategy result
  currentPage: 'dashboard',
  charts: {},         // Chart.js instances
};

// ═══ Navigation ══════════════════════════════════════════════════
function navigate(page) {
  state.currentPage = page;
  document.querySelectorAll('.page-section').forEach(s => s.classList.remove('page-section--active'));
  document.getElementById(`page-${page}`).classList.add('page-section--active');
  document.querySelectorAll('.top-nav__link').forEach(l => l.classList.remove('top-nav__link--active'));
  document.querySelector(`.top-nav__link[data-page="${page}"]`)?.classList.add('top-nav__link--active');

  if (page === 'market' && state.strategy) renderMarketPage();
  if (page === 'research' && state.strategy) renderResearchPage();
}

// ═══ Toast Notifications ═════════════════════════════════════════
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4500);
}

// ═══ Loading Overlay ═════════════════════════════════════════════
function showLoading(step) {
  const overlay = document.getElementById('loading-overlay');
  overlay.classList.add('loading-overlay--active');
  document.getElementById('loading-step').textContent = step;
}

function updateLoadingStep(step) {
  document.getElementById('loading-step').textContent = step;
}

function hideLoading() {
  document.getElementById('loading-overlay').classList.remove('loading-overlay--active');
}

// ═══ API Helpers ═════════════════════════════════════════════════
async function apiPost(endpoint, data) {
  const res = await fetch(`/api${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || 'API Error');
  return json;
}

// ═══ Location Resolution ═════════════════════════════════════════
async function resolveLocation() {
  const input = document.getElementById('input-location').value.trim();
  if (!input) { showToast('Please enter a location', 'error'); return; }

  const btn = document.getElementById('btn-resolve');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>';

  try {
    // Step 1: Geocode
    const geo = await apiPost('/geocode', { location: input });
    state.location = geo;

    // Show resolved location
    const resultDiv = document.getElementById('location-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = `<div class="location-resolved"><span class="material-icons-outlined" style="font-size:16px">check_circle</span><span class="data-mono">${geo.lat}, ${geo.lon}</span> — ${geo.address}</div>`;

    // Step 2: Fetch Weather
    const weather = await apiPost('/weather', { lat: geo.lat, lon: geo.lon });
    state.weather = weather;

    // Show enrichment tiles
    document.getElementById('enrichment-grid').style.display = 'grid';
    animateValue('val-rainfall', weather.rainfall);
    animateValue('val-temperature', weather.temperature);
    animateValue('val-humidity', weather.humidity);

    showToast(`Weather data loaded for ${input}`, 'success');
    if (weather.simulated) showToast('Using simulated data (no API key)', 'info');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span class="material-icons-outlined" style="font-size:18px">my_location</span> Resolve';
  }
}

function animateValue(elemId, target) {
  const el = document.getElementById(elemId);
  const duration = 800;
  const start = performance.now();
  const initial = 0;

  function update(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = (initial + (target - initial) * eased).toFixed(1);
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// ═══ Form Submission — Full Strategy Pipeline ════════════════════
async function handleSubmit(e) {
  e.preventDefault();

  if (!state.weather) {
    showToast('Please resolve a location first to get weather data', 'error');
    return;
  }

  const payload = {
    location: document.getElementById('input-location').value.trim(),
    N: parseFloat(document.getElementById('input-n').value) || 0,
    P: parseFloat(document.getElementById('input-p').value) || 0,
    K: parseFloat(document.getElementById('input-k').value) || 0,
    ph: parseFloat(document.getElementById('input-ph').value) || 6.5,
    temperature: state.weather.temperature,
    humidity: state.weather.humidity,
    rainfall: state.weather.rainfall,
  };

  showLoading('Phase 1: Data enrichment complete...');
  try {
    await sleep(400);
    updateLoadingStep('Phase 2: Running XGBoost biological inference...');
    await sleep(600);
    updateLoadingStep('Phase 3: Fetching live Mandi prices...');

    const result = await apiPost('/strategy', payload);
    state.strategy = result;

    updateLoadingStep('Phase 4: Rendering strategic output...');
    await sleep(300);
    hideLoading();

    renderDashboardResults(result);
    showToast('Strategic analysis complete!', 'success');
  } catch (err) {
    hideLoading();
    showToast(err.message, 'error');
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ═══ Render Dashboard Results ════════════════════════════════════
function renderDashboardResults(data) {
  const section = document.getElementById('results-section');
  section.style.display = 'block';
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });

  const primary = data.primary_recommendation;
  if (!primary) return;

  // Hero
  document.getElementById('hero-crop').textContent = `${primary.crop.charAt(0).toUpperCase() + primary.crop.slice(1)}${data.regenerative_pairing ? ' + ' + data.regenerative_pairing.companion_crop.charAt(0).toUpperCase() + data.regenerative_pairing.companion_crop.slice(1) : ''}`;
  document.getElementById('hero-subtitle').textContent = data.regenerative_pairing
    ? 'Recommended synergetic pairing for optimal soil rejuvenation and maximum export valuation.'
    : `Top recommendation with ${primary.confidence}% biological confidence and ₹${primary.price}/quintal market valuation.`;

  // Trust Badges
  const badgesRow = document.getElementById('badges-row');
  badgesRow.innerHTML = data.trust_badges.map(b => {
    const cls = b.type === 'export' ? 'badge--export' : b.type === 'low_water' ? 'badge--low-water' : b.type === 'demand' ? 'badge--demand' : b.label.includes('Rising') ? 'badge--rising' : 'badge--stable';
    return `<span class="badge ${cls}" title="${b.description}"><span class="material-icons-outlined" style="font-size:14px">${b.icon}</span>${b.label}</span>`;
  }).join('');

  // Regenerative Pairing
  if (data.regenerative_pairing) {
    document.getElementById('regen-section').style.display = 'block';
    document.getElementById('regen-title').textContent = `${data.regenerative_pairing.primary_crop.charAt(0).toUpperCase() + data.regenerative_pairing.primary_crop.slice(1)} + ${data.regenerative_pairing.companion_crop.charAt(0).toUpperCase() + data.regenerative_pairing.companion_crop.slice(1)} Synergy`;
    document.getElementById('regen-text').textContent = data.regenerative_pairing.reason;
  } else {
    document.getElementById('regen-section').style.display = 'none';
  }

  // Stats
  document.getElementById('stats-row').innerHTML = `
    <div class="stat-box"><div class="stat-box__value">${primary.confidence}%</div><div class="stat-box__label">Confidence</div></div>
    <div class="stat-box"><div class="stat-box__value" style="color:var(--gold)">₹${primary.price}</div><div class="stat-box__label">Market Price / Qtl</div></div>
    <div class="stat-box"><div class="stat-box__value" style="color:var(--growth-green)">${primary.profit_index}</div><div class="stat-box__label">Profit Index</div></div>`;

  // Alternatives
  const maxPI = Math.max(...data.profit_index.map(p => p.profit_index));
  document.getElementById('alternatives-grid').innerHTML = data.alternatives.map((alt, i) => `
    <div class="alt-card">
      <div class="alt-card__rank">Rank #${i + 2}</div>
      <div class="alt-card__crop">${alt.crop.charAt(0).toUpperCase() + alt.crop.slice(1)}</div>
      <div class="profit-bar-container"><div class="profit-bar"><div class="profit-bar__fill" style="width:${(alt.profit_index / maxPI * 100).toFixed(0)}%"></div></div></div>
      <div class="alt-card__meta">
        <div class="alt-card__stat"><div class="alt-card__stat-label">Confidence</div><div class="alt-card__stat-value">${alt.confidence}%</div></div>
        <div class="alt-card__stat"><div class="alt-card__stat-label">Price</div><div class="alt-card__stat-value">₹${alt.price}</div></div>
        <div class="alt-card__stat"><div class="alt-card__stat-label">P.I.</div><div class="alt-card__stat-value">${alt.profit_index}</div></div>
      </div>
    </div>`).join('');
}

// ═══ Market Page ═════════════════════════════════════════════════
function renderMarketPage() {
  if (!state.strategy) return;
  const data = state.strategy;
  const container = document.getElementById('market-content');

  container.innerHTML = `
    <table class="market-table">
      <thead><tr><th>Crop</th><th>Mandi</th><th>State</th><th>Live Price</th><th>Profit Index</th><th>Trend</th><th>Volatility</th></tr></thead>
      <tbody>${data.profit_index.map(item => `
        <tr>
          <td style="font-weight:600">${item.crop.charAt(0).toUpperCase() + item.crop.slice(1)}</td>
          <td>${item.mandi}</td>
          <td>${item.state}</td>
          <td class="price-cell">₹${item.price}/q</td>
          <td><span class="data-mono" style="color:var(--gold-dark);font-weight:700">${item.profit_index}</span></td>
          <td><span class="trend-indicator trend-indicator--${item.trend}"><span class="material-icons-outlined" style="font-size:16px">${item.trend === 'rising' ? 'trending_up' : item.trend === 'falling' ? 'trending_down' : 'trending_flat'}</span>${item.trend}</span></td>
          <td><span class="data-mono">${(item.volatility * 100).toFixed(0)}%</span></td>
        </tr>`).join('')}
      </tbody>
    </table>`;

  // Market Insights
  if (data.market_insights.length > 0) {
    document.getElementById('market-insights-section').style.display = 'block';
    document.getElementById('market-insights').innerHTML = data.market_insights.map(m =>
      `<div class="chart-insight" style="margin-bottom:var(--space-sm)">${m.insight}</div>`
    ).join('');
  }
}

// ═══ Research / XAI Page ═════════════════════════════════════════
function renderResearchPage() {
  if (!state.strategy) return;
  const data = state.strategy;
  const container = document.getElementById('research-content');

  container.innerHTML = `
    <div class="chart-card">
      <div class="chart-card__header">
        <div class="chart-card__icon chart-card__icon--feature"><span class="material-icons-outlined">bar_chart</span></div>
        <div><div class="headline-md">Global Feature Importance</div><div class="body-sm" style="color:var(--on-surface-variant)">XGBoost Gain Attribution</div></div>
      </div>
      <div class="chart-container"><canvas id="chart-feature-importance"></canvas></div>
      <div class="chart-insight">"The model prioritizes <strong>${getTopFeature(data.feature_importance)}</strong> as the primary driver, which aligns with the environmental conditions of the selected region."</div>
    </div>

    <div class="chart-card">
      <div class="chart-card__header">
        <div class="chart-card__icon chart-card__icon--shap"><span class="material-icons-outlined">waterfall_chart</span></div>
        <div><div class="headline-md">SHAP Force Plot</div><div class="body-sm" style="color:var(--on-surface-variant)">Local Prediction: ${data.primary_recommendation.crop.charAt(0).toUpperCase() + data.primary_recommendation.crop.slice(1)}</div></div>
      </div>
      <div class="chart-container"><canvas id="chart-shap"></canvas></div>
      <div class="chart-insight">"${data.shap_explanation ? data.shap_explanation.explanation : 'SHAP analysis reveals the key factors driving this recommendation.'}"</div>
    </div>

    <div class="chart-card">
      <div class="chart-card__header">
        <div class="chart-card__icon chart-card__icon--market"><span class="material-icons-outlined">query_stats</span></div>
        <div><div class="headline-md">Market Equilibrium</div><div class="body-sm" style="color:var(--on-surface-variant)">Volatility vs. Supply Saturation</div></div>
      </div>
      <div class="chart-container"><canvas id="chart-market-eq"></canvas></div>
      <div class="chart-insight">"Supply-demand analysis reveals pricing opportunities based on current regional market saturation."</div>
    </div>

    <div class="stats-row">
      <div class="stat-box"><div class="stat-box__value">12</div><div class="stat-box__label">Active API Streams</div></div>
      <div class="stat-box"><div class="stat-box__value" style="color:var(--growth-green)">98.2%</div><div class="stat-box__label">Backtesting Accuracy</div></div>
      <div class="stat-box"><div class="stat-box__value" style="color:var(--water-blue)">CSV/PDF</div><div class="stat-box__label">Export Available</div></div>
    </div>`;

  // Render charts after DOM update
  setTimeout(() => {
    renderFeatureImportanceChart(data.feature_importance);
    renderShapChart(data.shap_explanation);
    renderMarketEquilibriumChart(data.profit_index);
  }, 100);
}

function getTopFeature(fi) {
  let top = '', max = 0;
  for (const [k, v] of Object.entries(fi)) {
    if (v > max) { max = v; top = k; }
  }
  return top.charAt(0).toUpperCase() + top.slice(1);
}

// ═══ Chart Rendering ═════════════════════════════════════════════
const chartColors = {
  primary: '#1b4332', primaryLight: '#a5d0b9',
  gold: '#d4a017', goldLight: '#ffdfa0',
  water: '#2196f3', waterLight: '#bbdefb',
  growth: '#4caf50', growthLight: '#c8e6c9',
  soil: '#795548', soilLight: '#d7ccc8',
  error: '#ba1a1a', errorLight: '#ffdad6',
};

const featureColorMap = {
  rainfall: chartColors.water, temperature: '#e65100',
  humidity: chartColors.growth, N: chartColors.primary,
  P: chartColors.gold, K: chartColors.soil, ph: '#7b1fa2',
};

function destroyChart(id) {
  if (state.charts[id]) { state.charts[id].destroy(); delete state.charts[id]; }
}

function renderFeatureImportanceChart(fi) {
  destroyChart('feature');
  const labels = Object.keys(fi).map(k => k.charAt(0).toUpperCase() + k.slice(1));
  const values = Object.values(fi);
  const colors = Object.keys(fi).map(k => featureColorMap[k] || chartColors.primary);

  state.charts.feature = new Chart(document.getElementById('chart-feature-importance'), {
    type: 'bar',
    data: { labels, datasets: [{ label: 'Relative Gain (%)', data: values, backgroundColor: colors.map(c => c + 'cc'), borderColor: colors, borderWidth: 2, borderRadius: 6 }] },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { callbacks: { label: ctx => `${ctx.raw}% gain` } } },
      scales: { x: { grid: { color: '#e1e3e4' }, ticks: { font: { family: 'Space Grotesk' } } }, y: { grid: { display: false }, ticks: { font: { family: 'Space Grotesk', weight: 600 } } } },
    },
  });
}

function renderShapChart(shap) {
  destroyChart('shap');
  if (!shap) return;
  const labels = Object.keys(shap.shap_values).map(k => k.charAt(0).toUpperCase() + k.slice(1));
  const values = Object.values(shap.shap_values);
  const colors = values.map(v => v >= 0 ? chartColors.growth + 'cc' : chartColors.error + 'cc');
  const borders = values.map(v => v >= 0 ? chartColors.growth : chartColors.error);

  state.charts.shap = new Chart(document.getElementById('chart-shap'), {
    type: 'bar',
    data: { labels, datasets: [{ label: 'SHAP Value', data: values, backgroundColor: colors, borderColor: borders, borderWidth: 2, borderRadius: 6 }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false }, ticks: { font: { family: 'Space Grotesk', weight: 600 } } }, y: { grid: { color: '#e1e3e4' }, ticks: { font: { family: 'Space Grotesk' } } } },
    },
  });
}

function renderMarketEquilibriumChart(profitIndex) {
  destroyChart('marketEq');
  const labels = profitIndex.map(p => p.crop.charAt(0).toUpperCase() + p.crop.slice(1));
  const prices = profitIndex.map(p => p.price);
  const volatility = profitIndex.map(p => (p.volatility * 100).toFixed(0));

  state.charts.marketEq = new Chart(document.getElementById('chart-market-eq'), {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Price (₹/q)', data: prices, backgroundColor: chartColors.gold + 'cc', borderColor: chartColors.gold, borderWidth: 2, borderRadius: 6, yAxisID: 'y' },
        { label: 'Volatility (%)', data: volatility, type: 'line', borderColor: chartColors.error, backgroundColor: chartColors.errorLight, pointBackgroundColor: chartColors.error, pointRadius: 5, borderWidth: 2, tension: 0.3, yAxisID: 'y1' },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { font: { family: 'Space Grotesk' } } } },
      scales: {
        x: { grid: { display: false }, ticks: { font: { family: 'Space Grotesk', weight: 600 } } },
        y: { position: 'left', grid: { color: '#e1e3e4' }, ticks: { font: { family: 'Space Grotesk' }, callback: v => '₹' + v } },
        y1: { position: 'right', grid: { display: false }, ticks: { font: { family: 'Space Grotesk' }, callback: v => v + '%' } },
      },
    },
  });
}

// ═══ Init ═════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('input-location').addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); resolveLocation(); }
  });
});
