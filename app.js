// CompeteMind AI — Frontend Application Logic

let currentTimelineDays = 180;
let currentTimelineCategory = 'all';
let competitorsData = [];
let chartCategoryInstance = null;
let chartCompetitorsInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardStats();
    loadCompetitors();
    runAIPatternSpotter();
    loadTimeline();
    loadKaggleDatasets();
});

// --- Tab Switching ---
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('text-indigo-400', 'bg-indigo-950/40', 'border', 'border-indigo-800/50');
        btn.classList.add('text-slate-400');
    });

    const activeContent = document.getElementById(`tab-content-${tabId}`);
    if (activeContent) activeContent.classList.remove('hidden');

    const activeBtn = document.getElementById(`tab-btn-${tabId}`);
    if (activeBtn) {
        activeBtn.classList.remove('text-slate-400');
        activeBtn.classList.add('text-indigo-400', 'bg-indigo-950/40', 'border', 'border-indigo-800/50');
    }
}

// --- Dashboard Stats & Charts ---
async function loadDashboardStats() {
    try {
        const res = await fetch('/api/dashboard/stats');
        const data = await res.json();

        document.getElementById('stat-competitors').innerText = data.total_competitors || 0;
        document.getElementById('stat-events').innerText = data.total_events || 0;
        document.getElementById('stat-insights').innerText = data.total_insights || 0;

        renderCategoryChart(data.category_counts || {});
        renderCompetitorChart(data.competitor_counts || []);
    } catch (err) {
        console.error('Failed to load dashboard stats:', err);
    }
}

function renderCategoryChart(catCounts) {
    const ctx = document.getElementById('chart-category').getContext('2d');
    if (chartCategoryInstance) chartCategoryInstance.destroy();

    const labels = Object.keys(catCounts);
    const data = Object.values(catCounts);

    chartCategoryInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: ['#f59e0b', '#10b981', '#a855f7', '#06b6d4'],
                borderWidth: 2,
                borderColor: '#1e293b'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 11 } } }
            }
        }
    });
}

function renderCompetitorChart(compCounts) {
    const ctx = document.getElementById('chart-competitors').getContext('2d');
    if (chartCompetitorsInstance) chartCompetitorsInstance.destroy();

    const labels = compCounts.map(c => c.name);
    const data = compCounts.map(c => c.count);

    chartCompetitorsInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Intelligence Events Logged',
                data: data,
                backgroundColor: '#6366f1',
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { display: false } },
                y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// --- AI Pattern Spotter ---
async function runAIPatternSpotter() {
    const container = document.getElementById('patterns-container');
    container.innerHTML = `
        <div class="col-span-2 text-center py-8 text-slate-400">
            <i class="fa-solid fa-spinner fa-spin text-2xl text-indigo-400 mb-2"></i>
            <p class="text-xs">Analyzing 180-day cumulative memory horizon for macro strategic patterns...</p>
        </div>
    `;

    try {
        const res = await fetch('/api/analyze/patterns', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ timeframe_days: currentTimelineDays })
        });
        const data = await res.json();

        if (data.macro_synthesis) {
            document.getElementById('macro-headline').innerText = data.macro_synthesis.headline || '6-Month Landscape Synthesis';
            document.getElementById('macro-summary').innerText = data.macro_synthesis.executive_summary || '';
        }

        renderPatternCards(data.patterns || []);
    } catch (err) {
        console.error('Failed to run AI Pattern Spotter:', err);
    }
}

