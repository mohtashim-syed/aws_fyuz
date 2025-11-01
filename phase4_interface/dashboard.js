// WebSocket connection to UI broker
let ws = null;
let currentIncidents = [];
let reconnectAttempts = 0;
const MAX_RECONNECT_DELAY = 5000;

function connectWebSocket() {
    // Close existing connection if any
    if (ws && ws.readyState <= 1) {
        ws.close();
    }
    
    ws = new WebSocket('ws://localhost:7003/ws/ui');
    
    ws.onopen = () => {
        console.log('✓ Connected to UI broker');
        reconnectAttempts = 0;
    };
    
    ws.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            updateDashboard(payload);
        } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('Disconnected from UI broker');
        reconnectAttempts++;
        const delay = Math.min(1000 * reconnectAttempts, MAX_RECONNECT_DELAY);
        console.log(`Reconnecting in ${delay}ms...`);
        setTimeout(connectWebSocket, delay);
    };
}

function updateDashboard(payload) {
    // Update region tiles
    updateRegionTiles(payload.regions);
    
    // Update incident list
    updateIncidentList(payload.incidents);
    
    // Store current incidents
    currentIncidents = payload.incidents;
}

function updateRegionTiles(regions) {
    const container = document.getElementById('regionTiles');
    container.innerHTML = '';
    
    regions.forEach(region => {
        const kpis = region.kpis;
        const card = document.createElement('div');
        card.className = 'region-card';
        card.innerHTML = `
            <h3>${region.name}</h3>
            <div class="kpi-grid">
                <div class="kpi">
                    <div class="kpi-label">Packet Loss</div>
                    <div class="kpi-value ${getKpiClass(kpis.packet_loss_pct, 5, 10)}">${kpis.packet_loss_pct}%</div>
                </div>
                <div class="kpi">
                    <div class="kpi-label">Latency</div>
                    <div class="kpi-value ${getKpiClass(kpis.latency_ms, 80, 120)}">${kpis.latency_ms}ms</div>
                </div>
                <div class="kpi">
                    <div class="kpi-label">Backhaul Util</div>
                    <div class="kpi-value ${getKpiClass(kpis.backhaul_util_pct, 75, 85)}">${kpis.backhaul_util_pct}%</div>
                </div>
                <div class="kpi">
                    <div class="kpi-label">Throughput</div>
                    <div class="kpi-value normal">${kpis.throughput_mbps} Mbps</div>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

function getKpiClass(value, warningThreshold, criticalThreshold) {
    if (value >= criticalThreshold) return 'critical';
    if (value >= warningThreshold) return 'warning';
    return 'normal';
}

function updateIncidentList(incidents) {
    const container = document.getElementById('incidentList');
    container.innerHTML = '';
    
    if (incidents.length === 0) {
        container.innerHTML = '<p style="color: #94a3b8;">No active incidents</p>';
        return;
    }
    
    incidents.forEach(incident => {
        const item = document.createElement('div');
        item.className = 'incident-item';
        item.onclick = () => toggleIncidentDrawer(incident.event_id);
        item.innerHTML = `
            <div class="incident-header">
                <span class="incident-id">${incident.event_id}</span>
                <span class="incident-status status-${incident.status}">${incident.status}</span>
            </div>
            <div class="incident-summary">${incident.region} - ${incident.site_id}</div>
            <div class="incident-summary">${incident.summary}</div>
            <div class="incident-drawer" id="drawer-${incident.event_id}">
                <div class="drawer-section">
                    <h4>Evidence</h4>
                    <ul class="evidence-list">
                        ${incident.evidence ? incident.evidence.map(e => `<li>${e}</li>`).join('') : '<li>No evidence available</li>'}
                    </ul>
                </div>
                <div class="drawer-section">
                    <h4>Explanation</h4>
                    <p style="font-size: 13px; color: #cbd5e1;">${incident.explanation || 'No explanation available'}</p>
                </div>
                <div class="drawer-section">
                    <h4>Recommendations</h4>
                    <ul class="evidence-list">
                        ${incident.recommendations ? incident.recommendations.map(r => `<li>${r}</li>`).join('') : '<li>No recommendations available</li>'}
                    </ul>
                </div>
                <div class="drawer-section">
                    <h4>Risks</h4>
                    <ul class="evidence-list">
                        ${incident.risks ? incident.risks.map(r => `<li>${r}</li>`).join('') : '<li>No risks identified</li>'}
                    </ul>
                </div>
                <div style="margin-top: 15px;">
                    <button class="btn btn-primary" onclick="approvePlan('${incident.event_id}')">Approve Safe Plan</button>
                    <button class="btn btn-secondary" onclick="exportSnapshot('${incident.event_id}')">Export</button>
                </div>
            </div>
        `;
        container.appendChild(item);
    });
}

function toggleIncidentDrawer(eventId) {
    const drawer = document.getElementById(`drawer-${eventId}`);
    drawer.classList.toggle('active');
}

function approvePlan(eventId) {
    fetch('http://localhost:7003/api/approve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_id: eventId, approval: true })
    })
    .then(response => response.json())
    .then(data => {
        alert(`Plan approved for ${eventId}`);
    })
    .catch(error => console.error('Error approving plan:', error));
}

function runSimulation() {
    const trafficMultiplier = parseFloat(document.getElementById('trafficSlider').value);
    const capacityDelta = parseInt(document.getElementById('capacitySlider').value);
    
    fetch('http://localhost:7002/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            event_id: 'sim_test',
            region: 'NorthEast',
            site_id: 'NE_SITE_003',
            levers: {
                traffic_multiplier: trafficMultiplier,
                capacity_delta: { units: capacityDelta }
            },
            trace_id: `trace_sim_${Date.now()}`
        })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('simResults').style.display = 'block';
        document.getElementById('simOutput').innerHTML = `
            <p><strong>Predicted Packet Loss:</strong> ${data.pred_packet_loss_pct}%</p>
            <p><strong>Predicted Latency:</strong> ${data.pred_latency_ms}ms</p>
            <p><strong>Predicted Blocking Prob:</strong> ${data.pred_blocking_prob}</p>
            <p style="margin-top: 10px; font-size: 12px; color: #94a3b8;"><strong>Assumptions:</strong> ${data.assumptions.join(', ')}</p>
        `;
    })
    .catch(error => console.error('Error running simulation:', error));
}

function sendChat() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (!message) return;
    
    // Add user message
    addChatMessage(message, 'user');
    input.value = '';
    
    // Mock response (replace with actual API call)
    setTimeout(() => {
        const response = generateChatResponse(message);
        addChatMessage(response, 'system');
    }, 500);
}

function addChatMessage(text, sender) {
    const container = document.getElementById('chatMessages');
    const msg = document.createElement('div');
    msg.className = `chat-message ${sender}`;
    msg.textContent = text;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
}

function generateChatResponse(query) {
    if (query.toLowerCase().includes('packet loss') && query.toLowerCase().includes('northeast')) {
        return 'Packet loss in NorthEast spiked to 12.45% due to backhaul congestion. The backhaul link is saturated at 91% capacity. Confidence: 0.92';
    }
    return 'Query received. Please check the incident panel for detailed analysis.';
}

function exportSnapshot(eventId) {
    const incident = currentIncidents.find(i => i.event_id === eventId);
    if (!incident) return;
    
    const snapshot = {
        timestamp: new Date().toISOString(),
        incident: incident,
        export_type: 'incident_snapshot'
    };
    
    const blob = new Blob([JSON.stringify(snapshot, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `snapshot_${eventId}.json`;
    a.click();
}

// Slider updates
document.getElementById('trafficSlider').oninput = function() {
    document.getElementById('trafficValue').textContent = this.value + 'x';
};

document.getElementById('capacitySlider').oninput = function() {
    document.getElementById('capacityValue').textContent = '+' + this.value;
};

// Initialize
connectWebSocket();
