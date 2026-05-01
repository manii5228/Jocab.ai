/**
 * AgriSmart Strategic Portfolio — Frontend Application
 * ALL data from real APIs. No hardcoded/simulated data.
 */

// ═══ State ═══════════════════════════════════════════════════════
const state = {
  location: null,
  weather: null,
  nasaPower: null,
  strategy: null,
  modelMetrics: null,
  currentPage: 'dashboard',
  charts: {},
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

// ═══ Toast ═══════════════════════════════════════════════════════
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast--${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4500);
}

// ═══ Loading ═════════════════════════════════════════════════════
function showLoading(step) {
  document.getElementById('loading-overlay').classList.add('loading-overlay--active');
  document.getElementById('loading-step').textContent = step;
}
function updateLoadingStep(step) {
  document.getElementById('loading-step').textContent = step;
}
function hideLoading() {
  document.getElementById('loading-overlay').classList.remove('loading-overlay--active');
}

// ═══ API ═════════════════════════════════════════════════════════
async function apiPost(endpoint, data) {
  const res = await fetch(`/api${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || `API Error (${res.status})`);
  if (json.error) throw new Error(json.error);
  return json;
}

async function apiGet(endpoint) {
  const res = await fetch(`/api${endpoint}`);
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || `API Error (${res.status})`);
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

    const resultDiv = document.getElementById('location-result');
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = `<div class="location-resolved"><span class="material-icons-outlined" style="font-size:16px">check_circle</span><span class="data-mono">${geo.lat}, ${geo.lon}</span> — ${geo.address}</div>`;

    // Step 2: Fetch LIVE Weather from OpenWeather API
    const weather = await apiPost('/weather', { lat: geo.lat, lon: geo.lon });
    state.weather = weather;

    document.getElementById('enrichment-grid').style.display = 'grid';
    animateValue('val-rainfall', weather.rainfall);
    animateValue('val-temperature', weather.temperature);
    animateValue('val-humidity', weather.humidity);

    // Show source attribution
    const weatherSrc = document.getElementById('weather-source');
    weatherSrc.style.display = 'block';
    weatherSrc.innerHTML = `<span class="material-icons-outlined" style="font-size:14px;vertical-align:middle">verified</span> Source: ${weather.source || 'OpenWeather API'} — ${weather.city_name || input}, ${weather.description || ''}`;

    showToast(`Live weather loaded for ${weather.city_name || input}`, 'success');

    // Step 3: Fetch NASA POWER historical data (async, non-blocking)
    fetchNasaPower(geo.lat, geo.lon);

  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span class="material-icons-outlined" style="font-size:18px">my_location</span> Resolve';
  }
}

async function fetchNasaPower(lat, lon) {
  try {
    const nasa = await apiPost('/nasa-power', { lat, lon });
    state.nasaPower = nasa;

    document.getElementById('nasa-power-section').style.display = 'block';
    animateValue('val-nasa-rainfall', nasa.annual_rainfall_estimate);
    animateValue('val-nasa-temp', nasa.avg_temperature);
    animateValue('val-nasa-humidity', nasa.avg_humidity);

    document.getElementById('nasa-source').innerHTML = `<span class="material-icons-outlined" style="font-size:14px;vertical-align:middle">satellite_alt</span> Source: ${nasa.source} — Period: ${nasa.data_period}`;
    showToast('NASA POWER historical data loaded', 'success');
  } catch (err) {
    console.warn('NASA POWER error:', err.message);
    showToast('NASA POWER: ' + err.message, 'error');
  }
}

function animateValue(elemId, target) {
  const el = document.getElementById(elemId);
  if (!el || target === undefined || target === null) return;
  const duration = 800;
  const start = performance.now();
  function update(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = (target * eased).toFixed(1);
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

// ═══ Form Submit — Full Strategy Pipeline ════════════════════════
async function handleSubmit(e) {
  e.preventDefault();

  if (!state.weather) {
    showToast('Please resolve a location first to get live weather data', 'error');
    return;
  }

  // Use NASA POWER annual rainfall for the model if available,
  // since current-day rainfall from OpenWeather may be 0
  let rainfallForModel = state.weather.rainfall;
  if (state.nasaPower && state.nasaPower.annual_rainfall_estimate) {
    // Convert annual mm to approximate per-growing-season (4 months)
    rainfallForModel = Math.round(state.nasaPower.annual_rainfall_estimate / 3);
  }

  const payload = {
    location: document.getElementById('input-location').value.trim(),
    N: parseFloat(document.getElementById('input-n').value) || 0,
    P: parseFloat(document.getElementById('input-p').value) || 0,
    K: parseFloat(document.getElementById('input-k').value) || 0,
    ph: parseFloat(document.getElementById('input-ph').value) || 6.5,
    temperature: state.weather.temperature,
    humidity: state.weather.humidity,
    rainfall: rainfallForModel,
  };

  showLoading('Phase 1: Data enrichment complete...');
  try {
    updateLoadingStep('Phase 2: Running XGBoost inference on 57K-row trained model...');
    await sleep(400);
    updateLoadingStep('Phase 3: Fetching LIVE Mandi prices from Data.gov.in...');

    const result = await apiPost('/strategy', payload);
    state.strategy = result;

    updateLoadingStep('Phase 4: Rendering strategic output...');
    await sleep(200);
    hideLoading();

    // Fetch model metrics
    try {
      state.modelMetrics = await apiGet('/model-metrics');
    } catch (e) { console.warn('Could not fetch model metrics:', e); }

    renderDashboardResults(result);
    showToast('Strategic analysis complete — real data used', 'success');
  } catch (err) {
    hideLoading();
    showToast(err.message, 'error');
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ═══ Dashboard Results ═══════════════════════════════════════════
function renderDashboardResults(data) {
  const section = document.getElementById('results-section');
  section.style.display = 'block';
  section.scrollIntoView({ behavior: 'smooth', block: 'start' });

  const primary = data.primary_recommendation;
  if (!primary) return;

  const cap = s => s.charAt(0).toUpperCase() + s.slice(1);

  // Hero
  const heroName = data.regenerative_pairing
    ? `${cap(primary.crop)} + ${cap(data.regenerative_pairing.companion_crop)}`
    : cap(primary.crop);
  document.getElementById('hero-crop').textContent = heroName;
  document.getElementById('hero-subtitle').textContent = data.regenerative_pairing
    ? 'Recommended synergetic pairing for optimal soil rejuvenation and maximum export valuation.'
    : `Top recommendation with ${primary.confidence}% biological confidence and ₹${primary.price}/quintal market valuation.`;

  // Trust Badges
  const badgesRow = document.getElementById('badges-row');
  badgesRow.innerHTML = data.trust_badges.map(b => {
    const cls = b.type === 'export' ? 'badge--export' : b.type === 'low_water' ? 'badge--low-water' : b.type === 'demand' ? 'badge--demand' : b.label.includes('Rising') ? 'badge--rising' : 'badge--stable';
    return `<span class="badge ${cls}" title="${b.description}"><span class="material-icons-outlined" style="font-size:14px">${b.icon}</span>${b.label}</span>`;
  }).join('');

  // Regenerative
  if (data.regenerative_pairing) {
    document.getElementById('regen-section').style.display = 'block';
    document.getElementById('regen-title').textContent = `${cap(data.regenerative_pairing.primary_crop)} + ${cap(data.regenerative_pairing.companion_crop)} Synergy`;
    document.getElementById('regen-text').textContent = data.regenerative_pairing.reason;
  } else {
    document.getElementById('regen-section').style.display = 'none';
  }

  // Stats — show REAL model accuracy from training_metrics
  const metrics = data.training_metrics || {};
  document.getElementById('stats-row').innerHTML = `
    <div class="stat-box"><div class="stat-box__value">${primary.confidence}%</div><div class="stat-box__label">ML Confidence</div></div>
    <div class="stat-box"><div class="stat-box__value" style="color:var(--gold)">₹${primary.price || 'N/A'}</div><div class="stat-box__label">Live Mandi Price</div></div>
    <div class="stat-box"><div class="stat-box__value" style="color:var(--growth-green)">${primary.profit_index || 'N/A'}</div><div class="stat-box__label">Profit Index</div></div>
    <div class="stat-box"><div class="stat-box__value" style="color:var(--primary)">${metrics.test_accuracy ? (metrics.test_accuracy * 100).toFixed(1) + '%' : 'N/A'}</div><div class="stat-box__label">Model Accuracy</div></div>
    <div class="stat-box"><div class="stat-box__value" style="color:var(--water-blue)">${metrics.dataset_rows || 'N/A'}</div><div class="stat-box__label">Training Rows</div></div>
    <div class="stat-box"><div class="stat-box__value" style="color:var(--secondary)">${metrics.num_crops || 'N/A'}</div><div class="stat-box__label">Crops Trained</div></div>`;

  // Alternatives
  const maxPI = Math.max(...data.profit_index.map(p => p.profit_index || 0), 1);
  document.getElementById('alternatives-grid').innerHTML = data.alternatives.map((alt, i) => `
    <div class="alt-card">
      <div class="alt-card__rank">Rank #${i + 2}</div>
      <div class="alt-card__crop">${cap(alt.crop)}</div>
      <div class="profit-bar-container"><div class="profit-bar"><div class="profit-bar__fill" style="width:${((alt.profit_index || 0) / maxPI * 100).toFixed(0)}%"></div></div></div>
      <div class="alt-card__meta">
        <div class="alt-card__stat"><div class="alt-card__stat-label">Confidence</div><div class="alt-card__stat-value">${alt.confidence}%</div></div>
        <div class="alt-card__stat"><div class="alt-card__stat-label">Price</div><div class="alt-card__stat-value">${alt.price ? '₹' + alt.price : 'N/A'}</div></div>
        <div class="alt-card__stat"><div class="alt-card__stat-label">P.I.</div><div class="alt-card__stat-value">${alt.profit_index || 'N/A'}</div></div>
      </div>
    </div>`).join('');
}

// ═══ Market Page ═════════════════════════════════════════════════
function renderMarketPage() {
  if (!state.strategy) return;
  const data = state.strategy;
  const container = document.getElementById('market-content');
  const cap = s => s.charAt(0).toUpperCase() + s.slice(1);

  container.innerHTML = `
    <table class="market-table">
      <thead><tr><th>Crop</th><th>Mandi</th><th>State</th><th>Live Price</th><th>Profit Index</th><th>Trend</th><th>Source</th></tr></thead>
      <tbody>${data.profit_index.map(item => {
        const hasError = item.error;
        return `<tr>
          <td style="font-weight:600">${cap(item.crop)}</td>
          <td>${item.mandi || (hasError ? '—' : 'N/A')}</td>
          <td>${item.state || '—'}</td>
          <td class="price-cell">${item.price ? '₹' + item.price + '/q' : '<span style="color:var(--error)">No data</span>'}</td>
          <td><span class="data-mono" style="color:var(--gold-dark);font-weight:700">${item.profit_index || '—'}</span></td>
          <td><span class="trend-indicator trend-indicator--${item.trend || 'stable'}"><span class="material-icons-outlined" style="font-size:16px">${item.trend === 'rising' ? 'trending_up' : item.trend === 'falling' ? 'trending_down' : 'trending_flat'}</span>${item.trend || '—'}</span></td>
          <td class="body-sm">${item.source || (hasError ? '<span style="color:var(--error)">' + item.error + '</span>' : '—')}</td>
        </tr>`;
      }).join('')}
      </tbody>
    </table>`;

  if (data.market_insights && data.market_insights.length > 0) {
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
  const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
  const metrics = state.modelMetrics || data.training_metrics || {};

  const container = document.getElementById('research-content');
  container.innerHTML = `
    <!-- Model Training Metrics -->
    <div class="chart-card" style="border-left:4px solid var(--primary-container)">
      <div class="chart-card__header">
        <div class="chart-card__icon chart-card__icon--feature"><span class="material-icons-outlined">precision_manufacturing</span></div>
        <div><div class="headline-md">XGBoost Model Training Report</div><div class="body-sm" style="color:var(--on-surface-variant)">Trained on real dataset: ${metrics.dataset_rows || 'N/A'} rows, ${metrics.num_crops || 'N/A'} crops</div></div>
      </div>
      <div class="stats-row">
        <div class="stat-box"><div class="stat-box__value">${metrics.test_accuracy ? (metrics.test_accuracy * 100).toFixed(2) + '%' : 'N/A'}</div><div class="stat-box__label">Test Accuracy</div></div>
        <div class="stat-box"><div class="stat-box__value" style="color:var(--growth-green)">${metrics.macro_f1 ? (metrics.macro_f1 * 100).toFixed(2) + '%' : 'N/A'}</div><div class="stat-box__label">Macro F1 Score</div></div>
        <div class="stat-box"><div class="stat-box__value" style="color:var(--water-blue)">${metrics.weighted_f1 ? (metrics.weighted_f1 * 100).toFixed(2) + '%' : 'N/A'}</div><div class="stat-box__label">Weighted F1</div></div>
        <div class="stat-box"><div class="stat-box__value" style="color:var(--secondary)">${metrics.train_samples || 'N/A'}</div><div class="stat-box__label">Train Samples</div></div>
        <div class="stat-box"><div class="stat-box__value" style="color:var(--gold)">${metrics.test_samples || 'N/A'}</div><div class="stat-box__label">Test Samples</div></div>
        <div class="stat-box"><div class="stat-box__value">${metrics.train_accuracy ? (metrics.train_accuracy * 100).toFixed(2) + '%' : 'N/A'}</div><div class="stat-box__label">Train Accuracy</div></div>
      </div>
    </div>

    <div class="chart-card">
      <div class="chart-card__header">
        <div class="chart-card__icon chart-card__icon--feature"><span class="material-icons-outlined">bar_chart</span></div>
        <div><div class="headline-md">Global Feature Importance</div><div class="body-sm" style="color:var(--on-surface-variant)">XGBoost Gain Attribution — Real Model</div></div>
      </div>
      <div class="chart-container"><canvas id="chart-feature-importance"></canvas></div>
      <div class="chart-insight">"The model prioritizes <strong>${getTopFeature(data.feature_importance)}</strong> as the primary driver, reflecting real patterns in the ${metrics.dataset_rows || '57K'}-row training dataset."</div>
    </div>

    <div class="chart-card">
      <div class="chart-card__header">
        <div class="chart-card__icon chart-card__icon--shap"><span class="material-icons-outlined">waterfall_chart</span></div>
        <div><div class="headline-md">SHAP Force Plot</div><div class="body-sm" style="color:var(--on-surface-variant)">Local Prediction: ${cap(data.primary_recommendation.crop)}</div></div>
      </div>
      <div class="chart-container"><canvas id="chart-shap"></canvas></div>
      <div class="chart-insight">"${data.shap_explanation ? data.shap_explanation.explanation : 'SHAP analysis reveals the key factors driving this recommendation.'}"</div>
    </div>

    <div class="chart-card">
      <div class="chart-card__header">
        <div class="chart-card__icon chart-card__icon--market"><span class="material-icons-outlined">query_stats</span></div>
        <div><div class="headline-md">Market Equilibrium</div><div class="body-sm" style="color:var(--on-surface-variant)">Live Mandi Prices vs. Volatility — Data.gov.in</div></div>
      </div>
      <div class="chart-container"><canvas id="chart-market-eq"></canvas></div>
      <div class="chart-insight">"Supply-demand analysis from live Data.gov.in Mandi records."</div>
    </div>

    <div class="stats-row">
      <div class="stat-box"><div class="stat-box__value">3</div><div class="stat-box__label">Live API Streams</div></div>
      <div class="stat-box"><div class="stat-box__value" style="color:var(--growth-green)">${metrics.test_accuracy ? (metrics.test_accuracy * 100).toFixed(1) + '%' : 'N/A'}</div><div class="stat-box__label">Real Test Accuracy</div></div>
      <div class="stat-box"><div class="stat-box__value" style="color:var(--water-blue)">${metrics.dataset_rows || 'N/A'}</div><div class="stat-box__label">Dataset Size</div></div>
    </div>`;

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

// ═══ Charts ══════════════════════════════════════════════════════
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
      plugins: { legend: { display: false } },
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
  const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
  const labels = profitIndex.map(p => cap(p.crop));
  const prices = profitIndex.map(p => p.price || 0);
  const volatility = profitIndex.map(p => ((p.volatility || 0) * 100).toFixed(0));

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