function renderPatternCards(patterns) {
    const container = document.getElementById('patterns-container');
    container.innerHTML = '';

    if (patterns.length === 0) {
        container.innerHTML = `<p class="text-slate-400 text-xs col-span-2">No patterns detected in current memory.</p>`;
        return;
    }

    patterns.forEach(p => {
        const threatColor = p.threat === 'Critical' ? 'bg-red-500/10 text-red-400 border-red-500/30' :
                            p.threat === 'High' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';

        const card = document.createElement('div');
        card.className = 'glass-panel p-5 rounded-2xl border border-slate-800 space-y-3 relative overflow-hidden';
        card.innerHTML = `
            <div class="flex justify-between items-start">
                <span class="text-xs font-semibold px-2.5 py-1 rounded-full border ${threatColor}">
                    <i class="fa-solid fa-triangle-exclamation"></i> Threat: ${p.threat || 'Medium'}
                </span>
                <span class="text-xs text-slate-400">Confidence: ${p.confidence || 90}%</span>
            </div>
            <h4 class="font-bold text-white text-base">${p.title || p.insight_title}</h4>
            <p class="text-slate-300 text-xs leading-relaxed">${p.summary}</p>
            <div class="bg-indigo-950/40 p-3 rounded-xl border border-indigo-800/40">
                <p class="text-xs font-semibold text-indigo-300 flex items-center gap-1.5 mb-1">
                    <i class="fa-solid fa-chess"></i> Recommended Counter-Strategy:
                </p>
                <p class="text-xs text-slate-300">${p.response || p.recommended_response}</p>
            </div>
        `;
        container.appendChild(card);
    });
}

// --- 6-Month Memory Timeline ---
async function loadTimeline() {
    const container = document.getElementById('timeline-events-container');
    container.innerHTML = `<p class="text-slate-400 text-xs">Loading historical timeline memory...</p>`;

    try {
        const url = `/api/timeline?days=${currentTimelineDays}${currentTimelineCategory !== 'all' ? '&category=' + currentTimelineCategory : ''}`;
        const res = await fetch(url);
        const data = await res.json();

        container.innerHTML = '';
        if (!data.events || data.events.length === 0) {
            container.innerHTML = `<p class="text-slate-400 text-xs">No events logged in the ${currentTimelineDays}-day window for category '${currentTimelineCategory}'.</p>`;
            return;
        }

        data.events.forEach(ev => {
            const catBadge = ev.category === 'Pricing' ? 'bg-amber-500/20 text-amber-300 border-amber-500/30' :
                             ev.category === 'Feature' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' :
                             ev.category === 'Messaging' ? 'bg-purple-500/20 text-purple-300 border-purple-500/30' : 'bg-sky-500/20 text-sky-300 border-sky-500/30';

            const item = document.createElement('div');
            item.className = 'relative flex items-start space-x-4';
            item.innerHTML = `
                <div class="absolute -left-8 top-1 h-5 w-5 rounded-full bg-slate-900 border-2 border-indigo-500 flex items-center justify-center">
                    <div class="h-2 w-2 rounded-full bg-indigo-400"></div>
                </div>
                <div class="glass-panel p-4 rounded-xl border border-slate-800 w-full space-y-2">
                    <div class="flex flex-wrap justify-between items-center gap-2">
                        <div class="flex items-center space-x-2">
                            <span class="font-bold text-sm text-white">${ev.competitor_name}</span>
                            <span class="text-xs px-2 py-0.5 rounded-md border font-medium ${catBadge}">${ev.category}</span>
                        </div>
                        <span class="text-xs text-slate-400 font-mono"><i class="fa-regular fa-clock"></i> ${ev.detected_at.substring(0, 10)}</span>
                    </div>
                    <h5 class="text-xs font-semibold text-slate-200">${ev.title}</h5>
                    <p class="text-xs text-slate-400">${ev.description}</p>
                    <div class="flex items-center space-x-3 text-[10px] text-slate-500 pt-1">
                        <span>Source: ${ev.source_type}</span>
                        <span>Impact Score: ${'★'.repeat(ev.impact_score)}</span>
                    </div>
                </div>
            `;
            container.appendChild(item);
        });
    } catch (err) {
        console.error('Failed to load timeline:', err);
    }
}

function filterTimelineDays(days) {
    currentTimelineDays = days;
    document.querySelectorAll('.tday-btn').forEach(b => {
        b.classList.remove('bg-indigo-600', 'text-white', 'shadow-md');
        b.classList.add('bg-slate-800', 'text-slate-300');
    });
    document.getElementById(`tbtn-${days}`).classList.add('bg-indigo-600', 'text-white', 'shadow-md');
    loadTimeline();
}

