from flask import Flask, jsonify, render_template_string
import json
import os
import time
from datetime import datetime

app = Flask(__name__)

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'incidents.json')
ALERT_LOG = os.path.join(os.path.dirname(__file__), '..', 'logs', 'alerts.json')
RECOVERY_LOG = os.path.join(os.path.dirname(__file__), '..', 'logs', 'recovery.json')

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except:
        return []

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>SRE Platform Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Arial', sans-serif; background: #0d1117; color: #e6edf3; padding: 20px; }
        h1 { color: #58a6ff; margin-bottom: 5px; font-size: 24px; }
        .subtitle { color: #8b949e; margin-bottom: 30px; font-size: 13px; }
        .grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; }
        .card h3 { color: #8b949e; font-size: 12px; text-transform: uppercase; margin-bottom: 10px; }
        .card .value { font-size: 32px; font-weight: bold; }
        .healthy { color: #3fb950; }
        .unhealthy { color: #f85149; }
        .warning { color: #d29922; }
        .section { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .section h2 { color: #58a6ff; margin-bottom: 15px; font-size: 16px; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; color: #8b949e; font-size: 12px; padding: 8px; border-bottom: 1px solid #30363d; }
        td { padding: 10px 8px; border-bottom: 1px solid #21262d; font-size: 13px; }
        .badge { padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: bold; }
        .badge-green { background: #1a4731; color: #3fb950; }
        .badge-red { background: #3d1a1a; color: #f85149; }
        .badge-yellow { background: #3d2e0a; color: #d29922; }
        .badge-blue { background: #1a2d4a; color: #58a6ff; }
        .slo-bar { background: #21262d; border-radius: 4px; height: 8px; margin-top: 5px; }
        .slo-fill { height: 8px; border-radius: 4px; background: #3fb950; }
        .slo-fill.warning { background: #d29922; }
        .slo-fill.critical { background: #f85149; }
        .refresh { color: #8b949e; font-size: 11px; text-align: right; margin-bottom: 10px; }
    </style>
</head>
<body>
    <h1>🚀 SRE Platform Dashboard</h1>
    <p class="subtitle">Auto-refreshes every 10 seconds | SLO Target: 99.9% uptime</p>
    <p class="refresh">Last updated: {{ now }}</p>

    <!-- Summary Cards -->
    <div class="grid">
        <div class="card">
            <h3>Total Incidents</h3>
            <div class="value warning">{{ incidents|length }}</div>
        </div>
        <div class="card">
            <h3>Active Alerts</h3>
            <div class="value {{ 'unhealthy' if active_alerts > 0 else 'healthy' }}">{{ active_alerts }}</div>
        </div>
        <div class="card">
            <h3>Recovery Events</h3>
            <div class="value healthy">{{ recoveries|length }}</div>
        </div>
    </div>

    <!-- Incidents Table -->
    <div class="section">
        <h2>🚨 Incident Log</h2>
        {% if incidents %}
        <table>
            <tr>
                <th>ID</th>
                <th>Service</th>
                <th>Severity</th>
                <th>Detected At</th>
                <th>Status</th>
                <th>Root Cause</th>
            </tr>
            {% for inc in incidents|reverse %}
            <tr>
                <td>{{ inc.id }}</td>
                <td>{{ inc.service }}</td>
                <td>
                    <span class="badge {{ 'badge-red' if inc.severity == 'P1' else 'badge-yellow' }}">
                        {{ inc.severity }}
                    </span>
                </td>
                <td>{{ inc.detected_at[:19] }}</td>
                <td>
                    <span class="badge {{ 'badge-green' if inc.resolved_at else 'badge-red' }}">
                        {{ 'Resolved' if inc.resolved_at else 'Active' }}
                    </span>
                </td>
                <td>{{ inc.root_cause or 'Investigating...' }}</td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p style="color: #3fb950">✅ No incidents recorded</p>
        {% endif %}
    </div>

    <!-- Alerts Table -->
    <div class="section">
        <h2>🔔 Alert History</h2>
        {% if alerts %}
        <table>
            <tr>
                <th>ID</th>
                <th>Service</th>
                <th>Type</th>
                <th>Severity</th>
                <th>Fired At</th>
                <th>Status</th>
            </tr>
            {% for alert in alerts|reverse %}
            <tr>
                <td>{{ alert.id }}</td>
                <td>{{ alert.service }}</td>
                <td>{{ alert.type }}</td>
                <td>
                    <span class="badge {{ 'badge-red' if alert.severity == 'P1' else 'badge-yellow' }}">
                        {{ alert.severity }}
                    </span>
                </td>
                <td>{{ alert.fired_at[:19] }}</td>
                <td>
                    <span class="badge {{ 'badge-green' if alert.resolved_at else 'badge-red' }}">
                        {{ 'Resolved' if alert.resolved_at else 'Active' }}
                    </span>
                </td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p style="color: #3fb950">✅ No alerts fired</p>
        {% endif %}
    </div>

    <!-- Recovery Log -->
    <div class="section">
        <h2>🔧 Auto-Recovery Log</h2>
        {% if recoveries %}
        <table>
            <tr>
                <th>Service</th>
                <th>Event</th>
                <th>Timestamp</th>
                <th>Action</th>
                <th>Result</th>
            </tr>
            {% for rec in recoveries|reverse %}
            <tr>
                <td>{{ rec.service }}</td>
                <td>{{ rec.event }}</td>
                <td>{{ rec.timestamp[:19] }}</td>
                <td>{{ rec.action }}</td>
                <td>
                    <span class="badge {{ 'badge-green' if rec.success else 'badge-red' }}">
                        {{ 'Success' if rec.success else 'Failed' }}
                    </span>
                </td>
            </tr>
            {% endfor %}
        </table>
        {% else %}
        <p style="color: #8b949e">No recovery events yet</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    incidents = load_json(LOG_FILE)
    alerts = load_json(ALERT_LOG)
    recoveries = load_json(RECOVERY_LOG)
    active_alerts = sum(1 for a in alerts if not a.get('resolved_at'))

    return render_template_string(
        DASHBOARD_HTML,
        incidents=incidents,
        alerts=alerts,
        recoveries=recoveries,
        active_alerts=active_alerts,
        now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.route('/api/status')
def api_status():
    incidents = load_json(LOG_FILE)
    alerts = load_json(ALERT_LOG)
    recoveries = load_json(RECOVERY_LOG)
    return jsonify({
        "incidents": len(incidents),
        "active_alerts": sum(1 for a in alerts if not a.get('resolved_at')),
        "recoveries": len(recoveries),
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🚀 SRE Dashboard running on http://localhost:5000")
    app.run(port=5000, debug=False)