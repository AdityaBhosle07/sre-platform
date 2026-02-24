import json
import time
import os
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(__file__), '..', 'logs', 'incidents.json')
ALERT_LOG = os.path.join(os.path.dirname(__file__), '..', 'logs', 'alerts.json')

# Alert thresholds
THRESHOLDS = {
    "consecutive_failures": 3,      # Alert after 3 consecutive failures
    "uptime_below": 99.0,           # Alert if uptime drops below 99%
    "error_budget_consumed": 50.0,  # Alert if 50% of error budget consumed
    "latency_ms": 1000,             # Alert if latency exceeds 1000ms
}

# Alert state — prevents duplicate alerts
active_alerts = {}

def load_alerts():
    try:
        with open(ALERT_LOG, 'r') as f:
            content = f.read().strip()
            return json.loads(content) if content else []
    except:
        return []

def save_alert(alert):
    alerts = load_alerts()
    alerts.append(alert)
    with open(ALERT_LOG, 'w') as f:
        json.dump(alerts, f, indent=2)

def fire_alert(service, alert_type, message, severity="P2"):
    alert_key = f"{service}_{alert_type}"

    # Don't re-fire the same alert if already active
    if alert_key in active_alerts:
        return

    alert = {
        "id": f"ALERT-{int(time.time())}",
        "service": service,
        "type": alert_type,
        "severity": severity,
        "message": message,
        "fired_at": datetime.now().isoformat(),
        "resolved_at": None,
        "notified_via": ["console", "log"]
    }

    active_alerts[alert_key] = alert
    save_alert(alert)

    # Console notification (in real world this would be PagerDuty/Slack)
    print(f"\n🔔 ALERT FIRED [{severity}]")
    print(f"   Service  : {service}")
    print(f"   Type     : {alert_type}")
    print(f"   Message  : {message}")
    print(f"   Alert ID : {alert['id']}")
    print(f"   Time     : {alert['fired_at']}\n")

def resolve_alert(service, alert_type):
    alert_key = f"{service}_{alert_type}"

    if alert_key not in active_alerts:
        return

    alert = active_alerts.pop(alert_key)

    # Update alert log with resolution time
    alerts = load_alerts()
    for a in reversed(alerts):
        if a["id"] == alert["id"]:
            a["resolved_at"] = datetime.now().isoformat()
            break

    with open(ALERT_LOG, 'w') as f:
        json.dump(alerts, f, indent=2)

    print(f"\n✅ ALERT RESOLVED")
    print(f"   Service  : {service}")
    print(f"   Type     : {alert_type}")
    print(f"   Alert ID : {alert['id']}\n")

def evaluate_alerts(service_state):
    """Evaluate all services against thresholds and fire/resolve alerts"""
    for name, state in service_state.items():

        # 1. Consecutive failures alert
        if state["consecutive_failures"] >= THRESHOLDS["consecutive_failures"]:
            fire_alert(
                service=name,
                alert_type="consecutive_failures",
                message=f"{name} has failed {state['consecutive_failures']} consecutive health checks",
                severity="P1"
            )
        else:
            resolve_alert(name, "consecutive_failures")

        # 2. Uptime SLO breach alert
        if state["total_checks"] > 10 and state["uptime_percent"] < THRESHOLDS["uptime_below"]:
            fire_alert(
                service=name,
                alert_type="slo_breach",
                message=f"{name} uptime {state['uptime_percent']}% is below SLO target of {THRESHOLDS['uptime_below']}%",
                severity="P1"
            )
        else:
            resolve_alert(name, "slo_breach")

        # 3. Error budget consumed alert
        if state["error_budget_consumed"] >= THRESHOLDS["error_budget_consumed"]:
            fire_alert(
                service=name,
                alert_type="error_budget",
                message=f"{name} has consumed {state['error_budget_consumed']} minutes of error budget (50% threshold)",
                severity="P2"
            )
        else:
            resolve_alert(name, "error_budget")

        # 4. High latency alert
        last_latency = state.get("last_latency")
        if last_latency and last_latency > THRESHOLDS["latency_ms"]:
            fire_alert(
                service=name,
                alert_type="high_latency",
                message=f"{name} latency {last_latency}ms exceeds threshold of {THRESHOLDS['latency_ms']}ms",
                severity="P2"
            )
        else:
            resolve_alert(name, "high_latency")

def get_active_alerts():
    return list(active_alerts.values())

def print_alert_summary():
    alerts = get_active_alerts()
    if not alerts:
        print("  📭 No active alerts")
        return
    print(f"  🔔 {len(alerts)} active alert(s):")
    for alert in alerts:
        print(f"     [{alert['severity']}] {alert['service']} — {alert['type']}")

if __name__ == '__main__':
    print("Alert Manager running...")
    print(f"Thresholds: {json.dumps(THRESHOLDS, indent=2)}")