function filterTimelineCat(cat) {
    currentTimelineCategory = cat;
    document.querySelectorAll('.tcat-btn').forEach(b => {
        b.classList.remove('bg-indigo-600', 'text-white');
        b.classList.add('bg-slate-800');
    });
    document.getElementById(`tcat-${cat}`).classList.add('bg-indigo-600', 'text-white');
    loadTimeline();
}

// --- Competitor Roster & Matrix ---
async function loadCompetitors() {
    try {
        const res = await fetch('/api/competitors');
        competitorsData = await res.json();

        renderCompetitorsGrid(competitorsData);
        renderStrategyMatrix(competitorsData);
        populateSelectOptions(competitorsData);
    } catch (err) {
        console.error('Failed to load competitors:', err);
    }
}

function renderCompetitorsGrid(competitors) {
    const grid = document.getElementById('competitors-grid');
    grid.innerHTML = '';

    competitors.forEach(c => {
        const card = document.createElement('div');
        card.className = 'glass-panel p-5 rounded-2xl border border-slate-800 space-y-3 relative';
        card.innerHTML = `
            <div class="flex justify-between items-start">
                <h4 class="font-bold text-white text-base">${c.name}</h4>
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${c.threat_level === 'High' || c.threat_level === 'Critical' ? 'bg-red-500/20 text-red-300' : 'bg-slate-800 text-slate-300'}">
                    ${c.threat_level} Threat
                </span>
            </div>
            <p class="text-xs text-slate-400">${c.industry} | ${c.tier} Tier</p>
            <div class="text-xs text-slate-300 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800">
                <span class="text-slate-500 block text-[10px] uppercase font-semibold">Website</span>
                <a href="${c.website_url || '#'}" target="_blank" class="text-indigo-400 hover:underline truncate block">${c.domain || c.website_url || 'N/A'}</a>
            </div>
        `;
        grid.appendChild(card);
    });
}

function renderStrategyMatrix(competitors) {
    const tbody = document.getElementById('matrix-tbody');
    tbody.innerHTML = '';

    competitors.forEach(c => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-800/40 transition';
        tr.innerHTML = `
            <td class="p-3 font-semibold text-white">${c.name}</td>
            <td class="p-3"><span class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px] font-bold">${c.threat_level}</span></td>
            <td class="p-3 text-amber-300">Price tier restructures & AI add-on fee</td>
            <td class="p-3 text-emerald-300">AI Search, Automated Issue Triage</td>
            <td class="p-3 text-sky-300">LLM Engineers & Enterprise Sales VPs</td>
            <td class="p-3 text-slate-400 italic">"AI-Powered Productivity Platform"</td>
        `;
        tbody.appendChild(tr);
    });
}

function populateSelectOptions(competitors) {
    const scrapeSelect = document.getElementById('scrape-competitor-select');
    const simSelect = document.getElementById('sim-competitor-select');
    
    if (scrapeSelect) scrapeSelect.innerHTML = '';
    if (simSelect) simSelect.innerHTML = '';

    competitors.forEach(c => {
        if (scrapeSelect) scrapeSelect.innerHTML += `<option value="${c.id}">${c.name} (${c.domain || 'No URL'})</option>`;
        if (simSelect) simSelect.innerHTML += `<option value="${c.id}">${c.name}</option>`;
    });
}

function openAddCompetitorModal() {
    document.getElementById('modal-add-competitor').classList.remove('hidden');
}

function closeAddCompetitorModal() {
    document.getElementById('modal-add-competitor').classList.add('hidden');
}

async function saveNewCompetitor() {
    const name = document.getElementById('new-comp-name').value;
    if (!name) return alert('Please enter competitor name');

    try {
        const res = await fetch('/api/competitors', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                domain: document.getElementById('new-comp-domain').value,
                threat_level: document.getElementById('new-comp-threat').value,
                tier: document.getElementById('new-comp-tier').value,
                website_url: document.getElementById('new-comp-url').value,
                pricing_url: document.getElementById('new-comp-pricing').value
            })
        });
        const data = await res.json();
        closeAddCompetitorModal();
        loadCompetitors();
        loadDashboardStats();
    } catch (err) {
        console.error('Failed to save competitor:', err);
    }
}

// --- Kaggle Datasets Hub ---
async function loadKaggleDatasets(query = '') {
    const container = document.getElementById('kaggle-datasets-container');
    container.innerHTML = `<p class="text-slate-400 text-xs col-span-3">Searching Kaggle competitive intelligence datasets...</p>`;

    try {
        const res = await fetch(`/api/kaggle/search?q=${encodeURIComponent(query)}`);
        const data = await res.json();

        container.innerHTML = '';
        (data.datasets || []).forEach(ds => {
            const card = document.createElement('div');
            card.className = 'glass-panel p-5 rounded-2xl border border-slate-800 space-y-3 flex flex-col justify-between';
            card.innerHTML = `
                <div class="space-y-2">
                    <div class="flex justify-between items-start">
                        <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-sky-500/20 text-sky-300 border border-sky-500/30">
                            ${ds.category || 'Kaggle Dataset'}
                        </span>
                        <span class="text-[10px] text-slate-400">By ${ds.creator || 'Kaggle'}</span>
                    </div>
                    <h4 class="font-bold text-white text-sm leading-snug">${ds.title}</h4>
                    <p class="text-slate-400 text-xs leading-relaxed">${ds.description}</p>
                </div>
                <div class="pt-3 border-t border-slate-800 flex justify-between items-center">
                    <span class="text-slate-400 text-[10px]">${ds.sample_records || 50}+ Records</span>
                    <button onclick="importKaggleDataset('${ds.ref}')" class="bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-3 py-1.5 rounded-xl transition flex items-center gap-1.5">
                        <i class="fa-solid fa-file-import"></i> Import Dataset
                    </button>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error('Failed to load Kaggle datasets:', err);
    }
}

function searchKaggleDatasets() {
    const q = document.getElementById('kaggle-search-input').value;
    loadKaggleDatasets(q);
}

async function importKaggleDataset(ref) {
    alert(`Importing Kaggle dataset '${ref}' into 6-month cumulative memory database...`);
    try {
        const res = await fetch('/api/kaggle/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset_ref: ref })
        });
        const data = await res.json();
        alert(data.message);
        loadDashboardStats();
        runAIPatternSpotter();
        loadTimeline();
    } catch (err) {
        console.error('Failed to import Kaggle dataset:', err);
    }
}

// --- Live Website Scraper ---
async function triggerScrape() {
    const compId = document.getElementById('scrape-competitor-select').value;
    const box = document.getElementById('scrape-results-box');
    box.classList.remove('hidden');
    box.innerText = 'Connecting to competitor URL, performing HTML differential hashing scan...';

    try {
        const res = await fetch('/api/ingest/scrape', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ competitor_id: parseInt(compId) })
        });
        const data = await res.json();
        box.innerText = JSON.stringify(data, null, 2);
        loadDashboardStats();
        loadTimeline();
    } catch (err) {
        box.innerText = 'Error running scraper: ' + err.message;
    }
}

// --- Simulator ---
async function triggerSimulation() {
    const compId = document.getElementById('sim-competitor-select').value;
    const category = document.getElementById('sim-category-select').value;
    const title = document.getElementById('sim-title-input').value;
    const desc = document.getElementById('sim-desc-input').value;

    try {
        const res = await fetch('/api/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                competitor_id: parseInt(compId),
                category: category,
                title: title,
                description: desc
            })
        });
        const data = await res.json();
        alert(data.message);

        loadDashboardStats();
        runAIPatternSpotter();
        loadTimeline();
        switchTab('dashboard');
    } catch (err) {
        console.error('Simulation failed:', err);
    }
}
